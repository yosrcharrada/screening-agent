# WP4 â€” Skills & Questions (with evidence XAI)

What you build:
- POST /skills â†’ returns skills present in CV & JD, similarities, gap_map (present/partial/missing), tips, and evidence quotes (XAI).
- POST /questions â†’ returns 5 JD-aware questions with rationale â€œTargets gap: <Skill>â€.

Run locally (PowerShell):
1) py -3 -m venv .venv
2) .venv\Scripts\Activate.ps1
3) pip install -r requirements.txt
4) python -m spacy download en_core_web_sm
5) CLI demo: python scripts\skills_demo.py data\sample_cv.txt data\sample_jd.txt
6) Start API: uvicorn backend.app.main:app --reload
7) Open http://127.0.0.1:8000/docs

Quick curl tests:
- /skills
curl -X POST http://127.0.0.1:8000/skills -H "Content-Type: application/json" -d "{\"cv_text\":\"Built Python ETL with SQL and Docker.\",\"jd_text\":\"We need Python and SQL; Docker is a plus.\"}"

- /questions
curl -X POST http://127.0.0.1:8000/questions -H "Content-Type: application/json" -d "{\"gap_map\":[{\"skill\":\"python\",\"status\":\"present\"},{\"skill\":\"sql\",\"status\":\"present\"},{\"skill\":\"docker\",\"status\":\"partial\"}]}"
