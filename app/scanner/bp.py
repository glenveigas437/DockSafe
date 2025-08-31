"""
Scanner blueprint for Flask application
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.scanner.service import ScannerService
from app.models import VulnerabilityScan, Vulnerability, ScanException
from app import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('scanner', __name__)

def get_scanner_service():
    """Get scanner service instance"""
    config = {
        'scanner_type': current_app.config.get('SCANNER_TYPE', 'trivy'),
        'timeout': current_app.config.get('SCANNER_TIMEOUT', 300),
        'severity_threshold': current_app.config.get('VULNERABILITY_THRESHOLD', 'HIGH')
    }
    return ScannerService(config)

@bp.route('/scan', methods=['POST'])
@login_required
def scan_image():
    """Scan a container image for vulnerabilities"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        image_name = data.get('image_name')
        image_tag = data.get('image_tag', 'latest')
        
        if not image_name:
            return jsonify({'error': 'image_name is required'}), 400
        
        # Get scanner service
        scanner_service = get_scanner_service()
        
        # Check if scanner is available
        if not scanner_service.is_scanner_available():
            return jsonify({'error': 'Vulnerability scanner is not available'}), 503
        
        # Perform scan
        scan_record = scanner_service.scan_image(
            image_name=image_name,
            image_tag=image_tag,
            user_id=current_user.id if current_user else None
        )
        
        # Return scan results
        return jsonify({
            'message': 'Scan completed successfully',
            'scan_id': scan_record.id,
            'scan_status': scan_record.scan_status,
            'total_vulnerabilities': scan_record.total_vulnerabilities,
            'severity_breakdown': scan_record.severity_summary,
            'scan_duration_seconds': scan_record.scan_duration_seconds,
            'should_fail_build': scanner_service.should_fail_build(scan_record)
        }), 200
        
    except Exception as e:
        logger.error(f"Error during image scan: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/scan/<int:scan_id>', methods=['GET'])
@login_required
def get_scan_result(scan_id):
    """Get scan result by ID"""
    try:
        scanner_service = get_scanner_service()
        scan_record = scanner_service.get_scan_by_id(scan_id)
        
        if not scan_record:
            return jsonify({'error': 'Scan not found'}), 404
        
        # Get vulnerabilities for this scan
        vulnerabilities = scanner_service.get_vulnerabilities_for_scan(scan_id)
        
        return jsonify({
            'scan': scan_record.to_dict(),
            'vulnerabilities': [v.to_dict() for v in vulnerabilities],
            'should_fail_build': scanner_service.should_fail_build(scan_record)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scan result: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/scan/<int:scan_id>/vulnerabilities', methods=['GET'])
@login_required
def get_scan_vulnerabilities(scan_id):
    """Get vulnerabilities for a specific scan"""
    try:
        scanner_service = get_scanner_service()
        vulnerabilities = scanner_service.get_vulnerabilities_for_scan(scan_id)
        
        # Apply filters if provided
        severity_filter = request.args.get('severity')
        if severity_filter:
            vulnerabilities = [v for v in vulnerabilities if v.severity.upper() == severity_filter.upper()]
        
        return jsonify({
            'scan_id': scan_id,
            'vulnerabilities': [v.to_dict() for v in vulnerabilities],
            'count': len(vulnerabilities)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving vulnerabilities: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/history', methods=['GET'])
@login_required
def get_scan_history():
    """Get scan history"""
    try:
        scanner_service = get_scanner_service()
        
        # Get query parameters
        image_name = request.args.get('image_name')
        limit = int(request.args.get('limit', 50))
        
        # Get scan history
        scans = scanner_service.get_scan_history(image_name=image_name, limit=limit)
        
        return jsonify({
            'scans': [scan.to_dict() for scan in scans],
            'count': len(scans)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scan history: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics', methods=['GET'])
@login_required
def get_scan_statistics():
    """Get scan statistics"""
    try:
        scanner_service = get_scanner_service()
        
        # Get query parameters
        days = int(request.args.get('days', 30))
        
        # Get statistics
        stats = scanner_service.get_scan_statistics(days=days)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scan statistics: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/status', methods=['GET'])
@login_required
def get_scanner_status():
    """Get scanner status and information"""
    try:
        scanner_service = get_scanner_service()
        scanner_info = scanner_service.get_scanner_info()
        
        return jsonify(scanner_info), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scanner status: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/exceptions', methods=['GET'])
@login_required
def get_exceptions():
    """Get scan exceptions"""
    try:
        # Get query parameters
        image_name = request.args.get('image_name')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Build query
        query = ScanException.query
        
        if image_name:
            query = query.filter(ScanException.image_name == image_name)
        
        if active_only:
            query = query.filter(ScanException.is_active == True)
        
        exceptions = query.order_by(ScanException.created_at.desc()).all()
        
        return jsonify({
            'exceptions': [ex.to_dict() for ex in exceptions],
            'count': len(exceptions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving exceptions: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/exceptions', methods=['POST'])
@login_required
def create_exception():
    """Create a new scan exception"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['cve_id', 'reason', 'approved_by']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create exception
        exception = ScanException(
            cve_id=data['cve_id'],
            image_name=data.get('image_name'),  # Optional - null for global exceptions
            reason=data['reason'],
            approved_by=data['approved_by'],
            expires_at=data.get('expires_at'),  # Optional
            is_active=data.get('is_active', True)
        )
        
        db.session.add(exception)
        db.session.commit()
        
        return jsonify({
            'message': 'Exception created successfully',
            'exception': exception.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating exception: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/exceptions/<int:exception_id>', methods=['PUT'])
@login_required
def update_exception(exception_id):
    """Update an existing scan exception"""
    try:
        exception = ScanException.query.get(exception_id)
        
        if not exception:
            return jsonify({'error': 'Exception not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        if 'reason' in data:
            exception.reason = data['reason']
        if 'approved_by' in data:
            exception.approved_by = data['approved_by']
        if 'expires_at' in data:
            exception.expires_at = data['expires_at']
        if 'is_active' in data:
            exception.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Exception updated successfully',
            'exception': exception.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating exception: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/exceptions/<int:exception_id>', methods=['DELETE'])
@login_required
def delete_exception(exception_id):
    """Delete a scan exception"""
    try:
        exception = ScanException.query.get(exception_id)
        
        if not exception:
            return jsonify({'error': 'Exception not found'}), 404
        
        db.session.delete(exception)
        db.session.commit()
        
        return jsonify({'message': 'Exception deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting exception: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
