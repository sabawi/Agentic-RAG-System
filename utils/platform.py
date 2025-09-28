"""
Cross-platform utility functions for Windows 11+ and Linux compatibility
"""

import os
import platform
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging

try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)

class PlatformDetector:
    """Detect platform and provide OS-specific configurations"""
    
    @staticmethod
    def get_platform() -> str:
        """Get normalized platform name"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif system == "darwin":
            return "macos"
        else:
            logger.warning(f"Unknown platform: {system}, defaulting to linux")
            return "linux"
    
    @staticmethod
    def get_platform_config() -> Dict[str, Any]:
        """Get platform-specific configuration"""
        current_platform = PlatformDetector.get_platform()
        
        configs = {
            "windows": {
                "temp_dir": Path(os.environ.get("TEMP", "C:/temp")) / "agentic_rag",
                "config_dir": Path(os.environ.get("APPDATA", "C:/Users/Default/AppData/Roaming")) / "agentic_rag",
                "log_dir": Path(os.environ.get("LOCALAPPDATA", "C:/Users/Default/AppData/Local")) / "agentic_rag" / "logs",
                "path_separator": "\\",
                "line_ending": "\r\n",
                "shell": ["cmd", "/c"],
                "executable_extension": ".exe"
            },
            "linux": {
                "temp_dir": Path("/tmp") / "agentic_rag",
                "config_dir": Path.home() / ".config" / "agentic_rag", 
                "log_dir": Path.home() / ".local" / "share" / "agentic_rag" / "logs",
                "path_separator": "/",
                "line_ending": "\n",
                "shell": ["/bin/bash", "-c"],
                "executable_extension": ""
            },
            "macos": {
                "temp_dir": Path(tempfile.gettempdir()) / "agentic_rag",
                "config_dir": Path.home() / ".config" / "agentic_rag",
                "log_dir": Path.home() / ".local" / "share" / "agentic_rag" / "logs", 
                "path_separator": "/",
                "line_ending": "\n",
                "shell": ["/bin/bash", "-c"],
                "executable_extension": ""
            }
        }
        
        return configs.get(current_platform, configs["linux"])
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return PlatformDetector.get_platform() == "windows"
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return PlatformDetector.get_platform() == "linux"
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return PlatformDetector.get_platform() == "macos"

class CrossPlatformPaths:
    """Cross-platform path handling utilities"""
    
    def __init__(self):
        self.config = PlatformDetector.get_platform_config()
    
    def get_temp_dir(self) -> Path:
        """Get platform-appropriate temporary directory"""
        temp_dir = self.config["temp_dir"]
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def get_config_dir(self) -> Path:
        """Get platform-appropriate configuration directory"""
        config_dir = self.config["config_dir"]
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_log_dir(self) -> Path:
        """Get platform-appropriate log directory"""
        log_dir = self.config["log_dir"]
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def normalize_path(self, path: str) -> Path:
        """Convert string path to normalized Path object"""
        return Path(path).resolve()
    
    def get_temp_file(self, prefix: str = "temp", suffix: str = ".tmp") -> Path:
        """Get a temporary file path"""
        return self.get_temp_dir() / f"{prefix}_{os.getpid()}_{suffix}"
    
    def safe_path(self, *parts) -> Path:
        """Safely join path parts across platforms"""
        return Path(*parts).resolve()

class ProcessManager:
    """Cross-platform process management"""
    
    @staticmethod
    def run_command(command: str, shell: bool = True, capture_output: bool = True):
        """Run command cross-platform"""
        import subprocess
        
        platform_config = PlatformDetector.get_platform_config()
        
        if shell and PlatformDetector.is_windows():
            # Windows shell command
            full_command = platform_config["shell"] + [command]
        elif shell:
            # Unix shell command
            full_command = platform_config["shell"] + [command]
        else:
            # Direct command
            full_command = command.split() if isinstance(command, str) else command
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=capture_output,
                text=True,
                shell=False  # We handle shell ourselves
            )
            return result
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise
    
    @staticmethod
    def is_service_running(service_name: str) -> bool:
        """Check if a service is running (cross-platform)"""
        try:
            if PlatformDetector.is_windows():
                # Windows service check
                result = ProcessManager.run_command(
                    f'sc query "{service_name}"',
                    capture_output=True
                )
                return "RUNNING" in result.stdout
            else:
                # Linux service check (systemd)
                result = ProcessManager.run_command(
                    f'systemctl is-active {service_name}',
                    capture_output=True
                )
                return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def restart_service(service_name: str) -> bool:
        """Restart a service (cross-platform)"""
        try:
            if PlatformDetector.is_windows():
                # Windows service restart
                ProcessManager.run_command(f'net stop "{service_name}"')
                ProcessManager.run_command(f'net start "{service_name}"')
            else:
                # Linux service restart
                ProcessManager.run_command(f'sudo systemctl restart {service_name}')
            return True
        except Exception as e:
            logger.error(f"Service restart failed: {e}")
            return False

class EnvironmentManager:
    """Cross-platform environment variable management"""
    
    @staticmethod
    def expand_env_vars(text: str) -> str:
        """Expand environment variables in text"""
        # Load .env file if available and not already loaded
        if _DOTENV_AVAILABLE and not hasattr(EnvironmentManager, '_dotenv_loaded'):
            try:
                # Look for .env file in current directory and parent directories
                env_file = Path.cwd() / '.env'
                if env_file.exists():
                    load_dotenv(env_file)
                    logger.info(f"🔧 Loaded environment variables from {env_file}")
                else:
                    # Try parent directory
                    parent_env = Path.cwd().parent / '.env'
                    if parent_env.exists():
                        load_dotenv(parent_env)
                        logger.info(f"🔧 Loaded environment variables from {parent_env}")
                EnvironmentManager._dotenv_loaded = True
            except Exception as e:
                logger.warning(f"⚠️ Failed to load .env file: {e}")

        return os.path.expandvars(text)
    
    @staticmethod
    def get_env_with_fallback(key: str, fallback: str = None) -> str:
        """Get environment variable with fallback"""
        return os.environ.get(key, fallback)
    
    @staticmethod
    def set_env_var(key: str, value: str, persistent: bool = False):
        """Set environment variable"""
        os.environ[key] = value
        
        if persistent:
            if PlatformDetector.is_windows():
                # Windows registry setting (requires admin)
                try:
                    ProcessManager.run_command(
                        f'setx {key} "{value}"',
                        capture_output=True
                    )
                except Exception as e:
                    logger.warning(f"Could not set persistent env var on Windows: {e}")
            else:
                # Unix shell profile (basic implementation)
                profile_file = Path.home() / ".bashrc"
                if profile_file.exists():
                    with open(profile_file, "a") as f:
                        f.write(f"\nexport {key}='{value}'\n")

# Global instances for convenience
platform_paths = CrossPlatformPaths()
process_manager = ProcessManager()
env_manager = EnvironmentManager()

def get_platform_info() -> Dict[str, Any]:
    """Get comprehensive platform information"""
    return {
        "platform": PlatformDetector.get_platform(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "config": PlatformDetector.get_platform_config(),
        "paths": {
            "temp": str(platform_paths.get_temp_dir()),
            "config": str(platform_paths.get_config_dir()),
            "logs": str(platform_paths.get_log_dir())
        }
    }