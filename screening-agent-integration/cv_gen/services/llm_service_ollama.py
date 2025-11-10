# -*- coding: utf-8 -*-
"""
LLM Service with Ollama + Llama2
==================================

FREE, PRIVATE, UNLIMITED CV Generation!
Runs completely offline on your machine.
No API keys, no costs, no limits!
"""

import logging
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class LLMServiceOllama:
    """
    Service for calling Llama2 via Ollama (local, FREE!).
    
    Features:
    ✅ Completely FREE
    ✅ Runs locally (no internet needed after first download)
    ✅ 100% private (your data stays on your machine)
    ✅ No rate limits
    ✅ Unlimited use
    """
    
    def __init__(self, model="llama2", base_url="http://localhost:11434"):
        """
        Initialize Ollama LLM service.
        
        Args:
            model (str): Model to use (llama2, mistral, neural-chat)
            base_url (str): Ollama server URL (default: localhost:11434)
        """
        try:
            logger.info(f"Initializing Ollama LLM Service")
            logger.info(f"  Model: {model}")
            logger.info(f"  URL: {base_url}")
            
            # Check if Ollama is running
            import requests
            try:
                response = requests.get(f"{base_url}/api/tags", timeout=5)
                logger.info("✅ Ollama server is running!")
            except requests.exceptions.ConnectionError:
                logger.error(
                    "❌ Ollama server is NOT running!\n"
                    "Please start Ollama first in another terminal:\n"
                    "  ollama run llama2\n"
                    "or\n"
                    "  ollama run mistral"
                )
                raise ValueError(f"Cannot connect to Ollama at {base_url}")
            
            # Initialize Ollama
            self.llm = Ollama(
                model=model,
                base_url=base_url,
                temperature=0.7
            )
            
            self.model = model
            logger.info(f"✅ Ollama LLM Service ready with {model}!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Ollama: {e}")
            raise
    
    def _generate(self, prompt_text):
        """
        Internal method to generate text using Ollama.
        
        Args:
            prompt_text (str): The prompt to send to Ollama
            
        Returns:
            str: Generated text
        """
        try:
            logger.debug(f"Sending prompt to Ollama ({self.model})...")
            result = self.llm.invoke(prompt_text)
            logger.debug(f"Received response from Ollama")
            return result
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            return None
    
    def generate_professional_summary(self, user_data, examples):
        """Generate professional summary using Llama2"""
        try:
            logger.info("Generating professional summary with Llama2...")
            
            prompt = f"""You are an expert CV writer. Generate a professional 2-3 sentence summary for a job applicant.

Here are examples of professional summaries:

{examples}

Now write a professional summary for:
- Name: {user_data.get('full_name', 'Candidate')}
- Job Title: {user_data.get('job_title', 'Professional')}
- Years of Experience: {user_data.get('experience_years', 0)}
- Skills: {', '.join(user_data.get('skills', []))}
- Background: {user_data.get('professional_summary', 'Not provided')}

Generate a professional summary in the same style as the examples above. Focus on achievements and expertise. Output ONLY the summary text, no introduction or explanation."""
            
            result = self._generate(prompt)
            
            if result:
                logger.info("✅ Professional summary generated")
                return result.strip()
            else:
                logger.error("Failed to generate summary")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generating professional summary: {e}")
            return None
    
    def generate_achievement_bullets(self, user_data, examples, count=3):
        """Generate achievement bullet points using Llama2"""
        try:
            logger.info(f"Generating {count} achievement bullets with Llama2...")
            
            prompt = f"""You are an expert CV writer. Your job is to generate EXACTLY {count} achievement bullet points. 

CRITICAL INSTRUCTIONS:
- Output ONLY bullet points
- NO introduction, NO explanation, NO preamble
- Start each line with a dash (-)
- Each bullet should be 1-2 lines
- Use action verbs (Developed, Led, Managed, Implemented, Optimized, etc.)
- Include quantifiable results (numbers, percentages, metrics)

Here are examples of professional achievement bullets:

{examples}

Generate {count} achievement bullets for:
- Job Title: {user_data.get('job_title', 'Position')}
- Job Description: {user_data.get('job_description', 'Not provided')}
- Skills: {', '.join(user_data.get('skills', []))}

OUTPUT EXACTLY {count} BULLETS WITH DASHES - NOTHING ELSE:"""
            
            result = self._generate(prompt)
            
            if result:
                # Parse bullets - more robust parsing
                lines = result.strip().split('\n')
                bullets = []
                
                for line in lines:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Skip preamble/intro lines (common phrases to skip)
                    if any(skip in line.lower() for skip in ['here are', 'sure', 'certainly', 'of course', 'here is', "i'll", 'let me']):
                        continue
                    
                    # Extract bullet text
                    if line.startswith('-'):
                        bullet_text = line[1:].strip()
                    elif line.startswith('•'):
                        bullet_text = line[1:].strip()
                    elif line.startswith('*'):
                        bullet_text = line[1:].strip()
                    elif len(line) > 10 and line[0].isdigit() and '.' in line[:3]:
                        # Handle numbered bullets like "1. text"
                        bullet_text = line.split('.', 1)[1].strip()
                    else:
                        # Skip lines that don't look like bullets
                        continue
                    
                    # Add if it's a valid bullet (has meaningful content)
                    if bullet_text and len(bullet_text) > 15:
                        bullets.append(bullet_text)
                
                logger.info(f"✅ Generated {len(bullets)} achievement bullets")
                return bullets[:count]
            else:
                logger.error("Failed to generate bullets")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error generating achievement bullets: {e}")
            return []
    
    def generate_skills_section(self, user_data, examples):
        """Generate organized skills section using Llama2"""
        try:
            logger.info("Generating skills section with Llama2...")
            
            prompt = f"""You are an expert CV writer. Organize and enhance a skills list.

Here are examples of well-organized professional skills:

{examples}

Now organize these skills into categories:
Skills provided: {', '.join(user_data.get('skills', []))}

Organize them into categories (Technical, Soft Skills, Tools, Languages, etc.) in the same format as the examples. Be professional and concise."""
            
            result = self._generate(prompt)
            
            if result:
                logger.info("✅ Skills section generated")
                return result.strip()
            else:
                logger.error("Failed to generate skills section")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generating skills section: {e}")
            return None
    
    def generate_job_description(self, user_data, examples):
        """Generate professional job description using Llama2"""
        try:
            logger.info("Generating job description with Llama2...")
            
            prompt = f"""You are an expert CV writer. Write a professional job description.

Here are examples of professional job descriptions:

{examples}

Now write a job description for:
- Job Title: {user_data.get('job_title', 'Position')}
- Company: {user_data.get('company', 'Company')}
- Duration: {user_data.get('start_date', 'Date')} to {user_data.get('end_date', 'Date')}
- Brief Description: {user_data.get('description', 'Not provided')}

Write in the same professional style as the examples. Be concise and impactful."""
            
            result = self._generate(prompt)
            
            if result:
                logger.info("✅ Job description generated")
                return result.strip()
            else:
                logger.error("Failed to generate job description")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generating job description: {e}")
            return None
    
    def generate_education_section(self, user_data, examples):
        """Generate professional education section using Llama2"""
        try:
            logger.info("Generating education section with Llama2...")
            
            prompt = f"""You are an expert CV writer. Write professional education section details.

Here are examples of professional education sections:

{examples}

Now write education details for:
- Institution: {user_data.get('institution', 'University')}
- Degree: {user_data.get('degree', 'Bachelor')}
- Field: {user_data.get('field', 'Field')}
- Graduation Date: {user_data.get('graduation_date', 'Date')}
- GPA: {user_data.get('gpa', 'N/A')}
- Honors: {user_data.get('honors', 'N/A')}

Write in the same professional style as the examples. Include relevant honors or achievements."""
            
            result = self._generate(prompt)
            
            if result:
                logger.info("✅ Education section generated")
                return result.strip()
            else:
                logger.error("Failed to generate education section")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generating education section: {e}")
            return None