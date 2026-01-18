import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  PaginatedResponse,
  Workflow,
  Execution,
  Agent,
  Budget,
  BudgetSummary,
  Checkpoint,
  DashboardStats,
  SystemHealth,
} from '@/types';

// =============================================================================
// API Client Configuration
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class GorgonApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('gorgon_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('gorgon_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ---------------------------------------------------------------------------
  // Workflows
  // ---------------------------------------------------------------------------

  async getWorkflows(page = 1, pageSize = 20): Promise<PaginatedResponse<Workflow>> {
    const { data } = await this.client.get('/workflows', {
      params: { page, page_size: pageSize },
    });
    return data;
  }

  async getWorkflow(id: string): Promise<Workflow> {
    const { data } = await this.client.get(`/workflows/${id}`);
    return data;
  }

  async createWorkflow(workflow: Partial<Workflow>): Promise<Workflow> {
    const { data } = await this.client.post('/workflows', workflow);
    return data;
  }

  async updateWorkflow(id: string, workflow: Partial<Workflow>): Promise<Workflow> {
    const { data } = await this.client.patch(`/workflows/${id}`, workflow);
    return data;
  }

  async deleteWorkflow(id: string): Promise<void> {
    await this.client.delete(`/workflows/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Executions
  // ---------------------------------------------------------------------------

  async getExecutions(
    page = 1,
    pageSize = 20,
    workflowId?: string
  ): Promise<PaginatedResponse<Execution>> {
    const { data } = await this.client.get('/executions', {
      params: { page, page_size: pageSize, workflow_id: workflowId },
    });
    return data;
  }

  async getExecution(id: string): Promise<Execution> {
    const { data } = await this.client.get(`/executions/${id}`);
    return data;
  }

  async startExecution(workflowId: string, inputs?: Record<string, unknown>): Promise<Execution> {
    const { data } = await this.client.post(`/workflows/${workflowId}/execute`, { inputs });
    return data;
  }

  async pauseExecution(id: string): Promise<Execution> {
    const { data } = await this.client.post(`/executions/${id}/pause`);
    return data;
  }

  async resumeExecution(id: string, checkpointId?: string): Promise<Execution> {
    const { data } = await this.client.post(`/executions/${id}/resume`, {
      checkpoint_id: checkpointId,
    });
    return data;
  }

  async cancelExecution(id: string): Promise<void> {
    await this.client.post(`/executions/${id}/cancel`);
  }

  // ---------------------------------------------------------------------------
  // Agents
  // ---------------------------------------------------------------------------

  async getAgents(): Promise<Agent[]> {
    const { data } = await this.client.get('/agents');
    return data;
  }

  async getAgentStatus(role: string): Promise<Agent> {
    const { data } = await this.client.get(`/agents/${role}`);
    return data;
  }

  // ---------------------------------------------------------------------------
  // Budget
  // ---------------------------------------------------------------------------

  async getBudgets(): Promise<Budget[]> {
    const { data } = await this.client.get('/budgets');
    return data;
  }

  async getBudget(id: string): Promise<Budget> {
    const { data } = await this.client.get(`/budgets/${id}`);
    return data;
  }

  async createBudget(budget: Partial<Budget>): Promise<Budget> {
    const { data } = await this.client.post('/budgets', budget);
    return data;
  }

  async updateBudget(id: string, budget: Partial<Budget>): Promise<Budget> {
    const { data } = await this.client.patch(`/budgets/${id}`, budget);
    return data;
  }

  async getBudgetSummary(): Promise<BudgetSummary> {
    const { data } = await this.client.get('/budgets/summary');
    return data;
  }

  // ---------------------------------------------------------------------------
  // Checkpoints
  // ---------------------------------------------------------------------------

  async getCheckpoints(executionId: string): Promise<Checkpoint[]> {
    const { data } = await this.client.get(`/executions/${executionId}/checkpoints`);
    return data;
  }

  async getCheckpoint(id: string): Promise<Checkpoint> {
    const { data } = await this.client.get(`/checkpoints/${id}`);
    return data;
  }

  async deleteCheckpoint(id: string): Promise<void> {
    await this.client.delete(`/checkpoints/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Dashboard
  // ---------------------------------------------------------------------------

  async getDashboardStats(): Promise<DashboardStats> {
    const { data } = await this.client.get('/dashboard/stats');
    return data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const { data } = await this.client.get('/health');
    return data;
  }

  // ---------------------------------------------------------------------------
  // Auth
  // ---------------------------------------------------------------------------

  async login(credentials: { username: string; password: string }): Promise<{ token: string }> {
    const { data } = await this.client.post('/auth/login', credentials);
    localStorage.setItem('gorgon_token', data.token);
    return data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('gorgon_token');
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('gorgon_token');
  }
}

// Export singleton instance
export const api = new GorgonApiClient();

// Export types for external use
export type { GorgonApiClient };
