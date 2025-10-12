from app.mappers.scan_mapper import ScanMapper
from app.mappers.vulnerability_mapper import VulnerabilityMapper
from app.scanner.trivy_scanner import TrivyScanner
from app.scanner.clair_scanner import ClairScanner
from app.scanner.engine import ScanResult
from app.constants import DatabaseConstants, SystemConstants, ErrorMessages

logger = logging.getLogger(__name__)

class ScanService:
    def __init__(self, scanner_type=DatabaseConstants.DEFAULT_SCANNER_TYPE, config=None):
        self.scanner_type = scanner_type
        self.config = config or {}
        self.scanner = self._initialize_scanner()
    
    def _initialize_scanner(self):
        if self.scanner_type.lower() == DatabaseConstants.SCANNER_TYPES[1]:
            return ClairScanner(self.config)
            return TrivyScanner(self.config)
    
    def scan_image(self, image_name, image_tag='latest', user_id=None, group_id=None):
        logger.info(f"Starting vulnerability scan for {image_name}:{image_tag}")
        
        scan_record = ScanMapper.create_scan(
            image_name=image_name,
            image_tag=image_tag,
            scanner_type=self.scanner_type,
            group_id=group_id,
            created_by=user_id
        )
        
            scan_result = self.scanner.scan_image(image_name, image_tag)
            
            ScanMapper.update_scan(scan_record.id, 
                                 scan_status=scan_result.scan_status,
                                 scan_duration_seconds=scan_result.scan_duration_seconds,
                                 scanner_version=scan_result.scanner_version,
                                 scan_output=scan_result.scan_output,
                                 scan_metadata=scan_result.metadata,
                                 scan_timestamp=datetime.utcnow())
            
            self._store_vulnerabilities(scan_record.id, scan_result)
            self._apply_exceptions(scan_record.id, image_name)
            self._update_vulnerability_counts(scan_record.id)
            
            logger.info(f"Scan completed for {image_name}:{image_tag} - "
                       f"Status: {scan_result.scan_status}")
            
            return ScanMapper.get_scan_by_id(scan_record.id)
            
        except Exception as e:
            logger.error(f"Error during scan of {image_name}:{image_tag}: {e}")
            
            error_message = str(e)
            if "No such image" in error_message or "MANIFEST_UNKNOWN" in error_message:
                scan_output = ErrorMessages.IMAGE_NOT_FOUND
            elif "unable to find the specified image" in error_message:
                scan_output = ErrorMessages.IMAGE_NOT_FOUND_RUNTIME
                scan_output = f"{ErrorMessages.SCAN_FAILED}: {error_message}"
            
            ScanMapper.update_scan(scan_record.id, 
                                 scan_status=DatabaseConstants.SCAN_STATUSES[1],
                                 scan_output=scan_output)
            
    
    def _store_vulnerabilities(self, scan_id, scan_result):
        for vuln_result in scan_result.vulnerabilities:
            VulnerabilityMapper.create_vulnerability(
                scan_id=scan_id,
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
    
    def _apply_exceptions(self, scan_id, image_name):
        exceptions = VulnerabilityMapper.get_active_exceptions(image_name)
        excepted_cves = {ex.cve_id for ex in exceptions if ex.is_valid}
        
        if excepted_cves:
            VulnerabilityMapper.delete_vulnerabilities_by_cve_ids(scan_id, excepted_cves)
            logger.info(f"Applied {len(excepted_cves)} exceptions to scan {scan_id}")
    
    def _update_vulnerability_counts(self, scan_id):
        counts = VulnerabilityMapper.count_vulnerabilities_by_severity(scan_id)
        
        ScanMapper.update_scan(scan_id,
                             critical_count=counts['CRITICAL'],
                             high_count=counts['HIGH'],
                             medium_count=counts['MEDIUM'],
                             low_count=counts['LOW'],
                             total_vulnerabilities=counts['total'])
    
    def get_scan_history(self, image_name=None, limit=50, group_id=None):
        if image_name:
            return ScanMapper.get_scans_by_image(image_name, group_id, limit)
            return ScanMapper.get_scans_by_group(group_id, limit)
    
    def get_scan_by_id(self, scan_id):
        return ScanMapper.get_scan_by_id(scan_id)
    
    def get_vulnerabilities_for_scan(self, scan_id):
        return VulnerabilityMapper.get_vulnerabilities_by_scan(scan_id)
    
    def get_scan_statistics(self, group_id, days=30):
        return ScanMapper.get_scan_statistics(group_id, days)
    
    def get_chart_data(self, group_id, days=7):
        return ScanMapper.get_chart_data(group_id, days)
    
    def get_recent_scans(self, group_id, limit=5):
        return ScanMapper.get_recent_scans(group_id, limit)
    
    def is_scanner_available(self):
        return self.scanner.is_available()
    
    def get_scanner_info(self):
        return {
            'scanner_type': self.scanner_type,
            'scanner_version': self.scanner.get_scanner_version(),
            'is_available': self.scanner.is_available(),
            'config': self.config
        }
    
    def should_fail_build(self, scan_record, threshold=DatabaseConstants.DEFAULT_VULNERABILITY_THRESHOLD):
        from app.utils.validation_utils import SeverityUtils
        return SeverityUtils.should_fail_build(
            scan_record.critical_count,
            scan_record.high_count,
            scan_record.medium_count,
            scan_record.low_count,
        )
