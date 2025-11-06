import os

from api.ml_extractor import get_universal_cv_extractor
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
from .cv_analyzer import cv_analyzer
import re
from .score_calculator import score_calculator
from .llm_service import llm_service

# Tell pydub where ffmpeg and ffprobe are
from pydub import AudioSegment
AudioSegment.converter = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\ProgramData\chocolatey\bin\ffprobe.exe"

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
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
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

from .file_processor import file_processor
import tempfile
import os
import PyPDF2
from django.contrib import messages
from django.db import IntegrityError

from .analysis import dynamic_skill_analyzer  # Import your existing analyzer


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
from django.shortcuts import redirect


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

from .question_generator import ai_question_generator
from .models import QuestionSet

from .xai_question_generator import xai_question_generator
import json
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



@api_view(['GET'])
def test_llm_directly(request):
    """Test LLM directly to see if it works"""
    try:
        from .llm_service import llm_service
        
        test_data = {
            "final_score": 75.5,
            "subscores": {
                "content": {"score": 80},
                "delivery": {"score": 70}, 
                "communication": {"score": 75}
            }
        }
        
        logger.info("🧪 Testing LLM directly...")
        explanation = llm_service.generate_natural_explanation(test_data)
        
        return Response({
            "success": True,
            "llm_model": llm_service.fast_model,
            "explanation": explanation,
            "message": "LLM is working!"
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e),
            "message": "LLM failed"
        }, status=500)

def extract_info_from_cv(cv_text):
    """Extract information from CV using UNIVERSAL parser"""
    try:
        extractor = get_universal_cv_extractor()  # ← Use universal extractor
        result = extractor.extract_all_info(cv_text)
        
        logger.info(f"🎯 UNIVERSAL CV Extraction Result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ UNIVERSAL CV extraction error: {e}")
        return {
            "first_name": "",
            "last_name": "", 
            "email": "",
            "phone_number": ""
        }

def signup_view(request):
    extracted_data = None
    error = None
    
    if request.method == 'POST':
        if 'manual_submit' in request.POST:
            # Manual registration
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            phone_number = request.POST.get('phone_number', '').strip()
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Validation
            if not all([first_name, last_name, email, password1, password2]):
                error = "All fields are required"
            elif password1 != password2:
                error = "Passwords don't match"
            elif len(password1) < 8:
                error = "Password must be at least 8 characters long"
            else:
                try:
                    user = CustomUser.objects.create_user(
                        username=email,
                        email=email,
                        password=password1,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number,
                        registration_method='manual'
                    )
                    
                    login(request, user)
                    messages.success(request, f"Welcome {first_name}! Your account has been created successfully.")
                    return redirect('upload')
                    
                except IntegrityError:
                    error = "A user with this email already exists"
                except Exception as e:
                    error = f"An error occurred: {str(e)}"
                
        elif 'cv_submit' in request.POST:
            cv_file = request.FILES.get('cv_file')
            if cv_file:
                try:
                    if not cv_file.name.lower().endswith('.pdf'):
                        error = "Please upload a PDF file"
                    else:
                        pdf_reader = PyPDF2.PdfReader(cv_file)
                        cv_text = ""
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                cv_text += text + "\n"
                        
                        if not cv_text.strip():
                            error = "Could not extract text from the PDF file"
                        else:
                            extracted_data = extract_info_from_cv(cv_text)
                            request.session['cv_text'] = cv_text
                            request.session['extracted_data'] = extracted_data
                            
                except Exception as e:
                    error = f"Error processing CV: {str(e)}"
            else:
                error = "Please select a PDF file"
    
    return render(request, 'signup.html', {
        'extracted_data': extracted_data,
        'error': error
    })

