"use client";

import { useEffect, useCallback, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Workspace } from "@/components/workspace";
import { AssistantPanel } from "@/components/assistant-panel";
import { SettingsModal, EntityConfirmationModal } from "@/components/modals";
import { useAppStore, useHasHydrated, Project } from "@/lib/store";
import { fetchAPI } from "@/lib/utils";
import { AlertTriangle, X, Activity } from "lucide-react";

interface ActivePipeline {
  id: string;
  name: string;
  status: string;
  progress: number;
  message: string;
  current_stage?: string;
}

export default function Home() {
  const hasHydrated = useHasHydrated();
  const [isRestoring, setIsRestoring] = useState(true);
  const [showWelcomeBack, setShowWelcomeBack] = useState(false);
  const [activePipelines, setActivePipelines] = useState<ActivePipeline[]>([]);
  const [showActiveAlert, setShowActiveAlert] = useState(false);

  const {
    settingsOpen,
    setSettingsOpen,
    entityConfirmationOpen,
    setEntityConfirmationOpen,
    pendingEntityConfirmation,
    setPendingEntityConfirmation,
    projectPath,
    currentProject,
    lastProjectPath,
    lastSessionTime,
    setCurrentProject,
    setProjects,
    hasRunningProcesses,
    setWorkspaceMode,
  } = useAppStore();

  // Check for active pipelines on backend
  const checkActivePipelines = useCallback(async () => {
    try {
      const result = await fetchAPI<{ active_pipelines: ActivePipeline[]; count: number }>(
        "/api/pipelines/active"
      );
      if (result.count > 0) {
        setActivePipelines(result.active_pipelines);
        setShowActiveAlert(true);
      }
    } catch {
      // Backend might not be running yet
    }
  }, []);

  // Restore last project on startup
  const restoreLastProject = useCallback(async () => {
    if (!lastProjectPath) {
      setIsRestoring(false);
      return;
    }

    try {
      // Fetch all projects
      const projects = await fetchAPI<Project[]>("/api/projects");
      setProjects(projects);

      // Find the last project
      const lastProject = projects.find((p) => p.path === lastProjectPath);
      if (lastProject) {
        setCurrentProject(lastProject);

        // Show welcome back message if session was recent (within 24 hours)
        if (lastSessionTime) {
          const lastTime = new Date(lastSessionTime);
          const hoursSince = (Date.now() - lastTime.getTime()) / (1000 * 60 * 60);
          if (hoursSince < 24) {
            setShowWelcomeBack(true);
            setTimeout(() => setShowWelcomeBack(false), 3000);
          }
        }
      }

      // Also check for active pipelines
      await checkActivePipelines();
    } catch (error) {
      console.error("Failed to restore last project:", error);
    } finally {
      setIsRestoring(false);
    }
  }, [lastProjectPath, lastSessionTime, setCurrentProject, setProjects, checkActivePipelines]);

  // Restore session after hydration
  useEffect(() => {
    if (hasHydrated && !currentProject) {
      restoreLastProject();
    } else if (hasHydrated) {
      setIsRestoring(false);
      // Still check for active pipelines even if we have a project
      checkActivePipelines();
    }
  }, [hasHydrated, currentProject, restoreLastProject, checkActivePipelines]);

  // Check for pending entity confirmation when project loads
  const checkPendingConfirmation = useCallback(async () => {
    if (!projectPath) {
      setPendingEntityConfirmation(false);
      return;
    }

    try {
      const result = await fetchAPI<{
        pending: boolean;
        entity_counts?: { total: number };
      }>(`/api/ingestion/pending-confirmation/${encodeURIComponent(projectPath)}`);

      setPendingEntityConfirmation(result.pending);
    } catch {
      // Silently fail - project may not have any ingestion data yet
      setPendingEntityConfirmation(false);
    }
  }, [projectPath, setPendingEntityConfirmation]);

  // Check on project change
  useEffect(() => {
    checkPendingConfirmation();
  }, [checkPendingConfirmation, currentProject]);

  // Handle entity confirmation completion
  const handleEntityConfirmComplete = useCallback(() => {
    setPendingEntityConfirmation(false);
    setEntityConfirmationOpen(false);
  }, [setPendingEntityConfirmation, setEntityConfirmationOpen]);

  // Warn before closing if pipelines are running
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasRunningProcesses()) {
        e.preventDefault();
        e.returnValue = "Pipelines are still running. Are you sure you want to leave?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasRunningProcesses]);

  // Navigate to progress view when clicking on active pipeline alert
  const handleViewProgress = useCallback(() => {
    setWorkspaceMode("progress");
    setShowActiveAlert(false);
  }, [setWorkspaceMode]);

  // Show loading state while restoring
  if (!hasHydrated || isRestoring) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground text-sm">
            {isRestoring ? "Restoring session..." : "Loading..."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <Workspace />
        <AssistantPanel />
      </div>

      {/* Active Pipelines Alert */}
      {showActiveAlert && activePipelines.length > 0 && (
        <div className="fixed top-16 right-4 bg-amber-500/10 border border-amber-500/30 text-amber-400 px-4 py-3 rounded-lg shadow-lg animate-in slide-in-from-right-2 z-50 max-w-sm">
          <div className="flex items-start gap-3">
            <Activity className="h-5 w-5 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-300">
                {activePipelines.length} pipeline{activePipelines.length > 1 ? "s" : ""} running
              </p>
              <p className="text-xs text-amber-400/80 mt-1">
                {activePipelines.map((p) => p.name).join(", ")}
              </p>
              <button
                onClick={handleViewProgress}
                className="text-xs text-amber-300 hover:text-amber-200 underline mt-2"
              >
                View Progress
              </button>
            </div>
            <button
              onClick={() => setShowActiveAlert(false)}
              className="p-1 hover:bg-amber-500/20 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Welcome back toast */}
      {showWelcomeBack && currentProject && (
        <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg animate-in slide-in-from-bottom-2 z-50">
          <p className="text-sm font-medium">
            Welcome back! Restored: {currentProject.name}
          </p>
        </div>
      )}

      {/* Global Modals */}
      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />

      {/* Entity Confirmation Modal - Globally accessible for recovery */}
      <EntityConfirmationModal
        open={entityConfirmationOpen}
        onOpenChange={setEntityConfirmationOpen}
        onConfirmComplete={handleEntityConfirmComplete}
      />
    </div>
  );
}
