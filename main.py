from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, List, Dict
import json
import uuid
from datetime import datetime
import logging
import traceback
import os

from main_cli import ask
from supabase_client import memory
from services.ocr_service import ocr_service
from services.file_handler import file_handler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tawjihiai.log') if os.getenv('ENVIRONMENT') != 'production' else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TawjihiAI API",
    description="Intelligent Tutoring System for Jordanian Tawjihi Students",
    version="2.0.0"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,https://tawjihiai.netlify.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Pydantic models
class AgentInfo(BaseModel):
    id: str
    name: str
    description: str

class QuestionRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100, description="Subject must be between 1 and 100 characters")
    question: str = Field(..., min_length=1, max_length=5000, description="Question must be between 1 and 5000 characters")
    user_id: Optional[str] = Field(None, max_length=100, description="User ID must be less than 100 characters")

class MessageResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

class FileUploadResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    filename: Optional[str] = None
    extracted_text: Optional[str] = None
    confidence: Optional[float] = None
    content_type: Optional[str] = None
    error: Optional[str] = None

class OCRRequest(BaseModel):
    text: str
    language: str
    confidence: float
    content_type: str

class HomeworkSolution(BaseModel):
    problem: str
    solution: str
    steps: List[str]
    subject: str
    difficulty: str

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Username must be between 1 and 50 characters")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="Password must be between 6 and 100 characters")

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_json(self, data: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Invalid request data",
            "errors": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error on {request.url}: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "request_id": str(uuid.uuid4())
        }
    )

@app.get("/", response_class=HTMLResponse)
async def get_home():
    return """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><title>TawjihiAI FastAPI</title></head>
<body>
<h1>🎓 نظام التوجيهي الذكي - FastAPI</h1>
<p>✅ FastAPI server is running successfully!</p>
<p>📡 WebSocket endpoint: ws://localhost:8000/ws/user_id/agent_id</p>
<p>🔗 API endpoints available at /docs</p>
</body>
</html>"""

@app.get("/api/agents", response_model=List[AgentInfo])
async def get_agents():
    return [
        AgentInfo(id="math", name="MathTutor", description="متخصص في الرياضيات"),
        AgentInfo(id="arabic", name="ArabicTutor", description="متخصص في اللغة العربية"),
        AgentInfo(id="english", name="EnglishTutor", description="متخصص في اللغة الإنجليزية")
    ]

@app.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str):
    try:
        result = memory.client.table('conversations').select('*').eq('user_id', user_id).execute()
        return {"conversations": result.data if result.data else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    return {"message": "تم تسجيل الدخول بنجاح", "session_id": str(uuid.uuid4()), "user_id": request.username}

@app.post("/api/ask", response_model=MessageResponse)
async def ask_question(request: QuestionRequest):
    logger.info(f"Question received: subject={request.subject}, user_id={request.user_id}")
    try:
        if not request.subject or not request.question:
            raise HTTPException(status_code=400, detail="يرجى إدخال المادة والسؤال")
        
        user_id = request.user_id or str(uuid.uuid4())
        conversation_id = memory.get_or_create_conversation(user_id=user_id, teacher_id=request.subject.lower())
        
        if conversation_id:
            memory.save_message(conversation_id, request.question, 'user')
        
        response = ask(request.subject, request.question)
        
        if conversation_id:
            memory.save_message(conversation_id, response, 'assistant')
        
        return MessageResponse(response=response, conversation_id=conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{user_id}/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, agent_id: str):
    client_id = f"{user_id}_{agent_id}"
    await manager.connect(websocket, client_id)
    
    await manager.send_json({"type": "status", "content": f"متصل مع {agent_id}"}, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "question":
                question = message_data.get("question", "")
                subject = message_data.get("subject", agent_id)
                
                await manager.send_json({"type": "status", "content": "جاري التفكير..."}, client_id)
                
                try:
                    response = ask(subject, question)
                    await manager.send_json({"type": "message", "content": response}, client_id)
                except Exception as e:
                    await manager.send_json({"type": "error", "content": str(e)}, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.post("/api/upload/homework", response_model=FileUploadResponse)
async def upload_homework(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    subject: Optional[str] = Form(None)
):
    """
    Upload homework image or document for AI assistance
    """
    try:
        logger.info(f"Homework upload request from user {user_id}: {file.filename}")
        
        # Save file
        save_result = file_handler.save_file(file, user_id)
        if not save_result['success']:
            raise HTTPException(status_code=400, detail=save_result['errors'])
        
        # Extract text if it's an image
        extracted_text = None
        confidence = 0
        
        if file.content_type and file.content_type.startswith('image/'):
            # Read file content for OCR
            file_content = file.file.read()
            file.file.seek(0)  # Reset for potential future use
            
            # Extract text using OCR
            ocr_result = ocr_service.extract_homework_content(file_content)
            extracted_text = ocr_result.get('primary', {}).get('text', '')
            confidence = ocr_result.get('primary', {}).get('confidence', 0)
            
            logger.info(f"OCR extraction completed with confidence: {confidence}%")
        
        return FileUploadResponse(
            success=True,
            file_id=save_result['filename'],
            filename=file.filename,
            extracted_text=extracted_text,
            confidence=confidence,
            content_type=file.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Homework upload error: {e}")
        return FileUploadResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/ocr/extract")
async def extract_text_from_image(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Extract text from uploaded image using OCR
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text using OCR
        if language:
            ocr_result = ocr_service.extract_text(file_content, language)
        else:
            ocr_result = ocr_service.extract_text_bilingual(file_content)
            
        return ocr_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/api/solve/step-by-step")
async def solve_homework_step_by_step(
    problem_text: str = Form(..., min_length=1, max_length=5000),
    subject: str = Form(..., min_length=1, max_length=100),
    user_id: Optional[str] = Form(None, max_length=100)
):
    """
    Get step-by-step solution for homework problem
    """
    try:
        # Enhanced prompt for step-by-step solutions
        step_by_step_prompt = f"""
        Please solve this {subject} problem step-by-step:
        
        Problem: {problem_text}
        
        Provide:
        1. Clear step-by-step solution
        2. Explanation of each step
        3. Final answer
        4. Key concepts used
        
        Format your response in a clear, educational manner suitable for Tawjihi students.
        """
        
        # Get AI response
        response = ask(subject, step_by_step_prompt)
        
        return {
            "problem": problem_text,
            "solution": response,
            "subject": subject,
            "solved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Step-by-step solution error: {e}")
        raise HTTPException(status_code=500, detail=f"Solution generation failed: {str(e)}")

@app.get("/api/supported-formats")
async def get_supported_formats():
    """
    Get list of supported file formats for upload
    """
    return file_handler.get_supported_types()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TawjihiAI API", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 