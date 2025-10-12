"""
Test configuration and fixtures for DockSafe tests.
"""

import os
import pytest
import tempfile
from flask import Flask
from app import create_app, db
from app.models import User, Group, VulnerabilityScan, Vulnerability


@pytest.fixture(scope="function")
def app():
    """Create application for testing."""
    # Create a temporary database file for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'GOOGLE_CLIENT_ID': 'test-client-id',
        'GOOGLE_CLIENT_SECRET': 'test-client-secret',
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            first_name='Test',
            last_name='User',
            google_id=f'test-google-id-{unique_id}',
            picture_url='https://example.com/avatar.jpg',
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()
        return user.id  # Return ID instead of object to avoid detachment issues


@pytest.fixture
def sample_group(app, sample_user):
    """Create a sample group for testing."""
    with app.app_context():
        group = Group(
            name='Test Group',
            description='A test group',
            created_by=sample_user  # sample_user is now an ID
        )
        db.session.add(group)
        db.session.commit()
        
        # Add user to group
        from app.models import user_groups
        db.session.execute(
            user_groups.insert().values(
                user_id=sample_user,  # sample_user is now an ID
                group_id=group.id,
                role='owner'
            )
        )
        db.session.commit()
        
        return group.id  # Return ID instead of object


@pytest.fixture
def sample_scan(app, sample_group, sample_user):
    """Create a sample vulnerability scan for testing."""
    with app.app_context():
        scan = VulnerabilityScan(
            image_name='nginx',
            image_tag='latest',
            scanner_type='trivy',
            group_id=sample_group,  # sample_group is now an ID
            creator_id=sample_user,  # sample_user is now an ID
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
        return scan.id  # Return ID instead of object


@pytest.fixture
def sample_vulnerabilities(app, sample_scan):
    """Create sample vulnerabilities for testing."""
    with app.app_context():
        from datetime import datetime
        vulnerabilities = [
            Vulnerability(
                scan_id=sample_scan,  # sample_scan is now an ID
                cve_id='CVE-2021-23017',
                severity='CRITICAL',
                package_name='nginx',
                package_version='1.18.0',
                fixed_version='1.20.1',
                description='Buffer overflow in nginx HTTP/2 implementation',
                cvss_score=7.5,
                cvss_vector='CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H',
                published_date=datetime(2021, 5, 25),
                last_modified_date=datetime(2021, 5, 25),
                references=['https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-23017']
            ),
            Vulnerability(
                scan_id=sample_scan,  # sample_scan is now an ID
                cve_id='CVE-2020-12400',
                severity='HIGH',
                package_name='nginx',
                package_version='1.18.0',
                fixed_version='1.19.0',
                description='Memory leak in nginx HTTP/2 implementation',
                cvss_score=5.3,
                cvss_vector='CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L',
                published_date=datetime(2020, 6, 15),
                last_modified_date=datetime(2020, 6, 15),
                references=['https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-12400']
            )
        ]
        
        for vuln in vulnerabilities:
            db.session.add(vuln)
        db.session.commit()
        return [v.id for v in vulnerabilities]  # Return IDs instead of objects


@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers for API testing."""
    return {
        'Authorization': f'Bearer test-token-{sample_user}',  # sample_user is now an ID
        'Content-Type': 'application/json'
    }
