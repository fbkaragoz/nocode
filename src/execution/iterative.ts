/**
 * Iterative (Chained) Execution Handler
 *
 * Executes tasks sequentially in a chain, where each task's output
 * becomes available as context for subsequent tasks. Ideal for
 * workflows requiring strict ordering and data flow between steps.
 */

import type {
  ExecutionEngine,
  ExecutionPlan,
  ExecutionResult,
  Task,
  Progress,
  ExecutionContext,
} from './engine.ts';

// ============================================================================
// Types
// ============================================================================

/** Internal task state for tracking execution */
interface TaskState {
  task: Task;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying';
  result?: ExecutionResult;
  retryCount: number;
  startedAt?: Date;
  error?: Error;
}

/** Chain execution options */
interface ChainOptions {
  /** Whether to pass previous task output as input to next task */
  chainOutputs: boolean;
  /** Transform function for output before passing to next task */
  outputTransform?: (output: string, taskId: string) => string;
  /** Whether to continue execution after a failure */
  continueOnFailure: boolean;
  /** Delay between task executions in milliseconds */
  interTaskDelay: number;
}

// ============================================================================
// Default Configuration
// ============================================================================

const DEFAULT_CHAIN_OPTIONS: ChainOptions = {
  chainOutputs: true,
  continueOnFailure: false,
  interTaskDelay: 0,
};

// ============================================================================
// Iterative Executor
// ============================================================================

/**
 * Executes tasks in a strict sequential order.
 *
 * Features:
 * - Sequential execution respecting task order
 * - Output chaining between tasks
 * - Accumulative context building
 * - Checkpoint and resume support
 * - Detailed progress tracking per step
 */
export class IterativeExecutor {
  private readonly engine: ExecutionEngine;
  private chainOptions: ChainOptions = DEFAULT_CHAIN_OPTIONS;

  constructor(engine: ExecutionEngine) {
    this.engine = engine;
  }

  /**
   * Configure chain execution options.
   */
  configure(options: Partial<ChainOptions>): void {
    this.chainOptions = { ...this.chainOptions, ...options };
  }

  /**
   * Execute tasks in iterative/chained mode.
   */
  async execute(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    abortSignal: AbortSignal
  ): Promise<ExecutionResult[]> {
    const results: ExecutionResult[] = [];
    const completedResults = new Map<string, ExecutionResult>();
    const startTime = Date.now();

    // Sort tasks topologically to respect dependencies
    const sortedTasks = this.topologicalSort(plan.tasks);

    this.emitProgress(plan, taskStates, 0, sortedTasks.length, startTime, null);

    for (let i = 0; i < sortedTasks.length; i++) {
      const task = sortedTasks[i];
      if (!task) continue;

      // Check for cancellation
      if (abortSignal.aborted) {
        // Mark remaining tasks as cancelled
        for (let j = i; j < sortedTasks.length; j++) {
          const remainingTask = sortedTasks[j];
          if (!remainingTask) continue;

          const state = taskStates.get(remainingTask.id);
          if (state) {
            state.status = 'cancelled';
            const cancelledResult: ExecutionResult = {
              taskId: remainingTask.id,
              success: false,
              output: '',
              error: 'Execution cancelled',
              duration: 0,
              filesModified: [],
              retryCount: 0,
              startedAt: new Date(),
              completedAt: new Date(),
            };
            state.result = cancelledResult;
            results.push(cancelledResult);
          }
        }
        break;
      }

      const state = taskStates.get(task.id);
      if (!state) continue;

      // Emit progress for current task
      this.emitProgress(plan, taskStates, i, sortedTasks.length, startTime, task.id);

      // Collect dependency results
      const dependencyResults = new Map<string, ExecutionResult>();
      for (const depId of task.dependencies) {
        const depResult = completedResults.get(depId);
        if (depResult) {
          dependencyResults.set(depId, depResult);
        }
      }

      // Build chained context
      const chainedContext = this.buildChainedContext(
        plan.globalContext ?? {},
        completedResults,
        sortedTasks.slice(0, i)
      );

      // Create execution context
      const context = this.engine.createContext(
        dependencyResults,
        chainedContext,
        abortSignal
      );

      // Execute the task
      const result = await this.engine.executeTask(task, context, state);
      results.push(result);
      completedResults.set(task.id, result);

      // Handle failure
      if (!result.success) {
        const options = this.engine.getOptions();
        if (options.stopOnFailure || !this.chainOptions.continueOnFailure) {
          // Cancel remaining tasks
          for (let j = i + 1; j < sortedTasks.length; j++) {
            const remainingTask = sortedTasks[j];
            if (!remainingTask) continue;

            const remainingState = taskStates.get(remainingTask.id);
            if (remainingState) {
              remainingState.status = 'cancelled';
              const cancelledResult: ExecutionResult = {
                taskId: remainingTask.id,
                success: false,
                output: '',
                error: `Cancelled due to failure of task: ${task.id}`,
                duration: 0,
                filesModified: [],
                retryCount: 0,
                startedAt: new Date(),
                completedAt: new Date(),
              };
              remainingState.result = cancelledResult;
              results.push(cancelledResult);
            }
          }
          break;
        }
      }

      // Apply inter-task delay if configured
      if (this.chainOptions.interTaskDelay > 0 && i < sortedTasks.length - 1) {
        await this.sleep(this.chainOptions.interTaskDelay);
      }
    }

    // Final progress update
    this.emitProgress(plan, taskStates, sortedTasks.length, sortedTasks.length, startTime, null, true);

    return results;
  }

