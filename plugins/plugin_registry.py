"""
Plugin Registry - Discovery and metadata management
Scans /plugins/ directory for YAML definitions and loads plugin metadata.

Author: Agentic-RAG System
Created: 2025-10-02
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginDefinition:
    """
    Plugin metadata and configuration.
    Represents a complete plugin definition loaded from YAML.
    """
    # Metadata
    name: str
    version: str
    category: str
    author: str
    description: str
    license: Optional[str] = None
    homepage: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Execution configuration
    execution_type: str = "python"
    handler: str = ""
    entrypoint: str = "execute"
    timeout: int = 60
    memory_limit: int = 256
    cpu_limit: float = 1.0
    environment: Dict[str, str] = field(default_factory=dict)

    # Parameters (JSON Schema)
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Security configuration
    security: Dict[str, Any] = field(default_factory=dict)

    # Monitoring configuration
    monitoring: Dict[str, Any] = field(default_factory=dict)

    # Dependencies
    dependencies: Dict[str, Any] = field(default_factory=dict)

    # Error handling configuration
    error_handling: Dict[str, Any] = field(default_factory=dict)

    # Internal tracking
    _yaml_path: Optional[Path] = None
    _failure_count: int = 0

    @property
    def handler_path(self) -> Path:
        """Get absolute path to plugin handler"""
        if self._yaml_path:
            plugins_dir = self._yaml_path.parent
            return (plugins_dir / self.handler).resolve()
        return Path(self.handler)

    def __str__(self) -> str:
        return f"PluginDefinition(name='{self.name}', version='{self.version}', category='{self.category}')"


class PluginRegistry:
    """
    Plugin discovery and metadata management.
    Scans /plugins/ directory for YAML definitions (flat structure).
    """

    def __init__(self, plugins_dir: Path, config: Dict[str, Any]):
        """
        Initialize Plugin Registry.

        Args:
            plugins_dir: Path to /plugins/ directory
            config: Plugin configuration from llm_config.yaml
        """
        self.plugins_dir = Path(plugins_dir)
        self.config = config
        self.defaults = self._load_defaults()

        logger.info(f"PluginRegistry initialized: {self.plugins_dir}")

    async def discover_plugins(self) -> List[PluginDefinition]:
        """
        Discover all plugins from /plugins/ directory (flat structure).

        Returns:
            List of PluginDefinition objects
        """
        plugins = []

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return plugins

        # Scan for YAML files in /plugins/ root (flat structure)
        yaml_files = list(self.plugins_dir.glob('*.yaml')) + list(self.plugins_dir.glob('*.yml'))

        logger.info(f"Found {len(yaml_files)} plugin YAML files")

        for yaml_file in yaml_files:
            try:
                plugin_def = await self._load_plugin_definition(yaml_file)
                if plugin_def:
                    plugins.append(plugin_def)
                    logger.info(f"✅ Discovered plugin: {plugin_def.name} v{plugin_def.version} (category: {plugin_def.category})")
            except Exception as e:
                logger.error(f"Failed to load plugin {yaml_file.name}: {e}", exc_info=True)

        logger.info(f"Successfully loaded {len(plugins)} plugins across {self._get_category_count(plugins)} categories")
        return plugins

    async def _load_plugin_definition(self, yaml_file: Path) -> Optional[PluginDefinition]:
        """
        Load and validate plugin definition from YAML file.

        Args:
            yaml_file: Path to plugin YAML file

        Returns:
            PluginDefinition object or None if invalid
        """
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            # Validate required top-level fields
            required_fields = ['metadata', 'execution', 'parameters']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Plugin {yaml_file.name}: Missing required field '{field}'")
                    return None

            metadata = data['metadata']
            execution = data['execution']

            # Validate required metadata fields
            required_metadata = ['name', 'version', 'category', 'author', 'description']
            for field in required_metadata:
                if field not in metadata:
                    logger.error(f"Plugin {yaml_file.name}: Missing required metadata field '{field}'")
                    return None

            # Validate required execution fields
            required_execution = ['type', 'handler', 'entrypoint']
            for field in required_execution:
                if field not in execution:
                    logger.error(f"Plugin {yaml_file.name}: Missing required execution field '{field}'")
                    return None

            # Merge with default settings
            merged_security = {**self.defaults.get('security', {}), **data.get('security', {})}
            merged_monitoring = {**self.defaults.get('monitoring', {}), **data.get('monitoring', {})}
            merged_error_handling = {**self.defaults.get('error_handling', {}), **data.get('error_handling', {})}

            # Create PluginDefinition object
            plugin_def = PluginDefinition(
                # Metadata
                name=metadata['name'],
                version=metadata['version'],
                category=metadata['category'],
                author=metadata['author'],
                description=metadata['description'],
                license=metadata.get('license'),
                homepage=metadata.get('homepage'),
                tags=metadata.get('tags', []),

                # Execution
                execution_type=execution['type'],
                handler=execution['handler'],
                entrypoint=execution['entrypoint'],
                timeout=execution.get('timeout', self.defaults['execution']['timeout']),
                memory_limit=execution.get('memory_limit', self.defaults['execution']['memory_limit']),
                cpu_limit=execution.get('cpu_limit', self.defaults['execution']['cpu_limit']),
                environment=execution.get('environment', {}),

                # Parameters
                parameters=data['parameters'],

                # Security
                security=merged_security,

                # Monitoring
                monitoring=merged_monitoring,

                # Dependencies
                dependencies=data.get('dependencies', {}),

                # Error handling
                error_handling=merged_error_handling,

                # Internal
                _yaml_path=yaml_file
            )

            return plugin_def

        except yaml.YAMLError as e:
            logger.error(f"Plugin {yaml_file.name}: YAML parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Plugin {yaml_file.name}: Unexpected error: {e}", exc_info=True)
            return None

    def _load_defaults(self) -> Dict[str, Any]:
        """
        Load default plugin settings from config/plugin_defaults.yaml.

        Returns:
            Dict with default settings

        Raises:
            ValueError: If plugin_defaults.yaml not found (fail-fast)
        """
        defaults_file = self.plugins_dir / 'config' / 'plugin_defaults.yaml'

        if not defaults_file.exists():
            raise ValueError(
                f"Plugin defaults configuration required: {defaults_file}\n"
                "See /plugins/config/plugin_defaults.yaml"
            )

        try:
            with open(defaults_file, 'r') as f:
                defaults = yaml.safe_load(f)

            logger.info(f"Loaded plugin defaults from {defaults_file}")
            return defaults

        except Exception as e:
            raise ValueError(f"Failed to load plugin defaults: {e}")

    def _get_category_count(self, plugins: List[PluginDefinition]) -> int:
        """Get number of distinct categories"""
        return len(set(p.category for p in plugins))


# =============================================================================
# Utility Functions
# =============================================================================

def get_plugin_by_name(plugins: List[PluginDefinition], name: str) -> Optional[PluginDefinition]:
    """
    Get a plugin by its name.

    Args:
        plugins: List of plugin definitions
        name: Name of the plugin to find

    Returns:
        PluginDefinition or None if not found
    """
    for plugin in plugins:
        if plugin.name == name:
            return plugin
    return None


def get_plugins_by_category(plugins: List[PluginDefinition], category: str) -> List[PluginDefinition]:
    """
    Get all plugins in a specific category.

    Args:
        plugins: List of plugin definitions
        category: Category to filter by

    Returns:
        List of plugins in the category
    """
    return [p for p in plugins if p.category == category]


def get_all_categories(plugins: List[PluginDefinition]) -> List[str]:
    """
    Get list of all unique categories.

    Args:
        plugins: List of plugin definitions

    Returns:
        Sorted list of category names
    """
    return sorted(set(p.category for p in plugins))
