
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .engine import VulnerabilityScanner, ScanResult, VulnerabilityResult

logger = logging.getLogger(__name__)

class TrivyScanner(VulnerabilityScanner):
    """Trivy vulnerability scanner implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__('trivy', config)
        self.trivy_path = self.config.get('trivy_path', 'trivy')
        self.timeout = self.config.get('timeout', 300)
        self.severity_threshold = self.config.get('severity_threshold', 'UNKNOWN')
        self.format = self.config.get('format', 'json')
    
    def is_available(self) -> bool:
        """Check if Trivy is available and properly configured"""
        try:
            result = subprocess.run(
                [self.trivy_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            self.logger.error(f"Trivy not available: {e}")
            return False
    
    def get_scanner_version(self) -> str:
        """Get Trivy version"""
        try:
            result = subprocess.run(
                [self.trivy_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from output (e.g., "Version: 0.48.3")
                version_line = result.stdout.strip().split('\n')[0]
                return version_line.split(': ')[1] if ': ' in version_line else 'unknown'
            return 'unknown'
        except Exception as e:
            self.logger.error(f"Failed to get Trivy version: {e}")
            return 'unknown'
    
    def scan_image(self, image_name: str, image_tag: str = 'latest') -> ScanResult:
        """Scan container image using Trivy"""
        start_time = datetime.now()
        
        if not self.validate_image_name(image_name):
            raise ValueError(f"Invalid image name: {image_name}")
        
        if not self.validate_image_tag(image_tag):
            raise ValueError(f"Invalid image tag: {image_tag}")
        
        full_image_name = f"{image_name}:{image_tag}"
        self.logger.info(f"Starting Trivy scan for image: {full_image_name}")
        
        try:
            # Build Trivy command
            cmd = [
                self.trivy_path,
                'image',
                '--format', self.format,
                '--severity', self.severity_threshold,
                '--no-progress',
                '--quiet'
            ]
            
            # Add timeout if specified (convert seconds to Trivy format)
            if self.timeout:
                timeout_str = f"{self.timeout}s"  # Trivy expects format like "300s" or "5m"
                cmd.extend(['--timeout', timeout_str])
            
            # Add image name
            cmd.append(full_image_name)
            
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            
            # Execute Trivy scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 30  # Add buffer for subprocess overhead
            )
            
            scan_duration = int((datetime.now() - start_time).total_seconds())
            
            if result.returncode == 0:
                # Parse successful scan results
                vulnerabilities = self._parse_trivy_output(result.stdout)
                scan_status = 'SUCCESS'
            else:
                # Handle scan errors
                self.logger.error(f"Trivy scan failed: {result.stderr}")
                vulnerabilities = []
                scan_status = 'FAILED'
            
            return ScanResult(
                image_name=image_name,
                image_tag=image_tag,
                scan_status=scan_status,
                scan_duration_seconds=scan_duration,
                scanner_version=self.get_scanner_version(),
                vulnerabilities=vulnerabilities,
                scan_output=result.stdout + result.stderr,
                metadata={
                    'trivy_command': ' '.join(cmd),
                    'return_code': result.returncode,
                    'severity_threshold': self.severity_threshold
                }
            )
            
        except subprocess.TimeoutExpired:
            scan_duration = int((datetime.now() - start_time).total_seconds())
            self.logger.error(f"Trivy scan timed out after {scan_duration} seconds")
            return ScanResult(
                image_name=image_name,
                image_tag=image_tag,
                scan_status='TIMEOUT',
                scan_duration_seconds=scan_duration,
                scanner_version=self.get_scanner_version(),
                vulnerabilities=[],
                scan_output=f"Scan timed out after {scan_duration} seconds",
                metadata={'error': 'timeout'}
            )
        
        except Exception as e:
            scan_duration = int((datetime.now() - start_time).total_seconds())
            self.logger.error(f"Unexpected error during Trivy scan: {e}")
            return ScanResult(
                image_name=image_name,
                image_tag=image_tag,
                scan_status='ERROR',
                scan_duration_seconds=scan_duration,
                scanner_version=self.get_scanner_version(),
                vulnerabilities=[],
                scan_output=str(e),
                metadata={'error': str(e)}
            )
    
    def _parse_trivy_output(self, output: str) -> List[VulnerabilityResult]:
        """Parse Trivy JSON output into vulnerability results"""
        vulnerabilities = []
        
        try:
            # Parse JSON output
            scan_data = json.loads(output)
            
            # Handle different Trivy output formats
            if isinstance(scan_data, list):
                # List of results
                for result in scan_data:
                    vulnerabilities.extend(self._parse_result_item(result))
            elif isinstance(scan_data, dict):
                # Single result
                vulnerabilities.extend(self._parse_result_item(scan_data))
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Trivy JSON output: {e}")
            self.logger.debug(f"Raw output: {output}")
        
        return vulnerabilities
    
    def _parse_result_item(self, result: Dict[str, Any]) -> List[VulnerabilityResult]:
        """Parse individual result item from Trivy output"""
        vulnerabilities = []
        
        # Extract vulnerabilities from different possible locations
        vulns = result.get('Vulnerabilities', [])
        if not vulns and 'Results' in result:
            # Handle newer Trivy format
            for res in result.get('Results', []):
                vulns.extend(res.get('Vulnerabilities', []))
        
        for vuln in vulns:
            try:
                vulnerability = VulnerabilityResult(
                    cve_id=vuln.get('VulnerabilityID', ''),
                    severity=self.parse_severity(vuln.get('Severity', 'UNKNOWN')),
                    package_name=vuln.get('PkgName', ''),
                    package_version=vuln.get('InstalledVersion', ''),
                    fixed_version=vuln.get('FixedVersion', ''),
                    description=vuln.get('Description', ''),
                    cvss_score=self._parse_cvss_score(vuln),
                    cvss_vector=vuln.get('CVSS', {}).get('nvd', {}).get('V3Vector', ''),
                    published_date=self._parse_date(vuln.get('PublishedDate')),
                    last_modified_date=self._parse_date(vuln.get('LastModifiedDate')),
                    references=vuln.get('References', [])
                )
                vulnerabilities.append(vulnerability)
                
            except Exception as e:
                self.logger.warning(f"Failed to parse vulnerability: {e}")
                continue
        
        return vulnerabilities
    
    def _parse_cvss_score(self, vuln: Dict[str, Any]) -> Optional[float]:
        """Parse CVSS score from vulnerability data"""
        try:
            # Try different possible locations for CVSS score
            cvss_data = vuln.get('CVSS', {})
            if isinstance(cvss_data, dict):
                # Try NVD CVSS first
                nvd_cvss = cvss_data.get('nvd', {})
                if 'V3Score' in nvd_cvss:
                    return float(nvd_cvss['V3Score'])
                elif 'V2Score' in nvd_cvss:
                    return float(nvd_cvss['V2Score'])
                
                # Try other CVSS sources
                for source in ['redhat', 'ubuntu', 'debian']:
                    source_cvss = cvss_data.get(source, {})
                    if 'V3Score' in source_cvss:
                        return float(source_cvss['V3Score'])
                    elif 'V2Score' in source_cvss:
                        return float(source_cvss['V2Score'])
            
            return None
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Handle common date formats
            for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def update_database(self) -> bool:
        """Update Trivy vulnerability database"""
        try:
            self.logger.info("Updating Trivy vulnerability database...")
            result = subprocess.run(
                [self.trivy_path, 'image', '--download-db-only'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info("Trivy database updated successfully")
                return True
            else:
                self.logger.error(f"Failed to update Trivy database: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating Trivy database: {e}")
            return False
