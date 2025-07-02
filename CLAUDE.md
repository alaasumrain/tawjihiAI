# TawjihiAI Project

A Jordanian Tawjihi tutoring system with AI agents for Math, Arabic, and English subjects.

## System Overview
- FastAPI backend with AI agents
- React frontend with TypeScript
- Subject-specific AI tutors with conversation memory
- OCR support for homework image processing
- Arabic/English bilingual support
- Supabase database integration

## Project Structure
```
tawjihiAI/
├── backend/
│   ├── agents/          # Subject-specific AI tutors
│   ├── services/        # OCR and file handling services
│   ├── main.py         # FastAPI application
│   ├── supabase_client.py # Database client
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/  # React components
    │   ├── pages/      # Route pages
    │   ├── services/   # API services
    │   └── config/     # Configuration
    └── package.json
```

## Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend  
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (.env)
- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `ALLOWED_ORIGINS`: CORS allowed origins
- `ENVIRONMENT`: development/production

### Frontend (.env)
- `VITE_API_BASE`: Backend API URL
- `VITE_WS_BASE`: WebSocket URL

## API Endpoints
- `GET /api/agents`: Get available tutors
- `POST /api/ask`: Ask question to AI tutor
- `POST /api/upload/homework`: Upload homework image
- `POST /api/solve/step-by-step`: Get step-by-step solution
- `WS /ws/{user_id}/{agent_id}`: Real-time chat

## Subjects
- **math**: Mathematics tutor with step-by-step solutions
- **arabic**: Arabic language tutor
- **english**: English language tutor

## Commands
- Backend: `python main.py`
- Frontend: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`