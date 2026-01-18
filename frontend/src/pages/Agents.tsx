import { useState } from 'react';
import {
  Brain,
  Code,
  TestTube,
  Search,
  Building2,
  FileText,
  BarChart3,
  PieChart,
  FileOutput,
  Settings2,
  Power,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { AgentRole, AgentProvider } from '@/types';

interface AgentDefinition {
  role: AgentRole;
  name: string;
  description: string;
  icon: typeof Brain;
  color: string;
  capabilities: string[];
}

const agentDefinitions: AgentDefinition[] = [
  {
    role: 'planner',
    name: 'Planner',
    description: 'Breaks features into actionable steps and creates execution plans',
    icon: Brain,
    color: '#8B5CF6',
    capabilities: ['Task decomposition', 'Dependency analysis', 'Resource estimation'],
  },
  {
    role: 'builder',
    name: 'Builder',
    description: 'Writes production-ready code following best practices',
    icon: Code,
    color: '#3B82F6',
    capabilities: ['Code generation', 'Refactoring', 'Implementation'],
  },
  {
    role: 'tester',
    name: 'Tester',
    description: 'Creates comprehensive test suites and validates functionality',
    icon: TestTube,
    color: '#10B981',
    capabilities: ['Unit tests', 'Integration tests', 'Edge case coverage'],
  },
  {
    role: 'reviewer',
    name: 'Reviewer',
    description: 'Identifies bugs, security issues, and code quality problems',
    icon: Search,
    color: '#F59E0B',
    capabilities: ['Code review', 'Security audit', 'Best practices check'],
  },
  {
    role: 'architect',
    name: 'Architect',
    description: 'Makes architectural decisions and designs system structure',
    icon: Building2,
    color: '#EC4899',
    capabilities: ['System design', 'Pattern selection', 'Scalability planning'],
  },
  {
    role: 'documenter',
    name: 'Documenter',
    description: 'Creates API docs, guides, and technical documentation',
    icon: FileText,
    color: '#6366F1',
    capabilities: ['API documentation', 'README files', 'User guides'],
  },
  {
    role: 'analyst',
    name: 'Analyst',
    description: 'Performs statistical analysis and identifies patterns in data',
    icon: BarChart3,
    color: '#14B8A6',
    capabilities: ['Data analysis', 'Pattern recognition', 'Insights extraction'],
  },
  {
    role: 'visualizer',
    name: 'Visualizer',
    description: 'Creates charts, dashboards, and visual representations',
    icon: PieChart,
    color: '#F97316',
    capabilities: ['Chart generation', 'Dashboard design', 'Data visualization'],
  },
  {
    role: 'reporter',
    name: 'Reporter',
    description: 'Generates executive summaries and status reports',
    icon: FileOutput,
    color: '#8B5CF6',
    capabilities: ['Summary generation', 'Progress reports', 'Stakeholder updates'],
  },
];

interface AgentConfig {
  enabled: boolean;
  provider: AgentProvider;
  model: string;
  temperature: number;
  maxTokens: number;
}

const defaultConfig: AgentConfig = {
  enabled: true,
  provider: 'openai',
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 4096,
};

// Mock data for demo
const mockAgentConfigs: Record<AgentRole, AgentConfig> = {
  planner: { ...defaultConfig, model: 'gpt-4', temperature: 0.3 },
  builder: { ...defaultConfig, model: 'gpt-4', temperature: 0.2 },
  tester: { ...defaultConfig, model: 'gpt-4', temperature: 0.1 },
  reviewer: { ...defaultConfig, model: 'gpt-4', temperature: 0.2 },
  architect: { ...defaultConfig, provider: 'anthropic', model: 'claude-3-opus', temperature: 0.4 },
  documenter: { ...defaultConfig, model: 'gpt-4', temperature: 0.5 },
  analyst: { ...defaultConfig, model: 'gpt-4', temperature: 0.3 },
  visualizer: { ...defaultConfig, enabled: false, model: 'gpt-4-vision', temperature: 0.5 },
  reporter: { ...defaultConfig, model: 'gpt-4', temperature: 0.6 },
};

export function AgentsPage() {
  const [configs, setConfigs] = useState(mockAgentConfigs);
  const [editingAgent, setEditingAgent] = useState<AgentRole | null>(null);

  const enabledCount = Object.values(configs).filter((c) => c.enabled).length;

  const handleToggle = (role: AgentRole) => {
    setConfigs((prev) => ({
      ...prev,
      [role]: { ...prev[role], enabled: !prev[role].enabled },
    }));
  };

  const handleConfigChange = (role: AgentRole, updates: Partial<AgentConfig>) => {
    setConfigs((prev) => ({
      ...prev,
      [role]: { ...prev[role], ...updates },
    }));
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground mt-1">
            {enabledCount} of {agentDefinitions.length} agents enabled
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <span className="text-sm text-muted-foreground">Powered by OpenAI & Anthropic</span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agentDefinitions.map((agent) => (
          <AgentCard
            key={agent.role}
            agent={agent}
            config={configs[agent.role]}
            isEditing={editingAgent === agent.role}
            onToggle={() => handleToggle(agent.role)}
            onEdit={() => setEditingAgent(editingAgent === agent.role ? null : agent.role)}
            onConfigChange={(updates) => handleConfigChange(agent.role, updates)}
          />
        ))}
      </div>
    </div>
  );
}

