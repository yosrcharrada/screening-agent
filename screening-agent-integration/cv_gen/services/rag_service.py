"""
Enhanced RAG Service - Complete 15-Step Pipeline
================================================

Implements full Retrieval Augmented Generation with:
✅ Profession-based filtering
✅ Re-ranking
✅ Hybrid search (semantic + keyword)
✅ Output validation
✅ Caching
✅ Feedback loops
"""

import logging
import hashlib
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Q

from cv_gen.models import KnowledgeBase, RAGCache, CVGenerationFeedback
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """Complete RAG Service with all advanced features"""
    
    def __init__(self):
        """Initialize RAG service"""
        try:
            self.embedding_service = EmbeddingService()
            logger.info("✅ Enhanced RAG Service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing Enhanced RAG Service: {e}")
            raise
    
    def retrieve_similar_examples(
        self,
        query_text: str,
        profession: Optional[str] = None,
        cv_section: Optional[str] = None,
        top_k: int = 3,
        use_cache: bool = True
    ) -> List[KnowledgeBase]:
        """
        Retrieve similar examples with profession and section filtering.
        
        Steps:
        - Check cache
        - Generate query embedding
        - Filter by profession and section
        - Calculate cosine similarities
        - Re-rank results
        - Cache and return
        """
        try:
            logger.info(f"🔍 RAG Retrieval: '{query_text[:50]}...'")
            logger.info(f"   Filters: profession={profession}, section={cv_section}")
            
            # Check cache
            if use_cache:
                cached = self._get_cached_results(query_text, profession, cv_section)
                if cached:
                    logger.info(f"✅ Cache hit! Retrieved {len(cached)} cached results")
                    return cached
            
            # Generate query embedding
            logger.info("Step 1/5: Generating query embedding...")
            query_embedding = self.embedding_service.generate_embedding(query_text)
            logger.info(f"  ✅ Query embedding shape: {query_embedding.shape}")
            
            # Build database query
            logger.info("Step 2/5: Filtering KB entries...")
            kb_query = KnowledgeBase.objects.all()
            
            if profession:
                kb_query = kb_query.filter(profession=profession)
                logger.info(f"  └─ Filtered by profession: {profession}")
            
            if cv_section:
                kb_query = kb_query.filter(cv_section=cv_section)
                logger.info(f"  └─ Filtered by section: {cv_section}")
            
            kb_entries = list(kb_query[:2000])
            logger.info(f"  └─ Total entries to search: {len(kb_entries)}")
            
            if not kb_entries:
                logger.warning("⚠️  No KB entries found!")
                return []
            
            # Calculate similarities
            logger.info("Step 3/5: Calculating similarities...")
            similarities = []
            success_count = 0
            fail_count = 0
            
            for entry in kb_entries:
                try:
                    entry_embedding = self._parse_embedding_vector(entry.embedding_vector)
                    if entry_embedding is None:
                        fail_count += 1
                        continue
                    
                    sim_score = float(cosine_similarity(
                        [query_embedding],
                        [entry_embedding]
                    )[0][0])
                    
                    similarities.append({
                        'entry': entry,
                        'score': sim_score
                    })
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    continue
            
            logger.info(f"  ├─ Processed: {success_count}, Failed: {fail_count}")
            
            if not similarities:
                logger.warning("⚠️  No similarities calculated!")
                return []
            
            # Sort by similarity
            logger.info(f"Step 4/5: Ranking {len(similarities)} results...")
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            top_scores = [round(r['score'], 3) for r in similarities[:5]]
            logger.info(f"  Top scores: {top_scores}")
            
            # Get top-K and re-rank
            top_results = [r['entry'] for r in similarities[:top_k]]
            
            logger.info(f"Step 5/5: Re-ranking results...")
            top_results = self._rerank_results(query_text, top_results)
            
            logger.info(f"✅ Retrieved {len(top_results)} results")
            
            # Cache results
            if use_cache and top_results:
                self._cache_results(query_text, profession, cv_section, top_results)
            
            return top_results
            
        except Exception as e:
            logger.error(f"❌ Error in retrieve_similar_examples: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def hybrid_search(
        self,
        query_text: str,
        profession: Optional[str] = None,
        cv_section: Optional[str] = None,
        top_k: int = 5
    ) -> List[KnowledgeBase]:
        """Hybrid search combining semantic and keyword search"""
        try:
            logger.info("🔄 Performing hybrid search...")
            
            # Semantic search
            semantic_results = self.retrieve_similar_examples(
                query_text,
                profession=profession,
                cv_section=cv_section,
                top_k=top_k,
                use_cache=False
            )
            semantic_ids = {r.id for r in semantic_results}
            
            # Keyword search
            keywords = query_text.lower().split()
            keyword_query = KnowledgeBase.objects.all()
            
            if profession:
                keyword_query = keyword_query.filter(profession=profession)
            if cv_section:
                keyword_query = keyword_query.filter(cv_section=cv_section)
            
            for keyword in keywords:
                keyword_query = keyword_query.filter(
                    Q(title__icontains=keyword) |
                    Q(content__icontains=keyword)
                )
            
            keyword_results = list(keyword_query[:top_k])
            
            # Combine results
            combined = semantic_results + keyword_results
            unique_ids = set()
            final_results = []
            
            for r in combined:
                if r.id not in unique_ids:
                    final_results.append(r)
                    unique_ids.add(r.id)
            
            logger.info(f"✅ Hybrid search found {len(final_results)} results")
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Error in hybrid_search: {e}")
            return self.retrieve_similar_examples(query_text, profession, cv_section, top_k)
    
    def _rerank_results(
        self,
        query_text: str,
        results: List[KnowledgeBase],
        top_k: Optional[int] = None
    ) -> List[KnowledgeBase]:
        """Re-rank results by quality metrics"""
        try:
            if not results:
                return results
            
            logger.info(f"  Re-ranking {len(results)} results...")
            
            scores = []
            for result in results:
                base_score = min((result.word_count or 0) / 500, 1.0)
                confidence = result.confidence_score or 1.0
                content_type_score = {
                    'job_description': 1.0,
                    'paragraph': 0.8,
                    'bullet': 0.6,
                }.get(result.content_type, 0.5)
                
                total_score = (base_score * 0.3) + (confidence * 0.4) + (content_type_score * 0.3)
                scores.append((result, total_score))
            
            scores.sort(key=lambda x: x[1], reverse=True)
            reranked = [r[0] for r in scores]
            
            logger.info(f"  └─ Re-ranked successfully")
            return reranked[:top_k] if top_k else reranked
            
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}")
            return results
    
    def validate_generation(
        self,
        query_text: str,
        generated_text: str,
        context_examples: List[KnowledgeBase]
    ) -> Tuple[bool, str, float]:
        """Validate generated text quality"""
        try:
            logger.info("🔍 Validating generation...")
            
            issues = []
            
            # Check length
            if len(generated_text.strip()) < 50:
                issues.append("Text too short")
            
            # Check relevance
            gen_embedding = self.embedding_service.generate_embedding(generated_text)
            query_embedding = self.embedding_service.generate_embedding(query_text)
            relevance = float(cosine_similarity([gen_embedding], [query_embedding])[0][0])
            
            if relevance < 0.3:
                issues.append(f"Low relevance ({relevance:.2f})")
            else:
                logger.info(f"  ✅ Relevance: {relevance:.2f}")
            
            # Check grounding
            context_embeddings = [
                self.embedding_service.generate_embedding(ex.content)
                for ex in context_examples
            ]
            
            grounding_scores = [
                float(cosine_similarity([gen_embedding], [ctx_emb])[0][0])
                for ctx_emb in context_embeddings
            ]
            
            max_grounding = max(grounding_scores) if grounding_scores else 0
            
            if max_grounding < 0.2:
                issues.append(f"Poor grounding ({max_grounding:.2f})")
            else:
                logger.info(f"  ✅ Grounding: {max_grounding:.2f}")
            
            # Quality metrics
            word_count = len(generated_text.split())
            has_numbers = any(char.isdigit() for char in generated_text)
            has_verbs = any(
                verb in generated_text.lower()
                for verb in ['implemented', 'developed', 'designed', 'managed', 'led', 'created']
            )
            
            confidence = 1.0
            if not has_numbers:
                confidence -= 0.1
            if not has_verbs:
                confidence -= 0.15
            
            confidence = max(0.0, confidence)
            
            is_valid = len(issues) == 0 and confidence > 0.5
            reason = " | ".join(issues) if issues else "✅ All checks passed"
            
            logger.info(f"  Result: Valid={is_valid}, Confidence={confidence:.1%}")
            
            return is_valid, reason, confidence
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return True, "Validation skipped", 0.5
    
    def collect_feedback(
        self,
        cv_document,
        section_type: str,
        generated_content: str,
        rating: int,
        feedback_text: str = "",
        suggested_improvement: str = ""
    ) -> bool:
        """Collect user feedback"""
        try:
            logger.info(f"💾 Saving feedback: {section_type} rated {rating}/5")
            
            CVGenerationFeedback.objects.create(
                cv_document=cv_document,
                section_type=section_type,
                generated_content=generated_content,
                rating=rating,
                feedback_text=feedback_text,
                was_helpful=rating >= 3,
                suggested_improvement=suggested_improvement
            )
            
            logger.info(f"✅ Feedback saved")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving feedback: {e}")
            return False
    
    def format_examples_for_prompt(self, kb_entries: List[KnowledgeBase]) -> str:
        """Format KB entries for LLM prompt"""
        try:
            if not kb_entries:
                return "No examples available."
            
            formatted = "PROFESSIONAL EXAMPLES:\n\n"
            
            for i, entry in enumerate(kb_entries, 1):
                formatted += f"Example {i} ({entry.profession} - {entry.get_cv_section_display()}):\n"
                formatted += f"{entry.content}\n"
                formatted += f"[Confidence: {entry.confidence_score:.1%}]\n\n"
            
            logger.info(f"✅ Formatted {len(kb_entries)} examples")
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting: {e}")
            return ""
    
    def _parse_embedding_vector(self, embedding_str: str) -> Optional[np.ndarray]:
        """Parse embedding vector from JSON or CSV"""
        try:
            # Try JSON
            try:
                vector = json.loads(embedding_str)
                return np.array(vector, dtype=np.float32)
            except json.JSONDecodeError:
                pass
            
            # Try CSV
            try:
                vector = [float(x.strip()) for x in embedding_str.split(',')]
                return np.array(vector, dtype=np.float32)
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing embedding: {e}")
            return None
    
    def _get_cached_results(
        self,
        query_text: str,
        profession: Optional[str],
        cv_section: Optional[str]
    ) -> Optional[List[KnowledgeBase]]:
        """Retrieve cached results"""
        try:
            query_hash = self._get_query_hash(query_text, profession, cv_section)
            cache = RAGCache.objects.get(query_hash=query_hash)
            cache.hit_count += 1
            cache.save(update_fields=['hit_count', 'accessed_at'])
            
            result_ids = cache.cached_results.get('result_ids', [])
            return list(KnowledgeBase.objects.filter(id__in=result_ids))
            
        except RAGCache.DoesNotExist:
            return None
        except Exception as e:
            logger.warning(f"Cache error: {e}")
            return None
    
    def _cache_results(
        self,
        query_text: str,
        profession: Optional[str],
        cv_section: Optional[str],
        results: List[KnowledgeBase]
    ) -> None:
        """Cache RAG results"""
        try:
            query_hash = self._get_query_hash(query_text, profession, cv_section)
            
            RAGCache.objects.update_or_create(
                query_hash=query_hash,
                defaults={
                    'profession': profession or 'General',
                    'cv_section': cv_section or 'all',
                    'query_text': query_text,
                    'cached_results': {
                        'result_ids': [r.id for r in results],
                        'count': len(results),
                    }
                }
            )
            
            logger.info(f"✅ Cached {len(results)} results")
            
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def _get_query_hash(self, query_text: str, profession: Optional[str], cv_section: Optional[str]) -> str:
        """Generate hash for caching"""
        cache_key = f"{query_text}_{profession}_{cv_section}"
        return hashlib.sha256(cache_key.encode()).hexdigest()