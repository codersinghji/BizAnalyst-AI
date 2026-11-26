
import os
import smtplib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

gmail = os.getenv("GMAIL_ADDRESS")
password = os.getenv("GMAIL_APP_PASSWORD")

try:
    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        timeout=30
    ) as server:

        print("Connected to Gmail SSL.")

        server.login(gmail, password)

        print("SUCCESS: Gmail authentication working!")

except smtplib.SMTPAuthenticationError as error:
    print("Authentication rejected:", error.smtp_code)
    print(error.smtp_error.decode(errors="replace"))

except Exception as error:
    print("Error:", type(error).__name__, str(error))
