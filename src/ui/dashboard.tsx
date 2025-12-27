/**
 * Dashboard UI - Terminal User Interface with live updating panels
 *
 * Uses ink (React for terminals) to create a clean dashboard with:
 * - Header with app info
 * - Three agent panels showing live output
 * - Progress indicators
 * - Interactive goal input
 */

import React, { useState, useEffect, useCallback } from 'react';
import { render, Box, Text, useInput, useApp } from 'ink';
import Spinner from 'ink-spinner';
import TextInput from 'ink-text-input';
import { AgentType } from '../core/types';
import { AGENT_CONFIGS } from '../config/defaults';

// Types
interface AgentPanelState {
  status: 'idle' | 'running' | 'success' | 'error';
  output: string[];
  model: string;
  duration?: number;
  error?: string;
}

interface DashboardProps {
  onGoalSubmit: (goal: string, models: Record<AgentType, string>) => Promise<void>;
  initialGoal?: string;
}

// Agent Panel Component
const AgentPanel: React.FC<{
  name: string;
  color: string;
  state: AgentPanelState;
  width: string;
}> = ({ name, color, state, width }) => {
  const statusIcon = {
    idle: '○',
    running: '',
    success: '✓',
    error: '✗',
  }[state.status];

  const statusColor = {
    idle: 'gray',
    running: 'yellow',
    success: 'green',
    error: 'red',
  }[state.status] as 'gray' | 'yellow' | 'green' | 'red';

  // Get last N lines of output
  const maxLines = 8;
  const outputLines = state.output.slice(-maxLines);

  return (
    <Box
      flexDirection="column"
      width={width}
      borderStyle="round"
      borderColor={color as any}
      paddingX={1}
    >
      {/* Header */}
      <Box>
        <Text bold color={color as any}>
          {name}
        </Text>
        <Text> </Text>
        {state.status === 'running' ? (
          <Text color="yellow">
            <Spinner type="dots" />
          </Text>
        ) : (
          <Text color={statusColor}>{statusIcon}</Text>
        )}
        {state.model && (
          <Text color="gray"> ({state.model})</Text>
        )}
      </Box>

      {/* Duration */}
      {state.duration && (
        <Text color="gray" dimColor>
          {(state.duration / 1000).toFixed(1)}s
        </Text>
      )}

      {/* Output */}
      <Box flexDirection="column" marginTop={1}>
        {outputLines.length === 0 ? (
          <Text color="gray" dimColor>
            Waiting...
          </Text>
        ) : (
          outputLines.map((line, i) => (
            <Text key={i} wrap="truncate">
              {line.slice(0, 60)}
            </Text>
          ))
        )}
      </Box>

      {/* Error */}
      {state.error && (
        <Box marginTop={1}>
          <Text color="red">{state.error.slice(0, 50)}</Text>
        </Box>
      )}
    </Box>
  );
};

// Progress Bar Component
const ProgressBar: React.FC<{
  current: number;
  total: number;
  width: number;
}> = ({ current, total, width }) => {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0;
  const filled = Math.round((percent / 100) * width);
  const empty = width - filled;

  return (
    <Box>
      <Text color="green">{'█'.repeat(filled)}</Text>
      <Text color="gray">{'░'.repeat(empty)}</Text>
      <Text> {percent}%</Text>
    </Box>
  );
};

