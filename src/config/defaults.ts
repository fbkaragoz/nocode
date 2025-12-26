/**
 * Default configuration for the Multi-Agent Orchestrator
 */

import { AgentType } from '../core/types';
import type { OrchestratorConfig, AgentConfig } from '../core/types';

export const DEFAULT_CONFIG: OrchestratorConfig = {
  maxConcurrency: 3,
  defaultTimeout: 600000, // 10 minutes
  defaultRetries: 2,
  planningAgent: AgentType.GEMINI,    // Best for thinking/planning
  reviewAgent: AgentType.CLAUDE,       // Best for code review
  implementationAgent: AgentType.CODEX, // Best for quick code gen
  databasePath: './data/orchestrator.db',
  workingDirectory: process.cwd(),
  verbose: false
};

export const AGENT_CONFIGS: Record<AgentType, AgentConfig> = {
  [AgentType.CLAUDE]: {
    name: 'Claude',
    type: AgentType.CLAUDE,
    command: 'claude',
    args: ['--print', '--dangerously-skip-permissions'],
    timeout: 600000,
    maxRetries: 2,
    model: undefined // Uses CLI default, can be overridden via --model flag
  },
  [AgentType.GEMINI]: {
    name: 'Gemini',
    type: AgentType.GEMINI,
    command: 'gemini',
    args: ['-y', '-s'],
    timeout: 600000,
    maxRetries: 2,
    model: undefined // Uses CLI default, can be overridden via --model flag
  },
  [AgentType.CODEX]: {
    name: 'Codex',
    type: AgentType.CODEX,
    command: 'codex',
    args: ['--full-auto'],
    timeout: 300000,
    maxRetries: 2,
    model: undefined // Uses CLI default, can be overridden via --model flag
  }
};

// Agent capability mapping - which tasks each agent excels at
export const AGENT_CAPABILITIES = {
  [AgentType.CLAUDE]: {
    strengths: [
      'architectural-reasoning',
      'code-review',
      'refactoring',
      'documentation',
      'bug-analysis',
      'complex-logic'
    ],
    contextWindow: 200000,
    bestFor: 'Deep analysis and review tasks'
  },
  [AgentType.GEMINI]: {
    strengths: [
      'planning',
      'tool-use',
      'shell-commands',
      'api-integration',
      'rapid-prototyping',
      'file-operations'
    ],
    contextWindow: 1000000,
    bestFor: 'Planning and tool-heavy tasks'
  },
  [AgentType.CODEX]: {
    strengths: [
      'code-generation',
      'code-completion',
      'boilerplate',
      'test-generation',
      'language-conversion',
      'quick-fixes'
    ],
    contextWindow: 128000,
    bestFor: 'Fast code generation'
  }
};

// Task type to agent mapping
export const TASK_AGENT_MAPPING: Record<string, AgentType> = {
  // Planning tasks
  'plan': AgentType.GEMINI,
  'architect': AgentType.CLAUDE,
  'design': AgentType.CLAUDE,

  // Implementation tasks
  'implement': AgentType.CODEX,
  'code': AgentType.CODEX,
  'generate': AgentType.CODEX,
  'create': AgentType.CODEX,

  // Review tasks
  'review': AgentType.CLAUDE,
  'analyze': AgentType.CLAUDE,
  'audit': AgentType.CLAUDE,

  // Shell/tool tasks
  'run': AgentType.GEMINI,
  'execute': AgentType.GEMINI,
  'test': AgentType.GEMINI,
  'deploy': AgentType.GEMINI,

  // Fix tasks
  'fix': AgentType.CODEX,
  'debug': AgentType.CLAUDE,
  'refactor': AgentType.CLAUDE
};

// Keywords for automatic agent assignment
export const AGENT_KEYWORDS = {
  [AgentType.CLAUDE]: [
    'review', 'analyze', 'explain', 'understand', 'refactor',
    'architecture', 'design', 'document', 'why', 'reason'
  ],
  [AgentType.GEMINI]: [
    'run', 'execute', 'test', 'deploy', 'install', 'setup',
    'shell', 'command', 'api', 'fetch', 'plan', 'think'
  ],
  [AgentType.CODEX]: [
    'write', 'create', 'generate', 'implement', 'code',
    'function', 'class', 'component', 'boilerplate', 'convert'
  ]
};

/**
 * Determine the best agent for a task based on keywords
 */
export function selectAgent(taskDescription: string): AgentType {
  const lower = taskDescription.toLowerCase();

  // Check keywords for each agent
  for (const [agent, keywords] of Object.entries(AGENT_KEYWORDS)) {
    for (const keyword of keywords) {
      if (lower.includes(keyword)) {
        return agent as AgentType;
      }
    }
  }

  // Default to Codex for implementation
  return AgentType.CODEX;
}

/**
 * Get the best agent for a specific task type
 */
export function getAgentForTaskType(taskType: string): AgentType {
  return TASK_AGENT_MAPPING[taskType.toLowerCase()] || AgentType.CODEX;
}
