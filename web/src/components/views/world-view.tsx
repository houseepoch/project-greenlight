"use client";

import { useState, useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { fetchAPI, cn, API_BASE_URL } from "@/lib/utils";
import { Globe, User, MapPin, Package, RefreshCw, ChevronDown, ChevronUp, Save, Edit2, Sparkles, Loader2, X, Info, ImageIcon, ZoomIn, ZoomOut, Upload } from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import * as Dialog from "@radix-ui/react-dialog";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";

const MODEL_OPTIONS = [
  { key: 'z_image_turbo', name: 'Z-Image Turbo (Default)' },
  { key: 'nano_banana_pro', name: 'Nano Banana Pro (Best)' },
  { key: 'seedream', name: 'Seedream 4.5 (Fast)' },
  { key: 'flux_2_pro', name: 'FLUX 2 Pro (8 refs, text)' },
  { key: 'p_image_edit', name: 'P-Image-Edit ($0.01, fast)' },
];

const VISUAL_STYLES = [
  { key: 'live_action', name: 'Live Action', description: 'Photorealistic live-action cinematography' },
  { key: 'anime', name: 'Anime', description: 'Japanese anime style with expressive characters and bold colors' },
  { key: 'animation_2d', name: '2D Animation', description: 'Hand-drawn 2D animation aesthetic (Disney, Ghibli)' },
  { key: 'animation_3d', name: '3D Animation', description: 'Modern 3D CGI rendering (Pixar, Dreamworks)' },
  { key: 'cartoon', name: 'Cartoon', description: 'Stylized cartoon aesthetic with exaggerated features' },
  { key: 'claymation', name: 'Claymation', description: 'Stop-motion clay animation style (Aardman, Laika)' },
  { key: 'mixed', name: 'Mixed Media', description: 'Blend of multiple styles - specify in style notes' },
];

const MEDIA_TYPES = [
  { key: 'feature_film', name: 'Feature Film', description: '90-180 minute theatrical release' },
  { key: 'short_film', name: 'Short Film', description: 'Under 40 minute standalone story' },
  { key: 'series_episode', name: 'Series Episode', description: 'Episodic TV/streaming content' },
  { key: 'commercial', name: 'Commercial', description: 'Advertising or promotional content' },
  { key: 'music_video', name: 'Music Video', description: 'Visual accompaniment to music' },
];

interface WorldEntity {
  tag: string;
  name: string;
  description?: string;
  imagePath?: string;
  relationships?: string[];
  scenes?: number[];
  // Character-specific fields
  role?: string;
  appearance?: string;
  clothing?: string;
  personality?: string;
  summary?: string;
  want?: string;
  need?: string;
  flaw?: string;
  backstory?: string;
  voice_signature?: string;
  emotional_tells?: Record<string, string>;
  physicality?: string;
  speech_patterns?: string;
  // Location-specific fields
  time_of_day?: string;
  view_north?: string;
  view_east?: string;
  view_south?: string;
  view_west?: string;
}

interface StyleData {
  visual_style?: string;
  style_notes?: string;
  lighting?: string;
  vibe?: string;
}

interface WorldContext {
  setting?: string;
  time_period?: string;
  cultural_context?: string;
  social_structure?: string;
  technology_level?: string;
  clothing_norms?: string;
  architecture_style?: string;
  color_palette?: string;
  lighting_style?: string;
  mood?: string;
}

interface WorldData {
  characters: WorldEntity[];
  locations: WorldEntity[];
  props: WorldEntity[];
  style?: StyleData;
  world_context?: WorldContext;
  visual_style?: string;
  genre?: string;
  media_type?: string;
}

const tabs = [
  { id: "characters", label: "Characters", icon: User },
  { id: "locations", label: "Locations", icon: MapPin },
  { id: "props", label: "Props", icon: Package },
  { id: "world", label: "World Settings", icon: Globe },
];

// Get icon based on entity type
function getEntityIcon(tab: string) {
  switch (tab) {
    case "characters": return User;
    case "locations": return MapPin;
    case "props": return Package;
    default: return Globe;
  }
}

// Get tag color based on prefix
function getTagColor(tag: string): string {
  if (tag.startsWith("CHAR_")) return "text-blue-400 bg-blue-500/10";
  if (tag.startsWith("LOC_")) return "text-green-400 bg-green-500/10";
  if (tag.startsWith("PROP_")) return "text-orange-400 bg-orange-500/10";
  return "text-primary bg-primary/10";
}

export function WorldView() {
  const { currentProject, addPipelineProcess, updatePipelineProcess, addProcessLog, setWorkspaceMode } = useAppStore();
  const [worldData, setWorldData] = useState<WorldData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("characters");
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // FAB state for bulk reference generation
  const [generatingAll, setGeneratingAll] = useState(false);
  const [fabModel, setFabModel] = useState('z_image_turbo');
  const [fabMenuOpen, setFabMenuOpen] = useState(false);

  // Zoom level for entity grid (2-6 columns, default 4)
  const [zoomLevel, setZoomLevel] = useState(4);

  const loadWorld = async () => {
    if (!currentProject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAPI<WorldData>(
        `/api/projects/path-data/world?path=${encodeURIComponent(currentProject.path)}`
      );
      setWorldData(data);
    } catch (err) {
      // For new projects, world data won't exist yet
      setWorldData({ characters: [], locations: [], props: [], world_context: {} });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorld();
  }, [currentProject]);

  const toggleCard = (tag: string) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  };

  // Track logs we've already added to avoid duplicates during polling
  const [processedLogs, setProcessedLogs] = useState<Set<string>>(new Set());

  const handleGenerateAll = async () => {
    if (!currentProject || generatingAll) return;

    setGeneratingAll(true);
    setFabMenuOpen(false);
    setProcessedLogs(new Set());

    // Create a local process ID for the store (different from backend process_id)
    const localProcessId = `references-${Date.now()}`;
    const tabLabel = activeTab.charAt(0).toUpperCase() + activeTab.slice(1);
    const modelLabel = MODEL_OPTIONS.find(m => m.key === fabModel)?.name || fabModel;

    addPipelineProcess({
      id: localProcessId,
      name: `Generate ${tabLabel} References`,
      status: 'initializing',
      progress: 0,
      startTime: new Date(),
    });

    // Switch to progress view to show the generation
    setWorkspaceMode('progress');

    try {
      addProcessLog(localProcessId, `Starting reference generation for ${tabLabel}...`, 'info');
      addProcessLog(localProcessId, `Using model: ${modelLabel}`, 'info');
      updatePipelineProcess(localProcessId, { status: 'running' });

      // Start the background process - returns immediately with process_id
      const response = await fetchAPI<{
        success: boolean;
        message: string;
        process_id?: string;
      }>(`/api/projects/${encodeURIComponent(currentProject.path)}/references/generate-all`, {
        method: 'POST',
        body: JSON.stringify({
          tagType: activeTab,
          model: fabModel,
          overwrite: false,
          visual_style: worldData?.style?.visual_style || 'live_action'
        })
      });

      if (response.success && response.process_id) {
        // Store backend ID for cancellation
        updatePipelineProcess(localProcessId, { backendId: response.process_id });
        addProcessLog(localProcessId, `Process started with ID: ${response.process_id}`, 'info');
        // Start polling for status updates
        pollReferenceStatus(response.process_id, localProcessId);
      } else {
        addProcessLog(localProcessId, response.message || 'Failed to start generation', 'error');
        updatePipelineProcess(localProcessId, {
          status: 'error',
          endTime: new Date()
        });
        setGeneratingAll(false);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      addProcessLog(localProcessId, `Error: ${errorMsg}`, 'error');
      updatePipelineProcess(localProcessId, {
        status: 'error',
        error: errorMsg,
        endTime: new Date()
      });
      setGeneratingAll(false);
    }
  };

  const pollReferenceStatus = async (backendProcessId: string, localProcessId: string) => {
    if (!currentProject) return;

    const poll = async () => {
      try {
        const status = await fetchAPI<{
          status: string;
          progress: number;
          logs: string[];
          generated: number;
          skipped: number;
          total: number;
          errors: string[];
          error?: string;
        }>(`/api/projects/${encodeURIComponent(currentProject.path)}/references/status/${backendProcessId}`);

        // Update progress
        updatePipelineProcess(localProcessId, { progress: status.progress });

        // Add new logs (avoid duplicates)
        if (status.logs && status.logs.length > 0) {
          status.logs.forEach((log, idx) => {
            const logKey = `${idx}-${log}`;
            if (!processedLogs.has(logKey)) {
              const type = log.includes('❌') || log.includes('Error') || log.includes('Failed') ? 'error' :
                          log.includes('✓') || log.includes('✅') || log.includes('Complete') ? 'success' :
                          log.includes('⏭️') || log.includes('Skipping') ? 'warning' : 'info';
              addProcessLog(localProcessId, log, type);
              setProcessedLogs(prev => new Set(prev).add(logKey));
            }
          });
        }

        // Check completion status
        if (status.status === 'complete') {
          updatePipelineProcess(localProcessId, {
            status: 'complete',
            progress: 1,
            endTime: new Date()
          });
          setGeneratingAll(false);
          // Refresh world data to show new images
          loadWorld();
        } else if (status.status === 'error' || status.status === 'failed') {
          addProcessLog(localProcessId, status.error || 'Generation failed', 'error');
          updatePipelineProcess(localProcessId, {
            status: 'error',
            error: status.error,
            endTime: new Date()
          });
          setGeneratingAll(false);
        } else if (status.status === 'cancelled') {
          addProcessLog(localProcessId, 'Reference generation was cancelled', 'warning');
          updatePipelineProcess(localProcessId, {
            status: 'cancelled',
            endTime: new Date()
          });
          setGeneratingAll(false);
        } else {
          // Still running, poll again
          setTimeout(poll, 1000);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        addProcessLog(localProcessId, `Polling error: ${errorMsg}`, 'error');
        updatePipelineProcess(localProcessId, {
          status: 'error',
          error: errorMsg,
          endTime: new Date()
        });
        setGeneratingAll(false);
      }
    };

    poll();
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-destructive">{error}</p>
          <button onClick={loadWorld} className="text-sm text-primary hover:underline">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!worldData) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Globe className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="font-medium">No World Data</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Run the Writer pipeline to generate world data
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getEntities = () => {
    switch (activeTab) {
      case "characters": return worldData.characters || [];
      case "locations": return worldData.locations || [];
      case "props": return worldData.props || [];
      default: return [];
    }
  };

  const getCounts = () => ({
    characters: worldData.characters?.length || 0,
    locations: worldData.locations?.length || 0,
    props: worldData.props?.length || 0,
  });

  const counts = getCounts();

  return (
    <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
      <Tabs.List className="flex border-b border-border px-4 bg-card/50">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const count = counts[tab.id as keyof typeof counts];
          return (
            <Tabs.Trigger
              key={tab.id}
              value={tab.id}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
              {count !== undefined && count > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-secondary rounded-full">{count}</span>
              )}
            </Tabs.Trigger>
          );
        })}
      </Tabs.List>

      {/* Entity Tabs */}
      {activeTab !== "world" && (
        <Tabs.Content value={activeTab} className="flex-1 overflow-hidden flex flex-col">
          {/* Zoom Control Bar */}
          <div className="flex items-center justify-end gap-3 px-4 py-2 border-b border-border bg-card/30">
            <span className="text-xs text-muted-foreground">Cards per row:</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoomLevel(Math.max(2, zoomLevel - 1))}
                disabled={zoomLevel <= 2}
                className="p-1 hover:bg-secondary rounded disabled:opacity-30 disabled:cursor-not-allowed"
                title="Fewer cards (larger)"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <span className="w-6 text-center text-sm font-medium">{zoomLevel}</span>
              <button
                onClick={() => setZoomLevel(Math.min(6, zoomLevel + 1))}
                disabled={zoomLevel >= 6}
                className="p-1 hover:bg-secondary rounded disabled:opacity-30 disabled:cursor-not-allowed"
                title="More cards (smaller)"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
            </div>
          </div>
          <EntityGrid
            entities={getEntities()}
            tabType={activeTab}
            expandedCards={expandedCards}
            onToggleCard={toggleCard}
            projectPath={currentProject?.path}
            onRefresh={loadWorld}
            columns={zoomLevel}
          />
        </Tabs.Content>
      )}

      {/* World Settings Tab */}
      <Tabs.Content value="world" className="flex-1 overflow-hidden">
        <WorldSettingsTab
          worldData={worldData}
          projectPath={currentProject?.path}
          onSave={loadWorld}
        />
      </Tabs.Content>

      {/* Generate All References FAB - only show on entity tabs */}
      {activeTab !== "world" && (
        <div className="fixed bottom-6 right-6 z-40">
          {/* FAB with dropdown */}
          <div className="relative">
            {fabMenuOpen && (
              <div className="absolute bottom-full right-0 mb-2 w-48 bg-card border border-border rounded-lg shadow-xl overflow-hidden">
                <div className="p-2 border-b border-border">
                  <span className="text-xs text-muted-foreground">Select Model</span>
                </div>
                {MODEL_OPTIONS.map((model) => (
                  <button
                    key={model.key}
                    onClick={() => setFabModel(model.key)}
                    className={cn(
                      "w-full text-left px-3 py-2 text-sm hover:bg-secondary transition-colors",
                      fabModel === model.key && "bg-secondary text-primary"
                    )}
                  >
                    {model.name}
                    {fabModel === model.key && " ✓"}
                  </button>
                ))}
                <div className="border-t border-border p-2">
                  <button
                    onClick={handleGenerateAll}
                    disabled={generatingAll}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                  >
                    {generatingAll ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Generate All
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            <button
              onClick={() => setFabMenuOpen(!fabMenuOpen)}
              disabled={generatingAll}
              className={cn(
                "flex items-center gap-2 px-4 py-3 rounded-full shadow-lg transition-all",
                generatingAll
                  ? "bg-muted text-muted-foreground"
                  : "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-xl"
              )}
            >
              {generatingAll ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Sparkles className="h-5 w-5" />
              )}
              <span className="font-medium">
                {generatingAll ? "Generating..." : "Generate All References"}
              </span>
            </button>
          </div>
        </div>
      )}
    </Tabs.Root>
  );
}

