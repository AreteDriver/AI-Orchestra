import { useCallback, useMemo } from 'react';
import { X, Trash2, Terminal, PauseCircle, Layers, Split, Merge, GitBranch, Variable } from 'lucide-react';
import { useWorkflowBuilderStore } from '@/stores';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import {
  getAgentRoleInfo,
  isAgentNode,
  isShellNode,
  isCheckpointNode,
  isParallelNode,
  isFanOutNode,
  isFanInNode,
  isMapReduceNode,
  AGENT_ROLES,
  type AgentNodeData,
  type ShellNodeData,
  type CheckpointNodeData,
  type ParallelNodeData,
  type FanOutNodeData,
  type FanInNodeData,
  type MapReduceNodeData,
  type WorkflowNodeData,
} from '@/types/workflow-builder';
import type { AgentRole } from '@/types';

// Agent Node Properties
function AgentProperties({
  data,
  onChange,
}: {
  data: AgentNodeData;
  onChange: (field: keyof AgentNodeData, value: unknown) => void;
}) {
  const roleInfo = getAgentRoleInfo(data.role);

  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Step name"
        />
      </div>

      {/* Role */}
      <div className="space-y-2">
        <Label htmlFor="node-role">Agent Role</Label>
        <Select
          id="node-role"
          value={data.role}
          onChange={(e) => onChange('role', e.target.value as AgentRole)}
        >
          {AGENT_ROLES.map((role) => (
            <option key={role.role} value={role.role}>
              {role.label}
            </option>
          ))}
        </Select>
        <p className="text-xs text-muted-foreground">{roleInfo.description}</p>
      </div>

      {/* Prompt */}
      <div className="space-y-2">
        <Label htmlFor="node-prompt">Prompt</Label>
        <Textarea
          id="node-prompt"
          value={data.prompt || ''}
          onChange={(e) => onChange('prompt', e.target.value)}
          placeholder="Instructions for this agent..."
          rows={4}
        />
      </div>

      {/* On Failure */}
      <div className="space-y-2">
        <Label htmlFor="node-onfailure">On Failure</Label>
        <Select
          id="node-onfailure"
          value={data.onFailure || 'stop'}
          onChange={(e) =>
            onChange('onFailure', e.target.value as 'stop' | 'continue' | 'retry')
          }
        >
          <option value="stop">Stop workflow</option>
          <option value="continue">Continue to next step</option>
          <option value="retry">Retry step</option>
        </Select>
      </div>

      {/* Max Retries */}
      {data.onFailure === 'retry' && (
        <div className="space-y-2">
          <Label htmlFor="node-retries">Max Retries</Label>
          <Input
            id="node-retries"
            type="number"
            min={1}
            max={10}
            value={data.maxRetries || 3}
            onChange={(e) => onChange('maxRetries', parseInt(e.target.value, 10))}
          />
        </div>
      )}

      {/* Outputs */}
      <div className="space-y-2">
        <Label htmlFor="node-outputs">Expected Outputs</Label>
        <Input
          id="node-outputs"
          value={data.outputs?.join(', ') || ''}
          onChange={(e) =>
            onChange(
              'outputs',
              e.target.value
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean)
            )
          }
          placeholder="output1, output2, ..."
        />
        <p className="text-xs text-muted-foreground">
          Comma-separated list of output variable names
        </p>
      </div>
    </>
  );
}

