#!/usr/bin/env python3
"""
Test script to verify the compiler integration with FastAPI server.
This script tests the /compiler/run endpoint.
"""

import requests
import json
import pandas as pd
import sys
import os

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_compiler_integration():
    """Test the compiler endpoint with a sample dataset and path_request."""
    
    # Base URL for the FastAPI server (assuming it's running on localhost:8000)
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Compiler Integration with FastAPI Server")
    print("=" * 60)
    
    # Step 1: Upload a test dataset
    print("\n1️⃣ Uploading test dataset...")
    
    # Read the sample CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'Compiler', '10CallsCleaned.csv')
    if not os.path.exists(csv_path):
        print(f"❌ Sample CSV not found at {csv_path}")
        return False
    
    with open(csv_path, 'rb') as f:
        files = {'file': ('10CallsCleaned.csv', f, 'text/csv')}
        response = requests.post(f"{base_url}/datasets", files=files)
    
    if response.status_code != 200:
        print(f"❌ Failed to upload dataset: {response.text}")
        return False
    
    dataset_info = response.json()
    dataset_id = dataset_info['dataset_id']
    print(f"✅ Dataset uploaded successfully. ID: {dataset_id}")
    print(f"   Rows: {dataset_info['n_rows']}")
    
    # Step 2: Test the compiler endpoint
    print("\n2️⃣ Testing compiler endpoint...")
    
    # Full path_request from compiler.py
    path_request = [
        {
            "function": "binary_classification",
            "args": {
                "questions": [{
                    "context_prompt" : "Was a follow up scheduled on the call, be strict. Only say yes if you are 100 percent confident",
                    "input_data": "call_text",
                    "positive_label": "yes, follow up was scheduled",
                    "negative_label": "no, follow up was not scheduled",
                    "explanation_col": "follow_up_explanation",
                    "label_col": "follow_up_label"
                }],
                "max_workers": 2
            },
            "input_df_name": "starting_df",
            "output_df_name": "starting_df"
        },
        {
            "function": "open_classification",
            "args": {
                "context_prompt": "Score the explanation 1-5 on how solid/accurate they are",
                "response_col": "key_themes_response",
                "input_data": "follow_up_explanation",
                "max_workers": 2,
            },
            "input_df_name": "starting_df",
            "output_df_name": "starting_df"
        },
        {
            "function": "comparison",
            "args": {
                "grouping_column": "follow_up_label",
                "text_column": "key_themes_response",
                "context_prompt": (
                    "Compare calls where a follow-up *was* scheduled "
                    "to those where it *wasn’t*. What differentiates them?"
                ),
                "id_column": "call_id",
            },
            "input_df_name": "starting_df",
            "output_df_name": "comparison_results"
        },
    ]
    
    compiler_request = {
        "dataset_id": dataset_id,
        "path_request": path_request
    }
    
    print(f"   Sending compiler request with {len(path_request)} steps...")
    print("   Exact Input (Request JSON):\n" + json.dumps(compiler_request, indent=4))
    
    try:
        response = requests.post(
            f"{base_url}/compiler/run",
            json=compiler_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Compiler request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        print("   Exact Output (Response JSON):\n" + json.dumps(result, indent=4))
        
        if result['success']:
            print("✅ Compiler execution successful!")
            print(f"   State keys: {result['state_keys']}")
            print(f"   Execution log entries: {len(result['execution_log'])}")
            print(f"   Artifacts: {list(result['artifacts'].keys())}")
            
            # Show a sample of the results
            if 'starting_df_head' in result['artifacts']:
                sample_data = result['artifacts']['starting_df_head'][:3]  # First 3 rows
                print(f"\n   Sample results:")
                for i, row in enumerate(sample_data):
                    print(f"     Row {i+1}: {row.get('follow_up_label', 'N/A')} - {row.get('follow_up_explanation', 'N/A')[:50]}...")
            
            return True
        else:
            print(f"❌ Compiler execution failed: {result.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to FastAPI server. Make sure it's running on localhost:8000")
        print("   Start the server with: uvicorn server.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_local_df_integration():
    """Test the compiler endpoint with local_df toggle."""
    base_url = "http://localhost:8000"
    
    print("\n3️⃣ Testing local_df toggle...")
    
    # Full path_request from compiler.py
    path_request = [
        {
            "function": "binary_classification",
            "args": {
                "questions": [{
                    "context_prompt" : "Was a follow up scheduled on the call, be strict. Only say yes if you are 100 percent confident",
                    "input_data": "call_text",
                    "positive_label": "yes, follow up was scheduled",
                    "negative_label": "no, follow up was not scheduled",
                    "explanation_col": "follow_up_explanation",
                    "label_col": "follow_up_label"
                }],
                "max_workers": 2
            },
            "input_df_name": "starting_df",
            "output_df_name": "starting_df"
        },
        {
            "function": "open_classification",
            "args": {
                "context_prompt": "Score the explanation 1-5 on how solid/accurate they are",
                "response_col": "key_themes_response",
                "input_data": "follow_up_explanation",
                "max_workers": 2,
            },
            "input_df_name": "starting_df",
            "output_df_name": "starting_df"
        },
        {
            "function": "comparison",
            "args": {
                "grouping_column": "follow_up_label",
                "text_column": "key_themes_response",
                "context_prompt": (
                    "Compare calls where a follow-up *was* scheduled "
                    "to those where it *wasn’t*. What differentiates them?"
                ),
                "id_column": "call_id",
            },
            "input_df_name": "starting_df",
            "output_df_name": "comparison_results"
        },
    ]
    
    compiler_request = {
        "dataset_id": "local_df",
        "path_request": path_request,
        "local_csv_path": "LangChain_Orchestration/Compiler/10CallsCleaned.csv"  # Relative to workspace root
    }
    
    print(f"   Sending compiler request with local_df...")
    print("   Exact Input (Request JSON):\n" + json.dumps(compiler_request, indent=4))
    
    try:
        response = requests.post(
            f"{base_url}/compiler/run",
            json=compiler_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Local_df request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        print("   Exact Output (Response JSON):\n" + json.dumps(result, indent=4))
        
        if result['success']:
            print("✅ Local_df execution successful!")
            print(f"   State keys: {result['state_keys']}")
            return True
        else:
            print(f"❌ Local_df execution failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error in local_df test: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to verify server is running."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        return False

if __name__ == "__main__":
    print("🚀 Starting Compiler Integration Test")
    print("=" * 60)
    
    # Test 1: Check if server is running
    if not test_health_endpoint():
        print("\n💡 To start the server, run:")
        print("   cd LangChain_Orchestration")
        print("   uvicorn server.main:app --reload")
        sys.exit(1)
    
    # Test 2: Run the compiler integration test
    success = test_compiler_integration()
    
    # Test 3: Run the local_df test
    local_success = test_local_df_integration()
    success = success and local_success  # Overall success
    
    if success:
        print("\n🎉 All tests passed! Compiler integration is working correctly.")
    else:
        print("\n❌ Tests failed. Check the output above for details.")
        sys.exit(1)