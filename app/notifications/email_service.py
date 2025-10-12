import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from datetime import datetime
from flask import render_template, current_app

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 use_tls: bool = True, recipients: List[str] = None, subject_template: str = "[DockSafe]"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.recipients = recipients if recipients is not None else []
        self.subject_template = subject_template
    
    def send_email(self, subject: str, html_body: str, text_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email with HTML and optional text body and attachments"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            
            # Create text part
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Create HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {', '.join(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_vulnerability_alert(self, scan_data: Dict) -> bool:
        """Send vulnerability alert email using template"""
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            total_vulns = scan_data.get('total_vulnerabilities', 0)
            critical_count = scan_data.get('critical_count', 0)
            high_count = scan_data.get('high_count', 0)
            medium_count = scan_data.get('medium_count', 0)
            low_count = scan_data.get('low_count', 0)
            scan_time = scan_data.get('scan_timestamp', datetime.utcnow().isoformat())
            
            # Determine severity and emoji
            if critical_count > 0:
                severity = 'CRITICAL'
                emoji = '🚨'
            elif high_count > 0:
                severity = 'HIGH'
                emoji = '⚠️'
            elif medium_count > 0:
                severity = 'MEDIUM'
                emoji = '⚡'
            else:
                severity = 'LOW'
                emoji = 'ℹ️'
            
            subject = f"{self.subject_template} {emoji} {severity} Vulnerabilities Found in {image_name}:{image_tag}"
            
            # Render HTML template
            html_body = render_template('emails/vulnerability_alert.html',
                emoji=emoji,
                severity=severity,
                image_name=image_name,
                image_tag=image_tag,
                scan_time=scan_time,
                total_vulns=total_vulns,
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count
            )
            
            # Create text version
            text_body = f"""
DockSafe Vulnerability Alert - {severity}

{emoji} Security vulnerabilities have been detected in your container image.

Image Details:
- Image: {image_name}:{image_tag}
- Scan Time: {scan_time}
- Total Vulnerabilities: {total_vulns}

Severity Breakdown:
🔴 Critical: {critical_count}
🟠 High: {high_count}
🟡 Medium: {medium_count}
🟢 Low: {low_count}

Action Required:
Please review the vulnerabilities and take appropriate action to secure your container image.

For detailed information, please check the DockSafe dashboard.

---
This is an automated message from DockSafe Container Image Vulnerability Scanner.
"""
            
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error creating vulnerability alert email: {str(e)}")
            return False
    
    def send_scan_completion_notification(self, scan_data: Dict) -> bool:
        """Send scan completion notification using template"""
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            status = scan_data.get('scan_status', 'Unknown')
            duration = scan_data.get('scan_duration_seconds', 0)
            
            # Determine emoji and status color
            if status.lower() == 'success':
                emoji = '✅'
                status_color = 'success'
            elif status.lower() == 'failed':
                emoji = '❌'
                status_color = 'danger'
            else:
                emoji = 'ℹ️'
                status_color = 'info'
            
            subject = f"{self.subject_template} {emoji} Scan {status.title()}: {image_name}:{image_tag}"
            
            # Render HTML template
            html_body = render_template('emails/scan_completion.html',
                emoji=emoji,
                status=status,
                status_color=status_color,
                image_name=image_name,
                image_tag=image_tag,
                duration=duration
            )
            
            # Create text version
            text_body = f"""
DockSafe Scan Completion

{emoji} Scan {status} for {image_name}:{image_tag}

Duration: {duration} seconds

Please check the DockSafe dashboard for detailed results.

---
This is an automated message from DockSafe Container Image Vulnerability Scanner.
"""
            
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error creating scan completion email: {str(e)}")
            return False
    
    def send_scan_failure_notification(self, scan_data: Dict) -> bool:
        """Send scan failure notification using template"""
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            status = scan_data.get('scan_status', 'Unknown')
            scanner_type = scan_data.get('scanner_type', 'Unknown')
            
            subject = f"[DockSafe] Scan Failed - {image_name}:{image_tag}"
            
            # Create HTML version using template
            html_body = render_template('emails/scan_failure.html', 
                                       image_name=image_name,
                                       image_tag=image_tag,
                                       status=status,
                                       scanner_type=scanner_type,
                                       scan_timestamp=scan_data.get('scan_timestamp', datetime.utcnow().isoformat()),
                                       year=datetime.now().year)
            
            # Create text version
            text_body = f"""
DockSafe Scan Failure Notification

❌ Scan Failed: {image_name}:{image_tag}

Scan Details:
- Image: {image_name}:{image_tag}
- Scanner: {scanner_type}
- Status: {status}
- Time: {scan_data.get('scan_timestamp', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))}

Please check the scan logs for more details about the failure.

---
This notification was sent by DockSafe Container Image Vulnerability Scanner.
"""
            
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error creating scan failure email: {str(e)}")
            return False
    
    def send_test_message(self) -> bool:
        """Send test email using template"""
        try:
            subject = f"{self.subject_template} 🛡️ Test Email - DockSafe Integration"
            
            # Render HTML template
            html_body = render_template('emails/test_email.html',
                sent_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                recipients=', '.join(self.recipients),
                smtp_server=self.smtp_server,
                smtp_port=self.smtp_port
            )
            
            # Create text version
            text_body = f"""
DockSafe Test Email

✅ Email Integration Test Successful!

Your DockSafe email notifications are configured correctly.

Test Details:
- Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- Recipients: {', '.join(self.recipients)}
- SMTP Server: {self.smtp_server}:{self.smtp_port}

If you received this email, your DockSafe email notifications are configured correctly!

---
This is a test message from DockSafe Container Image Vulnerability Scanner.
"""
            
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error creating test email: {str(e)}")
            return False

def create_email_service(smtp_server: str, smtp_port: int, username: str, password: str,
                         recipients: List[str]) -> Optional[EmailNotificationService]:
    """Create EmailNotificationService instance"""
    try:
        if not smtp_server or not username or not password or not recipients:
            logger.error("Missing required email configuration parameters")
            return None
        
        return EmailNotificationService(smtp_server, smtp_port, username, password, recipients)
        
    except Exception as e:
        logger.error(f"Error creating email service: {str(e)}")
        return None