from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from groq import Groq
from dotenv import load_dotenv
import traceback
import json
import os

# Load environment variables
load_dotenv()

# ============================================
# DATABASE SETUP
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# PASSWORD HASHING
# ============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ============================================
# JWT SETTINGS
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================
# GROQ AI SETUP
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

def calculate_ats_score(resume_text: str, job_description: str, required_skills: str) -> dict:
    prompt = f"""
You are an ATS (Applicant Tracking System) expert. Analyze the resume against the job description and provide a detailed assessment.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS:
{required_skills}

Respond ONLY with a JSON object in this exact format:
{{
    "match_score": <number 0-100>,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "summary": "Brief 2-3 sentence summary of the candidate's fit"
}}
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    result_text = response.choices[0].message.content.strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()
    return json.loads(result_text)

# ============================================
# MODELS
# ============================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    description = Column(String(5000), nullable=False)
    required_skills = Column(String(1000), nullable=False)
    location = Column(String(200), nullable=False)
    salary = Column(String(100))
    posted_by = Column(Integer, nullable=False)

# ============================================
# SCHEMAS
# ============================================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: str
    location: str
    salary: str = ""

class ATSRequest(BaseModel):
    resume_text: str
    job_id: int

# ============================================
# CRUD OPERATIONS
# ============================================
def create_user(db: Session, user: UserCreate):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        db_user = User(
            name=user.name,
            email=user.email,
            password=hash_password(user.password),
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already exists")
    except Exception:
        db.rollback()
        raise

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# ============================================
# FASTAPI APP
# ============================================
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ROUTES
# ============================================
@app.get("/")
def home():
    return {"message": "AI ATS Backend Running"}


@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        print("SIGNUP REQUEST RECEIVED")
        new_user = create_user(db, user)
        return {
            "message": "User Registered Successfully",
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        print("LOGIN REQUEST RECEIVED")
        user = get_user_by_email(db, request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(request.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_access_token(data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name,
            "role": user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs")
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    try:
        print("CREATE JOB REQUEST RECEIVED")
        db_job = Job(
            title=job.title,
            company=job.company,
            description=job.description,
            required_skills=job.required_skills,
            location=job.location,
            salary=job.salary,
            posted_by=1
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return {
            "message": "Job Posted Successfully",
            "id": db_job.id,
            "title": db_job.title,
            "company": db_job.company
        }
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs")
def get_all_jobs(db: Session = Depends(get_db)):
    try:
        jobs = db.query(Job).all()
        return {
            "total": len(jobs),
            "jobs": [
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary": job.salary,
                    "required_skills": job.required_skills,
                    "description": job.description
                }
                for job in jobs
            ]
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
            "required_skills": job.required_skills,
            "description": job.description
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ats/score")
def ats_score(request: ATSRequest, db: Session = Depends(get_db)):
    try:
        print("ATS SCORE REQUEST RECEIVED")
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        result = calculate_ats_score(
            resume_text=request.resume_text,
            job_description=job.description,
            required_skills=job.required_skills
        )
        return {
            "job_title": job.title,
            "company": job.company,
            "match_score": result["match_score"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "strengths": result["strengths"],
            "improvements": result["improvements"],
            "summary": result["summary"]
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))