// Shell Node Properties
function ShellProperties({
  data,
  onChange,
}: {
  data: ShellNodeData;
  onChange: (field: keyof ShellNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Step name"
        />
      </div>

      {/* Command */}
      <div className="space-y-2">
        <Label htmlFor="node-command">Command</Label>
        <Textarea
          id="node-command"
          value={data.command || ''}
          onChange={(e) => onChange('command', e.target.value)}
          placeholder="echo 'Hello World'"
          rows={3}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Shell command to execute
        </p>
      </div>

      {/* Allow Failure */}
      <div className="space-y-2">
        <Label htmlFor="node-allowfailure">Allow Failure</Label>
        <Select
          id="node-allowfailure"
          value={data.allowFailure ? 'yes' : 'no'}
          onChange={(e) => onChange('allowFailure', e.target.value === 'yes')}
        >
          <option value="no">No - stop on failure</option>
          <option value="yes">Yes - continue on failure</option>
        </Select>
      </div>

      {/* Timeout */}
      <div className="space-y-2">
        <Label htmlFor="node-timeout">Timeout (seconds)</Label>
        <Input
          id="node-timeout"
          type="number"
          min={1}
          max={3600}
          value={data.timeout || 60}
          onChange={(e) => onChange('timeout', parseInt(e.target.value, 10))}
        />
        <p className="text-xs text-muted-foreground">
          Maximum execution time (1-3600 seconds)
        </p>
      </div>
    </>
  );
}

// Checkpoint Node Properties
function CheckpointProperties({
  data,
  onChange,
}: {
  data: CheckpointNodeData;
  onChange: (field: keyof CheckpointNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Checkpoint name"
        />
      </div>

      {/* Message */}
      <div className="space-y-2">
        <Label htmlFor="node-message">Pause Message</Label>
        <Textarea
          id="node-message"
          value={data.message || ''}
          onChange={(e) => onChange('message', e.target.value)}
          placeholder="Workflow paused for review..."
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Message shown when workflow pauses at this checkpoint
        </p>
      </div>
    </>
  );
}

// Parallel Node Properties
function ParallelProperties({
  data,
  onChange,
}: {
  data: ParallelNodeData;
  onChange: (field: keyof ParallelNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Parallel group name"
        />
      </div>

      {/* Strategy */}
      <div className="space-y-2">
        <Label htmlFor="node-strategy">Execution Strategy</Label>
        <Select
          id="node-strategy"
          value={data.strategy || 'threading'}
          onChange={(e) => onChange('strategy', e.target.value)}
        >
          <option value="threading">Threading (I/O bound)</option>
          <option value="asyncio">Async I/O (concurrent)</option>
          <option value="process">Process (CPU bound)</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          Threading for API calls, Process for CPU-intensive tasks
        </p>
      </div>

      {/* Max Workers */}
      <div className="space-y-2">
        <Label htmlFor="node-maxworkers">Max Workers</Label>
        <Input
          id="node-maxworkers"
          type="number"
          min={1}
          max={20}
          value={data.maxWorkers || 4}
          onChange={(e) => onChange('maxWorkers', parseInt(e.target.value, 10))}
        />
        <p className="text-xs text-muted-foreground">
          Maximum concurrent executions (1-20)
        </p>
      </div>

      {/* Fail Fast */}
      <div className="space-y-2">
        <Label htmlFor="node-failfast">Fail Fast</Label>
        <Select
          id="node-failfast"
          value={data.failFast ? 'yes' : 'no'}
          onChange={(e) => onChange('failFast', e.target.value === 'yes')}
        >
          <option value="no">No - continue on failure</option>
          <option value="yes">Yes - stop all on first failure</option>
        </Select>
      </div>
    </>
  );
}

// Fan Out Node Properties
function FanOutProperties({
  data,
  onChange,
}: {
  data: FanOutNodeData;
  onChange: (field: keyof FanOutNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Fan out name"
        />
      </div>

      {/* Items Variable */}
      <div className="space-y-2">
        <Label htmlFor="node-items">Items Variable</Label>
        <Input
          id="node-items"
          value={data.itemsVariable || ''}
          onChange={(e) => onChange('itemsVariable', e.target.value)}
          placeholder="files"
          className="font-mono"
        />
        <p className="text-xs text-muted-foreground">
          Variable containing the list to iterate over (e.g., "files" for ${'{files}'})
        </p>
      </div>

      {/* Max Concurrent */}
      <div className="space-y-2">
        <Label htmlFor="node-maxconcurrent">Max Concurrent</Label>
        <Input
          id="node-maxconcurrent"
          type="number"
          min={1}
          max={50}
          value={data.maxConcurrent || 5}
          onChange={(e) => onChange('maxConcurrent', parseInt(e.target.value, 10))}
        />
        <p className="text-xs text-muted-foreground">
          Maximum parallel tasks (1-50)
        </p>
      </div>

      {/* Fail Fast */}
      <div className="space-y-2">
        <Label htmlFor="node-failfast">Fail Fast</Label>
        <Select
          id="node-failfast"
          value={data.failFast ? 'yes' : 'no'}
          onChange={(e) => onChange('failFast', e.target.value === 'yes')}
        >
          <option value="no">No - continue on failure</option>
          <option value="yes">Yes - stop all on first failure</option>
        </Select>
      </div>
    </>
  );
}

// Fan In Node Properties
function FanInProperties({
  data,
  onChange,
}: {
  data: FanInNodeData;
  onChange: (field: keyof FanInNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Fan in name"
        />
      </div>

      {/* Input Variable */}
      <div className="space-y-2">
        <Label htmlFor="node-input">Input Variable</Label>
        <Input
          id="node-input"
          value={data.inputVariable || ''}
          onChange={(e) => onChange('inputVariable', e.target.value)}
          placeholder="results"
          className="font-mono"
        />
        <p className="text-xs text-muted-foreground">
          Variable containing results to aggregate
        </p>
      </div>

      {/* Aggregation Method */}
      <div className="space-y-2">
        <Label htmlFor="node-aggregation">Aggregation Method</Label>
        <Select
          id="node-aggregation"
          value={data.aggregation || 'concat'}
          onChange={(e) => onChange('aggregation', e.target.value)}
        >
          <option value="concat">Concatenate</option>
          <option value="claude_code">AI Aggregation</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          How to combine results from parallel branches
        </p>
      </div>

      {/* Aggregate Prompt (shown only for AI aggregation) */}
      {data.aggregation === 'claude_code' && (
        <div className="space-y-2">
          <Label htmlFor="node-prompt">Aggregation Prompt</Label>
          <Textarea
            id="node-prompt"
            value={data.aggregatePrompt || ''}
            onChange={(e) => onChange('aggregatePrompt', e.target.value)}
            placeholder="Combine and summarize these results..."
            rows={4}
          />
          <p className="text-xs text-muted-foreground">
            Instructions for AI to aggregate the results
          </p>
        </div>
      )}
    </>
  );
}

// Map Reduce Node Properties
function MapReduceProperties({
  data,
  onChange,
}: {
  data: MapReduceNodeData;
  onChange: (field: keyof MapReduceNodeData, value: unknown) => void;
}) {
  return (
    <>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="node-name">Name</Label>
        <Input
          id="node-name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Map-Reduce name"
        />
      </div>

      {/* Items Variable */}
      <div className="space-y-2">
        <Label htmlFor="node-items">Items Variable</Label>
        <Input
          id="node-items"
          value={data.itemsVariable || ''}
          onChange={(e) => onChange('itemsVariable', e.target.value)}
          placeholder="log_files"
          className="font-mono"
        />
        <p className="text-xs text-muted-foreground">
          Variable containing the list to process
        </p>
      </div>

      {/* Max Concurrent */}
      <div className="space-y-2">
        <Label htmlFor="node-maxconcurrent">Max Concurrent</Label>
        <Input
          id="node-maxconcurrent"
          type="number"
          min={1}
          max={50}
          value={data.maxConcurrent || 3}
          onChange={(e) => onChange('maxConcurrent', parseInt(e.target.value, 10))}
        />
      </div>

      {/* Map Prompt */}
      <div className="space-y-2">
        <Label htmlFor="node-mapprompt">Map Prompt</Label>
        <Textarea
          id="node-mapprompt"
          value={data.mapPrompt || ''}
          onChange={(e) => onChange('mapPrompt', e.target.value)}
          placeholder="Analyze this item: ${item}"
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Prompt for processing each item (use ${'{item}'} for current item)
        </p>
      </div>

      {/* Reduce Prompt */}
      <div className="space-y-2">
        <Label htmlFor="node-reduceprompt">Reduce Prompt</Label>
        <Textarea
          id="node-reduceprompt"
          value={data.reducePrompt || ''}
          onChange={(e) => onChange('reducePrompt', e.target.value)}
          placeholder="Combine all analysis results into a summary..."
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Prompt for combining all mapped results
        </p>
      </div>

      {/* Fail Fast */}
      <div className="space-y-2">
        <Label htmlFor="node-failfast">Fail Fast</Label>
        <Select
          id="node-failfast"
          value={data.failFast ? 'yes' : 'no'}
          onChange={(e) => onChange('failFast', e.target.value === 'yes')}
        >
          <option value="no">No - continue on failure</option>
          <option value="yes">Yes - stop all on first failure</option>
        </Select>
      </div>
    </>
  );
}

// Available Variables Component
function AvailableVariables({
  nodeId,
  onInsert,
}: {
  nodeId: string;
  onInsert?: (variable: string) => void;
}) {
  const { nodes, edges } = useWorkflowBuilderStore();

  // Find all upstream nodes by traversing edges backwards
  const upstreamVariables = useMemo(() => {
    const variables: { nodeId: string; nodeName: string; outputs: string[] }[] = [];
    const visited = new Set<string>();

    // BFS to find all upstream nodes
    const queue: string[] = [];

    // Find all edges pointing to this node
    edges
      .filter((e) => e.target === nodeId)
      .forEach((e) => queue.push(e.source));

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      if (visited.has(currentId)) continue;
      visited.add(currentId);

      const node = nodes.find((n) => n.id === currentId);
      if (node) {
        const data = node.data;
        let outputs: string[] = [];

        // Get outputs based on node type
        if ('outputs' in data && Array.isArray(data.outputs) && data.outputs.length > 0) {
          outputs = data.outputs;
        } else {
          // Use node ID as implicit output
          outputs = [currentId];
        }

        if (outputs.length > 0) {
          variables.push({
            nodeId: currentId,
            nodeName: ('name' in data ? data.name : currentId) as string,
            outputs,
          });
        }

        // Add upstream nodes of this node
        edges
          .filter((e) => e.target === currentId)
          .forEach((e) => queue.push(e.source));
      }
    }

    return variables;
  }, [nodeId, nodes, edges]);

  if (upstreamVariables.length === 0) {
    return null;
  }

  const handleCopy = (variable: string) => {
    navigator.clipboard.writeText(`\${${variable}}`);
    if (onInsert) {
      onInsert(variable);
    }
  };

  return (
    <div className="space-y-2 border-t pt-4">
      <div className="flex items-center gap-2">
        <Variable className="h-4 w-4 text-indigo-500" />
        <Label className="text-indigo-600 dark:text-indigo-400">Available Variables</Label>
      </div>
      <p className="text-xs text-muted-foreground">
        Click to copy. Use in prompts as ${'{variable}'}.
      </p>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {upstreamVariables.map(({ nodeId: nId, nodeName, outputs }) => (
          <div key={nId} className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">{nodeName}</p>
            <div className="flex flex-wrap gap-1">
              {outputs.map((output) => (
                <button
                  key={output}
                  onClick={() => handleCopy(output)}
                  className="inline-flex items-center rounded bg-indigo-100 dark:bg-indigo-900/30 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors cursor-pointer"
                  title={`Copy \${${output}}`}
                >
                  {output}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PropertyPanel() {
  const { nodes, selectedNodeId, updateNodeData, deleteNode, selectNode } =
    useWorkflowBuilderStore();

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  const handleClose = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  const handleDelete = useCallback(() => {
    if (selectedNodeId) {
      deleteNode(selectedNodeId);
    }
  }, [selectedNodeId, deleteNode]);

  // No selection
  if (!selectedNode) {
    return (
      <div className="h-full w-72 border-l bg-card p-4">
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          Select a node to edit its properties
        </div>
      </div>
    );
  }

  const data = selectedNode.data;

  const handleChange = (field: string, value: unknown) => {
    updateNodeData(selectedNode.id, { [field]: value } as Partial<WorkflowNodeData>);
  };

  // Determine header style based on node type
  let headerBg = '#6b7280'; // default gray
  let headerTitle = 'Properties';
  let HeaderIcon: React.ComponentType<{ className?: string }> | null = null;

  if (isAgentNode(data)) {
    const roleInfo = getAgentRoleInfo(data.role);
    headerBg = roleInfo.color;
    headerTitle = `${roleInfo.label} Properties`;
  } else if (isShellNode(data)) {
    headerBg = '#27272a'; // zinc-800
    headerTitle = 'Shell Command';
    HeaderIcon = Terminal;
  } else if (isCheckpointNode(data)) {
    headerBg = '#f59e0b'; // amber-500
    headerTitle = 'Checkpoint';
    HeaderIcon = PauseCircle;
  } else if (isParallelNode(data)) {
    headerBg = '#8b5cf6'; // violet-500
    headerTitle = 'Parallel Group';
    HeaderIcon = Layers;
  } else if (isFanOutNode(data)) {
    headerBg = '#06b6d4'; // cyan-500
    headerTitle = 'Fan Out';
    HeaderIcon = Split;
  } else if (isFanInNode(data)) {
    headerBg = '#14b8a6'; // teal-500
    headerTitle = 'Fan In';
    HeaderIcon = Merge;
  } else if (isMapReduceNode(data)) {
    headerBg = '#f97316'; // orange-500
    headerTitle = 'Map-Reduce';
    HeaderIcon = GitBranch;
  }

  return (
    <div className="h-full w-72 border-l bg-card overflow-y-auto">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ backgroundColor: headerBg }}
      >
        <div className="flex items-center gap-2">
          {HeaderIcon && (
            <HeaderIcon className={`h-4 w-4 ${isShellNode(data) ? 'text-green-400' : 'text-white'}`} />
          )}
          <span className="text-sm font-medium text-white">{headerTitle}</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClose}
          className="h-6 w-6 text-white hover:bg-white/20"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Form */}
      <div className="p-4 space-y-4">
        {isAgentNode(data) && (
          <AgentProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isShellNode(data) && (
          <ShellProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isCheckpointNode(data) && (
          <CheckpointProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isParallelNode(data) && (
          <ParallelProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isFanOutNode(data) && (
          <FanOutProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isFanInNode(data) && (
          <FanInProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}
        {isMapReduceNode(data) && (
          <MapReduceProperties
            data={data}
            onChange={(field, value) => handleChange(field as string, value)}
          />
        )}

        {/* Available Variables from upstream nodes */}
        <AvailableVariables nodeId={selectedNode.id} />

        {/* Delete Button */}
        <div className="pt-4 border-t">
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            className="w-full gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Delete Node
          </Button>
        </div>
      </div>
    </div>
  );
}
