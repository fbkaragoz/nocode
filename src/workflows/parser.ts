/**
 * Workflow Parser - Parse YAML workflow definitions
 */

import * as fs from 'fs';
import * as path from 'path';
import YAML from 'yaml';
import { ExecutionMode, AgentType, TaskStatus, TaskPriority } from '../core/types';
import type {
  WorkflowDefinition,
  WorkflowStep,
  ExecutionPlan,
  Task,
} from '../core/types';

export class WorkflowParser {
  private workflowsDir: string;

  constructor(workflowsDir: string = './workflows') {
    this.workflowsDir = workflowsDir;
    this.ensureDir();
  }

  private ensureDir(): void {
    if (!fs.existsSync(this.workflowsDir)) {
      fs.mkdirSync(this.workflowsDir, { recursive: true });
    }
  }

  /**
   * Parse a workflow YAML file
   */
  parseFile(filePath: string): WorkflowDefinition {
    const content = fs.readFileSync(filePath, 'utf-8');
    return this.parse(content);
  }

  /**
   * Parse workflow YAML content
   */
  parse(yamlContent: string): WorkflowDefinition {
    const raw = YAML.parse(yamlContent);

    return {
      name: raw.name || 'Unnamed Workflow',
      description: raw.description || '',
      mode: this.parseMode(raw.mode),
      steps: this.parseSteps(raw.steps || []),
      agentAssignments: this.parseAgentAssignments(raw.agent_assignments || raw.agentAssignments || {}),
      conditions: raw.conditions || {},
      onSuccess: raw.on_success || raw.onSuccess || [],
      onFailure: raw.on_failure || raw.onFailure || []
    };
  }

  private parseMode(mode: string | undefined): ExecutionMode {
    switch (mode?.toLowerCase()) {
      case 'parallel': return ExecutionMode.PARALLEL;
      case 'distributed': return ExecutionMode.DISTRIBUTED;
      case 'iterative':
      default: return ExecutionMode.ITERATIVE;
    }
  }

  private parseSteps(steps: any[]): WorkflowStep[] {
    return steps.map((step, index) => ({
      id: step.id || `step_${index + 1}`,
      name: step.name || `Step ${index + 1}`,
      agent: step.agent ? this.parseAgent(step.agent) : undefined,
      action: step.action || step.description || '',
      inputs: step.inputs || {},
      outputs: step.outputs || [],
      dependsOn: step.depends_on || step.dependsOn || [],
      condition: step.condition,
      timeout: step.timeout,
      retries: step.retries
    }));
  }

  private parseAgent(agent: string): AgentType {
    switch (agent.toLowerCase()) {
      case 'claude': return AgentType.CLAUDE;
      case 'gemini': return AgentType.GEMINI;
      case 'codex': return AgentType.CODEX;
      default: return AgentType.CLAUDE;
    }
  }

  private parseAgentAssignments(assignments: Record<string, string>): Record<string, AgentType> {
    const result: Record<string, AgentType> = {};
    for (const [key, value] of Object.entries(assignments)) {
      result[key] = this.parseAgent(value);
    }
    return result;
  }

  /**
   * Convert workflow to execution plan
   */
  workflowToPlan(workflow: WorkflowDefinition, goal?: string): ExecutionPlan {
    const tasks: Task[] = workflow.steps.map(step => ({
      id: step.id,
      description: step.action,
      agent: step.agent || workflow.agentAssignments[step.id],
      status: TaskStatus.PENDING,
      priority: TaskPriority.MEDIUM,
      dependencies: step.dependsOn,
      files: step.outputs,
      estimatedComplexity: 5,
      createdAt: new Date(),
      metadata: {
        inputs: step.inputs,
        condition: step.condition,
        timeout: step.timeout,
        retries: step.retries
      }
    }));

    return {
      id: `plan_${Date.now().toString(36)}`,
      goal: goal || workflow.description || workflow.name,
      mode: workflow.mode,
      tasks,
      thinkingOutput: '',
      createdAt: new Date(),
      metadata: {
        workflowName: workflow.name,
        onSuccess: workflow.onSuccess,
        onFailure: workflow.onFailure
      }
    };
  }

  /**
   * List available workflows
   */
  listWorkflows(): string[] {
    if (!fs.existsSync(this.workflowsDir)) return [];

    return fs.readdirSync(this.workflowsDir)
      .filter(f => f.endsWith('.yaml') || f.endsWith('.yml'))
      .map(f => f.replace(/\.(yaml|yml)$/, ''));
  }

  /**
   * Load a workflow by name
   */
  loadWorkflow(name: string): WorkflowDefinition | null {
    const yamlPath = path.join(this.workflowsDir, `${name}.yaml`);
    const ymlPath = path.join(this.workflowsDir, `${name}.yml`);

    if (fs.existsSync(yamlPath)) {
      return this.parseFile(yamlPath);
    } else if (fs.existsSync(ymlPath)) {
      return this.parseFile(ymlPath);
    }

    return null;
  }

  /**
   * Save a workflow definition
   */
  saveWorkflow(workflow: WorkflowDefinition, name?: string): string {
    const filename = name || workflow.name.toLowerCase().replace(/\s+/g, '-');
    const filePath = path.join(this.workflowsDir, `${filename}.yaml`);

    const yamlContent = YAML.stringify({
      name: workflow.name,
      description: workflow.description,
      mode: workflow.mode,
      steps: workflow.steps.map(step => ({
        id: step.id,
        name: step.name,
        agent: step.agent,
        action: step.action,
        inputs: step.inputs,
        outputs: step.outputs,
        depends_on: step.dependsOn,
        condition: step.condition,
        timeout: step.timeout,
        retries: step.retries
      })),
      agent_assignments: workflow.agentAssignments,
      conditions: workflow.conditions,
      on_success: workflow.onSuccess,
      on_failure: workflow.onFailure
    });

    fs.writeFileSync(filePath, yamlContent);
    return filePath;
  }

