import os
import re
import requests
import PyPDF2
import docx
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import logging
from urllib.parse import urlparse
import tempfile

logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Handles file uploads, URL processing, and text extraction from various formats
    """
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'PDF',
        '.docx': 'Word Document', 
        '.doc': 'Word Document',
        '.txt': 'Text File'
    }
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
    
    # ADD THIS MISSING METHOD
    def process_documents_for_analysis(self, cv_input, jd_input):
        """
        Process CV and JD from any input type and return extracted text
        """
        cv_content = ""
        jd_content = ""
        
        try:
            # Process CV
            if hasattr(cv_input, 'read'):  # It's a file object
                cv_content = self.extract_text_from_file(cv_input)
            elif isinstance(cv_input, str) and cv_input.startswith('http'):  # It's a URL
                cv_content = self.extract_text_from_url(cv_input)
            else:  # It's text
                cv_content = cv_input
            
            # Process JD
            if hasattr(jd_input, 'read'):  # It's a file object
                jd_content = self.extract_text_from_file(jd_input)
            elif isinstance(jd_input, str) and jd_input.startswith('http'):  # It's a URL
                jd_content = self.extract_text_from_url(jd_input)
            else:  # It's text
                jd_content = jd_input
            
            # Validate content
            if len(cv_content.strip()) < 50:
                raise ValueError("CV content too short")
            if len(jd_content.strip()) < 50:
                raise ValueError("JD content too short")
            
            return cv_content, jd_content
            
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            raise

    def extract_text_from_file(self, file):
        """
        Extract text from uploaded file (PDF, DOCX, TXT)
        """
        if not file:
            return None
            
        filename = file.name.lower()
        
        try:
            if filename.endswith('.pdf'):
                return self._extract_from_pdf(file)
            elif filename.endswith(('.docx', '.doc')):
                return self._extract_from_docx(file)
            elif filename.endswith('.txt'):
                return self._extract_from_txt(file)
            else:
                raise ValueError(f"Unsupported file format: {filename}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            raise
    
    def extract_text_from_url(self, url):
        """
        Extract text from URL (LinkedIn, job posting, etc.)
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Simple HTML to text conversion
            text = self._html_to_text(response.text)
            
            if not text.strip():
                raise ValueError("No text content found in URL")
                
            return self._clean_extracted_text(text)
            
        except Exception as e:
            logger.error(f"Error extracting text from URL {url}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file):
        """Extract text from PDF files"""
        text = ""
        
        try:
            # Method 1: Try pdfplumber first (better for text-based PDFs)
            file.seek(0)
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Method 2: If no text found, try PyPDF2
            if not text.strip():
                file.seek(0)
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            # Fallback: Try OCR if available
            try:
                text = self._extract_from_pdf_ocr(file)
            except Exception as ocr_error:
                logger.error(f"PDF OCR also failed: {ocr_error}")
                raise
        
        return self._clean_extracted_text(text)
    
    def _extract_from_pdf_ocr(self, file):
        """Extract text from PDF using OCR (for scanned PDFs)"""
        text = ""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Convert PDF to images and OCR
            images = convert_from_path(temp_file_path)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            
            # Clean up
            os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            raise
        
        return text
    
    def _extract_from_docx(self, file):
        """Extract text from Word documents"""
        try:
            file.seek(0)
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"
                    
            return self._clean_extracted_text(text)
            
        except Exception as e:
            logger.error(f"Error extracting from DOCX: {str(e)}")
            raise
    
    def _extract_from_txt(self, file):
        """Extract text from plain text files"""
        try:
            file.seek(0)
            # Try UTF-8 first, then fallback to latin-1
            try:
                text = file.read().decode('utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                text = file.read().decode('latin-1')
            return self._clean_extracted_text(text)
        except Exception as e:
            logger.error(f"Error extracting from TXT: {str(e)}")
            raise
    
    def _html_to_text(self, html_content):
        """Convert HTML to plain text"""
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        
        # Replace common HTML tags with spaces
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<div[^>]*>', '\n', text, flags=re.IGNORECASE)
        
        # Remove all other HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def _clean_extracted_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Fix common OCR/issues
        text = re.sub(r'\s+([.!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between words
        
        # Remove unwanted characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-&+/]', '', text)
        
        return text.strip()
    
    def validate_file(self, file):
        """Validate uploaded file"""
        if not file:
            return False, "No file provided"
        
        filename = file.name.lower()
        file_extension = os.path.splitext(filename)[1]
        
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format. Supported: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
        
        # Check file size
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                return False, f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                
        except Exception as e:
            return False, "Could not determine file size"
        
        return True, "File is valid"
    
    def validate_url(self, url):
        """Validate URL format"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

# Global instance
file_processor = FileProcessor()