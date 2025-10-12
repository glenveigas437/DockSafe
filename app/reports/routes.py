
from flask import render_template, jsonify, request, session, send_file, make_response
from datetime import datetime, timedelta
from app.models import VulnerabilityScan, Vulnerability
from app.decorators import login_required
from app.reports import bp
import json
import io

@bp.route('/')
@login_required
def index():
    """Reports index page"""
    return render_template('reports/index.html')

@bp.route('/<int:report_id>/details')
@login_required
def report_details(report_id):
    """Detailed report page for a specific scan"""
    try:
        # Get selected group ID
        group_id = session.get('selected_group_id')
        if not group_id:
            return render_template('reports/details.html', error='No group selected')
        
        scan = VulnerabilityScan.query.filter(
            VulnerabilityScan.id == report_id,
            VulnerabilityScan.group_id == group_id
        ).first()
        
        if not scan:
            return render_template('reports/details.html', error='Report not found')
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        severity_filter = request.args.get('severity', '')
        
        # Build query with filters
        query = Vulnerability.query.filter_by(scan_id=report_id)
        
        if severity_filter:
            query = query.filter_by(severity=severity_filter.upper())
        
        # Apply pagination
        vulnerabilities_pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template('reports/details.html', 
                             scan=scan, 
                             vulnerabilities=vulnerabilities_pagination.items,
                             pagination=vulnerabilities_pagination,
                             current_severity=severity_filter)
        
    except Exception as e:
        return render_template('reports/details.html', error=str(e))

@bp.route('/<int:report_id>/download')
@login_required
def download_report(report_id):
    """Download report as JSON"""
    try:
        # Get selected group ID
        group_id = session.get('selected_group_id')
        if not group_id:
            return jsonify({'error': 'No group selected'}), 400
        
        scan = VulnerabilityScan.query.filter(
            VulnerabilityScan.id == report_id,
            VulnerabilityScan.group_id == group_id
        ).first()
        
        if not scan:
            return jsonify({'error': 'Report not found'}), 404
        
        vulnerabilities = Vulnerability.query.filter_by(scan_id=report_id).all()
        
        # Create report data
        report_data = {
            'scan_info': {
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
        
        # Create JSON response
        json_data = json.dumps(report_data, indent=2)
        
        # Create file-like object
        output = io.BytesIO()
        output.write(json_data.encode('utf-8'))
        output.seek(0)
        
        # Create response
        response = make_response(send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'scan_report_{scan.id}_{scan.image_name.replace("/", "_")}_{scan.image_tag}.json'
        ))
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/list')
@login_required
def list_reports():
    """List scan reports with optional filters"""
    try:
        # Get selected group ID
        group_id = session.get('selected_group_id')
        if not group_id:
            return jsonify({'error': 'No group selected'}), 400
        
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        # Build query with group filter
        query = VulnerabilityScan.query.filter(VulnerabilityScan.group_id == group_id)
        
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
@login_required
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

@bp.route('/export')
@login_required
def export_reports():
    """Export all reports as CSV/JSON"""
    # TODO: Implement bulk export
    return jsonify({'message': 'Bulk export not yet implemented'}), 501

@bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate a new report"""
    # TODO: Implement report generation
    return jsonify({'message': 'Report generation not yet implemented'}), 501
