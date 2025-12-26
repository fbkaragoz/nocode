/**
 * Core Orchestrator Module
 *
 * The central brain of the multi-agent AI system. This module is responsible for:
 * - Parsing high-level user goals into actionable execution plans
 * - Coordinating between Claude, Gemini, and Codex agents
 * - Managing execution pipelines with dependency resolution
 * - Handling errors, retries, and state persistence
 *
 * @module core/orchestrator
 */

import { EventEmitter } from "events";

// ============================================================================
// Type Definitions & Interfaces
// ============================================================================

/** Supported AI agent types in the system */
export type AgentType = "claude" | "gemini" | "codex";

/** Execution modes for task orchestration */
export type ExecutionMode = "parallel" | "sequential" | "iterative" | "distributed";

/** Task execution status */
export type TaskStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "retrying";

/** Priority levels for task scheduling */
export type TaskPriority = "critical" | "high" | "normal" | "low";

/** Plan status */
export type PlanStatus =
  | "draft"
  | "planning"
  | "ready"
  | "executing"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

/** Agent capability definitions */
export interface AgentCapabilities {
  /** Agent identifier */
  agent: AgentType;
  /** Types of tasks this agent excels at */
  strengths: string[];
  /** Maximum concurrent operations */
  concurrencyLimit: number;
  /** Whether agent supports streaming */
  supportsStreaming: boolean;
  /** Whether agent supports thinking/reasoning mode */
  supportsThinkingMode: boolean;
  /** Cost per 1K tokens (for optimization) */
  costPer1kTokens: number;
  /** Maximum context window */
  maxContextTokens: number;
}

/** Configuration for agent API calls */
export interface AgentConfig {
  apiKey?: string;
  baseUrl?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  timeout?: number;
  thinkingMode?: boolean;
  thinkingBudget?: number;
}

/** Task definition within an execution plan */
export interface Task {
  /** Unique task identifier */
  id: string;
  /** Human-readable task name */
  name: string;
  /** Detailed task description */
  description: string;
  /** Assigned agent type */
  agent: AgentType;
  /** Task dependencies (IDs of tasks that must complete first) */
  dependencies: string[];
  /** Current execution status */
  status: TaskStatus;
  /** Task priority */
  priority: TaskPriority;
  /** Input data/context for the task */
  input: TaskInput;
  /** Output/result from task execution */
  output?: TaskOutput;
  /** Retry configuration */
  retryConfig: RetryConfig;
  /** Current retry count */
  retryCount: number;
  /** Execution timestamps */
  timestamps: TaskTimestamps;
  /** Task metadata */
  metadata: Record<string, unknown>;
  /** Estimated duration in milliseconds */
  estimatedDuration?: number;
  /** Actual duration in milliseconds */
  actualDuration?: number;
}

/** Task input specification */
export interface TaskInput {
  /** Primary prompt/instruction for the agent */
  prompt: string;
  /** Additional context from previous tasks */
  context?: string;
  /** Files or code to process */
  files?: FileReference[];
  /** Structured data input */
  data?: Record<string, unknown>;
  /** System prompt override */
  systemPrompt?: string;
}

/** File reference for task processing */
export interface FileReference {
  path: string;
  content?: string;
  language?: string;
}

/** Task output structure */
export interface TaskOutput {
  /** Whether task completed successfully */
  success: boolean;
  /** Primary result/response */
  result?: string;
  /** Structured data output */
  data?: Record<string, unknown>;
  /** Generated/modified files */
  files?: FileReference[];
  /** Error information if failed */
  error?: TaskError;
  /** Token usage statistics */
  usage?: TokenUsage;
  /** Thinking/reasoning trace (if applicable) */
  thinkingTrace?: string;
}

/** Token usage statistics */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  thinkingTokens?: number;
}

/** Task error information */
export interface TaskError {
  code: string;
  message: string;
  stack?: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}

/** Task timestamps */
export interface TaskTimestamps {
  created: Date;
  queued?: Date;
  started?: Date;
  completed?: Date;
}

/** Retry configuration */
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

/** Complete execution plan */
export interface ExecutionPlan {
  /** Unique plan identifier */
  id: string;
  /** Original user goal */
  goal: string;
  /** Parsed/refined goal description */
  refinedGoal: string;
  /** Execution mode */
  mode: ExecutionMode;
  /** All tasks in the plan */
  tasks: Task[];
  /** Task execution order (topologically sorted) */
  executionOrder: string[];
  /** Current plan status */
  status: PlanStatus;
  /** Plan creation timestamp */
  createdAt: Date;
  /** Last update timestamp */
  updatedAt: Date;
  /** Overall progress (0-100) */
  progress: number;
  /** Plan metadata */
  metadata: PlanMetadata;
  /** Execution context shared between tasks */
  sharedContext: SharedContext;
}

/** Plan metadata */
export interface PlanMetadata {
  /** Estimated total duration */
  estimatedDuration: number;
  /** Actual total duration */
  actualDuration?: number;
  /** Total token usage */
  totalTokens: number;
  /** Estimated cost */
  estimatedCost: number;
  /** Actual cost */
  actualCost?: number;
  /** Planning reasoning trace */
  planningTrace?: string;
  /** Number of planning iterations */
  planningIterations: number;
}

/** Shared context between tasks */
export interface SharedContext {
  /** Accumulated knowledge/findings */
  knowledge: Record<string, unknown>;
  /** Generated artifacts */
  artifacts: FileReference[];
  /** Variables that can be referenced across tasks */
  variables: Record<string, unknown>;
  /** Conversation/interaction history */
  history: ContextHistoryEntry[];
}

/** Context history entry */
export interface ContextHistoryEntry {
  taskId: string;
  timestamp: Date;
  type: "input" | "output" | "error" | "note";
  content: string;
}

