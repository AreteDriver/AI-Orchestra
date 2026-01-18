export interface MCPServer {
  id: string;
  name: string;
  url: string;
  type: 'sse' | 'stdio' | 'websocket';
  status: MCPServerStatus;
  description?: string;
  authType: 'none' | 'bearer' | 'api_key' | 'oauth';
  credentialId?: string;
  tools: MCPTool[];
  resources: MCPResource[];
  lastConnected?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export type MCPServerStatus =
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'connecting'
  | 'not_configured';

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export interface MCPResource {
  uri: string;
  name: string;
  mimeType?: string;
  description?: string;
}

export interface Credential {
  id: string;
  name: string;
  type: 'bearer' | 'api_key' | 'oauth';
  service: string;
  createdAt: string;
  lastUsed?: string;
}

export interface MCPServerCreateInput {
  name: string;
  url: string;
  type: 'sse' | 'stdio' | 'websocket';
  authType: 'none' | 'bearer' | 'api_key' | 'oauth';
  credentialId?: string;
  description?: string;
}

export const KNOWN_MCP_SERVERS = [
  {
    id: 'github',
    name: 'GitHub',
    url: 'https://mcp.github.com/sse',
    type: 'sse' as const,
    authType: 'bearer' as const,
    description: 'Access repositories, PRs, issues, and code',
    icon: 'github',
  },
  {
    id: 'slack',
    name: 'Slack',
    url: 'https://mcp.slack.com/sse',
    type: 'sse' as const,
    authType: 'oauth' as const,
    description: 'Send messages, read channels, manage workflows',
    icon: 'slack',
  },
  {
    id: 'notion',
    name: 'Notion',
    url: 'https://mcp.notion.com/mcp',
    type: 'sse' as const,
    authType: 'bearer' as const,
    description: 'Access pages, databases, and workspace content',
    icon: 'file-text',
  },
  {
    id: 'gmail',
    name: 'Gmail',
    url: 'https://mcp.google.com/gmail/sse',
    type: 'sse' as const,
    authType: 'oauth' as const,
    description: 'Read and send emails, manage labels',
    icon: 'mail',
  },
  {
    id: 'filesystem',
    name: 'Filesystem',
    url: 'stdio://mcp-filesystem',
    type: 'stdio' as const,
    authType: 'none' as const,
    description: 'Local file system access (sandboxed)',
    icon: 'folder',
  },
] as const;
