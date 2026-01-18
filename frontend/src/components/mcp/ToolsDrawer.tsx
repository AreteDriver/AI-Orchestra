import { useState } from 'react';
import { X, Play, ChevronDown, ChevronRight, Code } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useMCPTools, useInvokeMCPTool } from '@/hooks/useMCP';
import type { MCPServer, MCPTool } from '@/types/mcp';

interface ToolsDrawerProps {
  server: MCPServer;
  onClose: () => void;
}

export function ToolsDrawer({ server, onClose }: ToolsDrawerProps) {
  const { data: tools, isLoading } = useMCPTools(server.id);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-lg bg-background shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="font-semibold">{server.name} Tools</h2>
            <p className="text-sm text-muted-foreground">{tools?.length || 0} tools available</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tools List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading tools...</div>
          ) : tools?.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No tools available</div>
          ) : (
            <div className="space-y-3">
              {tools?.map((tool) => (
                <ToolCard key={tool.name} tool={tool} serverId={server.id} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ToolCard({ tool, serverId }: { tool: MCPTool; serverId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [testInput, setTestInput] = useState('{}');
  const [testResult, setTestResult] = useState<string | null>(null);
  const invokeTool = useInvokeMCPTool();

  const handleTest = async () => {
    try {
      const input = JSON.parse(testInput);
      const result = await invokeTool.mutateAsync({ serverId, toolName: tool.name, input });
      setTestResult(JSON.stringify(result, null, 2));
    } catch (error) {
      setTestResult(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <Card className="overflow-hidden">
      <button
        className="w-full p-3 flex items-start gap-3 text-left hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 mt-0.5 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-4 h-4 mt-0.5 text-muted-foreground" />
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-blue-500" />
            <span className="font-mono text-sm font-medium">{tool.name}</span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{tool.description}</p>
        </div>
      </button>

      {expanded && (
        <CardContent className="border-t p-3 bg-muted/30 space-y-3">
          {/* Input Schema */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              Input Schema
            </label>
            <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
              {JSON.stringify(tool.inputSchema, null, 2)}
            </pre>
          </div>

          {/* Test Tool */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              Test Input (JSON)
            </label>
            <textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              className="w-full h-20 p-2 text-xs font-mono border rounded resize-none bg-background"
              placeholder='{"param": "value"}'
            />
          </div>

          <Button size="sm" onClick={handleTest} disabled={invokeTool.isPending}>
            <Play className="w-3 h-3 mr-1" />
            {invokeTool.isPending ? 'Running...' : 'Test Tool'}
          </Button>

          {testResult && (
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Result</label>
              <pre className="text-xs bg-background p-2 rounded border overflow-x-auto max-h-40">
                {testResult}
              </pre>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