/** Orchestrator configuration */
export interface OrchestratorConfig {
  /** Agent configurations */
  agents: Partial<Record<AgentType, AgentConfig>>;
  /** Default execution mode */
  defaultMode: ExecutionMode;
  /** Maximum parallel tasks */
  maxParallelTasks: number;
  /** Global timeout in milliseconds */
  globalTimeout: number;
  /** State persistence path */
  statePath: string;
  /** Enable detailed logging */
  verbose: boolean;
  /** Default retry configuration */
  defaultRetryConfig: RetryConfig;
  /** Planning agent preference */
  planningAgent: AgentType;
  /** Enable thinking mode for planning */
  usePlanningThinkingMode: boolean;
  /** Thinking budget for planning */
  planningThinkingBudget: number;
}

/** Orchestrator events */
export interface OrchestratorEvents {
  "plan:created": (plan: ExecutionPlan) => void;
  "plan:started": (plan: ExecutionPlan) => void;
  "plan:progress": (plan: ExecutionPlan, progress: number) => void;
  "plan:completed": (plan: ExecutionPlan) => void;
  "plan:failed": (plan: ExecutionPlan, error: Error) => void;
  "plan:cancelled": (plan: ExecutionPlan) => void;
  "task:queued": (task: Task) => void;
  "task:started": (task: Task) => void;
  "task:progress": (task: Task, progress: number) => void;
  "task:completed": (task: Task) => void;
  "task:failed": (task: Task, error: TaskError) => void;
  "task:retrying": (task: Task, attempt: number) => void;
  "agent:calling": (agent: AgentType, task: Task) => void;
  "agent:response": (agent: AgentType, task: Task, output: TaskOutput) => void;
  "state:saved": (path: string) => void;
  "state:loaded": (path: string) => void;
}

/** Agent interface that must be implemented by agent adapters */
export interface IAgent {
  readonly type: AgentType;
  readonly capabilities: AgentCapabilities;
  execute(input: TaskInput, config?: AgentConfig): Promise<TaskOutput>;
  stream?(input: TaskInput, config?: AgentConfig): AsyncGenerator<string, TaskOutput>;
  validateInput?(input: TaskInput): boolean;
}

/** Planning result from the planning phase */
export interface PlanningResult {
  tasks: Omit<Task, "id" | "status" | "retryCount" | "timestamps">[];
  reasoning: string;
  estimatedDuration: number;
  suggestedMode: ExecutionMode;
  risks: string[];
  alternatives?: string[];
}

// ============================================================================
// Utility Functions
// ============================================================================

/** Generate a unique identifier */
function generateId(prefix: string = ""): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return prefix ? `${prefix}_${timestamp}_${random}` : `${timestamp}_${random}`;
}

/** Calculate exponential backoff delay */
function calculateBackoff(
  attempt: number,
  baseDelay: number,
  maxDelay: number,
  multiplier: number
): number {
  const delay = baseDelay * Math.pow(multiplier, attempt);
  return Math.min(delay, maxDelay);
}

/** Sleep for specified milliseconds */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Topological sort for dependency resolution */
function topologicalSort(tasks: Task[]): string[] {
  const taskMap = new Map(tasks.map((t) => [t.id, t]));
  const visited = new Set<string>();
  const visiting = new Set<string>();
  const order: string[] = [];

  function visit(taskId: string): void {
    if (visited.has(taskId)) return;
    if (visiting.has(taskId)) {
      throw new Error(`Circular dependency detected involving task: ${taskId}`);
    }

    visiting.add(taskId);
    const task = taskMap.get(taskId);
    if (task) {
      for (const depId of task.dependencies) {
        visit(depId);
      }
    }
    visiting.delete(taskId);
    visited.add(taskId);
    order.push(taskId);
  }

  for (const task of tasks) {
    visit(task.id);
  }

  return order;
}

/** Deep clone an object */
function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

// ============================================================================
// Default Configurations
// ============================================================================

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
};

const DEFAULT_ORCHESTRATOR_CONFIG: OrchestratorConfig = {
  agents: {},
  defaultMode: "sequential",
  maxParallelTasks: 5,
  globalTimeout: 600000, // 10 minutes
  statePath: ".orchestrator-state",
  verbose: false,
  defaultRetryConfig: DEFAULT_RETRY_CONFIG,
  planningAgent: "gemini",
  usePlanningThinkingMode: true,
  planningThinkingBudget: 10000,
};

const AGENT_CAPABILITIES: Record<AgentType, AgentCapabilities> = {
  claude: {
    agent: "claude",
    strengths: ["reasoning", "code-review", "analysis", "writing", "debugging"],
    concurrencyLimit: 5,
    supportsStreaming: true,
    supportsThinkingMode: true,
    costPer1kTokens: 0.015,
    maxContextTokens: 200000,
  },
  gemini: {
    agent: "gemini",
    strengths: ["planning", "research", "multimodal", "long-context", "reasoning"],
    concurrencyLimit: 10,
    supportsStreaming: true,
    supportsThinkingMode: true,
    costPer1kTokens: 0.00125,
    maxContextTokens: 2000000,
  },
  codex: {
    agent: "codex",
    strengths: ["code-generation", "refactoring", "testing", "documentation"],
    concurrencyLimit: 3,
    supportsStreaming: true,
    supportsThinkingMode: false,
    costPer1kTokens: 0.01,
    maxContextTokens: 128000,
  },
};

// ============================================================================
// Agent Registry (Placeholder for actual agent implementations)
// ============================================================================

/**
 * Agent Registry
 * Manages agent instances and provides factory methods
 */
class AgentRegistry {
  private agents: Map<AgentType, IAgent> = new Map();
  private configs: Partial<Record<AgentType, AgentConfig>> = {};

  constructor(configs: Partial<Record<AgentType, AgentConfig>> = {}) {
    this.configs = configs;
  }

  /** Register an agent implementation */
  register(agent: IAgent): void {
    this.agents.set(agent.type, agent);
  }

  /** Get an agent by type */
  get(type: AgentType): IAgent | undefined {
    return this.agents.get(type);
  }

