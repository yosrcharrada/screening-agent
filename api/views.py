import os
from .speech_analysis import transcribe, highlight_fillers, check_ffmpeg
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .speech_analysis import transcribe, highlight_fillers
import tempfile
import os
import os
from pydub import AudioSegment

# Tell pydub where ffmpeg and ffprobe are
from pydub import AudioSegment
AudioSegment.converter = r"C:\Users\maram\OneDrive - ESPRIT\Documents\5DS1\ADSP\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\Users\maram\OneDrive - ESPRIT\Documents\5DS1\ADSP\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe"

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
from .serializers import InterviewSessionSerializer, SkillMatchResultSerializer, QuestionSetSerializer, TranscriptSerializer, ScoreResultSerializer
from .speech_analysis import transcribe, highlight_fillers

from .utils import extract_text_from_pdf, fetch_content_from_url, validate_pdf_file
from django.utils import timezone

# views.py - Add these imports at the top
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time
# Add this to your views.py
import tempfile
# In views.py - replace analyze_speech function

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession
from .serializers import InterviewSessionSerializer

from .utils import extract_text_from_pdf, fetch_content_from_url, validate_pdf_file
from .analysis import dynamic_skill_analyzer

from .file_processor import file_processor
from django.core.files.storage import FileSystemStorage
import tempfile
import os

from .file_processor import file_processor
import tempfile
import os

from .analysis import dynamic_skill_analyzer  # Import your existing analyzer

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession
from .file_processor import file_processor
from .analysis import dynamic_skill_analyzer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import tempfile
import os
from .speech_analysis import transcribe, highlight_fillers, check_ffmpeg
import os
import tempfile
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import spacy
nlp = spacy.load("en_core_web_lg")
import os
import tempfile
import traceback
import cv2
from deepface import DeepFace
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# ADD THIS LOGGER
logger = logging.getLogger(__name__)

@api_view(['POST'])
def parse_documents(request):
    """Handle all document types: files, text, and URLs"""
    try:
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        cv_url = request.data.get('cv_url', '')
        cv_type = request.data.get('cv_type', 'text')
        
        jd_file = request.FILES.get('jd_file')
        jd_text = request.data.get('jd_text', '')
        jd_url = request.data.get('jd_url', '')
        jd_type = request.data.get('jd_type', 'text')
        
        # Determine CV input
        cv_input = None
        if cv_type == 'file' and cv_file:
            cv_input = cv_file
        elif cv_type == 'text' and cv_text:
            cv_input = cv_text
        elif cv_type == 'url' and cv_url:
            cv_input = cv_url
        else:
            return Response({"error": "Please provide CV content"}, status=400)
        
        # Determine JD input
        jd_input = None
        if jd_type == 'file' and jd_file:
            jd_input = jd_file
        elif jd_type == 'text' and jd_text:
            jd_input = jd_text
        elif jd_type == 'url' and jd_url:
            jd_input = jd_url
        else:
            return Response({"error": "Please provide JD content"}, status=400)
        
        # Extract text from inputs using file processor
        cv_content, jd_content = file_processor.process_documents_for_analysis(cv_input, jd_input)
        
        # Use your existing skill analyzer
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(cv_content, jd_content)
        
        # Create session with analysis results
        session = InterviewSession.objects.create(
            cv_text=cv_content,
            jd_text=jd_content,
            analysis_data=analysis_result
        )
        
        return Response({
            "session_id": session.id,
            "message": "Documents processed and analyzed successfully",
            "analysis": analysis_result
        })
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")  # NOW THIS WILL WORK
        return Response({"error": f"Processing failed: {str(e)}"}, status=500)

@csrf_exempt
def analyze_speech(request):
    """Endpoint to upload audio and get transcription, metrics, and filler hints"""
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]
        ext = os.path.splitext(audio_file.name)[1].lower()

        temp_path = None
        wav_path = None
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                temp_path = tmp.name
                for chunk in audio_file.chunks():
                    tmp.write(chunk)

            print(f"📁 Uploaded: {audio_file.name} → Temp: {temp_path} ({os.path.getsize(temp_path)} bytes)")

            # Optional language parameter
            language = request.POST.get("language", None)

            # Convert to WAV for safe processing
            wav_path = convert_to_wav(temp_path)

            # Transcribe
            result = transcribe(wav_path, language=language)
            highlighted = highlight_fillers(result["transcript"], language=result["language"])

            # Ensure numeric metrics
            metrics = {
                "wpm": float(result["metrics"].get("wpm", 0)),
                "filler_pct": float(result["metrics"].get("filler_pct", 0)),
                "duration_s": float(result["metrics"].get("duration_s", 0)),
                "word_count": int(result["metrics"].get("word_count", 0))
            }

            print("🎯 Backend analysis result:", {"transcript": result["transcript"], "metrics": metrics})

            return JsonResponse({
                "success": True,
                "transcript": result["transcript"],
                "highlighted_fillers": highlighted,
                "metrics": metrics,
                "hints": result["hints"],
                "language": result["language"]
            })

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"success": False, "error": str(e)})

        finally:
            # Cleanup temporary files
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            if wav_path and os.path.exists(wav_path):
                os.unlink(wav_path)

    return JsonResponse({"success": False, "error": "No audio file uploaded"})


