from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser,InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
from .serializers import InterviewSessionSerializer, SkillMatchResultSerializer, QuestionSetSerializer, TranscriptSerializer, ScoreResultSerializer
from .pdf_generator import PDFGenerator
import re  # Add this line at the top with other imports
from .utils import extract_text_from_pdf, fetch_content_from_url, validate_pdf_file
from django.utils import timezone

# views.py - Add these imports at the top
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time
# Add this to your views.py
# In views.py - replace analyze_speech function

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession
from .serializers import InterviewSessionSerializer

from .utils import extract_text_from_pdf, fetch_content_from_url, validate_pdf_file
from .analysis import dynamic_skill_analyzer
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .file_processor import file_processor
from django.core.files.storage import FileSystemStorage

from .file_processor import file_processor
import tempfile
import os
import PyPDF2
from django.contrib import messages
from django.db import IntegrityError

from .analysis import dynamic_skill_analyzer  # Import your existing analyzer

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession
from .file_processor import file_processor
from .analysis import dynamic_skill_analyzer
from django.shortcuts import redirect
# ADD THIS LOGGER
logger = logging.getLogger(__name__)

from .question_generator import ai_question_generator
from .models import QuestionSet

# views.py

import os
import tempfile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from .models import InterviewSession, QuestionSet
from .analysis import dynamic_skill_analyzer
from .question_generator import ai_question_generator

# Add this view function to views.py

# Add this to views.py for debugging
# Add to your existing views.py imports
from .cv_analyzer import cv_analyzer
import json

# ADD THESE IMPORTS AT THE TOP
from .ml_extractor import get_universal_cv_extractor

import logging

logger = logging.getLogger(__name__)

# IMPORT THE SCORING SYSTEM
from .score_calculator import score_calculator

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

# Add these new views to your existing views.py
# Add this to your views.py
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
    
def _generate_comprehensive_recommendations(cv_analysis, skill_analysis):
    """Generate targeted recommendations based on both CV and skill analysis"""
    recommendations = []
    
    # Add CV-specific recommendations
    if 'recommendations' in cv_analysis:
        recommendations.extend(cv_analysis['recommendations'])
    
    # Add skill gap recommendations
    if skill_analysis and 'missing_skills' in skill_analysis:
        missing_skills = skill_analysis.get('missing_skills', [])
        if missing_skills:
            recommendations.append(f"Focus on developing these missing skills: {', '.join(missing_skills[:5])}")
    
    # Add general best practices
    general_tips = [
        "Use action verbs to describe achievements (e.g., 'managed', 'developed', 'increased')",
        "Include quantifiable metrics (e.g., 'increased sales by 20%', 'managed team of 5')",
        "Keep CV length to 1-2 pages maximum",
        "Use consistent formatting and professional font",
        "Tailor CV to each specific job application"
    ]
    
    recommendations.extend(general_tips)
    return list(set(recommendations))[:10]  # Remove duplicates and limit

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

@login_required
@api_view(['GET'])
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
@login_required
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
    
# In views.py - Add this if it doesn't exist
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

@login_required
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

@login_required
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

# UPDATED: analyze_speech with REAL scoring integration
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
            
            # GET SESSION DATA FOR REAL SCORING
            session_id = request.POST.get('session_id')
            jd_keywords = []
            question_text = request.POST.get('question', '')
            
            if session_id:
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
                transcript=result['transcript'],
                wpm=result['metrics']['wpm'],
                filler_rate=result['metrics']['filler_pct'] / 100.0,  # Convert % to decimal
                answer_length_s=result['metrics']['duration_s'],
                jd_keywords=jd_keywords,
                question=question_text
            )
            
            print(f"🏆 REAL SCORE CALCULATED: {score_data['final_score']}/100")
            
            # Save to database if session exists
            if session_id:
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
                'score': score_data  # Now returns COMPREHENSIVE SCORE DATA
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

# UPDATED: Real scoring endpoint
@login_required
@api_view(['POST'])
def calculate_score(request):
    """Real scoring endpoint using the XAI scoring system"""
    try:
        session_id = request.data.get('session_id')
        transcript_text = request.data.get('transcript_text', "")
        wpm = request.data.get('wpm', 0)
        filler_rate = request.data.get('filler_rate', 0) / 100.0  # Convert percentage to decimal
        answer_length_s = request.data.get('answer_length_s', 0)
        question = request.data.get('question', "")
        
        # Get JD keywords from session
        jd_keywords = []
        if session_id:
            try:
                session = InterviewSession.objects.get(pk=session_id)
                # Extract keywords from JD text (simplified - in production use proper NLP)
                jd_words = re.findall(r'\b\w+\b', session.jd_text.lower())
                jd_keywords = [word for word in jd_words if len(word) > 4][:10]  # Simple keyword extraction
            except InterviewSession.DoesNotExist:
                pass
        
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

