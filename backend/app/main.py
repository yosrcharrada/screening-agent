from fastapi import FastAPI
from backend.app.routers.skills import router as skills_router
from backend.app.routers.questions import router as questions_router

app = FastAPI(title="screening-agent â€” WP4 Skills & Questions")

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(skills_router, tags=["skills"])
app.include_router(questions_router, tags=["questions"])
