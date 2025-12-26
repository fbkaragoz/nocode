/**
 * Main Execution Engine for Multi-Agent Orchestration
 *
 * Provides the core execution infrastructure for running tasks across
 * multiple agents with support for parallel, iterative, and distributed
 * execution modes.
 */

import { ParallelExecutor } from './parallel.ts';
import { IterativeExecutor } from './iterative.ts';
import { DistributedExecutor } from './distributed.ts';

// ============================================================================
// Type Definitions
// ============================================================================

/** Execution modes supported by the engine */
export type ExecutionMode = 'parallel' | 'iterative' | 'distributed';

/** Task status throughout its lifecycle */
export type TaskStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'retrying';

/** Priority levels for task scheduling */
export type TaskPriority = 'low' | 'normal' | 'high' | 'critical';

/** Progress information for real-time monitoring */
export interface Progress {
  /** Total number of tasks in the plan */
  totalTasks: number;
  /** Number of completed tasks */
  completedTasks: number;
  /** Number of failed tasks */
  failedTasks: number;
  /** Number of currently running tasks */
  runningTasks: number;
  /** Current progress percentage (0-100) */
  percentage: number;
  /** ID of the currently executing task (if single) */
  currentTaskId?: string;
  /** IDs of all currently running tasks */
  runningTaskIds: string[];
  /** Estimated time remaining in milliseconds */
  estimatedTimeRemaining?: number;
  /** Elapsed time in milliseconds */
  elapsedTime: number;
  /** Current execution phase */
  phase: 'initializing' | 'executing' | 'finalizing' | 'complete';
}

/** Result of a single task execution */
export interface ExecutionResult {
  /** Unique identifier for the task */
  taskId: string;
  /** Whether the task completed successfully */
  success: boolean;
  /** Output produced by the task */
  output: string;
  /** Error message if the task failed */
  error?: string;
  /** Execution duration in milliseconds */
  duration: number;
  /** List of files modified during execution */
  filesModified: string[];
  /** Number of retry attempts made */
  retryCount: number;
  /** Timestamp when execution started */
  startedAt: Date;
  /** Timestamp when execution completed */
  completedAt: Date;
  /** Additional metadata from the task */
  metadata?: Record<string, unknown>;
}

/** Aggregated results from an entire execution plan */
export interface AggregatedResult {
  /** Overall success status */
  success: boolean;
  /** Total execution duration in milliseconds */
  totalDuration: number;
  /** Individual task results */
  results: ExecutionResult[];
  /** Summary statistics */
  summary: {
    total: number;
    succeeded: number;
    failed: number;
    cancelled: number;
    totalRetries: number;
  };
  /** All files modified across all tasks */
  allFilesModified: string[];
  /** Execution started timestamp */
  startedAt: Date;
  /** Execution completed timestamp */
  completedAt: Date;
  /** Errors encountered during execution */
  errors: Array<{ taskId: string; error: string }>;
}

/** Configuration options for execution */
export interface ExecutionOptions {
  /** Maximum number of concurrent task executions */
  maxConcurrency: number;
  /** Timeout for individual tasks in milliseconds */
  timeout: number;
  /** Number of retry attempts for failed tasks */
  retries: number;
  /** Callback for progress updates */
  onProgress?: (progress: Progress) => void;
  /** Callback when a task starts */
  onTaskStart?: (taskId: string) => void;
  /** Callback when a task completes */
  onTaskComplete?: (result: ExecutionResult) => void;
  /** Callback when a task fails */
  onTaskError?: (taskId: string, error: Error) => void;
  /** Whether to stop execution on first failure */
  stopOnFailure?: boolean;
  /** Delay between retries in milliseconds */
  retryDelay?: number;
  /** Whether to use exponential backoff for retries */
  exponentialBackoff?: boolean;
  /** Base delay for exponential backoff */
  backoffBase?: number;
  /** Maximum delay for exponential backoff */
  maxBackoffDelay?: number;
  /** Enable detailed logging */
  verbose?: boolean;
}

/** A single task to be executed */
export interface Task {
  /** Unique identifier for the task */
  id: string;
  /** Human-readable name for the task */
  name: string;
  /** Detailed description of what the task does */
  description?: string;
  /** The agent responsible for executing this task */
  agentId: string;
  /** Input data/prompt for the task */
  input: string;
  /** IDs of tasks that must complete before this one */
  dependencies: string[];
  /** Task priority for scheduling */
  priority: TaskPriority;
  /** Target files or modules for distributed execution */
  targets?: string[];
  /** Task-specific timeout override */
  timeout?: number;
  /** Task-specific retry count override */
  retries?: number;
  /** Additional context for the task */
  context?: Record<string, unknown>;
  /** Tags for categorization and filtering */
  tags?: string[];
}

