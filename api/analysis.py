import re
import logging

logger = logging.getLogger(__name__)

class SkillAnalyzer:
    def __init__(self):
        self.technical_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php'],
            'web_frameworks': ['django', 'flask', 'react', 'angular', 'vue', 'spring', 'spring boot'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle'],
            'cloud': ['aws', 'amazon web services', 'azure', 'google cloud', 'docker', 'kubernetes'],
            'tools': ['git', 'jenkins', 'jira', 'linux', 'bash'],
        }
        
        self.soft_skills = [
            'leadership', 'team leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'adaptability', 'time management', 'project management'
        ]
        
        self.all_skills = []
        for category in self.technical_skills.values():
            self.all_skills.extend(category)
        self.all_skills.extend(self.soft_skills)
        self.all_skills = list(set(self.all_skills))
        
        logger.info(f"Skill analyzer initialized with {len(self.all_skills)} skills")

    def extract_skills_from_text(self, text):
        if not text or len(text.strip()) < 10:
            return []
            
        text_lower = text.lower()
        found_skills = set()
        
        for skill in self.all_skills:
            if self._exact_skill_match(skill, text_lower):
                found_skills.add(skill)
        
        logger.info(f"Extracted skills: {list(found_skills)}")
        return list(found_skills)

    def _exact_skill_match(self, skill, text_lower):
        if ' ' in skill:
            pattern = r'\b' + re.escape(skill) + r'\b'
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
        
        return re.search(pattern, text_lower) is not None

    def analyze_skill_gap(self, cv_text, jd_text):
        logger.info("Starting skill gap analysis")
        
        cv_skills = self.extract_skills_from_text(cv_text)
        jd_skills = self.extract_skills_from_text(jd_text)
        
        logger.info(f"CV skills: {cv_skills}")
        logger.info(f"JD skills: {jd_skills}")
        
        matched_skills = set(cv_skills) & set(jd_skills)
        missing_skills = set(jd_skills) - set(cv_skills)
        
        matched_skills = self._deduplicate_skills(matched_skills)
        missing_skills = self._deduplicate_skills(missing_skills)
        
        logger.info(f"Final matched: {matched_skills}")
        logger.info(f"Final missing: {missing_skills}")
        
        matched_evidence = []
        for skill in matched_skills:
            cv_evidence = self._find_exact_skill_evidence(skill, cv_text)
            jd_evidence = self._find_exact_skill_evidence(skill, jd_text)
            matched_evidence.append({
                'skill': skill.title(),
                'evidence_cv': cv_evidence,
                'evidence_jd': jd_evidence
            })
        
        missing_evidence = []
        for skill in missing_skills:
            jd_evidence = self._find_exact_skill_evidence(skill, jd_text)
            missing_evidence.append({
                'skill': skill.title(),
                'evidence_jd': jd_evidence
            })
        
        detailed_evidence = []
        for skill in jd_skills:
            if skill in ['team leadership', 'leadership'] and 'leadership' in matched_skills:
                continue
                
            cv_sentence = self._find_exact_skill_evidence(skill, cv_text)
            jd_sentence = self._find_exact_skill_evidence(skill, jd_text)
            
            status = "matched" if skill in matched_skills else "missing"
            
            detailed_evidence.append({
                'skill': skill.title(),
                'cv_sentence': cv_sentence,
                'jd_sentence': jd_sentence,
                'status': status
            })
        
        match_percentage = len(matched_skills) / len(jd_skills) * 100 if jd_skills else 0
        
        result = {
            'matched_skills': matched_evidence,
            'missing_skills': missing_evidence,
            'evidence': detailed_evidence,
            'cv_skill_count': len(cv_skills),
            'jd_skill_count': len(jd_skills),
            'match_percentage': match_percentage
        }
        
        logger.info(f"Analysis complete: {match_percentage:.1f}% match")
        return result

    def _deduplicate_skills(self, skills):
        skills_list = list(skills)
        if 'team leadership' in skills_list and 'leadership' in skills_list:
            skills_list.remove('team leadership')
        return set(skills_list)

    def _find_exact_skill_evidence(self, skill, text):
        if not text:
            return f"Looking for {skill} experience"
        
        sentences = re.split(r'[.!?\n]+', text)
        
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) < 5:
                continue
                
            if self._exact_skill_match(skill, sentence_clean.lower()):
                clean_sentence = self._extract_relevant_part(skill, sentence_clean)
                return clean_sentence
        
        if self._exact_skill_match(skill, text.lower()):
            return self._extract_relevant_part(skill, text)
        
        return f"Experience with {skill}"

    def _extract_relevant_part(self, skill, text):
        text_lower = text.lower()
        skill_index = text_lower.find(skill)
        
        if skill_index == -1:
            if 'technical:' in text_lower and skill in ['python', 'docker', 'java']:
                tech_index = text_lower.find('technical:')
                tech_section = text[tech_index:tech_index + 200]
                return tech_section.strip() + "..."
            elif 'soft:' in text_lower and skill in ['communication', 'teamwork']:
                soft_index = text_lower.find('soft:')
                soft_section = text[soft_index:soft_index + 150]
                return soft_section.strip() + "..."
            return f"Experience with {skill}"
        
        start = max(0, skill_index - 30)
        end = min(len(text), skill_index + len(skill) + 30)
        
        extracted = text[start:end].strip()
        extracted = re.sub(r'\s+', ' ', extracted)
        
        if extracted.startswith('...'):
            extracted = extracted[3:]
        if extracted.endswith('...'):
            extracted = extracted[:-3]
        
        return extracted.strip()

    def _get_empty_analysis(self):
        return {
            'matched_skills': [],
            'missing_skills': [],
            'evidence': [],
            'cv_skill_count': 0,
            'jd_skill_count': 0,
            'match_percentage': 0
        }

skill_analyzer = SkillAnalyzer()