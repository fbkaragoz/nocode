/**
 * Gemini CLI Agent Adapter
 *
 * Adapter for the Gemini CLI which provides access to
 * Google's Gemini models via command line.
 *
 * CLI: https://github.com/google-gemini/gemini-cli
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
// Gemini-Specific Configuration
// ============================================================================

/**
 * Extended configuration for Gemini CLI
 */
export interface GeminiAgentConfig extends AgentConfig {
  /** Automatically accept all actions (yolo mode) */
  yolo?: boolean;
  /** Run in sandbox mode */
  sandbox?: boolean;
  /** Model to use (e.g., 'gemini-2.5-pro') */
  model?: string;
  /** Output format: text, json, or stream-json */
  outputFormat?: 'text' | 'json' | 'stream-json';
  /** Approval mode: default, auto_edit, or yolo */
  approvalMode?: 'default' | 'auto_edit' | 'yolo';
  /** Enable debug mode */
  debug?: boolean;
}

// ============================================================================
// Gemini Agent Implementation
// ============================================================================

/**
 * Gemini CLI Agent Adapter
 *
 * Executes prompts via the Gemini CLI with full streaming support
 * and response parsing.
 */
export class GeminiAgent extends BaseAgent {
  readonly name = 'Gemini';
  readonly command = 'gemini';

  /** Default Gemini-specific configuration */
  private readonly geminiDefaults: Required<
    Omit<GeminiAgentConfig, keyof AgentConfig>
  > = {
    yolo: true,
    sandbox: true,
    model: '',
    outputFormat: 'text',
    approvalMode: 'yolo',
    debug: false,
  };

  /**
   * Build Gemini CLI arguments
   *
   * Valid Gemini CLI options:
   * -y, --yolo           Automatically accept all actions
   * -s, --sandbox        Run in sandbox mode
   * -m, --model          Model selection
   * -o, --output-format  Output format (text, json, stream-json)
   * --approval-mode      Approval mode (default, auto_edit, yolo)
   * -d, --debug          Debug mode
   * [query..]            Positional prompt argument
   */
  protected buildArgs(
    prompt: string,
    config: Required<AgentConfig> & Partial<GeminiAgentConfig>
  ): string[] {
    const args: string[] = [];

    // Yolo mode (auto-approve all actions)
    if (config.yolo ?? this.geminiDefaults.yolo) {
      args.push('-y');
    }

    // Sandbox mode
    if (config.sandbox ?? this.geminiDefaults.sandbox) {
      args.push('-s');
    }

    // Model selection
    const model = config.model ?? this.geminiDefaults.model;
    if (model) {
      args.push('-m', model);
    }

    // Output format
    const outputFormat = config.outputFormat ?? this.geminiDefaults.outputFormat;
    if (outputFormat && outputFormat !== 'text') {
      args.push('-o', outputFormat);
    }

    // Debug mode
    if (config.debug ?? this.geminiDefaults.debug) {
      args.push('-d');
    }

    // Extra arguments from config
    args.push(...config.extraArgs);

    // The prompt itself as positional argument (must be last)
    args.push(prompt);

    return args;
  }

  /**
   * Execute with Gemini-specific configuration
   */
  executeWithConfig(
    prompt: string,
    config?: GeminiAgentConfig,
    onStream?: StreamCallback
  ) {
    return this.execute(prompt, config, onStream);
  }

  /**
   * Run with Gemini-specific configuration
   */
  async runWithConfig(
    prompt: string,
    config?: GeminiAgentConfig,
    onStream?: StreamCallback
  ): Promise<AgentResponse> {
    return this.executeWithConfig(prompt, config, onStream).promise;
  }

  /**
   * Parse Gemini-specific response patterns
   */
  protected override parseResponse(
    rawOutput: string,
    exitCode: number | null,
    duration: number
  ): AgentResponse {
    // Get base parsing
    const baseResponse = super.parseResponse(rawOutput, exitCode, duration);

    // Gemini-specific: Parse function call responses
    const functionCalls = this.extractFunctionCalls(rawOutput);

    // Gemini-specific: Parse grounding citations
    const citations = this.extractCitations(rawOutput);

    // Add function calls to commands if present
    const enhancedCommands = [
      ...baseResponse.commands,
      ...functionCalls.map((fc) => ({
        command: `${fc.name}(${JSON.stringify(fc.args)})`,
        description: `Gemini function call: ${fc.name}`,
        isShell: false,
      })),
    ];

    // Include citations in text content if present
    let textContent = baseResponse.textContent;
    if (citations.length > 0) {
      textContent += '\n\n[Citations]\n' + citations.join('\n');
    }

    return {
      ...baseResponse,
      commands: enhancedCommands,
      textContent,
    };
  }

