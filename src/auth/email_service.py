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


def _send_credentials_email_sync(to_email: str, username: str, password: str, user_type: str) -> tuple[bool, Optional[str]]:
    """Internal synchronous email sending function for credentials."""
    try:
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            return False, "Email configuration is missing."
        
        msg = MIMEMultipart('alternative')
        msg['From'] = config.SMTP_FROM_EMAIL or config.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = f"Your {user_type.capitalize()} Account Credentials - SenseLearn"
        
        account_type = "Student" if user_type == "student" else "Tutor"
        
        text_content = f"""
Hello,

Your {account_type} account has been created on SenseLearn. Please find your login credentials below:

Email/Username: {username}
Password: {password}

Please log in and change your password after your first login for security.

Login URL: {config.APP_BASE_URL or 'http://localhost:5000'}/auth

If you did not request this account, please contact support immediately.

Best regards,
SenseLearn Team
"""
        html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #059669;">Your {account_type} Account Credentials</h2>
      <p>Hello,</p>
      <p>Your {account_type} account has been created on SenseLearn. Please find your login credentials below:</p>
      
      <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 10px 0;"><strong>Email/Username:</strong> {username}</p>
        <p style="margin: 10px 0;"><strong>Password:</strong> <code style="background-color: #fff; padding: 5px 10px; border-radius: 3px; font-size: 16px;">{password}</code></p>
      </div>
      
      <p><strong>Important:</strong> Please log in and change your password after your first login for security.</p>
      
      <div style="margin: 30px 0;">
        <a href="{config.APP_BASE_URL or 'http://localhost:5000'}/auth" 
           style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
          Login to Your Account
        </a>
      </div>
      
      <p style="color: #666; font-size: 12px; margin-top: 30px;">
        If you did not request this account, please contact support immediately.
      </p>
      
      <p>Best regards,<br>SenseLearn Team</p>
    </div>
  </body>
</html>
"""
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        
        current_app.logger.info(f"Credentials email sent successfully to {to_email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Failed to send credentials email: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg


def send_credentials_email(to_email: str, username: str, password: str, user_type: str, async_send: bool = True) -> tuple[bool, Optional[str]]:
    """
    Send account credentials email to newly created users.
    
    Args:
        to_email: Recipient email address
        username: Username or email for login
        password: Plain text password (will be shown in email)
        user_type: Type of user ('student' or 'tutor')
        async_send: If True, send email in background thread
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    if async_send:
        def send_in_background():
            try:
                _send_credentials_email_sync(to_email, username, password, user_type)
            except Exception as e:
                current_app.logger.error(f"Background credentials email sending failed: {str(e)}")
        
        thread = threading.Thread(target=send_in_background, daemon=True)
        thread.start()
        return True, None
    
    return _send_credentials_email_sync(to_email, username, password, user_type)