def finalize_cv_signup(request):
    error = None
    
    if request.method == 'POST':
        extracted_data = request.session.get('extracted_data', {})
        cv_text = request.session.get('cv_text', '')
        
        first_name = request.POST.get('first_name', extracted_data.get('first_name', '')).strip()
        last_name = request.POST.get('last_name', extracted_data.get('last_name', '')).strip()
        email = request.POST.get('email', extracted_data.get('email', '')).strip().lower()
        phone_number = request.POST.get('phone_number', extracted_data.get('phone_number', '')).strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not all([first_name, last_name, email, password1, password2]):
            error = "All fields are required"
        elif password1 != password2:
            error = "Passwords don't match"
        elif len(password1) < 8:
            error = "Password must be at least 8 characters long"
        else:
            try:
                user = CustomUser.objects.create_user(
                    username=email,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    cv_text=cv_text,
                    registration_method='cv'
                )
                
                login(request, user)
                
                if 'cv_text' in request.session:
                    del request.session['cv_text']
                if 'extracted_data' in request.session:
                    del request.session['extracted_data']
                
                messages.success(request, f"Welcome {first_name}! Your account has been created from your CV.")
                return redirect('upload')
                
            except IntegrityError:
                error = "A user with this email already exists"
            except Exception as e:
                error = f"An error occurred: {str(e)}"
    
    if error:
        messages.error(request, error)
    return redirect('signup')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
        if not email or not password:
            return render(request, 'login.html', {'error': 'Please enter both email and password'})
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('upload')
        else:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
