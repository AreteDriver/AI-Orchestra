import {
  Github,
  MessageSquare,
  Mail,
  FileText,
  Folder,
  Server,
  Trash2,
  RefreshCw,
  Settings,
  Wrench,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MCPStatusBadge } from './MCPStatusBadge';
import type { MCPServer } from '@/types/mcp';

const iconMap: Record<string, React.ElementType> = {
  github: Github,
  slack: MessageSquare,
  mail: Mail,
  gmail: Mail,
  'file-text': FileText,
  notion: FileText,
  folder: Folder,
  filesystem: Folder,
};

interface MCPServerCardProps {
  server: MCPServer;
  onConfigure: (server: MCPServer) => void;
  onTest: (server: MCPServer) => void;
  onViewTools: (server: MCPServer) => void;
  onDelete: (server: MCPServer) => void;
  isTestingConnection?: boolean;
}

export function MCPServerCard({
  server,
  onConfigure,
  onTest,
  onViewTools,
  onDelete,
  isTestingConnection,
}: MCPServerCardProps) {
  const Icon = iconMap[server.name.toLowerCase()] || Server;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-muted rounded-lg">
              <Icon className="w-6 h-6 text-muted-foreground" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-medium">{server.name}</h3>
                <MCPStatusBadge status={server.status} />
              </div>
              {server.description && (
                <p className="text-sm text-muted-foreground mt-1">{server.description}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                <span>{server.type.toUpperCase()}</span>
                <span>{server.tools.length} tools</span>
                {server.lastConnected && (
                  <span>Last: {new Date(server.lastConnected).toLocaleDateString()}</span>
                )}
              </div>
              {server.error && (
                <p className="text-xs text-destructive mt-1">{server.error}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onTest(server)}
              disabled={isTestingConnection}
              title="Test connection"
            >
              <RefreshCw className={`w-4 h-4 ${isTestingConnection ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewTools(server)}
              title="View tools"
              disabled={server.status !== 'connected'}
            >
              <Wrench className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onConfigure(server)}
              title="Configure"
            >
              <Settings className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(server)}
              title="Remove"
            >
              <Trash2 className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
