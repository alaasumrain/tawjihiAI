from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import uuid
from datetime import datetime

from main_cli import ask
from supabase_client import memory

app = FastAPI(
    title="TawjihiAI API",
    description="Intelligent Tutoring System for Jordanian Tawjihi Students",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AgentInfo(BaseModel):
    id: str
    name: str
    description: str

class QuestionRequest(BaseModel):
    subject: str
    question: str
    user_id: Optional[str] = None

class MessageResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TawjihiAI API", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 