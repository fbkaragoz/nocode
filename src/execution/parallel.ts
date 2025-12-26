/**
 * Parallel Execution Handler
 *
 * Executes tasks concurrently while respecting dependencies and
 * concurrency limits. Uses a work-stealing approach for optimal
 * resource utilization.
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

/** Priority queue item for task scheduling */
interface QueueItem {
  taskId: string;
  priority: number;
  addedAt: number;
}

// ============================================================================
// Priority Mapping
// ============================================================================

const PRIORITY_MAP: Record<string, number> = {
  critical: 4,
  high: 3,
  normal: 2,
  low: 1,
};

// ============================================================================
// Parallel Executor
// ============================================================================

/**
 * Executes tasks in parallel while respecting dependencies.
 *
 * Features:
 * - Concurrent execution with configurable limits
 * - Dependency-aware scheduling
 * - Priority-based task ordering
 * - Real-time progress reporting
 * - Graceful cancellation support
 */
export class ParallelExecutor {
  private readonly engine: ExecutionEngine;

  constructor(engine: ExecutionEngine) {
    this.engine = engine;
  }

  /**
   * Execute tasks in parallel mode.
   */
  async execute(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    abortSignal: AbortSignal
  ): Promise<ExecutionResult[]> {
    const options = this.engine.getOptions();
    const maxConcurrency = options.maxConcurrency;
    const results: ExecutionResult[] = [];
    const completedTaskIds = new Set<string>();
    const runningTasks = new Map<string, Promise<ExecutionResult>>();
    const startTime = Date.now();

    // Build dependency graph
    const dependencyGraph = this.buildDependencyGraph(plan.tasks);
    const reverseDependencyGraph = this.buildReverseDependencyGraph(plan.tasks);

    // Initialize priority queue with tasks that have no dependencies
    const readyQueue = new PriorityQueue<QueueItem>((a, b) => {
      // Higher priority first, then earlier added
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.addedAt - b.addedAt;
    });

    // Add initial tasks (no dependencies)
    for (const task of plan.tasks) {
      if (task.dependencies.length === 0) {
        readyQueue.enqueue({
          taskId: task.id,
          priority: PRIORITY_MAP[task.priority] ?? 2,
          addedAt: Date.now(),
        });
        const state = taskStates.get(task.id);
        if (state) {
          state.status = 'queued';
        }
      }
    }

    // Emit initial progress
    this.emitProgress(plan, taskStates, runningTasks, startTime);

    // Main execution loop
    while (
      completedTaskIds.size < plan.tasks.length &&
      !abortSignal.aborted
    ) {
      // Start new tasks up to concurrency limit
      while (
        runningTasks.size < maxConcurrency &&
        !readyQueue.isEmpty() &&
        !abortSignal.aborted
      ) {
        const item = readyQueue.dequeue();
        if (!item) break;

        const state = taskStates.get(item.taskId);
        if (!state || state.status === 'completed' || state.status === 'failed') {
          continue;
        }

        // Collect dependency results
        const dependencyResults = new Map<string, ExecutionResult>();
        const deps = dependencyGraph.get(item.taskId) ?? [];
        for (const depId of deps) {
          const depState = taskStates.get(depId);
          if (depState?.result) {
            dependencyResults.set(depId, depState.result);
          }
        }

        // Create execution context
        const context = this.engine.createContext(
          dependencyResults,
          plan.globalContext ?? {},
          abortSignal
        );

        // Start task execution
        const taskPromise = this.executeTaskWithTracking(
          state,
          context,
          item.taskId,
          runningTasks,
          results,
          completedTaskIds,
          taskStates,
          reverseDependencyGraph,
          readyQueue,
          dependencyGraph,
          plan,
          startTime
        );

        runningTasks.set(item.taskId, taskPromise);
      }

      // Wait for at least one task to complete
      if (runningTasks.size > 0) {
        await Promise.race(runningTasks.values());
      } else if (readyQueue.isEmpty() && completedTaskIds.size < plan.tasks.length) {
        // No running tasks and no ready tasks, but not all completed
        // This means we have tasks blocked by failed dependencies
        const blockedTasks = plan.tasks.filter(
          t => !completedTaskIds.has(t.id) && !runningTasks.has(t.id)
        );

        for (const task of blockedTasks) {
          const state = taskStates.get(task.id);
          if (state) {
            state.status = 'cancelled';
            const result: ExecutionResult = {
              taskId: task.id,
              success: false,
              output: '',
              error: 'Task cancelled due to failed dependencies',
              duration: 0,
              filesModified: [],
              retryCount: 0,
              startedAt: new Date(),
              completedAt: new Date(),
            };
            state.result = result;
            results.push(result);
            completedTaskIds.add(task.id);
          }
        }
      }

      // Emit progress update
      this.emitProgress(plan, taskStates, runningTasks, startTime);
    }

    // Handle cancellation
    if (abortSignal.aborted) {
      for (const task of plan.tasks) {
        if (!completedTaskIds.has(task.id)) {
          const state = taskStates.get(task.id);
          if (state && state.status !== 'completed' && state.status !== 'failed') {
            state.status = 'cancelled';
            const result: ExecutionResult = {
              taskId: task.id,
              success: false,
              output: '',
              error: 'Execution cancelled',
              duration: 0,
              filesModified: [],
              retryCount: 0,
              startedAt: new Date(),
              completedAt: new Date(),
            };
            state.result = result;
            results.push(result);
          }
        }
      }
    }

    // Final progress emission
    this.emitProgress(plan, taskStates, runningTasks, startTime, true);

    return results;
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private async executeTaskWithTracking(
    state: TaskState,
    context: ExecutionContext,
    taskId: string,
    runningTasks: Map<string, Promise<ExecutionResult>>,
    results: ExecutionResult[],
    completedTaskIds: Set<string>,
    taskStates: Map<string, TaskState>,
    reverseDependencyGraph: Map<string, string[]>,
    readyQueue: PriorityQueue<QueueItem>,
    dependencyGraph: Map<string, string[]>,
    plan: ExecutionPlan,
    startTime: number
  ): Promise<ExecutionResult> {
    try {
      const result = await this.engine.executeTask(state.task, context, state);
      results.push(result);
      completedTaskIds.add(taskId);
      runningTasks.delete(taskId);

      // If successful, check if any dependent tasks can now be scheduled
      if (result.success || !this.engine.getOptions().stopOnFailure) {
        const dependents = reverseDependencyGraph.get(taskId) ?? [];
        for (const dependentId of dependents) {
          if (this.canScheduleTask(dependentId, taskStates, dependencyGraph)) {
            const dependentState = taskStates.get(dependentId);
            if (dependentState && dependentState.status === 'pending') {
              dependentState.status = 'queued';
              readyQueue.enqueue({
                taskId: dependentId,
                priority: PRIORITY_MAP[dependentState.task.priority] ?? 2,
                addedAt: Date.now(),
              });
            }
          }
        }
      }

      // Emit progress after task completion
      this.emitProgress(plan, taskStates, runningTasks, startTime);

      return result;
    } catch (error) {
      runningTasks.delete(taskId);
      throw error;
    }
  }

  private canScheduleTask(
    taskId: string,
    taskStates: Map<string, TaskState>,
    dependencyGraph: Map<string, string[]>
  ): boolean {
    const dependencies = dependencyGraph.get(taskId) ?? [];
    const options = this.engine.getOptions();

    for (const depId of dependencies) {
      const depState = taskStates.get(depId);
      if (!depState) return false;

      if (depState.status !== 'completed') {
        // If stopOnFailure is false, we can proceed even if dependency failed
        if (depState.status === 'failed' && !options.stopOnFailure) {
          continue;
        }
        return false;
      }

      // If dependency failed and stopOnFailure is true, don't schedule
      if (!depState.result?.success && options.stopOnFailure) {
        return false;
      }
    }

    return true;
  }

  private buildDependencyGraph(tasks: Task[]): Map<string, string[]> {
    const graph = new Map<string, string[]>();
    for (const task of tasks) {
      graph.set(task.id, [...task.dependencies]);
    }
    return graph;
  }

  private buildReverseDependencyGraph(tasks: Task[]): Map<string, string[]> {
    const graph = new Map<string, string[]>();

    // Initialize all tasks
    for (const task of tasks) {
      graph.set(task.id, []);
    }

    // Build reverse dependencies
    for (const task of tasks) {
      for (const depId of task.dependencies) {
        const dependents = graph.get(depId) ?? [];
        dependents.push(task.id);
        graph.set(depId, dependents);
      }
    }

    return graph;
  }

  private emitProgress(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    runningTasks: Map<string, Promise<ExecutionResult>>,
    startTime: number,
    isComplete = false
  ): void {
    const completed = [...taskStates.values()].filter(
      s => s.status === 'completed'
    ).length;
    const failed = [...taskStates.values()].filter(
      s => s.status === 'failed' || s.status === 'cancelled'
    ).length;
    const running = runningTasks.size;
    const total = plan.tasks.length;
    const elapsedTime = Date.now() - startTime;

    // Estimate remaining time based on average task duration
    let estimatedTimeRemaining: number | undefined;
    if (completed > 0 && completed < total) {
      const avgDuration = elapsedTime / completed;
      const remaining = total - completed - running;
      estimatedTimeRemaining = Math.round(avgDuration * remaining);
    }

    const progress: Progress = {
      totalTasks: total,
      completedTasks: completed,
      failedTasks: failed,
      runningTasks: running,
      percentage: Math.round((completed / total) * 100),
      runningTaskIds: [...runningTasks.keys()],
      estimatedTimeRemaining,
      elapsedTime,
      phase: isComplete ? 'complete' : running > 0 ? 'executing' : 'initializing',
    };

    this.engine.emitProgress(progress);
  }
}

// ============================================================================
// Priority Queue Implementation
// ============================================================================

/**
 * A simple priority queue implementation using a binary heap.
 */
class PriorityQueue<T> {
  private heap: T[] = [];
  private comparator: (a: T, b: T) => number;