function EntityGrid({
  entities,
  tabType,
  expandedCards,
  onToggleCard,
  projectPath,
  onRefresh,
  columns = 4
}: {
  entities: WorldEntity[];
  tabType: string;
  expandedCards: Set<string>;
  onToggleCard: (tag: string) => void;
  projectPath?: string;
  onRefresh?: () => void;
  columns?: number;
}) {
  const Icon = getEntityIcon(tabType);

  // Map column count to Tailwind grid classes
  const gridColsClass = {
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-4",
    5: "grid-cols-5",
    6: "grid-cols-6",
  }[columns] || "grid-cols-4";

  if (entities.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Icon className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="font-medium">No {tabType} found</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Run the Writer pipeline to extract {tabType}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-hidden">
      <ScrollArea.Root className="h-full">
        <ScrollArea.Viewport className="h-full w-full">
          <div className={cn("grid gap-4 p-4", gridColsClass)}>
            {entities.map((entity) => (
              <EntityCard
                key={entity.tag}
                entity={entity}
                tabType={tabType}
                isExpanded={expandedCards.has(entity.tag)}
                onToggle={() => onToggleCard(entity.tag)}
                projectPath={projectPath}
                onRefresh={onRefresh}
              />
            ))}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex select-none touch-none p-0.5 bg-secondary w-2" orientation="vertical">
          <ScrollArea.Thumb className="flex-1 bg-muted-foreground rounded-full" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </div>
  );
}

