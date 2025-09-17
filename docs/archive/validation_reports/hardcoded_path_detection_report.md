# 🔍 Hardcoded Path Detection Report

## 📊 Summary: 118 files with potential path issues

## 🚨 Priority Summary
- 🔴 CRITICAL **Critical Absolute Paths**: 68 issues
- 🟡 HIGH **High Risk Relative Paths**: 116 issues
- 🟢 MEDIUM **Medium Risk Imports**: 84 issues
- 🔵 LOW **Low Risk Documentation**: 15 issues
- 🔵 LOW **Shell Script Paths**: 6 issues
- 🔵 LOW **Config File References**: 6 issues

## 📋 Detailed Issues by File

### 🟡 `Backtester.py`
**2 issues found:**

- **Line 426** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))
- **Line 562** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🟡 `CLAUDE.md`
**4 issues found:**

- **Line 80** `relative_dot_paths`: ./stop_complete.sh && ./start_complete.sh
- **Line 530** `relative_dot_paths`: ./stop_complete.sh && ./start_complete.sh
- **Line 756** `relative_dot_paths`: ./stop_complete.sh && ./start_complete.sh
- **Line 1050** `relative_dot_paths`: ./stop_complete.sh && ./start_complete.sh

### 🔴 `COMPLETE_MIGRATION_GUIDE.md`
**4 issues found:**

- **Line 33** `absolute_project_paths`: /home/sabawi/Development/flaskserver/
- **Line 46** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver
- **Line 52** `relative_dot_paths`: ./start_complete_server.sh
- **Line 206** `relative_dot_paths`: 🚀 **Start using it now with**: `./start_complete_server.sh`

### 🔴 `CRITICAL_MULTI_TOOL_CALLING_PROTECTION.md`
**3 issues found:**

- **Line 64** `relative_dot_paths`: 1. **Restart server**: `./stop_complete.sh && ./start_complete.sh`
- **Line 84** `absolute_project_paths`: grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/logs/server_complete.log | tail -3
- **Line 103** `relative_dot_paths`: 4. **Restart Server**: `./stop_complete.sh && ./start_complete.sh`

### 🟡 `DEVELOPER_API_REFERENCE.md`
**1 issues found:**

- **Line 820** `relative_dot_paths`: Save as `test_comprehensive.sh` and run with `chmod +x test_comprehensive.sh && ./test_comprehensive...

### 🟡 `DOCUMENT_INTERROGATION_SETUP.md`
**1 issues found:**

- **Line 23** `relative_dot_paths`: ./start_complete.sh

### 🔴 `EMAIL_SECURITY_SETUP.md`
**2 issues found:**

- **Line 148** `absolute_project_paths`: cd /home/sabawi/Development/flaskserver/user_tools
- **Line 148** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver/user_tools

### 🔴 `EMAIL_TOOL_SUMMARY.md`
**2 issues found:**

- **Line 8** `absolute_project_paths`: **Location**: `/home/sabawi/Development/flaskserver/user_tools/secure_email_sender.py`
- **Line 22** `absolute_project_paths`: **Location**: `/home/sabawi/Development/flaskserver/EMAIL_SECURITY_SETUP.md`

### 🟡 `ENDPOINT_COVERAGE_SUMMARY.md`
**5 issues found:**

- **Line 91** `relative_dot_paths`: ./test_api_endpoints.sh
- **Line 128** `relative_dot_paths`: ./testing/quick_health_check.sh
- **Line 133** `relative_dot_paths`: ./testing/test_api_endpoints.sh
- **Line 138** `relative_dot_paths`: ./testing/test_embedding_service.sh    # Document processing
- **Line 139** `relative_dot_paths`: ./testing/comprehensive_test_suite.sh  # All systems

### 🟡 `LLM_ABSTRACTION_DESIGN.md`
**2 issues found:**

- **Line 92** `pathlib_paths`: NEW: Path("/tmp") / "email_debug.eml"  # Linux
- **Line 103** `relative_dot_paths`: OLD: "./stop_complete.sh && ./start_complete.sh"

### 🟡 `MIGRATION_SUMMARY.md`
**3 issues found:**

- **Line 49** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver
- **Line 55** `relative_dot_paths`: ./start_server.sh
- **Line 138** `relative_dot_paths`: 1. **Start the server**: `./start_server.sh`

### 🟡 `README.md`
**6 issues found:**

- **Line 94** `relative_dot_paths`: ./setup_fastapi.sh
- **Line 97** `relative_dot_paths`: ./start_complete_server.sh
- **Line 218** `relative_dot_paths`: ./quick_health_check.sh            # Fast system verification
- **Line 223** `relative_dot_paths`: ./comprehensive_test_suite.sh       # Full system test suite
- **Line 224** `relative_dot_paths`: ./test_embedding_service.sh         # Document processing & search tests
- **Line 225** `relative_dot_paths`: ./test_api_endpoints.sh             # All API endpoints with curl examples

### 🟡 `README_FastAPI.md`
**2 issues found:**

- **Line 30** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver
- **Line 31** `relative_dot_paths`: ./setup_fastapi.sh

### 🔴 `TROUBLESHOOTING_GUIDE.md`
**17 issues found:**

- **Line 7** `absolute_project_paths`: cd /home/sabawi/Development/flaskserver/testing
- **Line 7** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver/testing
- **Line 8** `relative_dot_paths`: ./quick_health_check.sh
- **Line 13** `relative_dot_paths`: ./comprehensive_test_suite.sh
- **Line 14** `relative_dot_paths`: ./test_embedding_service.sh
- **Line 15** `relative_dot_paths`: ./test_api_endpoints.sh
- **Line 45** `relative_dot_paths`: ./stop_complete.sh
- **Line 160** `relative_dot_paths`: ./stop_complete.sh
- **Line 161** `relative_dot_paths`: ./start_complete.sh
- **Line 193** `relative_dot_paths`: ./test_embedding_service.sh
- **Line 310** `relative_dot_paths`: 0 3 * * * cd /home/sabawi/Development/flaskserver && ./stop_complete.sh && ./start_complete.sh
- **Line 310** `shell_cd_commands`: 0 3 * * * cd /home/sabawi/Development/flaskserver && ./stop_complete.sh && ./start_complete.sh
- **Line 420** `relative_dot_paths`: ./stop_complete.sh && ./start_complete.sh
- **Line 528** `relative_dot_paths`: ./stop_complete.sh
- **Line 547** `relative_dot_paths`: ./start_complete.sh
- **Line 550** `relative_dot_paths`: ./testing/quick_health_check.sh
- **Line 633** `relative_dot_paths`: ./testing/quick_health_check.sh > health_report.txt

### 🟡 `api_request_simulation.py`
**1 issues found:**

- **Line 16** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🔴 `arbitrator_system.py`
**2 issues found:**

- **Line 179** `absolute_project_paths`: with open('/home/sabawi/Development/flaskserver/config/arbitrator_system_prompt.txt', 'r') as f:
- **Line 179** `hardcoded_file_opens`: with open('/home/sabawi/Development/flaskserver/config/arbitrator_system_prompt.txt', 'r') as f:

### 🔴 `config/arbitrator_logging_config.py`
**2 issues found:**

- **Line 28** `absolute_project_paths`: log_file = Path("/home/sabawi/Development/flaskserver/logs/arbitrator.log")
- **Line 28** `pathlib_paths`: log_file = Path("/home/sabawi/Development/flaskserver/logs/arbitrator.log")

### 🟡 `debug_embedding_generation.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.append('.')

### 🟡 `debug_faiss_search.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('.')

### 🟡 `debug_faiss_step_by_step.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('.')

### 🟡 `debug_sandboxed_executor.py`
**1 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🟡 `debug_tool_definitions.py`
**1 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🟡 `demo_correct_workflow.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `docker-compose.yml`
**1 issues found:**

- **Line 40** `relative_dot_paths`: - ./init.sql:/docker-entrypoint-initdb.d/init.sql

### 🟡 `docs/ARBITRATOR_SUCCESS_CONSOLIDATION.md`
**2 issues found:**

- **Line 29** `relative_dot_paths`: ./run_arbitrator_regression_test.sh
- **Line 153** `relative_dot_paths`: - **Run regression test**: `./run_arbitrator_regression_test.sh` before any changes

### 🟡 `docs/ARBITRATOR_SYSTEM_ARCHITECTURE.md`
**1 issues found:**

- **Line 288** `relative_dot_paths`: ./run_arbitrator_regression_test.sh

### 🔴 `docs/HARDCODED_PATH_DETECTION_STRATEGY.md`
**24 issues found:**

- **Line 31** `relative_dot_paths`: find . -name "*.py" -not -path "./venv/*" -exec echo "Scanning: {}" \;
- **Line 48** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/user_tools/"
- **Line 49** `relative_dot_paths`: "./sandbox_workspace/"
- **Line 52** `relative_dot_paths`: sys.path.append("../user_tools")
- **Line 52** `relative_dotdot_paths`: sys.path.append("../user_tools")
- **Line 52** `sys_path_modifications`: sys.path.append("../user_tools")
- **Line 56** `relative_dot_paths`: open("./config/llm_config.yaml")
- **Line 56** `hardcoded_relative_opens`: open("./config/llm_config.yaml")
- **Line 57** `config_file_refs`: Path("user_tools/sandboxed_executor.py")
- **Line 60** `relative_dot_paths`: subprocess.run(["python", "./scripts/test.py"])
- **Line 60** `subprocess_with_paths`: subprocess.run(["python", "./scripts/test.py"])
- **Line 181** `relative_dot_paths`: CONFIG_PATH = "./config/llm_config.yaml"
- **Line 182** `relative_dot_paths`: TOOL_MODULES_DIR = "./user_tools/"
- **Line 194** `shell_cd_commands`: cd /home/sabawi/Development/flaskserver
- **Line 207** `absolute_project_paths`: sandbox_root: "/home/sabawi/Development/flaskserver/sandbox_workspace"
- **Line 208** `relative_dot_paths`: logs_dir: "./logs"
- **Line 218** `relative_dot_paths`: sys.path.append("./user_tools")
- **Line 218** `sys_path_modifications`: sys.path.append("./user_tools")
- **Line 235** `relative_dot_paths`: ./run_all_regression_tests.sh > baseline_results.txt
- **Line 253** `relative_dot_paths`: ./run_arbitrator_regression_test.sh
- **Line 302** `relative_dot_paths`: ./test_updated_references.sh
- **Line 308** `relative_dot_paths`: ./validate_complete_reorganization.sh
- **Line 316** `relative_dot_paths`: ./stop_complete.sh
- **Line 326** `relative_dot_paths`: ./start_complete.sh

### 🔴 `fastapi_server_baseline.py`
**5 issues found:**

- **Line 1342** `sys_path_modifications`: sys.path.append(user_tools_path)
- **Line 2255** `absolute_project_paths`: attachment_path = f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 2284** `absolute_project_paths`: "attachments": f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 2291** `absolute_project_paths`: "attachments": f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 2546** `absolute_project_paths`: base_dir = "/home/sabawi/Development/flaskserver/sandbox_workspace"

### 🔴 `fastapi_server_complete.py`
**5 issues found:**

- **Line 1397** `sys_path_modifications`: sys.path.append(user_tools_path)
- **Line 4512** `absolute_project_paths`: attachment_path = f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 4541** `absolute_project_paths`: "attachments": f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 4548** `absolute_project_paths`: "attachments": f"/home/sabawi/Development/flaskserver/sandbox_workspace/{filename}"
- **Line 4803** `absolute_project_paths`: base_dir = "/home/sabawi/Development/flaskserver/sandbox_workspace"

### 🔴 `final_fix_test.py`
**3 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 21** `absolute_project_paths`: test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_report.pdf")
- **Line 21** `pathlib_paths`: test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_report.pdf")

### 🔴 `fix_sandboxed_executor.py`
**5 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 23** `absolute_project_paths`: problematic_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_report.pdf")
- **Line 23** `pathlib_paths`: problematic_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_report.pdf")
- **Line 148** `absolute_project_paths`: sandbox_files = list(Path("/home/sabawi/Development/flaskserver/sandbox_workspace").glob("*"))
- **Line 148** `pathlib_paths`: sandbox_files = list(Path("/home/sabawi/Development/flaskserver/sandbox_workspace").glob("*"))

### 🟡 `fix_sandboxed_executor_newlines.py`
**2 issues found:**

- **Line 7** `config_file_refs`: with open('user_tools/sandboxed_executor.py', 'r') as f:
- **Line 77** `config_file_refs`: with open('user_tools/sandboxed_executor.py', 'w') as f:

### 🟡 `generate_google_token.py`
**2 issues found:**

- **Line 18** `relative_dot_paths`: credentials_path = "./credentials.json"
- **Line 19** `relative_dot_paths`: token_path = "./token.pickle"

### 🟡 `integrate_llm_abstraction.py`
**1 issues found:**

- **Line 225** `relative_dot_paths`: 1. Restart your server: `./stop_complete.sh && ./start_complete.sh`

### 🟡 `llm_config_tool.py`
**5 issues found:**

- **Line 14** `config_file_refs`: self.config_file = Path("config/llm_config.yaml")
- **Line 480** `relative_dot_paths`: print("./stop_complete.sh && ./start_complete.sh")
- **Line 500** `relative_dot_paths`: print("./stop_complete.sh && ./start_complete.sh")
- **Line 608** `relative_dot_paths`: print("./stop_complete.sh && ./start_complete.sh")
- **Line 736** `config_file_refs`: config_path = Path("config/llm_config.yaml")

### 🟡 `llm_providers/__init__.py`
**3 issues found:**

- **Line 12** `import_from_relative`: from .base import LLMProvider
- **Line 13** `import_from_relative`: from .factory import LLMProviderFactory
- **Line 14** `import_from_relative`: from .ollama import OllamaProvider

### 🟡 `llm_providers/factory.py`
**4 issues found:**

- **Line 7** `import_from_relative`: from .base import LLMProvider
- **Line 67** `import_from_relative`: from .ollama import OllamaProvider
- **Line 70** `import_from_relative`: from .openai import OpenAIProvider
- **Line 73** `import_from_relative`: from .qwen import QwenProvider

### 🟡 `llm_providers/manager.py`
**2 issues found:**

- **Line 8** `import_from_relative`: from .base import LLMProvider
- **Line 9** `import_from_relative`: from .factory import LLMProviderFactory

### 🟡 `llm_providers/ollama.py`
**1 issues found:**

- **Line 12** `import_from_relative`: from .base import LLMProvider

### 🟡 `llm_providers/openai.py`
**1 issues found:**

- **Line 12** `import_from_relative`: from .base import LLMProvider

### 🟡 `llm_providers/qwen.py`
**1 issues found:**

- **Line 12** `import_from_relative`: from .base import LLMProvider

### 🟡 `logs.sh`
**1 issues found:**

- **Line 10** `relative_dot_paths`: echo "💡 Make sure the server is running with './start_complete.sh'"

### 🟡 `model_switcher.py`
**2 issues found:**

- **Line 15** `config_file_refs`: CONFIG_FILE = "config/llm_config.yaml"
- **Line 212** `relative_dot_paths`: print("1. Restart the server: ./stop_complete.sh && ./start_complete.sh")

### 🟡 `rebuild_faiss_index.py`
**1 issues found:**

- **Line 10** `sys_path_modifications`: sys.path.append('.')

### 🟡 `run_arbitrator_regression_test.sh`
**3 issues found:**

- **Line 9** `relative_dot_paths`: #   ./run_arbitrator_regression_test.sh
- **Line 33** `relative_dot_paths`: echo "  ./start_complete.sh"
- **Line 43** `config_file_refs`: if [ ! -f "tests/test_arbitrator_word_count_regression.py" ]; then

### 🔴 `sandbox_workspace/Hype_Cycle_Analysis.md`
**1 issues found:**

- **Line 16** `absolute_project_paths`: `/home/sabawi/Development/flaskserver/sandbox_workspace/Hype_Cycle_Analysis.html`

### 🔴 `sandbox_workspace/game_theory_summary.md`
**1 issues found:**

- **Line 9** `absolute_project_paths`: **File Path:** `/home/sabawi/Development/flaskserver/sandbox_workspace/game_theory_summary.html`

### 🔴 `sandbox_workspace/graviton_research.md`
**1 issues found:**

- **Line 15** `absolute_project_paths`: /home/sabawi/Development/flaskserver/sandbox_workspace/graviton_research.html

### 🔴 `sandbox_workspace/gravity_paradox_edit.md`
**1 issues found:**

- **Line 6** `absolute_project_paths`: /home/sabawi/Development/flaskserver/sandbox_workspace/gravity_paradox_edit.html

### 🔴 `sandbox_workspace/merge_sort.md`
**1 issues found:**

- **Line 57** `absolute_project_paths`: - **Full Path:** `/home/sabawi/Development/flaskserver/sandbox_workspace/merge_sort.py`

### 🟡 `sandbox_workspace/word_frequency.py`
**1 issues found:**

- **Line 5** `hardcoded_file_opens`: with open('/var/www/html/silicon_dreams/stories/SD_TheQuantumConspiracy.md', 'r') as file:

### 🟡 `setup_fastapi.sh`
**1 issues found:**

- **Line 78** `sys_path_modifications`: sys.path.append('.')

### 🟡 `simple_attachment_test.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `start_complete.sh`
**2 issues found:**

- **Line 9** `relative_dot_paths`: echo "Use './stop_complete.sh' to stop it first."
- **Line 41** `relative_dot_paths`: echo "🛑 Stop: ./stop_complete.sh"

### 🟡 `start_complete_server.sh`
**1 issues found:**

- **Line 17** `relative_dot_paths`: echo "❌ Error: Virtual environment not found. Run ./setup_fastapi.sh first"

### 🟡 `status.sh`
**4 issues found:**

- **Line 63** `relative_dot_paths`: echo "   ./start_complete.sh  - Start the server"
- **Line 64** `relative_dot_paths`: echo "   ./stop_complete.sh   - Stop the server"
- **Line 65** `relative_dot_paths`: echo "   ./logs.sh           - Monitor logs"
- **Line 66** `relative_dot_paths`: echo "   ./status.sh         - Show this status"

### 🟡 `sys_prompt.txt`
**1 issues found:**

- **Line 1** `relative_dot_paths`: You are a co-developer for fastapi_server_complete.py and all the tools in ./user_tools like :

### 🔴 `test_all_formats_comprehensive.py`
**3 issues found:**

- **Line 28** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 34** `absolute_project_paths`: self.sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 34** `pathlib_paths`: self.sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")

### 🟡 `test_api_sandbox.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🔴 `test_attachment_fuzzy_matching.py`
**2 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')
- **Line 32** `absolute_project_paths`: sandbox_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/"

### 🔴 `test_attachment_waiting.py`
**3 issues found:**

- **Line 13** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')
- **Line 37** `absolute_project_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 37** `pathlib_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")

### 🟡 `test_auto_attach.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `test_calendar_auth.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🔴 `test_complete_final_verification.py`
**1 issues found:**

- **Line 151** `absolute_project_paths`: sandbox_path = "/home/sabawi/Development/flaskserver/sandbox_workspace"

### 🔴 `test_complete_fix.py`
**2 issues found:**

- **Line 42** `absolute_project_paths`: pdf_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/comprehensive_test.pdf"
- **Line 90** `absolute_project_paths`: pdf_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/comprehensive_test.pdf"

### 🔴 `test_complete_workflow.py`
**2 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 95** `absolute_project_paths`: full_report_path = f"/home/sabawi/Development/flaskserver/sandbox_workspace/{attachment_path}"

### 🟡 `test_complete_workflow_new.py`
**1 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🔴 `test_direct_tool.py`
**2 issues found:**

- **Line 7** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 27** `absolute_project_paths`: file_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/hello.py"

### 🔴 `test_direct_tools.py`
**3 issues found:**

- **Line 16** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 79** `absolute_project_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 79** `pathlib_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")

### 🟡 `test_document_search_direct.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.append('.')

