#!/usr/bin/env python3
"""Test script to verify runpod_manager package imports work correctly"""

try:
    from runpod_manager import PodManager, PodConfig
    print("✅ Import successful - PodManager and PodConfig imported correctly")
    
    try:
        config = PodConfig("test-project")
        print("❌ Config creation should have failed without RUNPOD_API_KEY")
    except ValueError as e:
        if "RUNPOD_API_KEY not found" in str(e):
            print("✅ Config correctly requires RUNPOD_API_KEY")
        else:
            print(f"❌ Unexpected error: {e}")
    
    print("✅ Package structure and imports are working correctly")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