interface AgentCardProps {
  agent: AgentDefinition;
  config: AgentConfig;
  isEditing: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onConfigChange: (updates: Partial<AgentConfig>) => void;
}

function AgentCard({ agent, config, isEditing, onToggle, onEdit, onConfigChange }: AgentCardProps) {
  const Icon = agent.icon;

  return (
    <Card className={`transition-all ${!config.enabled ? 'opacity-60' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${agent.color}20`, color: agent.color }}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {config.provider} / {config.model}
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onToggle}
            title={config.enabled ? 'Disable agent' : 'Enable agent'}
          >
            <Power className={`h-4 w-4 ${config.enabled ? 'text-green-500' : 'text-muted-foreground'}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{agent.description}</p>

        <div className="flex flex-wrap gap-1">
          {agent.capabilities.map((cap) => (
            <span
              key={cap}
              className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
            >
              {cap}
            </span>
          ))}
        </div>

        <div className="flex items-center justify-between pt-2 border-t">
          <div className="text-xs text-muted-foreground">
            Temp: {config.temperature} | Max: {config.maxTokens.toLocaleString()}
          </div>
          <Button variant="ghost" size="sm" onClick={onEdit}>
            <Settings2 className="h-4 w-4 mr-1" />
            {isEditing ? 'Close' : 'Configure'}
          </Button>
        </div>

        {isEditing && (
          <div className="pt-3 border-t space-y-3">
            <div>
              <label className="text-xs font-medium mb-1 block">Provider</label>
              <select
                value={config.provider}
                onChange={(e) => onConfigChange({ provider: e.target.value as AgentProvider })}
                className="w-full border rounded px-2 py-1.5 text-sm bg-background"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">Model</label>
              <select
                value={config.model}
                onChange={(e) => onConfigChange({ model: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm bg-background"
              >
                {config.provider === 'openai' ? (
                  <>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="gpt-4-vision">GPT-4 Vision</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  </>
                ) : (
                  <>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                    <option value="claude-3-haiku">Claude 3 Haiku</option>
                  </>
                )}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">
                Temperature: {config.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.temperature}
                onChange={(e) => onConfigChange({ temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">Max Tokens</label>
              <select
                value={config.maxTokens}
                onChange={(e) => onConfigChange({ maxTokens: parseInt(e.target.value) })}
                className="w-full border rounded px-2 py-1.5 text-sm bg-background"
              >
                <option value="1024">1,024</option>
                <option value="2048">2,048</option>
                <option value="4096">4,096</option>
                <option value="8192">8,192</option>
                <option value="16384">16,384</option>
              </select>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
