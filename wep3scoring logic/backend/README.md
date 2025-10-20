\# WP3: Scoring \& XAI Explanations \& PDF Report



\## Overview



This is the scoring engine for the AI Interview Practice Tool. It takes interview transcripts and delivery metrics, then produces an explainable score with detailed feedback.



\## What This Does



\- \*\*Scores interview answers\*\* on a 0-100 scale

\- \*\*Breaks down scores\*\* into Content (45%), Delivery (35%), and Communication (20%)

\- \*\*Explains the score\*\* with evidence from the transcript

\- \*\*Provides actionable feedback\*\* on what to improve

\- \*\*Generates PDF reports\*\* for candidates



\## Key Features



\### 🎯 9 Measurement Features



\*\*Content (What they say):\*\*

1\. STAR Completeness - Situation, Task, Action, Result structure

2\. JD Keyword Overlap - Job description keyword mentions

3\. Specificity Metrics - Quantifiable results (%, $, time)

4\. Relevance - Answer addresses the question



\*\*Delivery (How they say it):\*\*

5\. Speaking Pace - Words per minute (ideal: 120-160 WPM)

6\. Filler Rate - Um, uh, like, you know (ideal: <2%)

7\. Answer Length - Duration in seconds (ideal: 60-120s)

8\. Tone Expressiveness - Variation vs monotone



\*\*Communication (How well they explain):\*\*

9\. Logical Flow - Transition words and structure

10\. Clarity - Sentence length and complexity



\### 🔍 Explainable AI (XAI)



\- Every feature contributes a specific amount to the final score

\- All contributions sum exactly to the final score

\- Evidence bullets quote specific metrics

\- Next actions target the weakest areas



\## Installation



```bash

\# Navigate to backend folder

cd backend



\# Install dependencies

pip install -r requirements.txt

```



\## Running Tests



```bash

\# Run all tests

pytest



\# Run with verbose output

pytest -v



\# Run specific test file

pytest tests/test\_features.py



\# Run tests with coverage (if pytest-cov installed)

pytest --cov=app --cov-report=html

```



\## Usage



\### As a Python Function



```python

from app.services.score\_calculator import calculate\_score



result = calculate\_score(

&nbsp;   transcript="I led a project that improved performance by 30%...",

&nbsp;   wpm=145.0,

&nbsp;   filler\_rate=0.03,

&nbsp;   answer\_length\_s=85.0,

&nbsp;   jd\_keywords=\["python", "leadership", "agile"],

&nbsp;   question="Tell me about a leadership experience"

)



print(f"Final Score: {result\['final\_score']}/100")

print(f"Content: {result\['content']\['score']}")

print(f"Delivery: {result\['delivery']\['score']}")

print(f"Communication: {result\['communication']\['score']}")

```



\### As an API Endpoint



```bash

\# Start the server (WP1 should provide this)

uvicorn app.main:app --reload



\# Make a request

curl -X POST "http://localhost:8000/api/score" \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "transcript": "I worked on a project...",

&nbsp;   "wpm": 140.0,

&nbsp;   "filler\_rate": 0.05,

&nbsp;   "answer\_length\_s": 75.0,

&nbsp;   "jd\_keywords": \["python", "aws"],

&nbsp;   "question": "Describe your experience",

&nbsp;   "candidate\_name": "John Doe"

&nbsp; }'

```



\### Generate PDF Report



```python

from app.services.pdf\_generator import save\_pdf\_report



pdf\_path = save\_pdf\_report(

&nbsp;   score\_data=result,

&nbsp;   candidate\_name="Jane Smith",

&nbsp;   question="Tell me about a technical challenge",

&nbsp;   session\_id="abc-123"

)



print(f"Report saved to: {pdf\_path}")

```



\## Configuration



Edit `config/weights.yaml` to adjust scoring weights and thresholds:



```yaml

final\_score\_weights:

&nbsp; content\_weight: 0.45    # Change these to adjust importance

&nbsp; delivery\_weight: 0.35

&nbsp; communication\_weight: 0.20



delivery\_features:

&nbsp; pace\_wpm:

&nbsp;   ideal\_range: \[120, 160]  # Adjust ideal WPM range

&nbsp;   too\_slow: 80

&nbsp;   too\_fast: 200

```



\## File Structure



