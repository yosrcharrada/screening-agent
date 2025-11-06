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
from .cv_analyzer import cv_analyzer

# Tell pydub where ffmpeg and ffprobe are
from pydub import AudioSegment
AudioSegment.converter = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\ProgramData\chocolatey\bin\ffprobe.exe"

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
# ADD THIS LOGGER
logger = logging.getLogger(__name__)
# Questions 
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


# Job Notification Feature Views
from .models import UserProfile, JobOffer, JobNotification
from .serializers import UserProfileSerializer, JobOfferSerializer, JobNotificationSerializer
from .job_scraper import job_scraper
from .job_matcher import job_matcher
from .email_service import email_service


@api_view(['POST'])
def create_user_profile(request):
    """Create a new user profile for job notifications"""
    try:
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            user_profile = serializer.save()
            logger.info(f"Created new user profile: {user_profile.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def manage_user_profile(request, email):
    """Get, update, or delete a user profile"""
    try:
        user_profile = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Updated user profile: {email}")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        user_profile.delete()
        logger.info(f"Deleted user profile: {email}")
        return Response({"message": "User profile deleted"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def search_jobs_manually(request):
    """Manually search for jobs with given criteria"""
    try:
        keywords = request.data.get('keywords', [])
        location = request.data.get('location', '')
        limit = request.data.get('limit', 20)
        
        if not keywords:
            return Response({"error": "Keywords are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch jobs
        jobs = job_scraper.fetch_jobs(keywords=keywords, location=location, limit=limit)
        
        return Response({
            "total": len(jobs),
            "jobs": jobs
        })
    except Exception as e:
        logger.error(f"Error in manual job search: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_notifications(request, email):
    """Get job notifications for a user"""
    try:
        user_profile = UserProfile.objects.get(email=email)
        notifications = JobNotification.objects.filter(user_profile=user_profile).order_by('-sent_at')[:50]
        serializer = JobNotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = JobNotification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})
    except JobNotification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_test_email(request):
    """Send a test email to verify email configuration"""
    try:
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        success = email_service.send_test_email(email)
        
        if success:
            return Response({"message": "Test email sent successfully"})
        else:
            return Response({"error": "Failed to send test email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_recent_jobs(request):
    """Get recently fetched jobs"""
    try:
        limit = int(request.GET.get('limit', 50))
        jobs = JobOffer.objects.all()[:limit]
        serializer = JobOfferSerializer(jobs, many=True)
        return Response({
            "total": jobs.count(),
            "jobs": serializer.data
        })
    except Exception as e:
        logger.error(f"Error getting recent jobs: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def trigger_job_matching(request, email):
    """Manually trigger job matching and notification for a specific user"""
    try:
        user_profile = UserProfile.objects.get(email=email)
        
        # Get recent jobs
        recent_jobs = JobOffer.objects.all()[:100]
        
        if not recent_jobs.exists():
            return Response({"message": "No jobs available to match"}, status=status.HTTP_404_NOT_FOUND)
        
        # Find matching jobs
        min_score = float(request.data.get('min_score', 40.0))
        matches = job_matcher.find_matching_jobs(
            user_profile=user_profile,
            jobs=list(recent_jobs),
            min_score=min_score
        )
        
        if not matches:
            return Response({"message": "No matching jobs found"})
        
        # Filter out already notified jobs
        new_jobs = []
        match_scores = {}
        
        for job, score in matches:
            already_notified = JobNotification.objects.filter(
                user_profile=user_profile,
                job_offer=job
            ).exists()
            
            if not already_notified:
                new_jobs.append(job)
                match_scores[job.id] = score
        
        if not new_jobs:
            return Response({"message": "All matching jobs already notified"})
        
        # Send email
        send_email = request.data.get('send_email', False)
        if send_email:
            success = email_service.send_job_notification(
                user_profile=user_profile,
                jobs=new_jobs,
                match_scores=match_scores
            )
            
            if success:
                # Create notification records
                for job in new_jobs:
                    JobNotification.objects.create(
                        user_profile=user_profile,
                        job_offer=job,
                        match_score=match_scores.get(job.id, 0)
                    )
                
                return Response({
                    "message": f"Email sent with {len(new_jobs)} job(s)",
                    "jobs_count": len(new_jobs)
                })
            else:
                return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Just return matching jobs without sending email
            job_details = []
            for job in new_jobs[:10]:  # Limit to 10 for response
                job_details.append({
                    'title': job.title,
                    'company': job.company,
                    'match_score': match_scores.get(job.id, 0)
                })
            
            return Response({
                "message": f"Found {len(new_jobs)} matching job(s)",
                "jobs": job_details,
                "total_matches": len(new_jobs)
            })
        
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in trigger_job_matching: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)