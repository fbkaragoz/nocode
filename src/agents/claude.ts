/**
 * Claude CLI Agent Adapter
 *
 * Adapter for the Claude CLI (claude) which provides access to
 * Anthropic's Claude models via command line.
 *
 * CLI: https://github.com/anthropics/claude-cli
 */

import {
  BaseAgent,
  type AgentConfig,
  type AgentResponse,
  type StreamCallback,
  type CodeBlock,
  type FileOperation,
} from './base.ts';

// ============================================================================
// Claude-Specific Configuration
// ============================================================================

/**
 * Extended configuration for Claude CLI
 */
export interface ClaudeAgentConfig extends AgentConfig {
  /** Skip permission prompts (use with caution) */
  skipPermissions?: boolean;
  /** Use print mode for non-interactive output */
  printMode?: boolean;
  /** Model to use (e.g., 'claude-3-opus', 'claude-3-sonnet') */
  model?: string;
  /** System prompt to use */
  systemPrompt?: string;
  /** Maximum tokens for response */
  maxTokens?: number;
  /** Temperature for sampling (0-1) */
  temperature?: number;
  /** Output format: 'text', 'json', or 'stream-json' */
  outputFormat?: 'text' | 'json' | 'stream-json';
  /** Allowed tools/capabilities */
  allowedTools?: string[];
  /** Files to include as context */
  contextFiles?: string[];
}

// ============================================================================
// Claude Agent Implementation
// ============================================================================

/**
 * Claude CLI Agent Adapter
 *
 * Executes prompts via the Claude CLI with full streaming support
 * and response parsing.
 */
export class ClaudeAgent extends BaseAgent {
  readonly name = 'Claude';
  readonly command = 'claude';

  /** Default Claude-specific configuration */
  private readonly claudeDefaults: Required<
    Omit<ClaudeAgentConfig, keyof AgentConfig>
  > = {
    skipPermissions: true,
    printMode: true,
    model: '',
    systemPrompt: '',
    maxTokens: 0,
    temperature: -1,
    outputFormat: 'text',
    allowedTools: [],
    contextFiles: [],
  };

  /**
   * Build Claude CLI arguments
   *
   * Valid Claude CLI options:
   * --print, -p            Print output without interactive mode
   * --dangerously-skip-permissions  Skip permission prompts
   * --model                Model to use
   * --output-format        Output format (text, json, stream-json)
   * [prompt]               Positional prompt argument
   */
  protected buildArgs(
    prompt: string,
    config: Required<AgentConfig> & Partial<ClaudeAgentConfig>
  ): string[] {
    const args: string[] = [];

    // Print mode for non-interactive output
    if (config.printMode ?? this.claudeDefaults.printMode) {
      args.push('--print');
    }

    // Skip permissions (dangerous but needed for automation)
    if (config.skipPermissions ?? this.claudeDefaults.skipPermissions) {
      args.push('--dangerously-skip-permissions');
    }

    // Model selection
    const model = config.model ?? this.claudeDefaults.model;
    if (model) {
      args.push('--model', model);
    }

    // Output format
    const outputFormat = config.outputFormat ?? this.claudeDefaults.outputFormat;
    if (outputFormat !== 'text') {
      args.push('--output-format', outputFormat);
    }

    // Extra arguments from config
    args.push(...config.extraArgs);

    // The prompt itself as positional argument (must be last)
    args.push(prompt);

    return args;
  }

  /**
   * Execute with Claude-specific configuration
   */
  executeWithConfig(
    prompt: string,
    config?: ClaudeAgentConfig,
    onStream?: StreamCallback
  ) {
    return this.execute(prompt, config, onStream);
  }

  /**
   * Run with Claude-specific configuration
   */
  async runWithConfig(
    prompt: string,
    config?: ClaudeAgentConfig,
    onStream?: StreamCallback
  ): Promise<AgentResponse> {
    return this.executeWithConfig(prompt, config, onStream).promise;
  }