  /** Check if agent is registered */
  has(type: AgentType): boolean {
    return this.agents.has(type);
  }

  /** Get agent configuration */
  getConfig(type: AgentType): AgentConfig | undefined {
    return this.configs[type];
  }

  /** Get capabilities for an agent type */
  getCapabilities(type: AgentType): AgentCapabilities {
    return AGENT_CAPABILITIES[type];
  }

  /** Select best agent for a task based on requirements */
  selectAgent(requirements: string[]): AgentType {
    let bestMatch: AgentType = "claude";
    let bestScore = 0;

    for (const [type, caps] of Object.entries(AGENT_CAPABILITIES)) {
      const score = requirements.filter((r) =>
        caps.strengths.some((s) => s.includes(r) || r.includes(s))
      ).length;

      if (score > bestScore) {
        bestScore = score;
        bestMatch = type as AgentType;
      }
    }

    return bestMatch;
  }
}

// ============================================================================
// Task Runner
// ============================================================================

/**
 * Task Runner
 * Executes individual tasks with retry logic and progress tracking
 */
class TaskRunner {
  private emitter: EventEmitter;
  private registry: AgentRegistry;
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(emitter: EventEmitter, registry: AgentRegistry) {
    this.emitter = emitter;
    this.registry = registry;
  }

  /** Execute a single task */
  async execute(
    task: Task,
    context: SharedContext,
    config?: AgentConfig
  ): Promise<TaskOutput> {
    const abortController = new AbortController();
    this.abortControllers.set(task.id, abortController);

    try {
      // Update task status
      task.status = "running";
      task.timestamps.started = new Date();
      this.emitter.emit("task:started", task);

      // Get agent
      const agent = this.registry.get(task.agent);
      if (!agent) {
        // If no agent registered, use mock execution
        return await this.mockAgentExecution(task, context, config);
      }

      // Prepare input with context
      const enrichedInput = this.enrichInput(task.input, context);

      // Execute with agent
      const output = await agent.execute(
        enrichedInput,
        { ...this.registry.getConfig(task.agent), ...config }
      );

      return output;
    } finally {
      this.abortControllers.delete(task.id);
    }
  }

  /** Execute with retries */
  async executeWithRetry(
    task: Task,
    context: SharedContext,
    config?: AgentConfig
  ): Promise<TaskOutput> {
    let lastError: TaskError | null = null;

    for (let attempt = 0; attempt <= task.retryConfig.maxRetries; attempt++) {
      if (attempt > 0) {
        task.status = "retrying";
        task.retryCount = attempt;
        this.emitter.emit("task:retrying", task, attempt);

        const delay = calculateBackoff(
          attempt - 1,
          task.retryConfig.baseDelay,
          task.retryConfig.maxDelay,
          task.retryConfig.backoffMultiplier
        );
        await sleep(delay);
      }

      try {
        const output = await this.execute(task, context, config);

        if (output.success) {
          task.status = "completed";
          task.output = output;
          task.timestamps.completed = new Date();
          task.actualDuration =
            task.timestamps.completed.getTime() -
            (task.timestamps.started?.getTime() || task.timestamps.created.getTime());

          this.emitter.emit("task:completed", task);
          return output;
        }

        // Check if error is retryable
        if (output.error && !output.error.retryable) {
          throw output.error;
        }

        lastError = output.error || {
          code: "UNKNOWN_ERROR",
          message: "Task failed without specific error",
          retryable: true,
        };
      } catch (error) {
        lastError = this.normalizeError(error);
        if (!lastError.retryable) {
          break;
        }
      }
    }

    // All retries exhausted
    task.status = "failed";
    task.output = { success: false, error: lastError! };
    task.timestamps.completed = new Date();
    task.actualDuration =
      task.timestamps.completed.getTime() -
      (task.timestamps.started?.getTime() || task.timestamps.created.getTime());

    this.emitter.emit("task:failed", task, lastError!);
    return task.output;
  }

  /** Cancel a running task */
  cancel(taskId: string): boolean {
    const controller = this.abortControllers.get(taskId);
    if (controller) {
      controller.abort();
      return true;
    }
    return false;
  }

  /** Enrich task input with shared context */
  private enrichInput(input: TaskInput, context: SharedContext): TaskInput {
    const enrichedPrompt = this.buildEnrichedPrompt(input.prompt, context);

    return {
      ...input,
      prompt: enrichedPrompt,
      context: JSON.stringify(context.knowledge),
      data: {
        ...input.data,
        _sharedVariables: context.variables,
      },
    };
  }

  /** Build enriched prompt with context */
  private buildEnrichedPrompt(prompt: string, context: SharedContext): string {
    const parts: string[] = [];

    // Add relevant history
    if (context.history.length > 0) {
      const recentHistory = context.history.slice(-5);
      parts.push("## Previous Context");
      for (const entry of recentHistory) {
        parts.push(`[${entry.type.toUpperCase()}] ${entry.content.substring(0, 500)}`);
      }
      parts.push("");
    }

    // Add main prompt
    parts.push("## Current Task");
    parts.push(prompt);

    // Add available artifacts reference
    if (context.artifacts.length > 0) {
      parts.push("");
      parts.push("## Available Artifacts");
      for (const artifact of context.artifacts) {
        parts.push(`- ${artifact.path} (${artifact.language || "unknown"})`);
      }
    }

    return parts.join("\n");
  }

  /** Mock agent execution for when no real agent is registered */
  private async mockAgentExecution(
    task: Task,
    context: SharedContext,
    _config?: AgentConfig
  ): Promise<TaskOutput> {
    // Simulate processing time
    await sleep(100 + Math.random() * 400);

    // For demonstration, return a mock successful response
    return {
      success: true,
      result: `[Mock ${task.agent}] Executed task: ${task.name}`,
      data: {
        taskId: task.id,
        agent: task.agent,
        inputPromptLength: task.input.prompt.length,
        contextKnowledgeKeys: Object.keys(context.knowledge),
      },
      usage: {
        promptTokens: Math.floor(task.input.prompt.length / 4),
        completionTokens: 100,
        totalTokens: Math.floor(task.input.prompt.length / 4) + 100,
      },
    };
  }

