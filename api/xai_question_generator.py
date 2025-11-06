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
import shap
import numpy as np
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger(__name__)

class XAIQuestionGenerator:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY environment variable")
        self._initialize_models()
        self.explanation_data = {}

    def _initialize_models(self):
        logger.info("🚀 Initializing Google Gemini LLM and Embeddings models...")
        # Main generator model
        self.generator_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            google_api_key=self.api_key
        )
        
        # Judge model (can be same or different model)
        self.judge_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp", 
            temperature=0.1,  # Lower temperature for more consistent judging
            google_api_key=self.api_key
        )
        
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        logger.info("✅ Models initialized successfully")

    def _extract_key_phrases(self, text: str, max_phrases: int = 20) -> List[str]:
        """Extract key phrases from text for SHAP analysis"""
        # Simple extraction - you can enhance this with NLP libraries
        sentences = re.split(r'[.!?]+', text)
        key_phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum length
                # Extract noun phrases (simple pattern-based)
                words = sentence.split()
                if len(words) >= 3:
                    # Take important phrases (containing key terms)
                    if any(keyword in sentence.lower() for keyword in 
                          ['experience', 'skill', 'developed', 'built', 'managed', 
                           'created', 'implemented', 'led', 'responsible']):
                        key_phrases.append(sentence[:100])  # Limit length
        
        return key_phrases[:max_phrases]

    def _generate_shap_explanations(self, cv_phrases: List[str], jd_phrases: List[str], 
                                  questions: List[Dict]) -> Dict[str, Any]:
        """Generate SHAP-like explanations for question generation"""
        explanations = {}
        
        for i, question in enumerate(questions):
            question_text = question.get('question', '')
            target_skill = question.get('target_skill', '').lower()
            skill_type = question.get('skill_type', '')
            
            # Calculate influence scores based on keyword matching
            cv_influences = {}
            jd_influences = {}
            
            # Analyze CV influence
            for phrase in cv_phrases:
                phrase_lower = phrase.lower()
                score = 0
                
                # Skill mention in CV
                if target_skill in phrase_lower:
                    score += 3
                
                # Contextual relevance
                if any(context in phrase_lower for context in 
                      ['experience', 'project', 'work', 'role']):
                    score += 1
                
                if score > 0:
                    cv_influences[phrase] = score
            
            # Analyze JD influence
            for phrase in jd_phrases:
                phrase_lower = phrase.lower()
                score = 0
                
                # Direct requirement match
                if target_skill in phrase_lower:
                    score += 3
                
                # Job context relevance
                if any(context in phrase_lower for context in 
                      ['required', 'must have', 'looking for', 'qualifications']):
                    score += 2
                
                if score > 0:
                    jd_influences[phrase] = score
            
            explanations[f"question_{i+1}"] = {
                'question': question_text,
                'cv_influences': dict(sorted(cv_influences.items(), 
                                           key=lambda x: x[1], reverse=True)[:3]),
                'jd_influences': dict(sorted(jd_influences.items(), 
                                           key=lambda x: x[1], reverse=True)[:3]),
                'primary_drivers': self._identify_primary_drivers(cv_influences, jd_influences)
            }
        
        return explanations

    def _identify_primary_drivers(self, cv_influences: Dict, jd_influences: Dict) -> List[str]:
        """Identify primary drivers for question generation"""
        drivers = []
        
        if cv_influences:
            top_cv = max(cv_influences.items(), key=lambda x: x[1]) if cv_influences else None
            if top_cv:
                drivers.append(f"CV experience: '{top_cv[0][:50]}...'")
        
        if jd_influences:
            top_jd = max(jd_influences.items(), key=lambda x: x[1]) if jd_influences else None
            if top_jd:
                drivers.append(f"JD requirement: '{top_jd[0][:50]}...'")
        
        return drivers

    def _generate_chain_of_thought(self, cv_text: str, jd_text: str, 
                                 skill_gap_analysis: Dict) -> str:
        """Generate chain-of-thought reasoning for question generation"""
        cot_prompt = f"""
        Generate interview questions by following this reasoning chain step by step:

        STEP 1: ANALYZE SKILL GAPS
        - Matched skills: {skill_gap_analysis.get('matched_skills', [])}
        - Missing skills: {skill_gap_analysis.get('missing_skills', [])}
        - Match percentage: {skill_gap_analysis.get('match_percentage', 0)}%

        STEP 2: IDENTIFY ASSESSMENT PRIORITIES
        - Which matched skills are most critical for this role?
        - Which missing skills are most important to develop?
        - What behavioral competencies are needed?

        STEP 3: SELECT QUESTION TYPES
        - Behavioral questions for experience validation
        - Technical questions for matched skills
        - Situational questions for missing skills

        STEP 4: GENERATE SPECIFIC QUESTIONS
        - Ensure coverage across different skill types
        - Balance difficulty levels
        - Focus on practical application

        Now generate the actual questions based on this reasoning.
        """
        
        return cot_prompt

    def _llm_judge_questions(self, questions: List[Dict], cv_text: str, 
                           jd_text: str, skill_gap_analysis: Dict) -> Dict:
        """Use LLM as judge to evaluate generated questions"""
        
        judge_prompt = f"""
        You are an expert HR interviewer and technical assessor. Evaluate the following interview questions based on these criteria:

        EVALUATION CRITERIA:
        1. RELEVANCE (1-10): How well does the question match the CV and JD?
        2. ASSESSMENT_VALUE (1-10): How effectively does it assess the target skill?
        3. DIFFICULTY_APPROPRIATENESS (1-10): Is the difficulty level suitable?
        4. BIAS_POTENTIAL (1-10): Low score indicates potential bias (1=high bias, 10=no bias)
        5. COVERAGE (1-10): How well does it cover the skill gap analysis?

        CONTEXT:
        - CV Skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('matched_skills', [])]}
        - Missing Skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('missing_skills', [])]}
        - Job Role: Based on JD requirements

        QUESTIONS TO EVALUATE:
        {json.dumps(questions, indent=2)}

        Provide your evaluation in this exact JSON format:
        {{
            "overall_score": 85,
            "question_evaluations": [
                {{
                    "question_index": 0,
                    "relevance_score": 9,
                    "assessment_value_score": 8,
                    "difficulty_score": 7,
                    "bias_score": 9,
                    "coverage_score": 8,
                    "strengths": ["Good technical focus", "Relevant to role"],
                    "improvements": ["Could be more specific", "Add follow-up potential"],
                    "verdict": "APPROVED"
                }}
            ],
            "coverage_analysis": {{
                "well_covered_skills": ["python", "django"],
                "missing_coverage": ["aws", "leadership"],
                "recommendations": ["Add AWS scenario question", "Include leadership behavioral question"]
            }}
        }}
        """

        try:
            response = self.judge_llm.invoke(judge_prompt)
            generated_text = response.content
            
            # Clean the response
            cleaned_text = re.sub(r'```json\s*|\s*```', '', generated_text).strip()
            evaluation = json.loads(cleaned_text)
            
            logger.info(f"✅ Judge evaluation completed. Overall score: {evaluation.get('overall_score', 0)}")
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Judge evaluation failed: {e}")
            return self._generate_fallback_judgment(questions)

    def _generate_fallback_judgment(self, questions: List[Dict]) -> Dict:
        """Fallback judgment if LLM judge fails"""
        return {
            "overall_score": 75,
            "question_evaluations": [
                {
                    "question_index": i,
                    "relevance_score": 7,
                    "assessment_value_score": 7,
                    "difficulty_score": 6,
                    "bias_score": 8,
                    "coverage_score": 7,
                    "strengths": ["Relevant to general interview context"],
                    "improvements": ["Could be more specific to candidate"],
                    "verdict": "APPROVED"
                } for i in range(len(questions))
            ],
            "coverage_analysis": {
                "well_covered_skills": ["general_skills"],
                "missing_coverage": ["specific_domain_skills"],
                "recommendations": ["Add more role-specific questions"]
            }
        }

    def _generate_questions_with_llm(self, cv_text: str, jd_text: str, 
                                   skill_gap_analysis: Dict, num_questions: int) -> List[Dict]:
        """Use your existing question generation logic with enhanced XAI explanations"""
        
        matched = [s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get("matched_skills", [])]
        missing = [s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get("missing_skills", [])]

        prompt_text = f'''
    You are an expert HR strategist and senior technical interviewer. Based on the comprehensive analysis below,
    generate exactly {num_questions} highly strategic interview questions in JSON format.

    ENHANCED QUESTION STRUCTURE - EACH QUESTION MUST INCLUDE:
    - "question": Strategic interview question text
    - "focus": Primary assessment area (behavioral_strategic, technical_architecture, situational_leadership, technical_depth, business_alignment)
    - "explanation": Detailed strategic explanation object with:
      - "reason": EXTREMELY DETAILED strategic reasoning (4-6 sentences minimum with specific business impact)
      - "source_skills": List of relevant skills from CV/JD analysis
      - "relevance_score": Float between 0.8-0.95 (high relevance expected)
      - "evidence_from_cv": Specific CV experience reference
      - "evidence_from_jd": Specific JD requirement reference
      - "strategic_importance": High/Medium/Low business impact
      - "assessment_depth": Basic/Intermediate/Advanced/Expert level
    - "skill_type": "matched_skill", "missing_skill", or "strategic_potential"
    - "target_skill": Specific competency being assessed
    - "model_answer": A well-structured model answer using STAR method (Situation, Task, Action, Result)
    - "answer_hints": 3-5 strategic answering hints
    - "key_points": Critical evaluation criteria

    STRATEGIC CONTEXT:
    Matched Skills for Validation: {", ".join(matched[:5])}
    Development Areas to Assess: {", ".join(missing[:3])}
    Overall Skill Alignment: {skill_gap_analysis.get('match_percentage', 0)}%

    Candidate Profile Context:
    {cv_text[:1200]}...

    Job Requirements Context:
    {jd_text[:1200]}...

    CRITICAL: Ensure "reason" fields are EXTREMELY DETAILED and STRATEGIC, focusing on:
    - Specific business impact and organizational value
    - Technical competencies being assessed
    - Behavioral indicators being evaluated  
    - Strategic decision-making capabilities
    - Risk mitigation and validation approach

    Return ONLY valid JSON array format with proper double quotes and escaping.
    '''

        try:
            response = self.generator_llm.invoke(prompt_text)
            generated_text = response.content
            
            # Clean the response
            cleaned_text = re.sub(r'```json\s*|\s*```', '', generated_text).strip()
            questions_data = json.loads(cleaned_text)
            
            # Ensure we have the right number of questions
            if len(questions_data) > num_questions:
                questions_data = questions_data[:num_questions]
                
            return questions_data
            
        except Exception as e:
            logger.error(f"❌ Question generation failed: {e}")
            # Use your existing fallback
            return self._generate_fallback_questions(matched, missing, num_questions)

    def _generate_fallback_questions(self, matched_skills, missing_skills, num_questions):
        """Your existing fallback method with enhanced explanations"""
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
                    "explanation": {
                        "reason": f"Assessing depth of experience with {skill} which matches the job requirements",
                        "source_skills": [skill],
                        "relevance_score": 0.8,
                        "evidence_from_cv": f"CV mentions experience with {skill}",
                        "evidence_from_jd": f"JD requires proficiency in {skill}",
                        "xai_method": "fallback generation"
                    },
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
                    "explanation": {
                        "reason": f"Exploring willingness to learn missing skill {skill}",
                        "source_skills": [skill],
                        "relevance_score": 0.7,
                        "evidence_from_cv": f"CV does not mention {skill} experience",
                        "evidence_from_jd": f"JD requires {skill} proficiency",
                        "xai_method": "fallback generation"
                    },
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
                "explanation": {
                    "reason": "Assessing problem-solving and project management skills",
                    "source_skills": ["problem_solving", "project_management"],
                    "relevance_score": 0.9,
                    "evidence_from_cv": "General behavioral assessment",
                    "evidence_from_jd": "General competency evaluation",
                    "xai_method": "fallback generation"
                },
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
        
        logger.info(f"🔄 Generated {len(questions)} fallback questions with enhanced explanations")
        return questions[:num_questions]

    def generate_interview_questions_with_xai(self, cv_text: str, jd_text: str, 
                                            skill_gap_analysis: Dict, num_questions: int = 6) -> Dict[str, Any]:
        """Generate questions with XAI explanations and LLM judging"""
        
        logger.info("🧠 Starting XAI-enhanced question generation")
        
        # Extract key phrases for explanation
        cv_phrases = self._extract_key_phrases(cv_text[:2000])  # Limit for efficiency
        jd_phrases = self._extract_key_phrases(jd_text[:2000])
        
        # Generate chain of thought
        chain_of_thought = self._generate_chain_of_thought(cv_text, jd_text, skill_gap_analysis)
        
        # Generate questions using enhanced method
        questions = self._generate_questions_with_llm(cv_text, jd_text, skill_gap_analysis, num_questions)
        
        # Generate SHAP explanations for additional insights
        shap_explanations = self._generate_shap_explanations(cv_phrases, jd_phrases, questions)
        
        # LLM Judge evaluation
        judge_evaluation = self._llm_judge_questions(questions, cv_text, jd_text, skill_gap_analysis)
        
        # Compile comprehensive XAI report
        xai_report = {
            "generation_process": {
                "chain_of_thought": chain_of_thought,
                "skill_gap_analysis_used": {
                    "matched_skills": skill_gap_analysis.get('matched_skills', []),
                    "missing_skills": skill_gap_analysis.get('missing_skills', []),
                    "match_percentage": skill_gap_analysis.get('match_percentage', 0)
                }
            },
            "explanations": shap_explanations,
            "quality_assurance": judge_evaluation,
            "confidence_metrics": {
                "generation_confidence": self._calculate_confidence(questions, judge_evaluation),
                "coverage_completeness": self._calculate_coverage(questions, skill_gap_analysis),
                "relevance_score": judge_evaluation.get('overall_score', 0)
            }
        }
        
        logger.info("✅ XAI-enhanced generation completed")
        
        return {
            "questions": questions,
            "xai_report": xai_report,
            "generation_metadata": {
                "total_questions": len(questions),
                "judge_score": judge_evaluation.get('overall_score', 0),
                "has_explanations": True,
                "generation_method": "xai_enhanced_with_judge"
            }
        }

    def _calculate_confidence(self, questions: List[Dict], judge_evaluation: Dict) -> float:
        """Calculate overall confidence score"""
        if not judge_evaluation.get('question_evaluations'):
            return 0.7  # Default confidence
        
        scores = [q.get('relevance_score', 5) for q in judge_evaluation['question_evaluations']]
        return sum(scores) / (len(scores) * 10)  # Normalize to 0-1

    def _calculate_coverage(self, questions: List[Dict], skill_gap_analysis: Dict) -> float:
        """Calculate how well questions cover the skill gaps"""
        all_skills = set()
        
        # Get all skills from gap analysis
        for skill_list in ['matched_skills', 'missing_skills']:
            for skill in skill_gap_analysis.get(skill_list, []):
                if isinstance(skill, dict):
                    all_skills.add(skill['skill'].lower())
                else:
                    all_skills.add(skill.lower())
        
        # Get skills covered by questions
        covered_skills = set()
        for question in questions:
            target_skill = question.get('target_skill', '').lower()
            if target_skill:
                covered_skills.add(target_skill)
        
        if not all_skills:
            return 1.0
        
        return len(covered_skills) / len(all_skills)

    def generate_explanation_visualization(self, xai_report: Dict) -> str:
        """Generate visualization data for explanations"""
        # This can be extended to create actual charts
        # For now, return structured data for frontend visualization
        
        visualization_data = {
            "confidence_score": xai_report["confidence_metrics"]["generation_confidence"],
            "coverage_score": xai_report["confidence_metrics"]["coverage_completeness"],
            "judge_score": xai_report["quality_assurance"].get("overall_score", 0) / 100,
            "question_breakdown": []
        }
        
        for q_key, explanation in xai_report["explanations"].items():
            visualization_data["question_breakdown"].append({
                "question": explanation["question"],
                "cv_influence_strength": len(explanation["cv_influences"]),
                "jd_influence_strength": len(explanation["jd_influences"]),
                "primary_drivers": explanation["primary_drivers"]
            })
        
        return json.dumps(visualization_data)
    
    def _generate_detailed_reasoning(self, question: Dict, cv_text: str, jd_text: str, 
                               skill_gap_analysis: Dict) -> str:
        """Generate highly detailed strategic reasoning for question selection"""
    
        reasoning_prompt = f"""
        As a Chief HR Strategist and Senior Technical Interviewer, provide an EXTREMELY DETAILED 
        and STRATEGICALLY SOPHISTICATED explanation for why this specific interview question 
        was formulated and selected for this candidate.

        CANDIDATE CONTEXT:
        CV Excerpt: "{cv_text[:800]}"
    
        JOB REQUIREMENTS:
        JD Excerpt: "{jd_text[:800]}"
    
        SKILL LANDSCAPE ANALYSIS:
    - Matched Skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('matched_skills', [])][:5]}
    - Missing Skills: {[s['skill'] if isinstance(s, dict) else s for s in skill_gap_analysis.get('missing_skills', [])][:5]}
    - Alignment Score: {skill_gap_analysis.get('match_percentage', 0)}%

    QUESTION TO ANALYZE:
    "{question.get('question', '')}"
    
    Question Focus: {question.get('focus', 'N/A')}
    Target Skill: {question.get('target_skill', 'N/A')}
    Skill Type: {question.get('skill_type', 'N/A')}

    PROVIDE A COMPREHENSIVE STRATEGIC ANALYSIS COVERING:

    1. STRATEGIC SELECTION RATIONALE
       - Why this EXACT question formulation was chosen over alternatives
       - How it addresses specific organizational transformation priorities
       - The strategic business objectives it serves
       - Risk mitigation approach embedded in the question design

    2. COMPETENCY ASSESSMENT DEPTH
       - Technical competencies evaluated and assessment methodology
       - Behavioral indicators and soft skills being probed
       - Cognitive abilities and problem-solving patterns assessed
       - Leadership potential and strategic thinking evaluation

    3. EVIDENCE-BASED CONNECTIONS
       - Specific CV experiences that influenced question formulation
       - Direct JD requirements being validated through this question
       - Skill gap mitigation strategy embedded in the assessment

    CRITICAL REQUIREMENTS:
    - Be EXTREMELY DETAILED and SPECIFIC (4-6 sentences minimum)
    - Focus on BUSINESS IMPACT and STRATEGIC VALUE
    - Connect to ORGANIZATIONAL OBJECTIVES
    - Provide CONCRETE EXAMPLES and RATIONALE
    - Use PROFESSIONAL HR and TECHNICAL terminology

    Return ONLY the detailed reasoning text, no JSON formatting.
    """

        try:
            response = self.reasoning_llm.invoke(reasoning_prompt)
            reasoning_text = response.content.strip()
        
        # Ensure minimum length and quality
            if len(reasoning_text.split()) < 40:
                return self._generate_fallback_detailed_reasoning(question)
            
            return reasoning_text
        
        except Exception as e:
            logger.error(f"❌ Detailed reasoning generation failed: {e}")
            return self._generate_fallback_detailed_reasoning(question)

    def _generate_fallback_detailed_reasoning(self, question: Dict) -> str:
        """Fallback detailed reasoning with strategic depth"""
        target_skill = question.get('target_skill', 'technical_problem_solving')
        focus = question.get('focus', 'behavioral')
    
        reasoning_templates = {
        'technical_architecture': """
        This question was strategically formulated to evaluate the candidate's architectural decision-making capabilities at a senior engineering level. It specifically assesses their ability to balance technical constraints with business objectives, a critical competency for leadership roles in software architecture. The formulation tests for systems thinking, risk assessment, and stakeholder management skills that are essential for driving organizational technical strategy. By requiring discussion of trade-offs and long-term implications, it reveals the candidate's prioritization framework and strategic alignment capabilities. This approach validates not just technical knowledge but the maturity to make architecture decisions that serve both immediate business needs and future scalability requirements.
        """,
        
        'behavioral_leadership': """
        This behavioral question was carefully designed to assess leadership competencies and decision-making patterns in complex organizational contexts. It evaluates the candidate's ability to navigate ambiguity, influence stakeholders, and drive outcomes through collaborative leadership. The scenario-based formulation tests for emotional intelligence, strategic communication, and change management capabilities that are critical for senior roles. By examining past experiences, we can predict future leadership behaviors and cultural fit within the organization's transformation journey.
        """,
        
        'technical_problem_solving': """
        This technical question was strategically selected to evaluate the candidate's problem-solving methodology and technical depth. It assesses their approach to complex technical challenges, analytical thinking patterns, and solution design capabilities. The formulation specifically tests for systematic problem decomposition, technical trade-off analysis, and innovation potential. By examining their reasoning process and solution architecture, we gain insights into their technical maturity and ability to deliver scalable, maintainable solutions.
        """,
        
        'situational_strategic': """
        This situational question was designed to assess strategic thinking and business alignment capabilities. It evaluates how the candidate approaches complex business scenarios, balances competing priorities, and makes decisions with long-term implications. The formulation tests for commercial awareness, risk assessment, and value-based decision making that are essential for roles with strategic impact. By examining their reasoning framework and decision rationale, we can assess their potential to contribute to organizational growth and transformation.
        """
    }
    
        if 'architect' in target_skill.lower() or 'architecture' in target_skill.lower():
            template_key = 'technical_architecture'
        elif 'leadership' in target_skill.lower() or 'management' in target_skill.lower():
            template_key = 'behavioral_leadership'
        elif 'strategic' in target_skill.lower() or 'business' in target_skill.lower():
            template_key = 'situational_strategic'
        else:
            template_key = 'technical_problem_solving'
        
        return reasoning_templates[template_key].strip()

# Instantiate for reuse
xai_question_generator = XAIQuestionGenerator()