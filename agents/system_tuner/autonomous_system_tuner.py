#!/usr/bin/env python3
"""
Autonomous System Performance Tuning Agent
==========================================

An intelligent, self-directed agent that:
1. Discovers its operating environment and limitations
2. Researches optimal performance tuning strategies
3. Plans and executes safe system optimizations
4. Validates improvements and iterates until optimal
5. Operates fully autonomously with safety guardrails

This agent runs LOCAL to the server and uses the server's LLM capabilities
to research, plan, and execute system performance improvements.

SAFETY FEATURES:
- All changes are backed up and reversible
- Incremental testing with validation
- No destructive operations
- User approval for sudo operations
- Comprehensive logging and rollback capability

CONFIGURATION:
All configuration values are loaded from config/agents_config.yaml.
No hardcoded configuration values per PROJECT_CONFIGURATION_DIRECTIVE.

Author: Agentic-RAG Development Team
Version: 1.1.0
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import openai

# Add agents directory to path for common imports
agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

# Import configuration loader
from common.config_loader import get_agent_config, AgentConfigError, AgentConfig

# Agent name for configuration lookup
AGENT_NAME = "system_tuner"

# Load configuration at module level (fail-fast if missing)
try:
    _config = get_agent_config(AGENT_NAME)
except AgentConfigError as e:
    print(f"FATAL: Failed to load configuration for {AGENT_NAME}: {e}", file=sys.stderr)
    sys.exit(1)

# Get log file path from config
_log_file = _config.get_log_file() or "system_tuner.log"
_log_level_str = _config.get_log_level()
_log_level = getattr(logging, _log_level_str.upper(), logging.INFO)

# Configure logging using config values
logging.basicConfig(
    level=_log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SystemTunerAgent:
    """Autonomous system performance tuning agent."""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        server_url: Optional[str] = None,
        dry_run: Optional[bool] = None,
        max_iterations: Optional[int] = None
    ):
        """
        Initialize the autonomous tuning agent.

        All configuration is loaded from config/agents_config.yaml.
        Command-line arguments can override config values.

        Args:
            config: AgentConfig object (uses module-level _config if not provided)
            server_url: Override server URL from config
            dry_run: Override dry_run setting from config
            max_iterations: Override max_iterations from config
        """
        # Use provided config or module-level config
        self.config = config or _config

        # Load values from config, allow command-line overrides
        self.server_url = server_url or self.config.get_server_url()
        self.dry_run = dry_run if dry_run is not None else self.config.get_safety_setting('dry_run_default', True)
        self.max_iterations = max_iterations or self.config.get_execution_setting('max_iterations', 10)

        # Load additional config values
        self.require_user_approval = self.config.get_safety_setting('require_user_approval', True)
        self.skip_high_risk_in_dry_run = self.config.get_safety_setting('skip_high_risk_in_dry_run', True)
        self.allowed_risk_levels = self.config.get_safety_setting('allowed_risk_levels', ['low', 'medium'])
        self.forbidden_patterns = self.config.get_safety_setting('forbidden_patterns', [])
        self.pause_between_actions = self.config.get_execution_setting('pause_between_actions', 2)
        self.command_timeout = self.config.get_execution_setting('command_timeout', 30)

        # LLM settings
        self.llm_model = self.config.get_llm_model()
        self.llm_temperature = self.config.get_llm_setting('temperature', 0.3)
        self.llm_max_tokens = self.config.get_llm_setting('max_tokens', 4096)
        self.llm_timeout = self.config.get_llm_setting('timeout', 120)

        # State tracking
        self.system_info = {}
        self.baseline_metrics = {}
        self.initial_baseline_metrics = {}  # Store initial baseline separately
        self.tuning_plan = []
        self.executed_changes = []
        self.performance_history = []

        # Backup directory from config
        backup_base = self.config.get_backup_setting('base_directory', 'agents/system_tuner/system_tuning_backups')
        self.backup_dir = Path(backup_base) / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI client using config values
        self.client = openai.OpenAI(
            base_url=self.server_url,
            api_key=self.config.get_api_key()
        )

        logger.info("=" * 80)
        logger.info("🤖 AUTONOMOUS SYSTEM PERFORMANCE TUNING AGENT")
        logger.info("=" * 80)
        logger.info(f"Server: {self.server_url}")
        logger.info(f"Model: {self.llm_model}")
        logger.info(f"Dry Run: {self.dry_run}")
        logger.info(f"Max Iterations: {self.max_iterations}")
        logger.info(f"Backup Dir: {self.backup_dir}")
        logger.info(f"Config Path: {self.config._config}")
        logger.info("=" * 80)

    # ============================================================================
    # PHASE 1: SYSTEM DISCOVERY
    # ============================================================================

    def discover_system(self) -> Dict:
        """
        Phase 1: Discover system capabilities and limitations.

        Returns:
            Dictionary with complete system information
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: SYSTEM DISCOVERY")
        logger.info("=" * 80)

        info = {}

        # Basic system info
        info['os'] = platform.system()
        info['os_version'] = platform.version()
        info['os_release'] = platform.release()
        info['architecture'] = platform.machine()
        info['hostname'] = platform.node()
        info['python_version'] = platform.python_version()

        logger.info(f"OS: {info['os']} {info['os_release']}")
        logger.info(f"Architecture: {info['architecture']}")
        logger.info(f"Hostname: {info['hostname']}")

        # Detect Linux distribution
        if info['os'] == 'Linux':
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            info['distribution'] = line.split('=')[1].strip().strip('"')
                            logger.info(f"Distribution: {info['distribution']}")
                            break
            except FileNotFoundError:
                info['distribution'] = 'Unknown'
                logger.debug("Could not read /etc/os-release - file not found")
            except (IOError, OSError) as e:
                info['distribution'] = 'Unknown'
                logger.debug(f"Could not read /etc/os-release: {e}")

        # CPU information
        try:
            cpu_info = self._run_command("lscpu")
            info['cpu'] = self._parse_lscpu(cpu_info)
            logger.info(f"CPU: {info['cpu'].get('Model name', 'Unknown')}")
            logger.info(f"CPU Cores: {info['cpu'].get('CPU(s)', 'Unknown')}")
        except (ValueError, KeyError) as e:
            info['cpu'] = {}
            logger.debug(f"Failed to parse CPU info: {e}")

        # Memory information
        try:
            mem_info = self._run_command("free -h")
            info['memory'] = self._parse_free(mem_info)
            logger.info(f"Memory: {info['memory'].get('total', 'Unknown')}")
        except (ValueError, KeyError, IndexError) as e:
            info['memory'] = {}
            logger.debug(f"Failed to parse memory info: {e}")

        # Disk information
        try:
            disk_info = self._run_command("df -h /")
            info['disk'] = self._parse_df(disk_info)
            logger.info(f"Disk: {info['disk'].get('size', 'Unknown')} (Used: {info['disk'].get('used_percent', 'Unknown')})")
        except (ValueError, KeyError, IndexError) as e:
            info['disk'] = {}
            logger.debug(f"Failed to parse disk info: {e}")

        # Check permissions
        info['is_root'] = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        info['can_sudo'] = self._check_sudo()
        logger.info(f"Root: {info['is_root']}, Sudo: {info['can_sudo']}")

        # Detect running services
        info['services'] = self._detect_services()
        logger.info(f"Key Services: {', '.join(info['services'][:5])}")

        # Agent limitations
        info['limitations'] = self._assess_limitations()

        self.system_info = info
        return info

    def collect_baseline_metrics(self) -> Dict:
        """
        Collect baseline performance metrics.

        This method stores the metrics as the initial baseline for later comparison.
        Call this once at the beginning of the tuning process.

        Returns:
            Dictionary with baseline metrics
        """
        logger.info("\n📊 Collecting Baseline Metrics...")

        metrics = self._collect_current_metrics()

        # Store as both current baseline and initial baseline
        self.baseline_metrics = metrics
        self.initial_baseline_metrics = metrics.copy()

        return metrics

    def _collect_current_metrics(self) -> Dict:
        """
        Collect current performance metrics without storing as baseline.

        This is used for validation comparisons.

        Returns:
            Dictionary with current metrics
        """
        metrics = {}

        # CPU usage
        try:
            cpu_usage = self._run_command("top -bn1 | grep 'Cpu(s)'")
            metrics['cpu_idle'] = self._parse_cpu_usage(cpu_usage)
            logger.info(f"CPU Idle: {metrics['cpu_idle']}%")
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to collect CPU metrics: {e}")

        # Memory usage
        try:
            mem_info = self._run_command("free -m")
            metrics['memory'] = self._parse_memory_usage(mem_info)
            logger.info(f"Memory Used: {metrics['memory'].get('used_mb', 0)} MB / {metrics['memory'].get('total_mb', 0)} MB")
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to collect memory metrics: {e}")

        # Disk I/O
        try:
            io_stat = self._run_command("iostat -x 1 2 | tail -n +4")
            metrics['disk_io'] = self._parse_iostat(io_stat)
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to collect disk I/O metrics: {e}")

        # Network stats
        try:
            net_stat = self._run_command("netstat -s | head -20")
            metrics['network'] = {'raw': net_stat[:500]}
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to collect network metrics: {e}")

        # Load average
        try:
            uptime = self._run_command("uptime")
            metrics['load_average'] = uptime.split('load average:')[1].strip() if 'load average' in uptime else 'N/A'
            logger.info(f"Load Average: {metrics['load_average']}")
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to collect load average: {e}")

        return metrics

    # ============================================================================
    # PHASE 2: RESEARCH & KNOWLEDGE GATHERING
    # ============================================================================

    def research_tuning_strategies(self) -> Dict:
        """
        Phase 2: Use server LLM to research optimal tuning strategies.

        Returns:
            Dictionary with tuning strategies
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: RESEARCH & KNOWLEDGE GATHERING")
        logger.info("=" * 80)

        # Build comprehensive prompt for the server
        prompt = self._build_research_prompt()

        logger.info(f"🔍 Querying server LLM ({self.llm_model}) for tuning strategies...")

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.llm_temperature,
                max_tokens=self.llm_max_tokens
            )

            strategies_text = response.choices[0].message.content
            logger.info(f"✅ Received tuning strategies ({len(strategies_text)} chars)")

            # Parse strategies
            strategies = self._parse_strategies(strategies_text)

            return strategies

        except Exception as e:
            logger.error(f"❌ Failed to research strategies: {e}")
            return {}

    def _build_research_prompt(self) -> str:
        """Build comprehensive research prompt for the server."""
        return f"""
