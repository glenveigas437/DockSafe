"""
Scanner service for handling vulnerability scanning operations
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from app import db
from app.models import VulnerabilityScan, Vulnerability, ScanException
from .trivy_scanner import TrivyScanner
from .clair_scanner import ClairScanner
from .engine import ScanResult

logger = logging.getLogger(__name__)

class ScannerService:
    """Service class for handling vulnerability scanning operations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scanner_type = self.config.get('scanner_type', 'trivy')
        self.scanner = self._initialize_scanner()
    
    def _initialize_scanner(self):
        """Initialize the appropriate scanner based on configuration"""
        if self.scanner_type.lower() == 'clair':
            return ClairScanner(self.config)
        else:
            # Default to Trivy
            return TrivyScanner(self.config)
    
    def scan_image(self, image_name: str, image_tag: str = 'latest', 
                   user_id: Optional[str] = None) -> VulnerabilityScan:
        """
        Scan a container image for vulnerabilities and store results in database
        
        Args:
            image_name: Name of the container image
            image_tag: Tag of the container image
            user_id: ID of the user requesting the scan
            
        Returns:
            VulnerabilityScan: Database model instance with scan results
        """
        logger.info(f"Starting vulnerability scan for {image_name}:{image_tag}")
        
        # Create scan record in database
        scan_record = VulnerabilityScan(
            image_name=image_name,
            image_tag=image_tag,
            scan_status='IN_PROGRESS',
            scanner_type=self.scanner_type
        )
        
        try:
            db.session.add(scan_record)
            db.session.commit()
            
            # Perform the actual scan
            scan_result = self.scanner.scan_image(image_name, image_tag)
            
            # Update scan record with results
            self._update_scan_record(scan_record, scan_result)
            
            # Store individual vulnerabilities
            self._store_vulnerabilities(scan_record, scan_result)
            
            # Apply exceptions to filter out approved vulnerabilities
            self._apply_exceptions(scan_record)
            
            # Update final counts after applying exceptions
            self._update_vulnerability_counts(scan_record)
            
            db.session.commit()
            
            logger.info(f"Scan completed for {image_name}:{image_tag} - "
                       f"Status: {scan_record.scan_status}, "
                       f"Vulnerabilities: {scan_record.total_vulnerabilities}")
            
            return scan_record
            
        except Exception as e:
            logger.error(f"Error during scan of {image_name}:{image_tag}: {e}")
            
            # Update scan record with error status
            scan_record.scan_status = 'FAILED'
            scan_record.scan_output = str(e)
            db.session.commit()
            
            raise
    
    def _update_scan_record(self, scan_record: VulnerabilityScan, scan_result: ScanResult):
        """Update scan record with scan results"""
        scan_record.scan_status = scan_result.scan_status
        scan_record.scan_duration_seconds = scan_result.scan_duration_seconds
        scan_record.scanner_version = scan_result.scanner_version
        scan_record.scan_output = scan_result.scan_output
        scan_record.metadata = scan_result.metadata
        scan_record.scan_timestamp = datetime.utcnow()
    
    def _store_vulnerabilities(self, scan_record: VulnerabilityScan, scan_result: ScanResult):
        """Store individual vulnerabilities in database"""
        for vuln_result in scan_result.vulnerabilities:
            vulnerability = Vulnerability(
                scan_id=scan_record.id,
                cve_id=vuln_result.cve_id,
                severity=vuln_result.severity,
                package_name=vuln_result.package_name,
                package_version=vuln_result.package_version,
                fixed_version=vuln_result.fixed_version,
                description=vuln_result.description,
                cvss_score=vuln_result.cvss_score,
                cvss_vector=vuln_result.cvss_vector,
                published_date=vuln_result.published_date,
                last_modified_date=vuln_result.last_modified_date,
                references=vuln_result.references
            )
            db.session.add(vulnerability)
    
    def _apply_exceptions(self, scan_record: VulnerabilityScan):
        """Apply scan exceptions to filter out approved vulnerabilities"""
        # Get active exceptions for this image (or global exceptions)
        exceptions = ScanException.query.filter(
            db.or_(
                ScanException.image_name == scan_record.image_name,
                ScanException.image_name.is_(None)  # Global exceptions
            ),
            ScanException.is_active == True
        ).all()
        
        # Create set of excepted CVE IDs
        excepted_cves = {ex.cve_id for ex in exceptions if ex.is_valid}
        
        # Remove excepted vulnerabilities
        if excepted_cves:
            vulnerabilities_to_remove = Vulnerability.query.filter(
                Vulnerability.scan_id == scan_record.id,
                Vulnerability.cve_id.in_(excepted_cves)
            ).all()
            
            for vuln in vulnerabilities_to_remove:
                db.session.delete(vuln)
            
            logger.info(f"Applied {len(excepted_cves)} exceptions to scan {scan_record.id}")
    
    def _update_vulnerability_counts(self, scan_record: VulnerabilityScan):
        """Update vulnerability counts in scan record"""
        # Count vulnerabilities by severity
        counts = db.session.query(
            Vulnerability.severity,
            db.func.count(Vulnerability.id)
        ).filter(
            Vulnerability.scan_id == scan_record.id
        ).group_by(Vulnerability.severity).all()
        
        # Reset counts
        scan_record.critical_count = 0
        scan_record.high_count = 0
        scan_record.medium_count = 0
        scan_record.low_count = 0
        scan_record.total_vulnerabilities = 0
        
        # Update counts
        for severity, count in counts:
            if severity.upper() == 'CRITICAL':
                scan_record.critical_count = count
            elif severity.upper() == 'HIGH':
                scan_record.high_count = count
            elif severity.upper() == 'MEDIUM':
                scan_record.medium_count = count
            elif severity.upper() == 'LOW':
                scan_record.low_count = count
            
            scan_record.total_vulnerabilities += count
    
    def get_scan_history(self, image_name: Optional[str] = None, 
                        limit: int = 50) -> List[VulnerabilityScan]:
        """Get scan history with optional filtering"""
        query = VulnerabilityScan.query.order_by(VulnerabilityScan.created_at.desc())
        
        if image_name:
            query = query.filter(VulnerabilityScan.image_name == image_name)
        
        return query.limit(limit).all()
    
    def get_scan_by_id(self, scan_id: int) -> Optional[VulnerabilityScan]:
        """Get scan by ID"""
        return VulnerabilityScan.query.get(scan_id)
    
    def get_vulnerabilities_for_scan(self, scan_id: int) -> List[Vulnerability]:
        """Get all vulnerabilities for a specific scan"""
        return Vulnerability.query.filter(Vulnerability.scan_id == scan_id).all()
    
    def should_fail_build(self, scan_record: VulnerabilityScan, 
                         threshold: str = 'HIGH') -> bool:
        """Determine if build should fail based on scan results"""
        severity_levels = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        threshold_level = severity_levels.get(threshold.upper(), 3)
        
        if threshold_level >= 4 and scan_record.critical_count > 0:
            return True
        elif threshold_level >= 3 and scan_record.high_count > 0:
            return True
        elif threshold_level >= 2 and scan_record.medium_count > 0:
            return True
        elif threshold_level >= 1 and scan_record.low_count > 0:
            return True
        
        return False
    
    def get_scan_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get scan statistics for the specified number of days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get scans in date range
        scans = VulnerabilityScan.query.filter(
            VulnerabilityScan.created_at >= cutoff_date
        ).all()
        
        total_scans = len(scans)
        successful_scans = len([s for s in scans if s.scan_status == 'SUCCESS'])
        failed_scans = len([s for s in scans if s.scan_status == 'FAILED'])
        
        # Count vulnerabilities by severity
        total_vulns = sum(s.total_vulnerabilities for s in scans)
        critical_vulns = sum(s.critical_count for s in scans)
        high_vulns = sum(s.high_count for s in scans)
        medium_vulns = sum(s.medium_count for s in scans)
        low_vulns = sum(s.low_count for s in scans)
        
        # Get top vulnerable images
        image_stats = {}
        for scan in scans:
            if scan.image_name not in image_stats:
                image_stats[scan.image_name] = {
                    'total_vulns': 0,
                    'critical_vulns': 0,
                    'high_vulns': 0,
                    'scan_count': 0
                }
            
            image_stats[scan.image_name]['total_vulns'] += scan.total_vulnerabilities
            image_stats[scan.image_name]['critical_vulns'] += scan.critical_count
            image_stats[scan.image_name]['high_vulns'] += scan.high_count
            image_stats[scan.image_name]['scan_count'] += 1
        
        # Sort by total vulnerabilities
        top_vulnerable_images = sorted(
            image_stats.items(),
            key=lambda x: x[1]['total_vulns'],
            reverse=True
        )[:10]
        
        return {
            'period_days': days,
            'total_scans': total_scans,
            'successful_scans': successful_scans,
            'failed_scans': failed_scans,
            'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            'vulnerabilities': {
                'total': total_vulns,
                'critical': critical_vulns,
                'high': high_vulns,
                'medium': medium_vulns,
                'low': low_vulns
            },
            'top_vulnerable_images': top_vulnerable_images
        }
    
    def is_scanner_available(self) -> bool:
        """Check if the configured scanner is available"""
        return self.scanner.is_available()
    
    def get_scanner_info(self) -> Dict[str, Any]:
        """Get information about the configured scanner"""
        return {
            'scanner_type': self.scanner_type,
            'scanner_version': self.scanner.get_scanner_version(),
            'is_available': self.scanner.is_available(),
            'config': self.config
        }
