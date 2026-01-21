'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tabs from '@radix-ui/react-tabs';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import {
  X, User, MapPin, Package, Check, Trash2, Plus, Loader2, Sparkles,
  AlertCircle, ChevronDown, Edit2
} from 'lucide-react';
import { useStore, useAppStore } from '@/lib/store';
import { fetchAPI, cn } from '@/lib/utils';
import { toast } from '@/components/toast';

interface EntityConfirmationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirmComplete?: () => void;
}

interface ExtractedEntity {
  name: string;
  type?: 'character' | 'location' | 'prop';
  type_suggestion?: 'character' | 'location' | 'prop';
  role_hint?: string;
  description?: string;
  contexts?: string[];
  mentions?: number;
  source?: string;
  confirmed?: boolean;
  // UI state
  selected?: boolean;
  tag?: string;
}

interface ExtractedEntitiesData {
  created_at: string;
  status: string;
  source_files: {
    documents?: string[];
    images?: string[];
  };
  entities: {
    characters: ExtractedEntity[];
    locations: ExtractedEntity[];
    props: ExtractedEntity[];
  };
  world_hints?: {
    time_periods?: string[];
    cultural_contexts?: string[];
    visual_styles?: string[];
    moods?: string[];
  };
}

type EntityType = 'character' | 'location' | 'prop';

const ENTITY_TYPES: { key: EntityType; label: string; icon: typeof User; prefix: string }[] = [
  { key: 'character', label: 'Characters', icon: User, prefix: 'CHAR_' },
  { key: 'location', label: 'Locations', icon: MapPin, prefix: 'LOC_' },
  { key: 'prop', label: 'Props', icon: Package, prefix: 'PROP_' },
];

function generateTag(name: string, type: EntityType): string {
  const prefix = ENTITY_TYPES.find(t => t.key === type)?.prefix || 'ENTITY_';
  const cleanName = name
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, '')
    .trim()
    .replace(/\s+/g, '_');
  return `${prefix}${cleanName}`;
}

function getEntityTypeIcon(type: EntityType) {
  const config = ENTITY_TYPES.find(t => t.key === type);
  return config?.icon || User;
}

function getTypeColor(type: EntityType): string {
  switch (type) {
    case 'character': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    case 'location': return 'text-green-400 bg-green-500/10 border-green-500/30';
    case 'prop': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
  }
}

