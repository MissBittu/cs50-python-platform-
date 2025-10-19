"
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="CS50 Python Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users_db = {}
progress_db = {}

class User(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Progress(BaseModel):
    user_id: str
    lesson_id: str
    completed: bool
    timestamp: datetime

class Lesson(BaseModel):
    id: str
    title: str
    description: str
    video_url: str
    duration: str
    order: int

class Challenge(BaseModel):
    id: str
    lesson_id: str
    title: str
    description: str
    starter_code: str
    test_cases: List[dict]

LESSONS = [
    {
        "id": "1",
        "title": "Introduction to Python",
        "description": "Learn the basics of Python programming",
        "video_url": "https://www.youtube.com/embed/nLRL_NcnK-4",
        "duration": "2:01:42",
        "order": 1
    },
    {
        "id": "2",
        "title": "Conditionals and Loops",
        "description": "Master control flow in Python",
        "video_url": "https://www.youtube.com/embed/FHZpJGMKOxI",
        "duration": "1:57:01",
        "order": 2
    },
    {
        "id": "3",
        "title": "Functions and Variables",
        "description": "Write reusable code with functions",
        "video_url": "https://www.youtube.com/embed/s3IvdkCq2_c",
        "duration": "2:17:28",
        "order": 3
    },
    {
        "id": "4",
        "title": "Lists and Dictionaries",
        "description": "Work with Python data structures",
        "video_url": "https://www.youtube.com/embed/mIBCLloUj5s",
        "duration": "2:06:56",
        "order": 4
    }
]

CHALLENGES = [
    {
        "id": "c1",
        "lesson_id": "1",
        "title": "Hello World",
        "description": "Write a program that prints 'Hello, World!'",
        "starter_code": "# Write your code here\n",
        "test_cases": [{"input": "", "expected": "Hello, World!"}]
    },
    {
        "id": "c2",
        "lesson_id": "1",
        "title": "Variables and Input",
        "description": "Create a variable and print a personalized greeting",
        "starter_code": "# Get user's name and print greeting\nname = input('What is your name? ')\n",
        "test_cases": [{"input": "Alice", "expected": "Hello, Alice!"}]
    },
    {
        "id": "c3",
        "lesson_id": "2",
        "title": "Even or Odd",
        "description": "Write a function that determines if a number is even or odd",
        "starter_code": "def check_even_odd(number):\n    # Write your code here\n    pass\n",
        "test_cases": [{"input": "4", "expected": "even"}, {"input": "7", "expected": "odd"}]
    }
]

@app.get("/")
def read_root():
    return {"message": "CS50 Python Platform API", "status": "running"}

@app.get("/api/lessons", response_model=List[Lesson])
def get_lessons():
    return LESSONS

@app.get("/api/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: str):
    lesson = next((l for l in LESSONS if l["id"] == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@app.get("/api/challenges", response_model=List[Challenge])
def get_challenges(lesson_id: Optional[str] = None):
    if lesson_id:
        return [c for c in CHALLENGES if c["lesson_id"] == lesson_id]
    return CHALLENGES

@app.get("/api/challenges/{challenge_id}", response_model=Challenge)
def get_challenge(challenge_id: str):
    challenge = next((c for c in CHALLENGES if c["id"] == challenge_id), None)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@app.post("/api/register")
def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "password": user.password,
        "created_at": datetime.now().isoformat()
    }
    return {"message": "User registered successfully", "username": user.username}

@app.post("/api/login")
def login(credentials: UserLogin):
    user = users_db.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Login successful",
        "user": {"username": user["username"], "email": user["email"]}
    }

@app.post("/api/progress")
def save_progress(progress: Progress):
    key = f"{progress.user_id}_{progress.lesson_id}"
    progress_db[key] = {
        "user_id": progress.user_id,
        "lesson_id": progress.lesson_id,
        "completed": progress.completed,
        "timestamp": progress.timestamp.isoformat()
    }
    return {"message": "Progress saved", "progress": progress_db[key]}

@app.get("/api/progress/{user_id}")
def get_progress(user_id: str):
    user_progress = {k: v for k, v in progress_db.items() if v["user_id"] == user_id}
    return {"progress": user_progress}

@app.get("/api/stats/{user_id}")
def get_stats(user_id: str):
    user_progress = [v for k, v in progress_db.items() if v["user_id"] == user_id]
    completed_lessons = sum(1 for p in user_progress if p["completed"])
    return {
        "total_lessons": len(LESSONS),
        "completed_lessons": completed_lessons,
        "completion_rate": round((completed_lessons / len(LESSONS)) * 100, 1) if len(LESSONS) > 0 else 0,
        "total_challenges": len(CHALLENGES),
        "completed_challenges": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"@ | Out-File -FilePath "main.py" -Encoding UTF8
