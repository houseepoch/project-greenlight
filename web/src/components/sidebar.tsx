"use client";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import {
  FileText,
  Image,
  Globe,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  Activity,
  AlertCircle,
  Sparkles,
} from "lucide-react";

const navItems = [
  { id: "script" as const, label: "Script", icon: FileText },
  { id: "storyboard" as const, label: "Storyboard", icon: Image },
  { id: "world" as const, label: "World Bible", icon: Globe },
  { id: "progress" as const, label: "Progress", icon: Activity },
];

export function Sidebar() {
  const {
    workspaceMode,
    setWorkspaceMode,
    sidebarOpen,
    setSidebarOpen,
    currentProject,
    pendingEntityConfirmation,
    setEntityConfirmationOpen,
  } = useAppStore();

  return (
    <aside
      className={cn(
        "flex flex-col bg-card border-r border-border transition-all duration-300",
        sidebarOpen ? "w-56" : "w-14"
      )}
    >
      {/* Project Header */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        {sidebarOpen && (
          <div className="flex items-center gap-2 overflow-hidden">
            <FolderOpen className="h-4 w-4 text-primary shrink-0" />
            <span className="text-sm font-medium truncate">
              {currentProject?.name || "No Project"}
            </span>
          </div>
        )}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1 hover:bg-secondary rounded"
        >
          {sidebarOpen ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = workspaceMode === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setWorkspaceMode(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-secondary text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {sidebarOpen && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </button>
          );
        })}

        {/* Pending Entity Confirmation Alert */}
        {pendingEntityConfirmation && currentProject && (
          <button
            onClick={() => {
              setEntityConfirmationOpen(true);
              setWorkspaceMode('progress');  // Also switch to progress view
            }}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors mt-2",
              "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30"
            )}
            title="Resume entity confirmation"
          >
            <div className="relative shrink-0">
              <Sparkles className="h-4 w-4" />
              <AlertCircle className="h-2.5 w-2.5 absolute -top-1 -right-1 text-amber-500" />
            </div>
            {sidebarOpen && (
              <span className="text-sm font-medium">Confirm Entities</span>
            )}
          </button>
        )}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border">
        {sidebarOpen && (
          <div className="text-xs text-muted-foreground">
            Project Greenlight
          </div>
        )}
      </div>
    </aside>
  );
}

