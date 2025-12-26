/**
 * Codex CLI Agent Adapter
 *
 * Adapter for the OpenAI Codex CLI which provides access to
 * OpenAI's code-focused models via command line.
 *
 * CLI: https://github.com/openai/codex-cli
 */

import {
  BaseAgent,
  type AgentConfig,
  type AgentResponse,
  type StreamCallback,
  type CodeBlock,
  type FileOperation,
  type ParsedCommand,
} from './base.ts';

// ============================================================================
// Codex-Specific Configuration
// ============================================================================

/**
 * Extended configuration for Codex CLI
 */
export interface CodexAgentConfig extends AgentConfig {
  /** Run in fully autonomous mode */
  fullAuto?: boolean;
  /** Approval mode: 'suggest', 'auto-edit', 'full-auto' */
  approvalMode?: 'suggest' | 'auto-edit' | 'full-auto';
  /** Model to use (e.g., 'gpt-4', 'o1', 'o3-mini') */
  model?: string;
  /** Provider: 'openai', 'azure', 'openrouter', etc. */
  provider?: string;
  /** Disable specific tools */
  disableTools?: string[];
  /** Project context directory */
  projectDir?: string;
  /** Writable paths (for sandboxing) */
  writablePaths?: string[];
  /** Read-only paths */
  readOnlyPaths?: string[];
  /** Custom instructions */
  instructions?: string;
  /** Enable quiet mode (less verbose) */
  quiet?: boolean;
  /** Config profile to use */
  profile?: string;
}

// ============================================================================
// Codex Agent Implementation
// ============================================================================

/**
 * Codex CLI Agent Adapter
 *
 * Executes prompts via the Codex CLI with full streaming support
 * and response parsing. Codex is designed for autonomous code
 * generation and execution.
 */
export class CodexAgent extends BaseAgent {
  readonly name = 'Codex';
  readonly command = 'codex';

  /** Default Codex-specific configuration */
  private readonly codexDefaults: Required<
    Omit<CodexAgentConfig, keyof AgentConfig>
  > = {
    fullAuto: true,
    approvalMode: 'full-auto',
    model: '',
    provider: '',
    disableTools: [],
    projectDir: '',
    writablePaths: [],
    readOnlyPaths: [],
    instructions: '',
    quiet: false,
    profile: '',
  };

  /**
   * Build Codex CLI arguments
   */
  protected buildArgs(
    prompt: string,
    config: Required<AgentConfig> & Partial<CodexAgentConfig>
  ): string[] {
    const args: string[] = [];

    // Full auto mode (main execution mode)
    const fullAuto = config.fullAuto ?? this.codexDefaults.fullAuto;
    const approvalMode = config.approvalMode ?? this.codexDefaults.approvalMode;

    if (fullAuto || approvalMode === 'full-auto') {
      args.push('--full-auto');
    } else if (approvalMode === 'auto-edit') {
      args.push('--auto-edit');
    }
    // 'suggest' is the default, no flag needed

    // Model selection
    const model = config.model ?? this.codexDefaults.model;
    if (model) {
      args.push('--model', model);
    }

    // Provider
    const provider = config.provider ?? this.codexDefaults.provider;
    if (provider) {
      args.push('--provider', provider);
    }

    // Disable tools
    const disableTools = config.disableTools ?? this.codexDefaults.disableTools;
    for (const tool of disableTools) {
      args.push('--disable-tool', tool);
    }

    // Project directory
    const projectDir = config.projectDir ?? this.codexDefaults.projectDir;
    if (projectDir) {
      args.push('--project-dir', projectDir);
    }

    // Writable paths
    const writablePaths =
      config.writablePaths ?? this.codexDefaults.writablePaths;
    for (const path of writablePaths) {
      args.push('--writable-path', path);
    }

    // Read-only paths
    const readOnlyPaths =
      config.readOnlyPaths ?? this.codexDefaults.readOnlyPaths;
    for (const path of readOnlyPaths) {
      args.push('--read-only-path', path);
    }

    // Custom instructions
    const instructions = config.instructions ?? this.codexDefaults.instructions;
    if (instructions) {
      args.push('--instructions', instructions);
    }

    // Quiet mode
    if (config.quiet ?? this.codexDefaults.quiet) {
      args.push('--quiet');
    }

    // Profile
    const profile = config.profile ?? this.codexDefaults.profile;
    if (profile) {
      args.push('--profile', profile);
    }

    // Extra arguments
    args.push(...config.extraArgs);

    // The prompt itself (Codex takes it as positional argument)
    args.push(prompt);

    return args;
  }

  /**
   * Execute with Codex-specific configuration
   */
  executeWithConfig(
    prompt: string,
    config?: CodexAgentConfig,
    onStream?: StreamCallback
  ) {
    return this.execute(prompt, config, onStream);
  }