  /**
   * Execute tasks with checkpointing support for resume capability.
   */
  async executeWithCheckpoints(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    abortSignal: AbortSignal,
    onCheckpoint: (checkpoint: IterativeCheckpoint) => Promise<void>
  ): Promise<ExecutionResult[]> {
    const results: ExecutionResult[] = [];
    const completedResults = new Map<string, ExecutionResult>();
    const startTime = Date.now();

    const sortedTasks = this.topologicalSort(plan.tasks);

    for (let i = 0; i < sortedTasks.length; i++) {
      const task = sortedTasks[i];
      if (!task) continue;

      if (abortSignal.aborted) break;

      const state = taskStates.get(task.id);
      if (!state) continue;

      // Skip already completed tasks (for resume)
      if (state.status === 'completed' && state.result) {
        results.push(state.result);
        completedResults.set(task.id, state.result);
        continue;
      }

      this.emitProgress(plan, taskStates, i, sortedTasks.length, startTime, task.id);

      const dependencyResults = new Map<string, ExecutionResult>();
      for (const depId of task.dependencies) {
        const depResult = completedResults.get(depId);
        if (depResult) {
          dependencyResults.set(depId, depResult);
        }
      }

      const chainedContext = this.buildChainedContext(
        plan.globalContext ?? {},
        completedResults,
        sortedTasks.slice(0, i)
      );

      const context = this.engine.createContext(
        dependencyResults,
        chainedContext,
        abortSignal
      );

      const result = await this.engine.executeTask(task, context, state);
      results.push(result);
      completedResults.set(task.id, result);

      // Save checkpoint after each task
      const checkpoint: IterativeCheckpoint = {
        planId: plan.id,
        completedTaskIndex: i,
        completedTaskIds: [...completedResults.keys()],
        results: [...results],
        timestamp: new Date(),
        canResume: result.success || this.chainOptions.continueOnFailure,
      };

      await onCheckpoint(checkpoint);

      if (!result.success && !this.chainOptions.continueOnFailure) {
        break;
      }
    }

    return results;
  }

