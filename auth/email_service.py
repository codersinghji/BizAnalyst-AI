
import base64

from pathlib import Path
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


# ==========================================
# GET GMAIL SERVICE
# ==========================================

def get_gmail_service():

    credentials = None

    # Load previously authorized credentials
    if TOKEN_FILE.exists():

        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES
        )

    # Refresh or obtain authorization
    if credentials and credentials.expired and credentials.refresh_token:

        credentials.refresh(Request())

    elif not credentials or not credentials.valid:

        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "credentials.json not found in project root."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0,
            open_browser=True
        )

    # Save authorization token
    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8"
    )

    # Build Gmail API service
    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


# ==========================================
# SEND EMAIL
# ==========================================

def send_email(to_email, subject, body):

    try:

        service = get_gmail_service()

        message = EmailMessage()

        message["To"] = to_email
        message["Subject"] = subject

        message.set_content(body)

        # Encode email in Base64 URL-safe format
        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        request_body = {
            "raw": encoded_message
        }

        # Send email through Gmail API
        result = service.users().messages().send(
            userId="me",
            body=request_body
        ).execute()

        print("GMAIL MESSAGE SENT:", result.get("id"))

        return True, "Email sent successfully."

    except Exception as error:

        print("GMAIL API ERROR:", type(error).__name__, str(error))

        return False, (
            f"Email sending failed: {type(error).__name__}: {error}"
        )
