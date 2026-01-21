'use client';

import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import { X, FolderPlus } from 'lucide-react';
import { useStore } from '@/lib/store';
import { fetchAPI } from '@/lib/utils';

interface NewProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated?: () => void;
}

export function NewProjectModal({ open, onOpenChange, onProjectCreated }: NewProjectModalProps) {
  const { setProjectPath, setCurrentProject } = useStore();
  const [name, setName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setIsCreating(true);
    setError(null);

    try {
      const response = await fetchAPI<{ success: boolean; project_path?: string; name?: string }>('/api/projects/create', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim()
        })
      });

      if (response.project_path) {
        setProjectPath(response.project_path);
        setCurrentProject({
          name: response.name || name.trim(),
          path: response.project_path
        });
        setName('');
        onOpenChange(false);
        onProjectCreated?.();
      } else {
        setError('No project path returned from server');
      }
    } catch (e) {
      console.error('Failed to create project:', e);
      setError(e instanceof Error ? e.message : 'Failed to create project');
    } finally {
      setIsCreating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && name.trim()) {
      handleCreate();
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] bg-gradient-to-br from-[#0a1f0a] via-[#0d0d0d] to-[#0a0a0a] border border-[#39ff14]/30 rounded-lg shadow-xl shadow-[#39ff14]/10 z-50">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Create a new storyboard project.
            </Dialog.Description>
          </VisuallyHidden.Root>

          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gl-border">
            <Dialog.Title className="text-lg font-semibold text-gl-text-primary flex items-center gap-2">
              <FolderPlus className="w-5 h-5 text-gl-accent" /> New Project
            </Dialog.Title>
            <Dialog.Close className="p-1 hover:bg-gl-bg-hover rounded">
              <X className="w-4 h-4 text-gl-text-muted" />
            </Dialog.Close>
          </div>

          {/* Content */}
          <div className="p-5">
            <label className="block text-sm text-gl-text-secondary mb-2">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              className="w-full px-3 py-2.5 bg-gl-bg-medium border border-gl-border rounded-md text-gl-text-primary placeholder:text-gl-text-muted focus:outline-none focus:border-gl-accent/50 focus:ring-1 focus:ring-gl-accent/30"
              placeholder="Enter project name..."
            />

            {error && (
              <div className="mt-3 p-2.5 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-2 px-5 py-4 border-t border-gray-700">
            <button
              onClick={() => onOpenChange(false)}
              className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={!name.trim() || isCreating}
              className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 border border-green-500 rounded-md font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