  /**
   * Run with Codex-specific configuration
   */
  async runWithConfig(
    prompt: string,
    config?: CodexAgentConfig,
    onStream?: StreamCallback
  ): Promise<AgentResponse> {
    return this.executeWithConfig(prompt, config, onStream).promise;
  }

  /**
   * Parse Codex-specific response patterns
   */
  protected override parseResponse(
    rawOutput: string,
    exitCode: number | null,
    duration: number
  ): AgentResponse {
    // Get base parsing
    const baseResponse = super.parseResponse(rawOutput, exitCode, duration);

    // Codex-specific: Parse tool use events
    const toolEvents = this.extractToolEvents(rawOutput);

    // Codex-specific: Parse file diff operations
    const diffOperations = this.extractDiffOperations(rawOutput);

    // Merge file operations
    const mergedOps = this.mergeFileOperations(
      baseResponse.fileOperations,
      diffOperations
    );

    // Add executed commands from tool events
    const executedCommands = this.extractExecutedCommands(toolEvents);
    const enhancedCommands = [...baseResponse.commands, ...executedCommands];

    // Parse status/summary if present
    const summary = this.extractSummary(rawOutput);

    return {
      ...baseResponse,
      fileOperations: mergedOps,
      commands: enhancedCommands,
      textContent: summary
        ? `${baseResponse.textContent}\n\n[Summary]\n${summary}`
        : baseResponse.textContent,
    };
  }

  /**
   * Extract tool use events from Codex output
   */
  private extractToolEvents(
    output: string
  ): Array<{ tool: string; input: unknown; output?: string }> {
    const events: Array<{ tool: string; input: unknown; output?: string }> = [];

    // Match Codex tool event patterns
    // Format: [tool:name] input -> output
    const toolRegex =
      /\[tool:(\w+)\]\s*([\s\S]*?)(?=\[tool:|\[result\]|$)/g;

    let match: RegExpExecArray | null;
    while ((match = toolRegex.exec(output)) !== null) {
      const tool = match[1] ?? '';
      const content = match[2]?.trim() ?? '';

      // Try to parse as JSON, otherwise keep as string
      let input: unknown;
      try {
        input = JSON.parse(content);
      } catch {
        input = content;
      }

      events.push({ tool, input });
    }

    // Also match JSON-formatted tool calls
    const jsonToolRegex =
      /\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"input"\s*:\s*([\s\S]*?)\}/g;

    while ((match = jsonToolRegex.exec(output)) !== null) {
      const tool = match[1] ?? '';
      let input: unknown;
      try {
        input = JSON.parse(match[2] ?? '{}');
      } catch {
        input = match[2];
      }

      events.push({ tool, input });
    }

    return events;
  }

