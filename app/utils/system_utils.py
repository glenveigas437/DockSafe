import subprocess
import logging
import shlex
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SystemUtils:
    @staticmethod
    def check_command_exists(command: str) -> bool:
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def get_command_version(command: str) -> Optional[str]:
        try:
            result = subprocess.run([command, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        return None
    
    @staticmethod
    def execute_command(command: List[str], timeout: int = 300) -> Dict[str, Any]:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }

class FileUtils:
    @staticmethod
    def create_temp_file(content: str, suffix: str = '.txt') -> str:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def read_file_safely(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except (FileNotFoundError, PermissionError, IOError):
            return None
    
    @staticmethod
    def write_file_safely(file_path: str, content: str) -> bool:
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except (PermissionError, IOError):
            return False
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        import os
        try:
            os.unlink(file_path)
        except OSError:
            pass

class DockerUtils:
    @staticmethod
    def is_docker_available() -> bool:
        return SystemUtils.check_command_exists('docker')
    
    @staticmethod
    def get_docker_version() -> Optional[str]:
        return SystemUtils.get_command_version('docker')
    
    @staticmethod
    def pull_image(image_name: str, image_tag: str = 'latest') -> Dict[str, Any]:
        command = ['docker', 'pull', f'{image_name}:{image_tag}']
        return SystemUtils.execute_command(command, timeout=600)
    
    @staticmethod
    def inspect_image(image_name: str, image_tag: str = 'latest') -> Dict[str, Any]:
        command = ['docker', 'inspect', f'{image_name}:{image_tag}']
        return SystemUtils.execute_command(command)
    
    @staticmethod
    def list_images() -> Dict[str, Any]:
        command = ['docker', 'images', '--format', 'json']
        return SystemUtils.execute_command(command)

class SecurityUtils:
    @staticmethod
    def sanitize_image_name(image_name: str) -> str:
        return image_name.replace('..', '').replace('/', '_').strip()
    
    @staticmethod
    def sanitize_image_tag(image_tag: str) -> str:
        return image_tag.replace('..', '').replace('/', '_').strip()
    
    @staticmethod
    def validate_image_reference(image_name: str, image_tag: str) -> bool:
        if not image_name or not image_tag:
            return False
        
        if '..' in image_name or '..' in image_tag:
            return False
        
        if len(image_name) > 255 or len(image_tag) > 100:
            return False
        
        return True
        
    
    @staticmethod
    def escape_shell_input(input_str: str) -> str:
        return shlex.quote(input_str)

class PerformanceUtils:
    @staticmethod
    def measure_execution_time(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