@api_view(['POST']) 
def analyze_direct(request):
    """Direct analysis using your existing skill analyzer"""
    try:
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        cv_url = request.data.get('cv_url', '')
        
        jd_file = request.FILES.get('jd_file')
        jd_text = request.data.get('jd_text', '')
        jd_url = request.data.get('jd_url', '')
        
        # Process CV (priority: file > text > url)
        cv_input = None
        if cv_file:
            cv_input = cv_file
        elif cv_text:
            cv_input = cv_text
        elif cv_url:
            cv_input = cv_url
        else:
            return Response({"error": "Please provide CV content"}, status=400)
        
        # Process JD (priority: file > text > url)
        jd_input = None
        if jd_file:
            jd_input = jd_file
        elif jd_text:
            jd_input = jd_text
        elif jd_url:
            jd_input = jd_url
        else:
            return Response({"error": "Please provide JD content"}, status=400)
        
        # Extract text
        cv_content, jd_content = file_processor.process_documents_for_analysis(cv_input, jd_input)
        
        # Use your existing skill analyzer
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(cv_content, jd_content)
        
        return Response(analysis_result)
        
    except Exception as e:
        logger.error(f"Direct analysis error: {str(e)}")
        return Response({"error": f"Analysis failed: {str(e)}"}, status=500)

