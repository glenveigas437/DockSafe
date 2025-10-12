"""
Unit tests for DockSafe models.
"""

import pytest
from datetime import datetime
from app.models import User, Group, VulnerabilityScan, Vulnerability, user_groups
from app import db


class TestUser:
    """Test User model functionality."""
    
    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                google_id='test-google-id',
                picture_url='https://example.com/avatar.jpg',
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.first_name == 'Test'
            assert user.last_name == 'User'
            assert user.google_id == 'test-google-id'
            assert user.email_verified is True
            assert user.is_active is True
            assert user.created_at is not None
    
    def test_user_repr(self, sample_user):
        """Test User string representation."""
        assert repr(sample_user) == f'<User {sample_user.username}>'
    
    def test_user_to_dict(self, sample_user):
        """Test User to_dict method."""
        user_dict = sample_user.to_dict()
        
        assert isinstance(user_dict, dict)
        assert user_dict['id'] == sample_user
        assert user_dict['username'] == sample_user.username
        assert user_dict['email'] == sample_user.email
        assert user_dict['first_name'] == sample_user.first_name
        assert user_dict['last_name'] == sample_user.last_name
        assert user_dict['google_id'] == sample_user.google_id
        assert user_dict['email_verified'] == sample_user.email_verified
        assert user_dict['is_active'] == sample_user.is_active
    
    def test_user_get_role_in_group(self, app, sample_user, sample_group):
        """Test getting user role in a group."""
        with app.app_context():
            # Test when user is in group
            role = sample_user.get_role_in_group(sample_group)
            assert role == 'owner'
            
            # Test when user is not in group
            new_group = Group(
                name='Another Group',
                description='Another test group',
                created_by=sample_user
            )
            db.session.add(new_group)
            db.session.commit()
            
            role = sample_user.get_role_in_group(new_group.id)
            assert role is None


class TestGroup:
    """Test Group model functionality."""
    
    def test_create_group(self, app, sample_user):
        """Test creating a new group."""
        with app.app_context():
            group = Group(
                name='Test Group',
                description='A test group',
                created_by=sample_user
            )
            db.session.add(group)
            db.session.commit()
            
            assert group.id is not None
            assert group.name == 'Test Group'
            assert group.description == 'A test group'
            assert group.created_by == sample_user
            assert group.created_at is not None
    
    def test_group_repr(self, sample_group):
        """Test Group string representation."""
        assert repr(sample_group) == f'<Group {sample_group.name}>'
    
    def test_group_to_dict(self, sample_group):
        """Test Group to_dict method."""
        group_dict = sample_group.to_dict()
        
        assert isinstance(group_dict, dict)
        assert group_dict['id'] == sample_group
        assert group_dict['name'] == sample_group.name
        assert group_dict['description'] == sample_group.description
        assert group_dict['created_by'] == sample_group.created_by
    
    def test_group_members_relationship(self, app, sample_user, sample_group):
        """Test group members relationship."""
        with app.app_context():
            # Add another user to the group
            user2 = User(
                username='testuser2',
                email='test2@example.com',
                first_name='Test2',
                last_name='User2'
            )
            db.session.add(user2)
            db.session.commit()
            
            # Add user2 to group
            db.session.execute(
                user_groups.insert().values(
                    user_id=user2.id,
                    group_id=sample_group,
                    role='member'
                )
            )
            db.session.commit()
            
            # Test members relationship
            members = list(sample_group.members)
            assert len(members) == 2
            assert sample_user in members
            assert user2 in members