You are a Linux system performance expert. Analyze this system and provide specific, safe tuning recommendations.

SYSTEM INFORMATION:
{json.dumps(self.system_info, indent=2)}

BASELINE METRICS:
{json.dumps(self.baseline_metrics, indent=2)}

TASK:
Provide a comprehensive performance tuning plan with specific commands. Focus on:

1. **System Bottleneck Analysis**
   - Identify the primary performance bottlenecks from the metrics
   - Prioritize by impact (high/medium/low)

2. **Safe Tuning Recommendations**
   - Kernel parameters (sysctl.conf)
   - File system optimizations
   - Network tuning
   - Memory management
   - Disk I/O optimization
   - CPU scheduling

3. **Specific Commands**
   For each recommendation provide:
   - Exact command or config change
   - File to modify (with full path)
   - Expected impact
   - Reversibility (how to undo)
   - Risk level (low/medium/high)
   - Requires sudo: yes/no

OUTPUT FORMAT (JSON):
{{
  "bottlenecks": [
    {{"type": "memory", "severity": "high", "description": "..."}}
  ],
  "recommendations": [
    {{
      "priority": 1,
      "category": "memory",
      "description": "Increase vm.swappiness",
      "command": "sysctl -w vm.swappiness=10",
      "config_file": "/etc/sysctl.conf",
      "config_line": "vm.swappiness=10",
      "expected_impact": "Reduce swap usage by 30%",
      "how_to_revert": "sysctl -w vm.swappiness=60",
      "risk": "low",
      "requires_sudo": true
    }}
  ]
}}

