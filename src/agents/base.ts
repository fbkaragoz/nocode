/**
 * Base Agent Interface and Abstract Class
 *
 * Provides the foundation for all CLI agent adapters including:
 * - TypeScript interfaces for configuration and responses
 * - Abstract base class with common functionality
 * - Streaming output support via Bun.spawn
 * - Response parsing utilities for code blocks, files, and commands
 */

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Configuration for agent execution
 */
export interface AgentConfig {
  /** Maximum execution time in milliseconds (default: 300000 = 5 minutes) */
  timeout?: number;
  /** Working directory for command execution */
  cwd?: string;
  /** Environment variables to pass to the subprocess */
  env?: Record<string, string>;
  /** Maximum output buffer size in bytes (default: 10MB) */
  maxOutputSize?: number;
  /** Enable verbose logging for debugging */
  verbose?: boolean;
  /** Custom arguments to append to the CLI command */
  extraArgs?: string[];
}

/**
 * Parsed code block from agent response
 */
export interface CodeBlock {
  /** Programming language identifier (e.g., 'typescript', 'python') */
  language: string;
  /** The actual code content */
  content: string;
  /** Optional filename if specified in the code fence */
  filename?: string;
  /** Start position in the original response */
  startIndex: number;
  /** End position in the original response */
  endIndex: number;
}

/**
 * Parsed file operation from agent response
 */
export interface FileOperation {
  /** Type of operation */
  operation: 'create' | 'modify' | 'delete' | 'read';
  /** File path (relative or absolute) */
  path: string;
  /** File content for create/modify operations */
  content?: string;
  /** Programming language if detectable */
  language?: string;
}

/**
 * Parsed command from agent response
 */
export interface ParsedCommand {
  /** The command to execute */
  command: string;
  /** Description or context for the command */
  description?: string;
  /** Whether this is a shell command */
  isShell: boolean;
}

/**
 * Structured response from an agent
 */
export interface AgentResponse {
  /** Whether the execution was successful */
  success: boolean;
  /** Raw output from the agent */
  rawOutput: string;
  /** Parsed code blocks from the response */
  codeBlocks: CodeBlock[];
  /** Parsed file operations from the response */
  fileOperations: FileOperation[];
  /** Parsed commands from the response */
  commands: ParsedCommand[];
  /** Text content with code blocks removed */
  textContent: string;
  /** Error message if execution failed */
  error?: string;
  /** Exit code from the subprocess */
  exitCode: number | null;
  /** Execution duration in milliseconds */
  duration: number;
  /** Whether the execution was cancelled */
  cancelled: boolean;
  /** Whether the execution timed out */
  timedOut: boolean;
}

/**
 * Callback for streaming output
 */
export type StreamCallback = (chunk: string, type: 'stdout' | 'stderr') => void;

/**
 * Agent execution handle for cancellation support
 */
export interface AgentHandle {
  /** Promise that resolves with the agent response */
  promise: Promise<AgentResponse>;
  /** Cancel the ongoing execution */
  cancel: () => void;
  /** Whether the execution is still running */
  isRunning: () => boolean;
}

// ============================================================================
// Abstract Base Class
// ============================================================================

/**
 * Abstract base class for CLI agent adapters
 *
 * Provides common functionality for executing CLI commands,
 * streaming output, and parsing responses.
 */
export abstract class BaseAgent {
  /** Human-readable name of the agent */
  abstract readonly name: string;

  /** CLI command/binary name */
  abstract readonly command: string;

  /** Default configuration */
  protected readonly defaultConfig: Required<AgentConfig> = {
    timeout: 300000, // 5 minutes
    cwd: process.cwd(),
    env: {},
    maxOutputSize: 10 * 1024 * 1024, // 10MB
    verbose: false,
    extraArgs: [],
  };

  /** Active subprocess reference for cancellation */
  protected activeProcess: ReturnType<typeof Bun.spawn> | null = null;

  /** Flag indicating if current execution is cancelled */
  protected isCancelled = false;

  /**
   * Build the CLI arguments for this agent
   * @param prompt The user prompt to send to the agent
   * @param config Agent configuration
   * @returns Array of command line arguments
   */
  protected abstract buildArgs(prompt: string, config: Required<AgentConfig>): string[];

