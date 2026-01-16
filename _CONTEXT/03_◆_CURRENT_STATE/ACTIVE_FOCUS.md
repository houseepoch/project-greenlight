# Active Focus

> **What we're working on RIGHT NOW.**

---

## CURRENT TASK

```
ID: READY-002
Title: Director Pipeline + Frontend Fixes Complete
Priority: 🟢 P3
Status: ◉ COMPLETE
```

### Description
```
Director pipeline now reads confirmed_outline.json (beats array)
and generates visual frames directly - NO intermediate script step.

Each beat → 1 scene → 2-5 frames with cinematic prompts
Frame prompts ARE the storytelling (photograph-style visuals)
```

### What's Complete
```
✅ Director pipeline accepts llm_model parameter
✅ API stages updated: Load Outline → Load World → Generate Frames → Save
✅ Outline modal "Use This" button for one-click variant selection
✅ 422 errors fixed (Pydantic request body models)
✅ Director modal 404 fixed (removed /api/director/.../script endpoint)
✅ Full beat-to-frames pipeline operational
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
📍 greenlight/pipelines/__init__.py - Added exports
📍 greenlight/pipelines/director.py - Rewritten
📍 greenlight/pipelines/references.py - Simplified
📍 greenlight/pipelines/storyboard.py - Updated
📍 greenlight/api/pipelines.py - Added 10+ endpoints
📍 tests/test_api_endpoints.py - Created
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
TRACE: ◆📍READY-001
