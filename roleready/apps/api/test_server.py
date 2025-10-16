from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Role Ready API - Test Server",
    description="Test backend API for Role Ready application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:3002",  # Add port 3002
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",  # Add port 3002
        "http://192.168.1.160:3002"  # Add network IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Role Ready API Test Server is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/")
async def api_root():
    return {"message": "Role Ready API v1.0.0"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working correctly!", "status": "success"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Test upload endpoint"""
    try:
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "content_type": file.content_type,
            "size": "test_size"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/parse")
async def parse_resume():
    """Test parse endpoint - returns user-specific sample data"""
    import random
    
    # Different sample resumes for variety
    sample_resumes = [
        {
            "personal_info": "Alice Johnson, Senior Software Engineer",
            "experience": ["TechCorp - Senior Software Engineer (2021-Present)", "StartupXYZ - Software Developer (2019-2021)"],
            "education": "Master's in Computer Science",
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"]
        },
        {
            "personal_info": "Bob Smith, Product Manager", 
            "experience": ["ProductCo - Senior Product Manager (2020-Present)", "GrowthStartup - Product Manager (2018-2020)"],
            "education": "MBA in Business Administration",
            "skills": ["Product Strategy", "Data Analysis", "User Research", "Agile", "JIRA"]
        },
        {
            "personal_info": "Carol Davis, UX/UI Designer",
            "experience": ["DesignStudio - Senior UX Designer (2021-Present)", "CreativeAgency - UI Designer (2019-2021)"],
            "education": "Bachelor's in Graphic Design",
            "skills": ["Figma", "Sketch", "Adobe Creative Suite", "Prototyping", "User Testing"]
        }
    ]
    
    selected_resume = random.choice(sample_resumes)
    
    return {
        "message": "Resume parsed successfully",
        "sections": selected_resume
    }

@app.post("/api/align")
async def align_resume():
    """Test alignment endpoint"""
    return {
        "message": "Resume aligned successfully",
        "alignment_score": 85,
        "suggestions": [
            "Add more specific technical skills",
            "Include quantifiable achievements",
            "Optimize for ATS compatibility"
        ]
    }

@app.post("/api/rewrite")
async def rewrite_resume():
    """Test rewrite endpoint"""
    return {
        "message": "Resume rewritten successfully",
        "improved_sections": {
            "summary": "Experienced software engineer with 5+ years in full-stack development...",
            "experience": ["Led development of 3 major features increasing user engagement by 40%"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