# NEW: Test scoring system endpoint
@login_required
@api_view(['GET'])
def test_scoring_system(request, session_id):
    """Test the scoring system with actual session data"""
    try:
        session = InterviewSession.objects.get(pk=session_id)
        
        # Use real data from the session
        test_transcript = "I worked on a project where we faced performance issues. My task was to optimize the system. I implemented caching and database optimizations. As a result, we improved response times by 40% and reduced server costs by 25%."
        
        # Real metrics (you can modify these to test different scenarios)
        test_metrics = {
            'wpm': 145.0,
            'filler_rate': 0.03,  # 3%
            'duration_s': 65.0
        }
        
        # Extract JD keywords from actual session JD text
        jd_words = re.findall(r'\b\w+\b', session.jd_text.lower())
        jd_keywords = [word for word in jd_words if len(word) > 4][:15]  # Get top 15 keywords
        
        # Calculate real score
        score_result = score_calculator.calculate_comprehensive_score(
            transcript=test_transcript,
            wpm=test_metrics['wpm'],
            filler_rate=test_metrics['filler_rate'],
            answer_length_s=test_metrics['duration_s'],
            jd_keywords=jd_keywords,
            question="Tell me about a technical challenge you faced"
        )
        
        return Response({
            "session_id": session_id,
            "test_data": {
                "transcript_sample": test_transcript[:100] + "...",
                "metrics": test_metrics,
                "jd_keywords_found": jd_keywords
            },
            "score_result": score_result
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)

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

# In views.py - update the get_skills function
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

# In views.py - REPLACE the generate_report function with this:

@login_required
@api_view(['GET'])
def generate_report(request, session_id):
    """Generate PDF report and return download URL"""
    try:
        # For now, return a URL to the real PDF endpoint
        pdf_url = f"http://127.0.0.1:8000/api/generate-real-pdf/{session_id}/"
        
        return Response({
            "pdf_url": pdf_url,
            "message": "PDF report generated successfully",
            "download_url": pdf_url
        })
        
    except Exception as e:
        return Response({
            "error": f"Report generation failed: {str(e)}",
            "pdf_url": None
        }, status=500)
# A simple view to serve the mock PDF for testing
from django.http import FileResponse
import os

# In views.py - REPLACE the serve_mock_pdf function with this:

from django.http import HttpResponse, FileResponse
import os
from django.views.decorators.csrf import csrf_exempt

@login_required
def serve_mock_pdf(request, session_id):
    """Serve a mock PDF for testing purposes."""
    try:
        # For now, create a simple text response
        response = HttpResponse("Mock PDF Report - Session {}".format(session_id), 
                              content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="mock_report_{}.txt"'.format(session_id)
        return response
    except Exception as e:
        return HttpResponse("Error generating PDF: {}".format(str(e)), status=500)
    
    # In views.py - Add these imports at the top
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from datetime import datetime

@login_required
@api_view(['GET'])
def generate_real_pdf(request, session_id):
    """Generate a real PDF report using WeasyPrint"""
    try:
        # Get session data
        session = InterviewSession.objects.get(pk=session_id)
        
        # Get the latest score for this session
        latest_score = ScoreResult.objects.filter(session=session).order_by('-created_at').first()
        
        # Prepare context for PDF
        context = {
            'candidate_name': request.user.get_full_name() or request.user.email,
            'session_id': session_id,
            'generation_date': datetime.now().strftime("%B %d, %Y"),
            'final_score': latest_score.overall_score if latest_score else 0,
            'content_score': latest_score.content_score if latest_score else 0,
            'delivery_score': latest_score.delivery_score if latest_score else 0,
            'communication_score': latest_score.communication_score if latest_score else 0,
            'explanations': latest_score.evidence_quotes if latest_score else ["No analysis data available"],
            'next_actions': ["Practice more mock interviews", "Work on STAR method", "Improve speaking pace"] if latest_score else ["Complete a practice session first"],
        }
        
        # Render HTML template
        html_string = render_to_string('score_report.html', context)
        
        # Create PDF
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="interview_report_{session_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except InterviewSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return Response({"error": f"PDF generation failed: {str(e)}"}, status=500)
    
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