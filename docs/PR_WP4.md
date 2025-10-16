\# WP4 — Skills \& Questions (with evidence XAI)



This PR adds:

\- POST /skills: returns skills\_cv, skills\_jd, similarities, gap\_map, tips, and evidence quotes (cv\_quote, jd\_quote).

\- POST /questions: returns 5 targeted questions with rationale “Targets gap: <Skill>”.



How to run locally (Windows)

1\) py -3 -m venv .venv

2\) .venv\\Scripts\\Activate.ps1

3\) pip install -r requirements.txt

4\) python -m spacy download en\_core\_web\_sm

5\) python -m uvicorn backend.app.main:app --reload

6\) Open http://127.0.0.1:8000/docs



Quick tests in /docs

\- POST /skills with:

{

&nbsp; "cv\_text": "Built Python ETL with SQL and Docker.",

&nbsp; "jd\_text": "We need Python and SQL; Docker is a plus."

}

\- POST /questions with:

{

&nbsp; "gap\_map": \[

&nbsp;   {"skill":"python","status":"present"},

&nbsp;   {"skill":"sql","status":"present"},

&nbsp;   {"skill":"docker","status":"partial"}

&nbsp; ]

}



Notes

\- Thresholds in config/thresholds.yaml control present/partial/missing.

\- Set `use\_embeddings: false` for a lighter install (still works).

\- File reads use utf-8-sig to be Windows/BOM safe.

