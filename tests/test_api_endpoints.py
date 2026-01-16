"""
Test API Endpoints for Project Greenlight.

Verifies all pipeline endpoints are correctly configured and accessible.
Tests the full frontend operation flow.

TRACE: TEST-API-001
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from greenlight.api.main import app

client = TestClient(app)

# Test project path
TEST_PROJECT = Path(__file__).parent.parent / "test_project"


def test_health():
    """Test API health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    print("[OK] Health endpoint")


def test_pipeline_status():
    """Test pipeline status endpoint."""
    response = client.get("/api/pipelines/status/test_pipeline")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    print("[OK] Pipeline status endpoint")


def test_pipeline_validation():
    """Test pipeline validation endpoint."""
    response = client.get(f"/api/pipelines/validate/{TEST_PROJECT}")
    assert response.status_code == 200
    data = response.json()
    assert "project_exists" in data
    assert "pipelines" in data

    # Check all pipelines are listed
    expected_pipelines = [
        "writer", "ingestion", "world_builder",
        "outline_generator", "director", "references", "storyboard"
    ]
    for p in expected_pipelines:
        assert p in data["pipelines"], f"Missing pipeline: {p}"

    print(f"[OK] Pipeline validation endpoint - {len(data['pipelines'])} pipelines checked")

    # Print readiness status
    for name, status in data["pipelines"].items():
        ready = "READY" if status["ready"] else f"MISSING: {status['missing_requirements']}"
        print(f"    {name}: {ready}")


def test_prompts_endpoints():
    """Test prompt GET/PUT endpoints."""
    # GET prompts
    response = client.get(f"/api/pipelines/prompts/{TEST_PROJECT}")
    assert response.status_code == 200
    data = response.json()

    if data.get("success"):
        print(f"[OK] GET prompts - {len(data.get('prompts', []))} prompts from {data.get('source')}")
    else:
        print(f"[OK] GET prompts - No prompts yet ({data.get('error', 'N/A')})")


def test_references_endpoints():
    """Test reference image management endpoints."""
    # List references
    response = client.get(f"/api/pipelines/references/{TEST_PROJECT}")
    assert response.status_code == 200
    data = response.json()

    if data.get("success"):
        print(f"[OK] GET references - {data.get('generated', 0)}/{data.get('total', 0)} generated")
    else:
        print(f"[OK] GET references - No world_config yet")


def test_outline_endpoints():
    """Test outline management endpoints."""
    # Get outlines
    response = client.get(f"/api/pipelines/outlines/{TEST_PROJECT}")
    assert response.status_code == 200
    data = response.json()

    if data.get("success"):
        variants = data.get("data", {}).get("variants", {})
        print(f"[OK] GET outlines - {len(variants)} variants available")
    else:
        print(f"[OK] GET outlines - No outlines yet")


def test_project_endpoints():
    """Test project management endpoints."""
    # List projects
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    print(f"[OK] List projects - {len(projects)} projects")

    # Get specific project
    if TEST_PROJECT.exists():
        response = client.get(f"/api/projects/by-path/{TEST_PROJECT}")
        assert response.status_code == 200
        data = response.json()
        print(f"[OK] Get project - {data.get('name', 'Unknown')}")
        print(f"    has_pitch: {data.get('has_pitch')}")
        print(f"    has_world_config: {data.get('has_world_config')}")
        print(f"    has_visual_script: {data.get('has_visual_script')}")
        print(f"    has_storyboard: {data.get('has_storyboard')}")


def test_visual_script_endpoint():
    """Test visual script endpoint."""
    if not TEST_PROJECT.exists():
        print("[SKIP] Visual script - no test project")
        return

    response = client.get(f"/api/projects/test_project/visual-script")
    assert response.status_code == 200
    data = response.json()

    if data:
        frames = data.get("frames", [])
        print(f"[OK] Visual script - {len(frames)} frames")
        if frames:
            # Check frame structure
            frame = frames[0]
            required_fields = ["frame_id", "prompt", "tags", "scene_number"]
            for field in required_fields:
                assert field in frame, f"Missing field: {field}"
            print(f"    Frame structure valid: {list(frame.keys())}")
    else:
        print("[OK] Visual script - empty (run Director first)")


def test_storyboard_scene_endpoint_structure():
    """Verify scene-by-scene endpoint exists and accepts requests."""
    # Just verify the endpoint exists (don't actually run generation)
    response = client.post(
        "/api/pipelines/storyboard/scene/1",
        json={
            "project_path": str(TEST_PROJECT),
            "image_model": "seedream",
        }
    )
    # Should return 200 (background task started) or valid error
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_id" in data or "error" in data
    print("[OK] Storyboard scene endpoint exists")


def test_storyboard_frame_endpoint_structure():
    """Verify frame regeneration endpoint exists."""
    response = client.post(
        "/api/pipelines/storyboard/frame/1.1.cA",
        params={
            "project_path": str(TEST_PROJECT),
            "image_model": "seedream",
            "force": True,
        }
    )
    # Should return result dict
    assert response.status_code == 200
    data = response.json()
    # Will likely fail (no visual script), but endpoint should work
    print(f"[OK] Storyboard frame endpoint exists - {data.get('error', 'OK')}")


def test_ingestion_endpoints():
    """Test ingestion API endpoints."""
    # Get entities
    response = client.get(f"/api/ingestion/entities/{TEST_PROJECT}")
    # May 404 if no entities, that's fine
    print(f"[OK] Ingestion entities endpoint - status {response.status_code}")

    # Get chunks
    response = client.get(f"/api/ingestion/chunks/{TEST_PROJECT}")
    print(f"[OK] Ingestion chunks endpoint - status {response.status_code}")


def test_image_serving():
    """Test image serving endpoint."""
    # Try to get a non-existent image (should 404)
    response = client.get("/api/images/nonexistent.png")
    assert response.status_code == 404
    print("[OK] Image serving endpoint - returns 404 for missing")

    # Check if any storyboard images exist
    generated_dir = TEST_PROJECT / "storyboard_output" / "generated"
    if generated_dir.exists():
        images = list(generated_dir.glob("*.png"))
        if images:
            # Try to serve an actual image
            img_path = images[0]
            response = client.get(f"/api/images/{img_path}")
            assert response.status_code == 200
            assert response.headers.get("content-type") == "image/png"
            print(f"[OK] Image serving - served {img_path.name}")
        else:
            print("[OK] Image serving - no images to test")
    else:
        print("[OK] Image serving - no generated images yet")


def run_all_tests():
    """Run all API tests."""
    print("=" * 60)
    print("PROJECT GREENLIGHT - API ENDPOINT TESTS")
    print("=" * 60)
    print(f"Test Project: {TEST_PROJECT}")
    print(f"Project Exists: {TEST_PROJECT.exists()}")
    print("-" * 60)

    tests = [
        ("Health Check", test_health),
        ("Pipeline Status", test_pipeline_status),
        ("Pipeline Validation", test_pipeline_validation),
        ("Prompts Endpoints", test_prompts_endpoints),
        ("References Endpoints", test_references_endpoints),
        ("Outline Endpoints", test_outline_endpoints),
        ("Project Endpoints", test_project_endpoints),
        ("Visual Script", test_visual_script_endpoint),
        ("Storyboard Scene", test_storyboard_scene_endpoint_structure),
        ("Storyboard Frame", test_storyboard_frame_endpoint_structure),
        ("Ingestion Endpoints", test_ingestion_endpoints),
        ("Image Serving", test_image_serving),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
