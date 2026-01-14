/**
 * Context Manager - Shared context layer for all agents
 * Uses SQLite for persistence via Bun's built-in SQLite support
 */

import { Database } from 'bun:sqlite';
import { AgentType, TaskStatus } from '../core/types';
import type {
  ProjectContext,
  ContextHistoryEntry,
  ExecutionPlan,
  Task,
} from '../core/types';
import * as fs from 'fs';
import * as path from 'path';

export class ContextManager {
  private db: Database;
  private context: ProjectContext;
  private contextPath: string;

  constructor(dbPath: string = './data/orchestrator.db') {
    // Ensure data directory exists
    const dir = path.dirname(dbPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    this.db = new Database(dbPath);
    this.contextPath = dbPath;
    this.initializeDatabase();
    this.context = this.loadOrCreateContext();
  }

  private initializeDatabase(): void {
    // Create tables
    this.db.prepare(`
      CREATE TABLE IF NOT EXISTS context (
        id INTEGER PRIMARY KEY,
        root_path TEXT NOT NULL,
        project_name TEXT NOT NULL,
        description TEXT,
        tech_stack TEXT,
        file_structure TEXT,
        conventions TEXT,
        dependencies TEXT,
        environment TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        action TEXT NOT NULL,
        agent TEXT NOT NULL,
        task_id TEXT,
        summary TEXT
      );

      CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        goal TEXT NOT NULL,
        mode TEXT NOT NULL,
        tasks TEXT NOT NULL,
        thinking_output TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      );

      CREATE TABLE IF NOT EXISTS task_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        success INTEGER,
        output TEXT,
        error TEXT,
        duration REAL,
        agent TEXT,
        files_modified TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plan_id) REFERENCES plans(id)
      );

      CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp);
      CREATE INDEX IF NOT EXISTS idx_task_results_plan ON task_results(plan_id);
    `);
  }

  private loadOrCreateContext(): ProjectContext {
    const row = this.db.query('SELECT * FROM context WHERE id = 1').get() as any;

    if (row) {
      return {
        rootPath: row.root_path,
        projectName: row.project_name,
        description: row.description || '',
        techStack: JSON.parse(row.tech_stack || '[]'),
        fileStructure: JSON.parse(row.file_structure || '{}'),
        conventions: JSON.parse(row.conventions || '{}'),
        dependencies: JSON.parse(row.dependencies || '[]'),
        environment: JSON.parse(row.environment || '{}'),
        history: []
      };
    }

    // Create default context
    const defaultContext: ProjectContext = {
      rootPath: process.cwd(),
      projectName: path.basename(process.cwd()),
      description: '',
      techStack: [],
      fileStructure: {},
      conventions: {},
      dependencies: [],
      environment: {},
      history: []
    };

    this.saveContext(defaultContext);
    return defaultContext;
  }

  saveContext(ctx?: ProjectContext): void {
    const c = ctx || this.context;

    this.db.run(`
      INSERT OR REPLACE INTO context (id, root_path, project_name, description, tech_stack, file_structure, conventions, dependencies, environment, updated_at)
      VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    `, [
      c.rootPath,
      c.projectName,
      c.description,
      JSON.stringify(c.techStack),
      JSON.stringify(c.fileStructure),
      JSON.stringify(c.conventions),
      JSON.stringify(c.dependencies),
      JSON.stringify(c.environment)
    ]);
  }

  getContext(): ProjectContext {
    return { ...this.context };
  }

  updateContext(updates: Partial<ProjectContext>): void {
    this.context = { ...this.context, ...updates };
    this.saveContext();
  }

  setProjectInfo(name: string, description: string, rootPath?: string): void {
    this.context.projectName = name;
    this.context.description = description;
    if (rootPath) this.context.rootPath = rootPath;
    this.saveContext();
  }

  setTechStack(stack: string[]): void {
    this.context.techStack = stack;
    this.saveContext();
  }

  addConvention(key: string, value: string): void {
    this.context.conventions[key] = value;
    this.saveContext();
  }

  // History management
  addHistoryEntry(entry: Omit<ContextHistoryEntry, 'timestamp'>): void {
    this.db.run(`
      INSERT INTO history (action, agent, task_id, summary)
      VALUES (?, ?, ?, ?)
    `, [entry.action, entry.agent, entry.taskId, entry.summary]);
  }

  getHistory(limit: number = 50): ContextHistoryEntry[] {
    const rows = this.db.query(`
      SELECT timestamp, action, agent, task_id, summary
      FROM history
      ORDER BY timestamp DESC
      LIMIT ?
    `).all(limit) as any[];

    return rows.map(row => ({
      timestamp: new Date(row.timestamp),
      action: row.action,
      agent: row.agent as AgentType,
      taskId: row.task_id,
      summary: row.summary
    }));
  }

  // Plan management
  savePlan(plan: ExecutionPlan): void {
    this.db.run(`
      INSERT OR REPLACE INTO plans (id, goal, mode, tasks, thinking_output, status, created_at)
      VALUES (?, ?, ?, ?, ?, 'pending', ?)
    `, [
      plan.id,
      plan.goal,
      plan.mode,
      JSON.stringify(plan.tasks),
      plan.thinkingOutput,
      plan.createdAt.toISOString()
    ]);
  }

  getPlan(planId: string): ExecutionPlan | null {
    const row = this.db.query('SELECT * FROM plans WHERE id = ?').get(planId) as any;

    if (!row) return null;

    return {
      id: row.id,
      goal: row.goal,
      mode: row.mode,
      tasks: JSON.parse(row.tasks),
      thinkingOutput: row.thinking_output,
      createdAt: new Date(row.created_at),
      metadata: {}
    };
  }

  updatePlanStatus(planId: string, status: string): void {
    this.db.run(`
      UPDATE plans SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?
    `, [status, planId]);
  }

  // Task result management
  saveTaskResult(planId: string, result: {
    taskId: string;
    success: boolean;
    output: string;
    error?: string;
    duration: number;
    agent: AgentType;
    filesModified: string[];
  }): void {
    this.db.run(`
      INSERT INTO task_results (plan_id, task_id, success, output, error, duration, agent, files_modified)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      planId,
      result.taskId,
      result.success ? 1 : 0,
      result.output,
      result.error || null,
      result.duration,
      result.agent,
      JSON.stringify(result.filesModified)
    ]);
  }

  getTaskResults(planId: string): any[] {
    return this.db.query(`
      SELECT * FROM task_results WHERE plan_id = ? ORDER BY created_at
    `).all(planId) as any[];
  }

  // File structure scanning
  async scanFileStructure(rootPath?: string): Promise<Record<string, string[]>> {
    const root = rootPath || this.context.rootPath;
    const structure: Record<string, string[]> = {};

    const scanDir = (dir: string, depth: number = 0): void => {
      if (depth > 4) return; // Max depth

      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        const files: string[] = [];

        for (const entry of entries) {
          // Skip hidden and common ignore patterns
          if (entry.name.startsWith('.') ||
            entry.name === 'node_modules' ||
            entry.name === '__pycache__' ||
            entry.name === 'dist' ||
            entry.name === 'build') {
            continue;
          }

          const fullPath = path.join(dir, entry.name);
          const relativePath = path.relative(root, fullPath);

          if (entry.isDirectory()) {
            scanDir(fullPath, depth + 1);
          } else {
            files.push(entry.name);
          }
        }

        if (files.length > 0) {
          const relativeDir = path.relative(root, dir) || '.';
          structure[relativeDir] = files;
        }
      } catch (e) {
        // Ignore permission errors
      }
    };

    scanDir(root);
    this.context.fileStructure = structure;
    this.saveContext();
    return structure;
  }

  // Generate context string for agents
  generateContextString(): string {
    const ctx = this.context;
    const sections: string[] = [];

    sections.push(`# Project: ${ctx.projectName}`);
    if (ctx.description) {
      sections.push(`\n## Description\n${ctx.description}`);
    }

    if (ctx.techStack.length > 0) {
      sections.push(`\n## Tech Stack\n${ctx.techStack.map(t => `- ${t}`).join('\n')}`);
    }

    if (Object.keys(ctx.conventions).length > 0) {
      sections.push(`\n## Conventions`);
      for (const [key, value] of Object.entries(ctx.conventions)) {
        sections.push(`- **${key}**: ${value}`);
      }
    }

    if (Object.keys(ctx.fileStructure).length > 0) {
      sections.push(`\n## Project Structure`);
      for (const [dir, files] of Object.entries(ctx.fileStructure)) {
        sections.push(`### ${dir}/`);
        sections.push(files.map(f => `  - ${f}`).join('\n'));
      }
    }

    return sections.join('\n');
  }

  // Generate GEMINI.md file
  generateGeminiMd(outputPath?: string): string {
    const content = `# ${this.context.projectName}

${this.context.description}

## Tech Stack
${this.context.techStack.map(t => `- ${t}`).join('\n') || '- Not specified'}

## Coding Conventions
${Object.entries(this.context.conventions).map(([k, v]) => `- **${k}**: ${v}`).join('\n') || '- Follow best practices'}

## Project Structure
${Object.entries(this.context.fileStructure).map(([dir, files]) =>
      `### ${dir}/\n${files.map(f => `- ${f}`).join('\n')}`
    ).join('\n\n') || 'Run file scan to populate'}

## Guidelines
- Think before acting
- Test changes when possible
- Follow existing code patterns
- Document significant changes

---
*Auto-generated by Multi-Agent Orchestrator*
`;

    if (outputPath) {
      fs.writeFileSync(outputPath, content);
    }

    return content;
  }

  close(): void {
    this.db.close();
  }
}

export default ContextManager;
