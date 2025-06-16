# 📖 User Guide - Advanced AI Code Generation System

## 🚀 Getting Started

### 1. Launch Modes

```bash
# Basic single terminal
python run.py

# Dual terminal system (recommended)
python run.py --dual

# Multi-step project mode
python run.py --project

# Experimental split view
python run.py --split

# Combined modes
python run.py --dual --project
```

### 2. Interface Overview

#### **Standard Mode**
- Clean single terminal interface
- Periodic status updates every 10 seconds
- Automatic code saving with timestamps
- Real-time performance monitoring

#### **Dual Terminal Mode** ⭐ 
- **Main Terminal**: Code generation and user interaction
- **Analytics Terminal**: Live system monitoring
  - GPU utilization (NVIDIA/AMD/Intel support)
  - Memory and CPU usage
  - Network statistics
  - Project progress
  - Token generation rates

## 💡 Basic Usage

### Simple Code Generation

```
💭 What would you like me to code?: Create a Python web scraper for news articles
```

The system will:
1. Analyze your request
2. Generate appropriate code
3. Save to `generated_code/` with timestamp
4. Display file path upon completion

### Code Improvement

```
💭 What would you like me to code?: improve: [paste your existing code here]
```

Features:
- **Recursive improvement**: Multiple optimization cycles
- **Performance analysis**: Bottleneck identification
- **Security checks**: Vulnerability scanning
- **Best practices**: Code quality improvements

### Project Breakdown

```
💭 What would you like me to code?: breakdown: Create a full-stack e-commerce application
```

The system will:
1. Analyze project complexity
2. Break into manageable steps
3. Create dependency map
4. Estimate time requirements
5. Generate step-by-step plan

## 🔄 Multi-Step Project Mode

### Automatic Project Management

When using `--project` mode:

```bash
python run.py --project
```

Features:
- **Automatic decomposition**: Complex projects → simple steps
- **Dependency tracking**: Ensures proper execution order
- **Progress monitoring**: Real-time step completion tracking
- **Context preservation**: Each step builds on previous work
- **Error recovery**: Handles step failures gracefully

### Project Stages

1. **PLANNING** - Requirements analysis, architecture planning
2. **DESIGN** - System design, UI/UX, database schema
3. **IMPLEMENTATION** - Core development, feature implementation
4. **TESTING** - Unit tests, integration tests, user testing
5. **OPTIMIZATION** - Performance tuning, code cleanup
6. **DOCUMENTATION** - Code docs, user guides, deployment

### Example Project Flow

```
Input: "Create a Django blog with user authentication"

Step 1: [PLANNING] - Analyze requirements and plan architecture
Step 2: [DESIGN] - Design database models and URL structure  
Step 3: [IMPLEMENTATION] - Create Django project structure
Step 4: [IMPLEMENTATION] - Implement user authentication
Step 5: [IMPLEMENTATION] - Create blog models and views
Step 6: [TESTING] - Write unit tests for all components
Step 7: [DOCUMENTATION] - Create setup and usage documentation
```

## 📊 System Monitoring

### Dual Terminal Analytics

The analytics terminal provides:

#### **System Resources**
- **CPU Usage**: Real-time percentage with status indicators
- **Memory Usage**: RAM consumption with health status
- **GPU Metrics**: GPU utilization and VRAM usage (multi-vendor support)
- **Disk Usage**: Storage space monitoring
- **Network Activity**: Data transfer rates

#### **Project Metrics**
- **Session Statistics**: Requests, success rate, uptime
- **Performance Data**: Response times, token rates
- **Active Processes**: Running system components
- **Log Files**: Available log information

#### **Status Indicators**
- 🟢 **Normal**: System operating optimally
- 🟡 **High**: Resource usage elevated but acceptable
- 🔴 **Critical**: Resource usage at dangerous levels

## ⚙️ Advanced Configuration

### Model Parameters

Edit `config.yaml`:

```yaml
model_params:
  temperature: 0.1        # 0.0 = deterministic, 1.0 = creative
  top_p: 0.9             # Nucleus sampling
  top_k: 40              # Top-k sampling
  max_tokens: 8192       # Maximum response length
  context_length: 131072 # Extended context (131k tokens)
```