  /**
   * Extract function calls from Gemini response
   */
  private extractFunctionCalls(
    output: string
  ): Array<{ name: string; args: Record<string, unknown> }> {
    const calls: Array<{ name: string; args: Record<string, unknown> }> = [];

    // Match JSON function call format
    const functionCallRegex =
      /\{\s*"function_call"\s*:\s*\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{[^}]*\})\s*\}\s*\}/g;

    let match: RegExpExecArray | null;
    while ((match = functionCallRegex.exec(output)) !== null) {
      const name = match[1] ?? '';
      try {
        const args = JSON.parse(match[2] ?? '{}') as Record<string, unknown>;
        calls.push({ name, args });
      } catch {
        calls.push({ name, args: {} });
      }
    }

    // Also match XML-style function calls
    const xmlFunctionRegex =
      /<function_call>\s*<name>([^<]+)<\/name>\s*<arguments>([\s\S]*?)<\/arguments>\s*<\/function_call>/g;

    while ((match = xmlFunctionRegex.exec(output)) !== null) {
      const name = match[1]?.trim() ?? '';
      try {
        const args = JSON.parse(match[2]?.trim() ?? '{}') as Record<
          string,
          unknown
        >;
        calls.push({ name, args });
      } catch {
        calls.push({ name, args: { raw: match[2]?.trim() } });
      }
    }

    return calls;
  }

  /**
   * Extract grounding citations from Gemini response
   */
  private extractCitations(output: string): string[] {
    const citations: string[] = [];

    // Match citation patterns
    const citationPatterns = [
      /\[(?:Source|Citation|Reference)\s*(\d+)\]:\s*([^\n]+)/gi,
      /\[(\d+)\]\s*([^\n]+)/g,
      /<citation\s+url="([^"]+)"[^>]*>([^<]*)<\/citation>/gi,
    ];

    for (const pattern of citationPatterns) {
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(output)) !== null) {
        const citation = match[2]?.trim() || match[1]?.trim();
        if (citation && !citations.includes(citation)) {
          citations.push(citation);
        }
      }
    }

    return citations;
  }

  /**
   * Override code block extraction to handle Gemini-specific patterns
   */
  protected override extractCodeBlocks(output: string): CodeBlock[] {
    const blocks = super.extractCodeBlocks(output);

    // Gemini sometimes uses different code fence styles
    // Handle indented code blocks (4 spaces)
    const indentedBlockRegex =
      /(?:^|\n)((?:    [^\n]*\n){2,})/g;

    let match: RegExpExecArray | null;
    while ((match = indentedBlockRegex.exec(output)) !== null) {
      const content = match[1]
        ?.split('\n')
        .map((line) => line.slice(4))
        .join('\n')
        .trim();

      if (content && content.length > 20) {
        // Only if substantial
        // Avoid duplicates
        const isDuplicate = blocks.some((b) =>
          b.content.includes(content) || content.includes(b.content)
        );

        if (!isDuplicate) {
          blocks.push({
            language: this.inferLanguage(content),
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
   * Infer programming language from code content
   */
  private inferLanguage(content: string): string {
    const patterns: Array<[RegExp, string]> = [
      [/^import\s+.*from\s+['"]|^export\s+(default\s+)?/m, 'typescript'],
      [/^const\s+\w+\s*=\s*require\(/m, 'javascript'],
      [/^def\s+\w+\s*\(|^import\s+\w+$|^from\s+\w+\s+import/m, 'python'],
      [/^package\s+\w+|^func\s+\w+\s*\(/m, 'go'],
      [/^fn\s+\w+\s*\(|^use\s+\w+::|^impl\s+/m, 'rust'],
      [/^public\s+class\s+|^import\s+java\./m, 'java'],
      [/^#include\s*<|^int\s+main\s*\(/m, 'c'],
      [/^#include\s*<.*>|^class\s+\w+\s*\{|^namespace\s+/m, 'cpp'],
      [/^<!DOCTYPE|^<html/i, 'html'],
      [/^\s*\{[\s\S]*"[\w]+":/m, 'json'],
      [/^[\w-]+:\s*\S+/m, 'yaml'],
      [/^\$\s+|^#!/m, 'bash'],
    ];

    for (const [pattern, lang] of patterns) {
      if (pattern.test(content)) {
        return lang;
      }
    }

    return 'text';
  }

  /**
   * Override file operations to handle Gemini's output style
   */
  protected override extractFileOperations(
    output: string,
    codeBlocks: CodeBlock[]
  ): FileOperation[] {
    const operations = super.extractFileOperations(output, codeBlocks);

    // Gemini often uses headers like "### filename.ts" before code
    const headerFileRegex = /^#{1,4}\s+([^\n]+\.[\w]+)\s*$/gm;

    let match: RegExpExecArray | null;
    while ((match = headerFileRegex.exec(output)) !== null) {
      const path = match[1]?.trim();
      if (path && !operations.some((op) => op.path === path)) {
        // Find the next code block after this header
        const blockAfter = codeBlocks.find(
          (b) =>
            b.startIndex > match!.index && b.startIndex < match!.index + 200
        );

        if (blockAfter) {
          operations.push({
            operation: 'create',
            path,
            content: blockAfter.content,
            language: blockAfter.language,
          });
        }
      }
    }

    return operations;
  }
}

/**
 * Default Gemini agent instance
 */
export const gemini = new GeminiAgent();