@api_view(['GET'])
def get_skills(request, session_id):
    """Get enhanced dynamic skill gap analysis"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        logger.info(f"=== ENHANCED DYNAMIC ANALYSIS SESSION {session_id} ===")
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        logger.info("Starting enhanced dynamic analysis...")
        
        # Perform enhanced analysis
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(
            session.cv_text, 
            session.jd_text
        )
        
        logger.info(f"Enhanced analysis completed:")
        logger.info(f"- CV skills: {analysis_result.get('cv_skill_count', 0)}")
        logger.info(f"- JD skills: {analysis_result.get('jd_skill_count', 0)}")
        logger.info(f"- Matched skills: {len(analysis_result.get('matched_skills', []))}")
        logger.info(f"- Match percentage: {analysis_result.get('match_percentage', 0)}%")
        
        return Response(analysis_result)
        
    except Exception as e:
        logger.error(f"ENHANCED ANALYSIS ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            "error": "Enhanced analysis failed",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
def analyze_skill_gap_files(request):
    """Direct analysis from files without saving session"""
    try:
        cv_file = request.FILES.get('cv_file')
        jd_file = request.FILES.get('jd_file')
        cv_text = request.data.get('cv_text', '')
        jd_text = request.data.get('jd_text', '')
        
        # Process CV
        if cv_file:
            is_valid, message = file_processor.validate_file(cv_file)
            if not is_valid:
                return Response({"error": f"CV file invalid: {message}"}, status=400)
            cv_text = file_processor.extract_text_from_file(cv_file)
        
        # Process JD  
        if jd_file:
            is_valid, message = file_processor.validate_file(jd_file)
            if not is_valid:
                return Response({"error": f"JD file invalid: {message}"}, status=400)
            jd_text = file_processor.extract_text_from_file(jd_file)
        
        if not cv_text or not jd_text:
            return Response({"error": "Please provide both CV and JD content"}, status=400)
        
        # Perform analysis
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(cv_text, jd_text)
        
        return Response(analysis_result)
        
    except Exception as e:
        logger.error(f"Skill gap analysis error: {str(e)}")
        return Response({"error": f"Analysis failed: {str(e)}"}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import tempfile
import os
from pydub import AudioSegment
from pydub.utils import which
from .utils import calculate_interview_score

@csrf_exempt
def analyze_speech(request):
    if request.method == "POST" and request.FILES.get("audio"):
        try:
            import os, tempfile
            from django.http import JsonResponse
            from .speech_analysis import transcribe, highlight_fillers, check_ffmpeg
            audio_file = request.FILES["audio"]

            # Save uploaded file
            ext = os.path.splitext(audio_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                for chunk in audio_file.chunks():
                    tmp.write(chunk)
                temp_path = tmp.name

            print(f"📁 Uploaded: {audio_file.name} → Temp: {temp_path} ({os.path.getsize(temp_path)} bytes)")

            # Check FFmpeg
            if not check_ffmpeg():
                raise EnvironmentError("FFmpeg not found or not in PATH")

            # Transcribe
            result = transcribe(temp_path)
            highlighted = highlight_fillers(result["transcript"])

            # Clean up temp uploaded file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return JsonResponse({
                "success": True,
                "transcript": result["transcript"],
                "highlighted_fillers": highlighted,
                "metrics": result["metrics"],
                "hints": result["hints"]
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "No audio file"})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
import tempfile
import cv2
from deepface import DeepFace
from .speech_analysis import convert_webm_to_mp4
import subprocess

@csrf_exempt
def analyze_video_emotions(request):
    try:
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({
                'dominant_emotion': 'neutral',
                'hint': 'Detected emotion: neutral. No video uploaded.',
                'frame_emotions': [],
                'frame_hints': []
            }, status=400)

        # Save WebM temporarily
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        for chunk in video_file.chunks():
            temp_input.write(chunk)
        temp_input.close()

        # Convert WebM → MP4
        temp_video = convert_webm_to_mp4(temp_input.name)

        cap = cv2.VideoCapture(temp_video)
        if not cap.isOpened():
            raise ValueError("Unable to read video")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = max(1, int(fps / 2))  # analyze 2 frames/sec

        emotions = []
        frame_emotions = []
        frame_hints = []
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    analysis = DeepFace.analyze(
                        rgb_frame,
                        actions=['emotion'],
                        enforce_detection=False
                    )

                    dominant = None
                    if isinstance(analysis, list) and len(analysis) > 0:
                        dominant = analysis[0].get('dominant_emotion')
                    elif isinstance(analysis, dict):
                        dominant = analysis.get('dominant_emotion')

                    if dominant:
                        dominant = dominant.lower()
                        emotions.append(dominant)
                        frame_emotions.append(dominant)
                        frame_hints.append(get_hint_for_emotion(dominant))
                        print(f"Frame {frame_idx}: detected {dominant}")
                    else:
                        frame_emotions.append("neutral")
                        frame_hints.append(get_hint_for_emotion("neutral"))
                        print(f"Frame {frame_idx}: no face detected")
                except Exception as e:
                    frame_emotions.append("neutral")
                    frame_hints.append(get_hint_for_emotion("neutral"))
                    print(f"Frame skipped: {e}")

            frame_idx += 1

        cap.release()
        os.remove(temp_input.name)
        os.remove(temp_video)

        # Determine the most frequent emotion
        if not emotions:
            dominant_emotion = "neutral"
        else:
            dominant_emotion = max(set(emotions), key=emotions.count)

        # Map dominant emotion to hint
        hint_message = get_hint_for_emotion(dominant_emotion)

        return JsonResponse({
            'dominant_emotion': dominant_emotion,
            'hint': f"Detected emotion is {dominant_emotion}. {hint_message}",
            'frame_emotions': frame_emotions,
            'frame_hints': frame_hints
        })

    except subprocess.CalledProcessError:
        return JsonResponse({
            'dominant_emotion': 'neutral',
            'hint': 'FFmpeg conversion failed.',
            'frame_emotions': [],
            'frame_hints': []
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'dominant_emotion': 'neutral',
            'hint': f"Error: {str(e)}",
            'frame_emotions': [],
            'frame_hints': []
        }, status=500)


# -------------------------
# Map emotion → hint
# -------------------------
def get_hint_for_emotion(emotion):
    hints_dict = {
        "happy": "You look confident and engaged — great energy for communication!",
        "sad": "Try smiling more or lifting your tone to project enthusiasm.",
        "angry": "Your expression seems tense — relax your face and tone for calm delivery.",
        "fearful": "You appear anxious — take a deep breath and maintain eye contact.",
        "surprised": "Keep your expressions steady for a more composed appearance.",
        "neutral": "Balanced and calm — maintain this confident look!",
        "disgust": "You might seem uncomfortable — try relaxing your facial muscles."
    }
    return hints_dict.get(emotion, "Keep your expressions natural and expressive!")



@api_view(['POST'])
def parse_cv_jd(request):
    """Parse CV and JD using pure dynamic extraction"""
    cv_type = request.POST.get('cv_type', 'text')
    jd_type = request.POST.get('jd_type', 'text')
    
    cv_text = ""
    jd_text = ""
    
    # Process CV
    if cv_type == 'text':
        cv_text = request.POST.get('cv_text', '')
    elif cv_type == 'pdf':
        cv_file = request.FILES.get('cv_file')
        if cv_file:
            cv_text = extract_text_from_pdf(cv_file)
    elif cv_type == 'url':
        cv_url = request.POST.get('cv_url', '')
        if cv_url:
            cv_text = fetch_content_from_url(cv_url)
    
    # Process JD
    if jd_type == 'text':
        jd_text = request.POST.get('jd_text', '')
    elif jd_type == 'url':
        jd_url = request.POST.get('jd_url', '')
        if jd_url:
            jd_text = fetch_content_from_url(jd_url)
    
    # Validate
    if len(cv_text.strip()) < 10 or len(jd_text.strip()) < 10:
        return Response({"error": "Provided content is too short"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create session
    session_data = {
        'cv_text': cv_text,
        'jd_text': jd_text,
        'cv_type': cv_type,
        'jd_type': jd_type
    }
    
    serializer = InterviewSessionSerializer(data=session_data)
    if serializer.is_valid():
        session = serializer.save()
        return Response({
            "session_id": session.id, 
            "message": "CV and JD parsed successfully for dynamic analysis.",
            "cv_length": len(cv_text),
            "jd_length": len(jd_text)
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# In views.py - update the get_skills function
@api_view(['GET'])
def get_skills(request, session_id):
    """Get enhanced dynamic skill gap analysis"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        print(f"=== ENHANCED DYNAMIC ANALYSIS SESSION {session_id} ===")
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        print("Starting enhanced dynamic analysis...")
        
        # Perform enhanced analysis
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(
            session.cv_text, 
            session.jd_text
        )
        
        print(f"Enhanced analysis completed:")
        print(f"- CV skills: {analysis_result.get('cv_skill_count', 0)}")
        print(f"- JD skills: {analysis_result.get('jd_skill_count', 0)}")
        print(f"- Matched skills: {len(analysis_result.get('matched_skills', []))}")
        print(f"- Match percentage: {analysis_result.get('match_percentage', 0)}%")
        
        return Response(analysis_result)
        
    except Exception as e:
        print(f"ENHANCED ANALYSIS ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            "error": "Enhanced analysis failed",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
@api_view(['GET'])
def get_concept_extraction_debug(request, session_id):
    """Debug endpoint to see extracted concepts"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        cv_concepts = dynamic_skill_analyzer.extract_concepts_dynamic(session.cv_text)
        jd_concepts = dynamic_skill_analyzer.extract_concepts_dynamic(session.jd_text)
        
        return Response({
            "cv_concepts": cv_concepts,
            "jd_concepts": jd_concepts,
            "cv_concept_count": len(cv_concepts),
            "jd_concept_count": len(jd_concepts)
        })
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_questions(request, session_id):
    """Generate questions based on dynamic concept analysis"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        # Get dynamic analysis
        analysis_result = dynamic_skill_analyzer.analyze_skill_gap(
            session.cv_text, 
            session.jd_text
        )
        
        missing_skills = analysis_result.get('missing_skills', [])
        matched_skills = analysis_result.get('matched_skills', [])
        
        questions = []
        
        # Questions about matched concepts (strengths)
        for skill in matched_skills[:4]:
            questions.append({
                "question": f"Can you describe your experience with {skill['skill']}?",
                "rationale": f"Your background shows experience with {skill['cv_concept']} which aligns with the job's need for {skill['jd_concept']}.",
                "type": "strength",
                "similarity": skill.get('similarity', 0),
                "skill": skill['skill']
            })
        
        # Questions about missing concepts (development areas)
        for skill in missing_skills[:4]:
            questions.append({
                "question": f"How would you approach developing skills in {skill['skill']}?",
                "rationale": f"The position requires {skill['concept']} which represents an area for development.",
                "type": "development",
                "skill": skill['skill']
            })
        
        # Behavioral questions based on semantic analysis
        semantic_result = analysis_result.get('semantic_analysis', {})
        similar_pairs = semantic_result.get('most_similar_pairs', [])
        
        if similar_pairs:
            questions.append({
                "question": "Based on your experience, how would you approach the key responsibilities mentioned in this role?",
                "rationale": "Semantic analysis shows your background has relevant experience for this position.",
                "type": "behavioral",
                "similarity_score": similar_pairs[0].get('similarity_score', 0)
            })
        
        # Ensure minimum questions
        if len(questions) < 3:
            questions.extend([
                {
                    "question": "What motivated you to apply for this specific role?",
                    "rationale": "Understanding your motivation and alignment with the role.",
                    "type": "motivational"
                },
                {
                    "question": "Can you walk me through a complex project you're particularly proud of?",
                    "rationale": "Assessing your project experience and problem-solving approach.",
                    "type": "behavioral"
                }
            ])
        
        return Response({
            "questions": questions,
            "analysis_summary": {
                "matched_skills_count": len(matched_skills),
                "missing_skills_count": len(missing_skills),
                "match_percentage": analysis_result.get('match_percentage', 0),
                "semantic_similarity": semantic_result.get('similarity_score', 0)
            }
        })
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": "Dynamic question generation failed",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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