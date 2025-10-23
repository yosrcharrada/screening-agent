# cv_processor.py
import os
import tempfile
from .utils import extract_text_from_pdf, fetch_content_from_url
import logging

logger = logging.getLogger(__name__)

class CVProcessor:
    @staticmethod
    def extract_cv_content(cv_input):
        """
        Extract text from CV input (file, text, or URL)
        """
        try:
            cv_content = ""
            
            # If it's a file upload
            if hasattr(cv_input, 'read'):
                # Handle PDF files
                if hasattr(cv_input, 'name') and cv_input.name.endswith('.pdf'):
                    cv_content = extract_text_from_pdf(cv_input)
                else:
                    # Handle text files or other formats
                    cv_input.seek(0)
                    if hasattr(cv_input, 'read'):
                        content = cv_input.read()
                        if isinstance(content, bytes):
                            cv_content = content.decode('utf-8', errors='ignore')
                        else:
                            cv_content = str(content)
            
            # If it's text
            elif isinstance(cv_input, str) and len(cv_input) > 10:  # Basic check for meaningful text
                cv_content = cv_input
            
            # If it's a URL
            elif isinstance(cv_input, str) and cv_input.startswith(('http://', 'https://')):
                cv_content = fetch_content_from_url(cv_input)
            
            # Clean and validate content
            if cv_content and len(cv_content.strip()) > 50:  # Minimum meaningful content
                return cv_content.strip()
            else:
                raise ValueError("Insufficient CV content extracted")
                
        except Exception as e:
            logger.error(f"CV processing error: {str(e)}")
            raise ValueError(f"Failed to process CV: {str(e)}")

# Singleton instance
cv_processor = CVProcessor()