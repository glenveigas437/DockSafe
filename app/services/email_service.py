import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for
import secrets
import string


class EmailService:
    """Service to handle email operations including verification"""

    SENDER_EMAIL = "noreply.docksafe@gmail.com"

    @staticmethod
    def generate_verification_token():
        """Generate a secure verification token"""
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )

    @staticmethod
    def send_verification_email(user_email, verification_token, user_name=None):
        """Send email verification email"""
        try:
            # Create verification link - handle both request context and standalone usage
            try:
                verification_url = url_for(
                    "auth.verify_email", token=verification_token, _external=True
                )
            except RuntimeError:
                # Fallback when not in request context
                verification_url = (
                    f"http://localhost:5000/auth/verify-email/{verification_token}"
                )

            # Email content
            subject = "Verify Your DockSafe Email Address"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Email Verification</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔒 DockSafe</h1>
                        <h2>Email Verification Required</h2>
                    </div>
                    <div class="content">
                        <p>Hello {user_name or 'User'},</p>
                        
                        <p>Thank you for signing up with DockSafe! To complete your registration and secure your account, please verify your email address by clicking the button below:</p>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </div>
                        
                        <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace;">{verification_url}</p>
                        
                        <p><strong>Important:</strong></p>
                        <ul>
                            <li>This verification link will expire in 24 hours</li>
                            <li>If you didn't create a DockSafe account, please ignore this email</li>
                            <li>For security reasons, never share this verification link with anyone</li>
                        </ul>
                        
                        <p>If you have any questions or need assistance, please contact our support team.</p>
                        
                        <p>Best regards,<br>The DockSafe Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from noreply.docksafe@gmail.com</p>
                        <p>© 2025 DockSafe. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            DockSafe Email Verification
            
            Hello {user_name or 'User'},
            
            Thank you for signing up with DockSafe! To complete your registration and secure your account, please verify your email address by visiting the following link:
            
            {verification_url}
            
            Important:
            - This verification link will expire in 24 hours
            - If you didn't create a DockSafe account, please ignore this email
            - For security reasons, never share this verification link with anyone
            
            If you have any questions or need assistance, please contact our support team.
            
            Best regards,
            The DockSafe Team
            
            This email was sent from noreply.docksafe@gmail.com
            © 2025 DockSafe. All rights reserved.
            """

            # Send email
            EmailService._send_email(user_email, subject, html_body, text_body)
            return True

        except Exception as e:
            current_app.logger.error(f"Error sending verification email: {e}")
            return False

    @staticmethod
    def send_welcome_email(user_email, user_name=None):
        """Send welcome email after successful verification"""
        try:
            subject = "Welcome to DockSafe! 🎉"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to DockSafe</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 DockSafe</h1>
                        <h2>Welcome Aboard!</h2>
                    </div>
                    <div class="content">
                        <p>Hello {user_name or 'User'},</p>
                        
                        <p>Congratulations! Your email has been successfully verified and your DockSafe account is now active.</p>
                        
                        <p>You can now:</p>
                        <ul>
                            <li>🔍 Scan your Docker images for vulnerabilities</li>
                            <li>📊 View detailed security reports</li>
                            <li>🔔 Set up notifications for security alerts</li>
                            <li>👥 Collaborate with your team</li>
                            <li>📈 Track your security metrics</li>
                        </ul>
                        
                        <p>Ready to get started? Log in to your account and begin securing your Docker containers!</p>
                        
                        <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team.</p>
                        
                        <p>Happy scanning!<br>The DockSafe Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from noreply.docksafe@gmail.com</p>
                        <p>© 2025 DockSafe. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            Welcome to DockSafe!
            
            Hello {user_name or 'User'},
            
            Congratulations! Your email has been successfully verified and your DockSafe account is now active.
            
            You can now:
            - Scan your Docker images for vulnerabilities
            - View detailed security reports
            - Set up notifications for security alerts
            - Collaborate with your team
            - Track your security metrics
            
            Ready to get started? Log in to your account and begin securing your Docker containers!
            
            If you have any questions or need help getting started, don't hesitate to reach out to our support team.
            
            Happy scanning!
            The DockSafe Team
            
            This email was sent from noreply.docksafe@gmail.com
            © 2025 DockSafe. All rights reserved.
            """

            EmailService._send_email(user_email, subject, html_body, text_body)
            return True

        except Exception as e:
            current_app.logger.error(f"Error sending welcome email: {e}")
            return False

    @staticmethod
    def _send_email(to_email, subject, html_body, text_body):
        """Internal method to send email"""
        try:
            # Get SMTP configuration from Flask config
            smtp_server = current_app.config.get(
                "DOCSAFE_EMAIL_SMTP_SERVER", "smtp.gmail.com"
            )
            smtp_port = current_app.config.get("DOCSAFE_EMAIL_SMTP_PORT", 587)
            smtp_username = current_app.config.get(
                "DOCSAFE_EMAIL_USERNAME", "noreply.docksafe@gmail.com"
            )
            smtp_password = current_app.config.get("DOCSAFE_EMAIL_PASSWORD")
            use_tls = current_app.config.get("DOCSAFE_EMAIL_USE_TLS", True)

            # Check if SMTP password is configured
            if not smtp_password:
                current_app.logger.warning(
                    "SMTP password not configured. Email will be simulated."
                )
                return EmailService._simulate_email(
                    to_email, subject, html_body, text_body
                )

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = EmailService.SENDER_EMAIL
            msg["To"] = to_email

            # Create text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email via SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

            current_app.logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            current_app.logger.error(f"❌ Error sending email to {to_email}: {e}")
            # Fallback to simulation if SMTP fails
            return EmailService._simulate_email(to_email, subject, html_body, text_body)

    @staticmethod
    def _simulate_email(to_email, subject, html_body, text_body):
        """Simulate email sending for testing/fallback"""
        try:
            # Log the email details
            current_app.logger.info(f"📧 EMAIL SIMULATION:")
            current_app.logger.info(f"   To: {to_email}")
            current_app.logger.info(f"   From: {EmailService.SENDER_EMAIL}")
            current_app.logger.info(f"   Subject: {subject}")

            # Extract verification link if present
            verification_link = "Not found"
            if 'href="' in html_body:
                try:
                    verification_link = html_body.split('href="')[1].split('"')[0]
                except:
                    pass

            current_app.logger.info(f"   Verification Link: {verification_link}")

            # Print to console for easy testing
            print(f"\n{'='*60}")
            print(f"📧 EMAIL SIMULATION")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"From: {EmailService.SENDER_EMAIL}")
            print(f"Subject: {subject}")
            print(f"\n📧 Email would be sent successfully!")
            print(f"🔗 Verification link: {verification_link}")
            print(f"{'='*60}\n")

            return True

        except Exception as e:
            current_app.logger.error(f"Error in _simulate_email: {e}")
            return False
