# LLM Abstraction Layer Design v0.9.0

## 🎯 **Goals**

1. **Cross-Platform Compatibility**: Support Windows 11+ and Linux
2. **Configurable LLM Providers**: Support Ollama, OpenAI, Qwen API, and others
3. **Provider Abstraction**: Unified interface for tool calling and primary LLM
4. **Zero Regression**: Maintain existing functionality and performance

## 🏗️ **Architecture Overview**

### **1. LLM Provider Interface**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncIterator[str]
    
    @abstractmethod
    async def generate_tools(self, prompt: str, model: str, tools: List[dict], **kwargs) -> dict
    
    @abstractmethod
    async def health_check(self) -> bool
    
    @abstractmethod
    def get_available_models(self) -> List[str]
```

### **2. Provider Implementations**

#### **OllamaProvider**
- Current implementation (localhost:11434)
- Maintains existing streaming and tool calling
- Cross-platform Ollama support

#### **OpenAIProvider**  
- OpenAI GPT-4+ integration
- ChatCompletion API with function calling
- Streaming support for both tool and primary LLM

#### **QwenProvider**
- Qwen API integration  
- Compatible with Qwen function calling format
- Cloud-based model access

### **3. Configuration System**
```yaml
# config/llm_config.yaml
llm:
  providers:
    primary:
      type: "ollama"  # ollama | openai | qwen
      config:
        base_url: "http://127.0.0.1:11434"
        model: "llama3.2:3b"
        api_key: null  # For cloud providers
        
    tool_calling:
      type: "openai"  # ollama | openai | qwen  
      config:
        api_key: "${OPENAI_API_KEY}"
        model: "gpt-4-1106-preview"
        base_url: "https://api.openai.com/v1"
        
  fallback:
    enabled: true
    order: ["ollama", "openai"]  # Fallback sequence
```

### **4. Provider Factory**
```python
class LLMProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, config: dict) -> LLMProvider:
        providers = {
            'ollama': OllamaProvider,
            'openai': OpenAIProvider, 
            'qwen': QwenProvider
        }
        return providers[provider_type](config)
```

## 🪟 **Cross-Platform Compatibility**

### **File Path Handling**
```python
import os
from pathlib import Path

# Replace hardcoded paths
OLD: "/tmp/email_debug.eml"
NEW: Path.home() / "AppData" / "Local" / "Temp" / "email_debug.eml"  # Windows
NEW: Path("/tmp") / "email_debug.eml"  # Linux

# Use pathlib consistently
config_dir = Path.home() / ".agentic_rag"  # Cross-platform config
data_dir = config_dir / "data"
logs_dir = config_dir / "logs"
```

### **Process Management**
```python
# Replace shell scripts with Python
OLD: "./stop_complete.sh && ./start_complete.sh"
NEW: ProcessManager.restart_server()  # Cross-platform

# Windows service integration
if platform.system() == "Windows":
    # Use Windows Service API
    ServiceManager.install_service()
```

### **Dependency Detection**
```python
class PlatformDetector:
    @staticmethod
    def get_platform_config():
        if platform.system() == "Windows":
            return WindowsConfig()
        else:
            return LinuxConfig()
```

## 📋 **Implementation Plan**

### **Phase 1: Core Abstraction**
1. Create `LLMProvider` interface
2. Implement `OllamaProvider` (migrate existing code)
3. Create configuration system with YAML support
4. Implement provider factory pattern

### **Phase 2: Cloud Providers**
1. Implement `OpenAIProvider` with function calling
2. Implement `QwenProvider` 
3. Add API key management and security
4. Implement fallback mechanism

### **Phase 3: Cross-Platform**
1. Replace hardcoded Unix paths with `pathlib`
2. Create Windows-specific process management
3. Add platform detection and configuration
4. Update startup scripts for Windows

### **Phase 4: Testing & Documentation**
1. Test all provider combinations
2. Cross-platform testing (Windows 11, Linux)
3. Performance benchmarking
4. Update documentation and examples

## 🔧 **Key Files to Modify**

### **New Files**
- `llm_providers/__init__.py` - Provider interface
- `llm_providers/base.py` - Abstract base class
- `llm_providers/ollama.py` - Ollama implementation
- `llm_providers/openai.py` - OpenAI implementation  
- `llm_providers/qwen.py` - Qwen implementation
- `llm_providers/factory.py` - Provider factory
- `config/llm_config.yaml` - LLM configuration
- `utils/platform.py` - Cross-platform utilities
- `utils/paths.py` - Path handling utilities

### **Modified Files**
- `fastapi_server_complete.py` - Replace direct Ollama calls
- `document_interrogator.py` - Cross-platform paths
- `user_tools/*.py` - Path handling updates
- `requirements.txt` - Add new dependencies

## 🎯 **Benefits**

### **Flexibility**
- **Mix and match**: Use OpenAI for tool calling, Ollama for primary LLM
- **Cost optimization**: Use local models when possible, cloud when needed
- **Performance tuning**: Choose optimal model for each task

### **Reliability**  
- **Fallback support**: Auto-switch providers on failure
- **Health monitoring**: Provider health checks and recovery
- **Cross-platform**: Run on Windows development, Linux production

### **Future-Proof**
- **Easy integration**: Add new LLM providers with minimal code
- **Configuration-driven**: Change providers without code changes
- **Standardized interface**: Consistent API across all providers

## 🔒 **Security Considerations**

### **API Key Management**
- Environment variable support
- Encrypted configuration files  
- Key rotation capabilities
- Audit logging for API usage

### **Provider Validation**
- Input sanitization for all providers
- Response validation and safety checks
- Rate limiting and quota management
- Error handling and secure fallbacks

---

**Status**: 🎯 **Ready for Implementation** - Comprehensive design with clear phases and benefits