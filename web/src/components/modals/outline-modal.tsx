'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import {
  X, Loader2, Sparkles, AlertCircle, Check, Plus, Trash2,
  GripVertical, Edit2, Theater, Search, Heart, ChevronUp, ChevronDown, Copy
} from 'lucide-react';
import { useStore, useAppStore } from '@/lib/store';
import { fetchAPI, cn } from '@/lib/utils';
import { toast } from '@/components/toast';

interface OutlineModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirmComplete?: () => void;
}

interface OutlineVariant {
  name: string;
  description: string;
  beats: string[];
  error?: string;
}

interface OutlineData {
  created_at: string;
  title: string;
  status: 'pending_selection' | 'editing' | 'confirmed';
  variants: Record<string, OutlineVariant>;
  selected_variant: string | null;
  confirmed_beats: string[];
}

const VARIANT_INFO: Record<string, { icon: typeof Theater; color: string; bgColor: string; borderColor: string }> = {
  dramatic: {
    icon: Theater,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30'
  },
  mystery: {
    icon: Search,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30'
  },
  character: {
    icon: Heart,
    color: 'text-pink-400',
    bgColor: 'bg-pink-500/10',
    borderColor: 'border-pink-500/30'
  },
};

// Beat item component for drag source
function BeatItem({
  beat,
  index,
  variantKey,
  onDragStart,
  onDragEnd,
  onCopy,
  color
}: {
  beat: string;
  index: number;
  variantKey: string;
  onDragStart: (e: React.DragEvent, beat: string, variantKey: string) => void;
  onDragEnd: () => void;
  onCopy: (beat: string) => void;
  color: string;
}) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, beat, variantKey)}
      onDragEnd={onDragEnd}
      className={cn(
        "flex items-start gap-2 p-2 rounded bg-black/20 border border-white/5 cursor-grab active:cursor-grabbing group",
        "hover:border-white/20 transition-colors"
      )}
    >
      <GripVertical className="w-3 h-3 text-white/30 shrink-0 mt-0.5" />
      <span className={cn("text-[10px] font-mono w-4 shrink-0", color)}>
        {(index + 1).toString().padStart(2, '0')}
      </span>
      <p className="text-xs text-white/80 flex-1 leading-relaxed">{beat}</p>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onCopy(beat);
        }}
        className="p-1 opacity-0 group-hover:opacity-100 hover:bg-white/10 rounded transition-opacity"
        title="Copy to custom outline"
      >
        <Copy className="w-3 h-3 text-white/50" />
      </button>
    </div>
  );
}

// Drop zone between beats for inserting
function DropZone({
  index,
  onDropAt,
  onInsertNew,
  isDragging
}: {
  index: number;
  onDropAt: (index: number) => void;
  onInsertNew: (index: number) => void;
  isDragging: boolean;
}) {
  const [isOver, setIsOver] = useState(false);
  const [showInsert, setShowInsert] = useState(false);

  return (
    <div
      className={cn(
        "relative h-1 -my-0.5 transition-all group/drop",
        isDragging && "h-6 my-1"
      )}
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsOver(true);
      }}
      onDragLeave={() => setIsOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsOver(false);
        onDropAt(index);
      }}
      onMouseEnter={() => !isDragging && setShowInsert(true)}
      onMouseLeave={() => setShowInsert(false)}
    >
      {/* Drop indicator when dragging */}
      {isDragging && (
        <div className={cn(
          "absolute inset-x-2 top-1/2 -translate-y-1/2 h-1 rounded transition-colors",
          isOver ? "bg-green-400" : "bg-green-500/30"
        )} />
      )}
      {/* Insert button when hovering (not dragging) */}
      {showInsert && !isDragging && (
        <button
          onClick={() => onInsertNew(index)}
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-green-500/20 hover:bg-green-500/40 border border-green-500/50 flex items-center justify-center z-10 transition-all"
          title="Insert beat here"
        >
          <Plus className="w-3 h-3 text-green-400" />
        </button>
      )}
    </div>
  );
}