  /**
   * Parse Claude-specific response patterns
   */
  protected override parseResponse(
    rawOutput: string,
    exitCode: number | null,
    duration: number
  ): AgentResponse {
    // Get base parsing
    const baseResponse = super.parseResponse(rawOutput, exitCode, duration);

    // Claude-specific: Look for file operations in artifact-style output
    const additionalOps = this.parseClaudeArtifacts(rawOutput);
    const mergedOps = this.mergeFileOperations(
      baseResponse.fileOperations,
      additionalOps
    );

    // Claude-specific: Parse thinking/reasoning blocks
    const thinkingBlocks = this.extractThinkingBlocks(rawOutput);

    return {
      ...baseResponse,
      fileOperations: mergedOps,
      // Add thinking content to metadata via text content if present
      textContent: thinkingBlocks.length > 0
        ? `[Thinking]\n${thinkingBlocks.join('\n\n')}\n\n[Response]\n${baseResponse.textContent}`
        : baseResponse.textContent,
    };
  }

  /**
   * Parse Claude artifact-style file outputs
   */
  private parseClaudeArtifacts(output: string): FileOperation[] {
    const operations: FileOperation[] = [];

    // Match Claude's artifact pattern: <artifact identifier="..." type="..." title="...">
    const artifactRegex =
      /<artifact\s+(?:[^>]*?)identifier="([^"]+)"(?:[^>]*?)type="([^"]*)"(?:[^>]*?)(?:title="([^"]*)")?[^>]*>([\s\S]*?)<\/artifact>/g;

    let match: RegExpExecArray | null;
    while ((match = artifactRegex.exec(output)) !== null) {
      const identifier = match[1] ?? '';
      const type = match[2] ?? '';
      const title = match[3] ?? '';
      const content = match[4]?.trim() ?? '';

      // Determine if this is a file
      if (
        type.includes('code') ||
        type.includes('text') ||
        identifier.includes('.')
      ) {
        const language = this.inferLanguageFromType(type);
        operations.push({
          operation: 'create',
          path: title || identifier,
          content,
          language,
        });
      }
    }

    return operations;
  }

  /**
   * Extract thinking/reasoning blocks from Claude output
   */
  private extractThinkingBlocks(output: string): string[] {
    const blocks: string[] = [];

    // Match <thinking> tags
    const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/g;
    let match: RegExpExecArray | null;

    while ((match = thinkingRegex.exec(output)) !== null) {
      const content = match[1]?.trim();
      if (content) {
        blocks.push(content);
      }
    }

    return blocks;
  }

  /**
   * Infer programming language from artifact type
   */
  private inferLanguageFromType(type: string): string {
    const typeMap: Record<string, string> = {
      'application/vnd.ant.code+typescript': 'typescript',
      'application/vnd.ant.code+javascript': 'javascript',
      'application/vnd.ant.code+python': 'python',
      'application/vnd.ant.code+rust': 'rust',
      'application/vnd.ant.code+go': 'go',
      'application/vnd.ant.code+java': 'java',
      'application/vnd.ant.code+cpp': 'cpp',
      'application/vnd.ant.code+c': 'c',
      'text/markdown': 'markdown',
      'text/html': 'html',
      'text/css': 'css',
      'application/json': 'json',
      'application/xml': 'xml',
    };

    for (const [key, lang] of Object.entries(typeMap)) {
      if (type.includes(key) || type.includes(lang)) {
        return lang;
      }
    }

    return 'text';
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
      }
    }

    return merged;
  }

  /**
   * Override code block extraction to handle Claude-specific patterns
   */
  protected override extractCodeBlocks(output: string): CodeBlock[] {
    const blocks = super.extractCodeBlocks(output);

    // Also extract from artifact tags
    const artifactCodeRegex =
      /<artifact[^>]*type="application\/vnd\.ant\.code[^"]*"[^>]*>([\s\S]*?)<\/artifact>/g;

    let match: RegExpExecArray | null;
    while ((match = artifactCodeRegex.exec(output)) !== null) {
      const typeMatch = match[0].match(/type="application\/vnd\.ant\.code\+(\w+)"/);
      const language = typeMatch?.[1] ?? 'text';
      const content = match[1]?.trim() ?? '';

      blocks.push({
        language,
        content,
        startIndex: match.index,
        endIndex: match.index + match[0].length,
      });
    }

    return blocks;
  }
}

/**
 * Default Claude agent instance
 */
export const claude = new ClaudeAgent();
