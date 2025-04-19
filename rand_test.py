import os
import uuid
import requests
import psutil
import time
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://127.0.0.1:8000/generate"
BUCKET_NAME = "sqipstoreage"  # <-- replace with actual bucket
OBJECT_KEY = "patents/test_patent.pdf"  # <-- S3 path to the file
NUM_REQUESTS = 1  # Simulate 1+ concurrent users

def monitor_memory(label=""):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"📦 {label} - Memory usage: {mem_mb:.2f} MB")
    return mem_mb

# def send_request(i):
#     try:
#         data = {
#             "bucket_name": BUCKET_NAME,
#             "object_key": OBJECT_KEY,
#             "document_type": "elevator pitch",
#             "user_query": "What is this document about?",
#             "additional_info": f"Simulated S3 request #{i}"
#         }
#         response = requests.post(API_URL, data=data)
#         if response.status_code == 200:
#             print(f"[✓] Session {i} completed. Output: {response.json()['content']}")
#         else:
#             print(f"[✗] Session {i} failed: {response.text}")
#     except Exception as e:
#         print(f"[✗] Exception in session {i}: {e}")

def send_request(i):
    try:
        data = {
            "bucket_name": BUCKET_NAME,
            "object_key": OBJECT_KEY,
            "document_type": "target firms",
            "user_query": "What is this document about?",
            "additional_info": "I want to know more about the applications of this patent."
        }
        response = requests.post(API_URL, data=data)

        # print(f"\n🧾 Raw Response [{response.status_code}]: {response.text}")

        if response.status_code == 200:
            json_data = response.json()
            if "messages" in json_data and "content" in json_data["messages"]:
                print(f"[✓] Session {i} completed.")
                print(f"🧠 Output: {json_data['messages']['content']}")
                # print(f"🧾 Model: {json_data['messages'].get('response_metadata', {}).get('model', 'Unknown')}")
                # print(f"⏱️  Duration: {json_data['messages'].get('response_metadata', {}).get('total_duration', 'N/A')} ns")
            else:
                print(f"[✗] Session {i} succeeded but missing 'content' in 'messages'")
        else:
            print(f"[✗] Session {i} failed: {response.text}")
    except Exception as e:
        print(f"[✗] Exception in session {i}: {e}")



def run_memory_test():
    print("🚀 Starting S3-based memory test")
    monitor_memory("Before test")

    with ThreadPoolExecutor(max_workers=NUM_REQUESTS) as executor:
        for i in range(NUM_REQUESTS):
            executor.submit(send_request, i)

    time.sleep(3)
    monitor_memory("After test")

if __name__ == "__main__":
    run_memory_test()
