from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
from .serializers import InterviewSessionSerializer, SkillMatchResultSerializer, QuestionSetSerializer, TranscriptSerializer, ScoreResultSerializer

from .utils import extract_text_from_pdf, fetch_content_from_url, validate_pdf_file
from .analysis import skill_analyzer

# views.py - Add these imports at the top
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Add this to your views.py
import subprocess
import tempfile
import time
# In views.py - replace analyze_speech function
import os
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# In views.py - update the analyze_speech function
@csrf_exempt
def analyze_speech(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        try:
            print("🎯 Audio analysis request received")
            
            audio_file = request.FILES['audio']
            print(f"📁 Audio file: {audio_file.name}, {audio_file.size} bytes")
            
            # Save to temporary file with correct extension
            file_extension = '.webm'  # Default to webm since that's what browsers record in
            if audio_file.name.endswith('.wav'):
                file_extension = '.wav'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                for chunk in audio_file.chunks():
                    tmp_file.write(chunk)
                temp_path = tmp_file.name
            
            print(f"📁 Saved to: {temp_path}")
            
            # Perform analysis
            from .speech_analysis import transcribe
            result = transcribe(temp_path)
            print(f"🎤 Transcription result: {result['transcript']}")
            print(f"📊 Metrics: {result['metrics']}")
            print(f"💡 Hints: {result['hints']}")
            
            # Calculate score
            score_data = calculate_interview_score(result)
            print(f"🏆 Score: {score_data}")
            
            # Clean up
            try:
                os.unlink(temp_path)
                print(f"🧹 Cleaned temp file: {temp_path}")
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'transcript': result['transcript'],
                'metrics': result['metrics'],
                'hints': result['hints'],
                'score': score_data
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'No audio file'
    })
def calculate_interview_score(result):
    """Simple scoring logic"""
    metrics = result.get('metrics', {})
    hints = result.get('hints', [])
    
    wpm = metrics.get('wpm', 0)
    filler_pct = metrics.get('filler_pct', 0)
    word_count = metrics.get('word_count', 0)
    
    # Content score based on length
    content_score = min(100, (word_count / 30) * 100)
    
    # Delivery score based on WPM and fillers
    wpm_score = 0
    if 120 <= wpm <= 160:
        wpm_score = 90
    elif 100 <= wpm <= 180:
        wpm_score = 70
    else:
        wpm_score = 50
    
    filler_score = max(0, 100 - (filler_pct * 10))
    
    delivery_score = (wpm_score + filler_score) / 2
    
    # Communication score based on hints
    positive_hints = len([h for h in hints if any(word in h.lower() for word in ['good', 'excellent', 'minimal'])])
    negative_hints = len([h for h in hints if any(word in h.lower() for word in ['too', 'slow', 'fast', 'many', 'longer'])])
    
    communication_score = max(20, 80 - (negative_hints * 10) + (positive_hints * 5))
    
    # Overall score
    overall_score = round((content_score + delivery_score + communication_score) / 3)
    
    return {
        'overall_score': overall_score,
        'content_score': round(content_score),
        'delivery_score': round(delivery_score),
        'communication_score': round(communication_score),
        'feature_contributions': {
            'positive': [h for h in hints if any(word in h.lower() for word in ['good', 'excellent', 'minimal'])],
            'negative': [h for h in hints if any(word in h.lower() for word in ['too', 'slow', 'fast', 'many', 'longer'])]
        }
    }
