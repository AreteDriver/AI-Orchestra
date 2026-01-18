import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AgentRole, Execution } from '@/types';

// =============================================================================
// UI Store - Transient UI state
// =============================================================================

interface UIState {
  sidebarOpen: boolean;
  activeExecution: string | null;
  selectedAgents: AgentRole[];
  logLevel: 'all' | 'info' | 'warn' | 'error';
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveExecution: (id: string | null) => void;
  toggleAgentFilter: (agent: AgentRole) => void;
  clearAgentFilters: () => void;
  setLogLevel: (level: 'all' | 'info' | 'warn' | 'error') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeExecution: null,
  selectedAgents: [],
  logLevel: 'all',

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveExecution: (id) => set({ activeExecution: id }),
  
  toggleAgentFilter: (agent) =>
    set((state) => ({
      selectedAgents: state.selectedAgents.includes(agent)
        ? state.selectedAgents.filter((a) => a !== agent)
        : [...state.selectedAgents, agent],
    })),
  
  clearAgentFilters: () => set({ selectedAgents: [] }),
  setLogLevel: (level) => set({ logLevel: level }),
}));

// =============================================================================
// Preferences Store - Persisted user preferences
// =============================================================================

interface PreferencesState {
  theme: 'light' | 'dark' | 'system';
  compactView: boolean;
  showCosts: boolean;
  defaultPageSize: number;
  notifications: {
    executionComplete: boolean;
    executionFailed: boolean;
    budgetAlert: boolean;
  };
  
  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setCompactView: (compact: boolean) => void;
  setShowCosts: (show: boolean) => void;
  setDefaultPageSize: (size: number) => void;
  setNotification: (key: keyof PreferencesState['notifications'], value: boolean) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: 'system',
      compactView: false,
      showCosts: true,
      defaultPageSize: 20,
      notifications: {
        executionComplete: true,
        executionFailed: true,
        budgetAlert: true,
      },

      setTheme: (theme) => set({ theme }),
      setCompactView: (compactView) => set({ compactView }),
      setShowCosts: (showCosts) => set({ showCosts }),
      setDefaultPageSize: (defaultPageSize) => set({ defaultPageSize }),
      setNotification: (key, value) =>
        set((state) => ({
          notifications: { ...state.notifications, [key]: value },
        })),
    }),
    {
      name: 'gorgon-preferences',
    }
  )
);

// =============================================================================
// Workflow Builder Store - State for workflow editor
// =============================================================================

interface WorkflowStep {
  id: string;
  agentRole: AgentRole;
  name: string;
  config: Record<string, unknown>;
  position: { x: number; y: number };
}

interface WorkflowBuilderState {
  steps: WorkflowStep[];
  selectedStep: string | null;
  isDirty: boolean;
  
  // Actions
  addStep: (step: Omit<WorkflowStep, 'id'>) => void;
  updateStep: (id: string, updates: Partial<WorkflowStep>) => void;
  removeStep: (id: string) => void;
  selectStep: (id: string | null) => void;
  reorderSteps: (fromIndex: number, toIndex: number) => void;
  clearWorkflow: () => void;
  loadWorkflow: (steps: WorkflowStep[]) => void;
  markClean: () => void;
}

export const useWorkflowBuilderStore = create<WorkflowBuilderState>((set) => ({
  steps: [],
  selectedStep: null,
  isDirty: false,

  addStep: (step) =>
    set((state) => ({
      steps: [...state.steps, { ...step, id: crypto.randomUUID() }],
      isDirty: true,
    })),

  updateStep: (id, updates) =>
    set((state) => ({
      steps: state.steps.map((s) => (s.id === id ? { ...s, ...updates } : s)),
      isDirty: true,
    })),

  removeStep: (id) =>
    set((state) => ({
      steps: state.steps.filter((s) => s.id !== id),
      selectedStep: state.selectedStep === id ? null : state.selectedStep,
      isDirty: true,
    })),

  selectStep: (id) => set({ selectedStep: id }),

  reorderSteps: (fromIndex, toIndex) =>
    set((state) => {
      const newSteps = [...state.steps];
      const [removed] = newSteps.splice(fromIndex, 1);
      newSteps.splice(toIndex, 0, removed);
      return { steps: newSteps, isDirty: true };
    }),

  clearWorkflow: () => set({ steps: [], selectedStep: null, isDirty: false }),
  
  loadWorkflow: (steps) => set({ steps, selectedStep: null, isDirty: false }),
  
  markClean: () => set({ isDirty: false }),
}));

// =============================================================================
// Live Execution Store - Real-time execution monitoring
// =============================================================================

interface LiveExecutionState {
  executions: Map<string, Execution>;
  
  // Actions
  setExecution: (execution: Execution) => void;
  removeExecution: (id: string) => void;
  clearExecutions: () => void;
}

export const useLiveExecutionStore = create<LiveExecutionState>((set) => ({
  executions: new Map(),

  setExecution: (execution) =>
    set((state) => {
      const newExecutions = new Map(state.executions);
      newExecutions.set(execution.id, execution);
      return { executions: newExecutions };
    }),

  removeExecution: (id) =>
    set((state) => {
      const newExecutions = new Map(state.executions);
      newExecutions.delete(id);
      return { executions: newExecutions };
    }),

  clearExecutions: () => set({ executions: new Map() }),
}));
