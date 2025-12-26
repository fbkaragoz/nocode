/**
 * Execution Engine Module
 *
 * Multi-agent orchestration execution system with support for:
 * - Parallel execution with dependency resolution
 * - Iterative (chained) execution with output propagation
 * - Distributed execution across files and modules
 *
 * @module execution
 */

// ============================================================================
// Main Engine Exports
// ============================================================================

export {
  ExecutionEngine,
  createExecutionEngine,
  // Types
  type ExecutionMode,
  type TaskStatus,
  type TaskPriority,
  type Progress,
  type ExecutionResult,
  type AggregatedResult,
  type ExecutionOptions,
  type Task,
  type ExecutionPlan,
  type AgentExecutor,
  type ExecutionContext,
  type TaskExecutionOutput,
} from './engine.ts';

// ============================================================================
// Parallel Executor Exports
// ============================================================================

export {
  ParallelExecutor,
  createParallelExecutor,
} from './parallel.ts';

// ============================================================================
// Iterative Executor Exports
// ============================================================================

export {
  IterativeExecutor,
  createIterativeExecutor,
  type IterativeCheckpoint,
} from './iterative.ts';

// ============================================================================
// Distributed Executor Exports
// ============================================================================

export {
  DistributedExecutor,
  createDistributedExecutor,
  type DistributionStrategy,
  type WorkPartition,
  type DistributedOptions,
  type DistributionAnalysis,
} from './distributed.ts';

// ============================================================================
// Convenience Re-exports
// ============================================================================

/**
 * Default execution options for quick setup.
 */
export const DEFAULT_EXECUTION_OPTIONS = {
  maxConcurrency: 4,
  timeout: 300000,
  retries: 3,
  stopOnFailure: false,
  retryDelay: 1000,
  exponentialBackoff: true,
  backoffBase: 2,
  maxBackoffDelay: 30000,
  verbose: false,
} as const;

/**
 * Quick helper to create an execution plan.
 */
export function createExecutionPlan(
  id: string,
  name: string,
  mode: 'parallel' | 'iterative' | 'distributed',
  tasks: Array<{
    id: string;
    name: string;
    agentId: string;
    input: string;
    dependencies?: string[];
    priority?: 'low' | 'normal' | 'high' | 'critical';
    targets?: string[];
    timeout?: number;
    retries?: number;
    context?: Record<string, unknown>;
    description?: string;
    tags?: string[];
  }>,
  globalContext?: Record<string, unknown>
): import('./engine.ts').ExecutionPlan {
  return {
    id,
    name,
    mode,
    tasks: tasks.map(t => ({
      id: t.id,
      name: t.name,
      agentId: t.agentId,
      input: t.input,
      dependencies: t.dependencies ?? [],
      priority: t.priority ?? 'normal',
      targets: t.targets,
      timeout: t.timeout,
      retries: t.retries,
      context: t.context,
      description: t.description,
      tags: t.tags,
    })),
    globalContext,
  };
}

/**
 * Quick helper to create a simple agent executor for testing.
 */
export function createMockAgentExecutor(
  id: string,
  handler: (task: import('./engine.ts').Task) => Promise<{ output: string; filesModified?: string[] }>
): import('./engine.ts').AgentExecutor {
  return {
    getId: () => id,
    canHandle: () => true,
    execute: async (task) => {
      const result = await handler(task);
      return {
        output: result.output,
        filesModified: result.filesModified ?? [],
      };
    },
  };
}