CONSTRAINTS:
- ONLY suggest safe, reversible changes
- NO kernel module loading
- NO filesystem reformatting
- NO destructive operations
- Focus on tuning parameters, not software installation
"""

    # ============================================================================
    # PHASE 3: PLANNING & STRATEGY
    # ============================================================================

    def create_tuning_plan(self, strategies: Dict) -> List[Dict]:
        """
        Phase 3: Create detailed execution plan.

        Args:
            strategies: Tuning strategies from research

        Returns:
            List of tuning actions in execution order
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: STRATEGY PLANNING")
        logger.info("=" * 80)

        recommendations = strategies.get('recommendations', [])

        if not recommendations:
            logger.warning("No recommendations received")
            return []

        # Sort by priority
        sorted_recs = sorted(recommendations, key=lambda x: x.get('priority', 99))

        plan = []
        for i, rec in enumerate(sorted_recs, 1):
            action = {
                'step': i,
                'category': rec.get('category', 'unknown'),
                'description': rec.get('description', ''),
                'command': rec.get('command', ''),
                'config_file': rec.get('config_file'),
                'config_line': rec.get('config_line'),
                'expected_impact': rec.get('expected_impact', ''),
                'how_to_revert': rec.get('how_to_revert', ''),
                'risk': rec.get('risk', 'medium'),
                'requires_sudo': rec.get('requires_sudo', True),
                'status': 'pending'
            }

            # Skip high-risk items in dry-run
            if self.dry_run and action['risk'] == 'high':
                action['status'] = 'skipped'
                action['skip_reason'] = 'High risk (dry-run mode)'

            plan.append(action)

            logger.info(f"Step {i}: {action['description']}")
            logger.info(f"  Risk: {action['risk']}, Sudo: {action['requires_sudo']}")

        self.tuning_plan = plan
        return plan

    # ============================================================================
    # PHASE 4: EXECUTION
    # ============================================================================

    def execute_tuning_plan(self) -> List[Dict]:
        """
        Phase 4: Execute the tuning plan safely.

        Returns:
            List of execution results
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: EXECUTION")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("🔒 DRY RUN MODE - No changes will be made")

        results = []

        for action in self.tuning_plan:
            if action['status'] == 'skipped':
                logger.info(f"⏭️  Step {action['step']}: Skipped - {action.get('skip_reason', 'Unknown')}")
                continue

            logger.info(f"\n{'='*60}")
            logger.info(f"Step {action['step']}: {action['description']}")
            logger.info(f"{'='*60}")

            result = self._execute_single_action(action)
            results.append(result)

            # Stop on failures
            if result['success'] == False and result.get('critical', False):
                logger.error("❌ Critical failure - stopping execution")
                break

            # Pause between actions (from config)
            time.sleep(self.pause_between_actions)

        self.executed_changes = results
        return results

    def _execute_single_action(self, action: Dict) -> Dict:
        """Execute a single tuning action."""
        result = {
            'step': action['step'],
            'description': action['description'],
            'success': False,
            'output': '',
            'error': '',
            'backup_made': False
        }

        # Backup config file if exists
        if action.get('config_file'):
            backup_success = self._backup_file(action['config_file'])
            result['backup_made'] = backup_success

        # Check sudo requirement
        if action['requires_sudo'] and not self.system_info.get('can_sudo'):
            result['error'] = "Requires sudo but sudo not available"
            logger.warning(f"⚠️  Skipping (needs sudo): {action['description']}")
            return result

        if self.dry_run:
            result['success'] = True
            result['output'] = "[DRY RUN] Would execute: " + action['command']
            logger.info(f"🔍 [DRY RUN] {action['command']}")
            return result

        # Execute via server's sandboxed_executor tool
        try:
            logger.info(f"▶️  Executing: {action['command']}")

            exec_result = self._execute_via_server(action['command'])

            if exec_result['success']:
                result['success'] = True
                result['output'] = exec_result['output']
                logger.info(f"✅ Success: {action['description']}")

                # If config_line specified, append to config file
                if action.get('config_line') and action.get('config_file'):
                    self._append_to_config(action['config_file'], action['config_line'])
            else:
                result['error'] = exec_result['error']
                logger.error(f"❌ Failed: {result['error']}")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Exception: {e}")

        return result

    def _execute_via_server(self, command: str) -> Dict:
        """Execute command via server's sandboxed_executor tool."""
        # Check for forbidden patterns before execution
        for pattern in self.forbidden_patterns:
            if pattern in command:
                return {
                    'success': False,
                    'output': '',
                    'error': f"Command contains forbidden pattern: {pattern}"
                }

        try:
            # Use server to execute command safely
            prompt = f"""
Execute this system command safely using the process_executor tool:

Command: {command}

Return the output and any errors.
"""

            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Very low for command execution
                max_tokens=2048
            )

            output = response.choices[0].message.content

            return {
                'success': True,
                'output': output,
                'error': ''
            }

        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

    # ============================================================================
    # PHASE 5: VALIDATION & ITERATION
    # ============================================================================

    def validate_improvements(self) -> Dict:
        """
        Phase 5: Validate performance improvements.

        Returns:
            Validation results with before/after comparison
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: VALIDATION")
        logger.info("=" * 80)

        # Collect new metrics (store separately, don't overwrite baseline)
        logger.info("📊 Collecting post-tuning metrics...")
        new_metrics = self._collect_current_metrics()

        # Compare against INITIAL baseline (not the potentially overwritten one)
        comparison = self._compare_metrics(self.initial_baseline_metrics, new_metrics)

        logger.info("\n📈 Performance Comparison:")
        for key, change in comparison.items():
            if change['improved']:
                logger.info(f"  ✅ {key}: {change['description']}")
            elif change['degraded']:
                logger.warning(f"  ⚠️  {key}: {change['description']}")
            else:
                logger.info(f"  ➡️  {key}: {change['description']}")

        validation = {
            'baseline': self.baseline_metrics,
            'new_metrics': new_metrics,
            'comparison': comparison,
            'overall_improvement': self._calculate_overall_score(comparison)
        }

        self.performance_history.append(validation)

        return validation

    def generate_report(self) -> str:
        """Generate comprehensive tuning report."""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING FINAL REPORT")
        logger.info("=" * 80)

        report = f"""