@login_required
@api_view(['GET'])
def get_latest_score(request, session_id):
    """Get the latest score for a session"""
    try:
        latest_score = ScoreResult.objects.filter(session_id=session_id).order_by('-created_at').first()
        
        if not latest_score:
            return Response({"error": "No scores found for this session"}, status=404)
        
        # Convert database model to scoring system format
        score_data = {
            "final_score": latest_score.overall_score,
            "subscores": {
                "content": {"score": latest_score.content_score},
                "delivery": {"score": latest_score.delivery_score},
                "communication": {"score": latest_score.communication_score}
            },
            "explanations": latest_score.evidence_quotes or [],
            "next_actions": ["Practice more mock interviews", "Review your feedback"],  # You can customize these
            "feature_breakdown": latest_score.feature_contributions or {},
            "llm_explanation": f"Your overall score was {latest_score.overall_score}/100. Content: {latest_score.content_score}, Delivery: {latest_score.delivery_score}, Communication: {latest_score.communication_score}."
        }
        
        return Response(score_data)
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)
@login_required
@api_view(['POST'])
def calculate_score(request):
    """Real scoring endpoint using the XAI scoring system"""
    try:
        session_id = request.data.get('session_id')
        transcript_text = request.data.get('transcript_text', "")
        wpm = float(request.data.get('wpm', 0))
        filler_rate = float(request.data.get('filler_rate', 0)) / 100.0  # Convert percentage to decimal
        answer_length_s = float(request.data.get('answer_length_s', 0))
        question = request.data.get('question', "")
        
        logger.info(f"🎯 Starting score calculation for session {session_id}")
        logger.info(f"📊 Input metrics - WPM: {wpm}, Filler: {filler_rate}, Length: {answer_length_s}s")
        
        # Get JD keywords from session
        jd_keywords = []
        if session_id:
            try:
                session = InterviewSession.objects.get(pk=session_id)
                # Extract keywords from JD text (simplified - in production use proper NLP)
                jd_words = re.findall(r'\b\w+\b', session.jd_text.lower())
                jd_keywords = [word for word in jd_words if len(word) > 4][:10]  # Simple keyword extraction
                logger.info(f"🔑 Extracted {len(jd_keywords)} JD keywords")
            except InterviewSession.DoesNotExist:
                logger.warning(f"Session {session_id} not found")
        
        # Calculate comprehensive score
        score_result = score_calculator.calculate_comprehensive_score(
            transcript=transcript_text,
            wpm=wpm,
            filler_rate=filler_rate,
            answer_length_s=answer_length_s,
            jd_keywords=jd_keywords,
            question=question
        )
        
        # Save to database if session exists
        if session_id:
            try:
                session = InterviewSession.objects.get(pk=session_id)
                score_db = ScoreResult.objects.create(
                    session=session,
                    content_score=score_result['subscores']['content']['score'],
                    delivery_score=score_result['subscores']['delivery']['score'],
                    communication_score=score_result['subscores']['communication']['score'],
                    overall_score=score_result['final_score'],
                    feature_contributions=score_result['feature_breakdown'],
                    evidence_quotes=score_result['explanations']
                )
                logger.info(f"✅ Score saved to database: {score_db.id}")
            except InterviewSession.DoesNotExist:
                logger.warning(f"Session {session_id} not found, score not saved to database")
        
        return Response(score_result)
        
    except Exception as e:
        logger.error(f"❌ Score calculation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            "error": f"Score calculation failed: {str(e)}",
            "final_score": 0,
            "subscores": {
                "content": {"score": 0, "weight": 0.45},
                "delivery": {"score": 0, "weight": 0.35},
                "communication": {"score": 0, "weight": 0.20}
            },
            "explanations": ["Scoring system temporarily unavailable"],
            "next_actions": ["Please try again later"]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def get_jd_keywords_from_session(session_id):
    """Extract JD keywords from session for scoring"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        # Simple keyword extraction - you can enhance this
        jd_words = re.findall(r'\b\w+\b', session.jd_text.lower())
        # Filter for meaningful keywords (longer words)
        keywords = [word for word in jd_words if len(word) > 4]
        return keywords[:15]  # Limit to top 15 keywords
    except InterviewSession.DoesNotExist:
        return []
    
# ADD THIS LOGGER
logger = logging.getLogger(__name__)
# Questions 
@login_required
@api_view(['POST'])
def generate_questions_with_xai(request, session_id):
    """Generate questions with XAI explanations"""
    try:
        session = InterviewSession.objects.get(pk=session_id)

        # Perform skill gap analysis
        skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
        
        logger.info(f"🔍 XAI Skill Gap Analysis for session {session_id}:")
        logger.info(f"   Matched skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('matched_skills', [])]}")
        logger.info(f"   Missing skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('missing_skills', [])]}")

        # Generate questions with XAI
        result = xai_question_generator.generate_interview_questions_with_xai(
            session.cv_text,
            session.jd_text,
            skill_gap_analysis,
            num_questions=6
        )

        questions = result["questions"]
        xai_report = result["xai_report"]

        # TEMPORARY FIX: Store XAI data in session instead of QuestionSet
        # Save question set (without metadata for now)
        question_set = QuestionSet.objects.create(
            session=session, 
            questions=questions
            # Remove metadata parameter until model is updated
        )

        # Store XAI data in session's analysis_data
        if not session.analysis_data:
            session.analysis_data = {}
        
        session.analysis_data['xai_report'] = xai_report
        session.analysis_data['question_set_id'] = question_set.id
        session.analysis_data['generation_method'] = "xai_enhanced"
        session.analysis_data['judge_score'] = xai_report["quality_assurance"].get("overall_score", 0)
        session.save()

        logger.info(f"✅ XAI generation completed. Judge score: {xai_report['quality_assurance'].get('overall_score', 0)}")

        return Response({
            "session_id": session_id,
            "questions": questions,
            "xai_report": xai_report,
            "total_questions": len(questions),
            "generation_method": "xai_enhanced_with_judge",
            "quality_score": xai_report["quality_assurance"].get("overall_score", 0)
        })

    except InterviewSession.DoesNotExist:
        logger.error(f"❌ Session not found: {session_id}")
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ XAI question generation failed for session {session_id}: {str(e)}")
        return Response({"error": f"XAI question generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@login_required
@api_view(['GET'])
def get_xai_explanations(request, session_id):
    """Get XAI explanations for generated questions"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        # Check if XAI data exists in session analysis_data
        xai_report = None
        if session.analysis_data and isinstance(session.analysis_data, dict):
            xai_report = session.analysis_data.get('xai_report')
        
        if not xai_report:
            logger.info(f"ℹ️ No XAI report found for session {session_id}")
            return Response({
                "session_id": session_id,
                "xai_available": False,
                "message": "No AI explanations available. Questions were generated using standard method.",
                "questions": []  # Return empty to avoid frontend errors
            })

        # Get the latest question set for this session
        question_set = QuestionSet.objects.filter(session_id=session_id).order_by('-created_at').first()
        
        if not question_set:
            return Response({"error": "No questions found for this session"}, status=404)

        # Generate visualization data
        try:
            visualization_data = xai_question_generator.generate_explanation_visualization(xai_report)
            viz_data = json.loads(visualization_data)
        except Exception as e:
            logger.warning(f"Visualization generation failed: {e}")
            viz_data = {}

        return Response({
            "session_id": session_id,
            "xai_report": xai_report,
            "visualization_data": viz_data,
            "questions": question_set.questions,
            "quality_score": session.analysis_data.get('judge_score', 0),
            "xai_available": True
        })

    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)
    except Exception as e:
        logger.error(f"❌ Error getting XAI explanations: {e}")
        return Response({
            "error": str(e),
            "xai_available": False
        }, status=500)
