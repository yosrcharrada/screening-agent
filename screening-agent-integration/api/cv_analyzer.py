# cv_analyzer.py - USING LANGCHAIN WITH GEMINI 2.0 FLASH
import logging
import json
import re
import random
from typing import Dict, List, Any
import os
from datetime import datetime

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain-google-genai")

logger = logging.getLogger(__name__)

class CVAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyAERIkxZZS8jXsMG74UhZvEwCL9fWNIBw8')
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    temperature=0.7,
                    google_api_key=self.api_key
                )
                self.langchain_available = True
                logger.info("LangChain with Gemini 2.0 Flash initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LangChain: {e}")
                self.langchain_available = False
        else:
            self.langchain_available = False
            logger.warning("LangChain not available or API key missing")
        
    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Use Gemini 2.0 Flash via LangChain for CV analysis
        """
        logger.info("Starting CV analysis with Gemini 2.0 Flash...")
        
        # Try LangChain with Gemini first
        if self.langchain_available:
            gemini_result = self._try_langchain_gemini(cv_text)
            if gemini_result:
                logger.info("Successfully got Gemini 2.0 Flash analysis via LangChain")
                return gemini_result
        
        # Fallback to intelligent analysis
        logger.info("Using intelligent fallback analysis")
        return self._create_intelligent_fallback(cv_text)
    
    def _try_langchain_gemini(self, cv_text: str) -> Dict[str, Any]:
        """
        Use LangChain with Gemini 2.0 Flash Experimental
        """
        try:
            prompt = self._create_langchain_prompt(cv_text)
            
            messages = [
                SystemMessage(content="You are an expert CV consultant with 15+ years experience in tech recruitment."),
                HumanMessage(content=prompt)
            ]
            
            logger.info("Sending request to Gemini 2.0 Flash via LangChain...")
            response = self.llm.invoke(messages)
            
            if response and hasattr(response, 'content'):
                content = response.content
                logger.info(f"Gemini 2.0 Flash response received: {len(content)} characters")
                return self._parse_gemini_response(content, cv_text)
            else:
                logger.error("No content in Gemini response")
                
        except Exception as e:
            logger.error(f"LangChain Gemini failed: {str(e)}")
            
        return None
    
    def _create_langchain_prompt(self, cv_text: str) -> str:
        """Create optimized prompt for LangChain with Gemini"""
        return f"""
        You are an expert CV consultant specializing in technology professionals. 
        Analyze the following CV in extreme detail and provide highly specific, actionable feedback , all the recommendations ,all the ares of improvements and all the strengths.

        CRITICAL REQUIREMENTS:
        - Be EXTREMELY specific to the ACTUAL content of this CV
        - Reference exact technologies, projects, experiences, and achievements mentioned
        - Provide feedback that ONLY applies to this specific CV
        - Do NOT use generic phrases that could apply to any CV
        - Score realistically based on actual content quality (5-9 range)
        - Focus on actionable improvements with clear examples

        CV CONTENT TO ANALYZE:
        {cv_text[:3500]}

        Provide your analysis in this EXACT JSON format:

        {{
            "overall_score": "realistic_score/10",
            "strengths": [
                "specific strength mentioning actual technologies or experiences from CV",
                "specific strength about content quality or structure", 
                "specific strength about skills or achievements"
            ],
            "weaknesses": [
                "specific weakness with concrete examples from CV",
                "specific area needing improvement with references to actual content"
            ],
            "recommendations": [
                "highly specific, actionable recommendation tied to CV content",
                "concrete suggestion with examples of how to implement",
                "specific improvement that addresses actual gaps found"
            ],
            "content_analysis": {{
                "clarity": "specific assessment of writing clarity based on actual text",
                "relevance": "assessment of relevance for the roles/technologies mentioned", 
                "achievements": "detailed evaluation of achievement presentation quality",
                "uniqueness": "what makes this CV unique based on its actual content"
            }},
            "skill_analysis": {{
                "technical_skills": "detailed assessment of technical skills mentioned",
                "soft_skills": "evaluation of soft skills presentation", 
                "skill_gaps": "specific skill gaps identified from content",
                "skill_strengths": "particular technical strengths found"
            }},
            "formatting_analysis": {{
                "readability": "specific readability assessment with examples",
                "structure": "evaluation of CV structure and organization",
                "professionalism": "assessment of professional presentation"
            }},
            "key_insights": [
                "unique insight specific to this CV's content",
                "observation about career trajectory or specialization",
                "notable pattern or standout feature in CV"
            ]
        }}

        IMPORTANT: 
        - If you see Python, Django, AWS, or other specific technologies, mention them by name
        - If you see leadership experience, quantify it specifically
        - If you see projects or achievements, reference them directly
        - Be brutally honest and constructive
        - Provide feedback that would only make sense for THIS specific CV
        """
    
    def _parse_gemini_response(self, content: str, cv_text: str) -> Dict[str, Any]:
        """Parse Gemini response from LangChain"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # Clean common JSON issues
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r'\\"', '"', json_str)
                
                gemini_data = json.loads(json_str)
                
                # Enhance with metadata
                enhanced_data = self._enhance_gemini_data(gemini_data, cv_text)
                return enhanced_data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Problematic content: {content[:500]}...")
        
        # If JSON parsing fails, structure the text response
        return self._structure_text_response(content, cv_text)
    
    def _enhance_gemini_data(self, gemini_data: Dict[str, Any], cv_text: str) -> Dict[str, Any]:
        """Enhance and validate Gemini data"""
        enhanced = {
            "overall_score": gemini_data.get('overall_score', str(self._calculate_fallback_score(cv_text))),
            "strengths": self._ensure_array(gemini_data.get('strengths'), [
                "Professional content quality and structure",
                "Clear career progression information"
            ]),
            "weaknesses": self._ensure_array(gemini_data.get('weaknesses'), [
                "Opportunity for more specific achievement quantification"
            ]),
            "recommendations": self._ensure_array(gemini_data.get('recommendations'), [
                "Add specific metrics to key achievements",
                "Enhance project descriptions with technical details",
                "Highlight leadership experience with team sizes"
            ]),
            "content_analysis": {
                "clarity": gemini_data.get('content_analysis', {}).get('clarity', "Clear professional writing style"),
                "relevance": gemini_data.get('content_analysis', {}).get('relevance', "Relevant for technical roles"), 
                "achievements": gemini_data.get('content_analysis', {}).get('achievements', "Good achievement foundation"),
                "uniqueness": gemini_data.get('content_analysis', {}).get('uniqueness', "Unique professional background")
            },
            "skill_analysis": {
                "technical_skills": gemini_data.get('skill_analysis', {}).get('technical_skills', "Solid technical foundation"),
                "soft_skills": gemini_data.get('skill_analysis', {}).get('soft_skills', "Good interpersonal skills"),
                "skill_gaps": gemini_data.get('skill_analysis', {}).get('skill_gaps', "Opportunities for skill expansion"),
                "skill_strengths": gemini_data.get('skill_analysis', {}).get('skill_strengths', "Strong core competencies")
            },
            "formatting_analysis": {
                "readability": gemini_data.get('formatting_analysis', {}).get('readability', "Generally readable format"),
                "structure": gemini_data.get('formatting_analysis', {}).get('structure', "Good structural organization"),
                "professionalism": gemini_data.get('formatting_analysis', {}).get('professionalism', "Professional presentation")
            },
            "key_insights": self._ensure_array(gemini_data.get('key_insights'), [
                "Good foundation with specific enhancement opportunities",
                "Well-positioned for technical role applications"
            ]),
            "analysis_source": "gemini_2.0_flash_langchain",
            "analysis_timestamp": datetime.now().isoformat(),
            "content_preview": cv_text[:200] + "..." if len(cv_text) > 200 else cv_text,
            "model_used": "gemini-2.0-flash-exp",
            "ai_generated": True
        }
        
        return enhanced
    
    def _structure_text_response(self, text: str, cv_text: str) -> Dict[str, Any]:
        """Structure text response when JSON parsing fails"""
        logger.info("Structuring text response from Gemini")
        
        # Extract information from text
        analysis = self._analyze_response_text(text)
        
        return {
            "overall_score": analysis.get('score', '7'),
            "strengths": analysis.get('strengths', ["Professional CV with good structure"]),
            "weaknesses": analysis.get('weaknesses', ["Opportunity to enhance specific achievements"]),
            "recommendations": analysis.get('recommendations', [
                "Add quantifiable metrics to achievements",
                "Enhance technical skill descriptions",
                "Improve project documentation"
            ]),
            "content_analysis": {
                "clarity": analysis.get('clarity', "Clear and professional writing"),
                "relevance": analysis.get('relevance', "Relevant for target roles"), 
                "achievements": analysis.get('achievements', "Good achievement foundation"),
                "uniqueness": analysis.get('uniqueness', "Unique professional elements")
            },
            "skill_analysis": {
                "technical_skills": analysis.get('technical_skills', "Solid technical skills"),
                "soft_skills": analysis.get('soft_skills', "Good soft skills presentation"),
                "skill_gaps": analysis.get('skill_gaps', "Some skill enhancement opportunities"),
                "skill_strengths": analysis.get('skill_strengths', "Strong core competencies")
            },
            "formatting_analysis": {
                "readability": analysis.get('readability', "Generally good readability"),
                "structure": analysis.get('structure', "Well-structured format"),
                "professionalism": analysis.get('professionalism', "Professional presentation")
            },
            "key_insights": analysis.get('insights', [
                "Good potential for specific enhancements",
                "Solid foundation for technical roles"
            ]),
            "analysis_source": "gemini_2.0_flash_text",
            "analysis_timestamp": datetime.now().isoformat(),
            "content_preview": cv_text[:200] + "..." if len(cv_text) > 200 else cv_text,
            "model_used": "gemini-2.0-flash-exp",
            "ai_generated": True
        }
    
    def _analyze_response_text(self, text: str) -> Dict[str, Any]:
        """Analyze text response from Gemini"""
        analysis = {}
        
        # Extract score
        score_match = re.search(r'(\d+)(?:\s*\/\s*10)?|score.*?(\d+)', text.lower())
        analysis['score'] = score_match.group(1) or score_match.group(2) if score_match else '7'
        
        # Extract sections
        sections = self._extract_sections_from_text(text)
        analysis.update(sections)
        
        return analysis
    
    def _extract_sections_from_text(self, text: str) -> Dict[str, Any]:
        """Extract sections from text response"""
        sections = {}
        
        section_patterns = {
            'strengths': r'(?:strengths?|positives?).*?[:\n](.*?)(?=weaknesses|improvements|recommendations|$)',
            'weaknesses': r'(?:weaknesses?|improvements?).*?[:\n](.*?)(?=strengths|recommendations|$)',
            'recommendations': r'(?:recommendations?|suggestions?).*?[:\n](.*?)(?=strengths|weaknesses|$)'
        }
        
        text_lower = text.lower()
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                items = self._extract_items(content)
                if items:
                    sections[section] = items
        
        return sections
    
    def _extract_items(self, text: str) -> List[str]:
        """Extract items from text"""
        items = []
        
        # Multiple extraction strategies
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines and very short lines
            if line and len(line) > 15:
                # Remove bullet points and numbers
                clean_line = re.sub(r'^[•\-*\d\.\s]+', '', line)
                if clean_line and len(clean_line) > 10:
                    items.append(clean_line)
        
        return items[:4] if items else []
    
    def _ensure_array(self, value: Any, default: List[str]) -> List[str]:
        """Ensure value is a proper array"""
        if isinstance(value, list) and len(value) > 0:
            return value
        return default
    
    def _calculate_fallback_score(self, cv_text: str) -> int:
        """Calculate fallback score based on content quality"""
        cv_lower = cv_text.lower()
        
        score = 6
        if len(cv_text) > 1200:
            score += 1
        if any(tech in cv_lower for tech in ['python', 'django', 'aws', 'docker']):
            score += 1
        if len(re.findall(r'\d+%|\$\d+', cv_text)) >= 2:
            score += 1
        
        return min(9, max(5, score))
    
    def _create_intelligent_fallback(self, cv_text: str) -> Dict[str, Any]:
        """
        High-quality fallback when Gemini fails
        """
        cv_lower = cv_text.lower()
        
        # Analyze content
        analysis = self._analyze_content_intelligently(cv_text, cv_lower)
        
        return {
            "overall_score": str(analysis['score']),
            "strengths": analysis['strengths'],
            "weaknesses": analysis['weaknesses'],
            "recommendations": analysis['recommendations'],
            "content_analysis": {
                "clarity": analysis['clarity'],
                "relevance": analysis['relevance'], 
                "achievements": analysis['achievements'],
                "uniqueness": analysis['uniqueness']
            },
            "skill_analysis": {
                "technical_skills": analysis['technical_skills'],
                "soft_skills": analysis['soft_skills'],
                "skill_gaps": analysis['skill_gaps'],
                "skill_strengths": analysis['skill_strengths']
            },
            "formatting_analysis": {
                "readability": analysis['readability'],
                "structure": analysis['structure'],
                "professionalism": analysis['professionalism']
            },
            "key_insights": analysis['insights'],
            "analysis_source": "intelligent_fallback",
            "analysis_timestamp": datetime.now().isoformat(),
            "content_preview": cv_text[:200] + "..." if len(cv_text) > 200 else cv_text,
            "model_used": "fallback_analysis",
            "ai_generated": False
        }
    
    def _analyze_content_intelligently(self, cv_text: str, cv_lower: str) -> Dict[str, Any]:
        """Intelligent content analysis"""
        # Simple technology analysis
        technologies = []
        tech_keywords = ['python', 'django', 'aws', 'docker', 'javascript', 'react', 'java', 'sql']
        for tech in tech_keywords:
            if tech in cv_lower:
                technologies.append(tech)
        
        # Basic metrics
        word_count = len(cv_text.split())
        bullet_count = cv_text.count('•') + cv_text.count('- ')
        achievement_count = len(re.findall(r'\d+%|\$\d+', cv_text))
        
        return {
            'score': self._calculate_intelligent_score(technologies, word_count, bullet_count, achievement_count),
            'strengths': self._generate_intelligent_strengths(technologies, word_count, cv_text),
            'weaknesses': self._generate_intelligent_weaknesses(technologies, bullet_count, achievement_count),
            'recommendations': self._generate_intelligent_recommendations(technologies, achievement_count),
            'clarity': "Very clear" if word_count > 1000 else "Clear" if word_count > 500 else "Generally clear",
            'relevance': "Highly relevant" if len(technologies) >= 3 else "Relevant",
            'achievements': "Strong" if achievement_count >= 3 else "Good" if achievement_count >= 1 else "Needs improvement",
            'uniqueness': "Unique combination of skills" if len(technologies) >= 4 else "Good professional background",
            'technical_skills': f"Strong in {', '.join(technologies[:3])}" if technologies else "Good technical foundation",
            'soft_skills': "Well demonstrated" if any(skill in cv_lower for skill in ['communication', 'leadership', 'teamwork']) else "Good indication",
            'skill_gaps': "Opportunity to expand" if len(technologies) < 5 else "Well-rounded",
            'skill_strengths': f"Expertise in {', '.join(technologies[:2])}" if technologies else "Solid core skills",
            'readability': "Excellent" if bullet_count >= 8 else "Good" if bullet_count >= 4 else "Needs improvement",
            'structure': "Professional" if any(section in cv_lower for section in ['experience', 'education', 'skills']) else "Good",
            'professionalism': "Highly professional",
            'insights': [
                f"Strong foundation in {len(technologies)} technologies" if technologies else "Good professional foundation",
                "Opportunity to enhance quantitative achievements" if achievement_count < 3 else "Good achievement documentation"
            ]
        }
    
    def _calculate_intelligent_score(self, technologies: List[str], word_count: int, bullet_count: int, achievement_count: int) -> int:
        """Calculate intelligent score"""
        score = 6
        
        if len(technologies) >= 3:
            score += 1
        if word_count > 800:
            score += 1
        if bullet_count >= 5:
            score += 1
        if achievement_count >= 2:
            score += 1
        
        return min(9, max(5, score))
    
    def _generate_intelligent_strengths(self, technologies: List[str], word_count: int, cv_text: str) -> List[str]:
        """Generate intelligent strengths"""
        strengths = []
        
        if technologies:
            strengths.append(f"Strong technical skills in {', '.join(technologies[:3])}")
        
        if word_count > 1000:
            strengths.append("Comprehensive and detailed professional background")
        
        if any(term in cv_text.lower() for term in ['led', 'managed', 'directed']):
            strengths.append("Clear leadership and management experience")
        
        return strengths if strengths else ["Professional presentation with clear information"]
    
    def _generate_intelligent_weaknesses(self, technologies: List[str], bullet_count: int, achievement_count: int) -> List[str]:
        """Generate intelligent weaknesses"""
        weaknesses = []
        
        if achievement_count < 2:
            weaknesses.append("Limited quantifiable achievements - add specific metrics")
        
        if bullet_count < 5:
            weaknesses.append("Could benefit from more bullet points for better readability")
        
        if len(technologies) < 2:
            weaknesses.append("Opportunity to showcase more technical skills")
        
        return weaknesses if weaknesses else ["Opportunity to enhance specific accomplishments"]
    
    def _generate_intelligent_recommendations(self, technologies: List[str], achievement_count: int) -> List[str]:
        """Generate intelligent recommendations"""
        recommendations = [
            "Add 2-3 quantifiable achievements with specific numbers and percentages",
            "Use bullet points consistently throughout role descriptions",
            "Highlight key projects and their business impact"
        ]
        
        if 'python' in technologies:
            recommendations.append("Showcase specific Python projects or contributions")
        
        if 'aws' in technologies:
            recommendations.append("Detail specific AWS services and architectures used")
        
        if achievement_count < 2:
            recommendations.append("Use the STAR method (Situation, Task, Action, Result) for achievements")
        
        return recommendations

# Create the instance for import
cv_analyzer = CVAnalyzer()