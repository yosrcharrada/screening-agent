from fastapi import APIRouter
from app.models.schemas import QuestionsRequest, QuestionsResponse, QuestionItem

router = APIRouter()

@router.post("/questions", response_model=QuestionsResponse)
async def generate_questions(request: QuestionsRequest):
    # Stub implementation with mock questions
    questions = [
        QuestionItem(
            id="1",
            text="Can you describe a challenging project you worked on and how you overcame the obstacles?",
            difficulty="medium",
            rationale="Tests problem-solving and experience with real-world challenges"
        ),
        QuestionItem(
            id="2", 
            text="How do you handle conflicts within your team?",
            difficulty="easy",
            rationale="Assesses communication and teamwork skills"
        ),
        QuestionItem(
            id="3",
            text="Explain the concept of microservices and when you would use them.",
            difficulty="hard", 
            rationale="Tests technical knowledge and architectural understanding"
        )
    ]
    
    return QuestionsResponse(questions=questions)