  /**
   * Create default workflow templates
   */
  createDefaultWorkflows(): void {
    // Full-stack feature workflow
    const fullStackWorkflow: WorkflowDefinition = {
      name: 'Full-Stack Feature',
      description: 'Build a complete feature from database to UI',
      mode: ExecutionMode.ITERATIVE,
      steps: [
        {
          id: 'plan',
          name: 'Plan Architecture',
          agent: AgentType.CLAUDE,
          action: 'Analyze the feature requirements and design the architecture including database schema, API endpoints, and UI components',
          inputs: { feature: '${goal}' },
          outputs: ['architecture.md'],
          dependsOn: []
        },
        {
          id: 'database',
          name: 'Implement Database',
          agent: AgentType.GEMINI,
          action: 'Create database migrations and models based on the architecture plan',
          inputs: { plan: '${plan.output}' },
          outputs: ['migrations/', 'models/'],
          dependsOn: ['plan']
        },
        {
          id: 'api',
          name: 'Build API',
          agent: AgentType.CODEX,
          action: 'Implement API endpoints with proper validation and error handling',
          inputs: { models: '${database.output}' },
          outputs: ['api/', 'routes/'],
          dependsOn: ['database']
        },
        {
          id: 'ui',
          name: 'Create UI',
          agent: AgentType.CODEX,
          action: 'Build frontend components that consume the API',
          inputs: { api: '${api.output}' },
          outputs: ['components/', 'pages/'],
          dependsOn: ['api']
        },
        {
          id: 'review',
          name: 'Code Review',
          agent: AgentType.CLAUDE,
          action: 'Review all generated code for quality, security, and best practices',
          inputs: { files: '${ui.output}' },
          outputs: ['review.md'],
          dependsOn: ['ui']
        }
      ],
      agentAssignments: {},
      conditions: {},
      onSuccess: ['git add .', 'git commit -m "feat: ${goal}"'],
      onFailure: ['git checkout .']
    };

    // Bug fix workflow
    const bugFixWorkflow: WorkflowDefinition = {
      name: 'Bug Fix',
      description: 'Diagnose and fix a bug',
      mode: ExecutionMode.ITERATIVE,
      steps: [
        {
          id: 'diagnose',
          name: 'Diagnose Issue',
          agent: AgentType.CLAUDE,
          action: 'Analyze the bug report, search for relevant code, and identify the root cause',
          inputs: { bug: '${goal}' },
          outputs: ['diagnosis.md'],
          dependsOn: []
        },
        {
          id: 'fix',
          name: 'Implement Fix',
          agent: AgentType.GEMINI,
          action: 'Implement the fix based on the diagnosis',
          inputs: { diagnosis: '${diagnose.output}' },
          outputs: [],
          dependsOn: ['diagnose']
        },
        {
          id: 'test',
          name: 'Test Fix',
          agent: AgentType.GEMINI,
          action: 'Write and run tests to verify the fix',
          inputs: { fix: '${fix.output}' },
          outputs: ['tests/'],
          dependsOn: ['fix']
        },
        {
          id: 'verify',
          name: 'Verify Fix',
          agent: AgentType.CLAUDE,
          action: 'Review the fix and tests for completeness',
          inputs: { tests: '${test.output}' },
          outputs: ['verification.md'],
          dependsOn: ['test']
        }
      ],
      agentAssignments: {},
      conditions: {},
      onSuccess: [],
      onFailure: []
    };

    // Parallel implementation workflow
    const parallelWorkflow: WorkflowDefinition = {
      name: 'Parallel Development',
      description: 'Develop frontend and backend in parallel',
      mode: ExecutionMode.PARALLEL,
      steps: [
        {
          id: 'plan',
          name: 'Create Plan',
          agent: AgentType.CLAUDE,
          action: 'Create a development plan with clear API contracts',
          inputs: { goal: '${goal}' },
          outputs: ['plan.md', 'api-contract.json'],
          dependsOn: []
        },
        {
          id: 'backend',
          name: 'Backend Development',
          agent: AgentType.GEMINI,
          action: 'Implement backend according to API contract',
          inputs: { contract: '${plan.output}' },
          outputs: ['backend/'],
          dependsOn: ['plan']
        },
        {
          id: 'frontend',
          name: 'Frontend Development',
          agent: AgentType.CODEX,
          action: 'Implement frontend according to API contract',
          inputs: { contract: '${plan.output}' },
          outputs: ['frontend/'],
          dependsOn: ['plan']
        },
        {
          id: 'integrate',
          name: 'Integration',
          agent: AgentType.CLAUDE,
          action: 'Integrate frontend and backend, resolve any issues',
          inputs: {
            backend: '${backend.output}',
            frontend: '${frontend.output}'
          },
          outputs: [],
          dependsOn: ['backend', 'frontend']
        }
      ],
      agentAssignments: {},
      conditions: {},
      onSuccess: [],
      onFailure: []
    };

    this.saveWorkflow(fullStackWorkflow, 'full-stack-feature');
    this.saveWorkflow(bugFixWorkflow, 'bug-fix');
    this.saveWorkflow(parallelWorkflow, 'parallel-development');
  }
}

export default WorkflowParser;
