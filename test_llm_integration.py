import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing LLM Integration")
print("=" * 60)

# Test 1: Simple greeting
print("\n--- Test 1: Simple greeting ---")
response = requests.post(f"{BASE_URL}/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test 2: Specific request
print("\n--- Test 2: Java developer request ---")
response = requests.post(f"{BASE_URL}/chat", json={"messages": [{"role": "user", "content": "I need assessments for a mid-level Java developer"}]})
print(f"Status: {response.status_code}")
data = response.json()
print(f"Reply: {data['reply']}")
print(f"Recommendations: {len(data['recommendations'])}")
if data['recommendations']:
    for rec in data['recommendations'][:3]:
        print(f"  - {rec['name']} ({rec['test_type']})")

# Test 3: Multi-turn conversation
print("\n--- Test 3: Multi-turn conversation ---")
messages = [
    {"role": "user", "content": "I need assessments for a senior leadership role"}
]
response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
print(f"Turn 1: {response.json()['reply']}")

messages.append({"role": "assistant", "content": response.json()['reply']})
messages.append({"role": "user", "content": "This is for hiring new executives"})
response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
print(f"Turn 2: {response.json()['reply']}")
print(f"Recommendations: {len(response.json()['recommendations'])}")

print("\n" + "=" * 60)
print("LLM Integration Test Complete")
