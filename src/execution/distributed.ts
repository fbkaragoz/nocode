/**
 * Distributed Execution Handler
 *
 * Executes tasks distributed across files, modules, or workspaces.
 * Supports work partitioning, load balancing, and coordination
 * across multiple execution units.
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

/** Distribution strategy for partitioning work */
export type DistributionStrategy =
  | 'round-robin'
  | 'least-loaded'
  | 'file-affinity'
  | 'module-affinity'
  | 'random';

/** Work partition representing a subset of tasks */
export interface WorkPartition {
  /** Unique identifier for this partition */
  id: string;
  /** Name/description of the partition */
  name: string;
  /** Tasks assigned to this partition */
  tasks: Task[];
  /** Target files or modules for this partition */
  targets: string[];
  /** Partition-specific metadata */
  metadata?: Record<string, unknown>;
}

/** Distributed execution options */
export interface DistributedOptions {
  /** Strategy for distributing work */
  strategy: DistributionStrategy;
  /** Maximum partitions (0 = auto-detect based on targets) */
  maxPartitions: number;
  /** Concurrency limit per partition */
  concurrencyPerPartition: number;
  /** Whether to balance load dynamically */
  dynamicLoadBalancing: boolean;
  /** Timeout for partition completion */
  partitionTimeout: number;
  /** Whether to aggregate results across partitions */
  aggregateResults: boolean;
  /** File patterns to consider for distribution */
  filePatterns?: string[];
  /** Module patterns to consider for distribution */
  modulePatterns?: string[];
}

/** Partition execution status */
interface PartitionStatus {
  partition: WorkPartition;
  status: 'pending' | 'running' | 'completed' | 'failed';
  completedTasks: number;
  failedTasks: number;
  startedAt?: Date;
  completedAt?: Date;
  results: ExecutionResult[];
}

// ============================================================================
// Default Configuration
// ============================================================================

const DEFAULT_DISTRIBUTED_OPTIONS: DistributedOptions = {
  strategy: 'file-affinity',
  maxPartitions: 0,
  concurrencyPerPartition: 2,
  dynamicLoadBalancing: true,
  partitionTimeout: 600000, // 10 minutes
  aggregateResults: true,
};

// ============================================================================
// Distributed Executor
// ============================================================================

/**
 * Executes tasks in a distributed manner across files or modules.
 *
 * Features:
 * - Intelligent work partitioning
 * - Multiple distribution strategies
 * - File and module affinity
 * - Dynamic load balancing
 * - Partition-level progress tracking
 * - Cross-partition dependency resolution
 */
export class DistributedExecutor {
  private readonly engine: ExecutionEngine;
  private distributedOptions: DistributedOptions = DEFAULT_DISTRIBUTED_OPTIONS;

  constructor(engine: ExecutionEngine) {
    this.engine = engine;
  }

  /**
   * Configure distributed execution options.
   */
  configure(options: Partial<DistributedOptions>): void {
    this.distributedOptions = { ...this.distributedOptions, ...options };
  }

  /**
   * Execute tasks in distributed mode.
   */
  async execute(
    plan: ExecutionPlan,
    taskStates: Map<string, TaskState>,
    abortSignal: AbortSignal
  ): Promise<ExecutionResult[]> {
    const startTime = Date.now();
    const options = this.engine.getOptions();

    // Create partitions based on task targets
    const partitions = this.createPartitions(plan.tasks);

    if (partitions.length === 0) {
      // Fall back to single partition if no targets defined
      partitions.push({
        id: 'default',
        name: 'Default Partition',
        tasks: plan.tasks,
        targets: [],
      });
    }

    // Initialize partition statuses
    const partitionStatuses = new Map<string, PartitionStatus>(
      partitions.map(p => [p.id, {
        partition: p,
        status: 'pending',
        completedTasks: 0,
        failedTasks: 0,
        results: [],
      }])
    );

    // Build cross-partition dependency map
    const crossPartitionDeps = this.buildCrossPartitionDependencies(partitions, plan.tasks);

    // Execute partitions with managed concurrency
    const results = await this.executePartitions(
      partitions,
      partitionStatuses,
      crossPartitionDeps,
      taskStates,
      plan,
      abortSignal,
      startTime
    );

    return results;
  }