@api_view(['POST'])
def parse_cv_jd(request):
    cv_type = request.POST.get('cv_type', 'text')
    jd_type = request.POST.get('jd_type', 'text')
    
    cv_text = ""
    jd_text = ""
    
    # Process CV based on input type
    if cv_type == 'text':
        cv_text = request.POST.get('cv_text', '')
        if not cv_text.strip():
            return Response({"error": "Please provide CV text"}, status=status.HTTP_400_BAD_REQUEST)
            
    elif cv_type == 'pdf':
        cv_file = request.FILES.get('cv_file')
        if cv_file:
            if not validate_pdf_file(cv_file):
                return Response({"error": "Please upload a valid PDF file"}, status=status.HTTP_400_BAD_REQUEST)
            
            cv_text = extract_text_from_pdf(cv_file)
            if cv_text.startswith("Error extracting PDF"):
                return Response({"error": "Failed to process PDF file"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "No PDF file provided"}, status=status.HTTP_400_BAD_REQUEST)
            
    elif cv_type == 'url':
        cv_url = request.POST.get('cv_url', '')
        if cv_url:
            cv_text = fetch_content_from_url(cv_url)
            if cv_text.startswith("Error fetching URL"):
                return Response({"error": "Failed to fetch content from URL"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "No CV URL provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Process JD based on input type
    if jd_type == 'text':
        jd_text = request.POST.get('jd_text', '')
        if not jd_text.strip():
            return Response({"error": "Please provide Job Description text"}, status=status.HTTP_400_BAD_REQUEST)
            
    elif jd_type == 'url':
        jd_url = request.POST.get('jd_url', '')
        if jd_url:
            jd_text = fetch_content_from_url(jd_url)
            if jd_text.startswith("Error fetching URL"):
                return Response({"error": "Failed to fetch job description from URL"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "No Job URL provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate content
    if len(cv_text.strip()) < 10 or len(jd_text.strip()) < 10:
        return Response({"error": "Provided content is too short"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create session
    session_data = {
        'cv_text': cv_text,
        'jd_text': jd_text
    }
    
    serializer = InterviewSessionSerializer(data=session_data)
    if serializer.is_valid():
        session = serializer.save()
        return Response({
            "session_id": session.id, 
            "message": "CV and JD parsed successfully.",
            "cv_type": cv_type,
            "jd_type": jd_type,
            "cv_length": len(cv_text),
            "jd_length": len(jd_text)
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# MODIFIED get_skills VIEW:
@api_view(['GET'])
def get_skills(request, session_id):
    try:
        session = InterviewSession.objects.get(pk=session_id)
        print(f"=== ANALYZING SESSION {session_id} ===")
        print(f"CV Text Length: {len(session.cv_text)}")
        print(f"JD Text Length: {len(session.jd_text)}")
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        print("Starting skill analysis...")
        analysis_result = skill_analyzer.analyze_skill_gap(
            session.cv_text, 
            session.jd_text
        )
        
        print(f"Analysis completed: {len(analysis_result.get('matched_skills', []))} matched, {len(analysis_result.get('missing_skills', []))} missing")
        print(f"Match percentage: {analysis_result.get('match_percentage', 0)}%")
        
        return Response(analysis_result)
        
    except Exception as e:
        print(f"ANALYSIS ERROR: {str(e)}")
        return get_skills_fallback(session)

def get_skills_fallback(session):
    stub_skill_data = {
        "matched_skills": [
            {"skill": "Python", "evidence_cv": "Built a Django web application.", "evidence_jd": "Looking for a Python developer."},
            {"skill": "Project Management", "evidence_cv": "Led a team of 5.", "evidence_jd": "Must lead projects."}
        ],
        "missing_skills": [
            {"skill": "Docker", "evidence_jd": "Experience with containerization is a plus."}
        ],
        "evidence": [
            {"skill": "Python", "cv_sentence": "Built Django web applications for 3 years", "jd_sentence": "Python developer with framework experience required", "status": "matched"},
            {"skill": "Docker", "cv_sentence": "No containerization experience mentioned", "jd_sentence": "Docker and containerization experience required", "status": "missing"}
        ],
        "cv_skill_count": 2,
        "jd_skill_count": 3,
        "match_percentage": 66.7
    }
    
    skill_result, created = SkillMatchResult.objects.get_or_create(
        session=session, 
        defaults=stub_skill_data
    )
    
    response_data = {
        'matched_skills': stub_skill_data['matched_skills'],
        'missing_skills': stub_skill_data['missing_skills'],
        'evidence': stub_skill_data['evidence'],
        'cv_skill_count': 2,
        'jd_skill_count': 3,
        'match_percentage': 66.7
    }
    
    return Response(response_data)
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