# AI Code Generation System

Advanced AI-powered code generation system using Ollama with DeepSeek Coder model.

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd nocode
pip install -r requirements.txt

# Run system
python run.py                # Standard interface
python run.py --split        # Split terminal interface
```

## Requirements

- Python 3.8+
- Ollama running locally
- DeepSeek Coder model installed

## Configuration

Edit `config.yaml` for system settings:

```yaml
model_name: "huihui_ai/deepseek-r1-Fusion:32b-coder-9010"
ollama_url: "http://localhost:11434"
output_directory: "generated_code"
```

## Commands

- `generate <description>` - Generate code
- `improve <code>` - Improve existing code
- `breakdown <task>` - Break down complex tasks
- `explain <code>` - Explain code functionality
- `help` - Show help
- `clear` - Clear session
- `exit` - Exit system

## Architecture

```
src/
├── core/           # Core system components
│   ├── cli/        # CLI management
│   ├── interface/  # Terminal interfaces
│   └── streaming/  # Real-time streaming
├── models/         # Data models
├── services/       # External services
└── config/         # Configuration
```

## Features

- **Dual Interface**: Standard and split terminal modes
- **Real-time Streaming**: Live code generation display
- **System Monitoring**: Resource usage tracking
- **Session Management**: Conversation history and caching
- **Modular Design**: Clean separation of concerns

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)

## License

MIT License - see LICENSE file for details. 