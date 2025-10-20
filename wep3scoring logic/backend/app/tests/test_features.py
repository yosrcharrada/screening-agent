import pytest
from app.services.feature_extractors import (
    measure_star_completeness,
    measure_jd_keyword_overlap,
    measure_specificity_metric,
    measure_relevance,
    measure_pace,
    measure_filler_rate,
    measure_answer_length,
    measure_tone_expressiveness,
    measure_logical_flow,
    measure_clarity
)


class TestContentFeatures:
    """Test all content-related features"""
    
    def test_star_completeness_full(self):
        """Test when all STAR elements are present"""
        transcript = """
        In the situation where our team faced a critical deadline, 
        my task was to coordinate the development. 
        I implemented a new workflow system. 
        As a result, we improved delivery time by 30%.
        """
        result = measure_star_completeness(transcript)
        
        assert result['S'] == True
        assert result['T'] == True
        assert result['A'] == True
        assert result['R'] == True
        assert result['score'] == 1.0
    
    def test_star_completeness_partial(self):
        """Test when only some STAR elements present"""
        transcript = "I implemented a solution and it worked well."
        result = measure_star_completeness(transcript)
        
        assert result['score'] < 1.0
        assert result['A'] == True  # Has action
    
    def test_jd_keyword_overlap_high(self):
        """Test high keyword overlap"""
        transcript = "I used Python, React, and AWS to build the system"
        keywords = ["python", "react", "aws"]
        result = measure_jd_keyword_overlap(transcript, keywords)
        
        assert result['matched'] == 3
        assert result['total'] == 3
        assert result['score'] == 1.0
    
    def test_jd_keyword_overlap_partial(self):
        """Test partial keyword overlap"""
        transcript = "I used Python and JavaScript"
        keywords = ["python", "react", "aws", "docker"]
        result = measure_jd_keyword_overlap(transcript, keywords)
        
        assert result['matched'] == 1  # Only Python
        assert result['score'] == 0.25  # 1/4
    
    def test_specificity_metric_present(self):
        """Test when metrics are mentioned"""
        transcript = "We improved performance by 30% and saved $50K"
        result = measure_specificity_metric(transcript)
        
        assert result['has_metric'] == True
        assert result['score'] == 1.0
    
    def test_specificity_metric_absent(self):
        """Test when no metrics mentioned"""
        transcript = "We made things better and faster"
        result = measure_specificity_metric(transcript)
        
        assert result['has_metric'] == False
        assert result['score'] == 0.0
    
    def test_relevance_high(self):
        """Test high relevance to question"""
        question = "Tell me about a time you led a team project"
        transcript = "I led a team on a major project last year"
        result = measure_relevance(transcript, question)
        
        assert result['score'] > 0.4


class TestDeliveryFeatures:
    """Test all delivery-related features"""
    
    def test_pace_ideal(self):
        """Test ideal speaking pace"""
        result = measure_pace(140.0)
        
        assert result['rating'] == 'ideal'
        assert result['score'] == 1.0
    
    def test_pace_too_fast(self):
        """Test speaking too fast"""
        result = measure_pace(220.0)
        
        assert result['rating'] == 'too fast'
        assert result['score'] == 0.5
    
    def test_pace_too_slow(self):
        """Test speaking too slow"""
        result = measure_pace(70.0)
        
        assert result['rating'] == 'too slow'
        assert result['score'] == 0.5
    
    def test_filler_rate_excellent(self):
        """Test low filler word usage"""
        result = measure_filler_rate(0.01)  # 1%
        
        assert result['rating'] == 'excellent'
        assert result['score'] >= 0.9
    
    def test_filler_rate_high(self):
        """Test high filler word usage"""
        result = measure_filler_rate(0.15)  # 15%
        
        assert result['rating'] == 'high'
        assert result['score'] < 0.5
    
    def test_answer_length_ideal(self):
        """Test ideal answer length"""
        result = measure_answer_length(90.0)  # 90 seconds
        
        assert result['rating'] == 'ideal'
        assert result['score'] == 1.0
    
    def test_answer_length_too_short(self):
        """Test answer too short"""
        result = measure_answer_length(20.0)
        
        assert result['rating'] == 'too short'
        assert result['score'] == 0.5


class TestCommunicationFeatures:
    """Test all communication-related features"""
    
    def test_logical_flow_good(self):
        """Test good logical flow with transitions"""
        transcript = """
        First I analyzed the problem. Then I designed a solution.
        As a result, we achieved our goals. Finally, we documented everything.
        """
        result = measure_logical_flow(transcript)
        
        assert result['transitions_found'] >= 3
        assert result['score'] == 1.0
    
    def test_logical_flow_poor(self):
        """Test poor logical flow"""
        transcript = "I worked on the project. It was done."
        result = measure_logical_flow(transcript)
        
        assert result['transitions_found'] < 2
        assert result['score'] < 0.7
    
    def test_clarity_clear(self):
        """Test clear, concise sentences"""
        transcript = "I led the team. We finished on time. Everyone was happy."
        result = measure_clarity(transcript)
        
        assert result['clarity'] in ['very clear', 'clear']
        assert result['score'] >= 0.8
    
    def test_clarity_complex(self):
        """Test complex, long sentences"""
        transcript = """
        I was responsible for leading the team which consisted of five developers 
        and two designers who worked together on a project that lasted six months 
        and involved multiple stakeholders across different departments.
        """
        result = measure_clarity(transcript)
        
        assert result['avg_sentence_length'] > 20
        assert result['score'] < 0.8


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_transcript(self):
        """Test with empty transcript"""
        result = measure_star_completeness("")
        assert result['score'] == 0.0
    
    def test_empty_keywords(self):
        """Test with empty keyword list"""
        result = measure_jd_keyword_overlap("Some text", [])
        assert result['score'] >= 0.0
    
    def test_zero_wpm(self):
        """Test with zero WPM (edge case)"""
        result = measure_pace(0.0)
        assert result['score'] == 0.5  # Should handle gracefully
    
    def test_negative_filler_rate(self):
        """Test with negative filler rate (shouldn't happen but handle it)"""
        result = measure_filler_rate(-0.1)
        assert result['score'] >= 0.0  # Should clamp to valid range