import requests
import json

def test_graduate_management_trainee_trace():
    """Test the graduate management trainee conversation trace."""
    base_url = "http://localhost:8000"
    
    print("Testing Graduate Management Trainee Conversation Trace")
    print("=" * 60)
    
    # Turn 1: Initial request for full battery
    print("\n--- Turn 1: Initial Request ---")
    payload = {
        "messages": [
            {"role": "user", "content": "We run a graduate management trainee scheme. We need a full battery — cognitive, personality, and situational judgement. All recent graduates."}
        ]
    }
    response = requests.post(f"{base_url}/chat", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Reply: {result['reply']}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    print(f"End of conversation: {result['end_of_conversation']}")
    
    # Turn 2: Request to remove OPQ32r and replace with shorter
    print("\n--- Turn 2: Remove OPQ32r and replace with shorter ---")
    payload = {
        "messages": [
            {"role": "user", "content": "We run a graduate management trainee scheme. We need a full battery — cognitive, personality, and situational judgement. All recent graduates."},
            {"role": "assistant", "content": result['reply']},
            {"role": "user", "content": "But can you remove the OPQ32r and replace it with something shorter? Candidates complain it takes too long."}
        ]
    }
    response = requests.post(f"{base_url}/chat", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Reply: {result['reply']}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    print(f"End of conversation: {result['end_of_conversation']}")
    
    # Turn 3: User drops OPQ and finalizes
    print("\n--- Turn 3: Drop OPQ and finalize ---")
    payload = {
        "messages": [
            {"role": "user", "content": "We run a graduate management trainee scheme. We need a full battery — cognitive, personality, and situational judgement. All recent graduates."},
            {"role": "assistant", "content": "For a graduate management trainee battery covering all three dimensions..."},
            {"role": "user", "content": "But can you remove the OPQ32r and replace it with something shorter? Candidates complain it takes too long."},
            {"role": "assistant", "content": "OPQ32r is the most relevant solution for your need. As such, there is no shorter alternative to be used as its replacement."},
            {"role": "user", "content": "Drop the OPQ. Final list: Verify G+ and Graduate Scenarios."}
        ]
    }
    response = requests.post(f"{base_url}/chat", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Reply: {result['reply']}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    if result.get('recommendations'):
        for rec in result['recommendations']:
            print(f"  - {rec['name']} ({rec['test_type']})")
    print(f"End of conversation: {result['end_of_conversation']}")
    
    # Verify the final recommendations match expected
    expected_names = {"SHL Verify Interactive G+", "Graduate Scenarios"}
    actual_names = {rec['name'] for rec in result.get('recommendations', [])}
    
    print("\n--- Verification ---")
    if expected_names == actual_names:
        print("✓ Final recommendations match expected")
    else:
        print(f"✗ Expected: {expected_names}")
        print(f"✗ Actual: {actual_names}")
    
    if result['end_of_conversation']:
        print("✓ Conversation ended correctly")
    else:
        print("✗ Conversation should have ended")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_graduate_management_trainee_trace()
