#!/usr/bin/env python3
"""
App Server - Backend API for PySR Job Management
Handles user authentication, job management, and database operations
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base

from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import uuid
import hashlib
import jwt
import os
import aiofiles
import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
#DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:amit7488@localhost:5432/pysrmcp")
DATABASE_URL=os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:amit1199@localhost:5432/postgres")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
PYSR_MCP_URL = os.getenv("PYSR_MCP_URL", "http://localhost:8001/pysr")
UPLOAD_DIR = "uploads"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    jobs = relationship("Job", back_populates="user")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    config = Column(Text)  # JSON string
    status = Column(String, default="created")  # created, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    file_path = Column(String)
    result_path = Column(String)
    
    user = relationship("User", back_populates="jobs")
    job_runs = relationship("JobRun", back_populates="job")

class JobRun(Base):
    __tablename__ = "job_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    run_number = Column(Integer, default=1)
    pysr_job_id = Column(String)  # Job ID from PySR MCP server
    status = Column(String, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    result_data = Column(Text)  # JSON string
    error_message = Column(Text)
    
    job = relationship("Job", back_populates="job_runs")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool

class JobCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    file_path: Optional[str]
    result_path: Optional[str]

class JobRunResponse(BaseModel):
    id: str
    job_id: str
    run_number: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]

# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_jwt_token(user_id: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    user_id = verify_jwt_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# FastAPI App Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("App Server starting up...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create upload directory
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/data", exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/results", exist_ok=True)
    
    yield
    
    logger.info("App Server shutting down...")

app = FastAPI(
    title="PySR App Server",
    description="Backend API for PySR Job Management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Endpoints
@app.post("/auth/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    token = create_jwt_token(user.id)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
    }

@app.post("/auth/login")
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    token = create_jwt_token(user.id)
    
    return {
        "message": "Login successful",
        "token": token,
        "user": UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )

# Job Management Endpoints
@app.get("/jobs")
async def list_jobs_by_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all jobs for current user"""
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    
    job_responses = []
    for job in jobs:
        job_responses.append(JobResponse(
            id=str(job.id),
            name=job.name,
            description=job.description,
            config=json.loads(job.config) if job.config else {},
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            file_path=job.file_path,
            result_path=job.result_path
        ))
    
    return {"jobs": job_responses}