```

backend/

├── app/

│   ├── routers/

│   │   └── scoring.py              # /score endpoint

│   ├── services/

│   │   ├── feature\_extractors.py   # 9 measurement functions

│   │   ├── score\_calculator.py     # Main scoring logic

│   │   └── pdf\_generator.py        # PDF report generation

│   └── models/

│       └── score\_models.py         # Request/Response schemas

├── config/

│   └── weights.yaml                # Scoring configuration

├── tests/

│   ├── test\_features.py            # Test individual features

│   ├── test\_calculator.py          # Test scoring logic

│   └── sample\_data.py              # Sample test data

└── reports/                        # Generated PDFs

```



\## Testing Strategy



\### Unit Tests (`test\_features.py`)

\- Test each of the 9 features individually

\- Test edge cases (empty input, extreme values)

\- Verify feature scores are 0-1



\### Integration Tests (`test\_calculator.py`)

\- Test complete scoring workflow

\- \*\*Critical XAI test:\*\* Verify contributions sum to final score

\- Test deterministic behavior (same input = same output)

\- Verify evidence and next actions are generated



\### Test Data (`sample\_data.py`)

\- Excellent answer (expected score: 80+)

\- Average answer (expected score: 55-75)

\- Poor answer (expected score: <50)

\- Edge cases (no STAR, too short, high fillers)



\## API Contract



\### POST /api/score



\*\*Request:\*\*

```json

{

&nbsp; "transcript": "string",

&nbsp; "wpm": 140.0,

&nbsp; "filler\_rate": 0.05,

&nbsp; "answer\_length\_s": 75.0,

&nbsp; "jd\_keywords": \["python", "aws"],

&nbsp; "question": "string",

&nbsp; "candidate\_name": "string"

}

```



\*\*Response:\*\*

```json

{

&nbsp; "final\_score": 78.5,

&nbsp; "content": {

&nbsp;   "score": 82.0,

&nbsp;   "weight": 0.45,

&nbsp;   "features": {

&nbsp;     "star": {

&nbsp;       "name": "star",

&nbsp;       "value": 1.0,

&nbsp;       "contribution": 15.75,

&nbsp;       "evidence": "Found 4/4 STAR elements"

&nbsp;     }

&nbsp;   }

&nbsp; },

&nbsp; "delivery": { ... },

&nbsp; "communication": { ... },

&nbsp; "evidence": \[

&nbsp;   "✓ Strong STAR structure — all elements present",

&nbsp;   "✓ Speaking pace is good — 140 WPM is ideal"

&nbsp; ],

&nbsp; "next\_actions": \[

&nbsp;   "💪 Next step: Practice pausing for 2 seconds instead of saying 'um' or 'uh'"

&nbsp; ],

&nbsp; "report\_url": "/reports/abc-123"

}

```



\## Key Principles



1\. \*\*Deterministic\*\* - Same input always produces same output

2\. \*\*Explainable\*\* - Every score component has evidence

3\. \*\*Actionable\*\* - Feedback tells users exactly what to improve

4\. \*\*Accurate\*\* - Contributions mathematically sum to final score

5\. \*\*Configurable\*\* - All weights and thresholds in YAML



\## Troubleshooting



\### WeasyPrint Installation Issues



If PDF generation fails:



```bash

\# On Ubuntu/Debian

sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0



\# On macOS

brew install pango



\# On Windows

\# Use WSL or download GTK+ runtime

```



\### Tests Failing



```bash

\# Make sure you're in the backend directory

cd backend



\# Check Python path

export PYTHONPATH="${PYTHONPATH}:$(pwd)"



\# Run with more verbose output

pytest -vv --tb=long

```



\## Performance



\- Feature extraction: ~5ms per answer

\- Score calculation: ~2ms

\- PDF generation: ~200ms

\- Total endpoint latency: <250ms



\## Next Steps



1\. ✅ Run all tests: `pytest -v`

2\. ✅ Test the /score endpoint manually

3\. ✅ Generate a sample PDF

4\. ✅ Integrate with WP1 backend server

5\. ✅ Connect to WP2 frontend for visualization



\## Contributing



When modifying scoring logic:



1\. Update `config/weights.yaml` first

2\. Modify feature extractors if needed

3\. Add tests for new behavior

4\. Run full test suite: `pytest`

5\. Verify XAI contributions still sum correctly



\## Team: WP3 Owner



\*\*Your responsibility:\*\*

\- Scoring engine (this package)

\- Feature extraction

\- XAI explanations

\- PDF report generation



\*\*Not your responsibility:\*\*

\- Audio recording (WP5)

\- Skill extraction (WP4)

\- Frontend UI (WP2)

\- Server setup (WP1)



\## Contact



For questions about WP3 scoring engine, contact the WP3 team member.

