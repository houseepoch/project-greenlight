import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface Project {
  name: string;
  path: string;
  lastModified?: string;
}

export interface PipelineStatus {
  name: string;
  status: "idle" | "running" | "completed" | "error";
  progress: number;
  message?: string;
}

export interface PipelineLogEntry {
  timestamp: Date;
  message: string;
  type: "info" | "success" | "error" | "warning";
}

export interface WorkspaceMode {
  mode: "script" | "storyboard" | "world" | "progress";
}

// Enhanced pipeline process tracking
export type PipelineStage = "initializing" | "pending" | "running" | "complete" | "error" | "cancelled";

export interface PipelineStageInfo {
  name: string;
  status: PipelineStage;
  startTime?: Date;
  endTime?: Date;
  message?: string;
  started_at?: string;  // ISO string from backend
  completed_at?: string;  // ISO string from backend
}

export interface PipelineProcess {
  id: string;
  backendId?: string;  // Backend process ID for cancellation
  name: string;  // Writer, Director, World Bible, References, Storyboard
  status: PipelineStage;
  progress: number;
  startTime: Date;
  endTime?: Date;
  stages: PipelineStageInfo[];
  logs: PipelineLogEntry[];
  error?: string;
  expanded?: boolean;  // For UI expansion state
  currentStage?: string;  // Name of currently running stage
  currentItem?: string;  // Description of current item being processed
  totalItems?: number;  // Total items to process
  completedItems?: number;  // Number of items completed
  lastLogIndex?: number;  // Track which logs we've already processed
}

// Session state that persists across browser sessions
interface PersistedState {
  // Last project for auto-restore
  lastProjectPath: string | null;

  // Workspace preferences
  workspaceMode: WorkspaceMode["mode"];
  sidebarOpen: boolean;
  progressPanelOpen: boolean;

  // Session metadata
  lastSessionTime: string | null;
}

interface AppState extends PersistedState {
  // Project state
  currentProject: Project | null;
  projectPath: string;
  projects: Project[];
  setCurrentProject: (project: Project | null) => void;
  setProjectPath: (path: string) => void;
  setProjects: (projects: Project[]) => void;

  // Workspace state
  setWorkspaceMode: (mode: WorkspaceMode["mode"]) => void;

  // Pipeline state (legacy - for backward compatibility)
  pipelineStatus: PipelineStatus | null;
  setPipelineStatus: (status: PipelineStatus | null) => void;
  pipelineLogs: PipelineLogEntry[];
  addPipelineLog: (message: string, type?: PipelineLogEntry["type"]) => void;
  clearPipelineLogs: () => void;

  // Enhanced pipeline process tracking
  pipelineProcesses: PipelineProcess[];
  addPipelineProcess: (process: Omit<PipelineProcess, "logs" | "stages">) => void;
  updatePipelineProcess: (id: string, updates: Partial<PipelineProcess>) => void;
  addProcessLog: (processId: string, message: string, type?: PipelineLogEntry["type"]) => void;
  addProcessStage: (processId: string, stage: PipelineStageInfo) => void;
  updateProcessStage: (processId: string, stageName: string, updates: Partial<PipelineStageInfo>) => void;
  toggleProcessExpanded: (processId: string) => void;
  clearCompletedProcesses: () => void;
  cancelProcess: (processId: string) => void;
  hasRunningProcesses: () => boolean;

  // UI state
  setSidebarOpen: (open: boolean) => void;
  assistantOpen: boolean;
  setAssistantOpen: (open: boolean) => void;
  setProgressPanelOpen: (open: boolean) => void;

  // Modal state
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;

  // Entity confirmation state - for recovering from navigation issues
  pendingEntityConfirmation: boolean;
  setPendingEntityConfirmation: (pending: boolean) => void;
  entityConfirmationOpen: boolean;
  setEntityConfirmationOpen: (open: boolean) => void;

  // Connection state
  isConnected: boolean;
  setIsConnected: (connected: boolean) => void;

  // Session hydration state
  _hasHydrated: boolean;
  setHasHydrated: (hydrated: boolean) => void;

  // Session management
  updateLastSessionTime: () => void;
  clearSession: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Persisted state defaults
      lastProjectPath: null,
      workspaceMode: "script",
      sidebarOpen: true,
      progressPanelOpen: true,
      lastSessionTime: null,

      // Hydration state
      _hasHydrated: false,
      setHasHydrated: (hydrated) => set({ _hasHydrated: hydrated }),

      // Project state
      currentProject: null,
      projectPath: "",
      projects: [],
      setCurrentProject: (project) => set({
        currentProject: project,
        projectPath: project?.path || "",
        lastProjectPath: project?.path || null,
        lastSessionTime: new Date().toISOString(),
      }),
      setProjectPath: (path) => set({ projectPath: path }),
      setProjects: (projects) => set({ projects }),

      // Workspace state
      setWorkspaceMode: (mode) => set({ workspaceMode: mode }),

