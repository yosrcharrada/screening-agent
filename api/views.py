from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult
from .serializers import InterviewSessionSerializer, SkillMatchResultSerializer, QuestionSetSerializer, TranscriptSerializer, ScoreResultSerializer

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

from .file_processor import file_processor
from django.core.files.storage import FileSystemStorage

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

# In views.py, update the generate_questions function

# In views.py - Update the generate_questions function

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
    
# In views.py - Add this if it doesn't exist

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