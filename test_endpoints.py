import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_all_endpoints():
    # Test health
    print("Testing /health...")
    health_response = requests.get(f"{BASE_URL}/health")
    print(f"Health Status: {health_response.status_code}")
    print(json.dumps(health_response.json(), indent=2))
    
    # Test parse
    print("\nTesting /parse...")
    parse_data = {
        "cv_text": "Experienced Python developer with 5 years in web development.",
        "jd_text": "Looking for senior Python developer with FastAPI experience."
    }
    parse_response = requests.post(f"{BASE_URL}/parse", json=parse_data)
    print(f"Parse Status: {parse_response.status_code}")
    
    # Test skills
    print("\nTesting /skills...")
    skills_response = requests.post(f"{BASE_URL}/skills", json=parse_data)
    print(f"Skills Status: {skills_response.status_code}")
    
    # Test questions
    print("\nTesting /questions...")
    questions_data = {"jd_text": "Python developer role", "count": 3}
    questions_response = requests.post(f"{BASE_URL}/questions", json=questions_data)
    print(f"Questions Status: {questions_response.status_code}")
    print(json.dumps(questions_response.json(), indent=2))
    
    # Test transcribe
    print("\nTesting /transcribe...")
    transcribe_data = {
        "audio_data": "mock_audio_data",
        "session_id": "test_session_123"
    }
    transcribe_response = requests.post(f"{BASE_URL}/transcribe", json=transcribe_data)
    print(f"Transcribe Status: {transcribe_response.status_code}")
    
    # Test score
    print("\nTesting /score...")
    score_data = {
        "session_id": "test_session_123",
        "transcript": "This is a test transcript of an interview answer.",
        "jd_text": "Python developer role"
    }
    score_response = requests.post(f"{BASE_URL}/score", json=score_data)
    print(f"Score Status: {score_response.status_code}")
    print(json.dumps(score_response.json(), indent=2))
    
    # Test report
    print("\nTesting /report...")
    report_data = {"session_id": "test_session_123"}
    report_response = requests.post(f"{BASE_URL}/report", json=report_data)
    print(f"Report Status: {report_response.status_code}")

if __name__ == "__main__":
    test_all_endpoints()