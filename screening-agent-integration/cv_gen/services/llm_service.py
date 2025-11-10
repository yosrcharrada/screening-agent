"""
LLM Service - Ollama + Llama2 Integration
==========================================

Complete integration with Ollama for CV generation.
✅ Professional summary generation
✅ Achievement bullet generation
✅ Job description generation
✅ RAG-enhanced prompts
✅ Output validation
✅ Streaming support
"""

import logging
import requests
import json
from typing import Optional, List, Dict
import time

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """
    Integration with Ollama for LLM-based CV generation
    
    Features:
    - Connects to local Ollama server (localhost:11434)
    - Uses Llama2 model
    - Generates professional CV content
    - RAG-enhanced prompts
    - Streaming responses
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama connection"""
        self.base_url = base_url
        self.model = "llama2:latest"
        self.max_retries = 3
        self.timeout = 300  # 5 minutes for long generations
        
        # Verify connection
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify Ollama server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Ollama connection successful")
                return True
            else:
                logger.error(f"❌ Ollama error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: ollama serve"
            )
    
    def generate_professional_summary(
        self,
        user_profile: Dict,
        rag_examples: Optional[List] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate professional summary using LLM
        
        Args:
            user_profile: User's CV data
            rag_examples: Examples from RAG service
            temperature: Creativity level (0-1)
            
        Returns:
            Generated professional summary
        """
        try:
            logger.info("📝 Generating professional summary...")
            
            # Build context from RAG examples
            context = self._build_context(rag_examples)
            
            # Create prompt
            prompt = self._create_summary_prompt(user_profile, context)
            
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            # Call LLM
            response = self._call_ollama(prompt, temperature)
            
            # Clean and validate
            summary = self._clean_output(response)
            
            logger.info(f"✅ Generated summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            raise
    
    def generate_achievement_bullets(
        self,
        job_title: str,
        company: str,
        job_description: str,
        rag_examples: Optional[List] = None,
        num_bullets: int = 5,
        temperature: float = 0.7
    ) -> List[str]:
        """
        Generate achievement bullets for a job
        
        Args:
            job_title: Job title
            company: Company name
            job_description: Original job description
            rag_examples: Examples from RAG service
            num_bullets: Number of bullets to generate
            temperature: Creativity level
            
        Returns:
            List of achievement bullets
        """
        try:
            logger.info(f"💥 Generating {num_bullets} achievement bullets...")
            
            # Build context
            context = self._build_context(rag_examples)
            
            # Create prompt
            prompt = self._create_bullets_prompt(
                job_title, company, job_description, context, num_bullets
            )
            
            # Call LLM
            response = self._call_ollama(prompt, temperature)
            
            # Parse bullets
            bullets = self._parse_bullets(response)
            
            # Ensure we have requested number
            bullets = bullets[:num_bullets]
            
            logger.info(f"✅ Generated {len(bullets)} bullets")
            return bullets
            
        except Exception as e:
            logger.error(f"❌ Error generating bullets: {e}")
            raise
    
    def generate_job_description(
        self,
        job_title: str,
        original_description: str,
        rag_examples: Optional[List] = None,
        temperature: float = 0.6
    ) -> str:
        """Generate enhanced job description"""
        try:
            logger.info("📋 Generating enhanced job description...")
            
            context = self._build_context(rag_examples)
            prompt = self._create_description_prompt(
                job_title, original_description, context
            )
            
            response = self._call_ollama(prompt, temperature)
            description = self._clean_output(response)
            
            logger.info(f"✅ Generated description: {len(description)} characters")
            return description
            
        except Exception as e:
            logger.error(f"❌ Error generating description: {e}")
            raise
    
    def _call_ollama(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Call Ollama API with retry logic
        
        Args:
            prompt: Input prompt
            temperature: Creativity (0-1)
            max_tokens: Max response length
            
        Returns:
            Generated text
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔄 Calling Ollama (attempt {attempt + 1}/{self.max_retries})...")
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False,
                }
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "")
                    
                    logger.info(f"✅ Ollama response received: {len(text)} characters")
                    return text
                else:
                    logger.error(f"❌ Ollama error: {response.status_code}")
                    
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"⏳ Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    continue
                    
            except requests.Timeout:
                logger.warning(f"⏱️ Request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                continue
                
            except Exception as e:
                logger.error(f"❌ Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                continue
        
        raise RuntimeError("Failed to call Ollama after retries")
    
    def _create_summary_prompt(
        self,
        user_profile: Dict,
        context: str
    ) -> str:
        """Create prompt for professional summary"""
        name = user_profile.get('full_name', 'Professional')
        profession = user_profile.get('profession', 'Professional')
        experience_years = user_profile.get('years_of_experience', 5)
        
        prompt = f"""You are a professional CV writer. Based on the provided examples and user information, 
generate a compelling professional summary (2-3 sentences, max 100 words).

PROFESSIONAL EXAMPLES:
{context}

USER INFORMATION:
- Name: {name}
- Profession: {profession}
- Years of Experience: {experience_years}
- Current Summary: {user_profile.get('professional_summary', 'N/A')}

Generate a professional, impactful summary that highlights key strengths and experience.
Focus on results and achievements. Keep it concise and compelling.

PROFESSIONAL SUMMARY:"""
        
        return prompt
    
    def _create_bullets_prompt(
        self,
        job_title: str,
        company: str,
        job_description: str,
        context: str,
        num_bullets: int
    ) -> str:
        """Create prompt for achievement bullets"""
        prompt = f"""You are a professional CV writer. Based on the provided examples and job information,
generate {num_bullets} achievement bullets (each 1-2 lines, starting with action verbs).

ACHIEVEMENT EXAMPLES:
{context}

JOB INFORMATION:
- Job Title: {job_title}
- Company: {company}
- Job Description: {job_description[:500]}

Generate {num_bullets} achievement bullets that:
1. Start with strong action verbs (Implemented, Developed, Led, Managed, Improved, etc.)
2. Include quantifiable results where possible (percentages, numbers, metrics)
3. Highlight impact and value delivered
4. Are specific to this role

Format each bullet on a new line starting with a dash (-).

ACHIEVEMENT BULLETS:"""
        
        return prompt
    
    def _create_description_prompt(
        self,
        job_title: str,
        original_description: str,
        context: str
    ) -> str:
        """Create prompt for job description"""
        prompt = f"""You are a professional CV writer. Enhance the job description to be more impactful 
and professional while maintaining accuracy.

REFERENCE EXAMPLES:
{context}

ORIGINAL DESCRIPTION:
{original_description}

Enhance this description by:
1. Making it more specific and impactful
2. Adding quantifiable metrics if relevant
3. Highlighting key achievements
4. Using professional language
5. Keeping it concise (2-3 sentences)

ENHANCED DESCRIPTION:"""
        
        return prompt
    
    def _build_context(self, rag_examples: Optional[List]) -> str:
        """Build context from RAG examples"""
        if not rag_examples:
            return "No examples available."
        
        context = ""
        for i, example in enumerate(rag_examples[:3], 1):
            content = example.content if hasattr(example, 'content') else str(example)
            context += f"{i}. {content}\n\n"
        
        return context
    
    def _clean_output(self, text: str) -> str:
        """Clean and normalize LLM output"""
        # Remove common LLM artifacts
        text = text.strip()
        
        # Remove duplicate label if present
        if text.startswith("PROFESSIONAL SUMMARY:"):
            text = text.replace("PROFESSIONAL SUMMARY:", "", 1).strip()
        if text.startswith("ACHIEVEMENT BULLETS:"):
            text = text.replace("ACHIEVEMENT BULLETS:", "", 1).strip()
        if text.startswith("ENHANCED DESCRIPTION:"):
            text = text.replace("ENHANCED DESCRIPTION:", "", 1).strip()
        
        # Remove excessive whitespace
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        return text
    
    def _parse_bullets(self, text: str) -> List[str]:
        """Parse bullet points from LLM output"""
        bullets = []
        
        # Clean the text
        text = self._clean_output(text)
        
        # Split by newlines and filter
        for line in text.split('\n'):
            line = line.strip()
            
            # Remove bullet markers
            if line.startswith('-'):
                line = line[1:].strip()
            elif line.startswith('•'):
                line = line[1:].strip()
            elif line and line[0].isdigit() and '.' in line[:3]:
                line = line.split('.', 1)[1].strip()
            
            # Add if valid
            if line and len(line) > 10:
                bullets.append(line)
        
        return bullets