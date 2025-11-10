"""
Generation Service - RAG + LLM Pipeline
========================================

High-level API combining RAG retrieval with LLM generation.
Uses the LangChain-based Ollama service.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from cv_gen.models import CVDocument, CVGenerationFeedback
from .rag_service import EnhancedRAGService
from .llm_service_ollama import LLMServiceOllama

logger = logging.getLogger(__name__)


class CVGenerationService:
    """
    High-level service for complete CV generation
    
    Combines:
    - RAG for context retrieval
    - LLM (Ollama + LangChain) for generation
    - Validation and feedback
    """
    
    def __init__(self, model: str = "llama2"):
        """Initialize services"""
        try:
            self.rag_service = EnhancedRAGService()
            self.llm_service = LLMServiceOllama(model=model)
            logger.info("✅ CV Generation Service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing: {e}")
            raise
    
    def _calculate_years_of_experience(self, cv_document: CVDocument) -> int:
        """Calculate years of experience from work experiences"""
        try:
            work_exps = cv_document.work_experiences.all()
            if not work_exps:
                return 0
            
            total_years = 0
            for exp in work_exps:
                if exp.start_date and exp.end_date:
                    years = (exp.end_date - exp.start_date).days / 365.25
                    total_years += years
                elif exp.start_date and exp.is_current:
                    years = (datetime.now().date() - exp.start_date).days / 365.25
                    total_years += years
            
            return int(total_years)
        except Exception as e:
            logger.warning(f"Could not calculate years: {e}")
            return 0
    
    def generate_professional_summary(
        self,
        cv_document: CVDocument,
        use_rag: bool = True
    ) -> str:
        """
        Generate professional summary for CV
        
        Args:
            cv_document: User's CV document
            use_rag: Whether to use RAG examples
            
        Returns:
            Generated professional summary
        """
        try:
            logger.info(f"📝 Generating summary for {cv_document.full_name}...")
            
            # Get RAG examples if enabled
            rag_examples = None
            examples_text = ""
            
            if use_rag:
                rag_examples = self.rag_service.retrieve_similar_examples(
                    query_text=f"{cv_document.professional_headline} professional",
                    profession=cv_document.profession,
                    cv_section="summary",
                    top_k=3
                )
                logger.info(f"  Retrieved {len(rag_examples)} RAG examples")
                
                # Format examples for prompt
                examples_text = self.rag_service.format_examples_for_prompt(rag_examples)
            
            # Calculate years of experience
            years_exp = self._calculate_years_of_experience(cv_document)
            
            # Prepare user data
            user_data = {
                'full_name': cv_document.full_name,
                'profession': cv_document.profession,
                'job_title': cv_document.professional_headline,
                'experience_years': years_exp,
                'professional_summary': cv_document.professional_summary,
                'skills': list(cv_document.skills.values_list('skill_name', flat=True))
            }
            
            # Generate with LLM
            summary = self.llm_service.generate_professional_summary(
                user_data=user_data,
                examples=examples_text
            )
            
            if not summary:
                logger.warning("LLM returned empty summary")
                return ""
            
            # Save to CV document
            cv_document.generated_summary = summary
            cv_document.save(update_fields=['generated_summary'])
            
            logger.info(f"✅ Summary generated: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            raise
    
    def generate_achievement_bullets(
        self,
        cv_document: CVDocument,
        work_experience,
        num_bullets: int = 5,
        use_rag: bool = True
    ) -> List[str]:
        """
        Generate achievement bullets for work experience
        
        Args:
            cv_document: User's CV document
            work_experience: WorkExperience instance
            num_bullets: Number of bullets to generate
            use_rag: Whether to use RAG examples
            
        Returns:
            List of achievement bullets
        """
        try:
            logger.info(f"💥 Generating {num_bullets} bullets for {work_experience.job_title}...")
            
            # Get RAG examples
            rag_examples = None
            examples_text = ""
            
            if use_rag:
                rag_examples = self.rag_service.retrieve_similar_examples(
                    query_text=f"{work_experience.job_title} achievements",
                    profession=cv_document.profession,
                    cv_section="achievement",
                    top_k=5
                )
                logger.info(f"  Retrieved {len(rag_examples)} achievement examples")
                
                # Format examples
                examples_text = self.rag_service.format_examples_for_prompt(rag_examples)
            
            # Prepare user data
            user_data = {
                'job_title': work_experience.job_title,
                'company': work_experience.company_name,
                'job_description': work_experience.job_description,
                'skills': list(cv_document.skills.values_list('skill_name', flat=True)),
                'achievements': work_experience.achievements
            }
            
            # Generate bullets
            bullets = self.llm_service.generate_achievement_bullets(
                user_data=user_data,
                examples=examples_text,
                count=num_bullets
            )
            
            if not bullets:
                logger.warning("LLM returned no bullets")
                return []
            
            # Save to database
            work_experience.generated_bullets = "\n".join(bullets)
            work_experience.save(update_fields=['generated_bullets'])
            
            logger.info(f"✅ Generated {len(bullets)} bullets")
            return bullets
            
        except Exception as e:
            logger.error(f"❌ Error generating bullets: {e}")
            raise
    
    def generate_complete_cv(
        self,
        cv_document: CVDocument,
        include_summary: bool = True,
        include_bullets: bool = True,
        use_rag: bool = True
    ) -> Dict:
        """
        Generate complete CV content
        
        Args:
            cv_document: User's CV document
            include_summary: Generate professional summary
            include_bullets: Generate achievement bullets
            use_rag: Use RAG for context
            
        Returns:
            Dictionary with generated content
        """
        try:
            logger.info(f"🚀 Starting complete CV generation for {cv_document.full_name}...")
            
            result = {
                'cv_document_id': cv_document.id,
                'generated_at': datetime.now().isoformat(),
                'summary': None,
                'work_experiences': [],
                'errors': []
            }
            
            # Generate summary
            if include_summary:
                try:
                    summary = self.generate_professional_summary(
                        cv_document,
                        use_rag=use_rag
                    )
                    result['summary'] = summary
                except Exception as e:
                    logger.error(f"Summary generation failed: {e}")
                    result['errors'].append(f"Summary: {str(e)}")
            
            # Generate bullets for each work experience
            if include_bullets:
                for work_exp in cv_document.work_experiences.all():
                    try:
                        bullets = self.generate_achievement_bullets(
                            cv_document,
                            work_exp,
                            num_bullets=5,
                            use_rag=use_rag
                        )
                        result['work_experiences'].append({
                            'work_experience_id': work_exp.id,
                            'job_title': work_exp.job_title,
                            'company': work_exp.company_name,
                            'bullets': bullets
                        })
                    except Exception as e:
                        logger.error(f"Bullets generation failed for {work_exp.job_title}: {e}")
                        result['errors'].append(f"{work_exp.job_title}: {str(e)}")
            
            # Save complete content
            cv_document.generated_cv_content = result
            cv_document.save(update_fields=['generated_cv_content'])
            
            logger.info(f"✅ Complete CV generation finished")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in complete CV generation: {e}")
            raise
    
    def collect_feedback(
        self,
        cv_document: CVDocument,
        section_type: str,
        generated_content: str,
        rating: int,
        feedback_text: str = ""
    ) -> bool:
        """Collect feedback on generated content"""
        try:
            return self.rag_service.collect_feedback(
                cv_document=cv_document,
                section_type=section_type,
                generated_content=generated_content,
                rating=rating,
                feedback_text=feedback_text
            )
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return False
    
    def validate_generated_content(
        self,
        query_text: str,
        generated_text: str,
        profession: str
    ) -> tuple:
        """Validate generated content quality"""
        try:
            rag_examples = self.rag_service.retrieve_similar_examples(
                query_text=query_text,
                profession=profession,
                top_k=3
            )
            
            is_valid, reason, confidence = self.rag_service.validate_generation(
                query_text=query_text,
                generated_text=generated_text,
                context_examples=rag_examples
            )
            
            return is_valid, reason, confidence
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return True, "Validation skipped", 0.5