
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VulnerabilityResult:
    """Data class for vulnerability scan results"""
    cve_id: str
    severity: str
    package_name: str
    package_version: Optional[str] = None
    fixed_version: Optional[str] = None
    description: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    published_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    references: Optional[List[str]] = None

@dataclass
class ScanResult:
    """Data class for complete scan results"""
    image_name: str
    image_tag: str
    scan_status: str
    scan_duration_seconds: int
    scanner_version: str
    vulnerabilities: List[VulnerabilityResult]
    scan_output: str
    metadata: Dict[str, Any]
    
    @property
    def total_vulnerabilities(self) -> int:
        return len(self.vulnerabilities)
    
    @property
    def critical_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity.upper() == 'CRITICAL'])
    
    @property
    def high_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity.upper() == 'HIGH'])
    
    @property
    def medium_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity.upper() == 'MEDIUM'])
    
    @property
    def low_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity.upper() == 'LOW'])
    
    @property
    def has_critical_vulnerabilities(self) -> bool:
        return self.critical_count > 0
    
    @property
    def has_high_vulnerabilities(self) -> bool:
        return self.high_count > 0
    
    def filter_by_severity(self, min_severity: str = 'LOW') -> List[VulnerabilityResult]:
        """Filter vulnerabilities by minimum severity level"""
        severity_levels = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        min_level = severity_levels.get(min_severity.upper(), 1)
        return [
            v for v in self.vulnerabilities
            if severity_levels.get(v.severity.upper(), 0) >= min_level
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary"""
        return {
            'image_name': self.image_name,
            'image_tag': self.image_tag,
            'scan_status': self.scan_status,
            'scan_duration_seconds': self.scan_duration_seconds,
            'scanner_version': self.scanner_version,
            'total_vulnerabilities': self.total_vulnerabilities,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count,
            'vulnerabilities': [v.__dict__ for v in self.vulnerabilities],
            'scan_output': self.scan_output,
            'metadata': self.metadata
        }

class VulnerabilityScanner(ABC):
    """Abstract base class for vulnerability scanners"""
    
    def __init__(self, scanner_type: str = 'trivy', config: Optional[Dict[str, Any]] = None):
        self.scanner_type = scanner_type
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def scan_image(self, image_name: str, image_tag: str = 'latest') -> ScanResult:
        """Scan container image for vulnerabilities"""
        pass
    
    @abstractmethod
    def get_scanner_version(self) -> str:
        """Get scanner version"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is available and properly configured"""
        pass
    
    def validate_image_name(self, image_name: str) -> bool:
        """Validate image name format"""
        if not image_name or not isinstance(image_name, str):
            return False
        
        # Basic validation - can be extended based on requirements
        return len(image_name) > 0 and len(image_name) <= 255
    
    def validate_image_tag(self, image_tag: str) -> bool:
        """Validate image tag format"""
        if not image_tag or not isinstance(image_tag, str):
            return False
        
        # Basic validation - can be extended based on requirements
        return len(image_tag) > 0 and len(image_tag) <= 100
    
    def parse_severity(self, severity: str) -> str:
        """Parse and normalize severity levels"""
        severity_map = {
            'CRITICAL': 'CRITICAL',
            'HIGH': 'HIGH',
            'MEDIUM': 'MEDIUM',
            'LOW': 'LOW',
            'UNKNOWN': 'LOW'
        }
        return severity_map.get(severity.upper(), 'LOW')
    
    def should_fail_build(self, scan_result: ScanResult, threshold: str = 'HIGH') -> bool:
        """Determine if build should fail based on vulnerability threshold"""
        severity_levels = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        threshold_level = severity_levels.get(threshold.upper(), 3)
        
        if threshold_level >= 4 and scan_result.critical_count > 0:
            return True
        elif threshold_level >= 3 and scan_result.high_count > 0:
            return True
        elif threshold_level >= 2 and scan_result.medium_count > 0:
            return True
        elif threshold_level >= 1 and scan_result.low_count > 0:
            return True
        
        return False
    
    def get_scan_summary(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Get a summary of scan results"""
        return {
            'image': f"{scan_result.image_name}:{scan_result.image_tag}",
            'status': scan_result.scan_status,
            'duration_seconds': scan_result.scan_duration_seconds,
            'total_vulnerabilities': scan_result.total_vulnerabilities,
            'severity_breakdown': {
                'critical': scan_result.critical_count,
                'high': scan_result.high_count,
                'medium': scan_result.medium_count,
                'low': scan_result.low_count
            },
            'has_critical': scan_result.has_critical_vulnerabilities,
            'has_high': scan_result.has_high_vulnerabilities,
            'scanner_version': scan_result.scanner_version
        }