  /**
   * Extract file diff operations from Codex output
   */
  private extractDiffOperations(output: string): FileOperation[] {
    const operations: FileOperation[] = [];

    // Match unified diff format
    const diffRegex =
      /^diff\s+--git\s+a\/([^\s]+)\s+b\/([^\s]+)[\s\S]*?(?=^diff\s+--git|$)/gm;

    let match: RegExpExecArray | null;
    while ((match = diffRegex.exec(output)) !== null) {
      const filePath = match[2] ?? match[1] ?? '';

      // Determine operation type from diff content
      const diffContent = match[0];
      let operation: FileOperation['operation'] = 'modify';

      if (diffContent.includes('new file mode')) {
        operation = 'create';
      } else if (diffContent.includes('deleted file mode')) {
        operation = 'delete';
      }

      // Extract new content for create/modify
      let content: string | undefined;
      if (operation !== 'delete') {
        const addedLines: string[] = [];
        const lines = diffContent.split('\n');
        for (const line of lines) {
          if (line.startsWith('+') && !line.startsWith('+++')) {
            addedLines.push(line.slice(1));
          }
        }
        content = addedLines.join('\n');
      }

      operations.push({
        operation,
        path: filePath,
        content,
        language: this.inferLanguageFromPath(filePath),
      });
    }

    // Also match Codex's file write events
    const writeRegex =
      /(?:Writing|Created|Updated)\s+(?:file\s+)?[`'"]?([^`'":\n]+\.\w+)[`'"]?/gi;

    while ((match = writeRegex.exec(output)) !== null) {
      const path = match[1]?.trim();
      if (path && !operations.some((op) => op.path === path)) {
        operations.push({
          operation: 'create',
          path,
          language: this.inferLanguageFromPath(path),
        });
      }
    }

    return operations;
  }

  /**
   * Extract executed commands from tool events
   */
  private extractExecutedCommands(
    toolEvents: Array<{ tool: string; input: unknown; output?: string }>
  ): ParsedCommand[] {
    const commands: ParsedCommand[] = [];

    for (const event of toolEvents) {
      // Shell/bash/exec tool events
      if (['shell', 'bash', 'exec', 'run', 'command'].includes(event.tool)) {
        let command: string;

        if (typeof event.input === 'string') {
          command = event.input;
        } else if (
          typeof event.input === 'object' &&
          event.input !== null &&
          'command' in event.input
        ) {
          command = String((event.input as { command: unknown }).command);
        } else {
          continue;
        }

        commands.push({
          command,
          description: `Executed by Codex ${event.tool} tool`,
          isShell: true,
        });
      }
    }

    return commands;
  }

  /**
   * Extract summary from Codex output
   */
  private extractSummary(output: string): string | null {
    // Match summary section
    const summaryPatterns = [
      /(?:^|\n)## Summary\n([\s\S]*?)(?=\n##|$)/i,
      /(?:^|\n)Summary:\s*([\s\S]*?)(?=\n\n|$)/i,
      /\[summary\]\s*([\s\S]*?)(?=\[\/summary\]|$)/i,
    ];

    for (const pattern of summaryPatterns) {
      const match = pattern.exec(output);
      if (match?.[1]) {
        return match[1].trim();
      }
    }

    return null;
  }

  /**
   * Infer programming language from file path
   */
  private inferLanguageFromPath(filePath: string): string {
    const ext = filePath.split('.').pop()?.toLowerCase() ?? '';
    const extensionMap: Record<string, string> = {
      ts: 'typescript',
      tsx: 'typescript',
      js: 'javascript',
      jsx: 'javascript',
      mjs: 'javascript',
      cjs: 'javascript',
      py: 'python',
      rb: 'ruby',
      go: 'go',
      rs: 'rust',
      java: 'java',
      kt: 'kotlin',
      kts: 'kotlin',
      c: 'c',
      h: 'c',
      cpp: 'cpp',
      cc: 'cpp',
      cxx: 'cpp',
      hpp: 'cpp',
      cs: 'csharp',
      php: 'php',
      swift: 'swift',
      scala: 'scala',
      r: 'r',
      sql: 'sql',
      sh: 'bash',
      bash: 'bash',
      zsh: 'bash',
      ps1: 'powershell',
      html: 'html',
      htm: 'html',
      css: 'css',
      scss: 'scss',
      sass: 'sass',
      less: 'less',
      json: 'json',
      yaml: 'yaml',
      yml: 'yaml',
      xml: 'xml',
      md: 'markdown',
      mdx: 'markdown',
      toml: 'toml',
      ini: 'ini',
      cfg: 'ini',
      dockerfile: 'dockerfile',
      makefile: 'makefile',
      cmake: 'cmake',
    };

    return extensionMap[ext] ?? 'text';
  }

  /**
   * Merge file operations, avoiding duplicates
   */
  private mergeFileOperations(
    existing: FileOperation[],
    additional: FileOperation[]
  ): FileOperation[] {
    const merged = [...existing];
    const existingPaths = new Set(existing.map((op) => op.path));

    for (const op of additional) {
      if (!existingPaths.has(op.path)) {
        merged.push(op);
        existingPaths.add(op.path);
      } else {
        // Update existing operation if new one has more info
        const existingOp = merged.find((e) => e.path === op.path);
        if (existingOp && !existingOp.content && op.content) {
          existingOp.content = op.content;
        }
      }
    }

    return merged;
  }

  /**
   * Override code block extraction to handle Codex-specific patterns
   */
  protected override extractCodeBlocks(output: string): CodeBlock[] {
    const blocks = super.extractCodeBlocks(output);

    // Codex sometimes outputs with ANSI colors stripped but uses >>> markers
    const replOutputRegex = /^>>>\s*([\s\S]*?)(?=^>>>|\n\n|$)/gm;

    let match: RegExpExecArray | null;
    while ((match = replOutputRegex.exec(output)) !== null) {
      const content = match[1]?.trim();
      if (content && content.length > 10) {
        const isDuplicate = blocks.some(
          (b) =>
            b.content.includes(content) || content.includes(b.content)
        );

        if (!isDuplicate) {
          blocks.push({
            language: 'python', // >>> is typically Python REPL
            content,
            startIndex: match.index,
            endIndex: match.index + match[0].length,
          });
        }
      }
    }

    return blocks;
  }

  /**
   * Override command extraction to handle Codex's execution format
   */
  protected override extractCommands(output: string): ParsedCommand[] {
    const commands = super.extractCommands(output);

    // Codex often shows commands with $ prefix in execution logs
    const execLogRegex = /^\$\s+(.+)$/gm;

    let match: RegExpExecArray | null;
    while ((match = execLogRegex.exec(output)) !== null) {
      const command = match[1]?.trim();
      if (command && !commands.some((c) => c.command === command)) {
        commands.push({
          command,
          description: 'Executed command',
          isShell: true,
        });
      }
    }

    return commands;
  }
}

/**
 * Default Codex agent instance
 */
export const codex = new CodexAgent();
