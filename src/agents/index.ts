/**
 * Agent Adapters Module
 *
 * Provides unified access to multiple AI CLI agents (Claude, Gemini, Codex)
 * with a consistent interface for executing prompts, streaming output,
 * and parsing responses.
 *
 * @example
 * ```typescript
 * import { claude, gemini, codex, AgentRegistry } from './agents';
 *
 * // Use a specific agent
 * const response = await claude.run('Write a hello world function');
 *
 * // Stream output
 * const handle = claude.execute('Generate code', undefined, (chunk, type) => {
 *   process.stdout.write(chunk);
 * });
 *
 * // Cancel if needed
 * setTimeout(() => handle.cancel(), 5000);
 *
 * // Use the registry
 * const agent = AgentRegistry.get('claude');
 * const available = await AgentRegistry.getAvailable();
 * ```
 */

// ============================================================================
// Re-exports from base module
// ============================================================================

export {
  // Interfaces
  type AgentConfig,
  type AgentResponse,
  type AgentHandle,
  type StreamCallback,
  type CodeBlock,
  type FileOperation,
  type ParsedCommand,
  // Base class
  BaseAgent,
} from './base.ts';

// ============================================================================
// Re-exports from agent implementations
// ============================================================================

export {
  ClaudeAgent,
  claude,
  type ClaudeAgentConfig,
} from './claude.ts';

export {
  GeminiAgent,
  gemini,
  type GeminiAgentConfig,
} from './gemini.ts';

export {
  CodexAgent,
  codex,
  type CodexAgentConfig,
} from './codex.ts';

// ============================================================================
// Agent Registry
// ============================================================================

import { BaseAgent } from './base.ts';
import { claude, ClaudeAgent } from './claude.ts';
import { gemini, GeminiAgent } from './gemini.ts';
import { codex, CodexAgent } from './codex.ts';

/**
 * Supported agent names
 */
export type AgentName = 'claude' | 'gemini' | 'codex';

/**
 * Agent info structure
 */
export interface AgentInfo {
  name: AgentName;
  displayName: string;
  command: string;
  available: boolean;
  version: string | null;
}

/**
 * Registry for managing multiple agents
 */
export class AgentRegistry {
  private static readonly agents: Map<AgentName, BaseAgent> = new Map<AgentName, BaseAgent>([
    ['claude', claude as BaseAgent],
    ['gemini', gemini as BaseAgent],
    ['codex', codex as BaseAgent],
  ]);

  /**
   * Get an agent by name
   * @param name Agent name
   * @returns Agent instance or undefined
   */
  static get(name: AgentName): BaseAgent | undefined {
    return this.agents.get(name);
  }

  /**
   * Get all registered agents
   * @returns Map of agent name to instance
   */
  static getAll(): Map<AgentName, BaseAgent> {
    return new Map(this.agents);
  }

  /**
   * Get all agent names
   * @returns Array of agent names
   */
  static getNames(): AgentName[] {
    return Array.from(this.agents.keys());
  }

  /**
   * Check if an agent is registered
   * @param name Agent name
   * @returns true if registered
   */
  static has(name: string): name is AgentName {
    return this.agents.has(name as AgentName);
  }

  /**
   * Get info about all agents (including availability)
   * @returns Promise resolving to array of AgentInfo
   */
  static async getAllInfo(): Promise<AgentInfo[]> {
    const infos: AgentInfo[] = [];

    for (const [name, agent] of this.agents) {
      const [available, version] = await Promise.all([
        agent.isAvailable(),
        agent.getVersion(),
      ]);

      infos.push({
        name,
        displayName: agent.name,
        command: agent.command,
        available,
        version,
      });
    }

    return infos;
  }

  /**
   * Get only available agents
   * @returns Promise resolving to array of available agent instances
   */
  static async getAvailable(): Promise<BaseAgent[]> {
    const available: BaseAgent[] = [];

    for (const agent of this.agents.values()) {
      if (await agent.isAvailable()) {
        available.push(agent);
      }
    }

    return available;
  }

  /**
   * Get the first available agent
   * @param preferred Optional preferred agent name to try first
   * @returns Promise resolving to agent or null
   */
  static async getFirstAvailable(preferred?: AgentName): Promise<BaseAgent | null> {
    // Try preferred first
    if (preferred) {
      const agent = this.agents.get(preferred);
      if (agent && (await agent.isAvailable())) {
        return agent;
      }
    }

    // Try others
    for (const agent of this.agents.values()) {
      if (await agent.isAvailable()) {
        return agent;
      }
    }

    return null;
  }

  /**
   * Register a custom agent
   * @param name Agent name
   * @param agent Agent instance
   */
  static register(name: string, agent: BaseAgent): void {
    this.agents.set(name as AgentName, agent);
  }

  /**
   * Unregister an agent
   * @param name Agent name
   * @returns true if agent was removed
   */
  static unregister(name: AgentName): boolean {
    return this.agents.delete(name);
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create a new Claude agent instance with custom configuration
 * @returns New ClaudeAgent instance
 */
export function createClaudeAgent(): ClaudeAgent {
  return new ClaudeAgent();
}

/**
 * Create a new Gemini agent instance with custom configuration
 * @returns New GeminiAgent instance
 */
export function createGeminiAgent(): GeminiAgent {
  return new GeminiAgent();
}

/**
 * Create a new Codex agent instance with custom configuration
 * @returns New CodexAgent instance
 */
export function createCodexAgent(): CodexAgent {
  return new CodexAgent();
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Execute a prompt with the first available agent
 * @param prompt The prompt to execute
 * @param preferred Optional preferred agent
 * @returns Promise resolving to AgentResponse
 * @throws Error if no agents are available
 */
export async function executeWithAnyAgent(
  prompt: string,
  preferred?: AgentName
): Promise<{ agent: BaseAgent; response: import('./base.ts').AgentResponse }> {
  const agent = await AgentRegistry.getFirstAvailable(preferred);

  if (!agent) {
    throw new Error(
      'No AI agents are available. Please install one of: claude, gemini, or codex CLI.'
    );
  }

  const response = await agent.run(prompt);
  return { agent, response };
}

/**
 * Check availability of all agents
 * @returns Promise resolving to availability map
 */
export async function checkAgentAvailability(): Promise<
  Record<AgentName, boolean>
> {
  const infos = await AgentRegistry.getAllInfo();
  const result: Record<AgentName, boolean> = {
    claude: false,
    gemini: false,
    codex: false,
  };

  for (const info of infos) {
    result[info.name] = info.available;
  }

  return result;
}

/**
 * Print agent status to console (useful for debugging)
 */
export async function printAgentStatus(): Promise<void> {
  const infos = await AgentRegistry.getAllInfo();

  console.log('\nAgent Status:');
  console.log('─'.repeat(50));

  for (const info of infos) {
    const status = info.available ? '✓' : '✗';
    const version = info.version ? `v${info.version}` : 'not found';
    console.log(
      `  ${status} ${info.displayName.padEnd(10)} (${info.command}) - ${version}`
    );
  }

  console.log('─'.repeat(50));
}

// ============================================================================
// Default Export
// ============================================================================

export default {
  // Agent instances
  claude,
  gemini,
  codex,
  // Registry
  AgentRegistry,
  // Factory functions
  createClaudeAgent,
  createGeminiAgent,
  createCodexAgent,
  // Utilities
  executeWithAnyAgent,
  checkAgentAvailability,
  printAgentStatus,
};
