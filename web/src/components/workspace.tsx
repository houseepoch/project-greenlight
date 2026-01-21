"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { ScriptView } from "./views/script-view";
import { StoryboardView } from "./views/storyboard-view";
import { WorldView } from "./views/world-view";
import { ProgressView } from "./views/progress-view";
import { ProjectCardsView } from "./views/project-cards-view";
import { NewProjectModal, IngestionModal } from "./modals";

export function Workspace() {
  const { workspaceMode, currentProject } = useAppStore();
  const [newProjectOpen, setNewProjectOpen] = useState(false);
  const [ingestionOpen, setIngestionOpen] = useState(false);

  // Progress view doesn't require a project to be loaded
  if (workspaceMode === "progress") {
    return (
      <main className="flex-1 overflow-hidden bg-background">
        <ProgressView />
      </main>
    );
  }

  if (!currentProject) {
    return (
      <main className="flex-1 overflow-hidden bg-background">
        <ProjectCardsView onNewProject={() => setNewProjectOpen(true)} />
        <NewProjectModal
          open={newProjectOpen}
          onOpenChange={setNewProjectOpen}
          onProjectCreated={() => setIngestionOpen(true)}
        />
        <IngestionModal
          open={ingestionOpen}
          onOpenChange={setIngestionOpen}
          onIngestionComplete={() => setIngestionOpen(false)}
        />
      </main>
    );
  }

  return (
    <main className="flex-1 overflow-hidden bg-background">
      {workspaceMode === "script" && <ScriptView />}
      {workspaceMode === "storyboard" && <StoryboardView />}
      {workspaceMode === "world" && <WorldView />}
    </main>
  );
}