  /** Normalize error to TaskError format */
  private normalizeError(error: unknown): TaskError {
    if (typeof error === "object" && error !== null && "code" in error) {
      return error as TaskError;
    }

    const message = error instanceof Error ? error.message : String(error);
    const stack = error instanceof Error ? error.stack : undefined;

    // Determine if error is retryable
    const retryablePatterns = [
      /timeout/i,
      /rate.?limit/i,
      /503/,
      /502/,
      /504/,
      /ECONNRESET/,
      /ETIMEDOUT/,
      /network/i,
    ];
    const retryable = retryablePatterns.some((p) => p.test(message));

    return {
      code: "EXECUTION_ERROR",
      message,
      stack,
      retryable,
    };
  }
}

// ============================================================================
// Execution Pipeline
// ============================================================================

/**
 * Execution Pipeline
 * Manages the execution of tasks according to the plan's execution mode
 */
class ExecutionPipeline {
  private emitter: EventEmitter;
  private taskRunner: TaskRunner;
  private maxParallel: number;
  private activeTaskCount = 0;
  private isPaused = false;
  private isCancelled = false;

  constructor(
    emitter: EventEmitter,
    taskRunner: TaskRunner,
    maxParallel: number
  ) {
    this.emitter = emitter;
    this.taskRunner = taskRunner;
    this.maxParallel = maxParallel;
  }

  /** Execute plan based on its mode */
  async execute(plan: ExecutionPlan): Promise<ExecutionPlan> {
    plan.status = "executing";
    this.emitter.emit("plan:started", plan);

    try {
      switch (plan.mode) {
        case "sequential":
          await this.executeSequential(plan);
          break;
        case "parallel":
          await this.executeParallel(plan);
          break;
        case "iterative":
          await this.executeIterative(plan);
          break;
        case "distributed":
          await this.executeDistributed(plan);
          break;
      }

      // Check final status
      const failedTasks = plan.tasks.filter((t) => t.status === "failed");
      if (failedTasks.length > 0) {
        plan.status = "failed";
        this.emitter.emit("plan:failed", plan, new Error(`${failedTasks.length} tasks failed`));
      } else if (this.isCancelled) {
        plan.status = "cancelled";
        this.emitter.emit("plan:cancelled", plan);
      } else {
        plan.status = "completed";
        plan.progress = 100;
        this.emitter.emit("plan:completed", plan);
      }
    } catch (error) {
      plan.status = "failed";
      this.emitter.emit("plan:failed", plan, error instanceof Error ? error : new Error(String(error)));
    }

    plan.updatedAt = new Date();
    plan.metadata.actualDuration = plan.updatedAt.getTime() - plan.createdAt.getTime();

    return plan;
  }

  /** Sequential execution - one task at a time following dependencies */
  private async executeSequential(plan: ExecutionPlan): Promise<void> {
    const taskMap = new Map(plan.tasks.map((t) => [t.id, t]));

    for (const taskId of plan.executionOrder) {
      if (this.isCancelled) break;
      await this.waitWhilePaused();

      const task = taskMap.get(taskId)!;

      // Check dependencies
      const depsComplete = task.dependencies.every((depId) => {
        const dep = taskMap.get(depId);
        return dep?.status === "completed";
      });

      if (!depsComplete) {
        task.status = "cancelled";
        continue;
      }

      await this.taskRunner.executeWithRetry(task, plan.sharedContext);
      this.updateContext(plan, task);
      this.updateProgress(plan);
    }
  }

  /** Parallel execution - execute independent tasks concurrently */
  private async executeParallel(plan: ExecutionPlan): Promise<void> {
    const taskMap = new Map(plan.tasks.map((t) => [t.id, t]));
    const completedTasks = new Set<string>();
    const runningTasks = new Map<string, Promise<void>>();

    const canRun = (task: Task): boolean => {
      if (task.status !== "pending") return false;
      return task.dependencies.every((depId) => completedTasks.has(depId));
    };

    const runTask = async (task: Task): Promise<void> => {
      await this.taskRunner.executeWithRetry(task, plan.sharedContext);
      this.updateContext(plan, task);
      completedTasks.add(task.id);
      runningTasks.delete(task.id);
      this.activeTaskCount--;
      this.updateProgress(plan);
    };

    while (completedTasks.size < plan.tasks.length && !this.isCancelled) {
      await this.waitWhilePaused();

      // Find ready tasks
      const readyTasks = plan.tasks.filter(
        (t) => canRun(t) && !runningTasks.has(t.id)
      );

      // Start tasks up to concurrency limit
      for (const task of readyTasks) {
        if (this.activeTaskCount >= this.maxParallel) break;

        task.status = "queued";
        this.emitter.emit("task:queued", task);
        this.activeTaskCount++;

        const promise = runTask(task);
        runningTasks.set(task.id, promise);
      }

      // Wait for at least one task to complete
      if (runningTasks.size > 0) {
        await Promise.race(runningTasks.values());
      } else if (completedTasks.size < plan.tasks.length) {
        // No tasks can run and not all complete - dependency issue
        const blocked = plan.tasks.filter(
          (t) => !completedTasks.has(t.id) && !canRun(t)
        );
        for (const task of blocked) {
          task.status = "cancelled";
          task.output = {
            success: false,
            error: {
              code: "DEPENDENCY_FAILED",
              message: "Task cancelled due to failed dependencies",
              retryable: false,
            },
          };
        }
        break;
      }
    }

    // Wait for remaining tasks
    await Promise.all(runningTasks.values());
  }

