#!/usr/bin/env bun
/**
 * Multi-Agent Orchestrator - Main Entry Point
 *
 * A powerful pipeline that coordinates Claude, Gemini, and Codex
 * to accomplish complex software engineering tasks autonomously.
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { TerminalUI } from './ui/terminal';
import { ContextManager } from './context/manager';
import { WorkflowParser } from './workflows/parser';
import { Orchestrator } from './core/cli-orchestrator';
import { DEFAULT_CONFIG } from './config/defaults';
import { ExecutionMode, AgentType } from './core/types';
import * as fs from 'fs';
import * as path from 'path';

const VERSION = '1.0.0';

// Initialize components
const ui = new TerminalUI();
const contextManager = new ContextManager();
const workflowParser = new WorkflowParser();

async function main() {
  const program = new Command();

  program
    .name('orchestrate')
    .description('Multi-Agent AI Orchestrator - Claude + Gemini + Codex Pipeline')
    .version(VERSION);

  // Main execution command
  program
    .command('run')
    .alias('r')
    .description('Execute a goal using the multi-agent pipeline')
    .argument('<goal>', 'The goal to accomplish')
    .option('-m, --mode <mode>', 'Execution mode: parallel, iterative, distributed', 'iterative')
    .option('-w, --workflow <name>', 'Use a predefined workflow')
    .option('-v, --verbose', 'Enable verbose output')
    .option('--no-confirm', 'Skip plan confirmation')
    .option('--max-concurrency <n>', 'Maximum concurrent tasks', '3')
    .option('--claude-model <model>', 'Model to use for Claude agent')
    .option('--gemini-model <model>', 'Model to use for Gemini agent')
    .option('--codex-model <model>', 'Model to use for Codex agent')
    .action(async (goal, options) => {
      ui.showBanner();

      const config = {
        ...DEFAULT_CONFIG,
        verbose: options.verbose || false,
        maxConcurrency: parseInt(options.maxConcurrency)
      };

      // Apply model overrides from CLI
      if (options.claudeModel) {
        const { AGENT_CONFIGS } = await import('./config/defaults');
        AGENT_CONFIGS[AgentType.CLAUDE].model = options.claudeModel;
      }
      if (options.geminiModel) {
        const { AGENT_CONFIGS } = await import('./config/defaults');
        AGENT_CONFIGS[AgentType.GEMINI].model = options.geminiModel;
      }
      if (options.codexModel) {
        const { AGENT_CONFIGS } = await import('./config/defaults');
        AGENT_CONFIGS[AgentType.CODEX].model = options.codexModel;
      }

      const orchestrator = new Orchestrator(config, contextManager, ui);

      // Check agent availability
      ui.info('Checking agent availability...');
      const agents = await orchestrator.checkAgents();
      ui.showAgentStatus(agents);

      const availableCount = agents.filter(a => a.available).length;
      if (availableCount === 0) {
        ui.error('No agents available! Please install claude, gemini, or codex CLI.');
        process.exit(1);
      }

      // Parse mode
      const mode = parseMode(options.mode);

      // Use workflow if specified
      if (options.workflow) {
        const workflow = workflowParser.loadWorkflow(options.workflow);
        if (!workflow) {
          ui.error(`Workflow '${options.workflow}' not found`);
          process.exit(1);
        }
        const plan = workflowParser.workflowToPlan(workflow, goal);
        await orchestrator.executePlan(plan);
      } else {
        // Create and execute plan
        await orchestrator.run(goal, mode);
      }
    });

  // Plan command - just create a plan without executing
  program
    .command('plan')
    .description('Create an execution plan without running it')
    .argument('<goal>', 'The goal to plan for')
    .option('-m, --mode <mode>', 'Execution mode', 'iterative')
    .option('-o, --output <file>', 'Save plan to file')
    .action(async (goal, options) => {
      ui.showBanner();

      const config = { ...DEFAULT_CONFIG };
      const orchestrator = new Orchestrator(config, contextManager, ui);

      ui.info('Creating execution plan...');
      const mode = parseMode(options.mode);
      const plan = await orchestrator.createPlan(goal, mode);

      ui.showPlan(plan.tasks, plan.mode);

      if (options.output) {
        const output = JSON.stringify(plan, null, 2);
        fs.writeFileSync(options.output, output);
        ui.success(`Plan saved to ${options.output}`);
      }
    });

  // Workflow commands
  program
    .command('workflow')
    .description('Manage workflows')
    .argument('<action>', 'list, show, create, or run')
    .argument('[name]', 'Workflow name')
    .action(async (action, name) => {
      switch (action) {
        case 'list':
          const workflows = workflowParser.listWorkflows();
          if (workflows.length === 0) {
            ui.info('No workflows found. Creating defaults...');
            workflowParser.createDefaultWorkflows();
            const newWorkflows = workflowParser.listWorkflows();
            ui.success(`Created ${newWorkflows.length} default workflows`);
            newWorkflows.forEach(w => console.log(`  - ${w}`));
          } else {
            console.log('\nAvailable workflows:');
            workflows.forEach(w => console.log(`  - ${w}`));
          }
          break;

        case 'show':
          if (!name) {
            ui.error('Please specify a workflow name');
            return;
          }
          const workflow = workflowParser.loadWorkflow(name);
          if (workflow) {
            console.log('\n' + chalk.bold(workflow.name));
            console.log(chalk.gray(workflow.description));
            console.log(chalk.gray(`Mode: ${workflow.mode}`));
            console.log('\nSteps:');
            workflow.steps.forEach((step, i) => {
              const agent = step.agent ? chalk.cyan(`[${step.agent}]`) : '';
              console.log(`  ${i + 1}. ${step.name} ${agent}`);
              console.log(chalk.gray(`     ${step.action}`));
            });
          } else {
            ui.error(`Workflow '${name}' not found`);
          }
          break;

        case 'create':
          ui.info('Creating default workflows...');
          workflowParser.createDefaultWorkflows();
          ui.success('Default workflows created in ./workflows/');
          break;

        default:
          ui.error(`Unknown action: ${action}`);
      }
    });

  // Context commands
  program
    .command('context')
    .description('Manage project context')
    .argument('<action>', 'show, scan, set, or clear')
    .option('-n, --name <name>', 'Project name')
    .option('-d, --description <desc>', 'Project description')
    .option('-s, --stack <stack>', 'Tech stack (comma-separated)')
    .action(async (action, options) => {
      switch (action) {
        case 'show':
          const ctx = contextManager.getContext();
          console.log('\n' + chalk.bold('Project Context:'));
          console.log(`  Name: ${ctx.projectName}`);
          console.log(`  Path: ${ctx.rootPath}`);
          console.log(`  Description: ${ctx.description || '(not set)'}`);
          console.log(`  Tech Stack: ${ctx.techStack.join(', ') || '(not set)'}`);
          console.log(`  Files: ${Object.keys(ctx.fileStructure).length} directories`);
          break;

        case 'scan':
          ui.startSpinner('Scanning project structure...');
          const structure = await contextManager.scanFileStructure();
          ui.succeedSpinner(`Scanned ${Object.keys(structure).length} directories`);
          break;

        case 'set':
          if (options.name) {
            contextManager.setProjectInfo(options.name, options.description || '');
          }
          if (options.stack) {
            contextManager.setTechStack(options.stack.split(',').map((s: string) => s.trim()));
          }
          ui.success('Context updated');
          break;

        case 'clear':
          // Reset to defaults
          contextManager.updateContext({
            description: '',
            techStack: [],
            fileStructure: {},
            conventions: {}
          });
          ui.success('Context cleared');
          break;

        default:
          ui.error(`Unknown action: ${action}`);
      }
    });

  // Generate GEMINI.md
  program
    .command('gemini-md')
    .description('Generate GEMINI.md context file')
    .option('-o, --output <path>', 'Output path', './GEMINI.md')
    .action((options) => {
      const content = contextManager.generateGeminiMd(options.output);
      ui.success(`Generated ${options.output}`);
    });

  // Single agent execution
  program
    .command('agent')
    .description('Run a task with a specific agent')
    .argument('<agent>', 'Agent to use: claude, gemini, or codex')
    .argument('<task>', 'Task to execute')
    .option('-v, --verbose', 'Verbose output')
    .action(async (agent, task, options) => {
      ui.showBanner();

      const agentType = parseAgent(agent);
      if (!agentType) {
        ui.error(`Unknown agent: ${agent}. Use claude, gemini, or codex.`);
        process.exit(1);
      }

      const config = { ...DEFAULT_CONFIG, verbose: options.verbose };
      const orchestrator = new Orchestrator(config, contextManager, ui);

      await orchestrator.runSingleAgent(agentType, task);
    });

  // Interactive mode
  program
    .command('interactive')
    .alias('i')
    .description('Start interactive mode')
    .action(async () => {
      ui.showBanner();
      ui.info('Interactive mode - type your goals or "exit" to quit');

      const config = { ...DEFAULT_CONFIG, verbose: true };
      const orchestrator = new Orchestrator(config, contextManager, ui);

      // Check agents
      const agents = await orchestrator.checkAgents();
      ui.showAgentStatus(agents);

      // Interactive loop
      const readline = await import('readline');
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });

      const prompt = () => {
        rl.question(chalk.cyan('\n🎯 Goal> '), async (input) => {
          const goal = input.trim();

          if (goal.toLowerCase() === 'exit' || goal.toLowerCase() === 'quit') {
            ui.success('Goodbye!');
            rl.close();
            process.exit(0);
          }

          if (!goal) {
            prompt();
            return;
          }

          try {
            await orchestrator.run(goal, ExecutionMode.ITERATIVE);
          } catch (error) {
            ui.error(`Error: ${error}`);
          }

          prompt();
        });
      };

      prompt();
    });

  // Status command
  program
    .command('status')
    .description('Check system status and agent availability')
    .action(async () => {
      ui.showBanner();

      const config = { ...DEFAULT_CONFIG };
      const orchestrator = new Orchestrator(config, contextManager, ui);

      ui.info('Checking system status...');
      const agents = await orchestrator.checkAgents();
      ui.showAgentStatus(agents);

      // Show recent history
      const history = contextManager.getHistory(5);
      if (history.length > 0) {
        console.log('\nRecent activity:');
        history.forEach(entry => {
          console.log(`  ${chalk.gray(entry.timestamp.toISOString())} [${entry.agent}] ${entry.summary}`);
        });
      }
    });

  // Parse and execute
  await program.parseAsync(process.argv);

  // If no command provided, show help
  if (process.argv.length <= 2) {
    program.help();
  }
}

function parseMode(mode: string): ExecutionMode {
  switch (mode.toLowerCase()) {
    case 'parallel': return ExecutionMode.PARALLEL;
    case 'distributed': return ExecutionMode.DISTRIBUTED;
    case 'iterative':
    default: return ExecutionMode.ITERATIVE;
  }
}

function parseAgent(agent: string): AgentType | null {
  switch (agent.toLowerCase()) {
    case 'claude': return AgentType.CLAUDE;
    case 'gemini': return AgentType.GEMINI;
    case 'codex': return AgentType.CODEX;
    default: return null;
  }
}

// Run main
main().catch(error => {
  console.error(chalk.red('Fatal error:'), error);
  process.exit(1);
});