  /**
   * Resume execution from a checkpoint.
   */
  async resumeFromCheckpoint(
    plan: ExecutionPlan,
    checkpoint: IterativeCheckpoint,
    abortSignal: AbortSignal
  ): Promise<ExecutionResult[]> {
    // Validate checkpoint matches plan
    if (checkpoint.planId !== plan.id) {
      throw new Error('Checkpoint plan ID does not match execution plan');
    }

    // Restore task states from checkpoint
    const taskStates = new Map<string, TaskState>();
    const completedSet = new Set(checkpoint.completedTaskIds);

    for (const task of plan.tasks) {
      const existingResult = checkpoint.results.find(r => r.taskId === task.id);
      taskStates.set(task.id, {
        task,
        status: existingResult ? 'completed' : 'pending',
        result: existingResult,
        retryCount: existingResult?.retryCount ?? 0,
      });
    }

    // Continue execution
    return this.execute(plan, taskStates, abortSignal);
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  /**
   * Perform topological sort on tasks based on dependencies.
   */
  private topologicalSort(tasks: Task[]): Task[] {
    const sorted: Task[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();
    const taskMap = new Map(tasks.map(t => [t.id, t]));

    const visit = (taskId: string): void => {
      if (visited.has(taskId)) return;
      if (visiting.has(taskId)) {
        throw new Error(`Circular dependency detected at task: ${taskId}`);
      }

      visiting.add(taskId);

      const task = taskMap.get(taskId);
      if (task) {
        for (const depId of task.dependencies) {
          visit(depId);
        }
        visited.add(taskId);
        visiting.delete(taskId);
        sorted.push(task);
      }
    };

    for (const task of tasks) {
      visit(task.id);
    }

    return sorted;
  }

  /**
   * Build context by chaining previous task outputs.
   */
  private buildChainedContext(
    globalContext: Record<string, unknown>,
    completedResults: Map<string, ExecutionResult>,
    previousTasks: Task[]
  ): Record<string, unknown> {
    const context: Record<string, unknown> = { ...globalContext };

    if (!this.chainOptions.chainOutputs) {
      return context;
    }

    // Add outputs from all completed tasks
    const taskOutputs: Record<string, string> = {};
    const taskMetadata: Record<string, unknown> = {};
    const allFilesModified: string[] = [];

    for (const task of previousTasks) {
      const result = completedResults.get(task.id);
      if (result) {
        let output = result.output;
        if (this.chainOptions.outputTransform) {
          output = this.chainOptions.outputTransform(output, task.id);
        }
        taskOutputs[task.id] = output;

        if (result.metadata) {
          taskMetadata[task.id] = result.metadata;
        }

        allFilesModified.push(...result.filesModified);
      }
    }

    // Build the accumulated output (last successful output)
    const lastTask = [...previousTasks].reverse().find(t => {
      const result = completedResults.get(t.id);
      return result?.success;
    });

    const lastOutput = lastTask ? completedResults.get(lastTask.id)?.output : undefined;

    context['__chain'] = {
      outputs: taskOutputs,
      metadata: taskMetadata,
      filesModified: [...new Set(allFilesModified)],
      lastOutput,
      taskCount: previousTasks.length,
      successCount: [...completedResults.values()].filter(r => r.success).length,
    };

    // Also expose individual task outputs at the top level for convenience
    context['__previousOutputs'] = taskOutputs;

    return context;
  }

  private emitProgress(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    currentIndex: number,
    totalTasks: number,
    startTime: number,
    currentTaskId: string | null,
    isComplete = false
  ): void {
    const completed = [...taskStates.values()].filter(
      s => s.status === 'completed'
    ).length;
    const failed = [...taskStates.values()].filter(
      s => s.status === 'failed' || s.status === 'cancelled'
    ).length;
    const elapsedTime = Date.now() - startTime;

    // Estimate remaining time
    let estimatedTimeRemaining: number | undefined;
    if (completed > 0 && completed < totalTasks) {
      const avgDuration = elapsedTime / completed;
      const remaining = totalTasks - completed;
      estimatedTimeRemaining = Math.round(avgDuration * remaining);
    }

    const progress: Progress = {
      totalTasks,
      completedTasks: completed,
      failedTasks: failed,
      runningTasks: currentTaskId ? 1 : 0,
      percentage: Math.round((completed / totalTasks) * 100),
      currentTaskId: currentTaskId ?? undefined,
      runningTaskIds: currentTaskId ? [currentTaskId] : [],
      estimatedTimeRemaining,
      elapsedTime,
      phase: isComplete ? 'complete' : currentTaskId ? 'executing' : 'initializing',
    };

    this.engine.emitProgress(progress);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ============================================================================
// Checkpoint Types
// ============================================================================

/** Checkpoint for resumable execution */
export interface IterativeCheckpoint {
  /** Plan identifier */
  planId: string;
  /** Index of the last completed task */
  completedTaskIndex: number;
  /** IDs of all completed tasks */
  completedTaskIds: string[];
  /** Results from completed tasks */
  results: ExecutionResult[];
  /** Checkpoint timestamp */
  timestamp: Date;
  /** Whether execution can be resumed */
  canResume: boolean;
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a standalone iterative executor.
 * Note: Typically you would use the ExecutionEngine which manages this internally.
 */
export function createIterativeExecutor(engine: ExecutionEngine): IterativeExecutor {
  return new IterativeExecutor(engine);
}
