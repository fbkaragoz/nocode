#!/usr/bin/env bun
/**
 * Multi-Agent Orchestrator - Interactive CLI Entry Point
 *
 * Run with: nocode
 * Or: nocode "your goal here"
 */

import React, { useState } from 'react';
import { render, Box, Text, useInput, useApp } from 'ink';
import TextInput from 'ink-text-input';
import { AgentType, ExecutionMode } from './core/types';
import { AGENT_CONFIGS } from './config/defaults';
import { ContextManager } from './context/manager';
import { Orchestrator } from './core/cli-orchestrator';
import { DEFAULT_CONFIG } from './config/defaults';
import { TerminalUI } from './ui/terminal';

// Check if running with a goal argument
const args = process.argv.slice(2);
const initialGoal = args.length > 0 ? args.join(' ') : '';

// Main App Component
const App: React.FC = () => {
  const { exit } = useApp();

  const [phase, setPhase] = useState<'goal' | 'models' | 'running' | 'done'>(
    initialGoal ? 'models' : 'goal'
  );
  const [goal, setGoal] = useState(initialGoal);
  const [modelStep, setModelStep] = useState(0);
  const [modelInput, setModelInput] = useState('');
  const [models, setModels] = useState({
    gemini: '',
    claude: '',
    codex: '',
  });

  // Handle escape to exit
  useInput((input, key) => {
    if (key.escape) {
      exit();
    }
  });

  // Handle goal submission
  const handleGoalSubmit = () => {
    if (goal.trim()) {
      setPhase('models');
    }
  };

  // Handle model submission
  const handleModelSubmit = () => {
    const modelNames = ['gemini', 'claude', 'codex'];
    const currentModel = modelNames[modelStep];

    if (currentModel) {
      setModels(prev => ({ ...prev, [currentModel]: modelInput.trim() }));
    }

    setModelInput('');

    if (modelStep < 2) {
      setModelStep(modelStep + 1);
    } else {
      // Start execution
      setPhase('running');
      startExecution();
    }
  };

  // Skip model config
  const skipModels = () => {
    setPhase('running');
    startExecution();
  };

  // Start the orchestrator
  const startExecution = async () => {
    // Apply model configs
    if (models.gemini) AGENT_CONFIGS[AgentType.GEMINI].model = models.gemini;
    if (models.claude) AGENT_CONFIGS[AgentType.CLAUDE].model = models.claude;
    if (models.codex) AGENT_CONFIGS[AgentType.CODEX].model = models.codex;

    // Exit the ink app to prevent TUI conflicts with console output
    exit();

    // Now run in plain console mode
    console.clear();
    console.log('\n🤖 nocode - Multi-Agent Orchestrator');
    console.log('━'.repeat(70));
    console.log(`\n📋 Goal: ${goal}\n`);

    // Initialize orchestrator components
    const contextManager = new ContextManager();
    const ui = new TerminalUI();
    const config = { ...DEFAULT_CONFIG, verbose: false };

    // Create orchestrator
    const orchestrator = new Orchestrator(config, contextManager, ui);

    try {
      // Run the orchestrator in parallel mode with role-based agents
      const result = await orchestrator.run(goal, ExecutionMode.PARALLEL);

      // Show final result
      console.log('\n' + '━'.repeat(70));
      if (result.success) {
        console.log('✅ Execution completed successfully!');
        console.log(`⏱️  Total duration: ${(result.totalDuration / 1000).toFixed(1)}s`);
        if (result.filesModified.length > 0) {
          console.log(`📝 Files modified: ${result.filesModified.length}`);
        }
      } else {
        console.log('❌ Execution failed');
        result.errors.forEach(err => console.log(`   ${err}`));
      }
      console.log('━'.repeat(70) + '\n');
      process.exit(result.success ? 0 : 1);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error('\n❌ Error:', errorMsg);
      process.exit(1);
    }
  };

  // Render based on phase
  return (
    <Box flexDirection="column" padding={1}>
      {/* Header - only show once at start */}
      {phase === 'goal' && (
        <Box flexDirection="column">
          <Box justifyContent="center" marginBottom={1}>
            <Text bold color="cyan">🤖 nocode - Multi-Agent Orchestrator</Text>
          </Box>
          <Box justifyContent="center" marginBottom={1}>
            <Text color="gray">Claude + Gemini + Codex Pipeline</Text>
          </Box>
        </Box>
      )}

      {/* Goal Input Phase */}
      {phase === 'goal' && (
        <Box flexDirection="column" marginY={1}>
          <Text color="yellow">What would you like to accomplish?</Text>
          <Box marginTop={1}>
            <Text color="cyan">❯ </Text>
            <TextInput
              value={goal}
              onChange={setGoal}
              onSubmit={handleGoalSubmit}
              placeholder="Enter your goal..."
            />
          </Box>
          <Box marginTop={1}>
            <Text color="gray" dimColor>
              Press Enter to continue • Esc to exit
            </Text>
          </Box>
        </Box>
      )}

      {/* Model Selection Phase */}
      {phase === 'models' && (
        <Box flexDirection="column" marginY={1}>
          <Text color="white">Goal: {goal.slice(0, 60)}...</Text>
          <Box marginTop={1}>
            <Text color="yellow">
              {modelStep === 0 && 'Gemini model (empty = default):'}
              {modelStep === 1 && 'Claude model (empty = default):'}
              {modelStep === 2 && 'Codex model (empty = default):'}
            </Text>
          </Box>
          <Box marginTop={1}>
            <Text color="cyan">❯ </Text>
            <TextInput
              value={modelInput}
              onChange={setModelInput}
              onSubmit={handleModelSubmit}
              placeholder="e.g., gemini-2.5-pro, sonnet, o3-mini"
            />
          </Box>
          <Box marginTop={1}>
            <Text color="gray" dimColor>
              Press Enter to continue • Type 'skip' and Enter to use all defaults
            </Text>
          </Box>
        </Box>
      )}

      {/* Running Phase - Show transition message */}
      {phase === 'running' && (
        <Box flexDirection="column" marginY={1}>
          <Text color="cyan">Starting parallel execution...</Text>
          <Box marginTop={1}>
            <Text color="gray" dimColor>
              Switching to console output mode
            </Text>
          </Box>
        </Box>
      )}
    </Box>
  );
};

// Render the app
render(<App />);
