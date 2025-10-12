from app.models import VulnerabilityScan, Vulnerability, ScanException
from sqlalchemy import func, and_
from app.constants import DatabaseConstants, SystemConstants
from app import db


class ScanMapper:
    @staticmethod
    def create_scan(image_name, image_tag, scanner_type, group_id, created_by):
        scan = VulnerabilityScan(
            image_name=image_name,
            image_tag=image_tag,
            scanner_type=scanner_type,
            group_id=group_id,
            created_by=created_by,
            scan_status=DatabaseConstants.SCAN_STATUSES[2],
        )
        db.session.add(scan)
        db.session.commit()

    @staticmethod
    def update_scan(scan_id, **kwargs):
        scan = VulnerabilityScan.query.get(scan_id)
        if scan:
            for key, value in kwargs.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)
            db.session.commit()

    @staticmethod
    def get_scan_by_id(scan_id):
        return VulnerabilityScan.query.get(scan_id)

    @staticmethod
    def get_scans_by_group(group_id, limit=SystemConstants.DEFAULT_SCAN_LIMIT):
        return (
            VulnerabilityScan.query.filter(VulnerabilityScan.group_id == group_id)
            .order_by(VulnerabilityScan.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_scans_by_image(
        image_name, group_id=None, limit=SystemConstants.DEFAULT_SCAN_LIMIT
    ):
        query = VulnerabilityScan.query.filter(
            VulnerabilityScan.image_name == image_name
        )
        if group_id:
            query = query.filter(VulnerabilityScan.group_id == group_id)
        return query.order_by(VulnerabilityScan.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_recent_scans(group_id, limit=SystemConstants.DEFAULT_RECENT_SCANS_LIMIT):
        return (
            VulnerabilityScan.query.filter(VulnerabilityScan.group_id == group_id)
            .order_by(VulnerabilityScan.scan_timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_scan_statistics(group_id, days=SystemConstants.DEFAULT_STATISTICS_DAYS):
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        scans = VulnerabilityScan.query.filter(
            VulnerabilityScan.group_id == group_id,
            VulnerabilityScan.created_at >= cutoff_date,
        ).all()

        total_scans = len(scans)
        successful_scans = len(
            [s for s in scans if s.scan_status == DatabaseConstants.SCAN_STATUSES[0]]
        )

        critical_count = (
            db.session.query(func.sum(VulnerabilityScan.critical_count))
            .filter(
                VulnerabilityScan.group_id == group_id,
                VulnerabilityScan.created_at >= cutoff_date,
            )
            .scalar()
            or 0
        )

        high_count = (
            db.session.query(func.sum(VulnerabilityScan.high_count))
            .filter(
                VulnerabilityScan.group_id == group_id,
                VulnerabilityScan.created_at >= cutoff_date,
            )
            .scalar()
            or 0
        )

        medium_count = (
            db.session.query(func.sum(VulnerabilityScan.medium_count))
            .filter(
                VulnerabilityScan.group_id == group_id,
                VulnerabilityScan.created_at >= cutoff_date,
            )
            .scalar()
            or 0
        )

        low_count = (
            db.session.query(func.sum(VulnerabilityScan.low_count))
            .filter(
                VulnerabilityScan.group_id == group_id,
                VulnerabilityScan.created_at >= cutoff_date,
            )
            .scalar()
            or 0
        )

        return {
            "total_scans": total_scans,
            "successful_scans": successful_scans,
            "success_rate": (successful_scans / total_scans * 100)
            if total_scans > 0
            else 0,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
        }

    @staticmethod
    def get_chart_data(group_id, days=SystemConstants.DEFAULT_CHART_DAYS):
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        scans = (
            VulnerabilityScan.query.filter(
                and_(
                    VulnerabilityScan.group_id == group_id,
                    VulnerabilityScan.scan_timestamp >= start_date,
                    VulnerabilityScan.scan_timestamp <= end_date,
                )
            )
            .order_by(VulnerabilityScan.scan_timestamp.asc())
            .all()
        )

        chart_data = {"labels": [], "critical": [], "high": [], "medium": [], "low": []}

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            chart_data["labels"].append(current_date.strftime("%b %d"))

            day_scans = [
                scan
                for scan in scans
                if scan.scan_timestamp
                and scan.scan_timestamp.date() == current_date.date()
            ]

            if day_scans:
                critical = sum(scan.critical_count or 0 for scan in day_scans)
                high = sum(scan.high_count or 0 for scan in day_scans)
                medium = sum(scan.medium_count or 0 for scan in day_scans)
                low = sum(scan.low_count or 0 for scan in day_scans)
                critical = high = medium = low = 0

            chart_data["critical"].append(critical)
            chart_data["high"].append(high)
            chart_data["medium"].append(medium)
            chart_data["low"].append(low)

        return chart_data