  /** Iterative execution - run tasks in cycles with feedback */
  private async executeIterative(plan: ExecutionPlan): Promise<void> {
    const MAX_ITERATIONS = 10;
    let iteration = 0;

    while (iteration < MAX_ITERATIONS && !this.isCancelled) {
      await this.waitWhilePaused();

      // Reset pending tasks for new iteration
      for (const task of plan.tasks) {
        if (task.status === "failed" && task.retryCount < task.retryConfig.maxRetries) {
          task.status = "pending";
        }
      }

      // Run one sequential pass
      await this.executeSequential(plan);

      // Check if all tasks complete
      const allComplete = plan.tasks.every((t) => t.status === "completed");
      if (allComplete) break;

      // Analyze failures and adjust
      const failures = plan.tasks.filter((t) => t.status === "failed");
      if (failures.length > 0) {
        // Add context about failures for retry
        plan.sharedContext.knowledge["_lastIterationFailures"] = failures.map((t) => ({
          taskId: t.id,
          error: t.output?.error?.message,
        }));
      }

      iteration++;
    }
  }

  /** Distributed execution - partition tasks across agents */
  private async executeDistributed(plan: ExecutionPlan): Promise<void> {
    // Group tasks by agent
    const tasksByAgent = new Map<AgentType, Task[]>();
    for (const task of plan.tasks) {
      const existing = tasksByAgent.get(task.agent) || [];
      existing.push(task);
      tasksByAgent.set(task.agent, existing);
    }

    // Create execution promises for each agent's tasks
    const agentPromises: Promise<void>[] = [];

    for (const [_agent, tasks] of tasksByAgent) {
      const agentPlan: ExecutionPlan = {
        ...plan,
        tasks,
        executionOrder: topologicalSort(tasks),
        sharedContext: deepClone(plan.sharedContext),
      };

      agentPromises.push(
        this.executeParallel(agentPlan).then(() => {
          // Merge context back
          Object.assign(plan.sharedContext.knowledge, agentPlan.sharedContext.knowledge);
          plan.sharedContext.artifacts.push(...agentPlan.sharedContext.artifacts);
          plan.sharedContext.history.push(...agentPlan.sharedContext.history);
        })
      );
    }

    await Promise.all(agentPromises);
    this.updateProgress(plan);
  }

  /** Pause execution */
  pause(): void {
    this.isPaused = true;
  }

  /** Resume execution */
  resume(): void {
    this.isPaused = false;
  }

  /** Cancel execution */
  cancel(): void {
    this.isCancelled = true;
  }

  /** Wait while paused */
  private async waitWhilePaused(): Promise<void> {
    while (this.isPaused && !this.isCancelled) {
      await sleep(100);
    }
  }

  /** Update shared context from task output */
  private updateContext(plan: ExecutionPlan, task: Task): void {
    if (!task.output?.success) return;

    // Add to history
    plan.sharedContext.history.push({
      taskId: task.id,
      timestamp: new Date(),
      type: "output",
      content: task.output.result || "",
    });

    // Merge data into knowledge
    if (task.output.data) {
      plan.sharedContext.knowledge[task.id] = task.output.data;
    }

    // Add artifacts
    if (task.output.files) {
      plan.sharedContext.artifacts.push(...task.output.files);
    }

    // Update token usage
    if (task.output.usage) {
      plan.metadata.totalTokens += task.output.usage.totalTokens;
    }
  }

  /** Update plan progress */
  private updateProgress(plan: ExecutionPlan): void {
    const completed = plan.tasks.filter(
      (t) => t.status === "completed" || t.status === "failed" || t.status === "cancelled"
    ).length;
    plan.progress = Math.round((completed / plan.tasks.length) * 100);
    plan.updatedAt = new Date();
    this.emitter.emit("plan:progress", plan, plan.progress);
  }
}

// ============================================================================
// Goal Parser & Planner
// ============================================================================

/**
 * Goal Parser
 * Parses user goals and generates execution plans using AI planning
 */
class GoalParser {
  private emitter: EventEmitter;
  private registry: AgentRegistry;
  private config: OrchestratorConfig;

  constructor(
    emitter: EventEmitter,
    registry: AgentRegistry,
    config: OrchestratorConfig
  ) {
    this.emitter = emitter;
    this.registry = registry;
    this.config = config;
  }

  /** Parse a goal string and create an execution plan */
  async parse(goal: string): Promise<ExecutionPlan> {
    const planId = generateId("plan");

    // Create initial plan structure
    const plan: ExecutionPlan = {
      id: planId,
      goal,
      refinedGoal: "",
      mode: this.config.defaultMode,
      tasks: [],
      executionOrder: [],
      status: "planning",
      createdAt: new Date(),
      updatedAt: new Date(),
      progress: 0,
      metadata: {
        estimatedDuration: 0,
        totalTokens: 0,
        estimatedCost: 0,
        planningIterations: 0,
      },
      sharedContext: {
        knowledge: {},
        artifacts: [],
        variables: {},
        history: [],
      },
    };

    // Use planning agent to decompose goal
    const planningResult = await this.planWithAgent(goal);

    plan.refinedGoal = planningResult.reasoning;
    plan.mode = planningResult.suggestedMode;
    plan.metadata.planningTrace = planningResult.reasoning;
    plan.metadata.estimatedDuration = planningResult.estimatedDuration;

    // Convert planning result to tasks
    plan.tasks = planningResult.tasks.map((t, index) => this.createTask(t, index));

    // Calculate execution order
    plan.executionOrder = topologicalSort(plan.tasks);

    // Estimate costs
    plan.metadata.estimatedCost = this.estimateCost(plan.tasks);

    plan.status = "ready";
    plan.updatedAt = new Date();

    this.emitter.emit("plan:created", plan);

    return plan;
  }