/** An execution plan containing tasks to be executed */
export interface ExecutionPlan {
  /** Unique identifier for the plan */
  id: string;
  /** Human-readable name for the plan */
  name: string;
  /** Execution mode to use */
  mode: ExecutionMode;
  /** Tasks to execute */
  tasks: Task[];
  /** Global context available to all tasks */
  globalContext?: Record<string, unknown>;
  /** Plan-level metadata */
  metadata?: Record<string, unknown>;
}

/** Internal task state tracking */
interface TaskState {
  task: Task;
  status: TaskStatus;
  result?: ExecutionResult;
  retryCount: number;
  startedAt?: Date;
  error?: Error;
}

/** Agent executor interface for task execution */
export interface AgentExecutor {
  /** Execute a task and return the result */
  execute(task: Task, context: ExecutionContext): Promise<TaskExecutionOutput>;
  /** Check if the agent can handle this task */
  canHandle(task: Task): boolean;
  /** Get agent identifier */
  getId(): string;
}

/** Context passed to agents during execution */
export interface ExecutionContext {
  /** Results from dependency tasks */
  dependencyResults: Map<string, ExecutionResult>;
  /** Global context from the plan */
  globalContext: Record<string, unknown>;
  /** Abort signal for cancellation */
  abortSignal: AbortSignal;
  /** Execution options */
  options: ExecutionOptions;
}

/** Output from a task execution */
export interface TaskExecutionOutput {
  /** Output content */
  output: string;
  /** Files modified during execution */
  filesModified: string[];
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Default Configuration
// ============================================================================

const DEFAULT_OPTIONS: ExecutionOptions = {
  maxConcurrency: 4,
  timeout: 300000, // 5 minutes
  retries: 3,
  stopOnFailure: false,
  retryDelay: 1000,
  exponentialBackoff: true,
  backoffBase: 2,
  maxBackoffDelay: 30000,
  verbose: false,
};

// ============================================================================
// Execution Engine
// ============================================================================

/**
 * Main execution engine for multi-agent orchestration.
 *
 * Coordinates task execution across multiple agents with support for
 * different execution modes, dependency resolution, retries, and
 * real-time progress monitoring.
 */
export class ExecutionEngine {
  private readonly agents: Map<string, AgentExecutor> = new Map();
  private readonly options: ExecutionOptions;
  private readonly parallelExecutor: ParallelExecutor;
  private readonly iterativeExecutor: IterativeExecutor;
  private readonly distributedExecutor: DistributedExecutor;
  private abortController: AbortController | null = null;
  private isRunning = false;

  constructor(options: Partial<ExecutionOptions> = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
    this.parallelExecutor = new ParallelExecutor(this);
    this.iterativeExecutor = new IterativeExecutor(this);
    this.distributedExecutor = new DistributedExecutor(this);
  }

  // ==========================================================================
  // Agent Management
  // ==========================================================================

  /**
   * Register an agent executor with the engine.
   */
  registerAgent(agent: AgentExecutor): void {
    this.agents.set(agent.getId(), agent);
    this.log(`Registered agent: ${agent.getId()}`);
  }

  /**
   * Unregister an agent from the engine.
   */
  unregisterAgent(agentId: string): boolean {
    const removed = this.agents.delete(agentId);
    if (removed) {
      this.log(`Unregistered agent: ${agentId}`);
    }
    return removed;
  }

  /**
   * Get a registered agent by ID.
   */
  getAgent(agentId: string): AgentExecutor | undefined {
    return this.agents.get(agentId);
  }

  /**
   * Get all registered agents.
   */
  getAgents(): Map<string, AgentExecutor> {
    return new Map(this.agents);
  }

  // ==========================================================================
  // Execution
  // ==========================================================================

