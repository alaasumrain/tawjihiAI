from flask import Flask, request, jsonify, render_template_string, session
from main_cli import ask
from supabase_client import memory
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Simple HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎓 نظام التوجيهي الذكي</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            direction: rtl;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        select, textarea, button {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
        }
        select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .response {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            color: #667eea;
            font-weight: bold;
        }
        .subjects {
            text-align: center;
            margin-bottom: 30px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 نظام التوجيهي الذكي</h1>
        <div class="subjects">
            📚 المواد المتاحة: الرياضيات، اللغة العربية، اللغة الإنجليزية
        </div>
        
        <form id="tutorForm">
            <div class="form-group">
                <label for="subject">📖 المادة (Subject):</label>
                <select id="subject" name="subject" required>
                    <option value="">اختر المادة</option>
                    <option value="math">الرياضيات (Math)</option>
                    <option value="arabic">اللغة العربية (Arabic)</option>
                    <option value="english">اللغة الإنجليزية (English)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="question">❓ سؤالك (Your Question):</label>
                <textarea id="question" name="question" rows="4" placeholder="اكتب سؤالك هنا..." required></textarea>
            </div>
            
            <button type="submit">🤖 احصل على الإجابة</button>
        </form>
        
        <div id="response" class="response" style="display: none;"></div>
    </div>

    <script>
        document.getElementById('tutorForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const subject = document.getElementById('subject').value;
            const question = document.getElementById('question').value;
            const responseDiv = document.getElementById('response');
            
            responseDiv.style.display = 'block';
            responseDiv.innerHTML = '<div class="loading">🤖 جاري التفكير...</div>';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ subject, question })
                });
                
                const data = await response.json();
                responseDiv.innerHTML = `<strong>🤖 الإجابة:</strong><br><br>${data.response}`;
            } catch (error) {
                responseDiv.innerHTML = '<strong>❌ خطأ:</strong> حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Serve the main tutoring interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask', methods=['POST'])
def ask_tutor():
    """API endpoint for asking questions with memory"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        question = data.get('question')
        
        if not subject or not question:
            return jsonify({'error': 'يرجى إدخال المادة والسؤال'}), 400
        
        # Get or create user session
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        teacher_id = subject.lower()  # math, arabic, english
        
        # Get or create conversation for this user and teacher
        conversation_id = memory.get_or_create_conversation(
            user_id=user_id,
            teacher_id=teacher_id,
            title=f"Chat with {subject.title()} Teacher"
        )
        
        # Save user question to memory
        if conversation_id:
            memory.save_message(conversation_id, question, 'user')
        
        # Get conversation history for context
        history = []
        if conversation_id:
            history = memory.get_conversation_history(conversation_id, limit=10)
        
        # Build context from history
        context = ""
        if history:
            context = "\n\nPrevious conversation:\n"
            for msg in history[-5:]:  # Last 5 messages for context
                role = "Student" if msg['role'] == 'user' else "Teacher"
                context += f"{role}: {msg['content']}\n"
            context += "\nCurrent question:\n"
        
        # Get AI response with context
        full_question = context + question if context else question
        response = ask(subject, full_question)
        
        # Save AI response to memory
        if conversation_id:
            memory.save_message(conversation_id, response, 'assistant')
        
        return jsonify({
            'response': response,
            'conversation_id': conversation_id,
            'has_history': len(history) > 0
        })
    
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'TawjihiAI is running!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 