@login_required
@api_view(['POST'])
def judge_questions_manual(request, session_id):
    """Manual trigger for LLM judge evaluation"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        question_set = QuestionSet.objects.filter(session_id=session_id).order_by('-created_at').first()
        
        if not question_set:
            return Response({"error": "No questions found for this session"}, status=404)

        skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
        
        # Run judge evaluation
        judge_evaluation = xai_question_generator._llm_judge_questions(
            question_set.questions,
            session.cv_text,
            session.jd_text,
            skill_gap_analysis
        )

        # Update question set metadata
        if not question_set.metadata:
            question_set.metadata = {}
        
        question_set.metadata['judge_evaluation'] = judge_evaluation
        question_set.metadata['last_judged_at'] = timezone.now().isoformat()
        question_set.save()

        return Response({
            "session_id": session_id,
            "judge_evaluation": judge_evaluation,
            "overall_score": judge_evaluation.get('overall_score', 0)
        })

    except Exception as e:
        logger.error(f"❌ Manual judge evaluation failed: {e}")
        return Response({"error": str(e)}, status=500)
@login_required
@api_view(['GET'])
def get_session_questions(request, session_id):
    """Get questions for a session, generate if they don't exist"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        # Check if questions already exist
        question_set = QuestionSet.objects.filter(session=session).order_by('-created_at').first()
        
        if not question_set:
            # Generate questions if they don't exist
            skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
            
            questions = ai_question_generator.generate_interview_questions(
                session.cv_text,
                session.jd_text,
                skill_gap_analysis,
                num_questions=6
            )
            
            question_set = QuestionSet.objects.create(session=session, questions=questions)
        
        return Response({
            "questions": question_set.questions,
            "total_questions": len(question_set.questions),
            "session_id": session_id
        })
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@login_required
@api_view(['GET'])
def get_session_questions(request, session_id):
    """Get questions for a session, generate if they don't exist"""
    try:
        logger.info(f"📋 Getting questions for session {session_id}")
        session = InterviewSession.objects.get(pk=session_id)
        
        # Check if questions already exist
        question_set = QuestionSet.objects.filter(session=session).order_by('-created_at').first()
        
        if not question_set:
            logger.info(f"🔄 No questions found for session {session_id}, generating now...")
            
            # Generate questions if they don't exist
            skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
            
            questions = ai_question_generator.generate_interview_questions(
                session.cv_text,
                session.jd_text,
                skill_gap_analysis,
                num_questions=6
            )
            
            question_set = QuestionSet.objects.create(session=session, questions=questions)
            logger.info(f"✅ Generated {len(questions)} questions for session {session_id}")
        else:
            logger.info(f"✅ Found existing {len(question_set.questions)} questions for session {session_id}")
        
        return Response({
            "questions": question_set.questions,
            "total_questions": len(question_set.questions),
            "session_id": session_id,
            "auto_generated": not question_set.created_at  # Indicate if questions were just generated
        })
        
    except InterviewSession.DoesNotExist:
        logger.error(f"❌ Session {session_id} not found")
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Error getting questions for session {session_id}: {str(e)}")
        return Response({"error": f"Failed to get questions: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@login_required
@api_view(['POST'])
def generate_more_questions(request, session_id):
    """Generate additional questions for practice"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
        
        questions = ai_question_generator.generate_interview_questions(
            session.cv_text,
            session.jd_text,
            skill_gap_analysis,
            num_questions=6
        )
        
        # Create new question set for the additional questions
        question_set = QuestionSet.objects.create(session=session, questions=questions)
        
        return Response({
            "questions": questions,
            "total_questions": len(questions),
            "session_id": session_id
        })
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
def init_ai_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY environment variable")
    # Any necessary environment setup can go here
    return

# In views.py - Temporary fix
@api_view(['POST'])
@csrf_exempt
def generate_questions(request, session_id):
    try:
        session = InterviewSession.objects.get(pk=session_id)

        # Perform skill gap analysis
        skill_gap_analysis = dynamic_skill_analyzer.analyze_skill_gap(session.cv_text, session.jd_text)
        
        # Debug: Log skill gap analysis
        logger.info(f"🔍 Skill Gap Analysis for session {session_id}:")
        logger.info(f"   Matched skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('matched_skills', [])]}")
        logger.info(f"   Missing skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('missing_skills', [])]}")

        # TEMPORARY FIX: Use the original method name
        # Generate interview questions using AI module
        questions = ai_question_generator.generate_interview_questions(
            session.cv_text,
            session.jd_text,
            skill_gap_analysis,
            num_questions=6
        )

        # Debug: Log the final questions structure
        logger.info(f"📦 Final questions structure for session {session_id}:")
        for i, q in enumerate(questions):
            logger.info(f"   Q{i+1}: {q.get('question', 'No question')[:50]}...")
            logger.info(f"      Has answer: {'Yes' if q.get('model_answer') else 'No'}")
            logger.info(f"      Hints count: {len(q.get('answer_hints', []))}")
            logger.info(f"      Key points count: {len(q.get('key_points', []))}")

        # Save question set
        question_set = QuestionSet.objects.create(session=session, questions=questions)

        return Response({
            "session_id": session_id,
            "questions": questions,
            "total_questions": len(questions),
            "generation_method": "ai_powered_with_answers"
        })

    except InterviewSession.DoesNotExist:
        logger.error(f"❌ Session not found: {session_id}")
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Question generation failed for session {session_id}: {str(e)}")
        return Response({"error": f"Question generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@login_required    
@api_view(['GET'])
def get_questions(request, session_id):
    """Get questions for a session"""
    try:
        question_set = QuestionSet.objects.filter(session_id=session_id).order_by('-created_at').first()
        if question_set:
            # Debug: Log the questions structure
            logger.info(f"🔍 GET Questions for session {session_id}:")
            for i, q in enumerate(question_set.questions):
                logger.info(f"   Q{i+1}: {q.get('question', 'No question')[:50]}...")
                logger.info(f"      Has answer: {'Yes' if q.get('model_answer') else 'No'}")
                logger.info(f"      Hints count: {len(q.get('answer_hints', []))}")
            
            return Response({
                "questions": question_set.questions,
                "total_questions": len(question_set.questions),
                "session_id": session_id
            })
        else:
            logger.warning(f"⚠️ No questions found for session {session_id}")
            return Response({
                "questions": [],
                "total_questions": 0,
                "session_id": session_id,
                "message": "No questions found. Please generate questions first."
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Error getting questions for session {session_id}: {str(e)}")
        return Response({"error": f"Failed to get questions: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CV analysis 
def cv_analysis_page(request):
    """Render the CV analysis page"""
    return render(request, 'cv_analysis.html')
@login_required
@api_view(['POST'])
def analyze_cv_standalone(request):
    """
    Standalone CV analysis with enhanced processing
    """
    try:
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        
        cv_content = ""
        
        # Handle file upload
        if cv_file:
            try:
                # Use your existing PDF extraction
                if hasattr(cv_file, 'name') and cv_file.name.endswith('.pdf'):
                    from .utils import extract_text_from_pdf
                    cv_content = extract_text_from_pdf(cv_file)
                    logger.info(f"PDF extracted text length: {len(cv_content)}")
                else:
                    # Read text files
                    cv_file.seek(0)
                    content = cv_file.read()
                    if isinstance(content, bytes):
                        cv_content = content.decode('utf-8', errors='ignore')
                    else:
                        cv_content = str(content)
                    logger.info(f"Text file extracted length: {len(cv_content)}")
            except Exception as e:
                logger.error(f"File processing error: {e}")
                return Response({"error": f"Failed to process file: {str(e)}"}, status=400)
        
        elif cv_text:
            cv_content = cv_text
            logger.info(f"Direct text input length: {len(cv_content)}")
        
        if not cv_content or len(cv_content.strip()) < 50:
            return Response({"error": "CV content is too short or empty"}, status=400)
        
        logger.info(f"Analyzing CV content length: {len(cv_content)}")
        
        # Perform analysis with the CORRECT analyzer - use cv_analyzer instead of enhanced_analyzer
        analysis_result = cv_analyzer.analyze_cv(cv_content)
        
        # Create session
        session = InterviewSession.objects.create(
            cv_text=cv_content[:10000],  # Limit length
            jd_text="CV Analysis Session",
            analysis_data={"cv_analysis": analysis_result}
        )
        
        return Response({
            "session_id": session.id,
            "analysis": analysis_result,
            "content_length": len(cv_content),
            "analysis_method": analysis_result.get('analysis_method', 'unknown')
        })
        
    except Exception as e:
        logger.error(f"CV analysis error: {str(e)}")
        return Response({"error": f"Analysis failed: {str(e)}"}, status=500)
@login_required
@api_view(['POST'])
def analyze_cv_with_jd(request):
    """
    Comprehensive analysis: CV + JD together with enhanced feedback
    """
    try:
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        jd_file = request.FILES.get('jd_file') 
        jd_text = request.data.get('jd_text', '')
        
        # Process inputs
        cv_content = ""
        jd_content = ""
        
        if cv_file:
            cv_content, _ = file_processor.process_documents_for_analysis(cv_file, "")
        elif cv_text:
            cv_content = cv_text
            
        if jd_file:
            _, jd_content = file_processor.process_documents_for_analysis("", jd_file)
        elif jd_text:
            jd_content = jd_text
        
        if not cv_content.strip():
            return Response({"error": "No CV content provided"}, status=400)
        
        # Get standalone CV analysis
        cv_analysis = cv_analyzer.analyze_cv(cv_content)
        
        # Get skill gap analysis (using your existing function)
        skill_analysis = {}
        if jd_content.strip():
            skill_analysis = dynamic_skill_analyzer.analyze_skill_gap(cv_content, jd_content)
        
        # Combine analyses
        comprehensive_analysis = {
            "cv_analysis": cv_analysis,
            "skill_analysis": skill_analysis,
            "recommendations": self._generate_comprehensive_recommendations(cv_analysis, skill_analysis)
        }
        
        # Create session
        session = InterviewSession.objects.create(
            cv_text=cv_content,
            jd_text=jd_content,
            analysis_data=comprehensive_analysis
        )
        
        return Response({
            "session_id": session.id,
            "comprehensive_analysis": comprehensive_analysis
        })
        
    except Exception as e:
        logger.error(f"Comprehensive CV analysis error: {str(e)}")
        return Response({"error": f"Analysis failed: {str(e)}"}, status=500)
@login_required
@api_view(['GET'])
def get_cv_analysis_report(request, session_id):
    """
    Get CV analysis report for a session
    """
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        if not session.analysis_data:
            return Response({"error": "No analysis data found for this session"}, status=404)
        
        return Response({
            "session_id": session_id,
            "cv_preview": session.cv_text[:1000] + "..." if len(session.cv_text) > 1000 else session.cv_text,
            "analysis": session.analysis_data
        })
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

def debug_questions(request, session_id):
    """Debug endpoint to check question structure"""
    try:
        question_set = QuestionSet.objects.filter(session_id=session_id).order_by('-created_at').first()
        if question_set:
            questions = question_set.questions
            logger.info(f"🔍 DEBUG: Questions for session {session_id}:")
            for i, q in enumerate(questions):
                logger.info(f"   Question {i+1}: {q.get('question', 'No question')}")
                logger.info(f"   Answer: {q.get('model_answer', 'No answer')[:100]}...")
                logger.info(f"   Hints: {q.get('answer_hints', [])}")
                logger.info(f"   Key Points: {q.get('key_points', [])}")
                logger.info("   ---")
            
            return Response({
                "total_questions": len(questions),
                "questions_sample": questions[0] if questions else {},
                "all_questions": questions
            })
        else:
            return Response({"error": "No questions found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def practice_view(request, session_id):
    """Render the practice page"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        return render(request, 'practice.html', {
            'session_id': session_id
        })
    except InterviewSession.DoesNotExist:
        return render(request, 'error.html', {'error': 'Session not found'})

