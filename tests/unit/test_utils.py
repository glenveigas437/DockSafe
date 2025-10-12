"""
Unit tests for DockSafe utility functions.
"""

import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from app.utils.validation_utils import ValidationUtils, PasswordUtils
from app.utils.common_utils import LoggingUtils, JSONUtils, ErrorHandlingUtils
from app.utils.system_utils import SystemUtils, FileUtils, DockerUtils


class TestValidationUtils:
    """Test ValidationUtils functionality."""
    
    def test_is_valid_email(self):
        """Test email validation."""
        # Valid emails
        assert ValidationUtils.is_valid_email('test@example.com') is True
        assert ValidationUtils.is_valid_email('user.name@domain.co.uk') is True
        assert ValidationUtils.is_valid_email('test+tag@example.org') is True
        
        # Invalid emails
        assert ValidationUtils.is_valid_email('invalid-email') is False
        assert ValidationUtils.is_valid_email('@example.com') is False
        assert ValidationUtils.is_valid_email('test@') is False
        assert ValidationUtils.is_valid_email('') is False
        
        # Test None handling
        try:
            ValidationUtils.is_valid_email(None)
            assert False, "Should have raised TypeError for None input"
        except TypeError:
            pass
    
    def test_is_valid_image_name(self):
        """Test image name validation."""
        # Valid image names
        assert ValidationUtils.is_valid_image_name('nginx') is True
        assert ValidationUtils.is_valid_image_name('ubuntu') is True
        assert ValidationUtils.is_valid_image_name('registry.com/image') is True
        assert ValidationUtils.is_valid_image_name('my-org/my-app') is True
        
        # Invalid image names
        assert ValidationUtils.is_valid_image_name('') is False
        assert ValidationUtils.is_valid_image_name('invalid name') is False
        assert ValidationUtils.is_valid_image_name('invalid@name') is False
        assert ValidationUtils.is_valid_image_name('invalid#name') is False
    
    def test_is_valid_image_tag(self):
        """Test image tag validation."""
        # Valid tags
        assert ValidationUtils.is_valid_image_tag('latest') is True
        assert ValidationUtils.is_valid_image_tag('1.0.0') is True
        assert ValidationUtils.is_valid_image_tag('v2.1.3') is True
        assert ValidationUtils.is_valid_image_tag('dev') is True
        
        # Invalid tags
        assert ValidationUtils.is_valid_image_tag('') is False
        assert ValidationUtils.is_valid_image_tag('tag/with/slash') is False
    
    def test_hash_password(self):
        """Test password hashing."""
        password = 'testpassword123'
        hashed = PasswordUtils.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
        # Test that same password produces different hashes (due to salt)
        hashed2 = PasswordUtils.hash_password(password)
        assert hashed != hashed2
    
    def test_check_password(self):
        """Test password verification."""
        password = 'testpassword123'
        hashed = PasswordUtils.hash_password(password)
        
        # Correct password should verify
        assert PasswordUtils.check_password(password, hashed) is True
        
        # Wrong password should not verify
        assert PasswordUtils.check_password('wrongpassword', hashed) is False
        assert PasswordUtils.check_password('', hashed) is False


class TestLoggingUtils:
    """Test LoggingUtils functionality."""
    
    def test_setup_logger(self):
        """Test logger setup."""
        logger = LoggingUtils.setup_logger('test_logger')
        
        assert logger is not None
        assert logger.name == 'test_logger'
        assert logger.level == 20  # INFO level
    
    def test_log_request(self):
        """Test request logging."""
        logger = LoggingUtils.setup_logger('test_logger')
        
        # This should not raise an exception
        LoggingUtils.log_request(
            logger, 
            '/test/endpoint', 
            'GET', 
            user_id=123,
            extra_param='test'
        )
    
    def test_log_error(self):
        """Test error logging."""
        logger = LoggingUtils.setup_logger('test_logger')
        
        # This should not raise an exception
        try:
            raise ValueError('Test error')
        except ValueError as e:
            LoggingUtils.log_error(logger, e, 'test_context')
    
    def test_log_scan_event(self):
        """Test scan event logging."""
        logger = LoggingUtils.setup_logger('test_logger')
        
        # This should not raise an exception
        LoggingUtils.log_scan_event(
            logger,
            'scan_started',
            'nginx',
            'latest',
            user_id=123,
            scan_id=456
        )


