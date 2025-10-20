from weasyprint import HTML
from io import BytesIO
from pathlib import Path
from datetime import datetime

def generate_pdf(score_data: dict, candidate_name: str, question: str) -> bytes:
    """
    Generate a PDF report from score data.
    Returns: PDF as bytes
    """
    
    # Extract data
    final_score = score_data['final_score']
    content_score = score_data['content']['score']
    delivery_score = score_data['delivery']['score']
    communication_score = score_data['communication']['score']
    evidence = score_data['evidence']
    next_actions = score_data['next_actions']
    
    # Determine performance level
    if final_score >= 85:
        level = "🌟 Excellent"
        color = "#2ecc71"
    elif final_score >= 70:
        level = "👍 Good"
        color = "#3498db"
    elif final_score >= 55:
        level = "📈 Average"
        color = "#f39c12"
    else:
        level = "💪 Needs Work"
        color = "#e74c3c"
    
    # Get current date
    report_date = datetime.now().strftime("%B %d, %Y")
    
    # Create HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 40px;
                background: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            header {{
                border-bottom: 3px solid #0066cc;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            h1 {{
                color: #0066cc;
                margin: 0 0 10px 0;
                font-size: 32px;
            }}
            .subtitle {{
                color: #666;
                font-size: 14px;
                margin: 5px 0;
            }}
            .score-box {{
                background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin: 30px 0;
            }}
            .score-box h2 {{
                margin: 0;
                font-size: 48px;
                font-weight: bold;
            }}
            .score-box p {{
                margin: 10px 0 0 0;
                font-size: 20px;
                opacity: 0.95;
            }}
            .subscores {{
                display: flex;
                justify-content: space-between;
                margin: 30px 0;
                gap: 20px;
            }}
            .subscore {{
                flex: 1;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .subscore h3 {{
                margin: 0 0 10px 0;
                color: #0066cc;
                font-size: 16px;
            }}
            .subscore .value {{
                font-size: 32px;
                font-weight: bold;
                color: #333;
            }}
            .subscore .weight {{
                font-size: 12px;
                color: #999;
                margin-top: 5px;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section h2 {{
                color: #0066cc;
                font-size: 20px;
                margin-bottom: 15px;
                border-left: 4px solid #0066cc;
                padding-left: 12px;
            }}
            .evidence-list, .action-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            .evidence-list li, .action-list li {{
                padding: 12px 15px;
                margin: 8px 0;
                background: #f8f9fa;
                border-radius: 6px;
                border-left: 3px solid #0066cc;
            }}
            .action-list li {{
                border-left-color: #2ecc71;
                background: #f0fdf4;
            }}
            .question-box {{
                background: #fff9e6;
                border: 1px solid #ffd700;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .question-box strong {{
                color: #856404;
            }}
            footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #999;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Interview Performance Report</h1>
                <p class="subtitle">Candidate: {candidate_name}</p>
                <p class="subtitle">Date: {report_date}</p>
            </header>
            
            <div class="question-box">
                <strong>Question Answered:</strong><br>
                {question}
            </div>
            
            <div class="score-box">
                <h2>{final_score}/100</h2>
                <p>{level}</p>
            </div>
            
            <div class="subscores">
                <div class="subscore">
                    <h3>Content</h3>
                    <div class="value">{content_score:.0f}</div>
                    <div class="weight">45% of total</div>
                </div>
                <div class="subscore">
                    <h3>Delivery</h3>
                    <div class="value">{delivery_score:.0f}</div>
                    <div class="weight">35% of total</div>
                </div>
                <div class="subscore">
                    <h3>Communication</h3>
                    <div class="value">{communication_score:.0f}</div>
                    <div class="weight">20% of total</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Why This Score?</h2>
                <ul class="evidence-list">
    """
    
    # Add evidence bullets
    for item in evidence:
        html_content += f"                    <li>{item}</li>\n"
    
    html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Next Steps to Improve</h2>
                <ul class="action-list">
    """
    
    # Add next action bullets
    for action in next_actions:
        html_content += f"                    <li>{action}</li>\n"
    
    html_content += """
                </ul>
            </div>
            
            <footer>
                <p>Generated by AI Interview Practice Tool</p>
                <p>Keep practicing to improve your interview skills!</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return pdf_bytes


def save_pdf_report(score_data: dict, candidate_name: str, question: str, session_id: str) -> str:
    """
    Generate and save PDF report to disk.
    Returns: filepath to the saved PDF
    """
    # Generate PDF
    pdf_bytes = generate_pdf(score_data, candidate_name, question)
    
    # Create reports directory if it doesn't exist
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Save with session ID as filename
    filename = f"report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = reports_dir / filename
    
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)
    
    return str(filepath)