@login_required
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


# Helper function for internal score calculation
def calculate_score_internal(session_id, transcript_text, wpm, filler_rate, answer_length_s, question):
    """Internal function to calculate score without HTTP request"""
    from django.http import HttpRequest
    from rest_framework.request import Request
    
    # Create a mock request for the score calculator
    mock_data = {
        'session_id': session_id,
        'transcript_text': transcript_text,
        'wpm': wpm,
        'filler_rate': filler_rate,
        'answer_length_s': answer_length_s,
        'question': question
    }
    
    # Use the existing calculate_score view logic
    request = HttpRequest()
    request.method = 'POST'
    request.data = mock_data
    request.user = None  # You might need to handle authentication
    
    return calculate_score(Request(request))

@login_required
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
            session_id = request.POST.get("session_id")
            question = request.POST.get("question", "")

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

            # ✅ ADD REAL SCORING SYSTEM HERE
            score_data = None
            if session_id:
                try:
                    # Get JD keywords from session
                    jd_keywords = []
                    try:
                        session = InterviewSession.objects.get(pk=session_id)
                        # Extract REAL JD keywords from the actual job description
                        jd_words = re.findall(r'\b\w+\b', session.jd_text.lower())
                        jd_keywords = [word for word in jd_words if len(word) > 4][:15]
                        print(f"🎯 Using JD keywords: {jd_keywords}")
                    except Exception as e:
                        print(f"⚠️ Could not load session: {e}")
                    
                    # USE THE REAL SCORING SYSTEM
                    score_data = score_calculator.calculate_comprehensive_score(
                        transcript=result["transcript"],
                        wpm=result["metrics"]["wpm"],
                        filler_rate=result["metrics"]["filler_pct"] / 100.0,  # Convert % to decimal
                        answer_length_s=result["metrics"]["duration_s"],
                        jd_keywords=jd_keywords,
                        question=question
                    )
                    
                    print(f"🏆 REAL SCORE CALCULATED: {score_data['final_score']}/100")
                    
                    # Save to database
                    try:
                        session = InterviewSession.objects.get(pk=session_id)
                        score_db = ScoreResult.objects.create(
                            session=session,
                            content_score=score_data['subscores']['content']['score'],
                            delivery_score=score_data['subscores']['delivery']['score'],
                            communication_score=score_data['subscores']['communication']['score'],
                            overall_score=score_data['final_score'],
                            feature_contributions=score_data['feature_breakdown'],
                            evidence_quotes=score_data['explanations']
                        )
                        print(f"💾 Score saved to database with ID: {score_db.id}")
                    except Exception as e:
                        print(f"⚠️ Could not save score to database: {e}")
                        
                except Exception as score_error:
                    logger.error(f"❌ Score calculation failed: {score_error}")
                    # Continue without score data

            # Build response data
            response_data = {
                "success": True,
                "transcript": result["transcript"],
                "highlighted_fillers": highlighted,
                "metrics": result["metrics"],
                "hints": result["hints"]
            }
            
            # Add score data if available
            if score_data:
                response_data["score"] = score_data

            # Clean up temp uploaded file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return JsonResponse(response_data)

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
@login_required
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
@login_required
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
@login_required
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
@login_required
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


@login_required
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
@login_required
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
@login_required
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