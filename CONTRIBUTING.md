# Contributing to Advanced AI Code Generation System

Thank you for considering contributing to our project! This document provides guidelines for contributing.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Ollama installed and running
- Git for version control

### Development Setup

1. **Fork and clone the repository:**
```bash
git clone https://github.com/fbkaragoz/nocode.git
cd nocode
```

2. **Create development environment:**
```bash
conda create -n nocode_dev python=3.9
conda activate nocode_dev
pip install -r requirements.txt
```

3. **Install development dependencies:**
```bash
pip install black isort flake8 pytest mypy
```

4. **Run tests:**
```bash
python -m pytest tests/
```

## 📝 Code Style

### Python Code Standards
- Follow PEP 8 style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Maximum line length: 88 characters

### Code Formatting
```bash
# Format code
black src/
isort src/

# Check linting
flake8 src/
mypy src/
```

### Pre-commit Hooks
We recommend setting up pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## 🏗️ Architecture Guidelines

### Project Structure
```
src/
├── config/          # Configuration management
├── core/            # Core business logic
├── models/          # Data models and schemas
├── services/        # External service integrations
├── templates/       # Prompt templates and behaviors
├── ui/              # User interface components
└── utils/           # Utility functions
```

### Design Principles
- **Clean Architecture**: Separate concerns and dependencies
- **SOLID Principles**: Follow object-oriented design principles
- **Dependency Injection**: Use dependency injection for testability
- **Error Handling**: Comprehensive error handling and logging

## 🧪 Testing

### Test Structure
```
tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
├── fixtures/        # Test fixtures
└── conftest.py      # Pytest configuration
```

### Writing Tests
- Write tests for all new features
- Maintain test coverage above 80%
- Use meaningful test names
- Include both positive and negative test cases

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/unit/test_ollama_service.py
```

## 📦 Pull Request Process

### Before Submitting
1. Ensure all tests pass
2. Update documentation if needed
3. Add changelog entry
4. Check code formatting

### PR Guidelines
1. **Title**: Use clear, descriptive titles
2. **Description**: Explain what and why, not just how
3. **Size**: Keep PRs focused and reasonably sized
4. **Tests**: Include tests for new functionality
5. **Documentation**: Update docs for user-facing changes

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings/errors
```

## 🐛 Issue Reporting

### Bug Reports
Use the bug report template:
- **Environment**: OS, Python version, Ollama version
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Include relevant log messages

### Feature Requests
Use the feature request template:
- **Problem**: What problem does this solve?
- **Solution**: Describe your proposed solution
- **Alternatives**: Alternative solutions considered
- **Additional context**: Any other relevant information

## 📖 Documentation

### Code Documentation
- Write clear docstrings for all public functions/classes
- Include parameter types and return types
- Provide usage examples where helpful

### API Documentation
- Document all public APIs
- Include request/response examples
- Specify error conditions and responses

### User Documentation
- Update README for new features
- Create tutorials for complex features
- Maintain troubleshooting guides

## 🏷️ Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## 📋 Changelog

Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format:
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerabilities

## 🤝 Code of Conduct

### Our Standards
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Focus on what is best for the community
- Show empathy towards other community members

### Enforcement
Project maintainers are responsible for clarifying standards and taking corrective action.

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

## 🎯 Development Focus Areas

### Current Priorities
1. **Performance Optimization**: Improve response times
2. **Error Handling**: Better error messages and recovery
3. **Testing**: Increase test coverage
4. **Documentation**: Comprehensive user guides

### Future Roadmap
1. **Plugin System**: Extensible architecture
2. **Web Interface**: Browser-based UI
3. **Multi-model Support**: Support for various AI models
4. **Cloud Integration**: Cloud deployment options

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Special recognition for major features

Thank you for contributing to make this project better! 🚀 