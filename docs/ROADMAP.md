# Project Roadmap

This document outlines the strategic vision and planned features for the Auto-Coder project. Our goal is to evolve from a simple code generation tool into a more autonomous and intelligent software development agent.

## Phase 1: Stable Foundation (✅ Complete)

The focus of this phase was to build a reliable, stable, and understandable core system.

- [x] **Stable File I/O**: Correctly save and update files in a predictable `generated_code/` directory.
- [x] **Contextual Awareness**: Implement logic to read existing files for edit requests.
- [x] **Robust Prompting**: Use structured YAML templates for guiding the AI.
- [x] **Strict Parsing**: Prevent saving of non-code "thought process" responses.
- [x] **Clean Architecture**: Refactor the codebase to follow the Single Responsibility Principle.
- [x] **Accurate Documentation**: Update all user-facing documentation to reflect the current, working state of the project.

## Phase 2: Hierarchical Agent Architecture (Next Up)

This phase introduces a "separation of cognitive labor" by using two different AI models for different tasks, addressing the "single-pass error" problem where the model forgets or misses details.

- **`Architect Agent`**:
    - **Responsibility**: Planning, analysis, and task decomposition.
    - **Model**: A model with strong reasoning and language skills (e.g., `wizard-vicuna`, `Llama-3-Instruct`).
    - **Function**:
        1.  Receives the user's high-level request (e.g., "fix this bug," "add this feature").
        2.  Analyzes the existing code.
        3.  Creates a structured, step-by-step plan.
        4.  Generates a highly specific, low-level prompt for the Coder Agent.

- **`Coder Agent`**:
    - **Responsibility**: Pure code generation.
    - **Model**: A model highly optimized for code (e.g., `deepseek-coder`, `CodeLlama`).
    - **Function**:
        1.  Receives a very specific instruction from the Architect (e.g., "In file `x.py`, add the `global game_over` declaration on line 75.").
        2.  Executes this small, focused task.
        3.  Returns the complete, updated code.

## Phase 3: Autonomous Testing & Self-Correction

This is the key to true autonomy. The system will be able to validate its own work and correct its own mistakes.

- **`Tester Agent` / Command-Line Tools**:
    - **Responsibility**: Code execution and validation.
    - **Function**:
        1.  After the `Coder Agent` produces code, the system will attempt to run it using a `subprocess` (e.g., `python generated_code/script.py`).
        2.  It will capture `stdout` and `stderr`.
- **Feedback Loop**:
    - If the execution is successful (`stderr` is empty), the task is marked as complete.
    - If there is a `Traceback` in `stderr`, the error message is captured.
    - The captured error is passed back to the **`Architect Agent`** as a new problem to solve.
    - The loop continues until the code runs without errors or a maximum number of attempts is reached.

## Phase 4: Advanced Capabilities

- **Multi-File Project Awareness**: Extend the context management to handle entire project structures, not just single files.
- **Interactive Tool Use**: Allow the agent to use other command-line tools, like `git` for version control or `pip` for installing dependencies.
- **Long-Term Memory**: Implement a vector database (e.g., ChromaDB) to give the agent a persistent memory of past interactions and learned solutions. 