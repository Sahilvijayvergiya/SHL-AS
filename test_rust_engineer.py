import requests

BASE_URL = "http://localhost:8000"

def test_rust_engineer_trace():
    """Test the senior Rust engineer conversation trace."""
    print("Testing Senior Rust Engineer Conversation Trace")
    print("=" * 60)
    
    conversation = []
    
    # Turn 1: Initial request for Rust engineer
    user_msg_1 = "I'm hiring a senior Rust engineer for high-performance networking infrastructure. What assessments should I use?"
    conversation.append({"role": "user", "content": user_msg_1})
    
    response_1 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 1: Initial Request ---")
    print(f"Status: {response_1.status_code}")
    print(f"Reply: {response_1.json()['reply'][:200]}...")
    print(f"Recommendations: {len(response_1.json()['recommendations'])}")
    
    # Expected: Should mention Smart Interview Live Coding as closest fit for Rust
    
    # Turn 2: User confirms
    user_msg_2 = "That works. Build me a shortlist."
    conversation.append({"role": "assistant", "content": response_1.json()['reply']})
    conversation.append({"role": "user", "content": user_msg_2})
    
    response_2 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 2: Confirmation ---")
    print(f"Status: {response_2.status_code}")
    print(f"Reply: {response_2.json()['reply'][:200]}...")
    print(f"Recommendations: {len(response_2.json()['recommendations'])}")
    if response_2.json()['recommendations']:
        for rec in response_2.json()['recommendations']:
            print(f"  - {rec['name']}")
    
    print("\n" + "=" * 60)
    print("Test completed")

if __name__ == "__main__":
    test_rust_engineer_trace()
