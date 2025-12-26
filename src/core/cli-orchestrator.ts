/**
 * CLI Orchestrator - Bridge between CLI and execution system
 *
 * This provides the interface expected by the CLI entry point while
 * leveraging the core execution engine internally.
 */

import type { ContextManager } from '../context/manager';
import type { TerminalUI } from '../ui/terminal';
import {
  AgentType,
  ExecutionMode,
  TaskStatus,
  TaskPriority,
} from './types';
import type {
  ExecutionPlan,
  Task,
  ExecutionResult,
  TaskResult,
  OrchestratorConfig,
  ExecutionProgress,
} from './types';
import { AGENT_CONFIGS, selectAgent } from '../config/defaults';

export interface AgentStatus {
  name: string;
  available: boolean;
  model?: string;
}

/**
 * CLI-facing Orchestrator
 * Provides the methods expected by the main CLI entry point
 */
export class Orchestrator {
  private config: OrchestratorConfig;
  private contextManager: ContextManager;
  private ui: TerminalUI;
  private eventHandlers: Array<(event: unknown) => void> = [];

  constructor(
    config: OrchestratorConfig,
    contextManager: ContextManager,
    ui: TerminalUI
  ) {
    this.config = config;
    this.contextManager = contextManager;
    this.ui = ui;
  }

  /**
   * Check availability of all agents
   */
  async checkAgents(): Promise<AgentStatus[]> {
    const agents: AgentStatus[] = [];

    for (const [type, agentConfig] of Object.entries(AGENT_CONFIGS)) {
      const available = await this.isAgentAvailable(agentConfig.command);
      // Get actual model info from CLI if available
      const model = agentConfig.model || await this.getAgentDefaultModel(agentConfig.command);
      agents.push({
        name: agentConfig.name,
        available,
        model: model || 'default',
      });
    }

    return agents;
  }

  /**
   * Get the default model being used by an agent CLI
   */
  private async getAgentDefaultModel(command: string): Promise<string | undefined> {
    // Each CLI has different ways to show the current model
    // For now, return undefined to use 'default' display
    // The actual model will be shown in the streaming output
    return undefined;
  }

  /**
   * Check if a CLI command is available
   */
  private async isAgentAvailable(command: string): Promise<boolean> {
    try {
      const proc = Bun.spawn(['which', command], {
        stdout: 'pipe',
        stderr: 'pipe',
      });
      const exitCode = await proc.exited;
      return exitCode === 0;
    } catch {
      return false;
    }
  }

  /**
   * Create an execution plan for a goal
   */
  async createPlan(goal: string, mode: ExecutionMode): Promise<ExecutionPlan> {
    const planId = `plan_${Date.now().toString(36)}`;

    // Use the planning agent to decompose the goal
    const tasks = await this.decomposeGoal(goal, mode);

    const plan: ExecutionPlan = {
      id: planId,
      goal,
      mode,
      tasks,
      thinkingOutput: `Planning for: ${goal}`,
      createdAt: new Date(),
      metadata: {
        createdBy: 'orchestrator',
        estimatedDuration: tasks.length * 30000, // 30s per task estimate
      },
    };

    // Save to context manager
    this.contextManager.savePlan(plan);

    return plan;
  }

  /**
   * Decompose a goal into tasks
   */
  private async decomposeGoal(goal: string, mode: ExecutionMode): Promise<Task[]> {
    const tasks: Task[] = [];
    const goalLower = goal.toLowerCase();

    // Simple heuristic decomposition
    // In production, this would call the planning agent

    // Analysis task
    tasks.push(this.createTask(
      'analyze',
      `Analyze and understand the requirements for: ${goal}`,
      AgentType.GEMINI,
      []
    ));

    // Determine task type and add appropriate tasks
    if (goalLower.includes('build') || goalLower.includes('implement') || goalLower.includes('create')) {
      tasks.push(this.createTask(
        'plan',
        'Create detailed implementation plan',
        AgentType.CLAUDE,
        ['analyze']
      ));

      tasks.push(this.createTask(
        'implement',
        'Implement the solution based on the plan',
        AgentType.CODEX,
        ['plan']
      ));

      tasks.push(this.createTask(
        'review',
        'Review implementation for quality and best practices',
        AgentType.CLAUDE,
        ['implement']
      ));
    } else if (goalLower.includes('fix') || goalLower.includes('debug')) {
      tasks.push(this.createTask(
        'diagnose',
        'Diagnose the root cause of the issue',
        AgentType.CLAUDE,
        ['analyze']
      ));

      tasks.push(this.createTask(
        'fix',
        'Implement the fix',
        AgentType.GEMINI,
        ['diagnose']
      ));

      tasks.push(this.createTask(
        'verify',
        'Verify the fix resolves the issue',
        AgentType.CLAUDE,
        ['fix']
      ));
    } else {
      // Generic task
      tasks.push(this.createTask(
        'execute',
        `Execute: ${goal}`,
        selectAgent(goal),
        ['analyze']
      ));
    }

    return tasks;
  }