export function EntityConfirmationModal({
  open,
  onOpenChange,
  onConfirmComplete
}: EntityConfirmationModalProps) {
  const { projectPath } = useStore();
  const {
    addPipelineProcess,
    updatePipelineProcess,
    addProcessLog,
    setWorkspaceMode,
    setPendingEntityConfirmation,
  } = useAppStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<EntityType>('character');
  const [entities, setEntities] = useState<Record<EntityType, ExtractedEntity[]>>({
    character: [],
    location: [],
    prop: [],
  });
  const [worldHints, setWorldHints] = useState<ExtractedEntitiesData['world_hints']>({});
  const [isConfirming, setIsConfirming] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEntityName, setNewEntityName] = useState('');
  const [newEntityType, setNewEntityType] = useState<EntityType>('character');

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

  // Load extracted entities
  const loadEntities = useCallback(async () => {
    if (!projectPath) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchAPI<ExtractedEntitiesData>(
        `/api/ingestion/entities/${encodeURIComponent(projectPath)}`
      );

      // Process entities with default selection (all selected)
      const processEntities = (list: ExtractedEntity[], type: EntityType): ExtractedEntity[] =>
        list.map(e => ({
          ...e,
          type,
          selected: true,
          tag: generateTag(e.name, type),
        }));

      setEntities({
        character: processEntities(data.entities.characters || [], 'character'),
        location: processEntities(data.entities.locations || [], 'location'),
        prop: processEntities(data.entities.props || [], 'prop'),
      });

      setWorldHints(data.world_hints || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load entities');
    } finally {
      setLoading(false);
    }
  }, [projectPath]);

  useEffect(() => {
    if (open) {
      loadEntities();
    }
  }, [open, loadEntities]);

  // Toggle entity selection
  const toggleEntitySelection = (type: EntityType, index: number) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].map((e, i) =>
        i === index ? { ...e, selected: !e.selected } : e
      ),
    }));
  };

  // Update entity tag
  const updateEntityTag = (type: EntityType, index: number, newTag: string) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].map((e, i) =>
        i === index ? { ...e, tag: newTag.toUpperCase() } : e
      ),
    }));
  };

  // Change entity type
  const changeEntityType = (fromType: EntityType, index: number, toType: EntityType) => {
    const entity = entities[fromType][index];
    if (!entity) return;

    setEntities(prev => ({
      ...prev,
      [fromType]: prev[fromType].filter((_, i) => i !== index),
      [toType]: [...prev[toType], { ...entity, type: toType, tag: generateTag(entity.name, toType) }],
    }));
  };

  // Remove entity
  const removeEntity = (type: EntityType, index: number) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index),
    }));
  };

  // Update entity role (characters only)
  const updateEntityRole = (type: EntityType, index: number, role: string) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].map((e, i) =>
        i === index ? { ...e, role_hint: role } : e
      ),
    }));
  };

  // Update entity name
  const updateEntityName = (type: EntityType, index: number, name: string) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].map((e, i) =>
        i === index ? { ...e, name, tag: generateTag(name, type) } : e
      ),
    }));
  };

  // Update entity description
  const updateEntityDescription = (type: EntityType, index: number, description: string) => {
    setEntities(prev => ({
      ...prev,
      [type]: prev[type].map((e, i) =>
        i === index ? { ...e, description } : e
      ),
    }));
  };

  // Add new entity
  const addNewEntity = () => {
    if (!newEntityName.trim()) return;

    const newEntity: ExtractedEntity = {
      name: newEntityName.trim(),
      type: newEntityType,
      selected: true,
      tag: generateTag(newEntityName.trim(), newEntityType),
      source: 'manual',
      mentions: 1,
    };

    setEntities(prev => ({
      ...prev,
      [newEntityType]: [...prev[newEntityType], newEntity],
    }));

    setNewEntityName('');
    setShowAddForm(false);
  };

  // Confirm entities and start world builder
  const handleConfirm = async () => {
    if (!projectPath) return;

    setIsConfirming(true);

    // Collect confirmed entities
    const confirmedEntities = [
      ...entities.character.filter(e => e.selected).map(e => ({
        name: e.name,
        type: 'character' as const,
        tag: e.tag || generateTag(e.name, 'character'),
        confirmed: true,
        role_hint: e.role_hint || 'supporting',  // Pass role_hint for characters
      })),
      ...entities.location.filter(e => e.selected).map(e => ({
        name: e.name,
        type: 'location' as const,
        tag: e.tag || generateTag(e.name, 'location'),
        confirmed: true,
      })),
      ...entities.prop.filter(e => e.selected).map(e => ({
        name: e.name,
        type: 'prop' as const,
        tag: e.tag || generateTag(e.name, 'prop'),
        confirmed: true,
      })),
    ];

    // Create pipeline process
    const processId = `world-builder-${Date.now()}`;
    addPipelineProcess({
      id: processId,
      name: 'World Bible Builder',
      status: 'initializing',
      progress: 0,
      startTime: new Date(),
    });

    try {
      // 1. Confirm entities
      addProcessLog(processId, 'Confirming entities...', 'info');

      await fetchAPI('/api/ingestion/confirm-entities', {
        method: 'POST',
        body: JSON.stringify({
          project_path: projectPath,
          entities: confirmedEntities,
        }),
      });

      addProcessLog(processId,
        `Confirmed: ${entities.character.filter(e => e.selected).length} characters, ` +
        `${entities.location.filter(e => e.selected).length} locations, ` +
        `${entities.prop.filter(e => e.selected).length} props`,
        'success'
      );

      // 2. Start world builder pipeline
      addProcessLog(processId, 'Starting World Bible Builder...', 'info');
      updatePipelineProcess(processId, { status: 'running' });

      // Close modal and switch to progress view
      onOpenChange(false);
      setWorkspaceMode('progress');

      const response = await fetchAPI<{ success: boolean; pipeline_id?: string; message?: string }>(
        '/api/pipelines/world-builder',
        {
          method: 'POST',
          body: JSON.stringify({
            project_path: projectPath,
            visual_style: 'live_action',
          }),
        }
      );

      if (response.success && response.pipeline_id) {
        // Store backend ID for resume capability
        updatePipelineProcess(processId, { backendId: response.pipeline_id });
        addProcessLog(processId, `Pipeline started: ${response.pipeline_id}`, 'info');
        pollWorldBuilderStatus(response.pipeline_id, processId);
      } else {
        throw new Error(response.message || 'Failed to start world builder');
      }
    } catch (err) {
      setIsConfirming(false);
      addProcessLog(processId, `Error: ${err}`, 'error');
      updatePipelineProcess(processId, {
        status: 'error',
        error: String(err),
        endTime: new Date(),
      });
    }
  };

  const pollWorldBuilderStatus = async (pipelineId: string, processId: string) => {
    pollingActiveRef.current = true;
    let lastLogCount = 0;

    const poll = async () => {
      // Check if polling was stopped
      if (!pollingActiveRef.current) return;

      try {
        const status = await fetchAPI<{
          status: string;
          progress: number;
          message: string;
          logs: string[];
          current_item?: string;
          completed_fields?: number;
          total_fields?: number;
          current_stage?: string;
          stages?: Array<{ name: string; status: string; message?: string }>;
        }>(`/api/pipelines/status/${pipelineId}`);

        // Check again after async call
        if (!pollingActiveRef.current) return;

        // Build update object with enhanced fields
        const updates: Record<string, unknown> = {
          progress: status.progress,
        };

        if (status.current_item !== undefined) {
          updates.currentItem = status.current_item;
        }
        if (status.completed_fields !== undefined && status.total_fields !== undefined) {
          updates.completedItems = status.completed_fields;
          updates.totalItems = status.total_fields;
        }
        if (status.current_stage !== undefined) {
          updates.currentStage = status.current_stage;
        }
        if (status.stages && status.stages.length > 0) {
          updates.stages = status.stages.map(s => ({
            name: s.name,
            status: s.status as "running" | "complete" | "error" | "initializing",
            message: s.message,
          }));
        }

        updatePipelineProcess(processId, updates);

        // Add new logs (avoid duplicates)
        if (status.logs && status.logs.length > lastLogCount) {
          const newLogs = status.logs.slice(lastLogCount);
          newLogs.forEach(log => {
            const type = log.includes('✓') || log.includes('complete') || log.includes('[OK]') ? 'success' :
                        log.includes('Error') || log.includes('failed') ? 'error' : 'info';
            addProcessLog(processId, log, type);
          });
          lastLogCount = status.logs.length;
        }

        if (status.status === 'complete') {
          pollingActiveRef.current = false;
          addProcessLog(processId, 'World Bible complete!', 'success');
          updatePipelineProcess(processId, {
            status: 'complete',
            progress: 1,
            endTime: new Date(),
            currentItem: undefined,
            currentStage: undefined,
          });
          setIsConfirming(false);
          // Clear pending confirmation state - entities are now confirmed
          setPendingEntityConfirmation(false);
          toast.success('World Bible Complete', 'Entity descriptions and relationships generated');
          if (onConfirmComplete) onConfirmComplete();
        } else if (status.status === 'error') {
          pollingActiveRef.current = false;
          addProcessLog(processId, status.message || 'World builder failed', 'error');
          updatePipelineProcess(processId, {
            status: 'error',
            error: status.message,
            endTime: new Date(),
          });
          setIsConfirming(false);
          toast.error('World Builder Failed', status.message || 'An error occurred');
        } else {
          pollTimeoutRef.current = setTimeout(poll, 1500);
        }
      } catch (err) {
        pollingActiveRef.current = false;
        addProcessLog(processId, `Polling error: ${err}`, 'error');
        updatePipelineProcess(processId, {
          status: 'error',
          error: String(err),
          endTime: new Date(),
        });
        setIsConfirming(false);
        toast.error('World Builder Error', 'Lost connection to pipeline');
      }
    };

    poll();
  };

  const getCounts = () => ({
    character: entities.character.filter(e => e.selected).length,
    location: entities.location.filter(e => e.selected).length,
    prop: entities.prop.filter(e => e.selected).length,
    total: entities.character.filter(e => e.selected).length +
           entities.location.filter(e => e.selected).length +
           entities.prop.filter(e => e.selected).length,
  });

  const counts = getCounts();

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] max-h-[85vh] bg-gradient-to-br from-[#0a1f0a] via-[#0d0d0d] to-[#0a0a0a] border border-[#39ff14]/30 rounded-lg shadow-xl shadow-[#39ff14]/10 z-50 flex flex-col">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Review and confirm extracted entities before building the world bible.
            </Dialog.Description>
          </VisuallyHidden.Root>

          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gl-border">
            <Dialog.Title className="text-xl font-semibold text-gl-text-primary flex items-center gap-2">
              <Sparkles className="w-5 h-5" /> Confirm Entities
            </Dialog.Title>
            <Dialog.Close className="p-1 hover:bg-gl-bg-hover rounded" disabled={isConfirming}>
              <X className="w-5 h-5 text-gl-text-muted" />
            </Dialog.Close>
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex-1 flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-green-500" />
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center py-12">
              <div className="text-center space-y-3">
                <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
                <p className="text-red-400">{error}</p>
                <button
                  onClick={loadEntities}
                  className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : (
            <Tabs.Root value={activeTab} onValueChange={(v) => setActiveTab(v as EntityType)} className="flex-1 flex flex-col overflow-hidden">
              {/* Tabs */}
              <Tabs.List className="flex border-b border-gl-border px-6">
                {ENTITY_TYPES.map((type) => {
                  const Icon = type.icon;
                  const count = entities[type.key].length;
                  const selectedCount = entities[type.key].filter(e => e.selected).length;
                  return (
                    <Tabs.Trigger
                      key={type.key}
                      value={type.key}
                      className={cn(
                        "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors",
                        activeTab === type.key
                          ? "border-gl-accent text-gl-accent"
                          : "border-transparent text-gl-text-muted hover:text-gl-text-primary"
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      {type.label}
                      <span className="ml-1 px-1.5 py-0.5 text-xs bg-gl-bg-medium rounded-full">
                        {selectedCount}/{count}
                      </span>
                    </Tabs.Trigger>
                  );
                })}
              </Tabs.List>

              {/* Entity Lists */}
              {ENTITY_TYPES.map((type) => (
                <Tabs.Content key={type.key} value={type.key} className="flex-1 min-h-0">
                  <div className="h-full max-h-[350px] overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-gray-500 scrollbar-track-gray-800">
                    <div className="space-y-2">
                      {entities[type.key].length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                          <type.icon className="w-10 h-10 mx-auto mb-2 opacity-50" />
                          <p>No {type.label.toLowerCase()} found</p>
                          <button
                            onClick={() => {
                              setNewEntityType(type.key);
                              setShowAddForm(true);
                            }}
                            className="mt-3 px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white transition-colors"
                          >
                            Add Manually
                          </button>
                        </div>
                      ) : (
                        entities[type.key].map((entity, index) => (
                          <EntityRow
                            key={`${entity.name}-${index}`}
                            entity={entity}
                            type={type.key}
                            onToggle={() => toggleEntitySelection(type.key, index)}
                            onUpdateTag={(tag) => updateEntityTag(type.key, index, tag)}
                            onChangeType={(newType) => changeEntityType(type.key, index, newType)}
                            onRemove={() => removeEntity(type.key, index)}
                            onUpdateRole={type.key === 'character' ? (role) => updateEntityRole(type.key, index, role) : undefined}
                            onUpdateName={(name) => updateEntityName(type.key, index, name)}
                            onUpdateDescription={(desc) => updateEntityDescription(type.key, index, desc)}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </Tabs.Content>
              ))}
            </Tabs.Root>
          )}

          {/* Add Entity Form */}
          {showAddForm && (
            <div className="px-6 py-3 border-t border-gray-700 bg-gray-800/50">
              <div className="flex items-center gap-3">
                <select
                  value={newEntityType}
                  onChange={(e) => setNewEntityType(e.target.value as EntityType)}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-sm text-white"
                >
                  {ENTITY_TYPES.map(t => (
                    <option key={t.key} value={t.key}>{t.label.slice(0, -1)}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={newEntityName}
                  onChange={(e) => setNewEntityName(e.target.value)}
                  placeholder="Entity name..."
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-sm text-white placeholder:text-gray-400"
                  onKeyDown={(e) => e.key === 'Enter' && addNewEntity()}
                />
                <button
                  onClick={addNewEntity}
                  disabled={!newEntityName.trim()}
                  className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 border border-green-500 rounded-md font-medium text-white disabled:opacity-50 transition-colors"
                >
                  Add
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* World Hints */}
          {worldHints && Object.values(worldHints).some(arr => arr && arr.length > 0) && (
            <div className="px-6 py-3 border-t border-gl-border">
              <details className="group">
                <summary className="flex items-center gap-2 cursor-pointer text-sm text-gl-text-muted hover:text-gl-text-primary">
                  <ChevronDown className="w-4 h-4 group-open:rotate-180 transition-transform" />
                  World Hints from Images
                </summary>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  {worldHints.time_periods && worldHints.time_periods.length > 0 && (
                    <div>
                      <span className="text-gl-text-muted">Time:</span>{' '}
                      <span className="text-gl-text-secondary">{worldHints.time_periods.join(', ')}</span>
                    </div>
                  )}
                  {worldHints.cultural_contexts && worldHints.cultural_contexts.length > 0 && (
                    <div>
                      <span className="text-gl-text-muted">Culture:</span>{' '}
                      <span className="text-gl-text-secondary">{worldHints.cultural_contexts.join(', ')}</span>
                    </div>
                  )}
                  {worldHints.visual_styles && worldHints.visual_styles.length > 0 && (
                    <div>
                      <span className="text-gl-text-muted">Style:</span>{' '}
                      <span className="text-gl-text-secondary">{worldHints.visual_styles.join(', ')}</span>
                    </div>
                  )}
                  {worldHints.moods && worldHints.moods.length > 0 && (
                    <div>
                      <span className="text-gl-text-muted">Mood:</span>{' '}
                      <span className="text-gl-text-secondary">{worldHints.moods.join(', ')}</span>
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-between items-center gap-3 px-6 py-4 border-t border-gl-border">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white flex items-center gap-2 transition-colors"
              >
                <Plus className="w-4 h-4" /> Add Entity
              </button>
              <span className="text-sm text-gl-text-muted">
                {counts.total} entities selected
              </span>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => onOpenChange(false)}
                disabled={isConfirming}
                className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-md font-medium text-white disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={counts.total === 0 || isConfirming}
                className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 border border-green-500 rounded-md font-medium text-white flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isConfirming ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Building World...</>
                ) : (
                  <><Sparkles className="w-4 h-4" /> Build World Bible</>
                )}
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

const CHARACTER_ROLES = [
  { value: 'protagonist', label: 'Protagonist' },
  { value: 'antagonist', label: 'Antagonist' },
  { value: 'love_interest', label: 'Love Interest' },
  { value: 'supporting', label: 'Supporting' },
  { value: 'mentor', label: 'Mentor' },
  { value: 'minor', label: 'Minor' },
];

// Entity Row Component
function EntityRow({
  entity,
  type,
  onToggle,
  onUpdateTag,
  onChangeType,
  onRemove,
  onUpdateRole,
  onUpdateName,
  onUpdateDescription,
}: {
  entity: ExtractedEntity;
  type: EntityType;
  onToggle: () => void;
  onUpdateTag: (tag: string) => void;
  onChangeType: (type: EntityType) => void;
  onRemove: () => void;
  onUpdateRole?: (role: string) => void;
  onUpdateName?: (name: string) => void;
  onUpdateDescription?: (description: string) => void;
}) {
  const [isEditingTag, setIsEditingTag] = useState(false);
  const [editedTag, setEditedTag] = useState(entity.tag || '');
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(entity.name);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedDescription, setEditedDescription] = useState(entity.description || '');
  const Icon = getEntityTypeIcon(type);
  const typeColor = getTypeColor(type);

  const handleSaveTag = () => {
    onUpdateTag(editedTag);
    setIsEditingTag(false);
  };

  const handleSaveName = () => {
    if (onUpdateName && editedName.trim()) {
      onUpdateName(editedName.trim());
    }
    setIsEditingName(false);
  };

  const handleSaveDescription = () => {
    if (onUpdateDescription) {
      onUpdateDescription(editedDescription);
    }
    setIsEditingDescription(false);
  };

  return (
    <div className={cn(
      "flex items-start gap-3 p-3 rounded-lg border transition-colors",
      entity.selected
        ? "bg-gl-bg-medium/50 border-gl-border"
        : "bg-transparent border-transparent opacity-60"
    )}>
      {/* Checkbox */}
      <button
        onClick={onToggle}
        className={cn(
          "w-5 h-5 rounded border flex items-center justify-center shrink-0 mt-0.5",
          entity.selected
            ? "bg-gl-accent border-gl-accent"
            : "bg-transparent border-gl-text-muted"
        )}
      >
        {entity.selected && <Check className="w-3 h-3 text-white" />}
      </button>

      {/* Icon */}
      <div className={cn("p-1.5 rounded", typeColor)}>
        <Icon className="w-4 h-4" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          {isEditingName ? (
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              onBlur={handleSaveName}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
              className="px-2 py-0.5 text-sm font-medium bg-gl-bg-medium border border-gl-border rounded flex-1"
              autoFocus
            />
          ) : (
            <button
              onClick={() => setIsEditingName(true)}
              className="font-medium text-gl-text-primary hover:text-gl-accent transition-colors flex items-center gap-1 group"
              title="Click to edit name"
            >
              {entity.name}
              <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          )}
          {entity.role_hint && !isEditingName && (
            <span className="px-1.5 py-0.5 text-xs bg-gl-bg-medium rounded text-gl-text-muted">
              {entity.role_hint}
            </span>
          )}
          {entity.mentions && entity.mentions > 1 && !isEditingName && (
            <span className="text-xs text-gl-text-muted">
              ({entity.mentions} mentions)
            </span>
          )}
        </div>

        {/* Tag */}
        <div className="flex items-center gap-2">
          {isEditingTag ? (
            <input
              type="text"
              value={editedTag}
              onChange={(e) => setEditedTag(e.target.value.toUpperCase())}
              onBlur={handleSaveTag}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveTag()}
              className="px-2 py-0.5 text-xs font-mono bg-gl-bg-medium border border-gl-border rounded w-48"
              autoFocus
            />
          ) : (
            <button
              onClick={() => setIsEditingTag(true)}
              className="px-2 py-0.5 text-xs font-mono text-gl-accent bg-gl-accent/10 rounded hover:bg-gl-accent/20 flex items-center gap-1"
            >
              [{entity.tag}]
              <Edit2 className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Description - Editable */}
        <div>
          {isEditingDescription ? (
            <textarea
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              onBlur={handleSaveDescription}
              className="w-full px-2 py-1 text-xs bg-gl-bg-medium border border-gl-border rounded resize-none"
              rows={2}
              placeholder="Add a description..."
              autoFocus
            />
          ) : (
            <button
              onClick={() => setIsEditingDescription(true)}
              className="text-xs text-gl-text-muted hover:text-gl-text-secondary transition-colors text-left w-full group"
              title="Click to edit description"
            >
              {entity.description || entity.contexts?.[0] ? (
                <span className="flex items-start gap-1">
                  <span className="line-clamp-2">&ldquo;{entity.description || entity.contexts?.[0]}&rdquo;</span>
                  <Edit2 className="w-3 h-3 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity mt-0.5" />
                </span>
              ) : (
                <span className="italic flex items-center gap-1">
                  Add description...
                  <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </span>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        {/* Role Dropdown (Characters only) */}
        {type === 'character' && onUpdateRole && (
          <select
            value={entity.role_hint || 'supporting'}
            onChange={(e) => onUpdateRole(e.target.value)}
            className="px-2 py-1 text-xs bg-gl-bg-medium border border-gl-border rounded text-gl-text-secondary"
          >
            {CHARACTER_ROLES.map(r => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        )}

        {/* Change Type Dropdown */}
        <select
          value={type}
          onChange={(e) => onChangeType(e.target.value as EntityType)}
          className="px-2 py-1 text-xs bg-gl-bg-medium border border-gl-border rounded text-gl-text-secondary"
        >
          {ENTITY_TYPES.map(t => (
            <option key={t.key} value={t.key}>{t.label.slice(0, -1)}</option>
          ))}
        </select>

        {/* Remove */}
        <button
          onClick={onRemove}
          className="p-1 text-gl-text-muted hover:text-red-400 rounded hover:bg-gl-bg-hover"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
