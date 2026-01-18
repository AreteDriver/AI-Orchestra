import { useState } from 'react';
import { X, Key, Eye, EyeOff, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useCredentials, useCreateCredential, useDeleteCredential, useUpdateMCPServer } from '@/hooks/useMCP';
import type { MCPServer, Credential } from '@/types/mcp';

interface ConfigureServerModalProps {
  server: MCPServer;
  onClose: () => void;
  onSuccess: () => void;
}

export function ConfigureServerModal({ server, onClose, onSuccess }: ConfigureServerModalProps) {
  const { data: credentials } = useCredentials();
  const deleteCredential = useDeleteCredential();
  const updateServer = useUpdateMCPServer();

  const [showAddCredential, setShowAddCredential] = useState(false);
  const [selectedCredentialId, setSelectedCredentialId] = useState(server.credentialId || '');
  const [isSaving, setIsSaving] = useState(false);

  // Filter credentials for this service type
  const serviceCredentials = credentials?.filter(
    (c) => c.service === server.name.toLowerCase() || c.service === 'custom'
  );

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateServer.mutateAsync({
        id: server.id,
        data: { credentialId: selectedCredentialId || undefined },
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to update server:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg w-full max-w-md mx-4 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold">Configure {server.name}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Connection Info */}
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Server URL
            </label>
            <p className="font-mono text-sm bg-muted p-2 rounded">{server.url}</p>
          </div>

          {/* Auth Required */}
          {server.authType !== 'none' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">
                  <Key className="w-4 h-4 inline mr-1" />
                  Credentials
                </label>

                {serviceCredentials?.length === 0 && !showAddCredential ? (
                  <div className="text-center py-4 border-2 border-dashed rounded-lg">
                    <p className="text-sm text-muted-foreground mb-2">No credentials configured</p>
                    <Button size="sm" onClick={() => setShowAddCredential(true)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Credential
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {serviceCredentials?.map((cred) => (
                      <CredentialRow
                        key={cred.id}
                        credential={cred}
                        isSelected={selectedCredentialId === cred.id}
                        onSelect={() => setSelectedCredentialId(cred.id)}
                        onDelete={() => deleteCredential.mutate(cred.id)}
                      />
                    ))}

                    {!showAddCredential && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full"
                        onClick={() => setShowAddCredential(true)}
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Add New Credential
                      </Button>
                    )}
                  </div>
                )}
              </div>

              {/* Add Credential Form */}
              {showAddCredential && (
                <AddCredentialForm
                  service={server.name.toLowerCase()}
                  authType={server.authType}
                  onCancel={() => setShowAddCredential(false)}
                  onSuccess={(credId) => {
                    setShowAddCredential(false);
                    setSelectedCredentialId(credId);
                  }}
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t bg-muted/30">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>
    </div>
  );
}

function CredentialRow({
  credential,
  isSelected,
  onSelect,
  onDelete,
}: {
  credential: Credential;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-colors ${
        isSelected ? 'ring-2 ring-primary bg-primary/5' : 'hover:bg-muted/50'
      }`}
      onClick={onSelect}
    >
      <CardContent className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <input
              type="radio"
              checked={isSelected}
              onChange={onSelect}
              className="text-primary"
            />
            <div>
              <p className="font-medium text-sm">{credential.name}</p>
              <p className="text-xs text-muted-foreground">
                {credential.type} • Added {new Date(credential.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('Delete this credential?')) onDelete();
            }}
          >
            <Trash2 className="w-4 h-4 text-destructive" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function AddCredentialForm({
  service,
  authType,
  onCancel,
  onSuccess,
}: {
  service: string;
  authType: string;
  onCancel: () => void;
  onSuccess: (credentialId: string) => void;
}) {
  const createCredential = useCreateCredential();
  const [name, setName] = useState(`${service} token`);
  const [value, setValue] = useState('');
  const [showValue, setShowValue] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const cred = await createCredential.mutateAsync({
        name,
        type: authType,
        service,
        value,
      });
      onSuccess(cred.id);
    } catch (error) {
      console.error('Failed to create credential:', error);
    }
  };

  return (
    <Card className="bg-muted/30">
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Credential Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm bg-background"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {authType === 'bearer' ? 'Token' : authType === 'api_key' ? 'API Key' : 'Secret'}
            </label>
            <div className="relative">
              <input
                type={showValue ? 'text' : 'password'}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm font-mono pr-10 bg-background"
                placeholder="Enter your token or key"
                required
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
                onClick={() => setShowValue(!showValue)}
              >
                {showValue ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Stored securely. Never transmitted to external services except during MCP connection.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={!value || createCredential.isPending}>
              {createCredential.isPending ? 'Saving...' : 'Save Credential'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