  /** Use planning agent to decompose goal into tasks */
  private async planWithAgent(goal: string): Promise<PlanningResult> {
    const planningPrompt = this.buildPlanningPrompt(goal);
    const planningAgent = this.registry.get(this.config.planningAgent);

    if (planningAgent) {
      // Use actual agent for planning
      const config: AgentConfig = {
        ...this.registry.getConfig(this.config.planningAgent),
        thinkingMode: this.config.usePlanningThinkingMode,
        thinkingBudget: this.config.planningThinkingBudget,
      };

      const output = await planningAgent.execute(
        { prompt: planningPrompt },
        config
      );

      if (output.success && output.data) {
        return output.data as unknown as PlanningResult;
      }
    }

    // Fallback to heuristic planning
    return this.heuristicPlanning(goal);
  }

  /** Build the planning prompt */
  private buildPlanningPrompt(goal: string): string {
    return `You are an expert AI orchestrator. Analyze the following goal and break it down into discrete, executable tasks.

## Goal
${goal}

## Available Agents
- **claude**: Best for reasoning, code review, analysis, writing, and debugging
- **gemini**: Best for planning, research, multimodal tasks, and long-context work
- **codex**: Best for code generation, refactoring, testing, and documentation

## Instructions
1. Analyze the goal thoroughly
2. Identify all necessary subtasks
3. Determine dependencies between tasks
4. Assign the most suitable agent for each task
5. Estimate duration for each task
6. Suggest the best execution mode (sequential, parallel, iterative, distributed)

## Output Format (JSON)
{
  "tasks": [
    {
      "name": "Task name",
      "description": "Detailed description",
      "agent": "claude|gemini|codex",
      "dependencies": ["task_0", "task_1"],
      "priority": "critical|high|normal|low",
      "input": {
        "prompt": "The detailed prompt for this task"
      },
      "estimatedDuration": 5000
    }
  ],
  "reasoning": "Explanation of the decomposition strategy",
  "estimatedDuration": 60000,
  "suggestedMode": "parallel|sequential|iterative|distributed",
  "risks": ["Potential risk 1", "Potential risk 2"]
}`;
  }

  /** Heuristic planning when no agent is available */
  private heuristicPlanning(goal: string): PlanningResult {
    // Analyze goal keywords to determine task types
    const goalLower = goal.toLowerCase();
    const tasks: PlanningResult["tasks"] = [];

    // Analysis task
    tasks.push({
      name: "Analyze Requirements",
      description: `Analyze and understand the requirements for: ${goal}`,
      agent: "gemini",
      dependencies: [],
      priority: "high",
      input: {
        prompt: `Analyze the following goal and identify key requirements, constraints, and success criteria:\n\n${goal}`,
      },
      retryConfig: DEFAULT_RETRY_CONFIG,
      metadata: { phase: "analysis" },
      estimatedDuration: 10000,
    });

    // Determine main task type
    if (goalLower.includes("code") || goalLower.includes("implement") || goalLower.includes("build")) {
      tasks.push({
        name: "Generate Implementation Plan",
        description: "Create a detailed implementation plan",
        agent: "claude",
        dependencies: ["task_0"],
        priority: "high",
        input: {
          prompt: `Based on the analysis, create a detailed implementation plan for: ${goal}`,
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "planning" },
        estimatedDuration: 15000,
      });

      tasks.push({
        name: "Implement Solution",
        description: "Write the code implementation",
        agent: "codex",
        dependencies: ["task_1"],
        priority: "high",
        input: {
          prompt: `Implement the solution based on the plan. Goal: ${goal}`,
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "implementation" },
        estimatedDuration: 30000,
      });

      tasks.push({
        name: "Review and Refine",
        description: "Review the implementation and suggest improvements",
        agent: "claude",
        dependencies: ["task_2"],
        priority: "normal",
        input: {
          prompt: "Review the implementation for correctness, best practices, and potential improvements.",
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "review" },
        estimatedDuration: 15000,
      });
    } else if (goalLower.includes("research") || goalLower.includes("analyze") || goalLower.includes("investigate")) {
      tasks.push({
        name: "Deep Research",
        description: "Conduct in-depth research",
        agent: "gemini",
        dependencies: ["task_0"],
        priority: "high",
        input: {
          prompt: `Conduct comprehensive research on: ${goal}`,
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "research" },
        estimatedDuration: 20000,
      });

      tasks.push({
        name: "Synthesize Findings",
        description: "Synthesize and summarize research findings",
        agent: "claude",
        dependencies: ["task_1"],
        priority: "high",
        input: {
          prompt: "Synthesize the research findings into a coherent summary with key insights.",
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "synthesis" },
        estimatedDuration: 15000,
      });
    } else {
      // Generic task decomposition
      tasks.push({
        name: "Execute Primary Task",
        description: `Execute the main objective: ${goal}`,
        agent: "claude",
        dependencies: ["task_0"],
        priority: "high",
        input: {
          prompt: goal,
        },
        retryConfig: DEFAULT_RETRY_CONFIG,
        metadata: { phase: "execution" },
        estimatedDuration: 20000,
      });
    }

    // Verification task
    tasks.push({
      name: "Verify and Validate",
      description: "Verify the results meet the original goal",
      agent: "claude",
      dependencies: [tasks.length > 1 ? `task_${tasks.length - 1}` : "task_0"],
      priority: "normal",
      input: {
        prompt: `Verify that the completed work satisfies the original goal: ${goal}`,
      },
      retryConfig: DEFAULT_RETRY_CONFIG,
      metadata: { phase: "verification" },
      estimatedDuration: 10000,
    });

    const estimatedDuration = tasks.reduce((sum, t) => sum + (t.estimatedDuration || 10000), 0);

    return {
      tasks,
      reasoning: `Decomposed goal into ${tasks.length} tasks using heuristic analysis. Identified as a ${
        goalLower.includes("code") ? "development" : goalLower.includes("research") ? "research" : "general"
      } task.`,
      estimatedDuration,
      suggestedMode: tasks.length > 3 ? "parallel" : "sequential",
      risks: [
        "Heuristic planning may not capture all nuances",
        "Task dependencies may need refinement",
      ],
    };
  }

