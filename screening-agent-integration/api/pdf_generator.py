# api/pdf_generator.py
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
import os
from datetime import datetime

class PDFGenerator:
    """Generate PDF reports from score data"""
    
    @staticmethod
    def generate_score_report(score_data, candidate_name, session_id):
        """Generate a PDF report from score data"""
        
        context = {
            'candidate_name': candidate_name,
            'session_id': session_id,
            'generation_date': datetime.now().strftime("%B %d, %Y"),
            'final_score': score_data['final_score'],
            'content_score': score_data['subscores']['content']['score'],
            'delivery_score': score_data['subscores']['delivery']['score'],
            'communication_score': score_data['subscores']['communication']['score'],
            'explanations': score_data['explanations'],
            'next_actions': score_data['next_actions'],
        }
        
        # Render HTML template
        html_string = render_to_string('score_report.html', context)
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        
        return pdf_file
    
    @staticmethod
    def create_pdf_response(score_data, candidate_name, session_id, filename=None):
        """Create HTTP response with PDF"""
        if not filename:
            filename = f"interview_score_report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        pdf_content = PDFGenerator.generate_score_report(score_data, candidate_name, session_id)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response