// Editable beat in custom panel
function EditableBeat({
  beat,
  beatId,
  index,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast
}: {
  beat: string;
  beatId: string;
  index: number;
  onUpdate: (newText: string) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  isFirst: boolean;
  isLast: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(beat);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // CRITICAL: Sync editText when beat prop changes (fixes the reorder bug)
  useEffect(() => {
    setEditText(beat);
  }, [beat, beatId]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    if (editText.trim()) {
      onUpdate(editText.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      setEditText(beat);
      setIsEditing(false);
    }
  };

  return (
    <div className="flex items-start gap-2 p-2 rounded bg-green-500/10 border border-green-500/30 group">
      <div className="flex flex-col gap-0.5 shrink-0">
        <button
          onClick={onMoveUp}
          disabled={isFirst}
          className="p-0.5 hover:bg-white/10 rounded disabled:opacity-30"
        >
          <ChevronUp className="w-3 h-3 text-white/50" />
        </button>
        <button
          onClick={onMoveDown}
          disabled={isLast}
          className="p-0.5 hover:bg-white/10 rounded disabled:opacity-30"
        >
          <ChevronDown className="w-3 h-3 text-white/50" />
        </button>
      </div>
      <span className="text-[10px] font-mono w-4 shrink-0 text-green-400 mt-1">
        {(index + 1).toString().padStart(2, '0')}
      </span>
      {isEditing ? (
        <div className="flex-1 flex flex-col gap-1">
          <textarea
            ref={inputRef}
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSave}
            className="w-full px-2 py-1 bg-black/30 border border-green-500/50 rounded text-xs text-white resize-y min-h-[3rem]"
            rows={2}
          />
          <div className="flex gap-1 justify-end">
            <button
              onClick={() => {
                setEditText(beat);
                setIsEditing(false);
              }}
              className="px-2 py-0.5 text-[10px] bg-white/10 hover:bg-white/20 rounded"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-2 py-0.5 text-[10px] bg-green-600 hover:bg-green-700 rounded text-white"
            >
              Save
            </button>
          </div>
        </div>
      ) : (
        <>
          <p
            className="text-xs text-white/80 flex-1 leading-relaxed cursor-pointer hover:text-white"
            onClick={() => setIsEditing(true)}
          >
            {beat}
          </p>
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => setIsEditing(true)}
              className="p-1 hover:bg-white/10 rounded"
              title="Edit"
            >
              <Edit2 className="w-3 h-3 text-white/50" />
            </button>
            <button
              onClick={onRemove}
              className="p-1 hover:bg-red-500/20 rounded"
              title="Remove"
            >
              <Trash2 className="w-3 h-3 text-red-400/70" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// Variant panel component
function VariantPanel({
  variantKey,
  variant,
  onDragStart,
  onDragEnd,
  onCopyBeat,
  onUseOutline
}: {
  variantKey: string;
  variant: OutlineVariant;
  onDragStart: (e: React.DragEvent, beat: string, variantKey: string) => void;
  onDragEnd: () => void;
  onCopyBeat: (beat: string) => void;
  onUseOutline: (beats: string[]) => void;
}) {
  const info = VARIANT_INFO[variantKey] || VARIANT_INFO.dramatic;
  const Icon = info.icon;

  return (
    <div className={cn("flex flex-col h-full rounded-lg border overflow-hidden", info.borderColor, info.bgColor)}>
      {/* Header */}
      <div className={cn("px-3 py-2 border-b flex items-center gap-2", info.borderColor)}>
        <Icon className={cn("w-4 h-4", info.color)} />
        <span className="text-sm font-medium text-white">{variant.name}</span>
        <span className={cn("ml-auto text-xs px-1.5 py-0.5 rounded", info.bgColor, info.color)}>
          {variant.beats.length}
        </span>
      </div>

      {/* Description + Use Button */}
      <div className="px-3 py-2 border-b border-white/5 flex items-start gap-2">
        <p className="text-[10px] text-white/50 leading-relaxed flex-1">{variant.description}</p>
        <button
          onClick={() => onUseOutline(variant.beats)}
          className={cn(
            "px-2 py-1 text-[10px] font-medium rounded shrink-0 transition-colors",
            "bg-white/10 hover:bg-white/20 text-white border border-white/20"
          )}
        >
          Use This
        </button>
      </div>

      {/* Beats List - Scrollable */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea.Root className="h-full">
          <ScrollArea.Viewport className="h-full w-full">
            <div className="p-2 space-y-1.5">
              {variant.beats.map((beat, index) => (
                <BeatItem
                  key={index}
                  beat={beat}
                  index={index}
                  variantKey={variantKey}
                  onDragStart={onDragStart}
                  onDragEnd={onDragEnd}
                  onCopy={onCopyBeat}
                  color={info.color}
                />
              ))}
            </div>
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar className="flex select-none touch-none p-0.5 bg-black/20 w-2" orientation="vertical">
            <ScrollArea.Thumb className="flex-1 bg-white/20 rounded-full" />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>
      </div>
    </div>
  );
}

// Beat with stable ID for proper React reconciliation
interface BeatWithId {
  id: string;
  text: string;
}

// Custom outline panel
function CustomPanel({
  beats,
  onUpdateBeat,
  onRemoveBeat,
  onMoveBeat,
  onAddBeat,
  onInsertBeatAt,
  onDropAt,
  isDragOver,
  isDragging,
  onDragOver,
  onDragLeave,
  onDrop
}: {
  beats: BeatWithId[];
  onUpdateBeat: (index: number, text: string) => void;
  onRemoveBeat: (index: number) => void;
  onMoveBeat: (index: number, direction: 'up' | 'down') => void;
  onAddBeat: (text: string) => void;
  onInsertBeatAt: (index: number, text: string) => void;
  onDropAt: (index: number) => void;
  isDragOver: boolean;
  isDragging: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
}) {
  const [newBeatText, setNewBeatText] = useState('');
  const [insertingAt, setInsertingAt] = useState<number | null>(null);
  const [insertText, setInsertText] = useState('');
  const insertInputRef = useRef<HTMLTextAreaElement>(null);

  const handleAddBeat = () => {
    if (newBeatText.trim()) {
      onAddBeat(newBeatText.trim());
      setNewBeatText('');
    }
  };

  const handleInsertNew = (index: number) => {
    setInsertingAt(index);
    setInsertText('');
    setTimeout(() => insertInputRef.current?.focus(), 50);
  };

  const handleInsertSave = () => {
    if (insertText.trim() && insertingAt !== null) {
      onInsertBeatAt(insertingAt, insertText.trim());
    }
    setInsertingAt(null);
    setInsertText('');
  };

  const handleInsertCancel = () => {
    setInsertingAt(null);
    setInsertText('');
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full rounded-lg border overflow-hidden transition-colors",
        isDragOver
          ? "border-green-400 bg-green-500/20"
          : "border-green-500/30 bg-green-500/10"
      )}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-green-500/30 flex items-center gap-2">
        <Edit2 className="w-4 h-4 text-green-400" />
        <span className="text-sm font-medium text-white">Your Custom Outline</span>
        <span className="ml-auto text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">
          {beats.length}
        </span>
      </div>

      {/* Instructions */}
      <div className="px-3 py-2 border-b border-white/5">
        <p className="text-[10px] text-white/50 leading-relaxed">
          Drag beats between items or hover to insert. Click any beat to edit.
        </p>
      </div>

      {/* Beats List - Scrollable */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea.Root className="h-full">
          <ScrollArea.Viewport className="h-full w-full">
            <div className="p-2">
              {beats.length === 0 ? (
                <div className={cn(
                  "flex flex-col items-center justify-center py-8 text-center",
                  isDragOver ? "opacity-50" : ""
                )}>
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center mb-3">
                    <Plus className="w-6 h-6 text-green-400" />
                  </div>
                  <p className="text-xs text-white/50 mb-1">Drop beats here</p>
                  <p className="text-[10px] text-white/30">or add your own below</p>
                </div>
              ) : (
                <>
                  {/* Drop zone at the top */}
                  <DropZone
                    index={0}
                    onDropAt={onDropAt}
                    onInsertNew={handleInsertNew}
                    isDragging={isDragging}
                  />

                  {/* Insert form at top if inserting at 0 */}
                  {insertingAt === 0 && (
                    <div className="mb-2 p-2 rounded bg-green-500/20 border border-green-500/50">
                      <textarea
                        ref={insertInputRef}
                        value={insertText}
                        onChange={(e) => setInsertText(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleInsertSave();
                          }
                          if (e.key === 'Escape') handleInsertCancel();
                        }}
                        placeholder="Enter new beat..."
                        className="w-full px-2 py-1 bg-black/30 border border-green-500/50 rounded text-xs text-white resize-y min-h-[3rem]"
                        rows={2}
                      />
                      <div className="flex gap-1 justify-end mt-1">
                        <button
                          onClick={handleInsertCancel}
                          className="px-2 py-0.5 text-[10px] bg-white/10 hover:bg-white/20 rounded"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleInsertSave}
                          disabled={!insertText.trim()}
                          className="px-2 py-0.5 text-[10px] bg-green-600 hover:bg-green-700 rounded text-white disabled:opacity-50"
                        >
                          Insert
                        </button>
                      </div>
                    </div>
                  )}

                  {beats.map((beat, index) => (
                    <div key={beat.id}>
                      <EditableBeat
                        beat={beat.text}
                        beatId={beat.id}
                        index={index}
                        onUpdate={(text) => onUpdateBeat(index, text)}
                        onRemove={() => onRemoveBeat(index)}
                        onMoveUp={() => onMoveBeat(index, 'up')}
                        onMoveDown={() => onMoveBeat(index, 'down')}
                        isFirst={index === 0}
                        isLast={index === beats.length - 1}
                      />

                      {/* Drop zone after each beat */}
                      <DropZone
                        index={index + 1}
                        onDropAt={onDropAt}
                        onInsertNew={handleInsertNew}
                        isDragging={isDragging}
                      />

                      {/* Insert form after this beat if inserting here */}
                      {insertingAt === index + 1 && (
                        <div className="my-2 p-2 rounded bg-green-500/20 border border-green-500/50">
                          <textarea
                            ref={insertInputRef}
                            value={insertText}
                            onChange={(e) => setInsertText(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleInsertSave();
                              }
                              if (e.key === 'Escape') handleInsertCancel();
                            }}
                            placeholder="Enter new beat..."
                            className="w-full px-2 py-1 bg-black/30 border border-green-500/50 rounded text-xs text-white resize-y min-h-[3rem]"
                            rows={2}
                          />
                          <div className="flex gap-1 justify-end mt-1">
                            <button
                              onClick={handleInsertCancel}
                              className="px-2 py-0.5 text-[10px] bg-white/10 hover:bg-white/20 rounded"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={handleInsertSave}
                              disabled={!insertText.trim()}
                              className="px-2 py-0.5 text-[10px] bg-green-600 hover:bg-green-700 rounded text-white disabled:opacity-50"
                            >
                              Insert
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}

              {/* Add new beat input at bottom */}
              <div className="flex items-center gap-2 p-2 rounded border border-dashed border-green-500/30 mt-2">
                <Plus className="w-3 h-3 text-green-400/50 shrink-0" />
                <input
                  type="text"
                  value={newBeatText}
                  onChange={(e) => setNewBeatText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddBeat()}
                  placeholder="Add a new story beat..."
                  className="flex-1 bg-transparent text-xs text-white placeholder:text-white/30 outline-none"
                />
                {newBeatText && (
                  <button
                    onClick={handleAddBeat}
                    className="px-2 py-0.5 bg-green-600 hover:bg-green-700 rounded text-[10px] text-white shrink-0"
                  >
                    Add
                  </button>
                )}
              </div>
            </div>
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar className="flex select-none touch-none p-0.5 bg-black/20 w-2" orientation="vertical">
            <ScrollArea.Thumb className="flex-1 bg-white/20 rounded-full" />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>
      </div>
    </div>
  );
}

export function OutlineModal({
  open,
  onOpenChange,
  onConfirmComplete,
}: OutlineModalProps) {
  const { projectPath } = useStore();
  const { addPipelineProcess, updatePipelineProcess, addProcessLog, setWorkspaceMode } = useAppStore();

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [outlineData, setOutlineData] = useState<OutlineData | null>(null);
  const [customBeats, setCustomBeats] = useState<BeatWithId[]>([]);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragData, setDragData] = useState<{ beat: string; source: string } | null>(null);

  // Helper to generate unique IDs
  const generateBeatId = () => `beat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Helper to convert string[] to BeatWithId[]
  const stringsToBeats = (strings: string[]): BeatWithId[] =>
    strings.map(text => ({ id: generateBeatId(), text }));

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

  // Load existing outlines
  const loadOutlines = useCallback(async () => {
    if (!projectPath) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetchAPI<{ success: boolean; data?: OutlineData; error?: string }>(
        `/api/pipelines/outlines/${encodeURIComponent(projectPath)}`
      );

      if (response.success && response.data) {
        setOutlineData(response.data);
        // Load confirmed beats if they exist
        if (response.data.confirmed_beats.length > 0) {
          setCustomBeats(stringsToBeats(response.data.confirmed_beats));
        }
      } else {
        setOutlineData(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load outlines');
    } finally {
      setLoading(false);
    }
  }, [projectPath]);

  useEffect(() => {
    if (open) {
      loadOutlines();
    }
  }, [open, loadOutlines]);

  // Generate new outlines
  const handleGenerate = async () => {
    if (!projectPath) return;

    setGenerating(true);
    setError(null);

    const processId = `outline-gen-${Date.now()}`;
    addPipelineProcess({
      id: processId,
      name: 'Outline Generator',
      status: 'initializing',
      progress: 0,
      startTime: new Date(),
    });

    try {
      addProcessLog(processId, 'Starting outline generation...', 'info');
      updatePipelineProcess(processId, { status: 'running' });

      // Close modal and switch to progress view
      onOpenChange(false);
      setWorkspaceMode('progress');

      const response = await fetchAPI<{ success: boolean; pipeline_id?: string; message?: string }>(
        '/api/pipelines/outline-generator',
        {
          method: 'POST',
          body: JSON.stringify({ project_path: projectPath }),
        }
      );

      if (response.success && response.pipeline_id) {
        addProcessLog(processId, `Pipeline started: ${response.pipeline_id}`, 'info');
        updatePipelineProcess(processId, { backendId: response.pipeline_id });
        pollPipelineStatus(response.pipeline_id, processId);
      } else {
        throw new Error(response.message || 'Failed to start outline generator');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      addProcessLog(processId, `Error: ${err}`, 'error');
      updatePipelineProcess(processId, { status: 'error', error: String(err), endTime: new Date() });
      setGenerating(false);
    }
  };

  const pollPipelineStatus = async (pipelineId: string, processId: string) => {
    pollingActiveRef.current = true;
    let lastLogIndex = 0;

    const poll = async (): Promise<void> => {
      // Check if polling was stopped
      if (!pollingActiveRef.current) return;

      try {
        const status = await fetchAPI<{
          status: string;
          progress: number;
          message: string;
          logs: string[];
          current_stage?: string;
          stages?: Array<{ name: string; status: string; message?: string }>;
        }>(`/api/pipelines/status/${pipelineId}`);

        // Check again after async call
        if (!pollingActiveRef.current) return;

        // Build update object with progress and stage info
        const updates: Record<string, unknown> = {
          progress: status.progress || 0,
        };

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

        // Add only NEW logs to the process
        const newLogs = status.logs || [];
        if (newLogs.length > lastLogIndex) {
          const addedLogs = newLogs.slice(lastLogIndex);
          addedLogs.forEach(log => {
            const type = log.includes('[OK]') || log.includes('complete') || log.includes('✓') ? 'success' :
                        log.includes('Error') || log.includes('failed') ? 'error' :
                        log.includes('⚠') ? 'warning' : 'info';
            addProcessLog(processId, log, type);
          });
          lastLogIndex = newLogs.length;
        }

        if (status.status === 'complete') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'Outline generation complete!', 'success');
          updatePipelineProcess(processId, {
            status: 'complete',
            progress: 1,
            endTime: new Date(),
            currentStage: undefined
          });
          setGenerating(false);
          await loadOutlines();
          toast.success('Outlines Generated', '3 story outline variants are ready for review');
        } else if (status.status === 'error') {
          pollingActiveRef.current = false;
          addProcessLog(processId, status.message || 'Generation failed', 'error');
          updatePipelineProcess(processId, { status: 'error', error: status.message, endTime: new Date() });
          setGenerating(false);
          setError(status.message || 'Generation failed');
          toast.error('Outline Generation Failed', status.message || 'An error occurred');
        } else {
          pollTimeoutRef.current = setTimeout(poll, 1500);
        }
      } catch (err) {
        pollingActiveRef.current = false;
        addProcessLog(processId, `Polling error: ${err}`, 'error');
        updatePipelineProcess(processId, { status: 'error', error: String(err), endTime: new Date() });
        setGenerating(false);
        setError(String(err));
        toast.error('Outline Error', 'Lost connection to generation process');
      }
    };

    poll();
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, beat: string, variantKey: string) => {
    setDragData({ beat, source: variantKey });
    setIsDragging(true);
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    setDragData(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setIsDragging(false);
    if (dragData) {
      const newBeat: BeatWithId = { id: generateBeatId(), text: dragData.beat };
      setCustomBeats(prev => {
        const newBeats = [...prev, newBeat];
        saveBeats(newBeats.map(b => b.text));
        return newBeats;
      });
    }
    setDragData(null);
  };

  // Drop at a specific index (between beats)
  const handleDropAt = (index: number) => {
    if (dragData) {
      const newBeat: BeatWithId = { id: generateBeatId(), text: dragData.beat };
      setCustomBeats(prev => {
        const newBeats = [...prev];
        newBeats.splice(index, 0, newBeat);
        saveBeats(newBeats.map(b => b.text));
        return newBeats;
      });
    }
    setDragData(null);
    setIsDragging(false);
  };

  // Insert a new beat at a specific index
  const handleInsertBeatAt = (index: number, text: string) => {
    const newBeat: BeatWithId = { id: generateBeatId(), text };
    setCustomBeats(prev => {
      const newBeats = [...prev];
      newBeats.splice(index, 0, newBeat);
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  // Copy beat to custom
  const handleCopyBeat = (beat: string) => {
    const newBeat: BeatWithId = { id: generateBeatId(), text: beat };
    setCustomBeats(prev => {
      const newBeats = [...prev, newBeat];
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  // Use entire outline from a variant
  const handleUseOutline = (beats: string[]) => {
    const newBeats = stringsToBeats(beats);
    setCustomBeats(newBeats);
    saveBeats(beats);
  };

  // Custom beats handlers
  const handleUpdateBeat = (index: number, text: string) => {
    setCustomBeats(prev => {
      const newBeats = [...prev];
      newBeats[index] = { ...newBeats[index], text };
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  const handleRemoveBeat = (index: number) => {
    setCustomBeats(prev => {
      const newBeats = prev.filter((_, i) => i !== index);
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  const handleMoveBeat = (index: number, direction: 'up' | 'down') => {
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === customBeats.length - 1) return;

    setCustomBeats(prev => {
      const newBeats = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      [newBeats[index], newBeats[targetIndex]] = [newBeats[targetIndex], newBeats[index]];
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  const handleAddBeat = (text: string) => {
    const newBeat: BeatWithId = { id: generateBeatId(), text };
    setCustomBeats(prev => {
      const newBeats = [...prev, newBeat];
      saveBeats(newBeats.map(b => b.text));
      return newBeats;
    });
  };

  // Save beats to backend
  const saveBeats = async (beats: string[]) => {
    if (!projectPath) return;

    try {
      await fetchAPI('/api/pipelines/outlines/update-beats', {
        method: 'POST',
        body: JSON.stringify({ project_path: projectPath, beats }),
      });
    } catch (err) {
      console.error('Failed to save beats:', err);
    }
  };

  // Confirm and proceed
  const handleConfirm = async () => {
    if (!projectPath || customBeats.length === 0) return;

    setIsConfirming(true);

    try {
      const response = await fetchAPI<{ success: boolean; message?: string; error?: string }>(
        '/api/pipelines/outlines/confirm',
        {
          method: 'POST',
          body: JSON.stringify({ project_path: projectPath }),
        }
      );

      if (response.success) {
        onOpenChange(false);
        if (onConfirmComplete) onConfirmComplete();
      } else {
        setError(response.error || 'Failed to confirm outline');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Confirmation failed');
    } finally {
      setIsConfirming(false);
    }
  };

  const hasOutlines = outlineData && Object.keys(outlineData.variants).length > 0;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/80 z-50" />
        <Dialog.Content className="fixed inset-4 bg-gradient-to-br from-[#1a0a0a] via-[#0d0d0d] to-[#0a0a0a] border border-red-500/30 rounded-lg shadow-xl shadow-red-500/10 z-50 flex flex-col overflow-hidden">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Generate and edit story outlines with different narrative approaches.
            </Dialog.Description>
          </VisuallyHidden.Root>

          {/* Header */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-white/10 shrink-0">
            <Dialog.Title className="text-lg font-semibold text-white flex items-center gap-2">
              <Theater className="w-5 h-5 text-red-400" /> Story Outline Builder
            </Dialog.Title>
            <div className="flex items-center gap-3">
              {hasOutlines && (
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="px-3 py-1.5 text-sm bg-white/5 hover:bg-white/10 border border-white/10 rounded text-white flex items-center gap-2 disabled:opacity-50"
                >
                  {generating ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  Regenerate
                </button>
              )}
              <Dialog.Close className="p-1.5 hover:bg-white/10 rounded" disabled={generating || isConfirming}>
                <X className="w-5 h-5 text-white/60" />
              </Dialog.Close>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {loading ? (
              <div className="flex-1 flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-red-400" />
              </div>
            ) : error && !hasOutlines ? (
              <div className="flex-1 flex items-center justify-center h-full">
                <div className="text-center space-y-3">
                  <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
                  <p className="text-red-400">{error}</p>
                  <button
                    onClick={loadOutlines}
                    className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 rounded"
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : !hasOutlines ? (
              // No outlines - show generate button
              <div className="flex-1 flex items-center justify-center h-full">
                <div className="text-center space-y-4 max-w-md">
                  <Theater className="w-16 h-16 text-red-400/50 mx-auto" />
                  <h3 className="text-lg font-medium text-white">Generate Story Outlines</h3>
                  <p className="text-sm text-white/50">
                    Create 3 different story outline variants from your world bible.
                    Each uses a unique narrative approach - dramatic arc, mystery unfolding, or character journey.
                  </p>
                  <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded text-white font-medium flex items-center gap-2 mx-auto disabled:opacity-50"
                  >
                    {generating ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                    ) : (
                      <><Sparkles className="w-4 h-4" /> Generate 3 Variants</>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              // Four-panel layout
              <div className="grid grid-cols-4 gap-3 p-4 h-full">
                {/* Variant panels */}
                {Object.entries(outlineData!.variants).map(([key, variant]) => (
                  <VariantPanel
                    key={key}
                    variantKey={key}
                    variant={variant}
                    onDragStart={handleDragStart}
                    onDragEnd={handleDragEnd}
                    onCopyBeat={handleCopyBeat}
                    onUseOutline={handleUseOutline}
                  />
                ))}

                {/* Custom panel */}
                <CustomPanel
                  beats={customBeats}
                  onUpdateBeat={handleUpdateBeat}
                  onRemoveBeat={handleRemoveBeat}
                  onMoveBeat={handleMoveBeat}
                  onAddBeat={handleAddBeat}
                  onInsertBeatAt={handleInsertBeatAt}
                  onDropAt={handleDropAt}
                  onDrop={handleDrop}
                  isDragOver={isDragOver}
                  isDragging={isDragging}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                />
              </div>
            )}
          </div>

          {/* Footer */}
          {hasOutlines && (
            <div className="flex justify-between items-center px-6 py-3 border-t border-white/10 shrink-0">
              <div className="text-sm text-white/50">
                {customBeats.length > 0 ? (
                  <span className="text-green-400">{customBeats.length} beats in your custom outline</span>
                ) : (
                  <span>Drag beats from variants to build your custom outline</span>
                )}
              </div>
              <button
                onClick={handleConfirm}
                disabled={customBeats.length === 0 || isConfirming}
                className="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 rounded text-white flex items-center gap-2 disabled:opacity-50"
              >
                {isConfirming ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Confirming...</>
                ) : (
                  <><Check className="w-4 h-4" /> Confirm & Continue</>
                )}
              </button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