  /**
   * Get current partition information for monitoring.
   */
  analyzeDistribution(tasks: Task[]): DistributionAnalysis {
    const partitions = this.createPartitions(tasks);
    const targetDistribution = new Map<string, number>();
    const unassignedTasks: string[] = [];

    for (const task of tasks) {
      if (!task.targets || task.targets.length === 0) {
        unassignedTasks.push(task.id);
      } else {
        for (const target of task.targets) {
          targetDistribution.set(target, (targetDistribution.get(target) ?? 0) + 1);
        }
      }
    }

    return {
      totalTasks: tasks.length,
      partitionCount: partitions.length,
      partitions: partitions.map(p => ({
        id: p.id,
        name: p.name,
        taskCount: p.tasks.length,
        targets: p.targets,
      })),
      targetDistribution: Object.fromEntries(targetDistribution),
      unassignedTasks,
      estimatedParallelism: Math.min(
        partitions.length * this.distributedOptions.concurrencyPerPartition,
        this.engine.getOptions().maxConcurrency
      ),
    };
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  /**
   * Create work partitions based on task targets and distribution strategy.
   */
  private createPartitions(tasks: Task[]): WorkPartition[] {
    const strategy = this.distributedOptions.strategy;

    switch (strategy) {
      case 'file-affinity':
        return this.createFileAffinityPartitions(tasks);
      case 'module-affinity':
        return this.createModuleAffinityPartitions(tasks);
      case 'round-robin':
        return this.createRoundRobinPartitions(tasks);
      case 'least-loaded':
        return this.createLeastLoadedPartitions(tasks);
      case 'random':
        return this.createRandomPartitions(tasks);
      default:
        return this.createFileAffinityPartitions(tasks);
    }
  }

  /**
   * Create partitions based on file affinity.
   */
  private createFileAffinityPartitions(tasks: Task[]): WorkPartition[] {
    const fileGroups = new Map<string, Task[]>();
    const noTargetTasks: Task[] = [];

    for (const task of tasks) {
      if (!task.targets || task.targets.length === 0) {
        noTargetTasks.push(task);
        continue;
      }

      // Group by primary target (first target)
      const primaryTarget = task.targets[0];
      if (primaryTarget) {
        const group = fileGroups.get(primaryTarget) ?? [];
        group.push(task);
        fileGroups.set(primaryTarget, group);
      }
    }

    const partitions: WorkPartition[] = [];

    // Create partition for each file group
    for (const [file, fileTasks] of fileGroups) {
      partitions.push({
        id: `file-${this.hashString(file)}`,
        name: `File: ${this.extractFileName(file)}`,
        tasks: fileTasks,
        targets: [file],
      });
    }

    // Add tasks without targets to a general partition
    if (noTargetTasks.length > 0) {
      partitions.push({
        id: 'general',
        name: 'General Tasks',
        tasks: noTargetTasks,
        targets: [],
      });
    }

    // Limit partitions if configured
    if (this.distributedOptions.maxPartitions > 0 && partitions.length > this.distributedOptions.maxPartitions) {
      return this.mergePartitions(partitions, this.distributedOptions.maxPartitions);
    }

    return partitions;
  }

  /**
   * Create partitions based on module affinity.
   */
  private createModuleAffinityPartitions(tasks: Task[]): WorkPartition[] {
    const moduleGroups = new Map<string, Task[]>();
    const noModuleTasks: Task[] = [];

    for (const task of tasks) {
      if (!task.targets || task.targets.length === 0) {
        noModuleTasks.push(task);
        continue;
      }

      // Extract module from path (e.g., src/components -> components)
      const moduleName = this.extractModuleName(task.targets[0] ?? '');
      if (moduleName) {
        const group = moduleGroups.get(moduleName) ?? [];
        group.push(task);
        moduleGroups.set(moduleName, group);
      } else {
        noModuleTasks.push(task);
      }
    }

    const partitions: WorkPartition[] = [];

    for (const [module, moduleTasks] of moduleGroups) {
      const targets = [...new Set(moduleTasks.flatMap(t => t.targets ?? []))];
      partitions.push({
        id: `module-${module}`,
        name: `Module: ${module}`,
        tasks: moduleTasks,
        targets,
      });
    }

    if (noModuleTasks.length > 0) {
      partitions.push({
        id: 'unassigned',
        name: 'Unassigned Tasks',
        tasks: noModuleTasks,
        targets: [],
      });
    }

    return partitions;
  }

  /**
   * Create partitions using round-robin distribution.
   */
  private createRoundRobinPartitions(tasks: Task[]): WorkPartition[] {
    const numPartitions = this.distributedOptions.maxPartitions || Math.min(tasks.length, 4);
    const partitions: WorkPartition[] = [];

    for (let i = 0; i < numPartitions; i++) {
      partitions.push({
        id: `partition-${i}`,
        name: `Partition ${i + 1}`,
        tasks: [],
        targets: [],
      });
    }

    // Distribute tasks round-robin
    for (let i = 0; i < tasks.length; i++) {
      const task = tasks[i];
      const partition = partitions[i % numPartitions];
      if (task && partition) {
        partition.tasks.push(task);
        if (task.targets) {
          partition.targets.push(...task.targets);
        }
      }
    }

    // Deduplicate targets
    for (const partition of partitions) {
      partition.targets = [...new Set(partition.targets)];
    }

    // Remove empty partitions
    return partitions.filter(p => p.tasks.length > 0);
  }

  /**
   * Create partitions using least-loaded strategy (based on task complexity).
   */
  private createLeastLoadedPartitions(tasks: Task[]): WorkPartition[] {
    const numPartitions = this.distributedOptions.maxPartitions || Math.min(tasks.length, 4);
    const partitions: WorkPartition[] = [];
    const partitionLoads: number[] = [];

    for (let i = 0; i < numPartitions; i++) {
      partitions.push({
        id: `partition-${i}`,
        name: `Partition ${i + 1}`,
        tasks: [],
        targets: [],
      });
      partitionLoads.push(0);
    }

    // Sort tasks by estimated complexity (dependencies count as weight)
    const sortedTasks = [...tasks].sort((a, b) => b.dependencies.length - a.dependencies.length);

    // Assign each task to the least loaded partition
    for (const task of sortedTasks) {
      let minLoadIndex = 0;
      let minLoad = partitionLoads[0] ?? 0;

      for (let i = 1; i < numPartitions; i++) {
        const load = partitionLoads[i];
        if (load !== undefined && load < minLoad) {
          minLoad = load;
          minLoadIndex = i;
        }
      }

      const partition = partitions[minLoadIndex];
      if (partition) {
        partition.tasks.push(task);
        if (task.targets) {
          partition.targets.push(...task.targets);
        }
        // Weight: 1 base + 0.5 per dependency
        partitionLoads[minLoadIndex] = (partitionLoads[minLoadIndex] ?? 0) + 1 + task.dependencies.length * 0.5;
      }
    }

    // Deduplicate targets
    for (const partition of partitions) {
      partition.targets = [...new Set(partition.targets)];
    }

    return partitions.filter(p => p.tasks.length > 0);
  }

  /**
   * Create partitions using random distribution.
   */
  private createRandomPartitions(tasks: Task[]): WorkPartition[] {
    const numPartitions = this.distributedOptions.maxPartitions || Math.min(tasks.length, 4);
    const partitions: WorkPartition[] = [];

    for (let i = 0; i < numPartitions; i++) {
      partitions.push({
        id: `partition-${i}`,
        name: `Partition ${i + 1}`,
        tasks: [],
        targets: [],
      });
    }

    // Shuffle tasks and distribute
    const shuffled = [...tasks].sort(() => Math.random() - 0.5);

    for (let i = 0; i < shuffled.length; i++) {
      const task = shuffled[i];
      const partition = partitions[i % numPartitions];
      if (task && partition) {
        partition.tasks.push(task);
        if (task.targets) {
          partition.targets.push(...task.targets);
        }
      }
    }

    for (const partition of partitions) {
      partition.targets = [...new Set(partition.targets)];
    }

    return partitions.filter(p => p.tasks.length > 0);
  }

  /**
   * Merge partitions to fit within the maximum limit.
   */
  private mergePartitions(partitions: WorkPartition[], maxPartitions: number): WorkPartition[] {
    if (partitions.length <= maxPartitions) {
      return partitions;
    }

    // Sort by task count (ascending) and merge smallest
    const sorted = [...partitions].sort((a, b) => a.tasks.length - b.tasks.length);
    const merged: WorkPartition[] = [];

    while (sorted.length > maxPartitions) {
      const smallest = sorted.shift();
      const secondSmallest = sorted.shift();

      if (smallest && secondSmallest) {
        const combined: WorkPartition = {
          id: `merged-${smallest.id}-${secondSmallest.id}`,
          name: `${smallest.name} + ${secondSmallest.name}`,
          tasks: [...smallest.tasks, ...secondSmallest.tasks],
          targets: [...new Set([...smallest.targets, ...secondSmallest.targets])],
        };
        sorted.push(combined);
        sorted.sort((a, b) => a.tasks.length - b.tasks.length);
      }
    }

    return sorted;
  }

  /**
   * Build cross-partition dependency map.
   */
  private buildCrossPartitionDependencies(
    partitions: WorkPartition[],
    tasks: Task[]
  ): Map<string, Set<string>> {
    // Map task ID to partition ID
    const taskToPartition = new Map<string, string>();
    for (const partition of partitions) {
      for (const task of partition.tasks) {
        taskToPartition.set(task.id, partition.id);
      }
    }

    // Map partition ID to set of partition IDs it depends on
    const crossDeps = new Map<string, Set<string>>();
    for (const partition of partitions) {
      crossDeps.set(partition.id, new Set());
    }

    for (const task of tasks) {
      const taskPartition = taskToPartition.get(task.id);
      if (!taskPartition) continue;

      for (const depId of task.dependencies) {
        const depPartition = taskToPartition.get(depId);
        if (depPartition && depPartition !== taskPartition) {
          crossDeps.get(taskPartition)?.add(depPartition);
        }
      }
    }

    return crossDeps;
  }

  /**
   * Execute all partitions with proper coordination.
   */
  private async executePartitions(
    partitions: WorkPartition[],
    partitionStatuses: Map<string, PartitionStatus>,
    crossPartitionDeps: Map<string, Set<string>>,
    taskStates: Map<string, TaskState>,
    plan: ExecutionPlan,
    abortSignal: AbortSignal,
    startTime: number
  ): Promise<ExecutionResult[]> {
    const allResults: ExecutionResult[] = [];
    const completedPartitions = new Set<string>();
    const runningPartitions = new Map<string, Promise<ExecutionResult[]>>();
    const options = this.engine.getOptions();

    // Calculate max parallel partitions
    const maxParallelPartitions = Math.ceil(
      options.maxConcurrency / this.distributedOptions.concurrencyPerPartition
    );

    this.emitDistributedProgress(partitionStatuses, startTime, plan);

    while (completedPartitions.size < partitions.length && !abortSignal.aborted) {
      // Find partitions ready to execute
      for (const partition of partitions) {
        if (completedPartitions.has(partition.id) || runningPartitions.has(partition.id)) {
          continue;
        }

        // Check if all cross-partition dependencies are satisfied
        const deps = crossPartitionDeps.get(partition.id) ?? new Set();
        const depsComplete = [...deps].every(depId => completedPartitions.has(depId));

        if (depsComplete && runningPartitions.size < maxParallelPartitions) {
          const status = partitionStatuses.get(partition.id);
          if (status) {
            status.status = 'running';
            status.startedAt = new Date();
          }

          // Start partition execution
          const partitionPromise = this.executePartition(
            partition,
            taskStates,
            plan,
            abortSignal,
            partitionStatuses,
            startTime
          );

          runningPartitions.set(partition.id, partitionPromise);
        }
      }

      // Wait for at least one partition to complete
      if (runningPartitions.size > 0) {
        const partitionEntries = [...runningPartitions.entries()];
        const results = await Promise.race(
          partitionEntries.map(([id, promise]) =>
            promise.then(results => ({ id, results }))
          )
        );

        completedPartitions.add(results.id);
        runningPartitions.delete(results.id);
        allResults.push(...results.results);

        const status = partitionStatuses.get(results.id);
        if (status) {
          status.status = status.results.some(r => !r.success) ? 'failed' : 'completed';
          status.completedAt = new Date();
        }

        this.emitDistributedProgress(partitionStatuses, startTime, plan);
      } else if (completedPartitions.size < partitions.length) {
        // Deadlock detection
        const pendingPartitions = partitions.filter(
          p => !completedPartitions.has(p.id) && !runningPartitions.has(p.id)
        );
        if (pendingPartitions.length > 0) {
          // Mark blocked partitions as failed
          for (const partition of pendingPartitions) {
            for (const task of partition.tasks) {
              const state = taskStates.get(task.id);
              if (state) {
                state.status = 'cancelled';
                const result: ExecutionResult = {
                  taskId: task.id,
                  success: false,
                  output: '',
                  error: 'Partition blocked by failed dependencies',
                  duration: 0,
                  filesModified: [],
                  retryCount: 0,
                  startedAt: new Date(),
                  completedAt: new Date(),
                };
                state.result = result;
                allResults.push(result);
              }
            }
            completedPartitions.add(partition.id);
          }
        }
      }
    }

    return allResults;
  }

  /**
   * Execute a single partition.
   */
  private async executePartition(
    partition: WorkPartition,
    taskStates: Map<string, TaskState>,
    plan: ExecutionPlan,
    abortSignal: AbortSignal,
    partitionStatuses: Map<string, PartitionStatus>,
    startTime: number
  ): Promise<ExecutionResult[]> {
    const results: ExecutionResult[] = [];
    const completedResults = new Map<string, ExecutionResult>();
    const concurrency = this.distributedOptions.concurrencyPerPartition;

    // Sort tasks within partition by dependencies
    const sortedTasks = this.topologicalSortPartition(partition.tasks);

    // Track running tasks within partition
    const runningTasks = new Map<string, Promise<ExecutionResult>>();
    let taskIndex = 0;

    while (
      (taskIndex < sortedTasks.length || runningTasks.size > 0) &&
      !abortSignal.aborted
    ) {
      // Start new tasks up to concurrency limit
      while (
        runningTasks.size < concurrency &&
        taskIndex < sortedTasks.length &&
        !abortSignal.aborted
      ) {
        const task = sortedTasks[taskIndex];
        if (!task) {
          taskIndex++;
          continue;
        }

        // Check if dependencies within partition are complete
        const depsComplete = task.dependencies.every(depId => {
          const depInPartition = partition.tasks.some(t => t.id === depId);
          if (!depInPartition) return true; // Cross-partition dep already handled
          return completedResults.has(depId);
        });

        if (!depsComplete) {
          // Skip for now, will be handled in next iteration
          taskIndex++;
          continue;
        }

        const state = taskStates.get(task.id);
        if (!state) {
          taskIndex++;
          continue;
        }

        // Build dependency results
        const dependencyResults = new Map<string, ExecutionResult>();
        for (const depId of task.dependencies) {
          const depResult = completedResults.get(depId);
          if (depResult) {
            dependencyResults.set(depId, depResult);
          }
        }

        const context = this.engine.createContext(
          dependencyResults,
          {
            ...plan.globalContext,
            __partition: {
              id: partition.id,
              name: partition.name,
              targets: partition.targets,
            },
          },
          abortSignal
        );

        const taskPromise = this.engine.executeTask(task, context, state)
          .then(result => {
            results.push(result);
            completedResults.set(task.id, result);
            runningTasks.delete(task.id);

            const status = partitionStatuses.get(partition.id);
            if (status) {
              status.completedTasks++;
              if (!result.success) status.failedTasks++;
              status.results.push(result);
            }

            this.emitDistributedProgress(partitionStatuses, startTime, plan);
            return result;
          });

        runningTasks.set(task.id, taskPromise);
        taskIndex++;
      }

      // Wait for at least one task to complete
      if (runningTasks.size > 0) {
        await Promise.race(runningTasks.values());
      }
    }

    return results;
  }

  /**
   * Topological sort for tasks within a partition.
   */
  private topologicalSortPartition(tasks: Task[]): Task[] {
    const taskIds = new Set(tasks.map(t => t.id));
    const sorted: Task[] = [];
    const visited = new Set<string>();
    const taskMap = new Map(tasks.map(t => [t.id, t]));

    const visit = (taskId: string): void => {
      if (visited.has(taskId)) return;

      const task = taskMap.get(taskId);
      if (!task) return;

      visited.add(taskId);

      // Only visit dependencies within this partition
      for (const depId of task.dependencies) {
        if (taskIds.has(depId)) {
          visit(depId);
        }
      }

      sorted.push(task);
    };

    for (const task of tasks) {
      visit(task.id);
    }

    return sorted;
  }

  /**
   * Emit progress for distributed execution.
   */
  private emitDistributedProgress(
    partitionStatuses: Map<string, PartitionStatus>,
    startTime: number,
    plan: ExecutionPlan
  ): void {
    let totalCompleted = 0;
    let totalFailed = 0;
    let totalRunning = 0;
    const runningTaskIds: string[] = [];

    for (const status of partitionStatuses.values()) {
      totalCompleted += status.completedTasks;
      totalFailed += status.failedTasks;
      if (status.status === 'running') {
        totalRunning += status.partition.tasks.length - status.completedTasks;
        // Add task IDs that are not yet completed
        for (const task of status.partition.tasks) {
          if (!status.results.some(r => r.taskId === task.id)) {
            runningTaskIds.push(task.id);
          }
        }
      }
    }

    const total = plan.tasks.length;
    const elapsedTime = Date.now() - startTime;

    let estimatedTimeRemaining: number | undefined;
    if (totalCompleted > 0 && totalCompleted < total) {
      const avgDuration = elapsedTime / totalCompleted;
      estimatedTimeRemaining = Math.round(avgDuration * (total - totalCompleted));
    }

    const allComplete = totalCompleted + totalFailed >= total;

    const progress: Progress = {
      totalTasks: total,
      completedTasks: totalCompleted,
      failedTasks: totalFailed,
      runningTasks: Math.min(runningTaskIds.length, totalRunning),
      percentage: Math.round((totalCompleted / total) * 100),
      runningTaskIds: runningTaskIds.slice(0, 10), // Limit for display
      estimatedTimeRemaining,
      elapsedTime,
      phase: allComplete ? 'complete' : totalRunning > 0 ? 'executing' : 'initializing',
    };

    this.engine.emitProgress(progress);
  }

  // ==========================================================================
  // Utility Methods
  // ==========================================================================

  private extractFileName(path: string): string {
    const parts = path.split('/');
    return parts[parts.length - 1] ?? path;
  }

  private extractModuleName(path: string): string {
    const parts = path.split('/').filter(p => p && p !== '.' && p !== '..');
    // Skip 'src' and similar common directories
    const commonDirs = new Set(['src', 'lib', 'app', 'dist', 'build']);
    const filtered = parts.filter(p => !commonDirs.has(p));
    return filtered[0] ?? parts[0] ?? '';
  }

  private hashString(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).substring(0, 8);
  }
}

// ============================================================================
// Analysis Types
// ============================================================================

/** Distribution analysis result */
export interface DistributionAnalysis {
  totalTasks: number;
  partitionCount: number;
  partitions: Array<{
    id: string;
    name: string;
    taskCount: number;
    targets: string[];
  }>;
  targetDistribution: Record<string, number>;
  unassignedTasks: string[];
  estimatedParallelism: number;
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a standalone distributed executor.
 * Note: Typically you would use the ExecutionEngine which manages this internally.
 */
export function createDistributedExecutor(engine: ExecutionEngine): DistributedExecutor {
  return new DistributedExecutor(engine);
}