  /**
   * Check if the CLI tool is available
   * @returns Promise resolving to true if available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const proc = Bun.spawn(['which', this.command], {
        stdout: 'pipe',
        stderr: 'pipe',
      });
      const exitCode = await proc.exited;
      return exitCode === 0;
    } catch {
      return false;
    }
  }

  /**
   * Get the version of the CLI tool
   * @returns Promise resolving to version string or null
   */
  async getVersion(): Promise<string | null> {
    try {
      const proc = Bun.spawn([this.command, '--version'], {
        stdout: 'pipe',
        stderr: 'pipe',
      });
      const output = await new Response(proc.stdout).text();
      const exitCode = await proc.exited;
      if (exitCode === 0) {
        return output.trim().split('\n')[0] ?? null;
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Execute the agent with a prompt
   * @param prompt The user prompt
   * @param config Optional configuration overrides
   * @param onStream Optional callback for streaming output
   * @returns AgentHandle for the execution
   */
  execute(
    prompt: string,
    config?: AgentConfig,
    onStream?: StreamCallback
  ): AgentHandle {
    const mergedConfig = this.mergeConfig(config);
    this.isCancelled = false;

    let isRunning = true;

    const promise = this.runProcess(prompt, mergedConfig, onStream)
      .finally(() => {
        isRunning = false;
        this.activeProcess = null;
      });

    return {
      promise,
      cancel: () => this.cancel(),
      isRunning: () => isRunning,
    };
  }

  /**
   * Execute and wait for the result (convenience method)
   * @param prompt The user prompt
   * @param config Optional configuration overrides
   * @param onStream Optional callback for streaming output
   * @returns Promise resolving to AgentResponse
   */
  async run(
    prompt: string,
    config?: AgentConfig,
    onStream?: StreamCallback
  ): Promise<AgentResponse> {
    return this.execute(prompt, config, onStream).promise;
  }

  /**
   * Cancel the current execution
   */
  cancel(): void {
    this.isCancelled = true;
    if (this.activeProcess) {
      try {
        this.activeProcess.kill();
      } catch {
        // Process may have already exited
      }
    }
  }

  /**
   * Merge user config with defaults
   */
  protected mergeConfig(config?: AgentConfig): Required<AgentConfig> {
    return {
      ...this.defaultConfig,
      ...config,
      env: {
        ...this.defaultConfig.env,
        ...config?.env,
      },
      extraArgs: [
        ...this.defaultConfig.extraArgs,
        ...(config?.extraArgs ?? []),
      ],
    };
  }

  /**
   * Run the subprocess and collect output
   */
  protected async runProcess(
    prompt: string,
    config: Required<AgentConfig>,
    onStream?: StreamCallback
  ): Promise<AgentResponse> {
    const startTime = Date.now();
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    let exitCode: number | null = null;

    const args = this.buildArgs(prompt, config);

    if (config.verbose) {
      console.log(`[${this.name}] Executing: ${this.command} ${args.join(' ')}`);
    }

    try {
      this.activeProcess = Bun.spawn([this.command, ...args], {
        cwd: config.cwd,
        env: {
          ...process.env,
          ...config.env,
        },
        stdout: 'pipe',
        stderr: 'pipe',
      });

      // Set up timeout
      const timeoutPromise = new Promise<'timeout'>((resolve) => {
        setTimeout(() => resolve('timeout'), config.timeout);
      });

      // Stream stdout
      const stdoutPromise = this.activeProcess.stdout
        ? this.streamOutput(
            this.activeProcess.stdout as ReadableStream<Uint8Array>,
            config.maxOutputSize,
            (chunk) => {
              stdout += chunk;
              onStream?.(chunk, 'stdout');
            }
          )
        : Promise.resolve();

      // Stream stderr
      const stderrPromise = this.activeProcess.stderr
        ? this.streamOutput(
            this.activeProcess.stderr as ReadableStream<Uint8Array>,
            config.maxOutputSize,
            (chunk) => {
              stderr += chunk;
              onStream?.(chunk, 'stderr');
            }
          )
        : Promise.resolve();

      // Wait for completion or timeout
      const exitedPromise = this.activeProcess.exited;

      const result = await Promise.race([
        Promise.all([stdoutPromise, stderrPromise, exitedPromise]).then(
          ([, , code]) => ({ type: 'completed' as const, code })
        ),
        timeoutPromise.then(() => ({ type: 'timeout' as const })),
      ]);

      if (result.type === 'timeout') {
        timedOut = true;
        this.cancel();
        // Wait a bit for cleanup
        await Promise.race([
          this.activeProcess.exited,
          new Promise((resolve) => setTimeout(resolve, 1000)),
        ]);
      } else {
        exitCode = result.code;
      }

    } catch (error) {
      const duration = Date.now() - startTime;
      return this.createErrorResponse(
        error instanceof Error ? error.message : String(error),
        stdout,
        duration
      );
    }

    const duration = Date.now() - startTime;
    const combinedOutput = stdout + (stderr ? `\n[stderr]\n${stderr}` : '');

    if (this.isCancelled) {
      return this.createCancelledResponse(combinedOutput, duration);
    }

    if (timedOut) {
      return this.createTimeoutResponse(combinedOutput, duration, config.timeout);
    }

    return this.parseResponse(combinedOutput, exitCode, duration);
  }

  /**
   * Stream output from a readable stream
   */
  protected async streamOutput(
    stream: ReadableStream<Uint8Array>,
    maxSize: number,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const decoder = new TextDecoder();
    let totalSize = 0;

    try {
      for await (const chunk of stream) {
        if (this.isCancelled) break;

        const text = decoder.decode(chunk, { stream: true });
        totalSize += chunk.length;

        if (totalSize <= maxSize) {
          onChunk(text);
        } else if (totalSize - chunk.length < maxSize) {
          // Partial last chunk
          const remaining = maxSize - (totalSize - chunk.length);
          onChunk(text.slice(0, remaining) + '\n[Output truncated]');
        }
      }
    } catch {
      // Stream closed or error
    }
  }

  /**
   * Parse the agent response
   */
  protected parseResponse(
    rawOutput: string,
    exitCode: number | null,
    duration: number
  ): AgentResponse {
    const codeBlocks = this.extractCodeBlocks(rawOutput);
    const fileOperations = this.extractFileOperations(rawOutput, codeBlocks);
    const commands = this.extractCommands(rawOutput);
    const textContent = this.extractTextContent(rawOutput, codeBlocks);

    return {
      success: exitCode === 0,
      rawOutput,
      codeBlocks,
      fileOperations,
      commands,
      textContent,
      error: exitCode !== 0 ? `Process exited with code ${exitCode}` : undefined,
      exitCode,
      duration,
      cancelled: false,
      timedOut: false,
    };
  }

  /**
   * Extract code blocks from markdown-style response
   */
  protected extractCodeBlocks(output: string): CodeBlock[] {
    const blocks: CodeBlock[] = [];
    // Match ```language or ```language:filename
    const codeBlockRegex = /```(\w+)?(?::([^\n]+))?\n([\s\S]*?)```/g;

    let match: RegExpExecArray | null;
    while ((match = codeBlockRegex.exec(output)) !== null) {
      blocks.push({
        language: match[1] ?? 'text',
        filename: match[2]?.trim(),
        content: match[3]?.trim() ?? '',
        startIndex: match.index,
        endIndex: match.index + match[0].length,
      });
    }

    return blocks;
  }

  /**
   * Extract file operations from the response
   */
  protected extractFileOperations(
    output: string,
    codeBlocks: CodeBlock[]
  ): FileOperation[] {
    const operations: FileOperation[] = [];

    // Look for file creation patterns
    const filePatterns = [
      // "Create file: path/to/file.ts" followed by code block
      /(?:create|write|save)\s+(?:file[:\s]+)?([^\n]+\.[\w]+)/gi,
      // "File: path/to/file.ts"
      /^file:\s*([^\n]+\.[\w]+)/gim,
      // Code blocks with filename in fence
    ];

    for (const block of codeBlocks) {
      if (block.filename) {
        operations.push({
          operation: 'create',
          path: block.filename,
          content: block.content,
          language: block.language,
        });
      }
    }

    // Look for explicit file operations in text
    for (const pattern of filePatterns) {
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(output)) !== null) {
        const path = match[1]?.trim();
        if (path && !operations.some((op) => op.path === path)) {
          // Try to find associated code block
          const blockAfter = codeBlocks.find(
            (b) => b.startIndex > match!.index && b.startIndex < match!.index + 500
          );
          operations.push({
            operation: 'create',
            path,
            content: blockAfter?.content,
            language: blockAfter?.language,
          });
        }
      }
    }

    // Look for delete operations
    const deletePattern = /(?:delete|remove)\s+(?:file[:\s]+)?([^\n]+\.[\w]+)/gi;
    let deleteMatch: RegExpExecArray | null;
    while ((deleteMatch = deletePattern.exec(output)) !== null) {
      const path = deleteMatch[1]?.trim();
      if (path) {
        operations.push({
          operation: 'delete',
          path,
        });
      }
    }

    return operations;
  }

  /**
   * Extract shell commands from the response
   */
  protected extractCommands(output: string): ParsedCommand[] {
    const commands: ParsedCommand[] = [];

    // Match shell/bash code blocks
    const shellBlockRegex = /```(?:bash|sh|shell|zsh)\n([\s\S]*?)```/g;
    let match: RegExpExecArray | null;

    while ((match = shellBlockRegex.exec(output)) !== null) {
      const content = match[1]?.trim() ?? '';
      const lines = content.split('\n').filter((line) => {
        const trimmed = line.trim();
        return trimmed && !trimmed.startsWith('#');
      });

      for (const line of lines) {
        // Remove leading $ or > prompt
        const command = line.replace(/^[$>]\s*/, '').trim();
        if (command) {
          commands.push({
            command,
            isShell: true,
          });
        }
      }
    }

    // Look for inline commands with "Run:" or "Execute:" prefix
    const inlinePattern = /(?:run|execute|command)[:\s]+`([^`]+)`/gi;
    while ((match = inlinePattern.exec(output)) !== null) {
      const command = match[1]?.trim();
      if (command) {
        commands.push({
          command,
          isShell: true,
        });
      }
    }

    return commands;
  }

  /**
   * Extract plain text content (without code blocks)
   */
  protected extractTextContent(output: string, codeBlocks: CodeBlock[]): string {
    let text = output;

    // Remove code blocks (in reverse order to preserve indices)
    for (let i = codeBlocks.length - 1; i >= 0; i--) {
      const block = codeBlocks[i];
      if (block) {
        text = text.slice(0, block.startIndex) + text.slice(block.endIndex);
      }
    }

    // Clean up extra whitespace
    return text.replace(/\n{3,}/g, '\n\n').trim();
  }

  /**
   * Create an error response
   */
  protected createErrorResponse(
    error: string,
    partialOutput: string,
    duration: number
  ): AgentResponse {
    return {
      success: false,
      rawOutput: partialOutput,
      codeBlocks: [],
      fileOperations: [],
      commands: [],
      textContent: partialOutput,
      error,
      exitCode: null,
      duration,
      cancelled: false,
      timedOut: false,
    };
  }

  /**
   * Create a cancelled response
   */
  protected createCancelledResponse(
    partialOutput: string,
    duration: number
  ): AgentResponse {
    return {
      success: false,
      rawOutput: partialOutput,
      codeBlocks: this.extractCodeBlocks(partialOutput),
      fileOperations: [],
      commands: [],
      textContent: this.extractTextContent(partialOutput, []),
      error: 'Execution was cancelled',
      exitCode: null,
      duration,
      cancelled: true,
      timedOut: false,
    };
  }

  /**
   * Create a timeout response
   */
  protected createTimeoutResponse(
    partialOutput: string,
    duration: number,
    timeout: number
  ): AgentResponse {
    return {
      success: false,
      rawOutput: partialOutput,
      codeBlocks: this.extractCodeBlocks(partialOutput),
      fileOperations: [],
      commands: [],
      textContent: this.extractTextContent(partialOutput, []),
      error: `Execution timed out after ${timeout}ms`,
      exitCode: null,
      duration,
      cancelled: false,
      timedOut: true,
    };
  }
}
