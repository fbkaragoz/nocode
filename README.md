# 🚀 AI Code Generation System

High-performance AI-powered code generation system using **DeepSeek R1** with **GPU acceleration**.

## ✨ **Key Features**

- **🧠 Extended Context**: 131k tokens for complex projects
- **⚡ GPU Acceleration**: Optimized for NVIDIA, AMD, and Intel GPUs
- **🔄 Multi-Step Projects**: Automatic project breakdown and execution
- **📊 Analytics Dashboard**: Real-time system monitoring
- **💾 Smart Organization**: Automatic code saving with timestamps
- **🔍 System Monitoring**: CPU/Memory/GPU usage tracking
- **🎯 Multi-Language**: Python, JavaScript, TypeScript, Java, C++, Go, Rust

## 🚦 **Quick Start**

### Prerequisites

```bash
# GPU driver (NVIDIA/AMD/Intel)
# For NVIDIA: nvidia-smi
# For AMD: rocm-smi
# For Intel: intel_gpu_top

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

# Analytics dashboard mode
python run.py --analytics

# Multi-step project mode
python run.py --project

# Minimal interface mode
python run.py --minimal

# Combined modes
python run.py --analytics --project
```

## 🎮 **Interface Modes**

### **Standard Mode** (Default)
- Clean terminal interface with periodic status updates
- Automatic code saving to `generated_code/`
- Real-time performance monitoring

### **Analytics Dashboard Mode** (`--analytics`)
- **Main Terminal**: User interaction and code generation
- **Analytics Dashboard**: Live system monitoring in separate window
  - CPU/Memory/GPU metrics (NVIDIA/AMD/Intel support)
  - Project progress tracking  
  - Network and disk usage
  - Real-time performance charts

### **Project Mode** (`--project`)
- Automatic project breakdown into steps
- Step-by-step execution with dependencies
- Progress tracking across project phases
- Multi-file project organization

### **Minimal Mode** (`--minimal`)
- Streamlined interface for low-resource environments
- Essential features only
- Reduced visual elements

## 📊 **System Requirements**

### **Minimum**
- Linux (Ubuntu 20.04+)
- 16GB RAM
- GPU with 8GB+ VRAM (NVIDIA/AMD/Intel)
- Python 3.8+

### **Recommended**
- Linux (Ubuntu 22.04+)
- 32GB+ RAM
- High-end GPU with 16GB+ VRAM
- Python 3.10+
- NVMe SSD storage

## 🏗️ **Architecture**

```
├── Core Engine
│   ├── AutoCoderEngine     # Main AI interface
│   ├── ProjectManager      # Multi-step projects
│   └── StreamManager       # Real-time streaming
├── Display Layer
│   ├── DisplayManager      # Professional UI coordinator
│   ├── UIFormatter         # Clean formatting utilities
│   └── AnalyticsDisplay    # System monitoring dashboard
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