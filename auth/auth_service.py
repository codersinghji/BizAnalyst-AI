
import re
import secrets

from datetime import datetime, timedelta, timezone

import bcrypt

from auth.auth_database import (
    create_user,
    get_user_by_email,
    save_password_reset_otp,
    clear_password_reset_otp,
    update_user_password
)

from auth.email_service import send_email

# ==========================================
# PASSWORD HASHING
# ==========================================

def hash_password(password):
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")

def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False

# ==========================================
# USER REGISTRATION
# ==========================================

def register_user(name, email, password):

    try:
        name = name.strip()
        email = email.strip().lower()

        if not name:
            return False, "Name is required."

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(email_pattern, email):
            return False, "Please enter a valid email address."

        if len(password) < 8:
            return False, "Password must contain at least 8 characters."

        existing_user = get_user_by_email(email)

        if existing_user:
            return False, "User already exists. Please login."

        password_hash = hash_password(password)

        create_user(
            name=name,
            email=email,
            password_hash=password_hash,
            role="Analyst"
        )

        return True, "Registration successful. Please login."

    except Exception as error:
        print("REGISTRATION ERROR:", repr(error))
        return False, "Registration failed. Please try again."

# ==========================================
# USER LOGIN
# ==========================================

def login_user(email, password):

    try:
        email = email.strip().lower()

        user = get_user_by_email(email)

        if not user:
            return False, "Invalid email or password.", None

        if not user["is_active"]:
            return False, "Your account has been disabled.", None

        if not verify_password(password, user["password_hash"]):
            return False, "Invalid email or password.", None

        user_data = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }

        return True, "Login successful.", user_data

    except Exception as error:
        print("LOGIN ERROR:", repr(error))
        return False, "Login failed. Please try again.", None

# ==========================================
# SEND PASSWORD RESET OTP USING GMAIL API
# ==========================================

def send_password_reset_otp(email):

    email = email.strip().lower()
    stage = "initialization"

    try:
        stage = "checking user"

        user = get_user_by_email(email)

        if not user or not user["is_active"]:
            return True, (
                "If an active account exists for this email, "
                "an OTP will be sent."
            )

        # Generate six-digit OTP
        stage = "generating OTP"

        otp = f"{secrets.randbelow(1000000):06d}"

        otp_hash = hash_password(otp)

        expiry = (
            datetime.now(timezone.utc) + timedelta(minutes=5)
        ).isoformat()

        # Save hashed OTP in database
        stage = "saving OTP"

        save_password_reset_otp(
            email,
            otp_hash,
            expiry
        )

        # Prepare email
        stage = "preparing email"

        subject = "BizAnalyst AI - Password Reset OTP"

        body = f"""
Hello {user['name']},

Your BizAnalyst AI password reset OTP is:

{otp}

This OTP expires in 5 minutes.

If you did not request this password reset,
please ignore this email.

Regards,
BizAnalyst AI Team
"""

        # Send email using Gmail API and OAuth2
        stage = "sending email through Gmail API"

        success, message = send_email(
            to_email=email,
            subject=subject,
            body=body
        )

        if not success:
            clear_password_reset_otp(email)

            print("GMAIL DELIVERY ERROR:", message)

            return False, (
                "Unable to send OTP email. "
                "Please try again later."
            )

        return True, "OTP sent successfully. Check your email."

    except Exception as error:

        try:
            clear_password_reset_otp(email)
        except Exception:
            pass

        print("OTP ERROR STAGE:", stage)
        print("OTP ERROR DETAILS:", repr(error))

        return False, (
            "OTP sending failed. Please try again."
        )

# ==========================================
# VERIFY PASSWORD RESET OTP
# ==========================================

def verify_reset_otp(email, otp):

    try:
        email = email.strip().lower()

        user = get_user_by_email(email)

        if not user:
            return False, "Invalid email or OTP."

        otp_hash = user["otp_hash"]
        otp_expiry = user["otp_expiry"]

        if not otp_hash or not otp_expiry:
            return False, "Please request a new OTP."

        # Check OTP expiry
        expiry_time = datetime.fromisoformat(otp_expiry)

        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(
                tzinfo=timezone.utc
            )

        if datetime.now(timezone.utc) > expiry_time:
            clear_password_reset_otp(email)

            return False, (
                "OTP has expired. Please request a new OTP."
            )

        # Verify OTP
        if not verify_password(otp, otp_hash):
            return False, "Incorrect OTP. Please try again."

        return True, "OTP verified successfully."

    except Exception as error:
        print("OTP VERIFICATION ERROR:", repr(error))
        return False, "OTP verification failed. Please try again."

# ==========================================
# RESET PASSWORD
# ==========================================

def reset_password(email, otp, new_password):

    try:
        email = email.strip().lower()

        if len(new_password) < 8:
            return False, (
                "Password must contain at least 8 characters."
            )

        # Verify OTP before changing password
        success, message = verify_reset_otp(email, otp)

        if not success:
            return False, message

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Update database password
        update_user_password(
            email=email,
            password_hash=new_password_hash
        )

        # Clear OTP after successful reset
        clear_password_reset_otp(email)

        return True, (
            "Password reset successfully. Please login."
        )

    except Exception as error:
        print("PASSWORD RESET ERROR:", repr(error))
        return False, "Password reset failed. Please try again."