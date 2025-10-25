import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from passlib.context import CryptContext
import jwt

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models
from models import Base, User, Lesson, Challenge, UserProgress, UserSubmission

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="CS50 Python Platform API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Pydantic Models ====================

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class LessonResponse(BaseModel):
    id: int
    title: str
    description: str
    video_url: str
    duration: str
    order: int
    
    class Config:
        from_attributes = True

class ChallengeResponse(BaseModel):
    id: int
    lesson_id: int
    title: str
    description: str
    starter_code: str
    test_cases: list
    difficulty: str
    points: int
    
    class Config:
        from_attributes = True

class ProgressResponse(BaseModel):
    user_id: int
    challenge_id: int
    completed: bool
    best_score: float
    attempts: int
    
    class Config:
        from_attributes = True

class SubmissionRequest(BaseModel):
    challenge_id: int
    code: str

class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    challenge_id: int
    passed_tests: int
    total_tests: int
    score: float
    submitted_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Database Dependency ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    payload = {"sub": str(user_id)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== Routes ====================

@app.get("/")
def read_root():
    return {"message": "CS50 Python Platform API", "status": "running", "database": "connected"}

# ==================== Authentication Routes ====================

@app.post("/api/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create new user
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "username": new_user.username,
        "user_id": new_user.id
    }

@app.post("/api/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token(user.id)
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

# ==================== Lessons Routes ====================

@app.get("/api/lessons", response_model=List[LessonResponse])
def get_lessons(db: Session = Depends(get_db)):
    lessons = db.query(Lesson).order_by(Lesson.order).all()
    return lessons

@app.get("/api/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

# ==================== Challenges Routes ====================

@app.get("/api/challenges", response_model=List[ChallengeResponse])
def get_challenges(lesson_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Challenge)
    if lesson_id:
        query = query.filter(Challenge.lesson_id == lesson_id)
    return query.all()

@app.get("/api/challenges/{challenge_id}", response_model=ChallengeResponse)
def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

# ==================== Progress Routes ====================

@app.get("/api/user/progress")
def get_user_progress(token: str = None, db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    user = get_current_user(token, db)
    progress = db.query(UserProgress).filter(UserProgress.user_id == user.id).all()
    
    return {
        "user_id": user.id,
        "progress": [
            {
                "challenge_id": p.challenge_id,
                "completed": p.completed,
                "best_score": p.best_score,
                "attempts": p.attempts
            }
            for p in progress
        ]
    }

@app.get("/api/user/stats")
def get_user_stats(token: str = None, db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    user = get_current_user(token, db)
    
    total_lessons = db.query(Lesson).count()
    completed_challenges = db.query(UserProgress).filter(
        (UserProgress.user_id == user.id) & (UserProgress.completed == True)
    ).count()
    total_challenges = db.query(Challenge).count()
    average_score = db.query(UserSubmission).filter(
        UserSubmission.user_id == user.id
    ).value(db.func.avg(UserSubmission.score)) or 0
    
    return {
        "total_lessons": total_lessons,
        "total_challenges": total_challenges,
        "completed_challenges": completed_challenges,
        "completion_rate": round((completed_challenges / total_challenges * 100), 1) if total_challenges > 0 else 0,
        "average_score": round(average_score, 1)
    }

# ==================== Code Execution Routes ====================

from executor_simple import execute_code_safely, run_test_cases

@app.post("/api/code/execute")
def execute_code(code: str = None):
    """Execute code and return output"""
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    
    result = execute_code_safely(code)
    return result

# ==================== Submission Routes ====================

@app.post("/api/challenges/{challenge_id}/submit", response_model=SubmissionResponse)
def submit_challenge(
    challenge_id: int,
    submission: SubmissionRequest,
    token: str = None,
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    user = get_current_user(token, db)
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Execute code and run test cases
    test_result = run_test_cases(submission.code, challenge.test_cases or [])
    
    new_submission = UserSubmission(
        user_id=user.id,
        challenge_id=challenge_id,
        code=submission.code,
        passed_tests=test_result["passed"],
        total_tests=test_result["total"],
        score=test_result["score"],
        output=""
    )
    db.add(new_submission)
    
    # Update user progress
    progress = db.query(UserProgress).filter(
        (UserProgress.user_id == user.id) & (UserProgress.challenge_id == challenge_id)
    ).first()
    
    if not progress:
        progress = UserProgress(user_id=user.id, challenge_id=challenge_id)
        db.add(progress)
    
    progress.attempts += 1
    progress.last_submitted = datetime.utcnow()
    progress.best_score = max(progress.best_score, test_result["score"])
    
    # Mark as completed if all tests pass
    if test_result["passed"] == test_result["total"]:
        progress.completed = True
    
    db.commit()
    db.refresh(new_submission)
    
    return new_submission

# ==================== Run ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    