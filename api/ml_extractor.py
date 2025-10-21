import spacy
import re
import torch
from transformers import pipeline
import logging
from typing import Dict, List

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

class CVInformationExtractor:
    def __init__(self):
        logger.info("🔄 Loading ML models...")
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load spaCy: {e}")
            self.nlp = None
        
        try:
            # Load BERT NER model
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
            logger.info("✅ BERT NER model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load BERT: {e}")
            self.ner_pipeline = None
        
        # Log available professional features
        if EMAIL_VALIDATOR_AVAILABLE:
            logger.info("🎯 Professional email validation enabled")
        if PHONENUMBERS_AVAILABLE:
            logger.info("🎯 Professional phone validation enabled")
        if NAMEPARSER_AVAILABLE:
            logger.info("🎯 Professional name parsing enabled")
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess CV text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_email(self, text: str) -> str:
        """Professional email extraction with advanced validation"""
        # Simple email pattern that works reliably
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        
        logger.info(f"📧 Found potential emails: {emails}")
        
        valid_emails = []
        for email in emails:
            email_lower = email.lower().strip()
            
            # Skip obvious false positives
            if len(email_lower) < 5 or '..' in email_lower or email_lower.startswith('.'):
                continue
            
            # Skip common fake emails
            if any(domain in email_lower for domain in ['example.com', 'test.com', 'domain.com', 'email.com']):
                continue
            
            if EMAIL_VALIDATOR_AVAILABLE:
                try:
                    # Professional email validation
                    valid = validate_email(email_lower, check_deliverability=False)
                    valid_emails.append(valid.email)
                    logger.info(f"✅ Validated email: {valid.email}")
                    continue
                except EmailNotValidError as e:
                    logger.info(f"❌ Email validation failed for {email_lower}: {e}")
                    continue
            
            # Fallback basic validation
            if '@' in email_lower and '.' in email_lower.split('@')[1]:
                valid_emails.append(email_lower)
                logger.info(f"✅ Basic validation passed for: {email_lower}")
        
        result = valid_emails[0] if valid_emails else ''
        logger.info(f"🎯 Final email result: {result}")
        return result
    
    def extract_phone(self, text: str) -> str:
        """Professional phone number extraction - SIMPLIFIED"""
        # First try professional phone number parsing
        if PHONENUMBERS_AVAILABLE:
            try:
                for match in PhoneNumberMatcher(text, None):  # International
                    phone_number = match.number
                    if is_valid_number(phone_number):
                        formatted = format_number(phone_number, PhoneNumberFormat.E164)
                        logger.info(f"✅ Validated phone: {formatted}")
                        return formatted
            except Exception as e:
                logger.warning(f"⚠️ Phone number parsing failed: {e}")
        
        # SIMPLIFIED regex patterns - no complex ranges
        phone_patterns = [
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
        ]
        
        for pattern in phone_patterns:
            try:
                phones = re.findall(pattern, text)
                if phones:
                    logger.info(f"📞 Found phones with regex: {phones}")
                    # Clean the phone number (keep only digits)
                    clean_phone = re.sub(r'[^\d]', '', phones[0])
                    # Basic validation
                    if len(clean_phone) == 10:
                        logger.info(f"✅ Regex phone result: {clean_phone}")
                        return clean_phone
            except Exception as e:
                logger.warning(f"⚠️ Regex pattern failed: {pattern} - {e}")
                continue
        
        logger.info("❌ No valid phone found")
        return ''
    
    def extract_name_simple(self, text: str) -> Dict[str, str]:
        """Simple but reliable name extraction - focus on CV structure"""
        lines = text.split('\n')
        logger.info(f"📄 Checking first 5 lines for name: {lines[:5]}")
        
        # Check first 5 lines for name-like patterns
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            
            # Skip empty lines or very long lines
            if not line or len(line) > 100:
                continue
                
            # Skip lines with obvious contact info
            if any(keyword in line.lower() for keyword in ['email', 'phone', '@', 'http', 'linkedin', 'github']):
                continue
            
            words = line.split()
            
            # Look for 2-4 word lines that look like names
            if 2 <= len(words) <= 4:
                # Check if most words are capitalized (like names)
                capitalized_words = sum(1 for word in words if word and word[0].isupper())
                
                if capitalized_words >= len(words) - 1:  # Allow one non-capitalized word
                    logger.info(f"🎯 Potential name found: '{line}'")
                    
                    # Clean the name (remove titles, etc.)
                    clean_name = self._clean_name_line(line)
                    if clean_name:
                        result = self._parse_name_parts(clean_name)
                        if result["first_name"]:
                            logger.info(f"✅ Name extracted via structure: {result}")
                            return result
        
        logger.info("❌ No name found via structure")
        return {"first_name": "", "last_name": ""}
    
    def extract_name_with_spacy(self, text: str) -> Dict[str, str]:
        """Try spaCy NER for name extraction"""
        if not self.nlp:
            return {"first_name": "", "last_name": ""}
            
        try:
            # Use first 500 chars for better context
            preview = text[:500]
            doc = self.nlp(preview)
            
            # Look for PERSON entities
            persons = []
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    persons.append(ent.text)
            
            if persons:
                logger.info(f"✅ spaCy found persons: {persons}")
                return self._parse_name_parts(persons[0])
                
        except Exception as e:
            logger.error(f"❌ spaCy failed: {e}")
        
        return {"first_name": "", "last_name": ""}
    
    def extract_name_with_bert(self, text: str) -> Dict[str, str]:
        """Try BERT NER for name extraction"""
        if not self.ner_pipeline:
            return {"first_name": "", "last_name": ""}
            
        try:
            preview = text[:500]
            entities = self.ner_pipeline(preview)
            
            # Look for person entities
            persons = []
            for entity in entities:
                if entity['entity_group'] == 'PER' and entity['score'] > 0.8:
                    word = entity['word'].replace('##', '')
                    if word.strip():
                        persons.append(word)
            
            if persons:
                logger.info(f"✅ BERT found persons: {persons}")
                full_name = ' '.join(persons[:2])  # Combine first 2 person words
                return self._parse_name_parts(full_name)
                
        except Exception as e:
            logger.error(f"❌ BERT failed: {e}")
        
        return {"first_name": "", "last_name": ""}
    
    def _clean_name_line(self, line: str) -> str:
        """Remove common titles from name line"""
        titles = ['dr', 'mr', 'ms', 'mrs', 'prof', 'professor', 'phd', 'md']
        words = line.split()
        cleaned_words = []
        
        for word in words:
            clean_word = word.strip('.,;')
            if clean_word.lower() not in titles:
                cleaned_words.append(clean_word)
        
        return ' '.join(cleaned_words)
    
    def _parse_name_parts(self, full_name: str) -> Dict[str, str]:
        """Professional name parsing with nameparser fallback"""
        if not full_name:
            return {"first_name": "", "last_name": ""}
        
        if NAMEPARSER_AVAILABLE:
            try:
                # Professional name parsing
                name = HumanName(full_name)
                result = {
                    "first_name": name.first or "",
                    "last_name": name.last or "",
                }
                # Only return if we have at least a first name
                if result["first_name"]:
                    logger.info(f"✅ Nameparser parsed: '{full_name}' -> {result}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Nameparser failed for '{full_name}': {e}")
        
        # Fallback to basic parsing
        clean_name = re.sub(r'[^\w\s]', '', full_name).strip()
        name_parts = clean_name.split()
        
        if not name_parts:
            return {"first_name": "", "last_name": ""}
        elif len(name_parts) == 1:
            return {"first_name": name_parts[0], "last_name": ""}
        else:
            result = {
                "first_name": name_parts[0],
                "last_name": " ".join(name_parts[1:])
            }
            logger.info(f"✅ Basic parsing: '{full_name}' -> {result}")
            return result
    
    def extract_all_info(self, cv_text: str) -> Dict[str, str]:
        """Main extraction method with professional validation"""
        logger.info("🚀 STARTING PROFESSIONAL CV EXTRACTION")
        
        try:
            # Clean the text first
            clean_text = self.clean_text(cv_text)
            logger.info(f"📄 Processing text length: {len(clean_text)} chars")
            
            # Extract email and phone first (most reliable)
            email = self.extract_email(clean_text)
            phone = self.extract_phone(clean_text)
            
            # Try multiple name extraction methods in order of reliability
            name_methods = [
                self.extract_name_simple,      # Most reliable for CVs (structure-based)
                self.extract_name_with_spacy,  # ML fallback
                self.extract_name_with_bert,   # Last resort
            ]
            
            name_info = {"first_name": "", "last_name": ""}
            
            for method in name_methods:
                result = method(clean_text)
                if result["first_name"]:
                    name_info = result
                    logger.info(f"✅ Name found with {method.__name__}")
                    break
            
            final_result = {
                "first_name": name_info["first_name"],
                "last_name": name_info["last_name"], 
                "email": email,
                "phone_number": phone
            }
            
            logger.info(f"🎉 FINAL PROFESSIONAL EXTRACTION: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"💥 EXTRACTION CRASHED: {e}")
            import traceback
            logger.error(f"💥 TRACEBACK: {traceback.format_exc()}")
            return {"first_name": "", "last_name": "", "email": "", "phone_number": ""}

# Global instance with lazy loading
_extractor_instance = None

def get_cv_extractor():
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = CVInformationExtractor()
    return _extractor_instance