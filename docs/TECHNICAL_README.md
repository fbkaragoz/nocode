# Technical README

This document provides a technical overview of the Auto-Coder project, detailing its architecture, setup, and usage. It is intended for developers who wish to understand, contribute to, or extend the project.

## Architecture

The system is designed with a clean, single-responsibility architecture to ensure stability and maintainability.

- **`run.py`**: The main entry point. It initializes the `CLIManager` and starts the application.

- **`src/`**: Contains all core logic and services.
    - **`core/`**: The heart of the application.
        - **`cli/`**: Manages the command-line interface.
            - `cli_manager.py`: Handles the main user interaction loop, displays content, and orchestrates the command flow.
            - `command_processor.py`: Acts as a bridge between the CLI and the engine. It translates user input into specific actions for the engine.
        - `auto_coder.py`: This is the **Engine** or "brain". It is solely responsible for:
            - Interacting with the AI model.
            - Formatting prompts using templates from `.secrets/`.
            - Parsing the model's response.
            - All file I/O operations: saving new files, updating existing ones, and creating backups.
    - **`services/`**: Provides external service integrations.
        - `ollama_service.py`: Handles all API communication with the local Ollama instance.
    - **`config/`**: Contains application settings.
        - `settings.py`: A simple class that holds configuration values like model name and API endpoints.

- **`.secrets/`**: A secure directory (and gitignored) for sensitive information.
    - `prompts.yaml`: Defines the structured instruction templates that guide the AI model's behavior for different tasks (e.g., code creation vs. code editing).

- **`generated_code/`**: The default output directory where all generated and edited code is saved.

## Setup & Installation

1.  **Prerequisites**:
    - Python 3.9+
    - An installed and running instance of [Ollama](https://ollama.ai/).
    - A downloaded Ollama model suitable for coding (e.g., `deepseek-coder:6.7b` or `huihui_ai/deepseek-r1-Fusion:32b-coder-9010`).

2.  **Installation**:
    ```bash
    # Clone the repository
    git clone <repository_url>
    cd <repository_name>

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    - Open `src/config/settings.py`.
    - Find the `model_name` variable inside the `_get_default_config` method.
    - Change its value to match the name of the model you have downloaded in Ollama.

## How It Works

1.  The `CLIManager` captures the user's plain-text prompt.
2.  It passes the prompt to the `CommandProcessor`.
3.  The `CommandProcessor` asks the `AutoCoderEngine` to generate a stream for the prompt.
4.  The `AutoCoderEngine` determines if the request is for a new file or an edit. It finds the correct prompt template from `prompts.yaml` and populates it with context (like existing file content for an edit).
5.  The formatted prompt is sent to the `OllamaService`, which streams the response from the local LLM.
6.  The `CLIManager` receives the raw stream and displays it in real-time.
7.  Once the stream is complete, the `CLIManager` passes the full response text back to the `CommandProcessor`.
8.  The `CommandProcessor` asks the `AutoCoderEngine` to save the response.
9.  The `AutoCoderEngine` parses the response, extracts the code block, and saves or updates the appropriate file in `generated_code/`, creating a `.backup` if it's an update. 