class TestJSONUtils:
    """Test JSONUtils functionality."""
    
    def test_safe_json_loads(self):
        """Test safe JSON loading."""
        # Valid JSON
        valid_json = '{"key": "value", "number": 123}'
        result = JSONUtils.safe_json_loads(valid_json)
        assert result == {"key": "value", "number": 123}
        
        # Invalid JSON
        invalid_json = '{"key": "value", "number": 123'  # Missing closing brace
        result = JSONUtils.safe_json_loads(invalid_json)
        assert result is None
        
        # Invalid JSON with default
        result = JSONUtils.safe_json_loads(invalid_json, default={})
        assert result == {}
        
        # None input
        result = JSONUtils.safe_json_loads(None)
        assert result is None
    
    def test_safe_json_dumps(self):
        """Test safe JSON dumping."""
        # Valid object
        obj = {"key": "value", "number": 123}
        result = JSONUtils.safe_json_dumps(obj)
        assert result == '{"key": "value", "number": 123}'
        
        # Invalid object (circular reference)
        obj = {}
        obj['self'] = obj
        result = JSONUtils.safe_json_dumps(obj)
        assert result == "{}"
        
        # Invalid object with default
        result = JSONUtils.safe_json_dumps(obj, default='{"error": "serialization failed"}')
        assert result == '{"error": "serialization failed"}'
    
    def test_extract_json_from_request(self):
        """Test JSON extraction from request."""
        # This would need a Flask request context to test properly
        # For now, we'll test that it returns an empty dict when no context
        result = JSONUtils.extract_json_from_request()
        assert result == {}


class TestSystemUtils:
    """Test SystemUtils functionality."""
    
    @patch('subprocess.run')
    def test_check_command_exists(self, mock_run):
        """Test command existence check."""
        # Command exists
        mock_run.return_value = MagicMock()
        result = SystemUtils.check_command_exists('docker')
        assert result is True
        
        # Command doesn't exist
        mock_run.side_effect = subprocess.CalledProcessError(1, 'which')
        result = SystemUtils.check_command_exists('nonexistent')
        assert result is False
    
    @patch('subprocess.run')
    def test_get_command_version(self, mock_run):
        """Test command version retrieval."""
        # Successful version check
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Docker version 20.10.0'
        mock_run.return_value = mock_result
        
        result = SystemUtils.get_command_version('docker')
        assert result == 'Docker version 20.10.0'
        
        # Failed version check
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker')
        result = SystemUtils.get_command_version('nonexistent')
        assert result is None
    
    @patch('subprocess.run')
    def test_execute_command(self, mock_run):
        """Test command execution."""
        # Successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Command output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        
        result = SystemUtils.execute_command(['echo', 'test'])
        assert result['success'] is True
        assert result['stdout'] == 'Command output'
        assert result['stderr'] == ''
        assert result['returncode'] == 0
        
        # Failed execution
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Command failed'
        
        result = SystemUtils.execute_command(['invalid', 'command'])
        assert result['success'] is False
        assert result['stdout'] == ''
        assert result['stderr'] == 'Command failed'
        assert result['returncode'] == 1


class TestFileUtils:
    """Test FileUtils functionality."""
    
    def test_create_temp_file(self):
        """Test temporary file creation."""
        content = 'Test file content'
        file_path = FileUtils.create_temp_file(content, '.txt')
        
        assert file_path is not None
        assert os.path.exists(file_path)
        
        # Read the file to verify content
        with open(file_path, 'r') as f:
            assert f.read() == content
        
        # Clean up
        FileUtils.cleanup_temp_file(file_path)
        assert not os.path.exists(file_path)
    
    def test_read_file_safely(self):
        """Test safe file reading."""
        # Create a test file
        content = 'Test content'
        file_path = FileUtils.create_temp_file(content)
        
        # Read existing file
        result = FileUtils.read_file_safely(file_path)
        assert result == content
        
        # Read non-existent file
        result = FileUtils.read_file_safely('/nonexistent/file.txt')
        assert result is None
        
        # Clean up
        FileUtils.cleanup_temp_file(file_path)
    
    def test_write_file_safely(self):
        """Test safe file writing."""
        content = 'Test write content'
        file_path = '/tmp/test_write_file.txt'
        
        # Write to file
        result = FileUtils.write_file_safely(file_path, content)
        assert result is True
        
        # Verify content
        with open(file_path, 'r') as f:
            assert f.read() == content
        
        # Clean up
        os.unlink(file_path)


class TestDockerUtils:
    """Test DockerUtils functionality."""
    
    @patch('app.utils.system_utils.SystemUtils.check_command_exists')
    def test_is_docker_available(self, mock_check):
        """Test Docker availability check."""
        # Docker available
        mock_check.return_value = True
        result = DockerUtils.is_docker_available()
        assert result is True
        
        # Docker not available
        mock_check.return_value = False
        result = DockerUtils.is_docker_available()
        assert result is False
