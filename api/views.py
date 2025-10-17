from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
from .serializers import InterviewSessionSerializer, SkillMatchResultSerializer, QuestionSetSerializer, TranscriptSerializer, ScoreResultSerializer

@api_view(['POST'])
def parse_cv_jd(request):
    """Stub endpoint for /parse. Creates a new InterviewSession."""
    serializer = InterviewSessionSerializer(data=request.data)
    if serializer.is_valid():
        session = serializer.save()
        return Response({"session_id": session.id, "message": "CV and JD parsed successfully."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_skills(request, session_id):
    """Stub endpoint for /skills. Returns skill matches and gaps."""
    try:
        session = InterviewSession.objects.get(pk=session_id)
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    # UPDATED: Added evidence section
    stub_skill_data = {
        "matched_skills": [
            {
                "skill": "Python", 
                "evidence_cv": "Built a Django web application.", 
                "evidence_jd": "Looking for a Python developer."
            },
            {
                "skill": "Project Management", 
                "evidence_cv": "Led a team of 5.", 
                "evidence_jd": "Must lead projects."
            }
        ],
        "missing_skills": [
            {
                "skill": "Docker", 
                "evidence_jd": "Experience with containerization is a plus."
            }
        ],
        # ADD THIS EVIDENCE SECTION:
        "evidence": [
            {
                "skill": "Python",
                "cv_sentence": "Built Django web applications for 3 years",
                "jd_sentence": "Python developer with framework experience required"
            },
            {
                "skill": "Project Management", 
                "cv_sentence": "Led a team of 5 developers on multiple projects",
                "jd_sentence": "Must have team leadership and project management skills"
            },
            {
                "skill": "Docker",
                "cv_sentence": "No containerization experience mentioned", 
                "jd_sentence": "Docker and containerization experience required"
            }
        ]
    }
    
    skill_result, created = SkillMatchResult.objects.get_or_create(
        session=session, 
        defaults=stub_skill_data
    )
    serializer = SkillMatchResultSerializer(skill_result)
    return Response(serializer.data)

@api_view(['GET'])
def get_questions(request, session_id):
    """Stub endpoint for /questions. Returns targeted questions."""
    try:
        session = InterviewSession.objects.get(pk=session_id)
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    # Ensure this structure matches what frontend expects
    stub_question_data = {
        "questions": [
            {
                "question": "Tell me about a time you used Python to solve a complex problem.",
                "rationale": "Your CV mentions Python and the JD requires it."
            },
            {
                "question": "Describe your experience with project management.",
                "rationale": "Your CV indicates leadership, a key skill for this role."
            },
            {
                "question": "How do you handle tight deadlines in projects?",
                "rationale": "This tests your time management skills mentioned in the JD."
            },
            {
                "question": "What experience do you have with cloud technologies?",
                "rationale": "The JD mentions AWS experience as a plus."
            }
        ]
    }
    
    # Return directly without database operations for now
    return Response(stub_question_data)

@api_view(['POST'])
def transcribe_audio(request):
    """Stub endpoint for /transcribe. For now, just accepts text and returns metrics."""
    user_speech_text = request.data.get('text', "")

    # STUB ANALYSIS - Replace with real ASR/NLP logic later
    word_count = len(user_speech_text.split())
    # Assuming a 30-second answer for this stub
    wpm = (word_count / 0.5) if user_speech_text else 0
    filler_count = user_speech_text.lower().count('uh') + user_speech_text.lower().count('um')

    stub_transcript_data = {
        "text": user_speech_text,
        "wpm": wpm,
        "filler_words": filler_count,
        "hints": ["Try to use more metrics.", "Good structure, but slow down a bit."] if wpm > 170 else ["Good pacing!", "Consider adding specific examples."]
    }
    
    return Response(stub_transcript_data)

@api_view(['POST'])
def calculate_score(request):
    """Stub endpoint for /score. Returns explainable scores."""
    session_id = request.data.get('session_id')
    transcript_text = request.data.get('transcript_text', "")

    # STUB SCORING LOGIC - Replace with Tessnim's XAI model later
    stub_score_data = {
        "content_score": 38,
        "delivery_score": 28,
        "communication_score": 18,
        "overall_score": 84,
        "feature_contributions": {
            "positive": ["Used the STAR method", "Provided a specific metric (30%)", "Good eye contact"],
            "negative": ["Pace was too fast (180 WPM)", "Used 5 filler words", "Could use more technical details"]
        },
        "evidence_quotes": [
            {"quote": "I improved efficiency by 30%", "feature": "metric", "impact": "+5 points"},
            {"quote": "um... uh...", "feature": "filler_words", "impact": "-2 points"},
            {"quote": "Then I implemented the solution", "feature": "STAR method", "impact": "+3 points"}
        ]
    }
    
    if session_id:
        try:
            session = InterviewSession.objects.get(pk=session_id)
            score_result = ScoreResult.objects.create(session=session, **stub_score_data)
            serializer = ScoreResultSerializer(score_result)
            return Response(serializer.data)
        except InterviewSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # If no session, just return the stub data
    return Response(stub_score_data)

@api_view(['GET'])
def generate_report(request, session_id):
    """Stub endpoint for /report. Triggers PDF generation and returns a URL."""
    # This is a placeholder. WP3 will implement the real PDF generation.
    mock_pdf_url = f"http://127.0.0.1:8000/api/report/{session_id}/download.pdf"
    return Response({"pdf_url": mock_pdf_url})

# A simple view to serve the mock PDF for testing
from django.http import FileResponse
import os

def serve_mock_pdf(request, session_id):
    """Serve a mock PDF for testing purposes."""
    # For now, we'll just return a JSON response since we don't have a real PDF
    return Response({
        "message": "PDF report would be generated here",
        "session_id": session_id,
        "status": "mock_response"
    })

def test_page(request):
    """Simple page to test all API endpoints"""
    return render(request, 'test.html')



# Add these new views for WP2 pages
def upload_page(request):
    """Render the upload page"""
    return render(request, 'upload.html')

def skill_gap_page(request, session_id):
    """Render the skill gap page"""
    return render(request, 'skill_gap.html', {'session_id': session_id})

def practice_page(request, session_id):
    """Render the practice page"""
    return render(request, 'practice.html', {'session_id': session_id})

def results_page(request, session_id):
    """Render the results page"""
    return render(request, 'results.html', {'session_id': session_id})