  /**
   * Execute an execution plan and return aggregated results.
   */
  async execute(plan: ExecutionPlan): Promise<AggregatedResult> {
    if (this.isRunning) {
      throw new Error('Execution engine is already running');
    }

    this.isRunning = true;
    this.abortController = new AbortController();
    const startedAt = new Date();

    this.log(`Starting execution of plan: ${plan.name} (${plan.id})`);
    this.log(`Mode: ${plan.mode}, Tasks: ${plan.tasks.length}`);

    try {
      // Validate the plan
      this.validatePlan(plan);

      // Initialize task states
      const taskStates = this.initializeTaskStates(plan.tasks);

      // Execute based on mode
      let results: ExecutionResult[];

      switch (plan.mode) {
        case 'parallel':
          results = await this.parallelExecutor.execute(
            plan,
            taskStates,
            this.abortController.signal
          );
          break;

        case 'iterative':
          results = await this.iterativeExecutor.execute(
            plan,
            taskStates,
            this.abortController.signal
          );
          break;

        case 'distributed':
          results = await this.distributedExecutor.execute(
            plan,
            taskStates,
            this.abortController.signal
          );
          break;

        default:
          throw new Error(`Unknown execution mode: ${plan.mode}`);
      }

      const completedAt = new Date();
      return this.aggregateResults(results, startedAt, completedAt);

    } catch (error) {
      const completedAt = new Date();
      this.log(`Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`);

      return {
        success: false,
        totalDuration: completedAt.getTime() - startedAt.getTime(),
        results: [],
        summary: {
          total: plan.tasks.length,
          succeeded: 0,
          failed: plan.tasks.length,
          cancelled: 0,
          totalRetries: 0,
        },
        allFilesModified: [],
        startedAt,
        completedAt,
        errors: [{
          taskId: 'engine',
          error: error instanceof Error ? error.message : String(error),
        }],
      };
    } finally {
      this.isRunning = false;
      this.abortController = null;
    }
  }

  /**
   * Cancel the current execution.
   */
  cancel(): void {
    if (this.abortController) {
      this.log('Cancelling execution...');
      this.abortController.abort();
    }
  }

  /**
   * Check if the engine is currently executing.
   */
  isExecuting(): boolean {
    return this.isRunning;
  }

  // ==========================================================================
  // Task Execution (Used by mode executors)
  // ==========================================================================

  /**
   * Execute a single task with retry logic.
   * This method is called by the mode-specific executors.
   */
  async executeTask(
    task: Task,
    context: ExecutionContext,
    state: TaskState
  ): Promise<ExecutionResult> {
    const taskTimeout = task.timeout ?? this.options.timeout;
    const maxRetries = task.retries ?? this.options.retries;
    const startedAt = new Date();

    state.status = 'running';
    state.startedAt = startedAt;
    this.options.onTaskStart?.(task.id);

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      if (context.abortSignal.aborted) {
        return this.createCancelledResult(task, startedAt, attempt);
      }

      if (attempt > 0) {
        state.status = 'retrying';
        const delay = this.calculateRetryDelay(attempt);
        this.log(`Retrying task ${task.id} (attempt ${attempt + 1}/${maxRetries + 1}) after ${delay}ms`);
        await this.sleep(delay);
      }

      try {
        const agent = this.agents.get(task.agentId);
        if (!agent) {
          throw new Error(`Agent not found: ${task.agentId}`);
        }

        if (!agent.canHandle(task)) {
          throw new Error(`Agent ${task.agentId} cannot handle task ${task.id}`);
        }

        // Execute with timeout
        const output = await this.executeWithTimeout(
          () => agent.execute(task, context),
          taskTimeout
        );

        const completedAt = new Date();
        const result: ExecutionResult = {
          taskId: task.id,
          success: true,
          output: output.output,
          duration: completedAt.getTime() - startedAt.getTime(),
          filesModified: output.filesModified,
          retryCount: attempt,
          startedAt,
          completedAt,
          metadata: output.metadata,
        };

        state.status = 'completed';
        state.result = result;
        this.options.onTaskComplete?.(result);
        this.log(`Task ${task.id} completed successfully`);

        return result;

      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        state.error = lastError;
        this.log(`Task ${task.id} failed: ${lastError.message}`);
        this.options.onTaskError?.(task.id, lastError);

        // Check if we should stop on failure
        if (this.options.stopOnFailure) {
          break;
        }
      }
    }

    // All retries exhausted
    const completedAt = new Date();
    const result: ExecutionResult = {
      taskId: task.id,
      success: false,
      output: '',
      error: lastError?.message ?? 'Unknown error',
      duration: completedAt.getTime() - startedAt.getTime(),
      filesModified: [],
      retryCount: maxRetries,
      startedAt,
      completedAt,
    };

    state.status = 'failed';
    state.result = result;
    this.options.onTaskComplete?.(result);

    return result;
  }

  /**
   * Get the current execution options.
   */
  getOptions(): ExecutionOptions {
    return { ...this.options };
  }

  /**
   * Create an execution context for a task.
   */
  createContext(
    dependencyResults: Map<string, ExecutionResult>,
    globalContext: Record<string, unknown>,
    abortSignal: AbortSignal
  ): ExecutionContext {
    return {
      dependencyResults,
      globalContext,
      abortSignal,
      options: this.options,
    };
  }

