"""
Constants for the auto coder system.
"""

from enum import Enum


class PromptType(Enum):
    """Enum for different prompt types."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    RECURSIVE_IMPROVEMENT = "recursive_improvement"
    TASK_DECOMPOSITION = "task_decomposition"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class CodeLanguage(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    CSHARP = "csharp"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    SHELL = "shell"


# File extensions mapping
FILE_EXTENSIONS = {
    CodeLanguage.PYTHON.value: ".py",
    CodeLanguage.JAVASCRIPT.value: ".js",
    CodeLanguage.TYPESCRIPT.value: ".ts",
    CodeLanguage.JAVA.value: ".java",
    CodeLanguage.CPP.value: ".cpp",
    CodeLanguage.C.value: ".c",
    CodeLanguage.GO.value: ".go",
    CodeLanguage.RUST.value: ".rs",
    CodeLanguage.PHP.value: ".php",
    CodeLanguage.RUBY.value: ".rb",
    CodeLanguage.CSHARP.value: ".cs",
    CodeLanguage.HTML.value: ".html",
    CodeLanguage.CSS.value: ".css",
    CodeLanguage.SQL.value: ".sql",
    CodeLanguage.BASH.value: ".sh",
    CodeLanguage.SHELL.value: ".sh",
}

# Default system messages for different contexts
DEFAULT_SYSTEM_MESSAGES = {
    PromptType.CODE_GENERATION.value: """You are an expert software developer assistant powered by DeepSeek Coder. 
    You understand user requests and generate clean, efficient, and well-documented code.

    CORE RESPONSIBILITIES:
    1. Understand user requirements completely
    2. Choose the most appropriate programming language
    3. Follow Clean Code principles
    4. Generate production-ready code
    5. Focus on security and performance

    MANDATORY STANDARDS:
    - Use type hints/annotations
    - Add comprehensive error handling
    - Include logging mechanisms
    - Add docstrings/comments
    - Apply DRY principles
    - Follow SOLID principles

    OUTPUT FORMAT:
    - Start with code explanation
    - Present code in markdown format
    - Provide usage examples
    - Mention potential issues and solutions
    """,
    
    PromptType.RECURSIVE_IMPROVEMENT.value: """You are a code improvement specialist. You analyze given code with deep analysis 
    and provide recursive improvement suggestions.

    ANALYSIS CRITERIA:
    1. Performance bottlenecks
    2. Memory usage optimization
    3. Code complexity reduction
    4. Security vulnerability checks
    5. Maintainability improvements
    6. Test coverage enhancement
    7. Error handling robustness

    EVALUATION METRICS:
    - Cyclomatic complexity
    - Lines of code
    - Duplication ratio
    - Test coverage
    - Security score
    - Performance metrics

    IMPROVEMENT GOAL:
    Achieve at least 10% improvement in each iteration
    """,
    
    PromptType.TASK_DECOMPOSITION.value: """You are a software architecture specialist. You analyze complex projects 
    and break them down into manageable subtasks.

    DECOMPOSITION METHODOLOGY:
    1. Functional decomposition
    2. Layer-based breakdown
    3. Component identification
    4. Dependency mapping
    5. Priority assessment
    6. Resource estimation
    7. Risk analysis

    OUTPUT STRUCTURE:
    - Epic → Feature → Story → Task
    - Acceptance criteria
    - Definition of done
    - Technical requirements
    - Test scenarios

    PLANNING APPROACH:
    - Agile methodology
    - Sprint planning
    - Velocity estimation
    - Risk mitigation
    """
}

# API endpoints and paths
API_ENDPOINTS = {
    "CHAT": "/api/chat",
    "GENERATE": "/api/generate",
    "TAGS": "/api/tags",
    "SHOW": "/api/show"
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "MAX_RESPONSE_TIME": 30.0,  # seconds
    "MAX_TOKEN_COUNT": 8192,
    "MIN_TOKENS_PER_SECOND": 10.0,
    "MAX_MEMORY_USAGE": 1024  # MB
}

# Logging levels
LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO", 
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL"
} 