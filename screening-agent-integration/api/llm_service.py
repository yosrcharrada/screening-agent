# api/llm_service.py - FIXED VERSION WITH DEBUG LOGGING
import requests
import logging
import time

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.available_models = self._get_available_models()
        self.fast_model = self._select_lightweight_model()
        logger.info(f"🎯 Using lightweight LLM: {self.fast_model}")
    
    def _get_available_models(self):
        """Get all available Ollama models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=5
            )
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                logger.info(f"📋 Available models: {models}")
                return models
            return []
        except Exception as e:
            logger.error(f"❌ Error getting available models: {e}")
            return []
    
    def _select_lightweight_model(self):
        """Select the fastest available lightweight model"""
        # Priority: Lightweight models first
        lightweight_models = [
            "mistral:7b-instruct-q2_K",
            "mistral:7b-instruct-q3_K_M", 
            "mistral:7b-instruct-q4_K_M",
            "llama2:3b",
            "gemma:2b",
        ]
        
        for model in lightweight_models:
            if model in self.available_models:
                logger.info(f"✅ Selected lightweight model: {model}")
                return model
        
        # Fallback to first available model
        if self.available_models:
            logger.warning(f"⚠️ Using fallback model: {self.available_models[0]}")
            return self.available_models[0]
        
        logger.error("❌ No Ollama models available!")
        return None
    
    def generate_natural_explanation(self, score_result):
        """
        Generate LLM explanation with proper timeout handling
        """
        if not self.fast_model:
            logger.warning("⚠️ No LLM model available, using fallback")
            return self._get_fallback_explanation(score_result)
        
        try:
            logger.info(f"🤖 STARTING LLM CALL: {self.fast_model}")
            explanation = self._call_llm_with_retry(score_result)
            
            if explanation:
                logger.info("✅ LLM EXPLANATION SUCCESSFULLY GENERATED")
                return explanation
            else:
                logger.warning("⚠️ LLM returned empty response, using fallback")
                return self._get_fallback_explanation(score_result)
                
        except Exception as e:
            logger.error(f"❌ LLM CALL FAILED: {e}")
            return self._get_fallback_explanation(score_result)
    
    def _call_llm_with_retry(self, score_result, max_retries=2):
        """Call LLM with retry logic and detailed logging"""
        final_score = score_result.get('final_score', 0)
        content_score = score_result['subscores']['content']['score']
        delivery_score = score_result['subscores']['delivery']['score']
        communication_score = score_result['subscores']['communication']['score']
        
        # ✅ FIXED: Better prompt for complete explanations
        prompt = f"""Analyze this interview performance score and provide a complete explanation:
Final Score: {final_score}/100
- Content: {content_score}/100 (45% weight)
- Delivery: {delivery_score}/100 (35% weight) 
- Communication: {communication_score}/100 (20% weight)

Provide a comprehensive analysis explaining what each score means and the overall performance in 3-4 complete sentences."""
        
        logger.info(f"📝 LLM PROMPT: {prompt}")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 LLM ATTEMPT {attempt + 1}/{max_retries} with model: {self.fast_model}")
                
                start_time = time.time()
                session = requests.Session()
                
                response = session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.fast_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 200,  # ✅ FIXED: Increased from 80 to 200 for complete responses
                            "top_k": 20,
                            "top_p": 0.8,
                            "num_ctx": 1024  # ✅ FIXED: Increased context window
                        }
                    },
                    timeout=30
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get('response', '').strip()
                    
                    if explanation:
                        logger.info(f"🎉 LLM SUCCESS in {elapsed:.2f}s")
                        logger.info(f"💬 LLM RESPONSE LENGTH: {len(explanation)} characters")
                        logger.info(f"💬 LLM RESPONSE: {explanation}")
                        
                        # ✅ FIXED: Check if response is complete
                        if len(explanation) < 100:
                            logger.warning("⚠️ LLM response seems too short, might be truncated")
                        else:
                            logger.info("✅ LLM response appears complete")
                            
                        return explanation
                    else:
                        logger.warning("⚠️ LLM returned empty response")
                else:
                    logger.error(f"❌ LLM HTTP error {response.status_code}: {response.text}")
                
            except requests.exceptions.Timeout:
                logger.error(f"⏰ LLM TIMEOUT after {elapsed:.2f}s on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    logger.info("💤 Waiting 1 second before retry...")
                    time.sleep(1)
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.error(f"🔌 LLM CONNECTION ERROR: {e}")
                break
            except Exception as e:
                logger.error(f"🚨 LLM UNEXPECTED ERROR: {e}")
                break
        
        logger.error("💥 ALL LLM ATTEMPTS FAILED")
        return None
    
    def _get_fallback_explanation(self, score_result):
        """Generate fallback explanation when LLM unavailable"""
        logger.info("🔄 USING FALLBACK EXPLANATION (No LLM)")
        
        final_score = score_result.get('final_score', 0)
        content_score = score_result['subscores']['content']['score']
        delivery_score = score_result['subscores']['delivery']['score']
        communication_score = score_result['subscores']['communication']['score']
        
        # Calculate contributions
        content_contrib = content_score * 0.45
        delivery_contrib = delivery_score * 0.35
        communication_contrib = communication_score * 0.20
        
        # Determine main strength and weakness
        scores = {
            'Content': content_score,
            'Delivery': delivery_score,
            'Communication': communication_score
        }
        strength = max(scores, key=scores.get)
        weakness = min(scores, key=scores.get)
        
        return f"""Your interview score of {final_score:.1f}/100 reflects your performance across three key areas. Content contributed {content_contrib:.1f} points (45% weight), Delivery added {delivery_contrib:.1f} points (35% weight), and Communication provided {communication_contrib:.1f} points (20% weight). Your strongest area is {strength} ({scores[strength]:.1f}/100), while {weakness} ({scores[weakness]:.1f}/100) has the most room for improvement. Focus on enhancing your {weakness.lower()} skills to boost your overall score."""

# Create global instance
llm_service = LLMService()