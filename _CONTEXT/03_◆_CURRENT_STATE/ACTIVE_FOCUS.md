# Active Focus

> **What we're working on RIGHT NOW.**

---

## CURRENT TASK

```
ID: ICB-REMOVAL
Title: ICB Feature Removal + CORS Fixes
Priority: 🟢 P3
Status: ◉ COMPLETE
```

### Description
```
ICB (Intelligent Continuity Blending) feature was added to fix
continuity issues on existing storyboard frames. Results were bad
so the feature was removed entirely.

CORS fixes applied to enable image loading from frontend.
```

### What's Complete
```
✅ CORS fixes in main.py (expose_headers)
✅ CORS headers in images.py FileResponse
✅ CORS headers in pipelines.py SSE StreamingResponse
✅ ICB endpoints removed from pipelines.py
✅ greenlight/core/icb.py deleted
✅ ICB UI removed from storyboard-view.tsx
✅ All ICB state/interfaces/functions cleaned up
✅ Frontend builds successfully
✅ Backend compiles without errors
```

---

## AVAILABLE ACTIONS

### For User Testing
```
1. Run storyboard for specific scene:
   POST /api/pipelines/storyboard/scene/1

2. Regenerate single frame:
   POST /api/pipelines/storyboard/frame/1.1.cA

3. Edit prompts:
   GET /api/pipelines/prompts/{project_path}
   PUT /api/pipelines/prompts/{project_path}

4. Manage references:
   GET /api/pipelines/references/{project_path}
   POST /api/pipelines/references/{project_path}/regenerate/{tag}

5. Check pipeline readiness:
   GET /api/pipelines/validate/{project_path}
```

---

## CONTEXT

### Recent Files Modified
```
📍 greenlight/core/ingestion.py - Full context + 3-way consensus
📍 greenlight/pipelines/world_builder.py - Character-specific context
```

### Test Results
```
12/12 API tests PASSED
- Health Check ✓
- Pipeline Status ✓
- Pipeline Validation ✓
- Prompts Endpoints ✓
- References Endpoints ✓
- Outline Endpoints ✓
- Project Endpoints ✓
- Visual Script ✓
- Storyboard Scene ✓
- Storyboard Frame ✓
- Ingestion Endpoints ✓
- Image Serving ✓
```

---

## NEXT STEPS

```
◇ Frontend integration with new endpoints
◇ UI for prompt editing
◇ UI for reference image management
◇ Production testing with real API keys
```

---

DOCUMENT_STATUS: ◆_LIVE
TRACE: ◆📍INGEST-002
