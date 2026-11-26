
import streamlit as st

from auth.auth_database import initialize_auth_database
from auth.auth_service import (
    register_user,
    login_user,
    send_password_reset_otp,
    verify_reset_otp,
    reset_password
)


def initialize_auth():
    initialize_auth_database()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False

    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False

    if "reset_email" not in st.session_state:
        st.session_state.reset_email = ""


def logout_user():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def show_auth_page():

    initialize_auth()

    if st.session_state.authenticated:
        return True

    st.markdown("""
        <style>
        .auth-title {
            text-align: center;
            color: #FFD600;
            font-size: 34px;
            font-weight: 800;
        }

        .auth-subtitle {
            text-align: center;
            color: #AAAAAA;
            margin-bottom: 25px;
        }

        .auth-brand {
            text-align: center;
            color: white;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 2px;
        }

        div.stButton > button,
        div.stFormSubmitButton > button {
            background: #FFD600;
            color: #111111;
            font-weight: 800;
            border: none;
            border-radius: 9px;
            min-height: 43px;
        }

        div.stButton > button:hover,
        div.stFormSubmitButton > button:hover {
            background: #F0C800;
            color: #000000;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="auth-brand">BIZANALYST-AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="auth-title">Welcome</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="auth-subtitle">'
        'Your intelligent business analytics platform'
        '</div>',
        unsafe_allow_html=True
    )

    login_tab, register_tab, forgot_tab = st.tabs([
        "Login",
        "Register",
        "Forgot Password"
    ])

    # =====================================
    # LOGIN
    # =====================================

    with login_tab:

        st.subheader("Login to your account")

        with st.form("login_form"):

            email = st.text_input(
                "Email address",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            submit = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submit:

                if not email or not password:
                    st.error("Please enter email and password.")

                else:
                    success, message, user = login_user(
                        email,
                        password
                    )

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user

                        st.success(message)
                        st.rerun()

                    else:
                        st.error(message)

    # =====================================
    # REGISTER
    # =====================================

    with register_tab:

        st.subheader("Create your account")

        with st.form("register_form"):

            name = st.text_input(
                "Full name",
                placeholder="Enter your name"
            )

            email = st.text_input(
                "Email address",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Create password",
                type="password",
                placeholder="Minimum 8 characters"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            submit = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submit:

                if not name or not email or not password:
                    st.error("Please fill all required fields.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    success, message = register_user(
                        name,
                        email,
                        password
                    )

                    if success:
                        st.success(message)
                        st.info(
                            "You can now log in using your new account."
                        )
                    else:
                        st.error(message)

    # =====================================
    # FORGOT PASSWORD
    # =====================================

    with forgot_tab:

        st.subheader("🔐 Reset Your Password")

        st.write(
            "Enter your registered email address. "
            "We will send you a six-digit verification OTP."
        )

        with st.form("send_otp_form"):

            reset_email = st.text_input(
                "Registered Email",
                placeholder="Enter your registered email"
            )

            send_otp = st.form_submit_button(
                "📩 Send OTP",
                use_container_width=True
            )

            if send_otp:

                if not reset_email:
                    st.error("Please enter your email address.")

                else:
                    success, message = send_password_reset_otp(
                        reset_email
                    )

                    if success:
                        st.session_state.reset_email = (
                            reset_email.strip().lower()
                        )
                        st.session_state.otp_sent = True
                        st.session_state.otp_verified = False
                        st.success(message)
                    else:
                        st.error(message)

        # OTP verification
        if st.session_state.otp_sent:

            st.divider()
            st.subheader("Verify Email OTP")

            st.caption(
                f"Email: {st.session_state.reset_email}"
            )

            with st.form("verify_otp_form"):

                otp = st.text_input(
                    "6-digit OTP",
                    max_chars=6,
                    placeholder="Enter OTP received in your email"
                )

                verify_button = st.form_submit_button(
                    "Verify OTP",
                    use_container_width=True
                )

                if verify_button:

                    success, message = verify_reset_otp(
                        st.session_state.reset_email,
                        otp
                    )

                    if success:
                        st.session_state.otp_verified = True
                        st.success(message)
                    else:
                        st.error(message)

        # New password
        if st.session_state.otp_verified:

            st.divider()
            st.subheader("Create New Password")

            with st.form("reset_password_form"):

                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter new password"
                )

                confirm_new_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Confirm new password"
                )

                reset_button = st.form_submit_button(
                    "Reset Password",
                    use_container_width=True
                )

                if reset_button:

                    if not new_password or not confirm_new_password:
                        st.error("Please fill both password fields.")

                    elif new_password != confirm_new_password:
                        st.error("Passwords do not match.")

                    else:
                        success, message = reset_password(
                            st.session_state.reset_email,
                            otp,
                            new_password
                        )

                        if success:
                            st.success(message)

                            st.session_state.otp_sent = False
                            st.session_state.otp_verified = False
                            st.session_state.reset_email = ""

                            st.info(
                                "Go to the Login tab and sign in "
                                "with your new password."
                            )
                        else:
                            st.error(message)

    return False
