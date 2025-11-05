import spacy
import re
import torch
from transformers import pipeline
import logging
from typing import Dict, List, Tuple
import itertools

# Professional dependencies with fallbacks
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

try:
    import phonenumbers
    from phonenumbers import PhoneNumberMatcher, is_valid_number, format_number, PhoneNumberFormat
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

try:
    from nameparser import HumanName
    NAMEPARSER_AVAILABLE = True
except ImportError:
    NAMEPARSER_AVAILABLE = False

logger = logging.getLogger(__name__)

class UniversalCVExtractor:
    """
    Universal CV Parser - Handles all CV styles and formats:
    - Chronological, Functional, Combination, Modern, Creative CVs
    - International formats (US, EU, Asian styles)
    - PDF, DOCX, Text formats
    - Structured and unstructured layouts
    """
    
    def __init__(self):
        logger.info("🔄 Loading Universal CV Parser...")
        try:
            # Load spaCy model for better international name recognition
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load spaCy: {e}")
            self.nlp = None
        
        try:
            # Multi-language NER model
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
            logger.info("✅ BERT NER model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load BERT: {e}")
            self.ner_pipeline = None
        
        # Universal CV structure patterns
        self.CV_STRUCTURES = {
            'american': {
                'name_position': 'top',
                'contact_sections': ['contact', 'personal', 'information', 'details'],
                'common_formats': ['chronological', 'functional']
            },
            'european': {
                'name_position': 'top_left', 
                'contact_sections': ['personal data', 'contact information', 'coordonnées'],
                'common_formats': ['europass', 'structured']
            },
            'asian': {
                'name_position': 'top_center',
                'contact_sections': ['contact', 'personal particulars', '信息'],
                'common_formats': ['detailed', 'comprehensive']
            },
            'modern': {
                'name_position': 'variable',
                'contact_sections': ['get in touch', 'connect', 'reach me at'],
                'common_formats': ['creative', 'minimalist']
            }
        }
        
        # Enhanced international phone patterns
        self.PHONE_FORMATS = {
            'us_canada': [
                r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
                r'\((\d{3})\)[-.\s]?(\d{3})[-.\s]?(\d{4})'
            ],
            'international': [
                r'\+?(\d{1,3})[-.\s]?\(?(\d{1,4})\)?[-.\s]?(\d{1,4})[-.\s]?(\d{3,4})',
                r'\+?(\d{1,3})[-.\s]?(\d{2,5})[-.\s]?(\d{3,7})'
            ],
            'european': [
                r'\+?(\d{1,3})[-.\s]?(\d{2})[-.\s]?(\d{2})[-.\s]?(\d{2})[-.\s]?(\d{2})',
                r'\(?(\d{2})\)?[-.\s]?(\d{2})[-.\s]?(\d{2})[-.\s]?(\d{2})[-.\s]?(\d{2})'
            ],
            'compact': [
                r'(\d{10,15})',
                r'[\d\s\-\(\)\+]{10,20}'
            ]
        }
        
        # Enhanced email patterns for all formats
        self.EMAIL_PATTERNS = [
            # Standard format
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # With special characters in local part
            r'\b[A-Za-z0-9._%+!$&*-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # International domains
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,10}\b',
            # Fallback without word boundaries
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        ]
        
        # Common false positives to exclude
        self.FALSE_POSITIVES = {
            'emails': ['example.com', 'test.com', 'domain.com', 'email.com', 
                      'company.com', 'yourdomain.com', 'placeholder.com'],
            'phones': ['1234567890', '0000000000', '1111111111', '5555555555'],
            'names': ['Curriculum Vitae', 'Resume', 'CV', 'Application', 'Profile']
        }
        
        logger.info("🎯 Universal CV Parser initialized")

    def detect_cv_style(self, text: str) -> str:
        """Detect the style/structure of the CV"""
        text_lower = text.lower()
        
        # Check for European format indicators
        if any(indicator in text_lower for indicator in ['europass', 'personal data', 'date of birth', 'nationality']):
            return 'european'
        
        # Check for Asian format indicators
        if any(indicator in text_lower for indicator in ['particulars', 'ic', 'identification', 'race', 'religion']):
            return 'asian'
        
        # Check for modern/creative format
        if any(indicator in text_lower for indicator in ['portfolio', 'github', 'behance', 'dribbble', 'linkedin.com/in']):
            return 'modern'
        
        # Default to American style
        return 'american'

    def extract_header_section(self, text: str) -> str:
        """Extract header section from any CV style"""
        lines = text.split('\n')
        header_lines = []
        
        # Take first 10-15 lines as potential header
        potential_header = lines[:15]
        
        for i, line in enumerate(potential_header):
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Stop when we hit major sections
            if self._is_major_section_start(line_clean, i):
                break
                
            header_lines.append(line_clean)
            
            # Also stop if we've collected enough contact info
            if (self._contains_contact_info(' '.join(header_lines)) and 
                len(header_lines) >= 3):
                break
        
        return '\n'.join(header_lines)

    def _is_major_section_start(self, line: str, line_index: int) -> bool:
        """Check if line indicates start of a major section"""
        line_lower = line.lower().strip()
        
        # Common major section headers
        major_sections = [
            'experience', 'work experience', 'employment', 
            'education', 'academic background', 'qualifications',
            'skills', 'technical skills', 'competencies',
            'projects', 'portfolio', 'achievements',
            'summary', 'objective', 'profile'
        ]
        
        # Check for section headers (often in caps, bold, or underlined)
        is_section_header = (
            line_lower in major_sections or
            line.isupper() or
            len(line.split()) <= 4 and any(section in line_lower for section in major_sections) or
            re.search(r'^[A-Z][a-z]+\s*[A-Z][a-z]*$', line) or  # Title Case
            line_index > 8 and len(line_lower) < 30  # Short line after header
        )
        
        return is_section_header

    def _contains_contact_info(self, text: str) -> bool:
        """Check if text contains contact information"""
        text_lower = text.lower()
        contact_indicators = [
            '@',  # Email
            '+',  # International phone
            'phone', 'tel', 'mobile', 'cell',
            'email', 'e-mail', 'mail',
            'linkedin', 'github', 'portfolio'
        ]
        
        return any(indicator in text_lower for indicator in contact_indicators)

    def extract_email_universal(self, text: str) -> str:
        """Universal email extraction for all CV styles"""
        # Strategy 1: Extract header first
        header_section = self.extract_header_section(text)
        
        # Strategy 2: Try multiple search areas with priority
        search_areas = [
            (header_section, 2.0),  # Highest priority - header
            (text[:500], 1.5),      # High priority - beginning
            (text, 1.0)             # Normal priority - entire text
        ]
        
        best_email = ''
        best_score = 0
        
        for area, priority in search_areas:
            emails_found = self._find_emails_in_text(area)
            
            for email in emails_found:
                score = self._score_email_candidate(email, area, priority)
                
                if score > best_score:
                    best_email = email
                    best_score = score
                    logger.info(f"📧 New best email: {email} (score: {score})")
        
        logger.info(f"🎯 Final email selected: {best_email}")
        return best_email

    def _find_emails_in_text(self, text: str) -> List[str]:
        """Find all potential emails in text using multiple patterns"""
        emails = set()
        
        for pattern in self.EMAIL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_email = self._clean_email_candidate(match)
                if clean_email and self._is_valid_email_candidate(clean_email):
                    emails.add(clean_email)
        
        return list(emails)

    def _clean_email_candidate(self, email: str) -> str:
        """Clean email candidate from formatting issues"""
        if not email:
            return ""
        
        # Remove common prefixes
        prefixes = ['mailto:', 'email:', 'e-mail:', 'contact:', 'pe', 'the', 'my', 'our']
        for prefix in prefixes:
            if email.lower().startswith(prefix):
                email = email[len(prefix):]
        
        # Remove trailing punctuation and whitespace
        email = email.strip(' .,;()[]{}"\'<>')
        
        # Fix common OCR/formatting issues
        email = re.sub(r'\s+', '', email)  # Remove whitespace
        email = re.sub(r'\[at\]|\(at\)|\sat\s', '@', email, flags=re.IGNORECASE)
        email = re.sub(r'\[dot\]|\(dot\)|\sdot\s', '.', email, flags=re.IGNORECASE)
        
        return email.lower()

    def _is_valid_email_candidate(self, email: str) -> bool:
        """Validate email candidate"""
        if not email or '@' not in email:
            return False
        
        # Skip false positives
        if any(fp in email for fp in self.FALSE_POSITIVES['emails']):
            return False
        
        local_part, domain = email.split('@', 1)
        
        # Basic validation
        if (len(local_part) < 1 or len(domain) < 4 or
            '..' in email or email.startswith('.') or email.endswith('.')):
            return False
        
        # Check domain structure
        if '.' not in domain or len(domain.split('.')) < 2:
            return False
        
        # Professional validation if available
        if EMAIL_VALIDATOR_AVAILABLE:
            try:
                validate_email(email, check_deliverability=False)
                return True
            except EmailNotValidError:
                return False
        
        return True

    def _score_email_candidate(self, email: str, context: str, area_priority: float) -> float:
        """Score email candidate based on context and location"""
        score = 0.0
        
        # Area priority (header is best)
        score += area_priority
        
        # Context clues
        context_lower = context.lower()
        if any(keyword in context_lower for keyword in ['email', 'e-mail', 'contact']):
            score += 1.0
        
        # Email quality
        if re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email):
            score += 0.5
        
        # Name-based emails (often more reliable)
        if any(part in email for part in ['gmail', 'yahoo', 'hotmail', 'outlook']):
            score += 0.3
        
        return score

    def extract_phone_universal(self, text: str) -> str:
        """Universal phone extraction for all CV styles and formats WITH + SIGN"""
        header_section = self.extract_header_section(text)
        
        # Try professional parsing first (it handles + signs properly)
        if PHONENUMBERS_AVAILABLE:
            try:
                regions = ['US', 'GB', 'FR', 'DE', 'CA', 'AU', 'IN', 'BR', 'TN']
                for region in regions:
                    for match in PhoneNumberMatcher(header_section or text, region):
                        phone_number = match.number
                        if is_valid_number(phone_number):
                            formatted = format_number(phone_number, PhoneNumberFormat.E164)
                            logger.info(f"✅ Phone with +: {formatted}")
                            return formatted  # This includes + sign
            except Exception as e:
                logger.warning(f"⚠️ Professional phone parsing failed: {e}")
        
        # Fallback to regex - add + to valid numbers
        phone = self._extract_phone_regex_advanced(header_section) or self._extract_phone_regex_advanced(text)
        if phone:
            # Add + sign based on number length and format
            formatted_phone = self._format_phone_with_plus(phone)
            logger.info(f"✅ Formatted phone with +: {formatted_phone}")
            return formatted_phone
    
        logger.info("❌ No valid phone found")
        return ''

    def _extract_phone_regex_advanced(self, text: str) -> str:
        """Advanced regex-based phone extraction"""
        best_candidate = ''
        best_score = 0
        
        for format_name, patterns in self.PHONE_FORMATS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    candidate = match.group()
                    clean_candidate = self._clean_phone_candidate(candidate)
                    
                    if self._is_valid_phone_candidate(clean_candidate):
                        score = self._score_phone_candidate(clean_candidate, candidate, text, format_name)
                        if score > best_score:
                            best_candidate = clean_candidate
                            best_score = score
        
        return best_candidate

    def _extract_phone_contextual(self, text: str) -> str:
        """Contextual phone extraction near phone-related keywords"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['phone', 'tel', 'mobile', 'cell', 'contact']):
                # Check this line and surrounding lines
                context_lines = lines[max(0, i-1):min(len(lines), i+2)]
                context_text = '\n'.join(context_lines)
                
                phone = self._extract_phone_regex_advanced(context_text)
                if phone:
                    return phone
        
        return ''

    def _clean_phone_candidate(self, phone: str) -> str:
        """Clean phone number candidate"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Remove leading + for consistency (we'll add it back later)
        if clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        
        # Remove country code for US/Canada if present
        if len(clean_phone) == 11 and clean_phone.startswith('1'):
            clean_phone = clean_phone[1:]
        
        return clean_phone

    def _format_phone_with_plus(self, phone: str) -> str:
        """Format phone number with + sign for international numbers"""
        if not phone:
            return ""
        
        # If it's already 10 digits, assume US/Canada and add +1
        if len(phone) == 10:
            return '+1' + phone
        
        # If it's 11 digits and starts with 1, add + for US/Canada
        elif len(phone) == 11 and phone.startswith('1'):
            return '+' + phone
        
        # For other lengths, add + for international format
        else:
            return '+' + phone

    def _is_valid_phone_candidate(self, phone: str) -> bool:
        """Validate phone number candidate"""
        if not phone or not phone.isdigit():
            return False
        
        # Skip false positives
        if phone in self.FALSE_POSITIVES['phones']:
            return False
        
        length = len(phone)
        
        # Valid lengths for different formats
        valid_lengths = {
            7: 0.3,   # Local numbers
            10: 1.0,  # Standard US/International
            11: 0.8,  # With country code
            12: 0.6,  # International
            13: 0.5,  # International
            14: 0.4,  # International
            15: 0.3   # International
        }
        
        return length in valid_lengths

    def _score_phone_candidate(self, clean_phone: str, original: str, context: str, format_type: str) -> float:
        """Score phone number candidate"""
        score = 0.0
        
        # Length-based scoring
        length_scores = {7: 0.3, 10: 1.0, 11: 0.8, 12: 0.6, 13: 0.5, 14: 0.4, 15: 0.3}
        score += length_scores.get(len(clean_phone), 0.1)
        
        # Format type preference
        format_scores = {'us_canada': 1.0, 'international': 0.9, 'european': 0.8, 'compact': 0.6}
        score += format_scores.get(format_type, 0.5)
        
        # Context scoring
        context_lower = context.lower()
        if any(keyword in context_lower for keyword in ['phone', 'tel', 'mobile', 'cell']):
            score += 0.5
        
        # Formatting scoring (well-formatted numbers are more reliable)
        if re.search(r'[\(\)\-\.\s]', original):
            score += 0.3
        
        return min(score, 2.0)  # Cap at 2.0

    # KEEP THE WORKING NAME EXTRACTION (it works well)
    def extract_name_universal(self, text: str) -> Dict[str, str]:
        """Universal name extraction using multiple strategies"""
        # Try multiple strategies in order of reliability
        strategies = [
            self._extract_name_from_header,
            self._extract_name_structured,
            self._extract_name_ml
        ]
        
        for strategy in strategies:
            name_info = strategy(text)
            if name_info and name_info["first_name"]:
                logger.info(f"✅ Name found with {strategy.__name__}: {name_info}")
                return name_info
        
        return {"first_name": "", "last_name": ""}

    def _extract_name_from_header(self, text: str) -> Dict[str, str]:
        """Extract name from header section"""
        header = self.extract_header_section(text)
        lines = [line.strip() for line in header.split('\n') if line.strip()]
        
        # First non-empty line is often the name
        for line in lines[:3]:  # Check first 3 lines of header
            if (len(line) > 2 and len(line) < 50 and 
                not any(fp in line.lower() for fp in self.FALSE_POSITIVES['names']) and
                not any(keyword in line.lower() for keyword in ['email', 'phone', '@', 'http'])):
                
                name_info = self._parse_name_candidate(line)
                if name_info["first_name"]:
                    return name_info
        
        return {"first_name": "", "last_name": ""}

    def _extract_name_structured(self, text: str) -> Dict[str, str]:
        """Structured name extraction (your existing working method)"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            
            if not line or len(line) > 100:
                continue
                
            if any(keyword in line.lower() for keyword in ['email', 'phone', '@', 'http', 'linkedin', 'github']):
                continue
            
            words = line.split()
            
            if 2 <= len(words) <= 4:
                capitalized_words = sum(1 for word in words if word and word[0].isupper())
                
                if capitalized_words >= len(words) - 1:
                    clean_name = self._clean_name_line(line)
                    if clean_name:
                        return self._parse_name_parts(clean_name)
        
        return {"first_name": "", "last_name": ""}

    def _extract_name_ml(self, text: str) -> Dict[str, str]:
        """ML-based name extraction fallback"""
        # Your existing spaCy and BERT methods here
        if self.nlp:
            try:
                preview = text[:500]
                doc = self.nlp(preview)
                
                persons = []
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        persons.append(ent.text)
                
                if persons:
                    return self._parse_name_parts(persons[0])
            except Exception:
                pass
        
        return {"first_name": "", "last_name": ""}

    def _parse_name_candidate(self, text: str) -> Dict[str, str]:
        """Parse name candidate into first and last name"""
        # Remove common titles and clean
        titles = ['dr', 'mr', 'ms', 'mrs', 'prof', 'professor', 'phd', 'md', 'eng']
        words = [word.strip('.,;') for word in text.split()]
        clean_words = [word for word in words if word.lower() not in titles]
        clean_name = ' '.join(clean_words)
        
        return self._parse_name_parts(clean_name)

    def _clean_name_line(self, line: str) -> str:
        """Clean name line (your existing method)"""
        titles = ['dr', 'mr', 'ms', 'mrs', 'prof', 'professor', 'phd', 'md']
        words = line.split()
        cleaned_words = []
        
        for word in words:
            clean_word = word.strip('.,;')
            if clean_word.lower() not in titles:
                cleaned_words.append(clean_word)
        
        return ' '.join(cleaned_words)

    def _parse_name_parts(self, full_name: str) -> Dict[str, str]:
        """Parse name parts (your existing method)"""
        if not full_name:
            return {"first_name": "", "last_name": ""}
        
        if NAMEPARSER_AVAILABLE:
            try:
                name = HumanName(full_name)
                result = {
                    "first_name": name.first or "",
                    "last_name": name.last or "",
                }
                if result["first_name"]:
                    return result
            except Exception:
                pass
        
        clean_name = re.sub(r'[^\w\s]', '', full_name).strip()
        name_parts = clean_name.split()
        
        if not name_parts:
            return {"first_name": "", "last_name": ""}
        elif len(name_parts) == 1:
            return {"first_name": name_parts[0], "last_name": ""}
        else:
            return {
                "first_name": name_parts[0],
                "last_name": " ".join(name_parts[1:])
            }

    def extract_all_info(self, cv_text: str) -> Dict[str, str]:
        """Universal CV information extraction"""
        logger.info("🚀 UNIVERSAL CV EXTRACTION STARTED")
        
        try:
            # Detect CV style
            cv_style = self.detect_cv_style(cv_text)
            logger.info(f"📋 Detected CV style: {cv_style}")
            
            # Extract information
            email = self.extract_email_universal(cv_text)
            phone = self.extract_phone_universal(cv_text)
            name_info = self.extract_name_universal(cv_text)
            
            final_result = {
                "first_name": name_info["first_name"],
                "last_name": name_info["last_name"], 
                "email": email,
                "phone_number": phone,
                "detected_style": cv_style
            }
            
            logger.info(f"🎉 UNIVERSAL EXTRACTION RESULT: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"💥 UNIVERSAL EXTRACTION FAILED: {e}")
            import traceback
            logger.error(f"💥 TRACEBACK: {traceback.format_exc()}")
            return {"first_name": "", "last_name": "", "email": "", "phone_number": ""}

# Global instance
_universal_extractor_instance = None

def get_universal_cv_extractor():
    global _universal_extractor_instance
    if _universal_extractor_instance is None:
        _universal_extractor_instance = UniversalCVExtractor()
    return _universal_extractor_instance

# Backward compatibility
def get_enhanced_cv_extractor():
    return get_universal_cv_extractor()

def get_cv_extractor():
    return get_universal_cv_extractor()