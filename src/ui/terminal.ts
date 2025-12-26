/**
 * Terminal UI - Rich terminal interface with real-time updates
 */

import chalk from 'chalk';
import ora from 'ora';
import type { Ora } from 'ora';
import { input, confirm } from '@inquirer/prompts';
import { TaskStatus, AgentType } from '../core/types'
import type {
  ExecutionProgress,
  Task,
  OrchestratorEvent,
  ExecutionResult
} from '../core/types';

export class TerminalUI {
  private spinner: Ora | null = null;
  private verbose: boolean;
  private startTime: number = 0;

  constructor(verbose: boolean = false) {
    this.verbose = verbose;
  }

  // Branding
  showBanner(): void {
    console.log(chalk.cyan(`
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ${chalk.bold.white('🤖 Multi-Agent Orchestrator')}                              ║
║   ${chalk.gray('Claude + Gemini + Codex Pipeline')}                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
`));
  }

  // Status messages
  info(message: string): void {
    console.log(chalk.blue('ℹ'), message);
  }

  success(message: string): void {
    console.log(chalk.green('✓'), message);
  }

  error(message: string): void {
    console.log(chalk.red('✗'), message);
  }

  warning(message: string): void {
    console.log(chalk.yellow('⚠'), message);
  }

  debug(message: string): void {
    if (this.verbose) {
      console.log(chalk.gray('⋯'), chalk.gray(message));
    }
  }

  // Spinner management
  startSpinner(text: string): void {
    this.spinner = ora({
      text,
      spinner: 'dots12',
      color: 'cyan'
    }).start();
  }

  updateSpinner(text: string): void {
    if (this.spinner) {
      this.spinner.text = text;
    }
  }

  succeedSpinner(text?: string): void {
    if (this.spinner) {
      this.spinner.succeed(text);
      this.spinner = null;
    }
  }

  failSpinner(text?: string): void {
    if (this.spinner) {
      this.spinner.fail(text);
      this.spinner = null;
    }
  }

  stopSpinner(): void {
    if (this.spinner) {
      this.spinner.stop();
      this.spinner = null;
    }
  }

  // Progress display
  showProgress(progress: ExecutionProgress): void {
    const bar = this.createProgressBar(progress.percentage);
    const elapsed = this.formatDuration(progress.elapsedSeconds);

    const status = [
      chalk.cyan(`[${bar}]`),
      chalk.white(`${progress.percentage}%`),
      chalk.gray(`(${progress.completed}/${progress.total})`),
      chalk.gray(`⏱ ${elapsed}`)
    ].join(' ');

    if (progress.currentTask) {
      console.log(`\r${status} ${chalk.yellow('→')} ${this.truncate(progress.currentTask.description, 40)}`);
    } else {
      console.log(`\r${status}`);
    }
  }

  private createProgressBar(percentage: number, width: number = 20): string {
    const filled = Math.round((percentage / 100) * width);
    const empty = width - filled;
    return chalk.green('█'.repeat(filled)) + chalk.gray('░'.repeat(empty));
  }

