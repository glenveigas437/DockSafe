"""
Reports routes for DockSafe application
"""

from flask import render_template, jsonify, request
from datetime import datetime, timedelta
from app.models import VulnerabilityScan, Vulnerability
from app.reports import bp

@bp.route('/')
def index():
    """Reports index page"""
    return render_template('reports/index.html')

@bp.route('/list')
def list_reports():
    """List scan reports with optional filters"""
    try:
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        # Build query
        query = VulnerabilityScan.query
        
        # Apply date filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(VulnerabilityScan.scan_timestamp >= from_date)
            except ValueError:
                pass
                
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(VulnerabilityScan.scan_timestamp < to_date)
            except ValueError:
                pass
        
        # Apply status filter
        if status:
            query = query.filter(VulnerabilityScan.scan_status == status)
        
        # Apply severity filter (if specified, only show scans with vulnerabilities of that severity)
        if severity:
            # This would require a more complex query to filter by vulnerability severity
            # For now, we'll return all scans and filter in the frontend
            pass
        
        # Order by scan timestamp (newest first)
        query = query.order_by(VulnerabilityScan.scan_timestamp.desc())
        
        # Execute query
        scans = query.all()
        
        # Convert to JSON
        reports = []
        for scan in scans:
            report = {
                'id': scan.id,
                'image_name': scan.image_name,
                'image_tag': scan.image_tag,
                'scan_status': scan.scan_status,
                'scan_timestamp': scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
                'critical_count': scan.critical_count or 0,
                'high_count': scan.high_count or 0,
                'medium_count': scan.medium_count or 0,
                'low_count': scan.low_count or 0,
                'total_vulnerabilities': scan.total_vulnerabilities or 0
            }
            reports.append(report)
        
        return jsonify({'reports': reports})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:report_id>')
def get_report(report_id):
    """Get detailed report for a specific scan"""
    try:
        scan = VulnerabilityScan.query.get_or_404(report_id)
        vulnerabilities = Vulnerability.query.filter_by(scan_id=report_id).all()
        
        report_data = {
            'scan': {
                'id': scan.id,
                'image_name': scan.image_name,
                'image_tag': scan.image_tag,
                'scan_status': scan.scan_status,
                'scan_timestamp': scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
                'scan_duration_seconds': scan.scan_duration_seconds or 0,
                'scanner_type': scan.scanner_type,
                'scanner_version': scan.scanner_version,
                'critical_count': scan.critical_count or 0,
                'high_count': scan.high_count or 0,
                'medium_count': scan.medium_count or 0,
                'low_count': scan.low_count or 0,
                'total_vulnerabilities': scan.total_vulnerabilities or 0
            },
            'vulnerabilities': []
        }
        
        for vuln in vulnerabilities:
            vuln_data = {
                'cve_id': vuln.cve_id,
                'severity': vuln.severity,
                'package_name': vuln.package_name,
                'package_version': vuln.package_version,
                'fixed_version': vuln.fixed_version,
                'description': vuln.description
            }
            report_data['vulnerabilities'].append(vuln_data)
        
        return jsonify(report_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:report_id>/download')
def download_report(report_id):
    """Download report as PDF"""
    # TODO: Implement PDF generation
    return jsonify({'message': 'PDF download not yet implemented'}), 501

@bp.route('/export')
def export_reports():
    """Export all reports as CSV/JSON"""
    # TODO: Implement bulk export
    return jsonify({'message': 'Bulk export not yet implemented'}), 501

@bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new report"""
    # TODO: Implement report generation
    return jsonify({'message': 'Report generation not yet implemented'}), 501
