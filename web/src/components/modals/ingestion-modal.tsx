'use client';

import { useState, useRef, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import { X, FileText, Loader2, AlertCircle } from 'lucide-react';
import { useStore, useAppStore } from '@/lib/store';
import { fetchAPI, API_BASE_URL } from '@/lib/utils';
import { toast } from '@/components/toast';

interface IngestionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIngestionComplete?: () => void;
}

export function IngestionModal({ open, onOpenChange, onIngestionComplete }: IngestionModalProps) {
  const { projectPath } = useStore();
  const {
    addPipelineProcess,
    updatePipelineProcess,
    addProcessLog,
    setWorkspaceMode,
    setPendingEntityConfirmation,
    setEntityConfirmationOpen,
  } = useAppStore();

  const [pitch, setPitch] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleStartIngestion = async () => {
    if (!projectPath || !pitch.trim()) return;

    setIsSubmitting(true);
    setError(null);

    // Create pipeline process for tracking
    const processId = `ingestion-${Date.now()}`;
    addPipelineProcess({
      id: processId,
      name: 'Document Ingestion',
      status: 'initializing',
      progress: 0,
      startTime: new Date(),
    });

    try {
      // Save pitch first
      addProcessLog(processId, 'Saving pitch...', 'info');
      await fetchAPI(`/api/projects/path-data/pitch?path=${encodeURIComponent(projectPath)}`, {
        method: 'PUT',
        body: JSON.stringify({ content: pitch.trim() })
      });
      addProcessLog(processId, 'Pitch saved', 'success');

      addProcessLog(processId, 'Starting ingestion pipeline...', 'info');
      updatePipelineProcess(processId, { status: 'running' });

      // Start ingestion
      const formData = new FormData();
      formData.append('project_path', projectPath);
      formData.append('pitch', pitch.trim());

      const response = await fetch(`${API_BASE_URL}/api/ingestion/start`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Ingestion failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.pipeline_id) {
        addProcessLog(processId, `Pipeline started: ${data.pipeline_id}`, 'info');

        // Close modal and switch to progress view
        onOpenChange(false);
        setWorkspaceMode('progress');

        // Start polling for status
        pollIngestionStatus(data.pipeline_id, processId);
      }
    } catch (err) {
      setIsSubmitting(false);
      setError(err instanceof Error ? err.message : 'Ingestion failed');
      addProcessLog(processId, `Error: ${err}`, 'error');
      updatePipelineProcess(processId, { status: 'error', error: String(err), endTime: new Date() });
    }
  };

  const pollIngestionStatus = async (pipelineId: string, processId: string) => {
    pollingActiveRef.current = true;
    let lastLogCount = 0;

    const poll = async () => {
      // Check if polling was stopped
      if (!pollingActiveRef.current) return;

      try {
        const statusResponse = await fetchAPI<{
          status: string;
          progress: number;
          message: string;
          logs: string[];
          result?: {
            stats?: {
              documents_processed: number;
              images_processed: number;
              total_chunks: number;
              characters_found: number;
              locations_found: number;
              props_found: number;
            };
          };
        }>(`/api/ingestion/status/${pipelineId}`);

        // Check again after async call
        if (!pollingActiveRef.current) return;

        updatePipelineProcess(processId, { progress: statusResponse.progress });

        // Add new logs (using count tracking to avoid duplicates)
        if (statusResponse.logs && statusResponse.logs.length > lastLogCount) {
          const newLogs = statusResponse.logs.slice(lastLogCount);
          newLogs.forEach(log => {
            const type = log.includes('✓') || log.includes('Complete') ? 'success' :
                        log.includes('✗') || log.includes('Error') ? 'error' :
                        log.includes('⚠') ? 'warning' : 'info';
            addProcessLog(processId, log, type);
          });
          lastLogCount = statusResponse.logs.length;
        }

        if (statusResponse.status === 'complete') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'Ingestion complete!', 'success');
          updatePipelineProcess(processId, {
            status: 'complete',
            progress: 1,
            endTime: new Date()
          });

          // Log stats and show toast
          if (statusResponse.result?.stats) {
            const s = statusResponse.result.stats;
            addProcessLog(processId,
              `Found: ${s.characters_found} characters, ${s.locations_found} locations, ${s.props_found} props`,
              'info'
            );
            toast.success('Ingestion Complete', `Found ${s.characters_found} characters, ${s.locations_found} locations, ${s.props_found} props`);
          } else {
            toast.success('Ingestion Complete', 'Story processed successfully');
          }

          // Mark that entity confirmation is pending and open the modal
          setPendingEntityConfirmation(true);
          setEntityConfirmationOpen(true);

          // Trigger callback if provided
          if (onIngestionComplete) {
            onIngestionComplete();
          }
        } else if (statusResponse.status === 'error') {
          pollingActiveRef.current = false;
          addProcessLog(processId, statusResponse.message || 'Ingestion failed', 'error');
          updatePipelineProcess(processId, {
            status: 'error',
            error: statusResponse.message,
            endTime: new Date()
          });
          toast.error('Ingestion Failed', statusResponse.message || 'An error occurred during processing');
        } else {
          // Still processing
          pollTimeoutRef.current = setTimeout(poll, 1000);
        }
      } catch (err) {
        pollingActiveRef.current = false;
        addProcessLog(processId, `Error: ${err}`, 'error');
        updatePipelineProcess(processId, {
          status: 'error',
          error: String(err),
          endTime: new Date()
        });
        toast.error('Ingestion Error', 'Lost connection to processing pipeline');
      }
    };

    poll();
  };

  const canStartIngestion = pitch.trim() && !isSubmitting;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] max-h-[80vh] bg-gradient-to-br from-[#0a1f0a] via-[#0d0d0d] to-[#0a0a0a] border border-[#39ff14]/30 rounded-lg shadow-xl shadow-[#39ff14]/10 z-50 flex flex-col">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Enter your story pitch or synopsis to extract entities and build your world bible.
            </Dialog.Description>
          </VisuallyHidden.Root>

          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gl-border">
            <Dialog.Title className="text-xl font-semibold text-gl-text-primary flex items-center gap-2">
              <FileText className="w-5 h-5" /> Story Ingestion
            </Dialog.Title>
            <Dialog.Close className="p-1 hover:bg-gl-bg-hover rounded">
              <X className="w-5 h-5 text-gl-text-muted" />
            </Dialog.Close>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {/* Pitch / Synopsis */}
            <div>
              <label className="block text-sm font-medium text-gl-text-secondary mb-2">
                Story Pitch / Synopsis / Script
              </label>
              <textarea
                value={pitch}
                onChange={(e) => setPitch(e.target.value)}
                rows={12}
                placeholder="Paste your story, screenplay, or describe your story idea including characters, settings, and key plot points..."
                className="w-full px-3 py-2.5 bg-gl-bg-medium border border-gl-border rounded-md text-gl-text-primary placeholder:text-gl-text-muted focus:outline-none focus:border-gl-accent/50 focus:ring-1 focus:ring-gl-accent/30 resize-none"
                disabled={isSubmitting}
              />
              <p className="text-xs text-gl-text-muted mt-1">
                The AI will extract characters, locations, and significant props from your text
              </p>
            </div>

            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <span className="text-sm text-red-400 whitespace-pre-wrap">{error}</span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center gap-3 px-6 py-4 border-t border-gl-border">
            <p className="text-xs text-gl-text-muted">
              {!pitch.trim()
                ? 'Enter your story to extract entities'
                : `${pitch.length.toLocaleString()} characters entered`
              }
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartIngestion}
                disabled={!canStartIngestion}
                className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 border border-green-500 rounded-md font-medium text-white flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Starting...</>
                ) : (
                  <><FileText className="w-4 h-4" /> Extract Entities</>
                )}
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
