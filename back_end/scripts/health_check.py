import requests
import json
import sys

def main():
    url = "http://127.0.0.1:8000/api/health/"
    print(f"Checking health at {url}...")
    try:
        res = requests.get(url, timeout=5)
        print(f"HTTP Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
