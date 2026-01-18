import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { MCPServerCreateInput } from '@/types/mcp';

export function useMCPServers() {
  return useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => api.getMCPServers(),
  });
}

export function useMCPServer(id: string) {
  return useQuery({
    queryKey: ['mcp-servers', id],
    queryFn: () => api.getMCPServer(id),
    enabled: !!id,
  });
}

export function useCreateMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MCPServerCreateInput) => api.createMCPServer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });
}

export function useUpdateMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MCPServerCreateInput> }) =>
      api.updateMCPServer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });
}

export function useDeleteMCPServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteMCPServer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });
}

export function useTestMCPConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.testMCPConnection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });
}

export function useMCPTools(serverId: string) {
  return useQuery({
    queryKey: ['mcp-tools', serverId],
    queryFn: () => api.getMCPTools(serverId),
    enabled: !!serverId,
  });
}

export function useInvokeMCPTool() {
  return useMutation({
    mutationFn: ({
      serverId,
      toolName,
      input,
    }: {
      serverId: string;
      toolName: string;
      input: Record<string, unknown>;
    }) => api.invokeMCPTool(serverId, toolName, input),
  });
}

export function useCredentials() {
  return useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.getCredentials(),
  });
}

export function useCreateCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; type: string; service: string; value: string }) =>
      api.createCredential(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });
}

export function useDeleteCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteCredential(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });
}
