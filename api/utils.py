import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

def extract_text_from_pdf(pdf_file):
    try:
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                cleaned_text = clean_extracted_text(page_text)
                text += cleaned_text + "\n"
        
        print(f"PDF extracted text length: {len(text)}")
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {str(e)}")
        return f"Error extracting PDF: {str(e)}"

def clean_extracted_text(text):
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    text = re.sub(r'\b\d+\b\s*$', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    replacements = {
        '´': "'", '`': "'", '¶': ' ', '⌢': '-', '♂': '', 
        'ˆ': '^', '¸': ',', '¨': '"', '´e': 'é', '´E': 'É'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = re.sub(r' +', ' ', text)
    return text.strip()

def fetch_content_from_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|body'))
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return f"Error fetching URL content: {str(e)}"

def validate_pdf_file(file):
    try:
        file_name = file.name.lower()
        return file_name.endswith('.pdf')
    except Exception:
        return False

def calculate_interview_score(result):
    """
    Calculate a simple interview score based on transcription metrics.
    """
    metrics = result.get("metrics", {})
    word_count = metrics.get("word_count", 0)
    duration_s = metrics.get("duration_s", 1)  # avoid division by zero
    filler_pct = metrics.get("filler_pct", 0)

    # Words per minute
    wpm = word_count / (duration_s / 60)

    # Simple scoring logic: penalize for fillers
    score = wpm * (1 - filler_pct/100)
    score = max(0, min(100, int(score)))  # cap between 0 and 100

    return {"score": score}