  /**
   * Emit a progress update.
   */
  emitProgress(progress: Progress): void {
    this.options.onProgress?.(progress);
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private validatePlan(plan: ExecutionPlan): void {
    if (!plan.id) {
      throw new Error('Execution plan must have an id');
    }

    if (!plan.tasks || plan.tasks.length === 0) {
      throw new Error('Execution plan must have at least one task');
    }

    const taskIds = new Set<string>();
    for (const task of plan.tasks) {
      if (!task.id) {
        throw new Error('All tasks must have an id');
      }

      if (taskIds.has(task.id)) {
        throw new Error(`Duplicate task id: ${task.id}`);
      }
      taskIds.add(task.id);

      if (!task.agentId) {
        throw new Error(`Task ${task.id} must have an agentId`);
      }

      if (!this.agents.has(task.agentId)) {
        throw new Error(`Agent not registered: ${task.agentId}`);
      }

      // Validate dependencies exist
      for (const depId of task.dependencies) {
        if (!taskIds.has(depId) && !plan.tasks.some(t => t.id === depId)) {
          throw new Error(`Task ${task.id} has unknown dependency: ${depId}`);
        }
      }
    }

    // Check for circular dependencies
    this.detectCircularDependencies(plan.tasks);
  }

  private detectCircularDependencies(tasks: Task[]): void {
    const taskMap = new Map(tasks.map(t => [t.id, t]));
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycle = (taskId: string): boolean => {
      visited.add(taskId);
      recursionStack.add(taskId);

      const task = taskMap.get(taskId);
      if (task) {
        for (const depId of task.dependencies) {
          if (!visited.has(depId)) {
            if (hasCycle(depId)) {
              return true;
            }
          } else if (recursionStack.has(depId)) {
            return true;
          }
        }
      }

      recursionStack.delete(taskId);
      return false;
    };

    for (const task of tasks) {
      if (!visited.has(task.id)) {
        if (hasCycle(task.id)) {
          throw new Error(`Circular dependency detected involving task: ${task.id}`);
        }
      }
    }
  }

  private initializeTaskStates(tasks: Task[]): Map<string, TaskState> {
    const states = new Map<string, TaskState>();

    for (const task of tasks) {
      states.set(task.id, {
        task,
        status: 'pending',
        retryCount: 0,
      });
    }

    return states;
  }

  private async executeWithTimeout<T>(
    fn: () => Promise<T>,
    timeout: number
  ): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Task execution timed out')), timeout);
      }),
    ]);
  }

  private calculateRetryDelay(attempt: number): number {
    if (!this.options.exponentialBackoff) {
      return this.options.retryDelay ?? 1000;
    }

    const base = this.options.backoffBase ?? 2;
    const baseDelay = this.options.retryDelay ?? 1000;
    const maxDelay = this.options.maxBackoffDelay ?? 30000;

    const delay = baseDelay * Math.pow(base, attempt - 1);
    return Math.min(delay, maxDelay);
  }

  private createCancelledResult(task: Task, startedAt: Date, retryCount: number): ExecutionResult {
    const completedAt = new Date();
    return {
      taskId: task.id,
      success: false,
      output: '',
      error: 'Execution cancelled',
      duration: completedAt.getTime() - startedAt.getTime(),
      filesModified: [],
      retryCount,
      startedAt,
      completedAt,
    };
  }

  private aggregateResults(
    results: ExecutionResult[],
    startedAt: Date,
    completedAt: Date
  ): AggregatedResult {
    const succeeded = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success && r.error !== 'Execution cancelled').length;
    const cancelled = results.filter(r => r.error === 'Execution cancelled').length;
    const totalRetries = results.reduce((sum, r) => sum + r.retryCount, 0);

    const allFilesModified = [...new Set(
      results.flatMap(r => r.filesModified)
    )];

    const errors = results
      .filter(r => !r.success && r.error)
      .map(r => ({ taskId: r.taskId, error: r.error! }));

    return {
      success: failed === 0 && cancelled === 0,
      totalDuration: completedAt.getTime() - startedAt.getTime(),
      results,
      summary: {
        total: results.length,
        succeeded,
        failed,
        cancelled,
        totalRetries,
      },
      allFilesModified,
      startedAt,
      completedAt,
      errors,
    };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private log(message: string): void {
    if (this.options.verbose) {
      console.log(`[ExecutionEngine] ${message}`);
    }
  }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a new execution engine instance with the given options.
 */
export function createExecutionEngine(
  options?: Partial<ExecutionOptions>
): ExecutionEngine {
  return new ExecutionEngine(options);
}
