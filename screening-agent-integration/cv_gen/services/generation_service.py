"""
Generation Service - LLM ONLY Pipeline
========================================

High-level API for LLM-based CV generation.
RAG/KB is DISABLED for now.
Uses the LangChain-based Ollama service.
"""

import logging
from typing import Dict, List
from datetime import datetime

from cv_gen.models import CVDocument
# from .rag_service import EnhancedRAGService   # DISABLED
from .llm_service_ollama import LLMServiceOllama

logger = logging.getLogger(__name__)

class CVGenerationService:
    """
    High-level service for complete CV generation

    Uses:
    - LLM (Ollama + LangChain) for generation
    """

    def __init__(self, model: str = "llama2"):
        """Initialize services"""
        try:
            # self.rag_service = EnhancedRAGService()  # DISABLED
            self.llm_service = LLMServiceOllama(model=model)
            logger.info("✅ CV Generation Service initialized (LLM only, no RAG)")
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
        use_rag: bool = False
    ) -> str:
        """
        Generate professional summary for CV (LLM only)
        """
        try:
            logger.info(f"📝 Generating summary for {cv_document.full_name}...")

            # NO RAG
            examples_text = ""

            years_exp = self._calculate_years_of_experience(cv_document)

            user_data = {
                'full_name': cv_document.full_name,
                'profession': cv_document.profession,
                'job_title': cv_document.professional_headline,
                'experience_years': years_exp,
                'professional_summary': cv_document.professional_summary,
                'skills': list(cv_document.skills.values_list('skill_name', flat=True))
            }

            summary = self.llm_service.generate_professional_summary(
                user_data=user_data,
                examples=examples_text
            )

            if not summary:
                logger.warning("LLM returned empty summary")
                return ""

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
        use_rag: bool = False
    ) -> List[str]:
        """
        Generate achievement bullets for work experience (LLM only)
        """
        try:
            logger.info(f"💥 Generating {num_bullets} bullets for {work_experience.job_title}...")

            # NO RAG
            examples_text = ""

            user_data = {
                'job_title': work_experience.job_title,
                'company': work_experience.company_name,
                'job_description': work_experience.job_description,
                'skills': list(cv_document.skills.values_list('skill_name', flat=True)),
                'achievements': work_experience.achievements
            }

            bullets = self.llm_service.generate_achievement_bullets(
                user_data=user_data,
                examples=examples_text,
                count=num_bullets
            )

            if not bullets:
                logger.warning("LLM returned no bullets")
                return []

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
        use_rag: bool = False
    ) -> Dict:
        """
        Generate complete CV content (LLM only)
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

            if include_summary:
                try:
                    summary = self.generate_professional_summary(
                        cv_document,
                        use_rag=False
                    )
                    result['summary'] = summary
                except Exception as e:
                    logger.error(f"Summary generation failed: {e}")
                    result['errors'].append(f"Summary: {str(e)}")

            if include_bullets:
                for work_exp in cv_document.work_experiences.all():
                    try:
                        bullets = self.generate_achievement_bullets(
                            cv_document,
                            work_exp,
                            num_bullets=5,
                            use_rag=False
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

            cv_document.generated_cv_content = result
            cv_document.save(update_fields=['generated_cv_content'])

            logger.info(f"✅ Complete CV generation finished")
            return result

        except Exception as e:
            logger.error(f"❌ Error in complete CV generation: {e}")
            raise

    # Feedback and validation are RAG-only, so disable or raise here
    def collect_feedback(self, *args, **kwargs):
        logger.warning("RAG feedback is disabled.")
        return False

    def validate_generated_content(self, *args, **kwargs):
        logger.warning("RAG validation is disabled.")
        return True, "Validation skipped", 0.5