  private formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  }

  private truncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
  }

  // Task display
  showTask(task: Task): void {
    const agentBadge = this.getAgentBadge(task.agent);
    const statusIcon = this.getStatusIcon(task.status);

    console.log(`  ${statusIcon} ${agentBadge} ${task.description}`);

    if (task.files.length > 0 && this.verbose) {
      console.log(chalk.gray(`      Files: ${task.files.join(', ')}`));
    }
  }

  private getAgentBadge(agent?: AgentType): string {
    switch (agent) {
      case AgentType.CLAUDE:
        return chalk.bgMagenta.white(' CLAUDE ');
      case AgentType.GEMINI:
        return chalk.bgBlue.white(' GEMINI ');
      case AgentType.CODEX:
        return chalk.bgGreen.white(' CODEX ');
      default:
        return chalk.bgGray.white(' AUTO ');
    }
  }

  private getStatusIcon(status: TaskStatus): string {
    switch (status) {
      case TaskStatus.COMPLETED:
        return chalk.green('✓');
      case TaskStatus.FAILED:
        return chalk.red('✗');
      case TaskStatus.IN_PROGRESS:
        return chalk.yellow('◐');
      case TaskStatus.PENDING:
        return chalk.gray('○');
      case TaskStatus.QUEUED:
        return chalk.blue('◎');
      case TaskStatus.CANCELLED:
        return chalk.gray('⊘');
      default:
        return chalk.gray('?');
    }
  }

  // Plan display
  showPlan(tasks: Task[], mode: string): void {
    console.log();
    console.log(chalk.bold.white('📋 Execution Plan'));
    console.log(chalk.gray(`   Mode: ${mode}`));
    console.log(chalk.gray(`   Tasks: ${tasks.length}`));
    console.log();

    tasks.forEach((task, index) => {
      const deps = task.dependencies.length > 0
        ? chalk.gray(` (after: ${task.dependencies.join(', ')})`)
        : '';
      const agentBadge = this.getAgentBadge(task.agent);

      console.log(`  ${chalk.cyan(`${index + 1}.`)} ${agentBadge} ${task.description}${deps}`);
    });

    console.log();
  }

  // Result display
  showResult(result: ExecutionResult): void {
    console.log();
    console.log(chalk.bold.white('═══════════════════════════════════════'));

    if (result.success) {
      console.log(chalk.bold.green('✓ Execution Completed Successfully'));
    } else {
      console.log(chalk.bold.red('✗ Execution Failed'));
    }

    console.log(chalk.bold.white('═══════════════════════════════════════'));
    console.log();

    // Summary
    console.log(chalk.white('Summary:'));
    console.log(`  ${chalk.gray('Duration:')} ${this.formatDuration(result.totalDuration)}`);
    console.log(`  ${chalk.gray('Tasks:')} ${result.tasks.filter(t => t.success).length}/${result.tasks.length} succeeded`);

    if (result.filesModified.length > 0) {
      console.log(`  ${chalk.gray('Modified:')} ${result.filesModified.length} files`);
    }
    if (result.filesCreated.length > 0) {
      console.log(`  ${chalk.gray('Created:')} ${result.filesCreated.length} files`);
    }

    // Errors
    if (result.errors.length > 0) {
      console.log();
      console.log(chalk.red('Errors:'));
      result.errors.forEach(err => {
        console.log(chalk.red(`  • ${err}`));
      });
    }

    console.log();
  }

  // Event handling
  handleEvent(event: OrchestratorEvent): void {
    switch (event.type) {
      case 'plan_created':
        this.showPlan(event.plan.tasks, event.plan.mode);
        break;

      case 'task_started':
        this.startSpinner(`${this.getAgentBadge(event.task.agent)} ${event.task.description}`);
        break;

      case 'task_completed':
        this.succeedSpinner(`${event.task.description}`);
        break;

      case 'task_failed':
        this.failSpinner(`${event.task.description}: ${event.error}`);
        break;

      case 'progress_update':
        if (!this.spinner) {
          this.showProgress(event.progress);
        }
        break;

      case 'execution_complete':
        this.stopSpinner();
        this.showResult(event.result);
        break;

      case 'error':
        this.stopSpinner();
        this.error(event.error);
        break;
    }
  }

  // Streaming output
  streamOutput(chunk: string, agent?: AgentType): void {
    const prefix = agent ? this.getAgentBadge(agent) : '';
    process.stdout.write(chalk.gray(prefix + chunk));
  }

  // Clear line
  clearLine(): void {
    process.stdout.write('\r\x1b[K');
  }

  // Section separators
  section(title: string): void {
    console.log();
    console.log(chalk.bold.cyan(`── ${title} ──`));
    console.log();
  }

  // Code block display
  showCode(code: string, language?: string): void {
    console.log(chalk.gray('```' + (language || '')));
    console.log(code);
    console.log(chalk.gray('```'));
  }

  // Table display for agent status
  showAgentStatus(agents: { name: string; available: boolean; model?: string }[]): void {
    console.log();
    console.log(chalk.bold.white('Agent Status:'));

    agents.forEach(agent => {
      const status = agent.available
        ? chalk.green('● Online')
        : chalk.red('○ Offline');
      const model = agent.model ? chalk.gray(` (${agent.model})`) : '';
      console.log(`  ${agent.name.padEnd(10)} ${status}${model}`);
    });

    console.log();
  }

  // Prompt for user input
  prompt(message: string): void {
    console.log();
    console.log(chalk.yellow('?'), chalk.bold(message));
  }

  // Interactive model selection - queries from each CLI
  async selectModels(): Promise<Record<AgentType, string>> {
    const models: Record<AgentType, string> = {
      [AgentType.CLAUDE]: '',
      [AgentType.GEMINI]: '',
      [AgentType.CODEX]: '',
    };

    console.log();
    console.log(chalk.bold.cyan('🎛️  Model Configuration'));
    console.log(chalk.gray('   Enter model names for each agent (leave empty for CLI default)'));
    console.log(chalk.gray('   Examples: claude → sonnet, opus, haiku'));
    console.log(chalk.gray('            gemini → gemini-2.5-pro, gemini-2.5-flash'));
    console.log(chalk.gray('            codex  → o3, o3-mini, gpt-4.1'));
    console.log();

    // Ask if user wants to configure models
    const configure = await confirm({
      message: 'Configure models? (No = use CLI defaults)',
      default: false,
    });

    if (!configure) {
      console.log(chalk.gray('   Using default models for all agents'));
      return models;
    }

    // Get model for each agent
    for (const agentType of [AgentType.GEMINI, AgentType.CLAUDE, AgentType.CODEX]) {
      const agentName = agentType === AgentType.CLAUDE ? 'Claude'
                      : agentType === AgentType.GEMINI ? 'Gemini'
                      : 'Codex';

      const modelInput = await input({
        message: `${agentName} model (empty = default):`,
        default: '',
      });

      models[agentType] = modelInput.trim();

      if (modelInput.trim()) {
        console.log(chalk.green(`   ✓ ${agentName}: ${modelInput.trim()}`));
      } else {
        console.log(chalk.gray(`   · ${agentName}: using CLI default`));
      }
    }

    console.log();
    return models;
  }

  // Streaming output header
  showStreamingStart(agentType: AgentType, taskNumber: number, totalTasks: number, description: string): void {
    this.stopSpinner(); // Stop any running spinner

    const agentName = agentType === AgentType.CLAUDE ? 'Claude'
                    : agentType === AgentType.GEMINI ? 'Gemini'
                    : 'Codex';
    const agentColor = agentType === AgentType.CLAUDE ? chalk.magenta
                     : agentType === AgentType.GEMINI ? chalk.blue
                     : chalk.green;

    console.log();
    console.log(agentColor('┌' + '─'.repeat(70) + '┐'));
    console.log(agentColor('│') + chalk.bold(` 🤖 ${agentName} `) + chalk.gray(`[Task ${taskNumber}/${totalTasks}]`).padEnd(59) + agentColor('│'));
    console.log(agentColor('│') + chalk.gray(` ${this.truncate(description, 68)} `).padEnd(70) + agentColor('│'));
    console.log(agentColor('├' + '─'.repeat(70) + '┤'));
    console.log(agentColor('│') + chalk.gray(' Output:').padEnd(70) + agentColor('│'));
    console.log(agentColor('└' + '─'.repeat(70) + '┘'));
    console.log();
  }

  // Streaming output with live indicator
  showStreamingLine(line: string, agentType: AgentType): void {
    const agentColor = agentType === AgentType.CLAUDE ? chalk.magenta
                     : agentType === AgentType.GEMINI ? chalk.blue
                     : chalk.green;

    // Prefix each line with a subtle indicator
    console.log(agentColor('│') + ' ' + line);
  }

  // Streaming output footer
  showStreamingEnd(agentType: AgentType, duration: number, success: boolean): void {
    const agentName = agentType === AgentType.CLAUDE ? 'Claude'
                    : agentType === AgentType.GEMINI ? 'Gemini'
                    : 'Codex';
    const agentColor = agentType === AgentType.CLAUDE ? chalk.magenta
                     : agentType === AgentType.GEMINI ? chalk.blue
                     : chalk.green;

    console.log();
    if (success) {
      console.log(agentColor('┌' + '─'.repeat(70) + '┐'));
      console.log(agentColor('│') + chalk.green(` ✅ ${agentName} completed in ${(duration / 1000).toFixed(1)}s`).padEnd(70) + agentColor('│'));
      console.log(agentColor('└' + '─'.repeat(70) + '┘'));
    } else {
      console.log(agentColor('┌' + '─'.repeat(70) + '┐'));
      console.log(agentColor('│') + chalk.red(` ❌ ${agentName} failed after ${(duration / 1000).toFixed(1)}s`).padEnd(70) + agentColor('│'));
      console.log(agentColor('└' + '─'.repeat(70) + '┘'));
    }
    console.log();
  }

  // Show task progress summary
  showTaskProgress(currentTask: number, totalTasks: number, completedTasks: string[], failedTasks: string[]): void {
    console.log();
    console.log(chalk.bold.white('📊 Progress'));

    const progressPercent = Math.round((currentTask / totalTasks) * 100);
    const progressBar = this.createProgressBar(progressPercent, 30);

    console.log(`   ${progressBar} ${progressPercent}% (${currentTask}/${totalTasks})`);

    if (completedTasks.length > 0) {
      console.log(chalk.green(`   ✓ Completed: ${completedTasks.join(', ')}`));
    }
    if (failedTasks.length > 0) {
      console.log(chalk.red(`   ✗ Failed: ${failedTasks.join(', ')}`));
    }
    console.log();
  }

  // Show what's happening right now
  showCurrentAction(action: string): void {
    console.log(chalk.cyan('   → ') + chalk.white(action));
  }
}

export default TerminalUI;
