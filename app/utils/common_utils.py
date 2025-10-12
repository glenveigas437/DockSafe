import logging
import json
from typing import Dict, Any, Optional
from flask import jsonify, request


class LoggingUtils:
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @staticmethod
    def log_request(
        logger: logging.Logger,
        endpoint: str,
        method: str,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        log_data = {
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            **kwargs,
        }
        logger.info(f"Request: {json.dumps(log_data)}")

    @staticmethod
    def log_error(logger: logging.Logger, error: Exception, context: str = ""):
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)

    @staticmethod
    def log_scan_event(
        logger: logging.Logger,
        event: str,
        image_name: str,
        image_tag: str,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        log_data = {
            "event": event,
            "image_name": image_name,
            "image_tag": image_tag,
            "user_id": user_id,
            **kwargs,
        }
        logger.info(f"Scan Event: {json.dumps(log_data)}")


class JSONUtils:
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def safe_json_dumps(obj: Any, default: str = "{}") -> str:
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def extract_json_from_request() -> Dict[str, Any]:
        try:
            return request.get_json() or {}
        except Exception:
            return {}
            return {}


class ErrorHandlingUtils:
    @staticmethod
    def handle_database_error(
        error: Exception, logger: logging.Logger
    ) -> Dict[str, Any]:
        LoggingUtils.log_error(logger, error, "Database operation")
        return {
            "success": False,
            "error": "Database operation failed",
            "error_code": 500,
        }

    @staticmethod
    def handle_validation_error(
        error: Exception, logger: logging.Logger
    ) -> Dict[str, Any]:
        LoggingUtils.log_error(logger, error, "Validation")
        return {"success": False, "error": "Validation failed", "error_code": 400}

    @staticmethod
    def handle_permission_error(
        error: Exception, logger: logging.Logger
    ) -> Dict[str, Any]:
        LoggingUtils.log_error(logger, error, "Permission check")
        return {
            "success": False,
            "error": "Insufficient permissions",
            "error_code": 403,
        }

    @staticmethod
    def handle_not_found_error(resource: str, logger: logging.Logger) -> Dict[str, Any]:
        logger.warning(f"Resource not found: {resource}")
        return {"success": False, "error": f"{resource} not found", "error_code": 404}


class ConfigUtils:
    @staticmethod
    def get_scanner_config() -> Dict[str, Any]:
        return {
            "scanner_type": "trivy",
            "timeout": 300,
            "vulnerability_threshold": "HIGH",
        }

    @staticmethod
    def get_notification_config() -> Dict[str, Any]:
        return {
            "notify_critical": True,
            "notify_high": True,
            "notify_medium": False,
            "notify_low": False,
            "notify_scan_failed": True,
            "notify_daily_summary": False,
        }

    @staticmethod
    def get_default_group_settings() -> Dict[str, Any]:
        return {
            "scanner_type": "trivy",
            "vulnerability_threshold": "HIGH",
            "scan_timeout": 300,
            "enabled": True,
        }
