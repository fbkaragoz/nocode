"""
Constants for the auto coder system.
"""

from enum import Enum


class PromptType(Enum):
    """Enum for different prompt types."""
    CODE_GENERATION = "code_generation"
    GENERATE = "generate"
    IMPROVE = "improve"
    BREAKDOWN = "breakdown"
    EXPLAIN = "explain"
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

# Default system messages for fallback (when config files are not available)
DEFAULT_SYSTEM_MESSAGES = {
    # IP-protected prompts now loaded from secure sources
    # No hardcoded prompts allowed in this file
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
    # Dynamic token configuration - removed hardcoded values
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