  /**
   * Create a task object
   */
  private createTask(
    id: string,
    description: string,
    agent: AgentType,
    dependencies: string[]
  ): Task {
    return {
      id,
      description,
      agent,
      status: TaskStatus.PENDING,
      priority: TaskPriority.MEDIUM,
      dependencies,
      files: [],
      estimatedComplexity: 5,
      createdAt: new Date(),
      metadata: {},
    };
  }

  /**
   * Execute a goal from start to finish
   */
  async run(goal: string, mode: ExecutionMode): Promise<ExecutionResult> {
    // Create plan
    this.ui.info('Creating execution plan...');
    const plan = await this.createPlan(goal, mode);

    // Show plan
    this.ui.showPlan(plan.tasks, mode);

    // Execute
    return this.executePlan(plan);
  }

  /**
   * Execute an existing plan
   */
  async executePlan(plan: ExecutionPlan): Promise<ExecutionResult> {
    const startTime = Date.now();
    const taskResults: TaskResult[] = [];
    const filesModified: string[] = [];
    const filesCreated: string[] = [];
    const errors: string[] = [];

    // Sort tasks topologically
    const sortedTasks = this.topologicalSort(plan.tasks);

    for (const task of sortedTasks) {
      // Check if dependencies completed successfully
      const depsOk = task.dependencies.every(depId => {
        const dep = taskResults.find(r => r.taskId === depId);
        return dep?.success;
      });

      if (!depsOk) {
        task.status = TaskStatus.CANCELLED;
        taskResults.push({
          taskId: task.id,
          success: false,
          output: '',
          error: 'Dependencies failed',
          duration: 0,
          agent: task.agent || AgentType.CLAUDE,
          filesModified: [],
        });
        continue;
      }

      // Execute task
      this.ui.startSpinner(`Executing: ${task.description}`);
      task.status = TaskStatus.IN_PROGRESS;
      task.startedAt = new Date();

      try {
        const result = await this.executeTask(task, plan);
        taskResults.push(result);

        if (result.success) {
          task.status = TaskStatus.COMPLETED;
          task.output = result.output;
          filesModified.push(...result.filesModified);
          this.ui.succeedSpinner(`Completed: ${task.description}`);
        } else {
          task.status = TaskStatus.FAILED;
          task.error = result.error;
          errors.push(result.error || 'Unknown error');
          this.ui.failSpinner(`Failed: ${task.description}`);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        task.status = TaskStatus.FAILED;
        task.error = errorMsg;
        errors.push(errorMsg);
        taskResults.push({
          taskId: task.id,
          success: false,
          output: '',
          error: errorMsg,
          duration: 0,
          agent: task.agent || AgentType.CLAUDE,
          filesModified: [],
        });
        this.ui.failSpinner(`Failed: ${task.description} - ${errorMsg}`);
      }

      task.completedAt = new Date();
    }

    const result: ExecutionResult = {
      planId: plan.id,
      success: errors.length === 0,
      tasks: taskResults,
      totalDuration: Date.now() - startTime,
      filesModified: [...new Set(filesModified)],
      filesCreated: [...new Set(filesCreated)],
      summary: errors.length === 0
        ? `Successfully completed ${taskResults.filter(t => t.success).length} tasks`
        : `Completed with ${errors.length} errors`,
      errors,
    };

    this.ui.showResult(result);
    this.contextManager.updatePlanStatus(plan.id, result.success ? 'completed' : 'failed');

    return result;
  }

  /**
   * Execute a single task with real-time streaming output
   */
  private async executeTask(task: Task, plan: ExecutionPlan): Promise<TaskResult> {
    const agent = task.agent || selectAgent(task.description);
    const agentConfig = AGENT_CONFIGS[agent];
    const startTime = Date.now();

    // Build the prompt with context
    const context = this.contextManager.generateContextString();
    const prompt = `${context}\n\n## Task\n${task.description}\n\n## Goal\n${plan.goal}`;

    // Build args - add model if specified
    const args = [...agentConfig.args];
    if (agentConfig.model) {
      args.push('-m', agentConfig.model);
    }
    args.push(prompt);

    try {
      // Execute via CLI with streaming
      const proc = Bun.spawn([agentConfig.command, ...args], {
        cwd: this.config.workingDirectory,
        stdout: 'pipe',
        stderr: 'pipe',
      });

      let output = '';
      let stderr = '';

      // Show streaming header
      console.log(`\n${'─'.repeat(60)}`);
      console.log(`📡 ${agentConfig.name} Output:`);
      console.log(`${'─'.repeat(60)}\n`);

      // Stream stdout in real-time
      const decoder = new TextDecoder();
      const reader = proc.stdout.getReader();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          output += chunk;
          process.stdout.write(chunk); // Real-time output
        }
      } catch {
        // Stream ended
      }

      // Also capture stderr
      const stderrReader = proc.stderr.getReader();
      try {
        while (true) {
          const { done, value } = await stderrReader.read();
          if (done) break;
          stderr += decoder.decode(value, { stream: true });
        }
      } catch {
        // Stream ended
      }

      const exitCode = await proc.exited;
      const duration = Date.now() - startTime;

      console.log(`\n${'─'.repeat(60)}`);
      console.log(`✅ ${agentConfig.name} completed in ${(duration / 1000).toFixed(1)}s`);
      console.log(`${'─'.repeat(60)}\n`);

      // Log to history
      this.contextManager.addHistoryEntry({
        action: 'task_executed',
        agent,
        taskId: task.id,
        summary: exitCode === 0 ? 'Success' : `Failed: ${stderr.slice(0, 100)}`,
      });

      // Parse files modified from output
      const filesModified = this.parseFilesFromOutput(output);

      return {
        taskId: task.id,
        success: exitCode === 0,
        output,
        error: exitCode !== 0 ? stderr || `Exit code: ${exitCode}` : undefined,
        duration,
        agent,
        filesModified,
      };
    } catch (err) {
      const duration = Date.now() - startTime;
      const errorMsg = err instanceof Error ? err.message : String(err);

      console.log(`\n❌ ${agentConfig.name} failed: ${errorMsg}\n`);

      return {
        taskId: task.id,
        success: false,
        output: '',
        error: errorMsg,
        duration,
        agent,
        filesModified: [],
      };
    }
  }

  /**
   * Parse file paths from agent output
   */
  private parseFilesFromOutput(output: string): string[] {
    const files: string[] = [];

    // Match common patterns for file paths
    const patterns = [
      /(?:Created|Modified|Updated|Wrote to|Saved):\s*([^\s\n]+)/gi,
      /File:\s*([^\s\n]+)/gi,
    ];

    for (const pattern of patterns) {
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(output)) !== null) {
        if (match[1]) {
          files.push(match[1]);
        }
      }
    }

    return [...new Set(files)];
  }

  /**
   * Run a single agent with a task
   */
  async runSingleAgent(agent: AgentType, task: string): Promise<void> {
    const agentConfig = AGENT_CONFIGS[agent];

    this.ui.info(`Running ${agentConfig.name}...`);
    this.ui.startSpinner(task);

    try {
      const proc = Bun.spawn([agentConfig.command, ...agentConfig.args, task], {
        cwd: this.config.workingDirectory,
        stdout: 'pipe',
        stderr: 'pipe',
        timeout: agentConfig.timeout,
      });

      const output = await new Response(proc.stdout).text();
      const exitCode = await proc.exited;

      if (exitCode === 0) {
        this.ui.succeedSpinner('Task completed');
        console.log('\n' + output);
      } else {
        const stderr = await new Response(proc.stderr).text();
        this.ui.failSpinner('Task failed');
        console.error('\n' + stderr);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.ui.failSpinner(`Error: ${errorMsg}`);
    }
  }

  /**
   * Topological sort for task dependencies
   */
  private topologicalSort(tasks: Task[]): Task[] {
    const sorted: Task[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();
    const taskMap = new Map(tasks.map(t => [t.id, t]));

    const visit = (taskId: string): void => {
      if (visited.has(taskId)) return;
      if (visiting.has(taskId)) {
        throw new Error(`Circular dependency at task: ${taskId}`);
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
}

export default Orchestrator;