  /** Create a full Task from planning result */
  private createTask(
    partial: PlanningResult["tasks"][0],
    index: number
  ): Task {
    const taskId = `task_${index}`;

    // Fix dependencies to use actual task IDs
    const dependencies = partial.dependencies.map((dep) => {
      if (dep.startsWith("task_")) return dep;
      const depIndex = parseInt(dep, 10);
      return isNaN(depIndex) ? dep : `task_${depIndex}`;
    });

    return {
      id: taskId,
      name: partial.name,
      description: partial.description,
      agent: partial.agent,
      dependencies,
      status: "pending",
      priority: partial.priority,
      input: partial.input,
      retryConfig: partial.retryConfig || DEFAULT_RETRY_CONFIG,
      retryCount: 0,
      timestamps: {
        created: new Date(),
      },
      metadata: partial.metadata || {},
      estimatedDuration: partial.estimatedDuration,
    };
  }

  /** Estimate total cost for tasks */
  private estimateCost(tasks: Task[]): number {
    return tasks.reduce((total, task) => {
      const capabilities = AGENT_CAPABILITIES[task.agent];
      // Rough estimate: 1000 tokens per task on average
      const estimatedTokens = 1000;
      return total + (estimatedTokens / 1000) * capabilities.costPer1kTokens;
    }, 0);
  }
}

// ============================================================================
// State Manager
// ============================================================================

/**
 * State Manager
 * Handles state persistence and recovery
 */
class StateManager {
  private statePath: string;
  private emitter: EventEmitter;

  constructor(statePath: string, emitter: EventEmitter) {
    this.statePath = statePath;
    this.emitter = emitter;
  }

  /** Save execution plan state */
  async save(plan: ExecutionPlan): Promise<void> {
    const stateFile = `${this.statePath}/${plan.id}.json`;
    const state = JSON.stringify(plan, this.jsonReplacer, 2);

    await Bun.write(stateFile, state);
    this.emitter.emit("state:saved", stateFile);
  }

  /** Load execution plan state */
  async load(planId: string): Promise<ExecutionPlan | null> {
    const stateFile = `${this.statePath}/${planId}.json`;

    try {
      const file = Bun.file(stateFile);
      if (await file.exists()) {
        const content = await file.text();
        const plan = JSON.parse(content, this.jsonReviver);
        this.emitter.emit("state:loaded", stateFile);
        return plan;
      }
    } catch {
      // File doesn't exist or is corrupted
    }

    return null;
  }

  /** List all saved plans */
  async list(): Promise<string[]> {
    const { readdir } = await import("fs/promises");

    try {
      const files = await readdir(this.statePath);
      return files
        .filter((f: string) => f.endsWith(".json"))
        .map((f: string) => f.replace(".json", ""));
    } catch {
      return [];
    }
  }

  /** Delete a saved plan */
  async delete(planId: string): Promise<boolean> {
    const { unlink } = await import("fs/promises");
    const stateFile = `${this.statePath}/${planId}.json`;

    try {
      await unlink(stateFile);
      return true;
    } catch {
      return false;
    }
  }

  /** Ensure state directory exists */
  async ensureDirectory(): Promise<void> {
    const { mkdir } = await import("fs/promises");

    try {
      await mkdir(this.statePath, { recursive: true });
    } catch {
      // Directory already exists
    }
  }

  /** JSON replacer for Date serialization */
  private jsonReplacer(_key: string, value: unknown): unknown {
    if (value instanceof Date) {
      return { __type: "Date", value: value.toISOString() };
    }
    return value;
  }

  /** JSON reviver for Date deserialization */
  private jsonReviver(_key: string, value: unknown): unknown {
    if (
      typeof value === "object" &&
      value !== null &&
      "__type" in value &&
      (value as Record<string, unknown>).__type === "Date"
    ) {
      return new Date((value as Record<string, unknown>).value as string);
    }
    return value;
  }
}

// ============================================================================
// Main Orchestrator Class
// ============================================================================

/**
 * Orchestrator
 * The main brain of the multi-agent AI system
 *
 * @example
 * ```typescript
 * const orchestrator = new Orchestrator({
 *   agents: {
 *     claude: { apiKey: process.env.CLAUDE_API_KEY },
 *     gemini: { apiKey: process.env.GEMINI_API_KEY },
 *   },
 *   maxParallelTasks: 5,
 * });
 *
 * orchestrator.on("task:completed", (task) => {
 *   console.log(`Task ${task.name} completed!`);
 * });
 *
 * const result = await orchestrator.execute("Build a REST API for user management");
 * ```
 */
export class Orchestrator extends EventEmitter {
  private config: OrchestratorConfig;
  private registry: AgentRegistry;
  private goalParser: GoalParser;
  private taskRunner: TaskRunner;
  private pipeline: ExecutionPipeline;
  private stateManager: StateManager;
  private currentPlan: ExecutionPlan | null = null;

  constructor(config: Partial<OrchestratorConfig> = {}) {
    super();

    this.config = { ...DEFAULT_ORCHESTRATOR_CONFIG, ...config };
    this.registry = new AgentRegistry(this.config.agents);
    this.goalParser = new GoalParser(this, this.registry, this.config);
    this.taskRunner = new TaskRunner(this, this.registry);
    this.pipeline = new ExecutionPipeline(this, this.taskRunner, this.config.maxParallelTasks);
    this.stateManager = new StateManager(this.config.statePath, this);
  }

  // ========================================================================
  // Public API
  // ========================================================================

  /**
   * Execute a goal from start to finish
   * This is the main entry point for the orchestrator
   */
  async execute(goal: string): Promise<ExecutionPlan> {
    // Ensure state directory exists
    await this.stateManager.ensureDirectory();

    // Parse goal and create execution plan
    const plan = await this.goalParser.parse(goal);
    this.currentPlan = plan;

    // Save initial state
    await this.stateManager.save(plan);

    // Execute the plan
    const result = await this.pipeline.execute(plan);

    // Save final state
    await this.stateManager.save(result);

    this.currentPlan = null;
    return result;
  }

