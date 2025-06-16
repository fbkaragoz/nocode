# Installation Guide

Detailed installation instructions for the AI Code Generation System.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space
- Internet connection for model downloads

### Required Software
- [Ollama](https://ollama.ai/) - Local LLM runtime
- Git - Version control
- Text editor or IDE

## Step-by-Step Installation

### 1. Install Ollama

**Linux/macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download installer from [ollama.ai](https://ollama.ai)

### 2. Download AI Model

```bash
# Start Ollama service
ollama serve

# In another terminal, pull DeepSeek Coder model
ollama pull huihui_ai/deepseek-r1-Fusion:32b-coder-9010

# Or use a smaller model for lower-end systems
ollama pull deepseek-coder:6.7b
```

### 3. Clone Repository

```bash
git clone <repository-url>
cd nocode
```

### 4. Setup Python Environment

**Using conda (recommended):**
```bash
conda create -n nocode_env python=3.9
conda activate nocode_env
pip install -r requirements.txt
```

**Using venv:**
```bash
python -m venv nocode_env
source nocode_env/bin/activate  # Linux/macOS
# or
nocode_env\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 5. Configure System

Copy and edit configuration:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your preferred settings
```

### 6. Test Installation

```bash
# Start Ollama if not running
ollama serve &

# Test the system
python run.py
```

## Troubleshooting

### Common Issues

**Ollama connection failed:**
- Ensure Ollama service is running: `ollama serve`
- Check port 11434 is not blocked
- Verify model is downloaded: `ollama list`

**Python import errors:**
- Activate virtual environment
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

**Memory issues:**
- Use smaller model: `deepseek-coder:6.7b`
- Reduce context length in config.yaml
- Close other applications

### Getting Help

- Check logs in `logs/` directory
- View system status with `--debug` flag
- Report issues on GitHub

## Performance Optimization

### Hardware Recommendations
- **Minimum**: 8GB RAM, 4-core CPU
- **Recommended**: 16GB RAM, 8-core CPU, GPU support
- **Optimal**: 32GB RAM, GPU with 8GB+ VRAM

### Configuration Tips
- Adjust `max_tokens` based on available memory
- Use `temperature: 0.1` for consistent results
- Enable GPU acceleration if available

## Next Steps

After installation:
1. Read [Configuration Reference](configuration.md)
2. Review [API Documentation](api.md)
3. Explore example projects
4. Join community discussions 