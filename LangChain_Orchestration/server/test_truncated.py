import requests

def get_first_dataset_id(base_url="http://127.0.0.1:8000"):
    url = f"{base_url}/datasets"
    try:
        response = requests.get(url)
        response.raise_for_status()
        datasets = response.json()
        if datasets:
            return datasets[0]["id"]
        else:
            raise ValueError("No datasets available")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch datasets: {e}")

def test_truncated_endpoint(dataset_id, preview_rows=10, max_cell_chars=200, base_url="http://127.0.0.1:8000"):
    url = f"{base_url}/datasets/truncated/{dataset_id}"
    params = {
        "preview_rows": preview_rows,
        "max_cell_chars": max_cell_chars
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        print("Response JSON:")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        dataset_id = get_first_dataset_id()
        print(f"Testing with first dataset ID: {dataset_id}")
        test_truncated_endpoint(dataset_id)
    except ValueError as ve:
        print(ve)
