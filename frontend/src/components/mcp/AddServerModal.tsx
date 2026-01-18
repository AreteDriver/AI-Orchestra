import { useState } from 'react';
import { X, Plus, Server } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useCreateMCPServer } from '@/hooks/useMCP';
import { KNOWN_MCP_SERVERS } from '@/types/mcp';
import type { MCPServerCreateInput } from '@/types/mcp';

interface AddServerModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'select' | 'configure';

export function AddServerModal({ onClose, onSuccess }: AddServerModalProps) {
  const [step, setStep] = useState<Step>('select');
  const [selectedPreset, setSelectedPreset] = useState<(typeof KNOWN_MCP_SERVERS)[number] | null>(
    null
  );
  const [customMode, setCustomMode] = useState(false);

  const [formData, setFormData] = useState<MCPServerCreateInput>({
    name: '',
    url: '',
    type: 'sse',
    authType: 'none',
    description: '',
  });

  const createServer = useCreateMCPServer();

  const handlePresetSelect = (preset: (typeof KNOWN_MCP_SERVERS)[number]) => {
    setSelectedPreset(preset);
    setFormData({
      name: preset.name,
      url: preset.url,
      type: preset.type,
      authType: preset.authType,
      description: preset.description,
    });
    setStep('configure');
  };

  const handleCustom = () => {
    setCustomMode(true);
    setStep('configure');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createServer.mutateAsync(formData);
      onSuccess();
    } catch (error) {
      console.error('Failed to create server:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg w-full max-w-lg mx-4 shadow-xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold">
            {step === 'select'
              ? 'Add Connector'
              : customMode
                ? 'Custom MCP Server'
                : `Configure ${selectedPreset?.name}`}
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {step === 'select' ? (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground mb-4">
                Select a service to connect or add a custom MCP server
              </p>

              {/* Preset Options */}
              {KNOWN_MCP_SERVERS.map((preset) => (
                <Card
                  key={preset.id}
                  className="cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => handlePresetSelect(preset)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{preset.name}</h3>
                        <p className="text-sm text-muted-foreground">{preset.description}</p>
                      </div>
                      <Plus className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Custom Option */}
              <Card
                className="cursor-pointer hover:bg-muted/50 transition-colors border-dashed"
                onClick={handleCustom}
              >
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Server className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="font-medium">Custom MCP Server</h3>
                        <p className="text-sm text-muted-foreground">
                          Connect any MCP-compatible server
                        </p>
                      </div>
                    </div>
                    <Plus className="w-5 h-5 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 bg-background"
                  required
                />
              </div>

              {/* URL */}
              <div>
                <label className="block text-sm font-medium mb-1">Server URL</label>
                <input
                  type="text"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://mcp.example.com/sse"
                  className="w-full border rounded-lg px-3 py-2 font-mono text-sm bg-background"
                  required
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-sm font-medium mb-1">Connection Type</label>
                <select
                  value={formData.type}
                  onChange={(e) =>
                    setFormData({ ...formData, type: e.target.value as 'sse' | 'stdio' | 'websocket' })
                  }
                  className="w-full border rounded-lg px-3 py-2 bg-background"
                >
                  <option value="sse">SSE (Server-Sent Events)</option>
                  <option value="websocket">WebSocket</option>
                  <option value="stdio">Stdio (Local Process)</option>
                </select>
              </div>

              {/* Auth Type */}
              <div>
                <label className="block text-sm font-medium mb-1">Authentication</label>
                <select
                  value={formData.authType}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      authType: e.target.value as 'none' | 'bearer' | 'api_key' | 'oauth',
                    })
                  }
                  className="w-full border rounded-lg px-3 py-2 bg-background"
                >
                  <option value="none">None</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="api_key">API Key</option>
                  <option value="oauth">OAuth 2.0</option>
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 bg-background"
                />
              </div>

              {/* Auth notice */}
              {formData.authType !== 'none' && (
                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                  After adding this connector, you'll need to configure credentials in the settings.
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between p-4 border-t bg-muted/30">
          {step === 'configure' && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setStep('select');
                setSelectedPreset(null);
                setCustomMode(false);
              }}
            >
              Back
            </Button>
          )}
          <div className="flex gap-2 ml-auto">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            {step === 'configure' && (
              <Button
                onClick={handleSubmit}
                disabled={!formData.name || !formData.url || createServer.isPending}
              >
                {createServer.isPending ? 'Adding...' : 'Add Connector'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
