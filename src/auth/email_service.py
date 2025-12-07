"""
Email service for sending OTP emails via SMTP.
Optimized with background threading for faster API responses.
"""
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from flask import current_app

from src.config import config


def _send_email_sync(to_email: str, otp: str, purpose: str) -> tuple[bool, Optional[str]]:
    """Internal synchronous email sending function."""
    try:
        # Validate email configuration
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            return False, "Email configuration is missing."
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config.SMTP_FROM_EMAIL or config.SMTP_USERNAME
        msg['To'] = to_email
        
        if purpose == "password_reset":
            msg['Subject'] = "Password Reset OTP - SenseLearn"
            text_content = f"""
Hello,

You have requested to reset your password. Please use the following OTP code:

{otp}

This code will expire in {config.OTP_VALIDITY_MINUTES} minutes.

If you did not request this, please ignore this email.

Best regards,
SenseLearn Team
"""
            html_content = f"""
<html>
  <body>
    <h2>Password Reset OTP</h2>
    <p>Hello,</p>
    <p>You have requested to reset your password. Please use the following OTP code:</p>
    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0;">
      {otp}
    </div>
    <p>This code will expire in <strong>{config.OTP_VALIDITY_MINUTES} minutes</strong>.</p>
    <p>If you did not request this, please ignore this email.</p>
    <p>Best regards,<br>SenseLearn Team</p>
  </body>
</html>
"""
        else:  # verification
            msg['Subject'] = "Email Verification OTP - SenseLearn"
            text_content = f"""
Hello,

Thank you for registering with SenseLearn! Please verify your email address using the following OTP code:

{otp}

This code will expire in {config.OTP_VALIDITY_MINUTES} minutes.

If you did not create an account, please ignore this email.

Best regards,
SenseLearn Team
"""
            html_content = f"""
<html>
  <body>
    <h2>Email Verification</h2>
    <p>Hello,</p>
    <p>Thank you for registering with SenseLearn! Please verify your email address using the following OTP code:</p>
    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0;">
      {otp}
    </div>
    <p>This code will expire in <strong>{config.OTP_VALIDITY_MINUTES} minutes</strong>.</p>
    <p>If you did not create an account, please ignore this email.</p>
    <p>Best regards,<br>SenseLearn Team</p>
  </body>
</html>
"""
        
        # Add both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        
        current_app.logger.info(f"OTP email sent successfully to {to_email}")
        return True, None
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error occurred: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg


def send_otp_email(to_email: str, otp: str, purpose: str = "verification", async_send: bool = True) -> tuple[bool, Optional[str]]:
    """
    Send OTP email to the user.
    
    Args:
        to_email: Recipient email address
        otp: The OTP code to send
        purpose: Purpose of the email ('verification' or 'password_reset')
        async_send: If True, send email in background thread (non-blocking, faster API response)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
        For async sends, returns (True, None) immediately and sends email in background
    """
    # For async sending (default), start background thread and return immediately
    if async_send:
        def send_in_background():
            try:
                _send_email_sync(to_email, otp, purpose)
            except Exception as e:
                current_app.logger.error(f"Background email sending failed: {str(e)}")
        
        thread = threading.Thread(target=send_in_background, daemon=True)
        thread.start()
        # Return success immediately - email is being sent in background
        return True, None
    
    # For synchronous sending (when we need to wait for result)
    return _send_email_sync(to_email, otp, purpose)
