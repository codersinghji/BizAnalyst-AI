
from auth.email_service import send_email

MY_EMAIL = "singhravishekh91@gmail.com"

success, message = send_email(
    to_email=MY_EMAIL,
    subject="BizAnalyst AI - Gmail OAuth2 Test",
    body="""
Hello!

Your BizAnalyst AI Gmail API integration is working.

OAuth2 authorization and email sending were successful.

Regards,
BizAnalyst AI Team
"""
)

if success:
    print("\nSUCCESS:", message)
    print("Check your Gmail inbox.")
else:
    print("\nFAILED:", message)