  /**
   * Create an execution plan without executing it
   */
  async plan(goal: string): Promise<ExecutionPlan> {
    await this.stateManager.ensureDirectory();
    const plan = await this.goalParser.parse(goal);
    await this.stateManager.save(plan);
    return plan;
  }

  /**
   * Execute a previously created plan
   */
  async executePlan(planOrId: ExecutionPlan | string): Promise<ExecutionPlan> {
    let plan: ExecutionPlan;

    if (typeof planOrId === "string") {
      const loaded = await this.stateManager.load(planOrId);
      if (!loaded) {
        throw new Error(`Plan not found: ${planOrId}`);
      }
      plan = loaded;
    } else {
      plan = planOrId;
    }

    this.currentPlan = plan;
    const result = await this.pipeline.execute(plan);
    await this.stateManager.save(result);
    this.currentPlan = null;

    return result;
  }

  /**
   * Resume a paused or failed plan
   */
  async resume(planId: string): Promise<ExecutionPlan> {
    const plan = await this.stateManager.load(planId);
    if (!plan) {
      throw new Error(`Plan not found: ${planId}`);
    }

    // Reset failed/cancelled tasks to pending
    for (const task of plan.tasks) {
      if (task.status === "failed" || task.status === "cancelled") {
        if (task.retryCount < task.retryConfig.maxRetries) {
          task.status = "pending";
        }
      }
    }

    plan.status = "ready";
    return this.executePlan(plan);
  }

  /**
   * Pause current execution
   */
  pause(): void {
    if (this.currentPlan) {
      this.currentPlan.status = "paused";
      this.pipeline.pause();
    }
  }

  /**
   * Resume paused execution
   */
  unpause(): void {
    if (this.currentPlan) {
      this.currentPlan.status = "executing";
      this.pipeline.resume();
    }
  }

  /**
   * Cancel current execution
   */
  cancel(): void {
    if (this.currentPlan) {
      this.currentPlan.status = "cancelled";
      this.pipeline.cancel();
    }
  }

  /**
   * Register an agent implementation
   */
  registerAgent(agent: IAgent): void {
    this.registry.register(agent);
  }

  /**
   * Get current execution plan
   */
  getCurrentPlan(): ExecutionPlan | null {
    return this.currentPlan;
  }

  /**
   * Get execution status summary
   */
  getStatus(): {
    isRunning: boolean;
    planId: string | null;
    progress: number;
    tasksCompleted: number;
    tasksFailed: number;
    tasksRemaining: number;
  } {
    if (!this.currentPlan) {
      return {
        isRunning: false,
        planId: null,
        progress: 0,
        tasksCompleted: 0,
        tasksFailed: 0,
        tasksRemaining: 0,
      };
    }

    const completed = this.currentPlan.tasks.filter((t) => t.status === "completed").length;
    const failed = this.currentPlan.tasks.filter((t) => t.status === "failed").length;
    const remaining = this.currentPlan.tasks.length - completed - failed;

    return {
      isRunning: this.currentPlan.status === "executing",
      planId: this.currentPlan.id,
      progress: this.currentPlan.progress,
      tasksCompleted: completed,
      tasksFailed: failed,
      tasksRemaining: remaining,
    };
  }

  /**
   * Load a saved plan
   */
  async loadPlan(planId: string): Promise<ExecutionPlan | null> {
    return this.stateManager.load(planId);
  }

  /**
   * List all saved plans
   */
  async listPlans(): Promise<string[]> {
    return this.stateManager.list();
  }

  /**
   * Delete a saved plan
   */
  async deletePlan(planId: string): Promise<boolean> {
    return this.stateManager.delete(planId);
  }

  /**
   * Get agent capabilities
   */
  getAgentCapabilities(agent: AgentType): AgentCapabilities {
    return this.registry.getCapabilities(agent);
  }

  /**
   * Update orchestrator configuration
   */
  updateConfig(config: Partial<OrchestratorConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ========================================================================
  // Event Typing (for TypeScript consumers)
  // ========================================================================

  override on<K extends keyof OrchestratorEvents>(
    event: K,
    listener: OrchestratorEvents[K]
  ): this {
    return super.on(event, listener as (...args: unknown[]) => void);
  }

  override once<K extends keyof OrchestratorEvents>(
    event: K,
    listener: OrchestratorEvents[K]
  ): this {
    return super.once(event, listener as (...args: unknown[]) => void);
  }

  override emit<K extends keyof OrchestratorEvents>(
    event: K,
    ...args: Parameters<OrchestratorEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  override off<K extends keyof OrchestratorEvents>(
    event: K,
    listener: OrchestratorEvents[K]
  ): this {
    return super.off(event, listener as (...args: unknown[]) => void);
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create an orchestrator with default configuration
 */
export function createOrchestrator(
  config?: Partial<OrchestratorConfig>
): Orchestrator {
  return new Orchestrator(config);
}

/**
 * Create an orchestrator optimized for code generation tasks
 */
export function createCodeOrchestrator(
  config?: Partial<OrchestratorConfig>
): Orchestrator {
  return new Orchestrator({
    ...config,
    defaultMode: "sequential",
    planningAgent: "claude",
    maxParallelTasks: 3,
  });
}

/**
 * Create an orchestrator optimized for research tasks
 */
export function createResearchOrchestrator(
  config?: Partial<OrchestratorConfig>
): Orchestrator {
  return new Orchestrator({
    ...config,
    defaultMode: "parallel",
    planningAgent: "gemini",
    usePlanningThinkingMode: true,
    maxParallelTasks: 10,
  });
}

// ============================================================================
// Exports
// ============================================================================

export {
  AgentRegistry,
  TaskRunner,
  ExecutionPipeline,
  GoalParser,
  StateManager,
  AGENT_CAPABILITIES,
  DEFAULT_ORCHESTRATOR_CONFIG,
  DEFAULT_RETRY_CONFIG,
  generateId,
  topologicalSort,
};

// Default export
export default Orchestrator;
