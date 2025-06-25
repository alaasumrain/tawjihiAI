# TawjihiAI Project

A Jordanian Tawjihi tutoring system with AI agents for Math, Arabic, and English subjects.

## System Overview
- Interactive CLI tutoring system
- Subject-specific AI agents with memory
- PDF curriculum processing
- Arabic/English bilingual support

## Project Structure
```
tawjihiAI/
├── agents/          # Subject-specific AI tutors
├── data/           # Curriculum PDFs and documents
├── memories/       # Agent memory storage
├── main.py         # Main interactive interface
└── requirements.txt
```

## Usage
```bash
python main.py
```

## Available Commands
- Run system: `python main.py`
- Install deps: `pip install -r requirements.txt`
- Test agents: `python -m agents.math` etc.

## Subjects
- **math**: Mathematics tutor
- **arabic**: Arabic language tutor  
- **english**: English language tutor