### 🟡 `test_email_provider_fix.py`
**1 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🔴 `test_enhanced_executor.py`
**3 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 42** `absolute_project_paths`: script_path = "/home/sabawi/Development/flaskserver/test_report_script.py"
- **Line 58** `absolute_project_paths`: report_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/reports/TSLA_comprehensive_ana...

### 🟡 `test_faiss_scoring.py`
**1 issues found:**

- **Line 10** `sys_path_modifications`: sys.path.append('.')

### 🟡 `test_file_creation.py`
**1 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `test_formats_quick_fix.py`
**1 issues found:**

- **Line 16** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🔴 `test_html_entities.py`
**2 issues found:**

- **Line 7** `absolute_project_paths`: sys.path.append('/home/sabawi/Development/flaskserver/user_tools')
- **Line 7** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver/user_tools')

### 🟡 `test_html_pdf_fix.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.insert(0, user_tools_dir)

### 🟡 `test_improved_reports.py`
**1 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `test_llm_abstraction.py`
**1 issues found:**

- **Line 14** `sys_path_modifications`: sys.path.insert(0, str(Path(__file__).parent))

### 🟡 `test_passport_scores.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('.')

### 🟡 `test_pdf_creation.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🔴 `test_race_condition_fix.py`
**5 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 22** `absolute_project_paths`: test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_race_test.pdf")
- **Line 22** `pathlib_paths`: test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_race_test.pdf")
- **Line 141** `absolute_project_paths`: test_workflow_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_workflow_test...
- **Line 141** `pathlib_paths`: test_workflow_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_workflow_test...

### 🔴 `test_reindexing.py`
**1 issues found:**

- **Line 31** `absolute_project_paths`: db_path = "/home/sabawi/Development/flaskserver/document_store/metadata.db"

### 🟡 `test_sandboxed_executor.py`
**1 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🟡 `test_simplified_calendar.py`
**1 issues found:**

- **Line 8** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🔴 `test_smart_detection.py`
**3 issues found:**

- **Line 9** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')
- **Line 33** `absolute_project_paths`: report_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/TSLA_comprehensive_stock_analy...
- **Line 72** `absolute_project_paths`: report_path2 = "/home/sabawi/Development/flaskserver/sandbox_workspace/AAPL_financial_analysis_repor...

### 🔴 `test_title_escaping.py`
**2 issues found:**

- **Line 7** `absolute_project_paths`: sys.path.append('/home/sabawi/Development/flaskserver/user_tools')
- **Line 7** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver/user_tools')

### 🟡 `test_tool_calling_direct.py`
**1 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🔴 `test_tool_request_patterns.py`
**2 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')
- **Line 72** `absolute_project_paths`: sandbox_files = os.listdir('/home/sabawi/Development/flaskserver/sandbox_workspace/')

### 🟡 `testing/README_TESTING.md`
**18 issues found:**

- **Line 7** `relative_dot_paths`: ./quick_health_check.sh
- **Line 12** `relative_dot_paths`: ./comprehensive_test_suite.sh all
- **Line 17** `relative_dot_paths`: ./test_embedding_service.sh        # Document processing & search
- **Line 18** `relative_dot_paths`: ./test_api_endpoints.sh             # All API endpoints
- **Line 64** `relative_dot_paths`: ./comprehensive_test_suite.sh [category]
- **Line 67** `relative_dot_paths`: ./comprehensive_test_suite.sh tools
- **Line 68** `relative_dot_paths`: ./comprehensive_test_suite.sh documents
- **Line 69** `relative_dot_paths`: ./comprehensive_test_suite.sh performance
- **Line 72** `relative_dot_paths`: ./comprehensive_test_suite.sh all
- **Line 131** `relative_dot_paths`: **For API issues** → See [Developer API Reference](../DEVELOPER_API_REFERENCE.md)
- **Line 131** `relative_dotdot_paths`: **For API issues** → See [Developer API Reference](../DEVELOPER_API_REFERENCE.md)
- **Line 132** `relative_dot_paths`: **For embedding problems** → See [Embedding Service Debug Guide](../EMBEDDING_SERVICE_DEBUG_GUIDE.md...
- **Line 132** `relative_dotdot_paths`: **For embedding problems** → See [Embedding Service Debug Guide](../EMBEDDING_SERVICE_DEBUG_GUIDE.md...
- **Line 133** `relative_dot_paths`: **For general issues** → See [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)
- **Line 133** `relative_dotdot_paths`: **For general issues** → See [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)
- **Line 157** `relative_dot_paths`: run: ./testing/quick_health_check.sh
- **Line 159** `relative_dot_paths`: run: ./testing/comprehensive_test_suite.sh
- **Line 167** `relative_dot_paths`: if ! ./quick_health_check.sh; then

### 🟡 `testing/TestingReadme.md`
**2 issues found:**

- **Line 84** `relative_dot_paths`: ./start_complete_server.sh
- **Line 98** `relative_dot_paths`: ./curl_test.sh

### 🟡 `testing/comprehensive_test_suite.sh`
**2 issues found:**

- **Line 5** `relative_dot_paths`: # Usage: ./dev_test_framework.sh [test_category]
- **Line 50** `relative_dot_paths`: info "Please ensure the server is running: ./start_complete.sh"

### 🟡 `testing/debug_tool_calling.py`
**1 issues found:**

- **Line 13** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.abspath(__file__)))

