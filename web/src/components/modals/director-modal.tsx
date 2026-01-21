'use client';

import { useState, useEffect, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import { X, Play, Loader2, Film, FileText, AlertCircle } from 'lucide-react';
import { useStore, useAppStore } from '@/lib/store';
import { fetchAPI } from '@/lib/utils';
import { toast } from '@/components/toast';

interface DirectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface OutlineData {
  title: string;
  beats: string[];
  confirmed_at?: string;
}

const LLM_OPTIONS = [
  { key: 'claude-opus-4.5', name: 'Claude Opus 4.5' },
  { key: 'claude-haiku-4.5', name: 'Claude Haiku 4.5' },
  { key: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
  { key: 'gemini-3-pro', name: 'Gemini 3 Pro' },
  { key: 'grok-4', name: 'Grok 4' },
];

export function DirectorModal({ open, onOpenChange }: DirectorModalProps) {
  const { projectPath } = useStore();
  const { addPipelineProcess, updatePipelineProcess, addProcessLog, setWorkspaceMode } = useAppStore();
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [outlineData, setOutlineData] = useState<OutlineData | null>(null);
  const [outlineExists, setOutlineExists] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedLLM, setSelectedLLM] = useState('claude-haiku-4.5');

  // Polling cleanup refs
  const pollingActiveRef = useRef(false);
  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      pollingActiveRef.current = false;
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
        pollTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (open && projectPath) {
      loadOutlineData();
    }
  }, [open, projectPath]);

  const loadOutlineData = async () => {
    setLoading(true);
    try {
      // Check pipeline validation to see what's available
      const validation = await fetchAPI<{
        pipelines: {
          director: { ready: boolean; missing_requirements: string[] };
        };
      }>(`/api/pipelines/validate/${encodeURIComponent(projectPath)}`);

      if (validation.pipelines.director.ready) {
        // Try to load the confirmed outline
        const response = await fetchAPI<{ success: boolean; data?: { confirmed_beats?: string[]; title?: string } }>(
          `/api/pipelines/outlines/${encodeURIComponent(projectPath)}`
        );

        if (response.success && response.data?.confirmed_beats && response.data.confirmed_beats.length > 0) {
          setOutlineData({
            title: response.data.title || 'Untitled',
            beats: response.data.confirmed_beats,
          });
          setOutlineExists(true);
        } else {
          setOutlineExists(false);
        }
      } else {
        setOutlineExists(false);
      }
    } catch (e) {
      console.error('Failed to load outline data:', e);
      setOutlineExists(false);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    if (!projectPath || !outlineExists) return;
    setIsRunning(true);
    setProgress(0);
    setLogs([]);

    // Create a new process in the global store
    const processId = `director-${Date.now()}`;
    addPipelineProcess({
      id: processId,
      name: `Director: ${outlineData?.beats.length || 0} beats`,
      status: 'initializing',
      progress: 0,
      startTime: new Date(),
    });

    // Close modal and switch to progress view
    onOpenChange(false);
    setWorkspaceMode('progress');

    try {
      addProcessLog(processId, 'Starting Director pipeline...', 'info');
      updatePipelineProcess(processId, { status: 'running' });

      const response = await fetchAPI<{ success: boolean; pipeline_id?: string; message?: string }>(
        '/api/pipelines/director',
        {
          method: 'POST',
          body: JSON.stringify({
            project_path: projectPath,
            llm: selectedLLM
          })
        }
      );

      if (response.success && response.pipeline_id) {
        // Store backend ID for resume capability
        updatePipelineProcess(processId, { backendId: response.pipeline_id });
        addProcessLog(processId, `Pipeline started with ID: ${response.pipeline_id}`, 'info');
        pollStatus(response.pipeline_id, processId);
      } else {
        throw new Error(response.message || 'Failed to start pipeline');
      }
    } catch (e) {
      addProcessLog(processId, `Error: ${e}`, 'error');
      updatePipelineProcess(processId, { status: 'error', error: String(e), endTime: new Date() });
      setIsRunning(false);
    }
  };

  const pollStatus = async (pipelineId: string, processId: string) => {
    let lastLogIndex = 0;
    pollingActiveRef.current = true;

    const poll = async () => {
      // Check if polling was stopped
      if (!pollingActiveRef.current) return;

      try {
        const status = await fetchAPI<{
          status: string;
          progress?: number;
          logs?: string[];
          current_stage?: string;
          stages?: Array<{ name: string; status: string; message?: string }>;
        }>(`/api/pipelines/status/${pipelineId}`);

        // Check again after async call
        if (!pollingActiveRef.current) return;

        setProgress(status.progress || 0);

        // Build update object with all new fields
        const updates: Record<string, unknown> = {
          progress: status.progress || 0,
        };

        // Update current stage
        if (status.current_stage !== undefined) {
          updates.currentStage = status.current_stage;
        }

        // Update stages from backend
        if (status.stages && status.stages.length > 0) {
          updates.stages = status.stages.map(s => ({
            name: s.name,
            status: s.status as "running" | "complete" | "error" | "initializing",
            message: s.message,
          }));
        }

        updatePipelineProcess(processId, updates);

        // Add only NEW logs to the process (using index tracking)
        const newLogs = status.logs || [];
        if (newLogs.length > lastLogIndex) {
          const addedLogs = newLogs.slice(lastLogIndex);
          addedLogs.forEach(log => {
            const type = log.includes('❌') || log.includes('Error') || log.includes('Failed') ? 'error' :
                        log.includes('✓') || log.includes('✅') || log.includes('Complete') ? 'success' :
                        log.includes('⚠') ? 'warning' : 'info';
            addProcessLog(processId, log, type);
          });
          lastLogIndex = newLogs.length;
        }
        setLogs(newLogs);

        if (status.status === 'complete') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'Director pipeline completed successfully!', 'success');
          updatePipelineProcess(processId, {
            status: 'complete',
            progress: 1,
            endTime: new Date(),
            currentStage: undefined
          });
          setIsRunning(false);
          // Show completion toast
          toast.success('Director Pipeline Complete', 'Visual script generation finished successfully');
        } else if (status.status === 'error' || status.status === 'failed') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'Director pipeline failed', 'error');
          updatePipelineProcess(processId, { status: 'error', endTime: new Date() });
          setIsRunning(false);
          toast.error('Director Pipeline Failed', 'An error occurred during visual script generation');
        } else if (status.status === 'cancelled') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'Director pipeline was cancelled', 'warning');
          updatePipelineProcess(processId, { status: 'cancelled', endTime: new Date() });
          setIsRunning(false);
          toast.warning('Director Pipeline Cancelled', 'Visual script generation was cancelled');
        } else {
          // Continue polling
          pollTimeoutRef.current = setTimeout(poll, 1000);
        }
      } catch (e) {
        pollingActiveRef.current = false;
        addProcessLog(processId, `Polling error: ${e}`, 'error');
        updatePipelineProcess(processId, { status: 'error', error: String(e), endTime: new Date() });
        setIsRunning(false);
        toast.error('Director Pipeline Error', 'Lost connection to pipeline');
      }
    };
    poll();
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] max-h-[80vh] bg-gradient-to-br from-[#0a1f0a] via-[#0d0d0d] to-[#0a0a0a] border border-[#39ff14]/30 rounded-lg shadow-xl shadow-[#39ff14]/10 z-50 flex flex-col">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Configure and run the Director pipeline to generate visual scripts from your confirmed outline.
            </Dialog.Description>
          </VisuallyHidden.Root>
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gl-border">
            <Dialog.Title className="text-xl font-semibold text-gl-text-primary flex items-center gap-2">
              <Film className="w-5 h-5" /> Director Pipeline
            </Dialog.Title>
            <Dialog.Close className="p-1 hover:bg-gl-bg-hover rounded">
              <X className="w-5 h-5 text-gl-text-muted" />
            </Dialog.Close>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gl-accent" />
              </div>
            ) : !outlineExists ? (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-yellow-500/50 mx-auto mb-3" />
                <p className="text-gl-text-muted mb-2">No confirmed outline found</p>
                <p className="text-sm text-gl-text-muted">
                  Generate story outlines and confirm one before running the Director pipeline.
                </p>
              </div>
            ) : (
              <>
                {/* Outline Summary */}
                <div className="bg-gl-bg-medium rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-gl-accent" />
                    <h3 className="text-sm font-medium text-gl-text-primary">Confirmed Outline</h3>
                  </div>
                  <p className="text-2xl font-bold text-gl-accent">{outlineData?.beats.length || 0}</p>
                  <p className="text-sm text-gl-text-muted">story beats to convert to visual script</p>
                </div>

                {/* Beats Preview */}
                <div>
                  <h3 className="text-sm font-medium text-gl-text-primary mb-2">Story Beats</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto bg-black/20 rounded-lg p-3">
                    {outlineData?.beats.map((beat, index) => (
                      <div key={index} className="flex items-start gap-2 p-2 bg-gl-bg-medium rounded">
                        <span className="text-xs font-mono text-gl-accent shrink-0 w-6">
                          {(index + 1).toString().padStart(2, '0')}
                        </span>
                        <p className="text-xs text-gl-text-secondary leading-relaxed">{beat}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* LLM Selection */}
                <div>
                  <label className="block text-sm text-gl-text-secondary mb-1">AI Model</label>
                  <select value={selectedLLM} onChange={e => setSelectedLLM(e.target.value)}
                    className="w-full px-3 py-2 bg-[#2a2a2a] border border-gl-border rounded text-gray-100 [&>option]:bg-[#2a2a2a] [&>option]:text-gray-100">
                    {LLM_OPTIONS.map(l => <option key={l.key} value={l.key} className="bg-[#2a2a2a] text-gray-100">{l.name}</option>)}
                  </select>
                </div>

                {/* Progress */}
                {(isRunning || logs.length > 0) && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gl-text-secondary">Progress</span>
                      <span className="text-gl-text-primary">{Math.round(progress * 100)}%</span>
                    </div>
                    <div className="h-2 bg-gl-bg-medium rounded-full overflow-hidden mb-3">
                      <div className="h-full bg-gl-accent transition-all" style={{ width: `${progress * 100}%` }} />
                    </div>
                    <div className="bg-gl-bg-medium rounded p-3 h-32 overflow-y-auto font-mono text-xs">
                      {logs.map((log, i) => <div key={`log-${i}`} className="text-gl-text-secondary">{log}</div>)}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-700">
            <button onClick={() => onOpenChange(false)} className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white transition-colors">
              Cancel
            </button>
            <button onClick={handleRun} disabled={isRunning || !outlineExists || loading}
              className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 border border-green-500 rounded-md font-medium text-white flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Running...</> : <><Play className="w-4 h-4" /> Run Director</>}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
