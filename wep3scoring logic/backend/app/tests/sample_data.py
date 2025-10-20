# Sample interview answers for testing

SAMPLE_EXCELLENT_ANSWER = """
In the situation where our e-commerce platform was experiencing severe performance issues during peak hours,
affecting over 50,000 users daily, my task was to identify the bottlenecks and implement a solution within 
two weeks before the holiday shopping season.

I implemented a comprehensive caching strategy using Redis, optimized our database queries by adding proper 
indexes, and introduced a CDN for static assets. I also refactored the most critical API endpoints using 
asynchronous processing with Python and AWS Lambda.

As a result, we reduced page load times by 60%, from 4.2 seconds to 1.7 seconds, improved our server response 
time by 45%, and successfully handled Black Friday traffic which was 3x our normal volume without any downtime.
The solution saved the company an estimated $200,000 in potential lost revenue and improved our customer 
satisfaction scores by 23%.
"""

SAMPLE_AVERAGE_ANSWER = """
I worked on a project where we had to build a new feature for our application. The task was to create 
a user dashboard that would show analytics. I used React for the frontend and Node.js for the backend.

I coded the components and connected them to the API. Then I tested everything to make sure it worked.
The project took about three weeks to complete. In the end, we launched the feature and users started 
using it. Some people liked it and we got positive feedback.
"""

SAMPLE_POOR_ANSWER = """
Um, so like, I was working on this thing at my last job, you know. And basically, we had to do some stuff 
with the system. Like, it was kind of complicated but, um, I figured it out eventually. 

We, uh, made some changes and it got better. I mean, I think people were happy with it. It was, like, 
a good experience overall.
"""

SAMPLE_NO_STAR_ANSWER = """
I have experience with Python, JavaScript, and React. I've built several web applications and worked with 
databases. I'm good at problem-solving and I enjoy learning new technologies. I usually work well in teams 
and I can also work independently when needed.
"""

SAMPLE_TOO_SHORT_ANSWER = """
I led a project last year. We finished on time and it went well.
"""

SAMPLE_QUESTIONS = [
    "Tell me about a time you faced a technical challenge and how you overcame it.",
    "Describe a situation where you had to work with a difficult team member.",
    "Give me an example of when you had to meet a tight deadline.",
    "Tell me about a project you're most proud of.",
    "Describe a time when you had to learn a new technology quickly."
]

SAMPLE_JD_KEYWORDS = [
    "python", "react", "aws", "docker", "kubernetes",
    "agile", "scrum", "leadership", "teamwork",
    "problem-solving", "communication", "microservices"
]

# Test cases with expected score ranges
TEST_CASES = [
    {
        "name": "excellent_answer",
        "transcript": SAMPLE_EXCELLENT_ANSWER,
        "wpm": 145.0,
        "filler_rate": 0.01,
        "answer_length_s": 95.0,
        "jd_keywords": ["python", "aws", "performance", "optimization"],
        "question": SAMPLE_QUESTIONS[0],
        "expected_score_min": 80.0
    },
    {
        "name": "average_answer",
        "transcript": SAMPLE_AVERAGE_ANSWER,
        "wpm": 130.0,
        "filler_rate": 0.03,
        "answer_length_s": 60.0,
        "jd_keywords": ["react", "node", "api"],
        "question": SAMPLE_QUESTIONS[3],
        "expected_score_min": 55.0,
        "expected_score_max": 75.0
    },
    {
        "name": "poor_answer",
        "transcript": SAMPLE_POOR_ANSWER,
        "wpm": 180.0,
        "filler_rate": 0.18,
        "answer_length_s": 25.0,
        "jd_keywords": ["system", "design", "implementation"],
        "question": SAMPLE_QUESTIONS[0],
        "expected_score_max": 50.0
    },
    {
        "name": "no_star_structure",
        "transcript": SAMPLE_NO_STAR_ANSWER,
        "wpm": 140.0,
        "filler_rate": 0.02,
        "answer_length_s": 45.0,
        "jd_keywords": ["python", "javascript", "react"],
        "question": SAMPLE_QUESTIONS[0],
        "expected_score_max": 65.0
    },
    {
        "name": "too_short",
        "transcript": SAMPLE_TOO_SHORT_ANSWER,
        "wpm": 140.0,
        "filler_rate": 0.01,
        "answer_length_s": 12.0,
        "jd_keywords": ["leadership", "project"],
        "question": SAMPLE_QUESTIONS[3],
        "expected_score_max": 55.0
    }
]