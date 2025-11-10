# using nlp models
import logging
import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy

# Setup logging
logger = logging.getLogger(__name__)

class DynamicSkillAnalyzer:
    """
    Optimized Domain-Agnostic Skill Analyzer - Clean skills across all industries
    """
    
    DEFAULT_CONFIG = {
        "model_name": 'all-MiniLM-L6-v2',
        "similarity_threshold": 0.5,  # Increased for better precision
        "weight_overlap": 0.6,
        "weight_semantic": 0.4,
    }

    def __init__(self, config=None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        self.sentence_model = SentenceTransformer(self.config["model_name"])
        self.ner_model = spacy.load("en_core_web_lg")
        
        self.SIMILARITY_THRESHOLD = self.config["similarity_threshold"]
        self.WEIGHT_OVERLAP = self.config["weight_overlap"]
        self.WEIGHT_SEMANTIC = self.config["weight_semantic"]
        
        # Store text for evidence validation
        self.cv_text = ""
        self.jd_text = ""
        
        # Comprehensive tools and platforms across domains
        self.TOOLS_PLATFORMS = {
            # Technical
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
            'django', 'flask', 'spring', 'react', 'angular', 'vue', 'node.js', 'express', 'laravel', 'rails',
            'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github',
            'mysql', 'mongodb', 'postgresql', 'redis', 'cassandra', 'dynamodb', 'oracle',
            'git', 'jira', 'confluence', 'linux', 'unix', 'bash', 'shell',
            
            # Marketing
            'google analytics', 'google ads', 'facebook ads', 'mailchimp', 'hubspot',
            'hootsuite', 'buffer', 'sprout social', 'semrush', 'ahrefs', 'moz',
            'linkedin', 'instagram', 'twitter', 'tiktok', 'pinterest',
            
            # Business
            'excel', 'powerpoint', 'word', 'outlook', 'salesforce', 'sap', 'oracle',
            'trello', 'asana', 'slack', 'teams',
            
            # Design
            'figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'indesign',
            'canva', 'invision', 'marvel', 'principle',
            
            # Healthcare
            'epic', 'cerner', 'meditech', 'allscripts', 'ehr', 'emr'
        }
        
        # Clean skill categories (no partial phrases)
        self.SKILL_CATEGORIES = {
            # Marketing
            'seo', 'ppc', 'social media', 'email marketing', 'content marketing',
            'digital marketing', 'analytics', 'conversion optimization', 'crm',
            'market research', 'brand management', 'advertising',
            
            # Technical
            'web development', 'mobile development', 'cloud computing', 'devops',
            'database management', 'system administration', 'cybersecurity',
            'machine learning', 'data science', 'api development', 'microservices',
            
            # Business
            'project management', 'business analysis', 'financial analysis',
            'strategic planning', 'stakeholder management', 'process improvement',
            'risk management', 'budget management', 'team leadership',
            
            # Design
            'ux design', 'ui design', 'graphic design', 'user research',
            'prototyping', 'wireframing', 'visual design',
            
            # Healthcare
            'patient care', 'medical coding', 'clinical research', 'healthcare administration',
            'medical terminology', 'treatment planning'
        }
        
        # Enhanced exclusion patterns
        self.EXCLUDE_PATTERNS = [
            # Job titles
            r'^senior\s+\w+$', r'^junior\s+\w+$', r'^lead\s+\w+$', r'^principal\s+\w+$', 
            r'^digital\s+manager$', r'^marketing\s+manager$', r'^software\s+engineer$',
            
            # Partial phrases and generic terms
            r'^analyze\s+performance$', r'^comprehensive\s+marketing$', r'^digital\s+strategies$',
            r'^experienced\s+marketing$', r'^manage\s+marketing$', r'^marketing\s+using$',
            r'^media\s+efforts$', r'^optimize\s+campaigns$', r'^social\s+marketing$',
            r'^in\s+marketing$', r'^digital$', r'^email\s+campaigns$',
            
            # Too generic
            r'^strategies$', r'^campaigns$', r'^efforts$', r'^performance$', r'^using$',
            r'^teams$', r'^team$'
        ]
        
        logger.info("Optimized Domain-Agnostic Skill Analyzer initialized.")

    def extract_meaningful_skills(self, text):
        """Extract clean, meaningful skills across all domains"""
        if not text or len(text.strip()) < 10:
            return []
        
        skills = set()
        
        # Extract using focused methods
        skills.update(self._extract_tools_platforms(text))
        skills.update(self._extract_skill_categories(text))
        skills.update(self._extract_clean_skills_from_sections(text))
        
        # Apply strict filtering
        filtered_skills = self._apply_clean_filters(skills)
        
        logger.info(f"Extracted {len(filtered_skills)} clean skills: {filtered_skills}")
        return filtered_skills

    def _extract_tools_platforms(self, text):
        """Extract specific tools and platforms"""
        skills = set()
        text_lower = text.lower()
        
        for tool in self.TOOLS_PLATFORMS:
            pattern = r'\b' + re.escape(tool) + r'\b'
            if re.search(pattern, text_lower):
                skills.add(tool.title())
        
        return skills

    def _extract_skill_categories(self, text):
        """Extract clean skill categories"""
        skills = set()
        text_lower = text.lower()
        
        for skill in self.SKILL_CATEGORIES:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                skills.add(skill.title())
        
        return skills

    def _extract_clean_skills_from_sections(self, text):
        """Extract clean skills from sections only"""
        skills = set()
        
        section_patterns = {
            'skills': r'skills?[^:]*:([^•]+?(?=\n\s*\n|\n\s*[A-Z]|\Z))',
            'technologies': r'technologies?[^:]*:([^•]+?(?=\n\s*\n|\n\s*[A-Z]|\Z))',
            'tools': r'tools?[^:]*:([^•]+?(?=\n\s*\n|\n\s*[A-Z]|\Z))',
        }
        
        for section_name, pattern in section_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                items = re.split(r'[,\n•\-]', match)
                for item in items:
                    skill = self._clean_skill_item(item.strip())
                    if skill and self._is_clean_skill(skill):
                        skills.add(skill)
        
        return skills

    def _clean_skill_item(self, item):
        """Clean and normalize skill items strictly"""
        if not item:
            return None
        
        # Remove markdown and punctuation
        item = re.sub(r'[\*\#\`\-\•\(\)]', ' ', item).strip()
        item = re.sub(r'\s+', ' ', item)
        
        # Remove common prefixes/suffixes
        item = re.sub(r'^(?:experience with|proficient in|knowledge of|strong|excellent|basic|assisted with|participated in)\s+', '', item, flags=re.IGNORECASE)
        item = re.sub(r'\s+(?:management|marketing|development|design|analysis|optimization|strategy|campaigns|efforts)$', '', item, flags=re.IGNORECASE)
        
        # Must be a clean, meaningful skill
        words = item.split()
        if 1 <= len(words) <= 3 and 2 <= len(item) <= 30:
            return item.title()
        
        return None

    def _is_clean_skill(self, skill):
        """Strict validation for clean skills only"""
        skill_lower = skill.lower()
        
        # Exclude partial phrases and generic terms
        if any(re.search(pattern, skill_lower) for pattern in self.EXCLUDE_PATTERNS):
            return False
        
        # Must be a known tool/platform or skill category
        is_tool = any(tool in skill_lower for tool in self.TOOLS_PLATFORMS)
        is_skill_category = any(category in skill_lower for category in self.SKILL_CATEGORIES)
        
        return is_tool or is_skill_category

    def _apply_clean_filters(self, skills):
        """Apply final clean filters"""
        filtered_skills = []
        seen_lower = set()
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            
            if (skill_lower not in seen_lower and 
                self._is_clean_skill(skill)):
                filtered_skills.append(skill)
                seen_lower.add(skill_lower)
        
        # Remove duplicates and sort
        return sorted(list(set(filtered_skills)))

    # IMPROVED EVIDENCE EXTRACTION METHODS
    def _find_contextual_evidence(self, text, skill):
        """Improved evidence extraction that finds actual skill mentions"""
        if not text or not skill:
            return None
        
        skill_lower = skill.lower()
        text_lower = text.lower()
        
        # Split into meaningful segments (sentences, bullet points, list items)
        segments = self._split_into_meaningful_segments(text)
        
        # 1. First priority: Exact match in segments
        for segment in segments:
            segment_lower = segment.lower()
            if skill_lower in segment_lower:
                # Check if this is a meaningful context (not just in education/header)
                if self._is_meaningful_context(segment, skill):
                    return segment.strip()
        
        # 2. Second priority: Multi-word skill partial matching
        skill_words = skill_lower.split()
        if len(skill_words) > 1:
            for segment in segments:
                segment_lower = segment.lower()
                if all(word in segment_lower for word in skill_words):
                    if self._is_meaningful_context(segment, skill):
                        return segment.strip()
        
        # 3. Third priority: Look for skill in technical sections only
        technical_segments = self._extract_technical_segments(text)
        for segment in technical_segments:
            segment_lower = segment.lower()
            if skill_lower in segment_lower:
                return segment.strip()
        
        # 4. Final fallback: Find any occurrence but filter out bad contexts
        if skill_lower in text_lower:
            # Use regex to find the skill with context, avoiding education sections
            pattern = r'([^.!?]*?' + re.escape(skill) + r'[^.!?]*[.!?])'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if self._is_meaningful_context(match, skill):
                    return match.strip()
        
        return None

    def _split_into_meaningful_segments(self, text):
        """Split text into meaningful segments (not just sentences)"""
        segments = []
        
        # Split by sentences, bullet points, and list items
        raw_segments = re.split(r'[.!?]+|(?:\n\s*)[•\-*]\s*|(?:\n\s*)\d+\.\s*', text)
        
        for segment in raw_segments:
            clean_segment = segment.strip()
            # Filter out very short segments and education-like segments
            if (len(clean_segment) >= 10 and 
                len(clean_segment.split()) >= 3 and
                not self._is_education_section(clean_segment)):
                segments.append(clean_segment)
        
        return segments

    def _is_education_section(self, text):
        """Check if text is from education section (should be excluded from evidence)"""
        education_indicators = [
            'education', 'university', 'college', 'school', 'baccalaureat',
            'bachelor', 'master', 'phd', 'degree', 'diploma', 'graduat',
            'faculty', 'institute', 'academy', 'esprit', 'tunisia'
        ]
        
        text_lower = text.lower()
        education_keywords = sum(1 for indicator in education_indicators if indicator in text_lower)
        
        # If contains multiple education keywords, likely education section
        return education_keywords >= 2

    def _is_meaningful_context(self, text, skill):
        """Check if the context is meaningful for skill evidence"""
        text_lower = text.lower()
        skill_lower = skill.lower()
        
        # Exclude education sections
        if self._is_education_section(text):
            return False
        
        # Exclude very generic contexts
        generic_contexts = [
            'education', 'university', 'college', 'school',
            'name', 'address', 'phone', 'email', 'contact'
        ]
        
        if any(context in text_lower for context in generic_contexts):
            return False
        
        # Check if skill appears in a meaningful way (not just in a list)
        words = text_lower.split()
        skill_position = text_lower.find(skill_lower)
        
        # If skill is in a very short segment, it might just be a list item
        if len(words) <= 4:
            return False
        
        return True

    def _extract_technical_segments(self, text):
        """Extract segments from technical sections only"""
        technical_segments = []
        
        # Common technical section headers
        technical_headers = [
            'skills', 'experience', 'work', 'projects', 'technical',
            'technologies', 'tools', 'frameworks', 'languages',
            'proficiencies', 'expertise', 'qualifications'
        ]
        
        lines = text.split('\n')
        in_technical_section = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line starts a technical section
            if any(header in line_lower for header in technical_headers):
                in_technical_section = True
                continue
            
            # Check if we're leaving technical section (new major section)
            if (line_lower and 
                len(line.split()) <= 4 and 
                line[0].isupper() and 
                not any(header in line_lower for header in technical_headers)):
                in_technical_section = False
            
            # If in technical section and line is meaningful, add it
            if in_technical_section and len(line.strip()) >= 5:
                technical_segments.append(line.strip())
        
        return technical_segments

    def _find_better_evidence(self, text, skill, current_evidence):
        """Try to find better evidence if current is from education section"""
        # Look in technical sections specifically
        technical_segments = self._extract_technical_segments(text)
        
        for segment in technical_segments:
            if skill.lower() in segment.lower():
                return segment.strip()
        
        return current_evidence  # Return original if no better evidence found

    def _truncate_evidence(self, evidence, max_length=120):
        """Truncate evidence for display"""
        if not evidence:
            return "Not specifically demonstrated"
        
        if len(evidence) <= max_length:
            return evidence
        
        truncated = evidence[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.6:
            return truncated[:last_space] + "..."
        
        return truncated + "..."

    # IMPROVED MATCHING ALGORITHM
    def _flexible_skill_matching(self, cv_skills, jd_skills):
        """Improved skill matching with better evidence validation"""
        matched_pairs = []
        missing_skills = []
        
        for jd_skill in jd_skills:
            best_match = None
            best_score = 0.0

            for cv_skill in cv_skills:
                overlap_score = self._keyword_overlap(cv_skill, jd_skill)
                semantic_score = self._semantic_similarity(cv_skill, jd_skill)
                
                combined_score = (overlap_score * self.WEIGHT_OVERLAP) + (semantic_score * self.WEIGHT_SEMANTIC)
                
                if combined_score > best_score:
                    best_match, best_score = cv_skill, combined_score
            
            # Only count as matched if we have good score
            if best_score >= self.SIMILARITY_THRESHOLD:
                matched_pairs.append((best_match, jd_skill, best_score))
            else:
                missing_skills.append(jd_skill)

        return matched_pairs, missing_skills

    def _keyword_overlap(self, s1, s2):
        """Calculate keyword overlap"""
        if not s1 or not s2: 
            return 0.0
        
        w1 = set(re.findall(r'\b\w+\b', s1.lower()))
        w2 = set(re.findall(r'\b\w+\b', s2.lower()))
        
        if not w1 or not w2:
            return 0.0
            
        intersection = w1 & w2
        union = w1 | w2
        
        return len(intersection) / len(union) if union else 0.0

    def _semantic_similarity(self, s1, s2):
        """Calculate semantic similarity"""
        try:
            emb1 = self.sentence_model.encode([s1])
            emb2 = self.sentence_model.encode([s2])
            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(similarity)
        except Exception:
            return 0.0

    # MAIN ANALYSIS METHOD WITH IMPROVED EVIDENCE
    def analyze_skill_gap(self, cv_text, jd_text):
        """Main skill gap analysis with improved evidence"""
        # Store texts for evidence validation
        self.cv_text = cv_text
        self.jd_text = jd_text
        
        cv_skills = self.extract_meaningful_skills(cv_text)
        jd_skills = self.extract_meaningful_skills(jd_text)
        
        jd_skills = [re.sub(r'[\*`#]', '', skill).strip() for skill in jd_skills]
        
        matched_pairs, missing_skills_list = self._flexible_skill_matching(cv_skills, jd_skills)
        
        # Generate evidence with improved logic
        matched_evidence = []
        for cv_skill, jd_skill, sim in matched_pairs:
            cv_ev = self._find_contextual_evidence(cv_text, cv_skill)
            jd_ev = self._find_contextual_evidence(jd_text, jd_skill)
            
            # If evidence is from education section, try to find better evidence
            if cv_ev and self._is_education_section(cv_ev):
                cv_ev = self._find_better_evidence(cv_text, cv_skill, cv_ev)
            
            matched_evidence.append({
                "skill": jd_skill,
                "cv_skill": cv_skill,
                "evidence_cv": self._truncate_evidence(cv_ev),
                "evidence_jd": self._truncate_evidence(jd_ev),
                "similarity": round(sim, 2)
            })

        # Generate evidence for missing skills
        missing_evidence = []
        for skill in missing_skills_list:
            jd_full_context = self._find_contextual_evidence(jd_text, skill)
            missing_evidence.append({
                "skill": skill,
                "evidence_jd": self._truncate_evidence(jd_full_context),
                "jd_requirement_text": jd_full_context
            })

        match_percentage = (len(matched_pairs) / len(jd_skills)) * 100 if jd_skills else 0.0

        structured_missing_skills = [
            {
                "skill": item["skill"], 
                "jd_requirement": item["jd_requirement_text"] or "JD requirement"
            }
            for item in missing_evidence
        ]

        evidence_data = self._create_frontend_evidence(matched_evidence, missing_evidence)

        return {
            "matched_skills": matched_evidence,
            "missing_skills": structured_missing_skills, 
            "cv_skill_count": len(cv_skills),
            "jd_skill_count": len(jd_skills),
            "match_percentage": round(match_percentage, 1),
            "evidence": evidence_data 
        }

    def _create_frontend_evidence(self, matched_skills, missing_skills_data):
        """Create frontend evidence structure"""
        evidence_list = []
        
        for skill in matched_skills:
            evidence_list.append({
                "skill": skill["skill"],
                "status": "matched",
                "cv_sentence": skill["evidence_cv"],
                "jd_sentence": skill["evidence_jd"],
                "similarity": skill["similarity"],
                "matched_skill": skill["cv_skill"]
            })

        for skill_data in missing_skills_data:
            evidence_list.append({
                "skill": skill_data["skill"],
                "status": "missing",
                "cv_sentence": "Not specifically demonstrated in CV",
                "jd_sentence": skill_data["evidence_jd"],
                "similarity": 0,
                "matched_skill": None
            })
        
        return evidence_list


# Global instance
dynamic_skill_analyzer = DynamicSkillAnalyzer()