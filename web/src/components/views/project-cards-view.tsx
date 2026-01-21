"use client";

import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { fetchAPI } from "@/lib/utils";
import { FolderPlus, Clock, FileText, Globe, Film, Clapperboard, Check, ChevronRight, Trash2, MoreVertical, X, AlertTriangle, ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import * as Dialog from "@radix-ui/react-dialog";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

interface ProjectInfo {
  name: string;
  path: string;
  created_at: string;
  last_modified: string;
  has_pitch: boolean;
  has_world_config: boolean;
  has_script: boolean;
  has_visual_script: boolean;
  has_storyboard: boolean;
}

// Pipeline stage metadata
const PIPELINE_STAGES = [
  { key: 'has_pitch', label: 'Pitch', next: 'Add a pitch document', icon: FileText },
  { key: 'has_world_config', label: 'World Bible', next: 'Build world bible', icon: Globe },
  { key: 'has_script', label: 'Outline', next: 'Generate outline', icon: FileText },
  { key: 'has_visual_script', label: 'Director', next: 'Run director pipeline', icon: Clapperboard },
  { key: 'has_storyboard', label: 'Storyboard', next: 'Generate storyboard', icon: Film },
] as const;

interface ProjectCardsViewProps {
  onNewProject: () => void;
}

export function ProjectCardsView({ onNewProject }: ProjectCardsViewProps) {
  const { setCurrentProject, setProjectPath } = useAppStore();
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<ProjectInfo | null>(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await fetchAPI<ProjectInfo[]>('/api/projects');
      setProjects(data || []);
    } catch (e) {
      console.error('Failed to load projects:', e);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project: ProjectInfo) => {
    setCurrentProject({ name: project.name, path: project.path });
    setProjectPath(project.path);
  };

  const handleDeleteProject = async () => {
    if (!deleteTarget || deleteConfirmText !== "DELETE") return;

    setIsDeleting(true);
    try {
      await fetchAPI(`/api/projects/path-data/project?path=${encodeURIComponent(deleteTarget.path)}`, {
        method: 'DELETE'
      });
      // Remove from local state
      setProjects(projects.filter(p => p.path !== deleteTarget.path));
      setDeleteTarget(null);
      setDeleteConfirmText("");
    } catch (e) {
      console.error('Failed to delete project:', e);
    } finally {
      setIsDeleting(false);
    }
  };

  const openDeleteDialog = (project: ProjectInfo, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteTarget(project);
    setDeleteConfirmText("");
  };

  const closeDeleteDialog = () => {
    setDeleteTarget(null);
    setDeleteConfirmText("");
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getPipelineProgress = (project: ProjectInfo) => {
    const stages = PIPELINE_STAGES.map(stage => ({
      ...stage,
      done: project[stage.key as keyof ProjectInfo] as boolean,
    }));
    const completed = stages.filter(s => s.done).length;

    // Find next step
    const nextStage = stages.find(s => !s.done);

    return { stages, completed, total: stages.length, nextStage };
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-muted-foreground">Loading projects...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Projects</h1>
            <p className="text-muted-foreground mt-1">Select a project or create a new one</p>
          </div>
          <button
            onClick={onNewProject}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-md font-medium transition-colors"
          >
            <FolderPlus className="h-4 w-4" />
            New Project
          </button>
        </div>

        {/* Projects Grid */}
        {projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => {
              const progress = getPipelineProgress(project);
              return (
                <div
                  key={project.path}
                  className="group relative text-left p-4 bg-card border border-border rounded-lg hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all cursor-pointer"
                  onClick={() => handleSelectProject(project)}
                >
                  {/* Project Name */}
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                      {project.name}
                    </h3>
                    <div className="flex items-center gap-1">
                      <DropdownMenu.Root>
                        <DropdownMenu.Trigger asChild>
                          <button
                            onClick={(e) => e.stopPropagation()}
                            className="p-1 rounded hover:bg-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <MoreVertical className="h-4 w-4 text-muted-foreground" />
                          </button>
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Portal>
                          <DropdownMenu.Content
                            className="min-w-[160px] bg-card border border-border rounded-md shadow-lg p-1 z-50"
                            sideOffset={5}
                          >
                            <DropdownMenu.Item
                              className="flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded cursor-pointer outline-none"
                              onClick={(e) => openDeleteDialog(project, e)}
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete Project
                            </DropdownMenu.Item>
                          </DropdownMenu.Content>
                        </DropdownMenu.Portal>
                      </DropdownMenu.Root>
                      <ChevronRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>

                  {/* Last Modified */}
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-2">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{formatDate(project.last_modified)}</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
                      <span>Pipeline Progress</span>
                      <span>{progress.completed}/{progress.total}</span>
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${(progress.completed / progress.total) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Stage Icons */}
                  <div className="flex items-center gap-2 mt-3">
                    {progress.stages.map((stage) => {
                      const Icon = stage.icon;
                      const isNext = progress.nextStage?.key === stage.key;
                      return (
                        <div
                          key={stage.label}
                          className={cn(
                            "flex items-center justify-center w-7 h-7 rounded-full text-xs transition-all",
                            stage.done
                              ? "bg-success/20 text-success"
                              : isNext
                              ? "bg-primary/20 text-primary ring-2 ring-primary/30"
                              : "bg-secondary text-muted-foreground"
                          )}
                          title={stage.done ? `${stage.label} complete` : stage.next}
                        >
                          {stage.done ? (
                            <Check className="h-3.5 w-3.5" />
                          ) : isNext ? (
                            <ArrowRight className="h-3.5 w-3.5" />
                          ) : (
                            <Icon className="h-3.5 w-3.5" />
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Next Step Hint */}
                  {progress.nextStage && (
                    <div className="flex items-center gap-1.5 mt-3 text-xs text-primary">
                      <Sparkles className="h-3 w-3" />
                      <span>Next: {progress.nextStage.next}</span>
                    </div>
                  )}

                  {/* Completed Badge */}
                  {!progress.nextStage && (
                    <div className="flex items-center gap-1.5 mt-3 text-xs text-success">
                      <Check className="h-3 w-3" />
                      <span>Pipeline complete</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16 border border-dashed border-border rounded-lg">
            <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto">
              <FolderPlus className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mt-4 font-semibold">No Projects Yet</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Create your first project to get started
            </p>
            <button
              onClick={onNewProject}
              className="mt-4 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-md font-medium transition-colors"
            >
              Create Project
            </button>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog.Root open={!!deleteTarget} onOpenChange={(open) => !open && closeDeleteDialog()}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-card border border-border rounded-lg shadow-xl p-6 w-full max-w-md z-50">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-destructive/10 rounded-full">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <Dialog.Title className="text-lg font-semibold">
                Delete Project
              </Dialog.Title>
            </div>

            <Dialog.Description className="text-muted-foreground mb-4">
              Are you sure you want to delete <span className="font-semibold text-foreground">{deleteTarget?.name}</span>?
              This action cannot be undone and will permanently remove all project files including:
            </Dialog.Description>

            <ul className="text-sm text-muted-foreground mb-4 space-y-1 pl-4">
              <li>- World bible and character data</li>
              <li>- Reference images</li>
              <li>- Storyboard outputs</li>
              <li>- All generated content</li>
            </ul>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Type <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-destructive">DELETE</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="w-full px-3 py-2 bg-secondary border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-destructive/50"
                autoFocus
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={closeDeleteDialog}
                className="px-4 py-2 text-sm hover:bg-secondary rounded-md transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteProject}
                disabled={deleteConfirmText !== "DELETE" || isDeleting}
                className="px-4 py-2 text-sm bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isDeleting ? "Deleting..." : "Delete Project"}
              </button>
            </div>

            <Dialog.Close asChild>
              <button
                className="absolute top-4 right-4 p-1 hover:bg-secondary rounded"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
