from typing import Dict, List, Optional
from flask import current_app
from .slack_service import create_slack_service
from .email_service import create_email_service
import logging
import os

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self):
        self.slack_services = []
        self.teams_services = []
        self.email_services = []
        self._initialize_services()

    def _initialize_services(self):
        try:
            from app.models import NotificationConfiguration

            configs = NotificationConfiguration.query.filter_by(is_active=True).all()

            for config in configs:
                if config.type == "chat" and config.service == "Slack":
                    if config.webhook_url:
                        slack_service = create_slack_service(
                            config.webhook_url, config.channel
                        )
                        if slack_service:
                            slack_service.config = config
                            self.slack_services.append(slack_service)
                            logger.info(
                                f"Slack service initialized for config: {config.name}"
                            )
                        else:
                            logger.warning(
                                f"Failed to initialize Slack service for config: {config.name}"
                            )

                elif config.type == "chat" and config.service == "Teams":
                    logger.info(f"Teams service configuration found: {config.name}")

                elif config.type == "email":
                    email_service = create_email_service(
                        smtp_server=config.additional_config.get(
                            "smtp_server", "smtp.gmail.com"
                        ),
                        smtp_port=config.additional_config.get("smtp_port", 587),
                        username=config.additional_config.get("username", ""),
                        password=config.additional_config.get("password", ""),
                        recipients=config.channel or "",
                        subject_template=config.subject_template or "[DockSafe]",
                    )
                    if email_service:
                        email_service.config = config
                        self.email_services.append(email_service)
                        logger.info(
                            f"Email service initialized for config: {config.name}"
                        )
                    else:
                        logger.warning(
                            f"Failed to initialize Email service for config: {config.name}"
                        )

            logger.info(
                f"Initialized {len(self.slack_services)} Slack services, {len(self.email_services)} Email services"
            )

        except Exception as e:
            logger.error(f"Error initializing notification services: {str(e)}")
            self._initialize_from_env()

    def _initialize_from_env(self):
        slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        slack_channel = os.environ.get("SLACK_CHANNEL")

        if slack_webhook:
            slack_service = create_slack_service(slack_webhook, slack_channel)
            if slack_service:
                self.slack_services.append(slack_service)
                logger.info("Slack service initialized from environment variables")

    def send_vulnerability_alert(self, scan_data: Dict) -> Dict[str, List[Dict]]:
        results = {"slack": [], "teams": [], "email": []}

        should_send = self._should_send_alert(scan_data)
        if not should_send:
            logger.debug("Alert not sent - severity threshold not met")

        for slack_service in self.slack_services:
            try:
                success = slack_service.send_vulnerability_alert(scan_data)
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Alert sent successfully"
                        if success
                        else "Failed to send alert",
                    }
                )
                logger.info(
                    f"Slack vulnerability alert ({slack_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(f"Error sending Slack vulnerability alert: {str(e)}")
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

        for email_service in self.email_services:
            try:
                success = email_service.send_vulnerability_alert(scan_data)
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Alert sent successfully"
                        if success
                        else "Failed to send alert",
                    }
                )
                logger.info(
                    f"Email vulnerability alert ({email_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(f"Error sending Email vulnerability alert: {str(e)}")
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

    def send_scan_completion_notification(
        self, scan_data: Dict
    ) -> Dict[str, List[Dict]]:
        results = {"slack": [], "teams": [], "email": []}

        for slack_service in self.slack_services:
            try:
                success = slack_service.send_scan_completion_notification(scan_data)
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Notification sent successfully"
                        if success
                        else "Failed to send notification",
                    }
                )
                logger.info(
                    f"Slack scan completion notification ({slack_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(
                    f"Error sending Slack scan completion notification: {str(e)}"
                )
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

        for email_service in self.email_services:
            try:
                success = email_service.send_scan_completion_notification(scan_data)
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Notification sent successfully"
                        if success
                        else "Failed to send notification",
                    }
                )
                logger.info(
                    f"Email scan completion notification ({email_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(
                    f"Error sending Email scan completion notification: {str(e)}"
                )
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

    def send_test_message(self) -> Dict[str, List[Dict]]:
        results = {"slack": [], "teams": [], "email": []}

        for slack_service in self.slack_services:
            try:
                success = slack_service.send_test_message()
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Test message sent successfully"
                        if success
                        else "Failed to send test message",
                    }
                )
                logger.info(
                    f"Slack test message ({slack_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(f"Error sending Slack test message: {str(e)}")
                results["slack"].append(
                    {
                        "config_name": getattr(slack_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

        for email_service in self.email_services:
            try:
                success = email_service.send_test_message()
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": success,
                        "message": "Test message sent successfully"
                        if success
                        else "Failed to send test message",
                    }
                )
                logger.info(
                    f"Email test message ({email_service.config.name}): {'sent' if success else 'failed'}"
                )
            except Exception as e:
                logger.error(f"Error sending Email test message: {str(e)}")
                results["email"].append(
                    {
                        "config_name": getattr(email_service.config, "name", "Unknown"),
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

    def _should_send_alert(self, scan_data: Dict) -> bool:
        """
        Determine if an alert should be sent based on scan data

        Args:
            scan_data: Dictionary containing scan results

        Returns:
            bool: True if alert should be sent, False otherwise
        """
        return scan_data.get("total_vulnerabilities", 0) > 0

    def is_slack_configured(self) -> bool:
        return len(self.slack_services) > 0

    def is_email_configured(self) -> bool:
        return len(self.email_services) > 0

    def get_slack_channels(self) -> List[str]:
        channels = []
        for slack_service in self.slack_services:
            if slack_service.channel:
                channels.append(slack_service.channel)

    def get_email_recipients(self) -> List[str]:
        recipients = []
        for email_service in self.email_services:
            recipients.extend(email_service.recipients)

    def refresh_configurations(self):
        logger.info("Refreshing notification configurations...")
        self.slack_services = []
        self.teams_services = []
        self.email_services = []
        self._initialize_services()


notification_manager = None


def get_notification_manager() -> NotificationManager:
    global notification_manager
    if notification_manager is None:
        notification_manager = NotificationManager()
    return notification_manager


def send_vulnerability_alert(scan_data: Dict) -> Dict[str, bool]:
    """
    Send vulnerability alert

    Args:
        scan_data: Dictionary containing scan results

    Returns:
        Dict[str, bool]: Results of sending alerts
    """
    return get_notification_manager().send_vulnerability_alert(scan_data)


def send_scan_completion_notification(scan_data: Dict) -> Dict[str, bool]:
    """
    Send scan completion notification

    Args:
        scan_data: Dictionary containing scan results

    Returns:
        Dict[str, bool]: Results of sending notifications
    """
    return get_notification_manager().send_scan_completion_notification(scan_data)


def send_test_message() -> Dict[str, bool]:
    """
    Send test message

    Returns:
        Dict[str, bool]: Results of sending test messages
    """
    return get_notification_manager().send_test_message()
