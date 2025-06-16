# 🚀 Advanced AI Code Generation System

An enterprise-grade automatic code generation system powered by Ollama and DeepSeek Coder models. Features real-time streaming, split terminal interface, configurable AI behaviors, and advanced performance monitoring.

## ✨ Features

### 🔥 Core Capabilities
- **Real-time Code Generation**: Streaming code generation with live syntax highlighting
- **Split Terminal Interface**: Professional dual-pane interface with Rich UI components
- **Configurable AI Behaviors**: YAML-based model behavior configuration
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- **Recursive Code Improvement**: AI-powered iterative code enhancement
- **Task Decomposition**: Break down complex projects into manageable subtasks

### 📊 Advanced Features
- **Live Performance Metrics**: Real-time tracking of response time, tokens/second, memory usage
- **System Monitoring**: Background monitoring with health checks
- **Session Management**: Conversation history and context preservation
- **Auto-save Functionality**: Organized file structure with timestamp-based saves
- **Enhanced CLI Commands**: Special commands for configuration and code analysis

### 🎯 Technical Highlights
- Clean architecture with modular design
- Asyncio-based concurrent processing
- Enterprise-grade error handling
- Comprehensive logging system
- Memory-efficient conversation management
- Configurable model parameters

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Ollama installed and running
- DeepSeek Coder or compatible model

### Quick Setup

1. **Clone the repository:**
```bash
git clone https://github.com/fbkaragoz/nocode.git
cd nocode
```

2. **Create and activate conda environment:**
```bash
conda create -n nocode_env python=3.9
conda activate nocode_env
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure Ollama model:**
```bash
# Pull DeepSeek Coder model (or your preferred model)
ollama pull huihui_ai/deepseek-r1-Fusion:32b-coder-9010
```

5. **Run the system:**
```bash
python run.py
```

## 🎮 Usage

### Basic Commands
- **Code Generation**: Simply describe what you want to build
- **Recursive Improvement**: `improve: <your_code_here>`
- **Task Breakdown**: `breakdown: <project_description>`
- **Configuration**: `config: <setting>=<value>`
- **Clear History**: `clear` or `clear history`
- **Help**: `help` or `h`
- **Exit**: `exit`, `quit`, or `q`

### Example Sessions

**Simple Code Generation:**
```
🎯 What would you like me to do? > Create a Python function to calculate fibonacci numbers

# AI generates optimized fibonacci function with documentation
```

**Recursive Improvement:**
```
🎯 What would you like me to do? > improve: def fib(n): return fib(n-1) + fib(n-2) if n > 1 else n

# AI analyzes and provides optimized version with memoization
```

**Task Decomposition:**
```
🎯 What would you like me to do? > breakdown: Build a REST API for a todo application

# AI breaks down into subtasks: database design, models, endpoints, authentication, etc.
```

## 🔧 Configuration

### Model Behaviors (`src/templates/model_behaviors.yaml`)
```yaml
code_generation:
  creativity: "balanced"     # conservative, balanced, creative
  style: "enterprise"       # startup, standard, enterprise
  complexity: "adaptive"    # simple, adaptive, complex
  
code_review:
  standards: "enterprise"   # startup, standard, enterprise
  strictness: "balanced"    # lenient, balanced, strict
```

### System Settings (`config.yaml`)
```yaml
ollama:
  base_url: "http://127.0.0.1:11434"
  model_name: "huihui_ai/deepseek-r1-Fusion:32b-coder-9010"
  timeout: 300

model_params:
  temperature: 0.1
  top_p: 0.9
  max_tokens: 4096
```

## 🏗️ Architecture

```
src/
├── config/          # Configuration management
├── core/            # Core engine and CLI
├── models/          # Data models and schemas
├── services/        # External service integrations
├── templates/       # Prompt templates and behaviors
├── ui/              # User interface components
└── utils/           # Utility functions
```

### Key Components

- **AutoCoderEngine**: Core code generation engine
- **OllamaService**: Ollama API integration with smart caching
- **SplitTerminalInterface**: Rich-based UI with real-time updates
- **PromptManager**: Dynamic prompt template management
- **EnhancedCLI**: Feature-rich command-line interface

## 🔬 Performance Metrics

The system tracks and displays:
- **Response Time**: End-to-end generation time
- **Tokens/Second**: Model inference speed
- **Memory Usage**: System resource consumption
- **Model Confidence**: Estimated response quality
- **Session Statistics**: Conversation metrics

## 🛡️ Security & Best Practices

- Input validation and sanitization
- Safe code execution environment
- Configurable operation permissions
- Vulnerability scanning for generated code
- Secure model parameter handling

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Code formatting
black src/
isort src/

# Linting
flake8 src/
```

### Project Structure Guidelines
- Follow clean architecture principles
- Use type hints and docstrings
- Write comprehensive tests
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for the excellent local LLM runtime
- [DeepSeek](https://deepseek.com/) for the powerful coding models
- [Rich](https://rich.readthedocs.io/) for beautiful terminal interfaces
- The open source community for inspiration and contributions

## 📊 Roadmap

### Phase 1 (Current)
- [x] Basic code generation
- [x] Split terminal interface
- [x] Real-time streaming
- [x] Performance monitoring

### Phase 2 (Next)
- [ ] Plugin system
- [ ] Web interface
- [ ] Team collaboration features
- [ ] Advanced code analysis

### Phase 3 (Future)
- [ ] Multi-model support
- [ ] Cloud deployment
- [ ] Enterprise features
- [ ] API marketplace

## 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/fbkaragoz/nocode/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/fbkaragoz/nocode/discussions)
- **Documentation**: [Wiki](https://github.com/fbkaragoz/nocode/wiki)

## 📈 Stats

![GitHub stars](https://img.shields.io/github/stars/fbkaragoz/nocode)
![GitHub forks](https://img.shields.io/github/forks/fbkaragoz/nocode)
![GitHub issues](https://img.shields.io/github/issues/fbkaragoz/nocode)
![GitHub license](https://img.shields.io/github/license/fbkaragoz/nocode)

---

**Built with ❤️ for the AI coding community** 