import requests
import json

BASE_URL = "http://localhost:8000"

def test_senior_leadership_trace():
    """Test the senior leadership conversation trace."""
    print("Testing Senior Leadership Conversation Trace")
    print("=" * 60)
    
    conversation = []
    
    # Turn 1: User asks for senior leadership solution
    user_msg_1 = "We need a solution for senior leadership."
    conversation.append({"role": "user", "content": user_msg_1})
    
    response_1 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 1: Initial Request ---")
    print(f"Status: {response_1.status_code}")
    print(f"Reply: {response_1.json()['reply'][:200]}...")
    print(f"Recommendations: {len(response_1.json()['recommendations'])}")
    print(f"End of conversation: {response_1.json()['end_of_conversation']}")
    
    # Expected: Clarification question about purpose (selection vs development)
    # Should NOT return recommendations yet
    
    # Turn 2: User provides context about CXOs and directors
    user_msg_2 = "The pool consists of CXOs, director-level postions; people with more than 15 years of experience."
    conversation.append({"role": "assistant", "content": response_1.json()['reply']})
    conversation.append({"role": "user", "content": user_msg_2})
    
    response_2 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 2: Context provided ---")
    print(f"Status: {response_2.status_code}")
    print(f"Reply: {response_2.json()['reply'][:200]}...")
    print(f"Recommendations: {len(response_2.json()['recommendations'])}")
    print(f"End of conversation: {response_2.json()['end_of_conversation']}")
    
    # Expected: Should still ask about purpose since user didn't answer
    
    # Turn 3: User clarifies it's for selection with leadership benchmark
    user_msg_3 = "Selection — comparing candidates against a leadership benchmark."
    conversation.append({"role": "assistant", "content": response_2.json()['reply']})
    conversation.append({"role": "user", "content": user_msg_3})
    
    response_3 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 3: Selection with leadership benchmark ---")
    print(f"Status: {response_3.status_code}")
    print(f"Reply: {response_3.json()['reply'][:300]}...")
    print(f"Recommendations: {len(response_3.json()['recommendations'])}")
    if response_3.json()['recommendations']:
        for rec in response_3.json()['recommendations']:
            print(f"  - {rec['name']}")
    print(f"End of conversation: {response_3.json()['end_of_conversation']}")
    
    # Expected: OPQ32r, OPQ Universal Competency Report, OPQ Leadership Report
    
    # Turn 4: User confirms
    user_msg_4 = "Perfect, that's what we need."
    conversation.append({"role": "assistant", "content": response_3.json()['reply']})
    conversation.append({"role": "user", "content": user_msg_4})
    
    response_4 = requests.post(f"{BASE_URL}/chat", json={"messages": conversation})
    print(f"\n--- Turn 4: Confirmation ---")
    print(f"Status: {response_4.status_code}")
    print(f"Reply: {response_4.json()['reply'][:300]}...")
    print(f"Recommendations: {len(response_4.json()['recommendations'])}")
    if response_4.json()['recommendations']:
        for rec in response_4.json()['recommendations']:
            print(f"  - {rec['name']}")
    print(f"End of conversation: {response_4.json()['end_of_conversation']}")
    
    # Expected: Same recommendations, end_of_conversation = True
    
    print("\n" + "=" * 60)
    print("Test completed")

if __name__ == "__main__":
    test_senior_leadership_trace()
