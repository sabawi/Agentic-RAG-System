#!/usr/bin/env python3
"""
Installation Validation Script
Tests all components mentioned in INSTALLATION.md to ensure accuracy.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run shell command and return result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, check=check)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def test_system_packages():
    """Test required system packages are installed."""
    print("🔍 Testing System Packages...")
    
    packages = [
        ("python3.11", "python3.11 --version"),
        ("git", "git --version"),
        ("curl", "curl --version"),
        ("tesseract", "tesseract --version"),
        ("sqlite3", "sqlite3 --version"),
    ]
    
    results = []
    for name, cmd in packages:
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"  ✅ {name}: {stdout.split()[0] if stdout else 'OK'}")
        else:
            print(f"  ❌ {name}: Not found or error")
        results.append((name, success))
    
    return all(result[1] for result in results)

def test_python_environment():
    """Test Python virtual environment and dependencies."""
    print("\n🐍 Testing Python Environment...")
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print(f"  {'✅' if in_venv else '❌'} Virtual environment: {'Active' if in_venv else 'Not active'}")
    
    # Test our dependency test script
    if os.path.exists("tests/test_dependencies.py"):
        success, stdout, stderr = run_command("python tests/test_dependencies.py")
        if success and "🎉 All dependencies successfully installed" in stdout:
            print("  ✅ Dependencies: All required packages installed")
            return True
        else:
            print("  ❌ Dependencies: Missing packages detected")
            if stderr:
                print(f"    Error: {stderr}")
            return False
    else:
        print("  ❌ tests/test_dependencies.py not found")
        return False

def test_ollama():
    """Test Ollama installation and models."""
    print("\n🤖 Testing Ollama...")
    
    # Test Ollama installation
    success, stdout, stderr = run_command("ollama --version")
    if not success:
        print("  ❌ Ollama: Not installed")
        return False
    
    print(f"  ✅ Ollama: {stdout}")
    
    # Test Ollama service
    success, stdout, stderr = run_command("curl -s http://localhost:11434/api/tags")
    if not success:
        print("  ❌ Ollama Service: Not running on localhost:11434")
        return False
    
    print("  ✅ Ollama Service: Running")
    
    # Test required models
    success, stdout, stderr = run_command("ollama list")
    if success:
        models = stdout.lower()
        required_models = ["qwen3:8b", "qwen2.5vl:3b"]
        missing_models = []
        
        for model in required_models:
            if model.lower() in models:
                print(f"  ✅ Model {model}: Available")
            else:
                print(f"  ❌ Model {model}: Not found")
                missing_models.append(model)
        
        if missing_models:
            print(f"  ⚠️  Missing models: {', '.join(missing_models)}")
            print("  💡 Run: ollama pull <model-name> to download")
            return False
        
        return True
    else:
        print("  ❌ Could not list Ollama models")
        return False

def test_environment_variables():
    """Test environment variables and configuration."""
    print("\n⚙️  Testing Environment Configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ .env file: Found")
        
        # Check for key environment variables
        with open(".env", "r") as f:
            env_content = f.read()
        
        if "OPENAI_API_KEY" in env_content:
            # Check if it's set to a real value (not placeholder)
            openai_key = os.getenv("OPENAI_API_KEY", "")
            if openai_key and not openai_key.startswith("sk-your-"):
                print("  ✅ OPENAI_API_KEY: Configured")
            else:
                print("  ⚠️  OPENAI_API_KEY: Not set or using placeholder")
        else:
            print("  ❌ OPENAI_API_KEY: Not found in .env")
    else:
        print("  ⚠️  .env file: Not found")
        print("  💡 Create .env file with your API keys")
    
    # Check configuration files
    config_files = [
        "config/llm_config.yaml",
        "primary_model_system_prompt.txt",
        "pre_tool_model_system_prompt.txt",
        "config/image_to_text_system_prompt.txt"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file}: Found")
        else:
            print(f"  ❌ {config_file}: Missing")

def test_email_system():
    """Test email system configuration."""
    print("\n📧 Testing Email System...")
    
    # Test mail command
    success, stdout, stderr = run_command("which mail")
    if success:
        print("  ✅ mail command: Available")
    else:
        print("  ❌ mail command: Not found")
        print("  💡 Install with: sudo apt install mailutils")
    
    # Test postfix service
    success, stdout, stderr = run_command("systemctl is-active postfix")
    if success and "active" in stdout:
        print("  ✅ Postfix service: Running")
    else:
        print("  ⚠️  Postfix service: Not running or not installed")

def test_server_startup():
    """Test if server can start successfully."""
    print("\n🚀 Testing Server Startup...")
    
    # Check if startup script exists
    if os.path.exists("start_complete.sh"):
        print("  ✅ start_complete.sh: Found")
    else:
        print("  ❌ start_complete.sh: Not found")
        return False
    
    # Check if server is already running
    success, stdout, stderr = run_command("curl -s http://localhost:5000/health", check=False)
    if success:
        print("  ✅ Server: Already running on localhost:5000")
        return True
    else:
        print("  ⚠️  Server: Not currently running")
        print("  💡 Start with: ./start_complete.sh")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Agentic-RAG Server Installation Validation")
    print("=" * 50)
    
    tests = [
        ("System Packages", test_system_packages),
        ("Python Environment", test_python_environment),
        ("Ollama & Models", test_ollama),
        ("Configuration", test_environment_variables),
        ("Email System", test_email_system),
        ("Server Readiness", test_server_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name}: Error during test - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All validation tests passed! Your installation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above and follow the installation guide.")
        print("📚 See INSTALLATION.md for detailed setup instructions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())