class TestVulnerabilityScan:
    """Test VulnerabilityScan model functionality."""
    
    def test_create_scan(self, app, sample_group, sample_user):
        """Test creating a new vulnerability scan."""
        with app.app_context():
            scan = VulnerabilityScan(
                image_name='nginx',
                image_tag='latest',
                scanner_type='trivy',
                group_id=sample_group,
                creator_id=sample_user,
                scan_status='SUCCESS',
                scan_duration_seconds=30,
                scanner_version='0.45.0',
                scan_output='Scan completed successfully',
                critical_count=1,
                high_count=2,
                medium_count=3,
                low_count=4
            )
            db.session.add(scan)
            db.session.commit()
            
            assert scan.id is not None
            assert scan.image_name == 'nginx'
            assert scan.image_tag == 'latest'
            assert scan.scanner_type == 'trivy'
            assert scan.group_id == sample_group
            assert scan.creator_id == sample_user
            assert scan.scan_status == 'SUCCESS'
            assert scan.scan_duration_seconds == 30
            assert scan.scanner_version == '0.45.0'
            assert scan.critical_count == 1
            assert scan.high_count == 2
            assert scan.medium_count == 3
            assert scan.low_count == 4
    
    def test_scan_repr(self, sample_scan):
        """Test VulnerabilityScan string representation."""
        expected = f'<VulnerabilityScan {sample_scan.image_name}:{sample_scan.image_tag}>'
        assert repr(sample_scan) == expected
    
    def test_scan_to_dict(self, sample_scan):
        """Test VulnerabilityScan to_dict method."""
        scan_dict = sample_scan.to_dict()
        
        assert isinstance(scan_dict, dict)
        assert scan_dict['id'] == sample_scan
        assert scan_dict['image_name'] == sample_scan.image_name
        assert scan_dict['image_tag'] == sample_scan.image_tag
        assert scan_dict['scanner_type'] == sample_scan.scanner_type
        assert scan_dict['group_id'] == sample_scan.group_id
        assert scan_dict['creator_id'] == sample_scan.creator_id
        assert scan_dict['scan_status'] == sample_scan.scan_status
        assert scan_dict['critical_count'] == sample_scan.critical_count
        assert scan_dict['high_count'] == sample_scan.high_count
        assert scan_dict['medium_count'] == sample_scan.medium_count
        assert scan_dict['low_count'] == sample_scan.low_count


class TestVulnerability:
    """Test Vulnerability model functionality."""
    
    def test_create_vulnerability(self, app, sample_scan):
        """Test creating a new vulnerability."""
        with app.app_context():
            vuln = Vulnerability(
                scan_id=sample_scan,
                cve_id='CVE-2021-23017',
                severity='CRITICAL',
                package_name='nginx',
                package_version='1.18.0',
                fixed_version='1.20.1',
                description='Buffer overflow in nginx HTTP/2 implementation',
                cvss_score=7.5,
                cvss_vector='CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H',
                published_date='2021-05-25',
                last_modified_date='2021-05-25',
                references=['https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-23017']
            )
            db.session.add(vuln)
            db.session.commit()
            
            assert vuln.id is not None
            assert vuln.scan_id == sample_scan
            assert vuln.cve_id == 'CVE-2021-23017'
            assert vuln.severity == 'CRITICAL'
            assert vuln.package_name == 'nginx'
            assert vuln.package_version == '1.18.0'
            assert vuln.fixed_version == '1.20.1'
            assert vuln.description == 'Buffer overflow in nginx HTTP/2 implementation'
            assert vuln.cvss_score == 7.5
            assert vuln.cvss_vector == 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H'
    
    def test_vulnerability_repr(self, sample_vulnerabilities):
        """Test Vulnerability string representation."""
        vuln = sample_vulnerabilities[0]
        expected = f'<Vulnerability {vuln.cve_id} - {vuln.severity}>'
        assert repr(vuln) == expected
    
    def test_vulnerability_to_dict(self, sample_vulnerabilities):
        """Test Vulnerability to_dict method."""
        vuln = sample_vulnerabilities[0]
        vuln_dict = vuln.to_dict()
        
        assert isinstance(vuln_dict, dict)
        assert vuln_dict['id'] == vuln.id
        assert vuln_dict['scan_id'] == vuln.scan_id
        assert vuln_dict['cve_id'] == vuln.cve_id
        assert vuln_dict['severity'] == vuln.severity
        assert vuln_dict['package_name'] == vuln.package_name
        assert vuln_dict['package_version'] == vuln.package_version
        assert vuln_dict['fixed_version'] == vuln.fixed_version
        assert vuln_dict['description'] == vuln.description
        assert vuln_dict['cvss_score'] == vuln.cvss_score
        assert vuln_dict['cvss_vector'] == vuln.cvss_vector
