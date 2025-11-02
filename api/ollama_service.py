# api/ollama_service.py (Minimal Fix)
import subprocess
import logging

logger = logging.getLogger(__name__)

class SimpleLLMService:
    def __init__(self):
        self.ollama_path = r"C:\Users\amorr\AppData\Local\Programs\Ollama\ollama.exe"
    
    def get_mathematical_explanation(self, final_score, content_score, delivery_score, communication_score):
        """
        Simple LLM call with robust encoding handling
        """
        prompt = f"Explain this interview score mathematically: Total {final_score}/100 = Content {content_score}×45% + Delivery {delivery_score}×35% + Communication {communication_score}×20%. Keep explanation under 100 words."
        
        logger.info(f"🔍 LLM Request: {prompt}")
        
        try:
            command = f'"{self.ollama_path}" run mistral:7b-instruct-q4_K_M "{prompt}"'
            
            # Use subprocess.run with proper encoding
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=20,  # Increased timeout
                shell=True
            )
            
            # Handle output with multiple encoding attempts
            if result.returncode == 0 and result.stdout:
                # Try different encodings
                encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        explanation = result.stdout.decode(encoding).strip()
                        if explanation:
                            logger.info(f"✅ LLM SUCCESS with {encoding}: {explanation[:80]}...")
                            return explanation
                    except UnicodeDecodeError:
                        continue
                
                # If all encodings fail, use replace
                explanation = result.stdout.decode('utf-8', errors='replace').strip()
                if explanation:
                    logger.info(f"✅ LLM SUCCESS (with replacements): {explanation[:80]}...")
                    return explanation
            
            logger.warning("❌ LLM returned empty response")
            
        except subprocess.TimeoutExpired:
            logger.error("❌ LLM timeout after 20 seconds")
        except Exception as e:
            logger.error(f"❌ LLM exception: {e}")
        
        # Fallback
        return self._get_fallback_explanation(final_score, content_score, delivery_score, communication_score)
    
    def generate_natural_explanation(self, score_result):
        """Generate natural language explanation"""
        try:
            final_score = score_result.get('final_score', 0)
            content_score = score_result['subscores']['content']['score']
            delivery_score = score_result['subscores']['delivery']['score']
            communication_score = score_result['subscores']['communication']['score']
            
            return self.get_mathematical_explanation(
                final_score, content_score, delivery_score, communication_score
            )
        except Exception as e:
            logger.error(f"❌ Error in natural explanation: {e}")
            return self._get_fallback_explanation(
                score_result.get('final_score', 0),
                score_result['subscores']['content']['score'],
                score_result['subscores']['delivery']['score'],
                score_result['subscores']['communication']['score']
            )
    
    def _get_fallback_explanation(self, final_score, content_score, delivery_score, communication_score):
        """Fallback explanation"""
        content_pts = content_score * 0.45
        delivery_pts = delivery_score * 0.35
        communication_pts = communication_score * 0.20
        total = content_pts + delivery_pts + communication_pts
        
        return f"""MATHEMATICAL EXPLANATION:
Your score of {final_score}/100 is calculated as:

• Content: {content_score} × 45% = {content_pts:.2f} points
• Delivery: {delivery_score} × 35% = {delivery_pts:.2f} points  
• Communication: {communication_score} × 20% = {communication_pts:.2f} points
• TOTAL: {content_pts:.2f} + {delivery_pts:.2f} + {communication_pts:.2f} = {total:.2f}/100

The weighted average shows that Content has the biggest impact (45%), followed by Delivery (35%) and Communication (20%)."""

# Create instance
ollama_service = SimpleLLMService()