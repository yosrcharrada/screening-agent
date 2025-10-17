from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, parse, skills, questions, transcribe, score, report
from app.models import create_tables
import uvicorn

# Create tables
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="Interview Platform API",
    description="AI-powered interview preparation and evaluation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(parse.router, prefix="/api/v1", tags=["parse"])
app.include_router(skills.router, prefix="/api/v1", tags=["skills"])
app.include_router(questions.router, prefix="/api/v1", tags=["questions"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcribe"])
app.include_router(score.router, prefix="/api/v1", tags=["score"])
app.include_router(report.router, prefix="/api/v1", tags=["report"])

@app.get("/")
async def root():
    return {"message": "Interview Platform API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)