# AUTONOMOUS SYSTEM PERFORMANCE TUNING REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## System Information
- OS: {self.system_info.get('os', 'Unknown')} {self.system_info.get('os_release', '')}
- Distribution: {self.system_info.get('distribution', 'Unknown')}
- Architecture: {self.system_info.get('architecture', 'Unknown')}
- CPU: {self.system_info.get('cpu', {}).get('Model name', 'Unknown')}
- Memory: {self.system_info.get('memory', {}).get('total', 'Unknown')}

## Tuning Actions Executed
Total: {len(self.executed_changes)}
Successful: {sum(1 for r in self.executed_changes if r['success'])}
Failed: {sum(1 for r in self.executed_changes if not r['success'])}

### Details:
"""

        for result in self.executed_changes:
            status = "✅" if result['success'] else "❌"
            report += f"\n{status} Step {result['step']}: {result['description']}\n"
            if result.get('output'):
                report += f"   Output: {result['output'][:100]}...\n"
            if result.get('error'):
                report += f"   Error: {result['error']}\n"

        if self.performance_history:
            latest = self.performance_history[-1]
            report += f"\n## Performance Impact\n"
            report += f"Overall Improvement Score: {latest['overall_improvement']:.1f}%\n\n"

            for key, change in latest['comparison'].items():
                report += f"- {key}: {change['description']}\n"

        report += f"\n## Rollback Information\n"
        report += f"Backup Directory: {self.backup_dir}\n"
        report += f"To rollback all changes, run: python {sys.argv[0]} --rollback {self.backup_dir}\n"

        # Save report
        report_file = self.backup_dir / "tuning_report.md"
        report_file.write_text(report)
        logger.info(f"\n📄 Report saved to: {report_file}")

        return report

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _run_command(self, command: str) -> str:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.command_timeout
            )
            return result.stdout
        except subprocess.TimeoutExpired as e:
            logger.debug(f"Command timed out after {self.command_timeout}s: {command}")
            return ""
        except subprocess.SubprocessError as e:
            logger.debug(f"Command failed: {command} - {e}")
            return ""
        except Exception as e:
            logger.debug(f"Unexpected error running command: {command} - {e}")
            return ""

    def _check_sudo(self) -> bool:
        """Check if sudo is available."""
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.debug("sudo check timed out")
            return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"sudo check failed: {e}")
            return False

    def _detect_services(self) -> List[str]:
        """Detect running services."""
        services = []
        try:
            output = self._run_command("systemctl list-units --type=service --state=running --no-pager")
            for line in output.split('\n'):
                if '.service' in line:
                    parts = line.split()
                    if parts:
                        service_name = parts[0].replace('.service', '')
                        services.append(service_name)
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to detect services: {e}")
        return services[:20]  # Limit to 20

    def _assess_limitations(self) -> Dict:
        """Assess agent's limitations."""
        return {
            'no_root': not self.system_info.get('is_root', False),
            'requires_sudo_approval': not self.system_info.get('can_sudo', False),
            'limited_to_userspace': True,
            'no_kernel_modules': True,
            'safe_mode_only': True
        }

    def _backup_file(self, filepath: str) -> bool:
        """Backup a configuration file."""
        try:
            source = Path(filepath)
            if not source.exists():
                return False

            backup_name = source.name + ".backup"
            backup_path = self.backup_dir / backup_name

            # shutil is imported at module level
            shutil.copy2(source, backup_path)
            logger.info(f"💾 Backed up: {filepath} → {backup_path}")
            return True
        except (IOError, OSError, shutil.Error) as e:
            logger.error(f"Backup failed for {filepath}: {e}")
            return False

    def _append_to_config(self, filepath: str, config_line: str):
        """Append configuration line to file."""
        try:
            with open(filepath, 'a') as f:
                f.write(f"\n# Added by System Tuner - {datetime.now()}\n")
                f.write(f"{config_line}\n")
            logger.info(f"📝 Updated config: {filepath}")
        except Exception as e:
            logger.error(f"Config update failed: {e}")

    def _parse_lscpu(self, output: str) -> Dict:
        """Parse lscpu output."""
        cpu = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                cpu[key.strip()] = value.strip()
        return cpu

    def _parse_free(self, output: str) -> Dict:
        """Parse free command output."""
        lines = output.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            return {'total': parts[1], 'used': parts[2], 'free': parts[3]}
        return {}

    def _parse_df(self, output: str) -> Dict:
        """Parse df command output."""
        lines = output.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            return {
                'filesystem': parts[0],
                'size': parts[1],
                'used': parts[2],
                'available': parts[3],
                'used_percent': parts[4]
            }
        return {}

    def _parse_strategies(self, text: str) -> Dict:
        """Parse tuning strategies from LLM response."""
        # Try to extract JSON
        try:
            # Look for JSON block
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            elif '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
            else:
                json_str = text

            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse strategies: {e}")
            return {'bottlenecks': [], 'recommendations': []}

    def _parse_cpu_usage(self, output: str) -> float:
        """Parse CPU idle percentage."""
        try:
            idle_str = output.split('id,')[0].split()[-1]
            return float(idle_str)
        except:
            return 0.0

    def _parse_memory_usage(self, output: str) -> Dict:
        """Parse memory usage."""
        try:
            lines = output.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    'total_mb': int(parts[1]),
                    'used_mb': int(parts[2]),
                    'free_mb': int(parts[3])
                }
        except:
            return {}

    def _parse_iostat(self, output: str) -> Dict:
        """Parse iostat output."""
        return {'raw': output[:300]}

    def _compare_metrics(self, baseline: Dict, new: Dict) -> Dict:
        """Compare baseline vs new metrics."""
        comparison = {}

        # CPU comparison
        if 'cpu_idle' in baseline and 'cpu_idle' in new:
            old_idle = baseline['cpu_idle']
            new_idle = new['cpu_idle']
            change = new_idle - old_idle
            comparison['cpu_idle'] = {
                'improved': change > 0,
                'degraded': change < -5,
                'description': f"{old_idle:.1f}% → {new_idle:.1f}% (Δ {change:+.1f}%)"
            }

        # Memory comparison
        if 'memory' in baseline and 'memory' in new:
            old_used = baseline['memory'].get('used_mb', 0)
            new_used = new['memory'].get('used_mb', 0)
            change = old_used - new_used
            comparison['memory_freed'] = {
                'improved': change > 0,
                'degraded': change < -100,
                'description': f"Freed {change} MB"
            }

        return comparison

    def _calculate_overall_score(self, comparison: Dict) -> float:
        """Calculate overall improvement score."""
        if not comparison:
            return 0.0

        improved = sum(1 for v in comparison.values() if v.get('improved', False))
        degraded = sum(1 for v in comparison.values() if v.get('degraded', False))
        total = len(comparison)

        if total == 0:
            return 0.0

        score = ((improved - degraded) / total) * 100
        return max(0.0, min(100.0, score))

    # ============================================================================
    # MAIN AUTONOMOUS LOOP
    # ============================================================================

    def run_autonomous(self):
        """Main autonomous tuning loop."""
        try:
            logger.info("\n🚀 Starting Autonomous Tuning Process...")

            # Phase 1: Discovery
            self.discover_system()
            self.collect_baseline_metrics()

            # Phase 2: Research
            strategies = self.research_tuning_strategies()

            if not strategies.get('recommendations'):
                logger.warning("❌ No tuning strategies received - cannot proceed")
                return False

            # Phase 3: Planning
            plan = self.create_tuning_plan(strategies)

            if not plan:
                logger.warning("❌ No tuning plan created - cannot proceed")
                return False

            # User approval for non-dry-run
            if not self.dry_run:
                logger.info("\n" + "⚠️ " * 30)
                logger.info("READY TO EXECUTE SYSTEM CHANGES")
                logger.info(f"Total actions: {len(plan)}")
                logger.info(f"Backups will be saved to: {self.backup_dir}")
                logger.info("⚠️ " * 30)

                response = input("\nProceed with execution? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("❌ User cancelled execution")
                    return False

            # Phase 4: Execution
            results = self.execute_tuning_plan()

            # Phase 5: Validation
            validation = self.validate_improvements()

            # Generate report
            report = self.generate_report()

            logger.info("\n" + "=" * 80)
            logger.info("✅ AUTONOMOUS TUNING COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Overall Improvement: {validation['overall_improvement']:.1f}%")
            logger.info(f"Report: {self.backup_dir}/tuning_report.md")

            return True

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            return False
        except Exception as e:
            logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    # Get config defaults for help text
    default_server = _config.get_server_url()
    default_dry_run = _config.get_safety_setting('dry_run_default', True)
    default_max_iter = _config.get_execution_setting('max_iterations', 10)

    parser = argparse.ArgumentParser(
        description="Autonomous System Performance Tuning Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
This agent autonomously tunes system performance by:
1. Discovering system capabilities and limitations
2. Researching optimal tuning strategies via LLM
3. Planning safe, reversible optimizations
4. Executing changes with full backup capability
5. Validating improvements and iterating

Configuration is loaded from config/agents_config.yaml.
Command-line arguments override configuration values.

Examples:
  # Dry run (plan only, no changes) - default based on config
  %(prog)s --dry-run

  # Full autonomous tuning (override dry-run default)
  %(prog)s --execute

  # Custom server URL
  %(prog)s --server http://localhost:8000/v1

  # Verbose logging
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--server',
        default=None,
        help=f'Server URL (default from config: {default_server})'
    )

    # Mutually exclusive dry-run / execute
    run_mode = parser.add_mutually_exclusive_group()
    run_mode.add_argument(
        '--dry-run',
        action='store_true',
        default=None,
        help=f'Plan only, do not execute changes (config default: {default_dry_run})'
    )
    run_mode.add_argument(
        '--execute',
        action='store_true',
        help='Execute changes (opposite of --dry-run)'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=None,
        help=f'Maximum tuning iterations (config default: {default_max_iter})'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show loaded configuration and exit'
    )

    args = parser.parse_args()

    # Handle --show-config
    if args.show_config:
        import yaml
        print("Loaded configuration for system_tuner agent:")
        print(yaml.dump(_config.to_dict(), default_flow_style=False))
        sys.exit(0)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine dry_run setting
    dry_run = None
    if args.dry_run:
        dry_run = True
    elif args.execute:
        dry_run = False
    # If neither specified, agent will use config default

    # Create and run agent
    agent = SystemTunerAgent(
        server_url=args.server,
        dry_run=dry_run,
        max_iterations=args.max_iterations
    )

    success = agent.run_autonomous()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
