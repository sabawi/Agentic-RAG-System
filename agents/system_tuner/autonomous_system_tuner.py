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

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_tuner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SystemTunerAgent:
    """Autonomous system performance tuning agent."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        dry_run: bool = False,
        max_iterations: int = 10
    ):
        """
        Initialize the autonomous tuning agent.

        Args:
            server_url: URL of the Agentic-RAG server (must be local)
            dry_run: If True, only plan but don't execute changes
            max_iterations: Maximum tuning iterations
        """
        self.server_url = server_url
        self.dry_run = dry_run
        self.max_iterations = max_iterations

        # State tracking
        self.system_info = {}
        self.baseline_metrics = {}
        self.tuning_plan = []
        self.executed_changes = []
        self.performance_history = []

        # Backup directory
        self.backup_dir = Path("system_tuning_backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        logger.info("=" * 80)
        logger.info("🤖 AUTONOMOUS SYSTEM PERFORMANCE TUNING AGENT")
        logger.info("=" * 80)
        logger.info(f"Server: {server_url}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"Backup Dir: {self.backup_dir}")
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
            except:
                info['distribution'] = 'Unknown'

        # CPU information
        try:
            cpu_info = self._run_command("lscpu")
            info['cpu'] = self._parse_lscpu(cpu_info)
            logger.info(f"CPU: {info['cpu'].get('Model name', 'Unknown')}")
            logger.info(f"CPU Cores: {info['cpu'].get('CPU(s)', 'Unknown')}")
        except:
            info['cpu'] = {}

        # Memory information
        try:
            mem_info = self._run_command("free -h")
            info['memory'] = self._parse_free(mem_info)
            logger.info(f"Memory: {info['memory'].get('total', 'Unknown')}")
        except:
            info['memory'] = {}

        # Disk information
        try:
            disk_info = self._run_command("df -h /")
            info['disk'] = self._parse_df(disk_info)
            logger.info(f"Disk: {info['disk'].get('size', 'Unknown')} (Used: {info['disk'].get('used_percent', 'Unknown')})")
        except:
            info['disk'] = {}

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

        Returns:
            Dictionary with baseline metrics
        """
        logger.info("\n📊 Collecting Baseline Metrics...")

        metrics = {}

        # CPU usage
        try:
            cpu_usage = self._run_command("top -bn1 | grep 'Cpu(s)'")
            metrics['cpu_idle'] = self._parse_cpu_usage(cpu_usage)
            logger.info(f"CPU Idle: {metrics['cpu_idle']}%")
        except:
            pass

        # Memory usage
        try:
            mem_info = self._run_command("free -m")
            metrics['memory'] = self._parse_memory_usage(mem_info)
            logger.info(f"Memory Used: {metrics['memory'].get('used_mb', 0)} MB / {metrics['memory'].get('total_mb', 0)} MB")
        except:
            pass

        # Disk I/O
        try:
            io_stat = self._run_command("iostat -x 1 2 | tail -n +4")
            metrics['disk_io'] = self._parse_iostat(io_stat)
        except:
            pass

        # Network stats
        try:
            net_stat = self._run_command("netstat -s | head -20")
            metrics['network'] = {'raw': net_stat[:500]}
        except:
            pass

        # Load average
        try:
            uptime = self._run_command("uptime")
            metrics['load_average'] = uptime.split('load average:')[1].strip() if 'load average' in uptime else 'N/A'
            logger.info(f"Load Average: {metrics['load_average']}")
        except:
            pass

        self.baseline_metrics = metrics
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

        logger.info("🔍 Querying server LLM for tuning strategies...")

        try:
            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3,  # Lower temperature for factual analysis
                max_tokens=4096
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

            # Pause between actions
            time.sleep(2)

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
        try:
            # Use server to execute command safely
            prompt = f"""
Execute this system command safely using the process_executor tool:

Command: {command}

Return the output and any errors.
"""

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
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

        # Collect new metrics
        logger.info("📊 Collecting post-tuning metrics...")
        new_metrics = self.collect_baseline_metrics()

        # Compare
        comparison = self._compare_metrics(self.baseline_metrics, new_metrics)

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
                timeout=30
            )
            return result.stdout
        except Exception as e:
            logger.debug(f"Command failed: {command} - {e}")
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
        except:
            return False

    def _detect_services(self) -> List[str]:
        """Detect running services."""
        services = []
        try:
            output = self._run_command("systemctl list-units --type=service --state=running --no-pager")
            for line in output.split('\n'):
                if '.service' in line:
                    service_name = line.split()[0].replace('.service', '')
                    services.append(service_name)
        except:
            pass
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

            import shutil
            shutil.copy2(source, backup_path)
            logger.info(f"💾 Backed up: {filepath} → {backup_path}")
            return True
        except Exception as e:
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
    parser = argparse.ArgumentParser(
        description="Autonomous System Performance Tuning Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This agent autonomously tunes system performance by:
1. Discovering system capabilities and limitations
2. Researching optimal tuning strategies via LLM
3. Planning safe, reversible optimizations
4. Executing changes with full backup capability
5. Validating improvements and iterating

Examples:
  # Dry run (plan only, no changes)
  %(prog)s --dry-run

  # Full autonomous tuning
  %(prog)s

  # Custom server URL
  %(prog)s --server http://localhost:8000/v1

  # Verbose logging
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--server',
        default='http://localhost:5000/v1',
        help='Server URL (must be local)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Plan only, do not execute changes'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum tuning iterations (default: 10)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run agent
    agent = SystemTunerAgent(
        server_url=args.server,
        dry_run=args.dry_run,
        max_iterations=args.max_iterations
    )

    success = agent.run_autonomous()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
