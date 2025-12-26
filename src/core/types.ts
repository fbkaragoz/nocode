/**
 * Core type definitions for the Multi-Agent Orchestration System
 */

export enum AgentType {
  CLAUDE = 'claude',
  GEMINI = 'gemini',
  CODEX = 'codex'
}

export enum ExecutionMode {
  PARALLEL = 'parallel',       // Independent tasks run simultaneously
  ITERATIVE = 'iterative',     // Chain: Plan -> Implement -> Review
  DISTRIBUTED = 'distributed'  // Assign by file/module expertise
}

export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum TaskPriority {
  CRITICAL = 1,
  HIGH = 2,
  MEDIUM = 3,
  LOW = 4
}

export interface Task {
  id: string;
  description: string;
  agent?: AgentType;
  status: TaskStatus;
  priority: TaskPriority;
  dependencies: string[];
  output?: string;
  error?: string;
  files: string[];
  estimatedComplexity: number;  // 1-10
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  metadata: Record<string, unknown>;
}

export interface ExecutionPlan {
  id: string;
  goal: string;
  mode: ExecutionMode;
  tasks: Task[];
  thinkingOutput: string;
  createdAt: Date;
  metadata: Record<string, unknown>;
}

export interface AgentConfig {
  name: string;
  type: AgentType;
  command: string;
  args: string[];
  timeout: number;
  maxRetries: number;
  workingDirectory?: string;
  environment?: Record<string, string>;
  model?: string;
}

export interface AgentResponse {
  agent: AgentType;
  taskId: string;
  success: boolean;
  output: string;
  error?: string;
  tokensUsed?: number;
  duration: number;
  filesModified: string[];
  filesCreated: string[];
  codeBlocks: CodeBlock[];
  commands: string[];
  metadata: Record<string, unknown>;
}

export interface CodeBlock {
  language: string;
  code: string;
  filename?: string;
}

export interface ProjectContext {
  rootPath: string;
  projectName: string;
  description: string;
  techStack: string[];
  fileStructure: Record<string, string[]>;
  conventions: Record<string, string>;
  dependencies: string[];
  environment: Record<string, string>;
  history: ContextHistoryEntry[];
}

export interface ContextHistoryEntry {
  timestamp: Date;
  action: string;
  agent: AgentType;
  taskId: string;
  summary: string;
}

export interface WorkflowDefinition {
  name: string;
  description: string;
  mode: ExecutionMode;
  steps: WorkflowStep[];
  agentAssignments: Record<string, AgentType>;
  conditions: Record<string, unknown>;
  onSuccess: string[];
  onFailure: string[];
}

export interface WorkflowStep {
  id: string;
  name: string;
  agent?: AgentType;
  action: string;
  inputs: Record<string, string>;
  outputs: string[];
  dependsOn: string[];
  condition?: string;
  timeout?: number;
  retries?: number;
}

export interface ExecutionProgress {
  planId: string;
  total: number;
  completed: number;
  failed: number;
  inProgress: number;
  pending: number;
  percentage: number;
  currentTask?: Task;
  eta?: number;
  startedAt: Date;
  elapsedSeconds: number;
}

export interface ExecutionResult {
  planId: string;
  success: boolean;
  tasks: TaskResult[];
  totalDuration: number;
  filesModified: string[];
  filesCreated: string[];
  summary: string;
  errors: string[];
}

export interface TaskResult {
  taskId: string;
  success: boolean;
  output: string;
  error?: string;
  duration: number;
  agent: AgentType;
  filesModified: string[];
}

export interface OrchestratorConfig {
  maxConcurrency: number;
  defaultTimeout: number;
  defaultRetries: number;
  planningAgent: AgentType;
  reviewAgent: AgentType;
  implementationAgent: AgentType;
  databasePath: string;
  workingDirectory: string;
  verbose: boolean;
}

export interface PlanningResult {
  plan: ExecutionPlan;
  reasoning: string;
  confidence: number;
  alternatives?: ExecutionPlan[];
}

// Event types for progress tracking
export type OrchestratorEvent =
  | { type: 'plan_created'; plan: ExecutionPlan }
  | { type: 'task_started'; task: Task }
  | { type: 'task_completed'; task: Task; result: TaskResult }
  | { type: 'task_failed'; task: Task; error: string }
  | { type: 'progress_update'; progress: ExecutionProgress }
  | { type: 'execution_complete'; result: ExecutionResult }
  | { type: 'error'; error: string };

export type EventHandler = (event: OrchestratorEvent) => void;
