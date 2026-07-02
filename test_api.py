import requests
import json


def test_health():
    """Test health endpoint."""
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_vague_query():
    """Test vague query - should ask for clarification."""
    payload = {
        "messages": [
            {"role": "user", "content": "I need an assessment"}
        ]
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    print(f"\nVague query test: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_java_developer():
    """Test specific query - should recommend."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hiring a Java developer"}
        ]
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    print(f"\nJava developer test: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_comparison():
    """Test comparison query."""
    payload = {
        "messages": [
            {"role": "user", "content": "What is the difference between Verify - G+ and Verify - Numerical Ability?"}
        ]
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    print(f"\nComparison test: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_refinement():
    """Test refinement conversation."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hiring a developer"},
            {"role": "assistant", "content": "To help me find the right assessments, could you specify the seniority level of the role (e.g., entry-level, mid-level, senior, executive)?"},
            {"role": "user", "content": "Mid-level, actually add personality tests too"}
        ]
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    print(f"\nRefinement test: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_off_topic():
    """Test off-topic query - should refuse."""
    payload = {
        "messages": [
            {"role": "user", "content": "What salary should I offer a Java developer?"}
        ]
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    print(f"\nOff-topic test: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


if __name__ == "__main__":
    print("Testing SHL Assessment Agent API\n")
    print("=" * 50)
    
    tests = [
        test_health,
        test_vague_query,
        test_java_developer,
        test_comparison,
        test_refinement,
        test_off_topic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Error in {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {sum(results)}/{len(results)}")
