import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class SlackNotificationService:
    
    def __init__(self, webhook_url: str, channel: str = None):
        self.webhook_url = webhook_url
        self.channel = channel
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def send_message(self, message: str, blocks: List[Dict] = None, **kwargs) -> bool:
        """
        Send a message to Slack
        
        Args:
            message: The message text to send
            blocks: Optional Slack blocks for rich formatting
            **kwargs: Additional payload parameters
        """
        try:
            payload = {
                'text': message,
                'channel': self.channel
            }
            
            if blocks:
                payload['blocks'] = blocks
            
            payload.update(kwargs)
            
            response = self.session.post(
                self.webhook_url,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack message sent successfully to {self.channel}")
                return True
            else:
                logger.error(f"Failed to send Slack message: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack message: {str(e)}")
            return False
    
    def send_vulnerability_alert(self, scan_data: Dict) -> bool:
        """
        Send vulnerability alert to Slack
        
        Args:
            scan_data: Dictionary containing scan results
        """
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            total_vulns = scan_data.get('total_vulnerabilities', 0)
            critical_count = scan_data.get('critical_count', 0)
            high_count = scan_data.get('high_count', 0)
            medium_count = scan_data.get('medium_count', 0)
            low_count = scan_data.get('low_count', 0)
            scan_time = scan_data.get('scan_timestamp', datetime.utcnow().isoformat())
            
            if critical_count > 0:
                color = 'danger'
                emoji = '🚨'
                urgency = 'CRITICAL'
            elif high_count > 0:
                color = 'warning'
                emoji = '⚠️'
                urgency = 'HIGH'
            elif medium_count > 0:
                color = '#FFA500'
                emoji = '⚡'
                urgency = 'MEDIUM'
                color = 'good'
                emoji = '✅'
                urgency = 'LOW'
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} DockSafe Vulnerability Alert - {urgency}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Image:*\n{image_name}:{image_tag}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Scan Time:*\n{scan_time}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Vulnerabilities:*\n{total_vulns}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity Breakdown:*\n🔴 Critical: {critical_count}\n🟠 High: {high_count}\n🟡 Medium: {medium_count}\n🟢 Low: {low_count}"
                        }
                    ]
                }
            ]
            
            if total_vulns > 0:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Full Report"
                            },
                            "url": "http://localhost:5000/reports",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Dashboard"
                            },
                            "url": "http://localhost:5000/dashboard"
                        }
                    ]
                })
            
            fallback_text = f"{emoji} DockSafe Alert: {total_vulns} vulnerabilities found in {image_name}:{image_tag}"
            
            return self.send_message(
                message=fallback_text,
                blocks=blocks,
                color=color
            )
            
        except Exception as e:
            logger.error(f"Error creating vulnerability alert: {str(e)}")
    
    def send_scan_completion_notification(self, scan_data: Dict) -> bool:
        """
        Send scan completion notification to Slack
        
        Args:
            scan_data: Dictionary containing scan results
        """
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            status = scan_data.get('scan_status', 'Unknown')
            duration = scan_data.get('scan_duration_seconds', 0)
            
            if status.lower() == 'success':
                emoji = '✅'
                message = f"Scan completed successfully for {image_name}:{image_tag}"
                color = 'good'
            elif status.lower() == 'failed':
                emoji = '❌'
                message = f"Scan failed for {image_name}:{image_tag}"
                color = 'danger'
            else:
                emoji = 'ℹ️'
                message = f"Scan {status} for {image_name}:{image_tag}"
                color = '#36a64f'
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{message}*\nDuration: {duration}s"
                    }
                }
            ]
            
            return self.send_message(
                message=message,
                blocks=blocks,
                color=color
            )
            
        except Exception as e:
            logger.error(f"Error sending scan completion notification: {str(e)}")
    
    def send_scan_failure_notification(self, scan_data: Dict) -> bool:
        """
        Send scan failure notification to Slack
        
        Args:
            scan_data: Dictionary containing scan failure information
        """
        try:
            image_name = scan_data.get('image_name', 'Unknown')
            image_tag = scan_data.get('image_tag', 'latest')
            status = scan_data.get('scan_status', 'Unknown')
            scanner_type = scan_data.get('scanner_type', 'Unknown')
            
            emoji = '❌'
            message = f"Scan failed for {image_name}:{image_tag}"
            color = "danger"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{emoji} {message}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Image:*\n{image_name}:{image_tag}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Scanner:*\n{scanner_type}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{status}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Please check the scan logs for more details."
                        }
                    ]
                }
            ]
            
            return self.send_message(
                message=message,
                blocks=blocks,
                color=color
            )
            
        except Exception as e:
            logger.error(f"Error sending scan failure notification: {str(e)}")
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify Slack integration
        """
        try:
            test_message = "🛡️ DockSafe Test Message - Slack integration is working!"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{test_message}*\n\nThis is a test message to verify your Slack webhook configuration."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        }
                    ]
                }
            ]
            
            return self.send_message(
                message=test_message,
                blocks=blocks,
                color='good'
            )
            
        except Exception as e:
            logger.error(f"Error sending test message: {str(e)}")

def create_slack_service(webhook_url: str, channel: str = None) -> Optional[SlackNotificationService]:
    """
    Create a SlackNotificationService instance
    
    Args:
        webhook_url: Slack webhook URL
        channel: Optional channel name
        
    Returns:
        SlackNotificationService instance or None if webhook_url is invalid
    """
    if not webhook_url or not webhook_url.startswith('https://hooks.slack.com/'):
        logger.error("Invalid Slack webhook URL")
        return None
    
    return SlackNotificationService(webhook_url, channel)
