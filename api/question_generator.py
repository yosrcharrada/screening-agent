import os
import logging
import re
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from django.conf import settings

logger = logging.getLogger(__name__)

class AIQuestionGenerator:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY environment variable")
        self._initialize_models()

    def _initialize_models(self):
        logger.info("🚀 Initializing Google Gemini LLM and Embeddings models...")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            google_api_key=self.api_key
        )
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        logger.info("✅ Models initialized successfully")
    
    # Add to your existing AIQuestionGenerator class in question_generator.py

def generate_interview_questions_with_xai(self, cv_text, jd_text, skill_gap_analysis, num_questions=6):
    """
    XAI-enhanced question generation with backward compatibility
    Falls back to original method if XAI is not available
    """
    try:
        # Try to use XAI generator if available
        from .xai_question_generator import xai_question_generator
        logger.info("🎯 Using XAI-enhanced question generation")
        
        result = xai_question_generator.generate_interview_questions_with_xai(
            cv_text, jd_text, skill_gap_analysis, num_questions
        )
        return result
        
    except ImportError:
        logger.warning("⚠️ XAI generator not available, falling back to standard generation")
        # Fall back to original method
        return {
            "questions": self.generate_interview_questions_with_answers(cv_text, jd_text, skill_gap_analysis, num_questions),
            "xai_report": None,
            "generation_metadata": {
                "total_questions": num_questions,
                "generation_method": "standard_fallback"
            }
        }
    except Exception as e:
        logger.error(f"❌ XAI generation failed, using fallback: {e}")
        return {
            "questions": self.generate_interview_questions_with_answers(cv_text, jd_text, skill_gap_analysis, num_questions),
            "xai_report": None,
            "generation_metadata": {
                "total_questions": num_questions,
                "generation_method": "error_fallback"
            }
        }
    def process_pdf(self, file_path):
        logger.info(f"📄 Loading and splitting PDF from {file_path}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        return texts

    def generate_interview_questions(self, cv_text, jd_text, skill_gap_analysis, num_questions=6):
        """Original method - kept for backward compatibility"""
        return self.generate_interview_questions_with_answers(cv_text, jd_text, skill_gap_analysis, num_questions)

    def generate_interview_questions_with_answers(self, cv_text, jd_text, skill_gap_analysis, num_questions=6):
        matched = [s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get("matched_skills", [])]
        missing = [s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get("missing_skills", [])]

        prompt_text = (
            f"You are an expert HR interviewer and career coach. Based on the job description and candidate CV below, "
            f"please generate exactly {num_questions} interview questions in JSON format.\n\n"
            "STRUCTURE EACH QUESTION WITH:\n"
            "- 'question': The interview question text\n"
            "- 'focus': Which skill area this targets (behavioral, technical_django, technical_python, technical_aws, technical_gcp, situational, leadership)\n"
            "- 'rationale': Brief explanation of why this question is relevant for this candidate\n"
            "- 'skill_type': Whether this addresses 'matched_skill' or 'missing_skill'\n"
            "- 'target_skill': The specific skill being assessed\n"
            "- 'model_answer': A well-structured model answer using STAR method (Situation, Task, Action, Result)\n"
            "- 'answer_hints': List of 3-5 specific hints to help answer this question effectively\n"
            "- 'key_points': List of key points that should be covered in a good answer\n\n"
            f"MATCHED SKILLS TO ASSESS: {', '.join(matched)}\n"
            f"MISSING SKILLS TO ADDRESS: {', '.join(missing)}\n\n"
            "QUESTIONS SHOULD COVER:\n"
            "- 2 behavioral questions about past experience\n"
            "- 2 technical questions on matched skills\n" 
            "- 2 situational questions addressing missing skills\n\n"
            f"Job Description:\n{jd_text[:1000]}...\n\n"
            f"Candidate CV:\n{cv_text[:1000]}...\n\n"
            "Return ONLY valid JSON array format, no other text:\n"
            "[{'question': '...', 'focus': '...', 'rationale': '...', 'skill_type': '...', 'target_skill': '...', 'model_answer': '...', 'answer_hints': ['hint1', 'hint2'], 'key_points': ['point1', 'point2']}]"
        )

        logger.info("🧠 Generating interview questions with answers and hints")
        logger.info(f"📊 Matched skills: {matched}")
        logger.info(f"📊 Missing skills: {missing}")
        
        try:
            response = self.llm.invoke(prompt_text)
            generated_text = response.content
            
            # Debug: Print the raw response
            logger.info("📨 Raw AI Response:")
            logger.info(generated_text[:500] + "..." if len(generated_text) > 500 else generated_text)
            
            # Clean the response - remove markdown code blocks if present
            cleaned_text = re.sub(r'```json\s*|\s*```', '', generated_text).strip()
            
            # Parse JSON response
            questions_data = json.loads(cleaned_text)
            
            # Debug: Print parsed data
            logger.info(f"✅ Successfully parsed {len(questions_data)} questions")
            for i, q in enumerate(questions_data):
                logger.info(f"📝 Question {i+1}: {q.get('question', 'No question')[:100]}...")
                logger.info(f"   Answer: {'Yes' if q.get('model_answer') else 'No'}")
                logger.info(f"   Hints: {len(q.get('answer_hints', []))}")
                logger.info(f"   Key Points: {len(q.get('key_points', []))}")
            
            # Ensure we have the right number of questions
            if len(questions_data) > num_questions:
                questions_data = questions_data[:num_questions]
                
            logger.info(f"✅ Successfully generated {len(questions_data)} questions with answers and hints")
            return questions_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {generated_text}")
            # Fallback to simple question generation
            return self._generate_fallback_questions_with_answers(matched, missing, num_questions)
        except Exception as e:
            logger.error(f"❌ Unexpected error in question generation: {e}")
            return self._generate_fallback_questions_with_answers(matched, missing, num_questions)

    def _generate_fallback_questions_with_answers(self, matched_skills, missing_skills, num_questions):
        """Fallback method if JSON parsing fails"""
        logger.warning("🔄 Using fallback question generation")
        questions = []
        
        # Distribute questions between matched and missing skills
        num_matched = min(3, len(matched_skills))
        num_missing = min(3, len(missing_skills))
        
        for i in range(num_matched):
            if i < len(matched_skills):
                skill = matched_skills[i]
                questions.append({
                    "question": f"Can you describe your experience with {skill} and provide an example of a project where you used it effectively?",
                    "focus": f"technical_{skill.lower()}",
                    "rationale": f"Assessing depth of experience with {skill} which matches the job requirements",
                    "skill_type": "matched_skill",
                    "target_skill": skill,
                    "model_answer": f"In my previous role, I extensively used {skill} to develop a scalable solution. The situation required handling increasing user load. My task was to optimize performance. I implemented efficient algorithms and caching strategies using {skill}, which resulted in 40% performance improvement and better user satisfaction. The key was understanding the system constraints and applying the right {skill} features to address them.",
                    "answer_hints": [
                        f"Focus on a specific project example using {skill}",
                        "Mention the business impact of your work",
                        "Describe the technical challenges you overcame",
                        "Quantify your results with metrics",
                        f"Explain why you chose specific {skill} features"
                    ],
                    "key_points": [
                        f"Specific {skill} features used",
                        "Problem-solving approach",
                        "Measurable outcomes",
                        "Learning and improvements",
                        "Business impact"
                    ]
                })
        
        for i in range(num_missing):
            if i < len(missing_skills):
                skill = missing_skills[i]
                questions.append({
                    "question": f"How would you approach learning and implementing {skill} if required for this role?",
                    "focus": f"technical_{skill.lower()}",
                    "rationale": f"Exploring willingness to learn missing skill {skill}",
                    "skill_type": "missing_skill", 
                    "target_skill": skill,
                    "model_answer": f"While I haven't worked extensively with {skill}, I have a strong foundation in related technologies. I would start by taking online courses and building small projects to understand the fundamentals. Then I'd seek mentorship from experienced colleagues and gradually take on more complex tasks. My experience with similar technologies would help me ramp up quickly, and I'm confident I could become productive with {skill} within a few weeks.",
                    "answer_hints": [
                        "Show enthusiasm for learning",
                        "Connect to your existing skills",
                        "Provide a concrete learning plan",
                        "Mention how you'll apply it to the role",
                        "Set realistic timeline expectations"
                    ],
                    "key_points": [
                        "Learning strategy and resources",
                        "Timeline for skill acquisition",
                        "Transferable skills",
                        "Practical application plans",
                        "Measurement of progress"
                    ]
                })
        
        # Fill remaining slots with behavioral questions
        while len(questions) < num_questions:
            questions.append({
                "question": "Describe a challenging project you worked on and how you overcame the main obstacles.",
                "focus": "behavioral",
                "rationale": "Assessing problem-solving and project management skills",
                "skill_type": "behavioral",
                "target_skill": "problem_solving",
                "model_answer": "In a recent project, we faced tight deadlines and technical challenges with integrating multiple legacy systems. The situation required delivering a critical feature under pressure while maintaining system stability. My task was to lead the development team and ensure on-time delivery. I organized daily standups, broke down tasks into manageable chunks, implemented agile practices, and created contingency plans. The result was successful on-time delivery with all requirements met, and the client was very satisfied with both the process and outcome.",
                "answer_hints": [
                    "Use STAR method: Situation, Task, Action, Result",
                    "Be specific about challenges and constraints",
                    "Highlight your leadership and decision-making role",
                    "Quantify the success metrics",
                    "Show what you learned from the experience"
                ],
                "key_points": [
                    "Clear problem description with context",
                    "Your specific actions and decisions",
                    "Team collaboration and communication",
                    "Measurable outcomes and impact",
                    "Lessons learned and improvements"
                ]
            })
        
        logger.info(f"🔄 Generated {len(questions)} fallback questions with answers")
        return questions[:num_questions]

    def create_qa_system(self, texts):
        """Create a simple QA system without complex chains"""
        vector_store = FAISS.from_documents(texts, self.embedding_model)
        retriever = vector_store.as_retriever(search_kwargs={'k': 3})
        return retriever

    def generate_all(self, cv_text, jd_text, skill_gap_analysis, pdf_path):
        """Main method to generate questions and answers"""
        try:
            # Process PDF for context
            texts = self.process_pdf(pdf_path)
            
            # Generate structured questions with answers
            questions = self.generate_interview_questions_with_answers(cv_text, jd_text, skill_gap_analysis)
            
            # Create QA system for answering
            retriever = self.create_qa_system(texts)
            
            return {
                "questions": questions,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in generate_all: {e}")
            return {
                "questions": [],
                "status": "error",
                "error": str(e)
            }

# Instantiate for reuse
ai_question_generator = AIQuestionGenerator()