      // Pipeline state (legacy)
      pipelineStatus: null,
      setPipelineStatus: (status) => set({ pipelineStatus: status }),
      pipelineLogs: [],
      addPipelineLog: (message, type = "info") => set((state) => ({
        pipelineLogs: [...state.pipelineLogs, { timestamp: new Date(), message, type }]
      })),
      clearPipelineLogs: () => set({ pipelineLogs: [] }),

      // Enhanced pipeline process tracking
      pipelineProcesses: [],
      addPipelineProcess: (process) => set((state) => ({
        pipelineProcesses: [...state.pipelineProcesses, { ...process, logs: [], stages: [], expanded: true, lastLogIndex: 0 }]
      })),
      updatePipelineProcess: (id, updates) => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === id ? { ...p, ...updates } : p
        )
      })),
      addProcessLog: (processId, message, type = "info") => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === processId
            ? { ...p, logs: [...p.logs, { timestamp: new Date(), message, type }] }
            : p
        )
      })),
      addProcessStage: (processId, stage) => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === processId
            ? { ...p, stages: [...p.stages, stage] }
            : p
        )
      })),
      updateProcessStage: (processId, stageName, updates) => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === processId
            ? {
                ...p,
                stages: p.stages.map(s =>
                  s.name === stageName ? { ...s, ...updates } : s
                )
              }
            : p
        )
      })),
      toggleProcessExpanded: (processId) => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === processId ? { ...p, expanded: !p.expanded } : p
        )
      })),
      clearCompletedProcesses: () => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.filter(
          p => p.status === "running" || p.status === "initializing"
        )
      })),
      cancelProcess: (processId) => set((state) => ({
        pipelineProcesses: state.pipelineProcesses.map(p =>
          p.id === processId
            ? { ...p, status: "cancelled" as PipelineStage, endTime: new Date() }
            : p
        )
      })),
      hasRunningProcesses: () => {
        const state = get();
        return state.pipelineProcesses.some(
          p => p.status === "running" || p.status === "initializing"
        );
      },

      // UI state
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      assistantOpen: false,
      setAssistantOpen: (open) => set({ assistantOpen: open }),
      setProgressPanelOpen: (open) => set({ progressPanelOpen: open }),

      // Modal state
      settingsOpen: false,
      setSettingsOpen: (open) => set({ settingsOpen: open }),

      // Entity confirmation state
      pendingEntityConfirmation: false,
      setPendingEntityConfirmation: (pending) => set({ pendingEntityConfirmation: pending }),
      entityConfirmationOpen: false,
      setEntityConfirmationOpen: (open) => set({ entityConfirmationOpen: open }),

      // Connection state
      isConnected: false,
      setIsConnected: (connected) => set({ isConnected: connected }),

      // Session management
      updateLastSessionTime: () => set({ lastSessionTime: new Date().toISOString() }),
      clearSession: () => set({
        lastProjectPath: null,
        currentProject: null,
        projectPath: "",
        workspaceMode: "script",
        pipelineProcesses: [],
        pipelineLogs: [],
      }),
    }),
    {
      name: "greenlight-session",
      storage: createJSONStorage(() => localStorage),
      // Only persist specific fields including pipeline processes
      partialize: (state) => ({
        lastProjectPath: state.lastProjectPath,
        workspaceMode: state.workspaceMode,
        sidebarOpen: state.sidebarOpen,
        progressPanelOpen: state.progressPanelOpen,
        lastSessionTime: state.lastSessionTime,
        // Persist pipeline processes so they survive refresh
        pipelineProcesses: state.pipelineProcesses.map(p => ({
          ...p,
          // Convert Date objects to ISO strings for serialization
          startTime: p.startTime instanceof Date ? p.startTime.toISOString() : p.startTime,
          endTime: p.endTime instanceof Date ? p.endTime.toISOString() : p.endTime,
          logs: p.logs.map(log => ({
            ...log,
            timestamp: log.timestamp instanceof Date ? log.timestamp.toISOString() : log.timestamp,
          })),
        })),
        pendingEntityConfirmation: state.pendingEntityConfirmation,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        // Restore Date objects from ISO strings after rehydration
        if (state?.pipelineProcesses) {
          state.pipelineProcesses = state.pipelineProcesses.map(p => ({
            ...p,
            startTime: typeof p.startTime === 'string' ? new Date(p.startTime) : p.startTime,
            endTime: p.endTime ? (typeof p.endTime === 'string' ? new Date(p.endTime) : p.endTime) : undefined,
            logs: p.logs.map(log => ({
              ...log,
              timestamp: typeof log.timestamp === 'string' ? new Date(log.timestamp) : log.timestamp,
            })),
          }));
        }
      },
    }
  )
);

// Alias for compatibility with modals
export const useStore = useAppStore;

// Hook to check if store is hydrated (for SSR safety)
export const useHasHydrated = () => useAppStore((state) => state._hasHydrated);
