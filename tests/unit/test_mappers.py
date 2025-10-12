"""
Unit tests for DockSafe mappers.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.mappers.group_mapper import GroupMapper
from app.mappers.user_mapper import UserMapper
from app.mappers.scan_mapper import ScanMapper
from app.mappers.vulnerability_mapper import VulnerabilityMapper


class TestGroupMapper:
    """Test GroupMapper functionality."""
    
    def test_find_by_id(self, app, sample_group):
        """Test finding group by ID."""
        with app.app_context():
            group = GroupMapper.find_by_id(sample_group)  # sample_group is now an ID
            assert group is not None
            assert group.id == sample_group
            assert group.name == 'Test Group'
    
    def test_find_by_id_not_found(self, app):
        """Test finding group by non-existent ID."""
        with app.app_context():
            group = GroupMapper.find_by_id(99999)
            assert group is None
    
    def test_find_by_name(self, app, sample_group):
        """Test finding group by name."""
        with app.app_context():
            group = GroupMapper.find_by_name('Test Group')
            assert group is not None
            assert group.id == sample_group  # sample_group is now an ID
            assert group.name == 'Test Group'
    
    def test_find_by_name_not_found(self, app):
        """Test finding group by non-existent name."""
        with app.app_context():
            group = GroupMapper.find_by_name('Non-existent Group')
            assert group is None
    
    def test_get_user_groups(self, app, sample_user, sample_group):
        """Test getting user groups."""
        with app.app_context():
            groups = GroupMapper.get_user_groups(sample_user)  # sample_user is now an ID
            assert len(groups) == 1
            assert groups[0].id == sample_group  # sample_group is now an ID
    
    def test_create_group(self, app, sample_user):
        """Test creating a new group."""
        with app.app_context():
            group = GroupMapper.create_group(
                'New Test Group',
                'A new test group',
                sample_user  # sample_user is now an ID
            )
            assert group is not None
            assert group.name == 'New Test Group'
            assert group.description == 'A new test group'
            assert group.created_by == sample_user  # sample_user is now an ID
    
    def test_add_member(self, app, sample_group, sample_user):
        """Test adding member to group."""
        with app.app_context():
            # Create another user
            from app.models import User
            user2 = User(
                username='testuser2',
                email='test2@example.com',
                first_name='Test2',
                last_name='User2'
            )
            from app import db
            db.session.add(user2)
            db.session.commit()
            
            # Add user to group
            GroupMapper.add_member(sample_group, user2.id, 'member')
            
            # Verify user is in group
            groups = GroupMapper.get_user_groups(user2.id)
            assert len(groups) == 1
            assert groups[0].id == sample_group
    
    def test_remove_member(self, app, sample_group, sample_user):
        """Test removing member from group."""
        with app.app_context():
            # Remove user from group
            GroupMapper.remove_member(sample_group, sample_user)
            
            # Verify user is no longer in group
            groups = GroupMapper.get_user_groups(sample_user)
            assert len(groups) == 0
    
    def test_get_user_role_in_group(self, app, sample_group, sample_user):
        """Test getting user role in group."""
        with app.app_context():
            role = GroupMapper.get_user_role_in_group(sample_group, sample_user)
            assert role == 'owner'
    
    def test_get_group_members(self, app, sample_group, sample_user):
        """Test getting group members."""
        with app.app_context():
            members = GroupMapper.get_group_members(sample_group)
            assert len(members) == 1
            assert members[0].id == sample_user


class TestUserMapper:
    """Test UserMapper functionality."""
    
    def test_find_by_id(self, app, sample_user):
        """Test finding user by ID."""
        with app.app_context():
            user = UserMapper.find_by_id(sample_user)
            assert user is not None
            assert user.id == sample_user
            assert user.username == sample_user.username
    
    def test_find_by_email(self, app, sample_user):
        """Test finding user by email."""
        with app.app_context():
            user = UserMapper.find_by_email(sample_user.email)
            assert user is not None
            assert user.email == sample_user.email
    
    def test_find_by_google_id(self, app, sample_user):
        """Test finding user by Google ID."""
        with app.app_context():
            user = UserMapper.find_by_google_id(sample_user.google_id)
            assert user is not None
            assert user.google_id == sample_user.google_id
    
    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = UserMapper.create_user(
                username='newuser',
                email='newuser@example.com',
                first_name='New',
                last_name='User',
                google_id='new-google-id'
            )
            assert user is not None
            assert user.username == 'newuser'
            assert user.email == 'newuser@example.com'
            assert user.first_name == 'New'
            assert user.last_name == 'User'
            assert user.google_id == 'new-google-id'
    
    def test_update_user(self, app, sample_user):
        """Test updating user information."""
        with app.app_context():
            updated_user = UserMapper.update_user(
                sample_user,
                first_name='Updated',
                last_name='Name',
                country='USA'
            )
            assert updated_user.first_name == 'Updated'
            assert updated_user.last_name == 'Name'
            assert updated_user.country == 'USA'


class TestScanMapper:
    """Test ScanMapper functionality."""
    
    def test_create_scan(self, app, sample_group, sample_user):
        """Test creating a new scan."""
        with app.app_context():
            scan = ScanMapper.create_scan(
                'nginx',
                'latest',
                'trivy',
                sample_group,
                sample_user
            )
            assert scan is not None
            assert scan.image_name == 'nginx'
            assert scan.image_tag == 'latest'
            assert scan.scanner_type == 'trivy'
            assert scan.group_id == sample_group
            assert scan.creator_id == sample_user
    
    def test_update_scan(self, app, sample_scan):
        """Test updating scan information."""
        with app.app_context():
            updated_scan = ScanMapper.update_scan(
                sample_scan,
                scan_status='COMPLETED',
                scan_duration_seconds=60,
                scanner_version='0.46.0',
                scan_output='Scan completed successfully',
                critical_count=2,
                high_count=3,
                medium_count=4,
                low_count=5
            )
            assert updated_scan.scan_status == 'COMPLETED'
            assert updated_scan.scan_duration_seconds == 60
            assert updated_scan.scanner_version == '0.46.0'
            assert updated_scan.critical_count == 2
            assert updated_scan.high_count == 3
            assert updated_scan.medium_count == 4
            assert updated_scan.low_count == 5
    
    def test_get_scans_by_group(self, app, sample_group, sample_scan):
        """Test getting scans by group."""
        with app.app_context():
            scans = ScanMapper.get_scans_by_group(sample_group)
            assert len(scans) == 1
            assert scans[0].id == sample_scan
    
    def test_get_scan_by_id(self, app, sample_scan):
        """Test getting scan by ID."""
        with app.app_context():
            scan = ScanMapper.get_scan_by_id(sample_scan)
            assert scan is not None
            assert scan.id == sample_scan
    
    def test_get_scan_statistics(self, app, sample_group, sample_scan):
        """Test getting scan statistics."""
        with app.app_context():
            stats = ScanMapper.get_scan_statistics(sample_group)
            assert stats['total_scans'] == 1
            assert stats['successful_scans'] == 1
            assert stats['failed_scans'] == 0
            assert stats['critical_vulnerabilities'] == 1
            assert stats['high_vulnerabilities'] == 2
            assert stats['medium_vulnerabilities'] == 3
            assert stats['low_vulnerabilities'] == 4


class TestVulnerabilityMapper:
    """Test VulnerabilityMapper functionality."""
    
    def test_create_vulnerability(self, app, sample_scan):
        """Test creating a new vulnerability."""
        with app.app_context():
            vuln = VulnerabilityMapper.create_vulnerability(
                sample_scan,
                'CVE-2021-12345',
                'HIGH',
                'openssl',
                '1.1.1f',
                '1.1.1j',
                'Buffer overflow in OpenSSL',
                6.5,
                'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H',
                '2021-03-15',
                '2021-03-15',
                ['https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-12345']
            )
            assert vuln is not None
            assert vuln.scan_id == sample_scan
            assert vuln.cve_id == 'CVE-2021-12345'
            assert vuln.severity == 'HIGH'
            assert vuln.package_name == 'openssl'
            assert vuln.package_version == '1.1.1f'
            assert vuln.fixed_version == '1.1.1j'
            assert vuln.description == 'Buffer overflow in OpenSSL'
            assert vuln.cvss_score == 6.5
    
    def test_get_vulnerabilities_by_scan(self, app, sample_scan, sample_vulnerabilities):
        """Test getting vulnerabilities by scan."""
        with app.app_context():
            vulns = VulnerabilityMapper.get_vulnerabilities_by_scan(sample_scan)
            assert len(vulns) == 2
            assert vulns[0].scan_id == sample_scan
            assert vulns[1].scan_id == sample_scan
    
    def test_get_vulnerability_counts(self, app, sample_scan, sample_vulnerabilities):
        """Test getting vulnerability counts."""
        with app.app_context():
            counts = VulnerabilityMapper.get_vulnerability_counts(sample_scan)
            assert counts['CRITICAL'] == 1
            assert counts['HIGH'] == 1
            assert counts['MEDIUM'] == 0
            assert counts['LOW'] == 0
    
    def test_delete_vulnerabilities_by_scan(self, app, sample_scan, sample_vulnerabilities):
        """Test deleting vulnerabilities by scan."""
        with app.app_context():
            VulnerabilityMapper.delete_vulnerabilities_by_scan(sample_scan)
            
            # Verify vulnerabilities are deleted
            vulns = VulnerabilityMapper.get_vulnerabilities_by_scan(sample_scan)
            assert len(vulns) == 0
    
    def test_get_vulnerabilities_by_severity(self, app, sample_scan, sample_vulnerabilities):
        """Test getting vulnerabilities by severity."""
        with app.app_context():
            critical_vulns = VulnerabilityMapper.get_vulnerabilities_by_severity(
                sample_scan, 'CRITICAL'
            )
            assert len(critical_vulns) == 1
            assert critical_vulns[0].severity == 'CRITICAL'
            
            high_vulns = VulnerabilityMapper.get_vulnerabilities_by_severity(
                sample_scan, 'HIGH'
            )
            assert len(high_vulns) == 1
            assert high_vulns[0].severity == 'HIGH'
