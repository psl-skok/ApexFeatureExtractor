import requests
import time
import sys
import json
import os
import pandas as pd

BASE_URL = 'http://127.0.0.1:8000' 

def upload_dataset(csv_path):
    print(f"Uploading dataset from {csv_path}...")
    with open(csv_path, 'rb') as f:
        response = requests.post(f"{BASE_URL}/datasets", files={'file': (csv_path.split('/')[-1], f, 'text/csv')})
    if response.status_code != 200:
        raise ValueError(f"Upload failed: {response.text}")
    data = response.json()
    if not data.get('success'):
        raise ValueError(f"Upload failed: {data}")
    return data['dataset_id']

def run_compiler(dataset_id):
    print(f"Triggering compiler run for dataset {dataset_id}...")
    # Sample path_request - customize to your actual functions/args
    path_request = [
        {
            "function": "binary_classification",
            "args": {
                "questions": [{
                "context_prompt": "Was a follow up scheduled on the call, be strict. Only say yes if you are 100 percent confident",
                "input_data": "call_text",
                "positive_label": "yes, follow up was scheduled",
                "negative_label": "no, follow up was not scheduled",
                "explanation_col": "follow_up_explanation",
                "label_col": "follow_up_label"}],
                "max_workers": 4,
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
                "max_workers": 4,
            },
            "input_df_name": "starting_df",
            "output_df_name": "starting_df"
        },
        # {
        #     "function": "unique_value_splitter",
        #     "args": {"splitter_column": "follow_up_label"},
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },
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
    payload = {"dataset_id": dataset_id, "path_request": path_request}
    response = requests.post(f"{BASE_URL}/compiler/run", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response Text: {response.text}")
    if response.status_code != 200:
        raise ValueError(f"Compiler run failed: {response.text}")
    return response.json()['analysis_id']

def poll_analysis_status(analysis_id, max_attempts=60, sleep_sec=5):
    print(f"Polling status for analysis {analysis_id}...")
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/analyses/{analysis_id}")
        if response.status_code != 200:
            print(f"Error checking status: {response.text}")
            time.sleep(sleep_sec)
            continue
        data = response.json()
        status = data['status']
        print(f"Attempt {attempt+1}: Status = {status}")
        if status in ['completed', 'failed']:
            return data  
        time.sleep(sleep_sec)
    raise TimeoutError("Polling timed out")

if __name__ == "__main__":
    # Default CSV or from command line: python test_api.py path/to/csv
    csv_path = sys.argv[1] if len(sys.argv) > 1 else r'Data\Post-Clean Data\10CallsCleaned.csv'
    try:
        dataset_id = upload_dataset(csv_path)
        print(f"Dataset uploaded: {dataset_id}")
        
        analysis_id = run_compiler(dataset_id)
        print(f"Analysis started: {analysis_id}")
        
        final_analysis = poll_analysis_status(analysis_id)
        if final_analysis['status'] == 'completed':
            artifacts = final_analysis['artifacts']
            if artifacts:
                for key in artifacts:
                    response = requests.get(f"{BASE_URL}/analyses/{analysis_id}/artifacts/{key}", stream=True)
                    if response.status_code == 200:
                        temp_file = f"temp_{key}.csv"
                        with open(temp_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        df = pd.read_csv(temp_file)
                        print(f"Artifact Data for {key} (head):")
                        print(df.head())
                        os.remove(temp_file)
                    else:
                        print(f"Failed to fetch artifact {key}: {response.text}")
        print("Final Analysis:")
        print(json.dumps(final_analysis, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