### 🟡 `testing/quick_health_check.sh`
**4 issues found:**

- **Line 23** `relative_dot_paths`: echo "Server not responding. Check: ./start_complete.sh"
- **Line 100** `relative_dot_paths`: echo "  ./testing/comprehensive_test_suite.sh"
- **Line 101** `relative_dot_paths`: echo "  ./testing/test_embedding_service.sh"
- **Line 102** `relative_dot_paths`: echo "  ./testing/test_api_endpoints.sh"

### 🟡 `testing/test_embedding_service.sh`
**10 issues found:**

- **Line 106** `relative_dot_paths`: if [ -f "../document_store/faiss.index" ]; then
- **Line 106** `relative_dotdot_paths`: if [ -f "../document_store/faiss.index" ]; then
- **Line 107** `relative_dot_paths`: INDEX_SIZE=$(stat -f%z "../document_store/faiss.index" 2>/dev/null || stat -c%s "../document_store/f...
- **Line 107** `relative_dotdot_paths`: INDEX_SIZE=$(stat -f%z "../document_store/faiss.index" 2>/dev/null || stat -c%s "../document_store/f...
- **Line 119** `relative_dot_paths`: if [ -f "../document_store/metadata.db" ]; then
- **Line 119** `relative_dotdot_paths`: if [ -f "../document_store/metadata.db" ]; then
- **Line 120** `relative_dot_paths`: DB_SIZE=$(stat -f%z "../document_store/metadata.db" 2>/dev/null || stat -c%s "../document_store/meta...
- **Line 120** `relative_dotdot_paths`: DB_SIZE=$(stat -f%z "../document_store/metadata.db" 2>/dev/null || stat -c%s "../document_store/meta...
- **Line 125** `relative_dot_paths`: INTEGRITY_CHECK=$(sqlite3 "../document_store/metadata.db" "PRAGMA integrity_check;" 2>/dev/null || e...
- **Line 125** `relative_dotdot_paths`: INTEGRITY_CHECK=$(sqlite3 "../document_store/metadata.db" "PRAGMA integrity_check;" 2>/dev/null || e...

### 🟡 `testing/test_financial_news.py`
**1 issues found:**

- **Line 120** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🟡 `testing/test_missing_endpoints.py`
**1 issues found:**

- **Line 141** `relative_dot_paths`: print("💡 Make sure to start the server with: ./start_complete_server.sh")

### 🟡 `testing/test_tools_available.py`
**1 issues found:**

- **Line 84** `sys_path_modifications`: sys.path.insert(0, current_dir)

### 🟡 `testing/test_tools_individually.py`
**1 issues found:**

- **Line 11** `sys_path_modifications`: sys.path.append('/home/sabawi/Development/flaskserver')

### 🔴 `tests/test_arbitrator_framework.py`
**1 issues found:**

- **Line 263** `absolute_project_paths`: expected_prompt_path = "/home/sabawi/Development/flaskserver/config/arbitrator_system_prompt.txt"

### 🟡 `tests/test_arbitrator_word_count_regression.py`
**1 issues found:**

- **Line 33** `sys_path_modifications`: sys.path.insert(0, '/home/sabawi/Development/flaskserver')

### 🟡 `user_tools/README.md`
**1 issues found:**

- **Line 23** `import_from_relative`: from .base_user_tool import BaseUserTool

### 🟡 `user_tools/__init__.py`
**2 issues found:**

- **Line 6** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 7** `import_from_relative`: from .tool_discovery import discover_user_tools, load_user_tools

### 🔴 `user_tools/_disabled_analytical_visualizer.py`
**7 issues found:**

- **Line 31** `absolute_project_paths`: self.working_dir = "/home/sabawi/Development/flaskserver/sandbox_workspace"
- **Line 217** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/supply_demand_analysis.png"
- **Line 288** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/distribution_analysis.png"
- **Line 373** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/function_analysis.png"
- **Line 474** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/s_curve_project_analysis.png"
- **Line 562** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/exponential_growth_analysis.pn...
- **Line 631** `absolute_project_paths`: output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/analytical_plot.png"

### 🟡 `user_tools/_disabled_analytical_visualizer_tool.py`
**1 issues found:**

- **Line 12** `sys_path_modifications`: sys.path.append(os.path.dirname(__file__))

### 🟡 `user_tools/_disabled_stock_analyzer.py`
**1 issues found:**

- **Line 21** `import_from_relative`: from .base_user_tool import BaseUserTool

### 🟡 `user_tools/comprehensive_stock_analyzer.py`
**3 issues found:**

- **Line 16** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
- **Line 20** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 268** `import_from_relative`: from ._universal_pdf_generator import UniversalPDFGenerator

### 🟡 `user_tools/document_search.py`
**1 issues found:**

- **Line 12** `import_from_relative`: from .base_user_tool import BaseUserTool

### 🟡 `user_tools/example_calculator.py`
**1 issues found:**

- **Line 8** `import_from_relative`: from .base_user_tool import BaseUserTool

### 🟡 `user_tools/google_calendar_scheduler.py`
**3 issues found:**

- **Line 16** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 48** `relative_dot_paths`: self.credentials_path = "./credentials.json"
- **Line 49** `relative_dot_paths`: self.token_path = "./token.pickle"

### 🔴 `user_tools/process_executor.py`
**6 issues found:**

- **Line 18** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 42** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/sandbox_workspace",
- **Line 43** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/games",
- **Line 44** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/projects",
- **Line 45** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/output",
- **Line 166** `absolute_project_paths`: default_wd = "/home/sabawi/Development/flaskserver/sandbox_workspace"

### 🟡 `user_tools/published_papers_search_tool.py`
**1 issues found:**

- **Line 29** `import_from_relative`: from .base_user_tool import BaseUserTool

### 🔴 `user_tools/sandboxed_executor.py`
**12 issues found:**

- **Line 19** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 41** `pathlib_paths`: self.base_dir = Path("/home/sabawi/Development/flaskserver")
- **Line 571** `relative_dot_paths`: r'gcc.*-o\s+bin/.*\.c\s+&&\s+\./bin/',
- **Line 572** `relative_dot_paths`: r'g\+\+.*-o\s+bin/.*\.cpp\s+&&\s+\./bin/',
- **Line 574** `relative_dot_paths`: r'rustc.*-o\s+bin/.*\.rs\s+&&\s+\./bin/'
- **Line 615** `absolute_project_paths`: "/home/sabawi/Development/flaskserver/games",
- **Line 628** `absolute_project_paths`: custom_dir = "/home/sabawi/Development/flaskserver/games"
- **Line 956** `sys_path_modifications`: sys.path.insert(0, current_dir)
- **Line 1364** `relative_dot_paths`: 'c': f'gcc -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}',
- **Line 1365** `relative_dot_paths`: 'cpp': f'g++ -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}',
- **Line 1367** `relative_dot_paths`: 'rust': f'rustc -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}'
- **Line 1528** `sys_path_modifications`: sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

### 🔴 `user_tools/secure_email_sender.py`
**7 issues found:**

- **Line 18** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 187** `absolute_project_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace") / file_path
- **Line 187** `pathlib_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace") / file_path
- **Line 256** `absolute_project_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 256** `pathlib_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 358** `absolute_project_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
- **Line 358** `pathlib_paths`: sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")

### 🟡 `user_tools/tool_discovery.py`
**2 issues found:**

- **Line 11** `import_from_relative`: from .base_user_tool import BaseUserTool
- **Line 80** `sys_path_modifications`: sys.path.insert(0, tools_dir)

### 🟡 `utils/config_loader.py`
**2 issues found:**

- **Line 10** `import_from_relative`: from .platform import platform_paths, EnvironmentManager
- **Line 28** `config_file_refs`: Path("config/llm_config.yaml"),

### 🟡 `utils/platform.py`
**1 issues found:**

- **Line 47** `pathlib_paths`: "temp_dir": Path("/tmp") / "agentic_rag",

### 🔴 `verify_multi_tool_calling.sh`
**6 issues found:**

- **Line 13** `relative_dot_paths`: echo "   ./start_complete.sh"
- **Line 34** `absolute_project_paths`: TOOL_CALLS_1=$(grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/logs/server_complete.log |...
- **Line 62** `absolute_project_paths`: TOOL_CALLS_2=$(grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/logs/server_complete.log |...
- **Line 82** `absolute_project_paths`: grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/logs/server_complete.log | tail -5
- **Line 86** `absolute_project_paths`: SINGLE_TOOL_COUNT=$(grep "Found 1 tool calls" /home/sabawi/Development/flaskserver/server_complete.l...
- **Line 87** `absolute_project_paths`: MULTI_TOOL_COUNT=$(grep -E "Found [2-9] tool calls|Found [1-9][0-9] tool calls" /home/sabawi/Develop...

## 🔧 Recommended Fix Actions

### 1. CRITICAL - Absolute Paths (Must Fix)
- [ ] Fix: test_all_formats_comprehensive.py:34
- [ ] Fix: test_complete_final_verification.py:151
- [ ] Fix: test_attachment_fuzzy_matching.py:32
- [ ] Fix: fix_sandboxed_executor.py:23
- [ ] Fix: fix_sandboxed_executor.py:148
- [ ] Fix: test_direct_tool.py:27
- [ ] Fix: fastapi_server_complete.py:4512
- [ ] Fix: fastapi_server_complete.py:4541
- [ ] Fix: fastapi_server_complete.py:4548
- [ ] Fix: fastapi_server_complete.py:4803
- [ ] Fix: test_reindexing.py:31
- [ ] Fix: test_tool_request_patterns.py:72
- [ ] Fix: test_smart_detection.py:33
- [ ] Fix: test_smart_detection.py:72
- [ ] Fix: test_attachment_waiting.py:37
- [ ] Fix: test_title_escaping.py:7
- [ ] Fix: test_complete_fix.py:42
- [ ] Fix: test_complete_fix.py:90
- [ ] Fix: test_enhanced_executor.py:42
- [ ] Fix: test_enhanced_executor.py:58
- [ ] Fix: final_fix_test.py:21
- [ ] Fix: test_direct_tools.py:79
- [ ] Fix: fastapi_server_baseline.py:2255
- [ ] Fix: fastapi_server_baseline.py:2284
- [ ] Fix: fastapi_server_baseline.py:2291
- [ ] Fix: fastapi_server_baseline.py:2546
- [ ] Fix: arbitrator_system.py:179
- [ ] Fix: test_race_condition_fix.py:22
- [ ] Fix: test_race_condition_fix.py:141
- [ ] Fix: test_html_entities.py:7
- [ ] Fix: test_complete_workflow.py:95
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:31
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:217
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:288
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:373
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:474
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:562
- [ ] Fix: user_tools/_disabled_analytical_visualizer.py:631
- [ ] Fix: user_tools/process_executor.py:42
- [ ] Fix: user_tools/process_executor.py:43
- [ ] Fix: user_tools/process_executor.py:44
- [ ] Fix: user_tools/process_executor.py:45
- [ ] Fix: user_tools/process_executor.py:166
- [ ] Fix: user_tools/secure_email_sender.py:187
- [ ] Fix: user_tools/secure_email_sender.py:256
- [ ] Fix: user_tools/secure_email_sender.py:358
- [ ] Fix: user_tools/sandboxed_executor.py:615
- [ ] Fix: user_tools/sandboxed_executor.py:628
- [ ] Fix: config/arbitrator_logging_config.py:28
- [ ] Fix: tests/test_arbitrator_framework.py:263
- [ ] Fix: verify_multi_tool_calling.sh:34
- [ ] Fix: verify_multi_tool_calling.sh:62
- [ ] Fix: verify_multi_tool_calling.sh:82
- [ ] Fix: verify_multi_tool_calling.sh:86
- [ ] Fix: verify_multi_tool_calling.sh:87
- [ ] Fix: COMPLETE_MIGRATION_GUIDE.md:33
- [ ] Fix: TROUBLESHOOTING_GUIDE.md:7
- [ ] Fix: EMAIL_TOOL_SUMMARY.md:8
- [ ] Fix: EMAIL_TOOL_SUMMARY.md:22
- [ ] Fix: CRITICAL_MULTI_TOOL_CALLING_PROTECTION.md:84
- [ ] Fix: EMAIL_SECURITY_SETUP.md:148
- [ ] Fix: sandbox_workspace/Hype_Cycle_Analysis.md:16
- [ ] Fix: sandbox_workspace/merge_sort.md:57
- [ ] Fix: sandbox_workspace/graviton_research.md:15
- [ ] Fix: sandbox_workspace/game_theory_summary.md:9
- [ ] Fix: sandbox_workspace/gravity_paradox_edit.md:6
- [ ] Fix: docs/HARDCODED_PATH_DETECTION_STRATEGY.md:48
- [ ] Fix: docs/HARDCODED_PATH_DETECTION_STRATEGY.md:207

### 2. HIGH RISK - Relative Paths (Should Fix)
- [ ] Review: llm_config_tool.py:480
- [ ] Review: llm_config_tool.py:500
- [ ] Review: llm_config_tool.py:608
- [ ] Review: arbitrator_system.py:179
- [ ] Review: integrate_llm_abstraction.py:225
- [ ] Review: model_switcher.py:212
- [ ] Review: generate_google_token.py:18
- [ ] Review: generate_google_token.py:19
- [ ] Review: testing/test_missing_endpoints.py:141
- [ ] Review: sandbox_workspace/word_frequency.py:5
- ... and 106 more

### 3. SHELL SCRIPTS (Must Fix)
- [ ] Update: run_arbitrator_regression_test.sh:43
- [ ] Update: testing/test_embedding_service.sh:106
- [ ] Update: testing/test_embedding_service.sh:107
- [ ] Update: testing/test_embedding_service.sh:119
- [ ] Update: testing/test_embedding_service.sh:120
- [ ] Update: testing/test_embedding_service.sh:125