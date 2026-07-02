import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"messages": [{"role": "user", "content": "Hello"}]}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