function EntityCard({
  entity,
  tabType,
  isExpanded,
  onToggle,
  projectPath,
  onRefresh
}: {
  entity: WorldEntity;
  tabType: string;
  isExpanded: boolean;
  onToggle: () => void;
  projectPath?: string;
  onRefresh?: () => void;
}) {
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [imageCacheBuster, setImageCacheBuster] = useState(Date.now());
  const [isEditing, setIsEditing] = useState(false);
  const [editedEntity, setEditedEntity] = useState<Partial<WorldEntity>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const Icon = getEntityIcon(tabType);
  const tagColor = getTagColor(entity.tag);

  // Initialize edited entity when entering edit mode
  const startEditing = () => {
    setEditedEntity({
      name: entity.name,
      description: entity.description || '',
      appearance: entity.appearance || '',
      clothing: entity.clothing || '',
      personality: entity.personality || '',
      summary: entity.summary || '',
      want: entity.want || '',
      need: entity.need || '',
      flaw: entity.flaw || '',
      backstory: entity.backstory || '',
      view_north: entity.view_north || '',
      view_east: entity.view_east || '',
      view_south: entity.view_south || '',
      view_west: entity.view_west || '',
    });
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditedEntity({});
  };

  const saveEntity = async () => {
    if (!projectPath) return;
    setIsSaving(true);
    try {
      await fetchAPI(`/api/projects/path-data/world/entity/${entity.tag}?path=${encodeURIComponent(projectPath)}`, {
        method: 'PATCH',
        body: JSON.stringify(editedEntity)
      });
      setIsEditing(false);
      setEditedEntity({});
      onRefresh?.();
    } catch (err) {
      console.error('Failed to save entity:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field: keyof WorldEntity, value: string) => {
    setEditedEntity(prev => ({ ...prev, [field]: value }));
  };

  // Map tabType to tagType for the modal
  const tagType = tabType === "characters" ? "character" : tabType === "locations" ? "location" : "prop";

  // Get summary text for minimized view
  const getSummaryText = () => {
    if (tabType === "characters") {
      return entity.summary || entity.description || "";
    }
    return entity.description || "";
  };

  // Check if entity has extended details
  const hasExtendedDetails = tabType === "characters" && (
    entity.appearance || entity.clothing || entity.personality ||
    entity.want || entity.need || entity.flaw ||
    entity.backstory || entity.voice_signature || entity.emotional_tells ||
    entity.physicality || entity.speech_patterns
  );

  // Check if location has directional views
  const hasLocationViews = tabType === "locations" && (
    entity.view_north || entity.view_east || entity.view_south || entity.view_west
  );

  // Handle single reference generation using z_image_turbo
  const handleGenerateReference = async () => {
    if (!projectPath || isGenerating) return;

    setIsGenerating(true);
    try {
      const response = await fetchAPI<{ success: boolean; message?: string; error?: string; path?: string }>(
        `/api/projects/path-data/references/generate?path=${encodeURIComponent(projectPath)}`,
        {
          method: 'POST',
          body: JSON.stringify({
            tag: entity.tag,
            model: 'z_image_turbo',  // Default to z_image_turbo for reference images
            overwrite: true
          })
        }
      );

      if (response.success) {
        // Bust the cache and refresh to show new image
        setImageCacheBuster(Date.now());
        onRefresh?.();
      } else {
        console.error('Generation failed:', response.error || response.message);
      }
    } catch (err) {
      console.error('Failed to generate reference:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle image upload
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !projectPath) return;

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      console.error('Invalid file type. Please upload PNG, JPEG, or WebP.');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Use path-data endpoint with query params for path and tag
      const response = await fetch(
        `${API_BASE_URL}/api/projects/path-data/references/upload?path=${encodeURIComponent(projectPath)}&tag=${encodeURIComponent(entity.tag)}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      const result = await response.json();

      if (result.success) {
        // Bust the cache and refresh to show new image
        setImageCacheBuster(Date.now());
        onRefresh?.();
      } else {
        console.error('Upload failed:', result.error || result.message);
      }
    } catch (err) {
      console.error('Failed to upload image:', err);
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <>
      {/* Hidden file input for image upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        onChange={handleImageUpload}
        className="hidden"
      />

      <div className="bg-card rounded-lg border border-border overflow-hidden hover:border-primary/50 transition-colors">
        {/* Image Section */}
        <div className="aspect-[16/12] bg-secondary flex items-center justify-center relative group">
          {entity.imagePath ? (
            <>
              <img
                src={`${API_BASE_URL}/api/images/${encodeURIComponent(entity.imagePath)}?t=${imageCacheBuster}`}
                alt={entity.name}
                className="w-full h-full object-contain bg-black"
              />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                {/* Upload Button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Upload
                    </>
                  )}
                </button>
                {/* Generate Button */}
                <button
                  onClick={handleGenerateReference}
                  disabled={isGenerating || isUploading}
                  className="px-3 py-1.5 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <ImageIcon className="h-4 w-4" />
                      Regenerate
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Icon className="h-12 w-12 text-muted-foreground" />
              <div className="flex items-center gap-2">
                {/* Upload Button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-3 w-3" />
                      Upload
                    </>
                  )}
                </button>
                {/* Generate Button */}
                <button
                  onClick={handleGenerateReference}
                  disabled={isGenerating || isUploading}
                  className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <ImageIcon className="h-3 w-3" />
                      Generate
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Content Section */}
        <div className="p-3 space-y-2">
          {/* Tag Badge and Role */}
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1 flex-wrap min-w-0 flex-1">
              <span className={cn("px-1.5 py-0.5 text-[10px] font-mono rounded truncate", tagColor)}>
                [{entity.tag}]
              </span>
              {entity.role && (
                <span className="px-1.5 py-0.5 bg-secondary text-[10px] rounded capitalize truncate">
                  {entity.role.replace(/_/g, ' ')}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              {isEditing ? (
                <>
                  <button
                    onClick={cancelEditing}
                    className="p-1.5 hover:bg-secondary rounded transition-colors text-muted-foreground"
                    title="Cancel editing"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <button
                    onClick={saveEntity}
                    disabled={isSaving}
                    className="p-1.5 hover:bg-green-500/20 rounded transition-colors text-green-500 disabled:opacity-50"
                    title="Save changes"
                  >
                    {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  </button>
                </>
              ) : (
                <button
                  onClick={startEditing}
                  className="p-1.5 hover:bg-secondary rounded transition-colors"
                  title="Edit entity"
                >
                  <Edit2 className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={onToggle}
                className="p-1.5 hover:bg-secondary rounded transition-colors bg-secondary/50"
                title={isExpanded ? "Collapse details" : "Expand details"}
              >
                {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Name */}
          {isEditing ? (
            <input
              type="text"
              value={editedEntity.name || ''}
              onChange={(e) => updateField('name', e.target.value)}
              className="w-full px-2 py-1 bg-secondary border border-border rounded text-sm font-semibold"
            />
          ) : (
            <h3 className="font-semibold text-sm leading-tight truncate" title={entity.name}>{entity.name}</h3>
          )}

          {/* Minimized View - Summary only */}
          {!isExpanded && (
            <div className="space-y-0.5">
              {isEditing ? (
                <textarea
                  value={tabType === "characters" ? (editedEntity.summary || '') : (editedEntity.description || '')}
                  onChange={(e) => updateField(tabType === "characters" ? 'summary' : 'description', e.target.value)}
                  className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                  rows={2}
                  placeholder={tabType === "characters" ? "Character summary..." : "Description..."}
                />
              ) : (
                <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                  {getSummaryText()}
                </p>
              )}
            </div>
          )}

          {/* Expanded Details */}
          {isExpanded && (
            <div className="space-y-2">
              {/* Character-specific fields */}
              {tabType === "characters" && (
                <>
                  {(entity.appearance || isEditing) && (
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-medium text-blue-400">Appearance</span>
                      {isEditing ? (
                        <textarea
                          value={editedEntity.appearance || ''}
                          onChange={(e) => updateField('appearance', e.target.value)}
                          className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                          rows={2}
                          placeholder="Physical appearance..."
                        />
                      ) : (
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-3">
                          {entity.appearance}
                        </p>
                      )}
                    </div>
                  )}
                  {(entity.clothing || isEditing) && (
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-medium text-purple-400">Clothing</span>
                      {isEditing ? (
                        <textarea
                          value={editedEntity.clothing || ''}
                          onChange={(e) => updateField('clothing', e.target.value)}
                          className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                          rows={2}
                          placeholder="Clothing style..."
                        />
                      ) : (
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                          {entity.clothing}
                        </p>
                      )}
                    </div>
                  )}
                  {(entity.personality || isEditing) && (
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-medium text-green-400">Personality</span>
                      {isEditing ? (
                        <textarea
                          value={editedEntity.personality || ''}
                          onChange={(e) => updateField('personality', e.target.value)}
                          className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                          rows={2}
                          placeholder="Personality traits..."
                        />
                      ) : (
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                          {entity.personality}
                        </p>
                      )}
                    </div>
                  )}
                  {(entity.summary || isEditing) && (
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-medium text-orange-400">Summary</span>
                      {isEditing ? (
                        <textarea
                          value={editedEntity.summary || ''}
                          onChange={(e) => updateField('summary', e.target.value)}
                          className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                          rows={2}
                          placeholder="Character summary..."
                        />
                      ) : (
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-3">
                          {entity.summary}
                        </p>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Location-specific fields */}
              {tabType === "locations" && (
                <>
                  {(entity.description || isEditing) && (
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-medium text-muted-foreground">Description</span>
                      {isEditing ? (
                        <textarea
                          value={editedEntity.description || ''}
                          onChange={(e) => updateField('description', e.target.value)}
                          className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                          rows={2}
                          placeholder="Location description..."
                        />
                      ) : (
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-3">
                          {entity.description}
                        </p>
                      )}
                    </div>
                  )}
                  {(hasLocationViews || isEditing) && (
                    <div className="space-y-1 pt-1 border-t border-border">
                      <span className="text-[10px] font-medium text-muted-foreground">Directional Views</span>
                      <div className="grid grid-cols-2 gap-1">
                        <div className="p-1.5 bg-secondary/50 rounded">
                          <span className="text-[10px] font-medium text-blue-400">N</span>
                          {isEditing ? (
                            <textarea
                              value={editedEntity.view_north || ''}
                              onChange={(e) => updateField('view_north', e.target.value)}
                              className="w-full px-1 py-0.5 bg-secondary border border-border rounded text-[10px] resize-y min-h-[2.5rem] mt-0.5"
                              rows={2}
                              placeholder="North view..."
                            />
                          ) : (
                            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{entity.view_north || '-'}</p>
                          )}
                        </div>
                        <div className="p-1.5 bg-secondary/50 rounded">
                          <span className="text-[10px] font-medium text-green-400">E</span>
                          {isEditing ? (
                            <textarea
                              value={editedEntity.view_east || ''}
                              onChange={(e) => updateField('view_east', e.target.value)}
                              className="w-full px-1 py-0.5 bg-secondary border border-border rounded text-[10px] resize-y min-h-[2.5rem] mt-0.5"
                              rows={2}
                              placeholder="East view..."
                            />
                          ) : (
                            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{entity.view_east || '-'}</p>
                          )}
                        </div>
                        <div className="p-1.5 bg-secondary/50 rounded">
                          <span className="text-[10px] font-medium text-orange-400">S</span>
                          {isEditing ? (
                            <textarea
                              value={editedEntity.view_south || ''}
                              onChange={(e) => updateField('view_south', e.target.value)}
                              className="w-full px-1 py-0.5 bg-secondary border border-border rounded text-[10px] resize-y min-h-[2.5rem] mt-0.5"
                              rows={2}
                              placeholder="South view..."
                            />
                          ) : (
                            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{entity.view_south || '-'}</p>
                          )}
                        </div>
                        <div className="p-1.5 bg-secondary/50 rounded">
                          <span className="text-[10px] font-medium text-purple-400">W</span>
                          {isEditing ? (
                            <textarea
                              value={editedEntity.view_west || ''}
                              onChange={(e) => updateField('view_west', e.target.value)}
                              className="w-full px-1 py-0.5 bg-secondary border border-border rounded text-[10px] resize-y min-h-[2.5rem] mt-0.5"
                              rows={2}
                              placeholder="West view..."
                            />
                          ) : (
                            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{entity.view_west || '-'}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Props - just description */}
              {tabType === "props" && (entity.description || isEditing) && (
                <div className="space-y-0.5">
                  <span className="text-[10px] font-medium text-muted-foreground">Description</span>
                  {isEditing ? (
                    <textarea
                      value={editedEntity.description || ''}
                      onChange={(e) => updateField('description', e.target.value)}
                      className="w-full px-2 py-1 bg-secondary border border-border rounded text-[11px] resize-y min-h-[3rem]"
                      rows={2}
                      placeholder="Prop description..."
                    />
                  ) : (
                    <p className="text-[11px] text-muted-foreground leading-snug line-clamp-3">
                      {entity.description}
                    </p>
                  )}
                </div>
              )}

              {/* Relationships */}
              {entity.relationships && entity.relationships.length > 0 && (
                <div className="pt-1 border-t border-border">
                  <span className="text-[10px] font-medium text-muted-foreground">Relationships</span>
                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                    {entity.relationships.slice(0, 4).map((rel) => (
                      <span key={rel} className="px-1 py-0.5 bg-secondary text-[10px] rounded">
                        {rel}
                      </span>
                    ))}
                    {entity.relationships.length > 4 && (
                      <span className="px-1 py-0.5 text-[10px] text-muted-foreground">
                        +{entity.relationships.length - 4} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Scene appearances */}
              {entity.scenes && entity.scenes.length > 0 && (
                <div>
                  <span className="text-[10px] font-medium text-muted-foreground">Appears in</span>
                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                    {entity.scenes.slice(0, 6).map((scene) => (
                      <span key={scene} className="px-1 py-0.5 bg-primary/10 text-primary text-[10px] rounded">
                        S{scene}
                      </span>
                    ))}
                    {entity.scenes.length > 6 && (
                      <span className="px-1 py-0.5 text-[10px] text-muted-foreground">
                        +{entity.scenes.length - 6}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* See Full Profile button for characters with more details */}
              {hasExtendedDetails && (
                <button
                  onClick={() => setDetailModalOpen(true)}
                  className="w-full mt-1 px-2 py-1.5 bg-secondary hover:bg-secondary/80 text-[11px] rounded transition-colors flex items-center justify-center gap-1"
                >
                  <Info className="h-3 w-3" />
                  Full Profile
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Character Detail Modal */}
      {hasExtendedDetails && (
        <CharacterDetailModal
          open={detailModalOpen}
          onOpenChange={setDetailModalOpen}
          entity={entity}
        />
      )}
    </>
  );
}

// Character Detail Modal Component
function CharacterDetailModal({
  open,
  onOpenChange,
  entity
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entity: WorldEntity;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-card border border-border rounded-lg shadow-xl z-50 w-[90vw] max-w-3xl max-h-[85vh] flex flex-col">
          <VisuallyHidden.Root>
            <Dialog.Description>
              Full character profile for {entity.name}
            </Dialog.Description>
          </VisuallyHidden.Root>

          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <Dialog.Title className="text-lg font-semibold flex items-center gap-2">
              <User className="h-5 w-5" />
              {entity.name}
              {entity.role && (
                <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded capitalize">
                  {entity.role.replace(/_/g, ' ')}
                </span>
              )}
            </Dialog.Title>
            <Dialog.Close className="p-2 hover:bg-secondary rounded-md transition-colors">
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>

          {/* Content */}
          <ScrollArea.Root className="flex-1 overflow-hidden">
            <ScrollArea.Viewport className="h-full w-full p-6">
              <div className="space-y-6">
                {/* Summary */}
                {entity.summary && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Summary</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {entity.summary}
                    </p>
                  </section>
                )}

                {/* Appearance & Clothing */}
                {(entity.appearance || entity.clothing) && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Physical Description</h3>
                    <div className="space-y-3">
                      {entity.appearance && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-blue-400">Appearance</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.appearance}</p>
                        </div>
                      )}
                      {entity.clothing && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-purple-400">Clothing</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.clothing}</p>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Personality */}
                {entity.personality && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Personality</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {entity.personality}
                    </p>
                  </section>
                )}

                {/* Core Motivations */}
                {(entity.want || entity.need || entity.flaw) && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Core Motivations</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {entity.want && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-green-400">WANT</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.want}</p>
                        </div>
                      )}
                      {entity.need && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-blue-400">NEED</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.need}</p>
                        </div>
                      )}
                      {entity.flaw && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-red-400">FLAW</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.flaw}</p>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Backstory */}
                {entity.backstory && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Backstory</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {entity.backstory}
                    </p>
                  </section>
                )}

                {/* Voice & Speech */}
                {(entity.voice_signature || entity.speech_patterns) && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Voice & Speech</h3>
                    <div className="space-y-2">
                      {entity.voice_signature && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-purple-400">Voice Signature</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.voice_signature}</p>
                        </div>
                      )}
                      {entity.speech_patterns && (
                        <div className="p-3 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-purple-400">Speech Patterns</span>
                          <p className="text-sm text-muted-foreground mt-1">{entity.speech_patterns}</p>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Physicality */}
                {entity.physicality && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Physicality</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {entity.physicality}
                    </p>
                  </section>
                )}

                {/* Emotional Tells */}
                {entity.emotional_tells && Object.keys(entity.emotional_tells).length > 0 && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Emotional Tells</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(entity.emotional_tells).map(([emotion, tell]) => (
                        <div key={emotion} className="p-2 bg-secondary/50 rounded-lg">
                          <span className="text-xs font-medium text-orange-400 capitalize">{emotion}</span>
                          <p className="text-xs text-muted-foreground mt-1">{tell}</p>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Relationships */}
                {entity.relationships && entity.relationships.length > 0 && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Relationships</h3>
                    <div className="flex flex-wrap gap-2">
                      {entity.relationships.map((rel) => (
                        <span key={rel} className="px-2 py-1 bg-secondary text-sm rounded">
                          {rel}
                        </span>
                      ))}
                    </div>
                  </section>
                )}

                {/* Scenes */}
                {entity.scenes && entity.scenes.length > 0 && (
                  <section>
                    <h3 className="text-sm font-semibold text-primary mb-2">Appears In</h3>
                    <div className="flex flex-wrap gap-2">
                      {entity.scenes.map((scene) => (
                        <span key={scene} className="px-2 py-1 bg-primary/10 text-primary text-sm rounded">
                          Scene {scene}
                        </span>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </ScrollArea.Viewport>
            <ScrollArea.Scrollbar className="flex select-none touch-none p-0.5 bg-secondary w-2" orientation="vertical">
              <ScrollArea.Thumb className="flex-1 bg-muted-foreground rounded-full" />
            </ScrollArea.Scrollbar>
          </ScrollArea.Root>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// Editable Field Component for World Settings
function EditableField({
  label,
  icon,
  value,
  onSave,
  multiline = false
}: {
  label: string;
  icon: string;
  value: string;
  onSave: (newValue: string) => Promise<void>;
  multiline?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (editValue === value) {
      setIsEditing(false);
      return;
    }
    setIsSaving(true);
    try {
      await onSave(editValue);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to save:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  return (
    <div className="p-4 bg-card rounded-lg border border-border group">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-secondary rounded transition-all"
            title={`Edit ${label}`}
          >
            <Edit2 className="h-3 w-3 text-muted-foreground" />
          </button>
        )}
      </div>
      {isEditing ? (
        <div className="space-y-2">
          {multiline ? (
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full px-2 py-1 bg-secondary border border-border rounded text-sm resize-none"
              rows={3}
              autoFocus
            />
          ) : (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full px-2 py-1 bg-secondary border border-border rounded text-sm"
              autoFocus
            />
          )}
          <div className="flex justify-end gap-2">
            <button
              onClick={handleCancel}
              className="px-2 py-1 text-xs hover:bg-secondary rounded transition-colors"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 flex items-center gap-1"
            >
              {isSaving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
              Save
            </button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-foreground leading-relaxed">{value || <span className="text-muted-foreground italic">Not set</span>}</p>
      )}
    </div>
  );
}

// World Settings Tab - displays world_context fields and media type
function WorldSettingsTab({
  worldData,
  projectPath,
  onSave
}: {
  worldData: WorldData | null;
  projectPath?: string;
  onSave?: () => void;
}) {
  const [visualStyle, setVisualStyle] = useState(worldData?.visual_style || 'live_action');
  const [isSavingStyle, setIsSavingStyle] = useState(false);
  const worldContext = worldData?.world_context;

  // Update local state when worldData changes
  useEffect(() => {
    if (worldData?.visual_style) {
      setVisualStyle(worldData.visual_style);
    }
  }, [worldData?.visual_style]);

  // World context field labels with icons
  const contextFields = [
    { key: 'setting', label: 'Setting', icon: '🌍' },
    { key: 'time_period', label: 'Time Period', icon: '📅' },
    { key: 'cultural_context', label: 'Cultural Context', icon: '🎭' },
    { key: 'social_structure', label: 'Social Structure', icon: '👥' },
    { key: 'technology_level', label: 'Technology Level', icon: '⚙️' },
    { key: 'clothing_norms', label: 'Clothing Norms', icon: '👔' },
    { key: 'architecture_style', label: 'Architecture', icon: '🏛️' },
    { key: 'color_palette', label: 'Color Palette', icon: '🎨' },
    { key: 'lighting_style', label: 'Lighting Style', icon: '💡' },
    { key: 'mood', label: 'Mood', icon: '✨' },
  ];

  const handleSaveContextField = async (fieldKey: string, newValue: string) => {
    if (!projectPath) return;
    try {
      await fetchAPI(`/api/projects/path-data/world/context/${fieldKey}?path=${encodeURIComponent(projectPath)}`, {
        method: 'PATCH',
        body: JSON.stringify({ value: newValue })
      });
      onSave?.();
    } catch (err) {
      console.error('Failed to save field:', err);
      throw err;
    }
  };

  const handleVisualStyleChange = async (newStyle: string) => {
    if (!projectPath || newStyle === visualStyle) return;
    setIsSavingStyle(true);
    try {
      await fetchAPI(`/api/projects/path-data/visual-style?path=${encodeURIComponent(projectPath)}`, {
        method: 'PUT',
        body: JSON.stringify({ visual_style: newStyle })
      });
      setVisualStyle(newStyle);
      onSave?.();
    } catch (err) {
      console.error('Failed to save visual style:', err);
    } finally {
      setIsSavingStyle(false);
    }
  };

  if (!worldContext || Object.keys(worldContext).length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <Globe className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="font-medium">No World Settings</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Run the World Builder pipeline to generate world context
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea.Root className="h-full">
      <ScrollArea.Viewport className="h-full w-full p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3">
            <Globe className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">World Settings</h1>
          </div>

          {/* Media Type & Visual Style Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {worldData?.genre && (
              <div className="p-4 bg-card rounded-lg border border-border">
                <span className="text-xs font-medium text-muted-foreground">Genre</span>
                <p className="text-foreground font-medium mt-1">{worldData.genre}</p>
              </div>
            )}

            {/* Visual Style Dropdown */}
            <div className="p-4 bg-card rounded-lg border border-border">
              <span className="text-xs font-medium text-muted-foreground">Visual Style</span>
              <div className="relative mt-1">
                <select
                  value={visualStyle}
                  onChange={(e) => handleVisualStyleChange(e.target.value)}
                  disabled={isSavingStyle}
                  className="w-full px-3 py-2 bg-secondary border border-border rounded-md text-sm font-medium appearance-none cursor-pointer disabled:opacity-50"
                >
                  {VISUAL_STYLES.map((style) => (
                    <option key={style.key} value={style.key}>
                      {style.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                {isSavingStyle && (
                  <Loader2 className="absolute right-8 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary" />
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {VISUAL_STYLES.find(s => s.key === visualStyle)?.description}
              </p>
            </div>

            {worldData?.media_type && (
              <div className="p-4 bg-card rounded-lg border border-border">
                <span className="text-xs font-medium text-muted-foreground">Media Type</span>
                <p className="text-foreground font-medium mt-1 capitalize">
                  {worldData.media_type.replace(/_/g, ' ')}
                </p>
              </div>
            )}
          </div>

          {/* World Context Fields - Editable */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-muted-foreground">World Context</h2>
            <p className="text-xs text-muted-foreground">Hover over any field and click the edit icon to modify.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {contextFields.map(({ key, label, icon }) => {
                const value = worldContext[key as keyof WorldContext] || '';
                return (
                  <EditableField
                    key={key}
                    label={label}
                    icon={icon}
                    value={value}
                    onSave={(newValue) => handleSaveContextField(key, newValue)}
                    multiline={true}
                  />
                );
              })}
            </div>
          </div>
        </div>
      </ScrollArea.Viewport>
      <ScrollArea.Scrollbar className="flex select-none touch-none p-0.5 bg-secondary w-2" orientation="vertical">
        <ScrollArea.Thumb className="flex-1 bg-muted-foreground rounded-full" />
      </ScrollArea.Scrollbar>
    </ScrollArea.Root>
  );
}


