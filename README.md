# 🚀 Advanced AI Code Generation System

High-performance AI-powered code generation system using **DeepSeek R1** with **RTX 4090** acceleration.

## ✨ **Key Features**

- **🧠 Extended Context**: 131k tokens for complex projects
- **⚡ GPU Acceleration**: RTX 4090 optimized performance  
- **🔄 Multi-Step Projects**: Automatic project breakdown and execution
- **📊 Dual Terminal**: Separate analytics monitoring window
- **💾 Smart Organization**: Automatic code saving with timestamps
- **🔍 Real-time Monitoring**: CPU/Memory/GPU usage tracking
- **🎯 Multi-Language**: Python, JavaScript, TypeScript, Java, C++, Go, Rust

## 🚦 **Quick Start**

### Prerequisites

```bash
# GPU driver and CUDA
nvidia-smi  # Should show RTX 4090

# Ollama with DeepSeek R1
ollama pull huihui_ai/deepseek-r1-Fusion:32b-coder-9010
```

### Installation

```bash
git clone <repository>
cd nocode
conda env create -f environment.yml
conda activate nocode_env
```

### Usage

```bash
# Standard mode
python run.py

# Dual terminal (main + analytics)
python run.py --dual

# Multi-step project mode
python run.py --project

# Experimental split view
python run.py --split

# Combined modes
python run.py --dual --project
```

## 🎮 **Interface Modes**

### **Standard Mode** (Default)
- Single terminal with periodic status updates
- Automatic code saving to `generated_code/`
- Real-time performance monitoring

### **Dual Terminal Mode** (`--dual`)
- **Main Terminal**: User interaction and code generation
- **Analytics Terminal**: Live system monitoring
  - CPU/Memory/GPU metrics
  - Project progress tracking  
  - Network and disk usage
  - Real-time charts and graphs

### **Project Mode** (`--project`)
- Automatic project breakdown into steps
- Step-by-step execution with dependencies
- Progress tracking across project phases
- Multi-file project organization

## 📊 **System Requirements**

### **Minimum**
- Linux (Ubuntu 20.04+)
- 16GB RAM
- NVIDIA GPU (RTX 3070+)
- Python 3.8+

### **Recommended**
- Linux (Ubuntu 22.04+)
- 32GB+ RAM
- NVIDIA RTX 4090 (24GB VRAM)
- Python 3.10+
- NVMe SSD storage

## 🏗️ **Architecture**

```
├── Core Engine
│   ├── AutoCoderEngine     # Main AI interface
│   ├── ProjectManager      # Multi-step projects
│   └── StreamManager       # Real-time streaming
├── Interfaces
│   ├── TerminalInterface   # Standard UI
│   ├── DualTerminalInterface # Dual window system
│   └── SplitTerminalInterface # Experimental split
├── Services
│   ├── OllamaService      # Model communication
│   └── SystemMonitor     # Performance tracking
└── Storage
    ├── generated_code/    # Auto-saved projects
    ├── logs/             # Session logs
    └── cache/            # Performance cache
```

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

With RTX 4090:
- **Generation Speed**: 50-80 tokens/second
- **Context Length**: 131k tokens
- **Response Time**: 2-5 seconds average
- **Memory Usage**: ~22GB GPU VRAM
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
nvidia-smi  # Check GPU status
nvidia-docker --version  # Verify CUDA
```

### **Ollama Connection Issues**
```bash
ollama list  # Check installed models
ollama serve  # Restart Ollama service
```

### **Performance Issues**
- Ensure RTX 4090 has adequate cooling
- Check VRAM availability: `nvidia-smi`
- Monitor system resources in dual terminal mode

## 📜 **License**

MIT License - See LICENSE file for details.

---

**🔥 Powered by DeepSeek R1 + RTX 4090 for maximum performance** 