  constructor(comparator: (a: T, b: T) => number) {
    this.comparator = comparator;
  }

  enqueue(item: T): void {
    this.heap.push(item);
    this.bubbleUp(this.heap.length - 1);
  }

  dequeue(): T | undefined {
    if (this.heap.length === 0) return undefined;

    const result = this.heap[0];
    const last = this.heap.pop();

    if (this.heap.length > 0 && last !== undefined) {
      this.heap[0] = last;
      this.bubbleDown(0);
    }

    return result;
  }

  peek(): T | undefined {
    return this.heap[0];
  }

  isEmpty(): boolean {
    return this.heap.length === 0;
  }

  size(): number {
    return this.heap.length;
  }

  private bubbleUp(index: number): void {
    while (index > 0) {
      const parentIndex = Math.floor((index - 1) / 2);
      const parent = this.heap[parentIndex];
      const current = this.heap[index];

      if (parent === undefined || current === undefined) break;

      if (this.comparator(current, parent) >= 0) break;

      this.heap[parentIndex] = current;
      this.heap[index] = parent;
      index = parentIndex;
    }
  }

  private bubbleDown(index: number): void {
    const length = this.heap.length;

    while (true) {
      const leftIndex = 2 * index + 1;
      const rightIndex = 2 * index + 2;
      let smallest = index;

      const current = this.heap[index];
      const left = this.heap[leftIndex];
      const right = this.heap[rightIndex];

      if (current === undefined) break;

      if (leftIndex < length && left !== undefined && this.comparator(left, current) < 0) {
        smallest = leftIndex;
      }

      const smallestItem = this.heap[smallest];
      if (
        rightIndex < length &&
        right !== undefined &&
        smallestItem !== undefined &&
        this.comparator(right, smallestItem) < 0
      ) {
        smallest = rightIndex;
      }

      if (smallest === index) break;

      const smallestValue = this.heap[smallest];
      if (smallestValue !== undefined) {
        this.heap[index] = smallestValue;
        this.heap[smallest] = current;
      }
      index = smallest;
    }
  }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a standalone parallel executor.
 * Note: Typically you would use the ExecutionEngine which manages this internally.
 */
export function createParallelExecutor(engine: ExecutionEngine): ParallelExecutor {
  return new ParallelExecutor(engine);
}
