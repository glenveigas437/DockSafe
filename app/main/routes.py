from flask import (
    render_template,
    current_app,
    jsonify,
    redirect,
    url_for,
    session,
    request,
)
from app.main import bp
from app.scanner.service import ScannerService
from app.decorators import login_required
from app.models import User, VulnerabilityScan, Group
from app import db
from sqlalchemy import func, and_
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@bp.route("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            VulnerabilityScan.query.limit(1).all()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check Redis connection (if using Redis)
        redis_status = "healthy"  # Placeholder - implement Redis check if needed

        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {"database": db_status, "redis": redis_status},
        }

        # If any service is unhealthy, return 503
        if "unhealthy" in db_status or "unhealthy" in redis_status:
            health_data["status"] = "unhealthy"
            return jsonify(health_data), 503

        return jsonify(health_data), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                }
            ),
            503,
        )


@bp.route("/")
@login_required
def index():
    """Home page - redirect to group selection if user has no groups"""
    user_id = session.get("user_id")
    selected_group_id = session.get("selected_group_id")

    if user_id:
        user = User.query.get(user_id)
        if user and len(list(user.groups)) == 0:
            return redirect(url_for("groups.select_group"))

        # Get user's groups for the modal
        user_groups = []
        if user:
            for group in user.groups:
                user_groups.append(
                    {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "member_count": len(list(group.members)),
                        "scan_count": len(list(group.vulnerability_scans))
                        if hasattr(group, "vulnerability_scans")
                        else 0,
                    }
                )

    # Calculate statistics for homepage
    stats = {}
    if selected_group_id:
        # Get real statistics from database for selected group
        total_scans = VulnerabilityScan.query.filter(
            VulnerabilityScan.group_id == selected_group_id
        ).count()

        successful_scans = VulnerabilityScan.query.filter(
            and_(
                VulnerabilityScan.group_id == selected_group_id,
                VulnerabilityScan.scan_status == "SUCCESS",
            )
        ).count()

        success_rate = (successful_scans / total_scans * 100) if total_scans > 0 else 0

        # Get vulnerability counts
        critical_count = (
            db.session.query(func.sum(VulnerabilityScan.critical_count))
            .filter(VulnerabilityScan.group_id == selected_group_id)
            .scalar()
            or 0
        )

        high_count = (
            db.session.query(func.sum(VulnerabilityScan.high_count))
            .filter(VulnerabilityScan.group_id == selected_group_id)
            .scalar()
            or 0
        )

        medium_count = (
            db.session.query(func.sum(VulnerabilityScan.medium_count))
            .filter(VulnerabilityScan.group_id == selected_group_id)
            .scalar()
            or 0
        )

        low_count = (
            db.session.query(func.sum(VulnerabilityScan.low_count))
            .filter(VulnerabilityScan.group_id == selected_group_id)
            .scalar()
            or 0
        )

        stats = {
            "total_scans": total_scans,
            "success_rate": round(success_rate, 1),
            "critical_issues": critical_count,
            "high_severity": high_count,
            "medium_severity": medium_count,
            "low_severity": low_count,
        }
    else:
        # If no group selected, show empty stats
        stats = {
            "total_scans": 0,
            "success_rate": 0,
            "critical_issues": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
        }

    # Check if we should show the group selection modal
    # Only show if user has multiple groups AND no group is selected
    show_group_modal = (
        request.args.get("show_group_modal") == "true"
        and len(user_groups) > 1
        and not selected_group_id
    )

    return render_template(
        "index.html",
        user_groups=user_groups,
        show_group_modal=show_group_modal,
        selected_group_id=selected_group_id,
        user=user,
        stats=stats,
    )


@bp.route("/health")
def health():
    """Health check endpoint"""
    try:
        # Check scanner availability
        scanner_service = ScannerService()
        scanner_available = scanner_service.is_scanner_available()

        return (
            jsonify(
                {
                    "status": "healthy",
                    "scanner_available": scanner_available,
                    "version": "1.0.0",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@bp.route("/about")
@login_required
def about():
    return render_template("about.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    return redirect("/groups/")
