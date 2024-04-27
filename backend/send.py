import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# Configuration for the email client
conf = ConnectionConfig(
    MAIL_USERNAME="ronitvirwani1@gmail.com",  # Use your email username
    MAIL_PASSWORD="azbhblplcwcgtnsr",  # Use your email password
    MAIL_FROM="ronitvirwani1@gmail.com",  # Use the email you're sending from
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",  # Use your SMTP server
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Email message details
message = MessageSchema(
    subject="Test Email from FastAPI-Mail",
    recipients=["britster032@gmail.com"],  # Change to your recipient's email address
    body="<p>This is a test email sent from a standalone script using FastAPI-Mail.</p>",
    subtype="html"
)

# Function to send an email
async def send_email():
    fm = FastMail(conf)
    await fm.send_message(message)
    print("Email has been sent.")

# Running the email sending function
loop = asyncio.get_event_loop()
loop.run_until_complete(send_email())







