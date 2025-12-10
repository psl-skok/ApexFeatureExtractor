import requests

BASE_URL = "http://127.0.0.1:8000"

def test_functions():
    try:
        res = requests.get(f"{BASE_URL}/functions")
        print("GET /functions:", res.status_code, res.json())
    except Exception as e:
        print("Error testing /functions:", e)

def test_dataset_preview(dataset_id):
    try:
        res = requests.get(f"{BASE_URL}/datasets/{dataset_id}")
        print(f"GET /datasets/{dataset_id}:", res.status_code, res.json())
    except Exception as e:
        print(f"Error testing /datasets/{dataset_id}:", e)

if __name__ == "__main__":
    test_functions()
    # Replace with a valid ID from your datasets
    test_dataset_preview("your_dataset_id_here")  # e.g., "abc123"