// Main Dashboard Component
export const Dashboard: React.FC<DashboardProps> = ({ onGoalSubmit, initialGoal }) => {
  const { exit } = useApp();

  const [goal, setGoal] = useState(initialGoal || '');
  const [isRunning, setIsRunning] = useState(false);
  const [phase, setPhase] = useState<'input' | 'model-select' | 'running' | 'done'>('input');
  const [selectedModels, setSelectedModels] = useState<Record<AgentType, string>>({
    [AgentType.CLAUDE]: '',
    [AgentType.GEMINI]: '',
    [AgentType.CODEX]: '',
  });
  const [currentModelSelect, setCurrentModelSelect] = useState<AgentType>(AgentType.GEMINI);
  const [modelInput, setModelInput] = useState('');

  const [agents, setAgents] = useState<Record<AgentType, AgentPanelState>>({
    [AgentType.CLAUDE]: { status: 'idle', output: [], model: 'default' },
    [AgentType.GEMINI]: { status: 'idle', output: [], model: 'default' },
    [AgentType.CODEX]: { status: 'idle', output: [], model: 'default' },
  });

  const [progress, setProgress] = useState({ current: 0, total: 0 });

  // Handle keyboard input
  useInput((input, key) => {
    if (key.escape) {
      exit();
    }
  });

  // Handle goal submission
  const handleGoalSubmit = useCallback(async () => {
    if (!goal.trim()) return;
    setPhase('model-select');
  }, [goal]);

  // Handle model selection
  const handleModelSubmit = useCallback(() => {
    const models = { ...selectedModels };
    models[currentModelSelect] = modelInput.trim();
    setSelectedModels(models);
    setModelInput('');

    if (currentModelSelect === AgentType.GEMINI) {
      setCurrentModelSelect(AgentType.CLAUDE);
    } else if (currentModelSelect === AgentType.CLAUDE) {
      setCurrentModelSelect(AgentType.CODEX);
    } else {
      // All models selected, start running
      setPhase('running');
      setIsRunning(true);

      // Update agent models
      setAgents(prev => ({
        [AgentType.CLAUDE]: { ...prev[AgentType.CLAUDE], model: models[AgentType.CLAUDE] || 'default' },
        [AgentType.GEMINI]: { ...prev[AgentType.GEMINI], model: models[AgentType.GEMINI] || 'default' },
        [AgentType.CODEX]: { ...prev[AgentType.CODEX], model: models[AgentType.CODEX] || 'default' },
      }));

      // Start execution
      onGoalSubmit(goal, models).then(() => {
        setIsRunning(false);
        setPhase('done');
      });
    }
  }, [currentModelSelect, modelInput, selectedModels, goal, onGoalSubmit]);

  return (
    <Box flexDirection="column" padding={1}>
      {/* Header */}
      <Box justifyContent="center" marginBottom={1}>
        <Text bold color="cyan">
          🤖 Multi-Agent Orchestrator
        </Text>
      </Box>

      {/* Input Phase */}
      {phase === 'input' && (
        <Box flexDirection="column">
          <Text color="yellow">Enter your goal:</Text>
          <Box marginTop={1}>
            <Text color="cyan">❯ </Text>
            <TextInput
              value={goal}
              onChange={setGoal}
              onSubmit={handleGoalSubmit}
              placeholder="Describe what you want to accomplish..."
            />
          </Box>
          <Box marginTop={1}>
            <Text color="gray" dimColor>
              Press Enter to continue, Esc to exit
            </Text>
          </Box>
        </Box>
      )}

      {/* Model Selection Phase */}
      {phase === 'model-select' && (
        <Box flexDirection="column">
          <Text color="yellow">
            Configure {currentModelSelect === AgentType.GEMINI ? 'Gemini' :
                      currentModelSelect === AgentType.CLAUDE ? 'Claude' : 'Codex'} model:
          </Text>
          <Text color="gray" dimColor>
            (leave empty for default, or enter model name)
          </Text>
          <Box marginTop={1}>
            <Text color="cyan">❯ </Text>
            <TextInput
              value={modelInput}
              onChange={setModelInput}
              onSubmit={handleModelSubmit}
              placeholder="e.g., gemini-2.5-pro, sonnet, o3-mini"
            />
          </Box>
        </Box>
      )}

      {/* Running/Done Phase - Show Agent Panels */}
      {(phase === 'running' || phase === 'done') && (
        <>
          {/* Goal Display */}
          <Box marginBottom={1}>
            <Text color="gray">Goal: </Text>
            <Text>{goal.slice(0, 80)}...</Text>
          </Box>

          {/* Progress Bar */}
          <Box marginBottom={1}>
            <ProgressBar
              current={progress.current}
              total={progress.total || 3}
              width={40}
            />
          </Box>

          {/* Agent Panels - Side by Side */}
          <Box>
            <AgentPanel
              name="Gemini"
              color="blue"
              state={agents[AgentType.GEMINI]}
              width="33%"
            />
            <AgentPanel
              name="Claude"
              color="magenta"
              state={agents[AgentType.CLAUDE]}
              width="33%"
            />
            <AgentPanel
              name="Codex"
              color="green"
              state={agents[AgentType.CODEX]}
              width="33%"
            />
          </Box>

          {/* Status */}
          <Box marginTop={1} justifyContent="center">
            {isRunning ? (
              <Text color="yellow">
                <Spinner type="dots" /> Running...
              </Text>
            ) : (
              <Text color="green">✓ Completed</Text>
            )}
          </Box>
        </>
      )}
    </Box>
  );
};

// Export function to update agent state (called from orchestrator)
export type AgentUpdateFn = (
  agent: AgentType,
  update: Partial<AgentPanelState>
) => void;

export type ProgressUpdateFn = (current: number, total: number) => void;

// Render function
export function renderDashboard(
  onGoalSubmit: DashboardProps['onGoalSubmit'],
  initialGoal?: string
) {
  return render(
    <Dashboard onGoalSubmit={onGoalSubmit} initialGoal={initialGoal} />
  );
}

export default Dashboard;
