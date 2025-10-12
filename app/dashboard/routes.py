"""
Dashboard routes for DockSafe application
"""

from flask import render_template, jsonify, session, request
from app.scanner.service import ScannerService
from app.models import VulnerabilityScan, Vulnerability, Group, User
from app.decorators import login_required
from app import db
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.dashboard import bp

@bp.route('/')
@login_required
def index():
    """Dashboard index page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return render_template('dashboard/index.html', stats={})
        
        user = User.query.get(user_id)
        if not user:
            return render_template('dashboard/index.html', stats={})
        
        # Get selected group ID
        selected_group_id = session.get('selected_group_id')
        
        if not selected_group_id:
            # If no group selected, show empty stats
            stats = {
                'total_scans': 0,
                'success_rate': 0,
                'critical_issues': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'recent_scans': [],
                'system_status': {
                    'scanner_service': 'Online',
                    'database': 'Connected',
                    'api_gateway': 'Operational',
                    'notification_service': 'Operational'
                }
            }
        else:
            # Get real statistics from database for selected group
            total_scans = VulnerabilityScan.query.filter(
                VulnerabilityScan.group_id == selected_group_id
            ).count()
            
            successful_scans = VulnerabilityScan.query.filter(
                and_(
                    VulnerabilityScan.group_id == selected_group_id,
                    VulnerabilityScan.scan_status == 'SUCCESS'
                )
            ).count()
            
            success_rate = (successful_scans / total_scans * 100) if total_scans > 0 else 0
            
            # Get vulnerability counts
            critical_count = db.session.query(func.sum(VulnerabilityScan.critical_count)).filter(
                VulnerabilityScan.group_id == selected_group_id
            ).scalar() or 0
            
            high_count = db.session.query(func.sum(VulnerabilityScan.high_count)).filter(
                VulnerabilityScan.group_id == selected_group_id
            ).scalar() or 0
            
            medium_count = db.session.query(func.sum(VulnerabilityScan.medium_count)).filter(
                VulnerabilityScan.group_id == selected_group_id
            ).scalar() or 0
            
            low_count = db.session.query(func.sum(VulnerabilityScan.low_count)).filter(
                VulnerabilityScan.group_id == selected_group_id
            ).scalar() or 0
            
            # Get recent scans
            recent_scans = VulnerabilityScan.query.filter(
                VulnerabilityScan.group_id == selected_group_id
            ).order_by(VulnerabilityScan.scan_timestamp.desc()).limit(5).all()
            
            recent_scans_data = []
            for scan in recent_scans:
                recent_scans_data.append({
                    'id': scan.id,
                    'image_name': scan.image_name,
                    'image_tag': scan.image_tag,
                    'scan_status': scan.scan_status,
                    'scan_timestamp': scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
                    'total_vulnerabilities': scan.total_vulnerabilities or 0,
                    'critical_count': scan.critical_count or 0,
                    'high_count': scan.high_count or 0,
                    'medium_count': scan.medium_count or 0,
                    'low_count': scan.low_count or 0,
                    'scan_duration_seconds': scan.scan_duration_seconds or 0,
                    'scanner_type': scan.scanner_type,
                    'scanner_version': scan.scanner_version
                })
            
            stats = {
                'total_scans': total_scans,
                'success_rate': round(success_rate, 1),
                'critical_issues': critical_count,
                'high_severity': high_count,
                'medium_severity': medium_count,
                'low_severity': low_count,
                'recent_scans': recent_scans_data,
                'system_status': {
                    'scanner_service': 'Online',
                    'database': 'Connected',
                    'api_gateway': 'Operational',
                    'notification_service': 'Operational'
                }
            }
        return render_template('dashboard/index.html', stats=stats)
        
    except Exception as e:
        return render_template('dashboard/index.html', stats={})

@bp.route('/chart-data')
@login_required
def chart_data():
    """Get historical vulnerability data for charts"""
    try:
        # Get selected group ID
        selected_group_id = session.get('selected_group_id')
        if not selected_group_id:
            return jsonify({'error': 'No group selected'}), 400
        
        # Get number of days (default 7)
        days = int(request.args.get('days', 7))
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get scans for the date range
        scans = VulnerabilityScan.query.filter(
            and_(
                VulnerabilityScan.group_id == selected_group_id,
                VulnerabilityScan.scan_timestamp >= start_date,
                VulnerabilityScan.scan_timestamp <= end_date
            )
        ).order_by(VulnerabilityScan.scan_timestamp.asc()).all()
        
        # Generate daily data points
        chart_data = {
            'labels': [],
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Create data points for each day
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            chart_data['labels'].append(current_date.strftime('%b %d'))
            
            # Find scans for this day
            day_scans = [scan for scan in scans if 
                        scan.scan_timestamp and 
                        scan.scan_timestamp.date() == current_date.date()]
            
            if day_scans:
                # Sum vulnerabilities for this day
                critical = sum(scan.critical_count or 0 for scan in day_scans)
                high = sum(scan.high_count or 0 for scan in day_scans)
                medium = sum(scan.medium_count or 0 for scan in day_scans)
                low = sum(scan.low_count or 0 for scan in day_scans)
            else:
                critical = high = medium = low = 0
            
            chart_data['critical'].append(critical)
            chart_data['high'].append(high)
            chart_data['medium'].append(medium)
            chart_data['low'].append(low)
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/stats')
@login_required
def get_stats():
    """Get dashboard statistics"""
    try:
        scanner_service = ScannerService()
        stats = scanner_service.get_scan_statistics(days=30)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500