### Performance Tuning

```yaml
performance:
  track_token_usage: true      # Monitor token consumption
  track_response_time: true    # Monitor response times
  track_memory_usage: true     # Monitor memory usage
  benchmark_mode: false        # Enable for performance testing
```

### Code Generation Settings

```yaml
code_generation:
  output_directory: "generated_code"
  save_format: "organized"     # organized, flat, timestamped
  auto_save: true             # Automatically save all code
  file_extensions:
    python: ".py"
    javascript: ".js"
    typescript: ".ts"
    # ... more languages
```

## 🎯 Advanced Features

### Extended Context Length

With 131k token context:
- **Complex Projects**: Handle large codebases
- **Long Conversations**: Maintain context across sessions
- **Detailed Requirements**: Process extensive specifications
- **Multi-file Projects**: Understand relationships between files

### GPU Acceleration

GPU Optimizations:
- **Model Loading**: Efficient VRAM utilization (16-24GB typical)
- **Inference Speed**: 50-80 tokens/second on high-end GPUs
- **Parallel Processing**: Multi-threaded operations
- **Memory Management**: Smart VRAM allocation

### Smart Code Organization

```
generated_code/
└── create_a_flask_web_app_20250616_153105/
    ├── app.py                 # Main application
    ├── models.py              # Database models
    ├── templates/             # HTML templates
    │   ├── base.html
    │   └── index.html
    ├── static/                # CSS/JS files
    │   └── style.css
    ├── requirements.txt       # Dependencies
    └── README.md             # Project documentation
```

## 🛠️ Troubleshooting

### Common Issues

#### **No Analytics Terminal**
```bash
# Check terminal emulator
which gnome-terminal
# or
which konsole

# Install if missing
sudo apt install gnome-terminal
```

#### **GPU Not Utilized**
```bash
# Check GPU status
nvidia-smi

# Verify Ollama GPU usage
sudo docker logs ollama  # If using Docker
```

#### **Slow Generation**
- Check GPU temperature and throttling
- Verify adequate VRAM (need ~22GB free)
- Monitor system resources in analytics terminal
- Reduce context length if needed

#### **Memory Issues**
```bash
# Check system memory
free -h

# Check GPU memory
nvidia-smi

# Reduce batch size in config.yaml
model_params:
  max_tokens: 4096  # Reduce from 8192
```

### Performance Optimization

#### **For Best Performance:**
1. Use analytics dashboard mode for monitoring
2. Ensure GPU has adequate cooling and power
3. Close unnecessary applications
4. Use NVMe SSD for faster I/O
5. Monitor resource usage continuously

#### **Resource Management:**
- **CPU**: Keep below 80% usage
- **Memory**: Maintain 4GB+ free RAM  
- **GPU**: Monitor temperature <80°C (varies by GPU)
- **Storage**: Keep 10GB+ free space

## 📈 Usage Examples

### Web Development

```bash
# Simple web app
"Create a Flask blog with SQLite database"

# Complex application  
"Build a React + Node.js chat application with real-time messaging"

# Full stack project
"Create a Django e-commerce site with payment integration and admin panel"
```

### Data Science

```bash
# Data analysis
"Create a Pandas script to analyze sales data from CSV"

# Machine learning
"Build a scikit-learn classifier for iris dataset with visualization"

# Deep learning
"Create a TensorFlow neural network for image classification"
```

### System Programming

```bash
# CLI tools
"Create a Python command-line file organizer"

# System monitoring
"Build a system resource monitor with real-time graphs"

# Network tools
"Create a port scanner with multithreading"
```

### Game Development

```bash
# Simple games
"Create a Python Snake game with Pygame"

# Complex games  
"Build a 2D platformer with physics and level editor"
```

## 🔍 Monitoring and Debugging

### Log Files

```bash
# System logs
tail -f logs/system.log

# Session logs
cat logs/session_20250616_153105.json

# Application logs
tail -f logs/auto_coder.log
```

### Performance Analysis

Use dual terminal mode to monitor:
- Token generation rates
- Memory usage patterns
- GPU utilization trends
- Response time distribution

### Debug Mode

Enable verbose logging:

```yaml
logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

**💡 Tip**: Use `--dual --project` for the best experience with complex projects! 