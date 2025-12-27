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

// Agent role definitions
export interface AgentRole {
  name: string;
  description: string;
  responsibilities: string[];
  systemPrompt: string;
}

export const AGENT_ROLES: Record<AgentType, AgentRole> = {
  [AgentType.CLAUDE]: {
    name: 'Architect',
    description: 'System architecture and high-level design',
    responsibilities: [
      'Design overall system architecture',
      'Define component interactions',
      'Establish coding standards and patterns',
      'Review and validate technical decisions'
    ],
    systemPrompt: `You are the System Architect. Your role is to:
- Design the overall architecture and system structure
- Make high-level technical decisions
- Define how components should interact
- Ensure scalability and maintainability
- Review other agents' work for architectural consistency

When given a task, focus on the big picture and architectural patterns.`
  },
  [AgentType.GEMINI]: {
    name: 'Integrator',
    description: 'Frontend and backend integration',
    responsibilities: [
      'Implement frontend components',
      'Connect frontend to backend APIs',
      'Handle data flow and state management',
      'Ensure smooth integration across layers'
    ],
    systemPrompt: `You are the Integration Specialist. Your role is to:
- Implement frontend and backend integration
- Build UI components and connect them to APIs
- Manage data flow between layers
- Handle state management and data synchronization
- Ensure seamless communication between components

Focus on making different parts of the system work together cohesively.`
  },
  [AgentType.CODEX]: {
    name: 'Reviewer',
    description: 'Quality assurance and code review',
    responsibilities: [
      'Review code quality and best practices',
      'Integrate work from other agents',
      'Ensure tests pass and code works',
      'Validate final implementation'
    ],
    systemPrompt: `You are the Quality Reviewer. Your role is to:
- Review code from other agents for quality
- Ensure best practices are followed
- Integrate and validate the final implementation
- Run tests and verify functionality
- Identify bugs and improvement opportunities

Focus on quality, correctness, and final integration of all work.`
  }
};

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
    try {
      // Try to query the model from the CLI
      // Each CLI has different ways to show configuration
      let args: string[] = [];

      if (command === 'claude') {
        // Claude CLI shows model with --version or in help
        args = ['--help'];
      } else if (command === 'gemini') {
        // Gemini CLI might have a config command
        args = ['--help'];
      } else if (command === 'codex') {
        // Codex CLI configuration
        args = ['--help'];
      }

      const proc = Bun.spawn([command, ...args], {
        stdout: 'pipe',
        stderr: 'pipe',
        timeout: 3000,
      });

      const output = await new Response(proc.stdout).text();
      await proc.exited;

      // Try to extract model info from help output
      // This is a best-effort attempt - if it fails, we'll show 'default'
      const modelMatch = output.match(/model[:\s]+([^\s\n]+)/i);
      if (modelMatch && modelMatch[1]) {
        return modelMatch[1];
      }

      return undefined;
    } catch {
      return undefined;
    }
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
    // For parallel mode, use role-based parallel execution
    if (mode === ExecutionMode.PARALLEL) {
      return this.executeParallel(goal);
    }

    // Create plan for iterative mode
    this.ui.info('Creating execution plan...');
    const plan = await this.createPlan(goal, mode);

    // Show plan
    this.ui.showPlan(plan.tasks, mode);

    // Execute
    return this.executePlan(plan);
  }

  /**
   * Execute with all agents in parallel using their specialized roles
   */
  async executeParallel(goal: string): Promise<ExecutionResult> {
    const startTime = Date.now();
    const planId = `parallel_${Date.now().toString(36)}`;

    this.ui.info('Starting parallel execution with role-based agents...');
    console.log();

    // Show agent roles
    for (const [agentType, role] of Object.entries(AGENT_ROLES)) {
      const agentConfig = AGENT_CONFIGS[agentType as AgentType];
      const modelInfo = agentConfig.model || 'default';
      console.log(`  ${role.name} (${agentConfig.name}) [${modelInfo}]: ${role.description}`);
    }
    console.log();

    // Create shared context for inter-agent communication
    const sharedContext = {
      goal,
      architectureNotes: '',
      integrationNotes: '',
      reviewNotes: '',
    };

    // Execute all agents in parallel
    const agentPromises = [
      this.executeAgentWithRole(AgentType.CLAUDE, goal, sharedContext),
      this.executeAgentWithRole(AgentType.GEMINI, goal, sharedContext),
      this.executeAgentWithRole(AgentType.CODEX, goal, sharedContext),
    ];

    const results = await Promise.allSettled(agentPromises);

    // Process results
    const taskResults: TaskResult[] = [];
    const errors: string[] = [];
    const filesModified: string[] = [];

    results.forEach((result, index) => {
      const agent = [AgentType.CLAUDE, AgentType.GEMINI, AgentType.CODEX][index]!;

      if (result.status === 'fulfilled') {
        taskResults.push(result.value);
        filesModified.push(...result.value.filesModified);
      } else {
        errors.push(`${agent}: ${result.reason}`);
        taskResults.push({
          taskId: agent,
          success: false,
          output: '',
          error: String(result.reason),
          duration: 0,
          agent,
          filesModified: [],
        });
      }
    });

    const totalDuration = Date.now() - startTime;
    const successCount = taskResults.filter(r => r.success).length;

    const executionResult: ExecutionResult = {
      planId,
      success: errors.length === 0,
      tasks: taskResults,
      totalDuration,
      filesModified: [...new Set(filesModified)],
      filesCreated: [],
      summary: `Parallel execution: ${successCount}/3 agents succeeded in ${(totalDuration / 1000).toFixed(1)}s`,
      errors,
    };

    this.ui.showResult(executionResult);
    return executionResult;
  }

  /**
   * Execute a single agent with its specialized role
   */
  private async executeAgentWithRole(
    agent: AgentType,
    goal: string,
    sharedContext: any
  ): Promise<TaskResult> {
    const startTime = Date.now();
    const agentConfig = AGENT_CONFIGS[agent];
    const role = AGENT_ROLES[agent];

    // Build role-based prompt
    const context = this.contextManager.generateContextString();
    const prompt = `${role.systemPrompt}

## Project Context
${context}

## Goal
${goal}

## Your Responsibilities (${role.name})
${role.responsibilities.map((r, i) => `${i + 1}. ${r}`).join('\n')}

## Inter-Agent Collaboration
- Architecture decisions will be shared by the Architect
- Integration work will be coordinated by the Integrator
- Final review and validation by the Reviewer

Please focus on your specific responsibilities while keeping the overall goal in mind.`;

    // Build args
    const args = [...agentConfig.args];
    if (agentConfig.model) {
      args.push('-m', agentConfig.model);
    }
    args.push(prompt);

    // Show agent starting
    this.ui.showStreamingStart(agent, 0, 3, `${role.name}: ${role.description}`);

    try {
      const proc = Bun.spawn([agentConfig.command, ...args], {
        cwd: this.config.workingDirectory,
        stdout: 'pipe',
        stderr: 'pipe',
      });

      let output = '';
      let stderr = '';

      // Stream output
      const decoder = new TextDecoder();
      const reader = proc.stdout.getReader();

      try {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          output += chunk;
          buffer += chunk;

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim()) {
              console.log(`[${role.name}] ${line}`);
            }
          }
        }

        if (buffer.trim()) {
          console.log(`[${role.name}] ${buffer}`);
        }
      } catch {
        // Stream ended
      }

      // Capture stderr
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

      this.ui.showStreamingEnd(agent, duration, exitCode === 0);

      // Update shared context based on role
      if (exitCode === 0) {
        if (agent === AgentType.CLAUDE) {
          sharedContext.architectureNotes = output.slice(0, 500);
        } else if (agent === AgentType.GEMINI) {
          sharedContext.integrationNotes = output.slice(0, 500);
        } else if (agent === AgentType.CODEX) {
          sharedContext.reviewNotes = output.slice(0, 500);
        }
      }

      const filesModified = this.parseFilesFromOutput(output);

      return {
        taskId: agent,
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

      this.ui.showStreamingEnd(agent, duration, false);

      return {
        taskId: agent,
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
   * Execute an existing plan
   */
  async executePlan(plan: ExecutionPlan): Promise<ExecutionResult> {
    const startTime = Date.now();
    const taskResults: TaskResult[] = [];
    const filesModified: string[] = [];
    const filesCreated: string[] = [];
    const errors: string[] = [];
    const completedTaskIds: string[] = [];
    const failedTaskIds: string[] = [];

    // Sort tasks topologically
    const sortedTasks = this.topologicalSort(plan.tasks);
    const totalTasks = sortedTasks.length;

    for (let i = 0; i < sortedTasks.length; i++) {
      const task = sortedTasks[i]!;
      const taskNumber = i + 1;

      // Show current progress
      this.ui.showTaskProgress(taskNumber, totalTasks, completedTaskIds, failedTaskIds);

      // Check if dependencies completed successfully
      const depsOk = task.dependencies.every(depId => {
        const dep = taskResults.find(r => r.taskId === depId);
        return dep?.success;
      });

      if (!depsOk) {
        task.status = TaskStatus.CANCELLED;
        failedTaskIds.push(task.id);
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

      // Execute task (no spinner - streaming UI handles this)
      task.status = TaskStatus.IN_PROGRESS;
      task.startedAt = new Date();

      try {
        const result = await this.executeTask(task, plan, taskNumber, totalTasks);
        taskResults.push(result);

        if (result.success) {
          task.status = TaskStatus.COMPLETED;
          task.output = result.output;
          filesModified.push(...result.filesModified);
          completedTaskIds.push(task.id);
        } else {
          task.status = TaskStatus.FAILED;
          task.error = result.error;
          errors.push(result.error || 'Unknown error');
          failedTaskIds.push(task.id);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        task.status = TaskStatus.FAILED;
        task.error = errorMsg;
        errors.push(errorMsg);
        failedTaskIds.push(task.id);
        taskResults.push({
          taskId: task.id,
          success: false,
          output: '',
          error: errorMsg,
          duration: 0,
          agent: task.agent || AgentType.CLAUDE,
          filesModified: [],
        });
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
  private async executeTask(
    task: Task,
    plan: ExecutionPlan,
    taskNumber: number,
    totalTasks: number
  ): Promise<TaskResult> {
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

    // Show streaming header with agent info
    this.ui.showStreamingStart(agent, taskNumber, totalTasks, task.description);

    try {
      // Execute via CLI with streaming
      const proc = Bun.spawn([agentConfig.command, ...args], {
        cwd: this.config.workingDirectory,
        stdout: 'pipe',
        stderr: 'pipe',
      });

      let output = '';
      let stderr = '';

      // Stream stdout in real-time
      const decoder = new TextDecoder();
      const reader = proc.stdout.getReader();

      try {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          output += chunk;
          buffer += chunk;

          // Process complete lines for cleaner output
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.trim()) {
              process.stdout.write(line + '\n');
            }
          }
        }

        // Output any remaining buffer
        if (buffer.trim()) {
          process.stdout.write(buffer + '\n');
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

      // Show completion status
      this.ui.showStreamingEnd(agent, duration, exitCode === 0);

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

      this.ui.showStreamingEnd(agent, duration, false);

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
