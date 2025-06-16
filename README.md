# 🚀 Auto-Coder: A Streaming-First Local AI Coding Assistant

This project is a simple, streaming-first AI code generation system designed to run entirely on your local machine using Ollama and your own GPU. It provides a terminal-based interface to interact with a local language model for generating and editing code.

## ✨ Core Features

- **🧠 Local First**: Works entirely offline with your local Ollama instance. No data leaves your machine.
- **⚡ Streaming Responses**: See the code being generated in real-time, character by character.
- **📝 File Editing & Context**: The system can remember the last file it created. You can ask it to fix or modify that file, and it will read the content, understand the context, and update it.
- **🐍 Python Focused**: Optimized for generating and editing Python scripts.
- **🔧 Clean Architecture**: A simple, understandable architecture that separates concerns (CLI, Engine, Services).

## 🚦 Quick Start

### 1. Prerequisites

- **Ollama**: Ensure [Ollama](https://ollama.ai/) is installed and running.
- **A Language Model**: Pull a model suitable for coding.
  ```bash
  # Recommended: A powerful, instruction-tuned model
  ollama pull huihui_ai/deepseek-r1-Fusion:32b-coder-9010
  
  # A smaller alternative
  ollama pull deepseek-coder:6.7b
  ```
- **Python Environment**: Python 3.9+ is recommended.

### 2. Installation

```bash
# Clone the repository
git clone <repository_url>
cd nocode

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

The model used is hardcoded in `src/config/settings.py`. Open this file and change the `model_name` to the one you have downloaded in Ollama.

### 4. Usage

Simply run the application from your terminal:
```bash
python run.py
```
The application will start, and you can begin giving it coding instructions.

## 🎮 How to Use

### Creating a New File
Simply ask for what you want to create.
> `create a simple snake game in python`

The system will generate the code and save it under the `generated_code/` directory.

### Editing an Existing File
After a file is created, you can ask the system to fix or modify it.
> `the game ended with an error, can you fix @simple_snake_game.py`

The system will read the specified file, provide the context to the model, and overwrite the existing file with the corrected version. A `.backup` of the old file will be created automatically.

## 🏗️ Simplified Architecture

- **`run.py`**: The main entry point.
- **`src/core/cli/`**: Manages the user interface and command flow.
  - `cli_manager.py`: The main loop for the CLI.
  - `command_processor.py`: Orchestrates requests to the engine.
- **`src/core/auto_coder.py`**: The "brain" of the application. It talks to the AI model and handles all file I/O (saving, editing, backups).
- **`src/services/ollama_service.py`**: Handles all communication with the Ollama API.
- **`src/config/settings.py`**: A simple class for application settings.
- **`.secrets/prompts.yaml`**: Contains the structured instruction templates sent to the AI.
- **`generated_code/`**: The output directory for all generated files.

This project serves as a solid foundation for building more complex, autonomous coding agents.

## 🎯 **Example Commands**

```bash
# Generate a complete web application
"Create a Flask web app with user authentication and SQLite database"

# Multi-file project
"Build a Python REST API with Docker deployment and unit tests"

# Code improvement
"improve: [paste your code here]"

# Project breakdown
"breakdown: Create a real-time chat application with React and Node.js"
```

## 📈 **Performance Metrics**

With High-end GPU:
- **Generation Speed**: 50-80 tokens/second
- **Context Length**: 131k tokens
- **Response Time**: 2-5 seconds average
- **Memory Usage**: ~16-24GB GPU VRAM
- **CPU Efficiency**: Multi-threaded processing

## 🔧 **Configuration**

Edit `config.yaml`:

```yaml
model_params:
  temperature: 0.1          # Creativity vs consistency
  context_length: 131072    # Max context (131k tokens)
  max_tokens: 8192         # Response length

performance:
  track_token_usage: true
  track_response_time: true
  benchmark_mode: false
```

## 📝 **Output Organization**

```
generated_code/
└── project_name_20250616_153105/
    ├── block_1_python.py
    ├── block_2_html.html
    └── requirements.txt

logs/
├── session_20250616_153105.json
├── system.log
└── auto_coder.log
```

## 🎲 **Advanced Features**

### **Recursive Code Improvement**
```bash
improve: [your code]
```
Automatically applies multiple improvement cycles for optimization.

### **Task Decomposition**
```bash
breakdown: Create a microservices architecture
```
Breaks complex projects into manageable subtasks with dependencies.

### **Real-time Analytics**
- GPU utilization monitoring
- Token generation rates
- Memory usage patterns
- Network activity tracking

## 🚨 **Troubleshooting**

### **GPU Not Detected**
```bash
# For NVIDIA
nvidia-smi  # Check GPU status

# For AMD
rocm-smi  # Check AMD GPU status

# For Intel
intel_gpu_top  # Check Intel GPU status
```

### **Ollama Connection Issues**
```bash
ollama list  # Check installed models
ollama serve  # Restart Ollama service
```

### **Performance Issues**
- Ensure GPU has adequate cooling and power
- Check VRAM availability with appropriate GPU command
- Monitor system resources in analytics dashboard mode

## 📜 **License**

MIT License - See LICENSE file for details.

---

**🔥 Powered by DeepSeek R1 + GPU acceleration for maximum performance**

# Professional AI Code Generation System

## ✨ Enterprise-Grade Security & IP Protection

This system implements a professional architecture with **complete IP protection**:

- **🔒 Zero Hardcoded Instructions**: All AI behaviors loaded from secure, encrypted sources
- **🎯 Dynamic Model Parameters**: Auto-configured based on system resources and request complexity
- **🛡️ IP-Protected Behaviors**: Proprietary AI instructions never exposed in public codebase
- **⚡ Resource-Aware Optimization**: Automatic scaling based on available hardware
- **🔄 Fallback Safety**: Graceful degradation when secure sources unavailable

## 🏗️ Security Architecture

```
📁 .secrets/                    # NEVER COMMITTED - IP Protected
├── behavior_profiles.yaml      # Proprietary AI behavior definitions
└── [encrypted_instructions]    # Additional secure configurations

📁 src/core/
├── behavior_loader.py          # Secure IP loading system
├── model_context_manager.py    # Dynamic parameter management  
└── secure_prompt_manager.py    # IP-protected prompt coordination

📁 config/
└── app.yaml                    # General settings only (no IP content)
```

## 🚀 Dynamic Configuration

### Automatic Resource Detection
- **System Analysis**: CPU, Memory, GPU capabilities
- **Resource Tiers**: Low → Medium → High → Enterprise
- **Performance Optimization**: Context length and token limits auto-adjusted

### Request Complexity Analysis
- **Simple**: Basic scripts, quick fixes
- **Moderate**: Standard applications, refactoring
- **Complex**: Multi-file projects, architecture design
- **Enterprise**: Production systems, security-critical code

### Model Parameter Optimization
```python
# NO MORE HARDCODED VALUES!
ModelConfig(
    context_length=auto_detected,    # Based on available resources
    max_tokens=complexity_adjusted,   # Scaled by request complexity
    temperature=task_optimized,       # Adjusted for code vs creative tasks
    buffer_ratio=performance_tuned    # Memory management
)
```

## 🛡️ IP Protection Features

### Zero-Trust Architecture
- ✅ **No hardcoded prompts** in source code
- ✅ **No hardcoded model parameters** anywhere
- ✅ **Secure behavior loading** with validation
- ✅ **Encrypted instruction storage** (.secrets/ directory)
- ✅ **Automatic security validation** on startup

### Production-Ready Security
- **Fallback Mechanisms**: System works with minimal functionality if secrets unavailable
- **Security Status Monitoring**: Real-time validation of IP protection
- **Access Control**: Behavior profiles only accessible through secure loader
- **Audit Trail**: All security events logged for compliance 