@app.post("/jobs")
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new job"""
    job = Job(
        user_id=current_user.id,
        name=job_data.name,
        description=job_data.description,
        config=json.dumps(job_data.config)
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {
        "message": "Job created successfully",
        "job": JobResponse(
            id=str(job.id),
            name=job.name,
            description=job.description,
            config=job_data.config,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            file_path=job.file_path,
            result_path=job.result_path
        )
    }

@app.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific job"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=str(job.id),
        name=job.name,
        description=job.description,
        config=json.loads(job.config) if job.config else {},
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        file_path=job.file_path,
        result_path=job.result_path
    )

@app.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update job"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_update.name is not None:
        job.name = job_update.name
    if job_update.description is not None:
        job.description = job_update.description
    if job_update.config is not None:
        job.config = json.dumps(job_update.config)
    
    db.commit()
    
    return {"message": "Job updated successfully"}

@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete job"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated files
    if job.file_path and os.path.exists(job.file_path):
        os.remove(job.file_path)
    if job.result_path and os.path.exists(job.result_path):
        os.remove(job.result_path)
    
    # Delete job runs
    db.query(JobRun).filter(JobRun.job_id == job.id).delete()
    
    # Delete job
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}

# File Upload Endpoint
@app.post("/jobs/{job_id}/upload")
async def upload_file(
    job_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload data file for job"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create file path
    file_extension = Path(file.filename).suffix
    file_path = f"{UPLOAD_DIR}/data/{job_id}{file_extension}"
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Update job
    job.file_path = file_path
    db.commit()
    
    return {
        "message": "File uploaded successfully",
        "file_path": file_path,
        "file_size": len(content)
    }

# Job Execution Endpoints
@app.post("/jobs/{job_id}/submit")
async def submit_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit job for execution"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.file_path or not os.path.exists(job.file_path):
        raise HTTPException(status_code=400, detail="No data file uploaded")
    
    try:
        # Create job run
        job_run = JobRun(job_id=job.id, run_number=len(job.job_runs) + 1)
        db.add(job_run)
        db.commit()
        db.refresh(job_run)
        
        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Process job asynchronously
        asyncio.create_task(process_job_async(str(job.id), str(job_run.id), db))
        
        return {
            "message": "Job submitted successfully",
            "job_run_id": str(job_run.id),
            "status": "submitted"
        }
        
    except Exception as e:
        logger.error(f"Error submitting job {job_id}: {str(e)}")
        job.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")

async def process_job_async(job_id: str, job_run_id: str, db: Session):
    """Process job asynchronously"""
    try:
        # Get job and job run
        job = db.query(Job).filter(Job.id == job_id).first()
        job_run = db.query(JobRun).filter(JobRun.id == job_run_id).first()
        
        if not job or not job_run:
            logger.error(f"Job or job run not found: {job_id}, {job_run_id}")
            return
        
        # Load data file
        import pandas as pd
        data = pd.read_csv(job.file_path)
        
        # Parse job configuration
        config = json.loads(job.config)
        
        # Prepare data for PySR
        X = data.iloc[:, :-1].values.tolist()  # All columns except last
        y = data.iloc[:, -1].values.tolist()   # Last column
        
        # Create model via PySR MCP server
        async with aiohttp.ClientSession() as session:
            # Step 1: Create model
            create_request = {
                "action": "create_model",
                "data": config.get("model_config", {})
            }
            
            async with session.post(PYSR_MCP_URL, json=create_request) as response:
                create_result = await response.json()
                
                if create_result["status"] != "success":
                    raise Exception(f"Model creation failed: {create_result['message']}")
                
                model_id = create_result["result"]["model_id"]
                job_run.pysr_job_id = model_id
                
            # Step 2: Fit model
            fit_request = {
                "action": "fit_model",
                "data": {
                    "model_id": model_id,
                    "training_data": {
                        "X": X,
                        "y": y,
                        "feature_names": config.get("feature_names"),
                        "variable_names": config.get("variable_names")
                    }
                }
            }
            
            async with session.post(PYSR_MCP_URL, json=fit_request) as response:
                fit_result = await response.json()
                
                if fit_result["status"] != "success":
                    raise Exception(f"Model fitting failed: {fit_result['message']}")
            
            # Step 3: Monitor training
            while True:
                monitor_request = {
                    "action": "monitor_training",
                    "data": {"model_id": model_id}
                }
                
                async with session.post(PYSR_MCP_URL, json=monitor_request) as response:
                    monitor_result = await response.json()
                    
                    if monitor_result["status"] == "success":
                        training_status = monitor_result["result"]["status"]
                        
                        if training_status == "completed":
                            break
                        elif training_status == "failed":
                            raise Exception("Training failed")
                        
                    await asyncio.sleep(5)  # Check every 5 seconds
            
            # Step 4: Get equations
            equations_request = {
                "action": "get_equations",
                "data": {"model_id": model_id}
            }
            
            async with session.post(PYSR_MCP_URL, json=equations_request) as response:
                equations_result = await response.json()
                
                if equations_result["status"] != "success":
                    raise Exception(f"Failed to get equations: {equations_result['message']}")
                
                # Save results
                result_data = {
                    "equations": equations_result["result"]["equations"],
                    "best_equation_index": equations_result["result"]["best_equation_index"],
                    "total_equations": equations_result["result"]["total_equations"],
                    "model_id": model_id
                }
                
                # Save result file
                result_path = f"{UPLOAD_DIR}/results/{job_id}.json"
                with open(result_path, 'w') as f:
                    json.dump(result_data, f, indent=2, default=str)
                
                # Update database
                job_run.status = "completed"
                job_run.completed_at = datetime.utcnow()
                job_run.result_data = json.dumps(result_data)
                
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.result_path = result_path
                
                db.commit()
                
                logger.info(f"Job {job_id} completed successfully")
                
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        
        # Update failure status
        if 'job_run' in locals():
            job_run.status = "failed"
            job_run.error_message = str(e)
            job_run.completed_at = datetime.utcnow()
            
        if 'job' in locals():
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            
        db.commit()

# Job Run Endpoints
@app.get("/jobs/{job_id}/runs")
async def get_job_runs(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all runs for a job"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    runs = db.query(JobRun).filter(JobRun.job_id == job.id).all()
    
    run_responses = []
    for run in runs:
        result_data = json.loads(run.result_data) if run.result_data else None
        run_responses.append(JobRunResponse(
            id=str(run.id),
            job_id=str(run.job_id),
            run_number=run.run_number,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            result_data=result_data,
            error_message=run.error_message
        ))
    
    return {"job_runs": run_responses}

@app.get("/jobs/{job_id}/runs/{run_id}")
async def get_job_run(
    job_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific job run"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    run = db.query(JobRun).filter(
        JobRun.id == run_id,
        JobRun.job_id == job.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Job run not found")
    
    result_data = json.loads(run.result_data) if run.result_data else None
    
    return JobRunResponse(
        id=str(run.id),
        job_id=str(run.job_id),
        run_number=run.run_number,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        result_data=result_data,
        error_message=run.error_message
    )

# Status Endpoint
@app.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job status"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get latest job run
    latest_run = db.query(JobRun).filter(JobRun.job_id == job.id).order_by(JobRun.run_number.desc()).first()
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "latest_run": {
            "id": str(latest_run.id),
            "status": latest_run.status,
            "run_number": latest_run.run_number
        } if latest_run else None
    }

# Health Check and Info Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Test PySR MCP server connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PYSR_MCP_URL.replace('/pysr', '/health')}", timeout=5) as response:
                if response.status == 200:
                    pysr_status = "healthy"
                else:
                    pysr_status = f"unhealthy: HTTP {response.status}"
    except Exception as e:
        pysr_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and "healthy" in pysr_status else "unhealthy",
        "database": db_status,
        "pysr_mcp_server": pysr_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def server_info():
    """Server information"""
    return {
        "name": "PySR App Server",
        "version": "1.0.0",
        "description": "Backend API for PySR Job Management",
        "endpoints": {
            "auth": ["/auth/register", "/auth/login", "/auth/me"],
            "jobs": ["/jobs", "/jobs/{id}", "/jobs/{id}/upload", "/jobs/{id}/submit"],
            "runs": ["/jobs/{id}/runs", "/jobs/{id}/runs/{run_id}"],
            "status": ["/jobs/{id}/status"],
            "system": ["/health", "/info"]
        },
        "pysr_mcp_url": PYSR_MCP_URL,
        "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "configured"
    }

if __name__ == "__main__":
    print("🚀 Starting App Server...")
    print("🏢 Backend API for PySR Job Management")
    print("=" * 50)
    print(f"🔗 Base URL: http://localhost:8000")
    print(f"🔐 Auth: http://localhost:8000/auth/*")
    print(f"📋 Jobs: http://localhost:8000/jobs/*")
    print(f"💡 Health: http://localhost:8000/health")
    print(f"ℹ️  Info: http://localhost:8000/info")
    print("=" * 50)
    
    uvicorn.run(
        "app_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )