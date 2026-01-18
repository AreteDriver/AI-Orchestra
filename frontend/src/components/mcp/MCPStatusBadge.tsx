import { CheckCircle, XCircle, Loader, AlertCircle, Settings } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { MCPServerStatus } from '@/types/mcp';

const statusConfig: Record<
  MCPServerStatus,
  {
    icon: React.ElementType;
    variant: 'default' | 'secondary' | 'destructive' | 'outline';
    label: string;
    className?: string;
  }
> = {
  connected: { icon: CheckCircle, variant: 'default', label: 'Connected', className: 'bg-green-100 text-green-700 hover:bg-green-100' },
  disconnected: { icon: XCircle, variant: 'secondary', label: 'Disconnected' },
  error: { icon: AlertCircle, variant: 'destructive', label: 'Error' },
  connecting: { icon: Loader, variant: 'outline', label: 'Connecting', className: 'text-blue-600' },
  not_configured: { icon: Settings, variant: 'outline', label: 'Not Configured', className: 'text-yellow-600' },
};

export function MCPStatusBadge({ status }: { status: MCPServerStatus }) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={config.className}>
      <Icon className={`w-3 h-3 mr-1 ${status === 'connecting' ? 'animate-spin' : ''}`} />
      {config.label}
    </Badge>
  );
}
