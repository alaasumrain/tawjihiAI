# Frontend-Backend Connection Guide

## 📡 API Endpoints Available

Your FastAPI backend provides these endpoints:

- `GET /api/agents` - Get available agents
- `GET /api/conversations/{user_id}` - Get user's conversation history  
- `POST /api/auth/login` - User authentication
- `POST /api/ask` - Ask a question to an agent
- `GET /health` - Health check
- `WebSocket /ws/{user_id}/{agent_id}` - Real-time chat

## 🌐 CORS Configuration

Your backend already has CORS enabled for all origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📱 Frontend Examples

### **1. React/Next.js Frontend**

```jsx
// api/tawjihi.js
const API_BASE = 'http://localhost:8000';

export const tawjihiAPI = {
  // Get available agents
  async getAgents() {
    const response = await fetch(`${API_BASE}/api/agents`);
    return response.json();
  },

  // Ask a question
  async askQuestion(subject, question, userId = null) {
    const response = await fetch(`${API_BASE}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject,
        question,
        user_id: userId
      })
    });
    return response.json();
  },

  // Get conversation history
  async getConversations(userId) {
    const response = await fetch(`${API_BASE}/api/conversations/${userId}`);
    return response.json();
  },

  // Login
  async login(username, password) {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
    return response.json();
  }
};

// WebSocket for real-time chat
export class TawjihiWebSocket {
  constructor(userId, agentId, onMessage) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${agentId}`);
    
    this.ws.onopen = () => {
      console.log('Connected to TawjihiAI');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    this.ws.onclose = () => {
      console.log('Disconnected from TawjihiAI');
    };
  }
  
  sendQuestion(subject, question) {
    this.ws.send(JSON.stringify({
      type: 'question',
      subject,
      question
    }));
  }
  
  close() {
    this.ws.close();
  }
}
```

**React Component Example:**
```jsx
import React, { useState, useEffect } from 'react';
import { tawjihiAPI, TawjihiWebSocket } from './api/tawjihi';

function TawjihiChat() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Load agents on component mount
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const agentsData = await tawjihiAPI.getAgents();
      setAgents(agentsData);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const connectWebSocket = () => {
    if (!selectedAgent) return;
    
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);
    const websocket = new TawjihiWebSocket(userId, selectedAgent, (data) => {
      setMessages(prev => [...prev, {
        type: data.type,
        content: data.content,
        timestamp: new Date()
      }]);
    });
    
    setWs(websocket);
    setIsConnected(true);
  };

  const sendQuestion = () => {
    if (ws && question.trim()) {
      ws.sendQuestion(selectedAgent, question);
      setMessages(prev => [...prev, {
        type: 'user',
        content: question,
        timestamp: new Date()
      }]);
      setQuestion('');
    }
  };

  return (
    <div className="tawjihi-chat">
      <h1>🎓 نظام التوجيهي الذكي</h1>
      
      <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
        <option value="">اختر المادة</option>
        {agents.map(agent => (
          <option key={agent.id} value={agent.id}>{agent.name}</option>
        ))}
      </select>
      
      <button onClick={connectWebSocket} disabled={!selectedAgent || isConnected}>
        {isConnected ? 'متصل' : 'اتصل'}
      </button>
      
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <strong>{msg.type === 'user' ? 'أنت' : 'المعلم'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="اكتب سؤالك هنا..."
        />
        <button onClick={sendQuestion} disabled={!isConnected}>
          إرسال
        </button>
      </div>
    </div>
  );
}

export default TawjihiChat;
```

### **2. Vue.js Frontend**

```javascript
// composables/useTawjihi.js
import { ref } from 'vue'

const API_BASE = 'http://localhost:8000'

export function useTawjihi() {
  const agents = ref([])
  const messages = ref([])
  const isConnected = ref(false)
  const ws = ref(null)

  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/agents`)
      agents.value = await response.json()
    } catch (error) {
      console.error('Error loading agents:', error)
    }
  }

  const connectWebSocket = (userId, agentId) => {
    ws.value = new WebSocket(`ws://localhost:8000/ws/${userId}/${agentId}`)
    
    ws.value.onopen = () => {
      isConnected.value = true
    }
    
    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      messages.value.push({
        type: data.type,
        content: data.content,
        timestamp: new Date()
      })
    }
    
    ws.value.onclose = () => {
      isConnected.value = false
    }
  }

  const sendQuestion = (subject, question) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        type: 'question',
        subject,
        question
      }))
    }
  }

  const askQuestion = async (subject, question, userId = null) => {
    try {
      const response = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject,
          question,
          user_id: userId
        })
      })
      return await response.json()
    } catch (error) {
      console.error('Error asking question:', error)
      throw error
    }
  }

  return {
    agents,
    messages,
    isConnected,
    loadAgents,
    connectWebSocket,
    sendQuestion,
    askQuestion
  }
}
```

### **3. Vanilla JavaScript (HTML)**

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>🎓 نظام التوجيهي الذكي</title>
    <style>
        body { font-family: Arial; padding: 20px; direction: rtl; }
        .container { max-width: 800px; margin: 0 auto; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background-color: #e3f2fd; text-align: right; }
        .assistant { background-color: #f3e5f5; text-align: left; }
        .status { background-color: #fff3e0; text-align: center; }
        .error { background-color: #ffebee; text-align: center; }
        textarea, select, button { width: 100%; padding: 10px; margin: 5px 0; }
        button { background: #1976d2; color: white; border: none; cursor: pointer; }
        button:disabled { background: #ccc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 نظام التوجيهي الذكي</h1>
        
        <select id="agentSelect">
            <option value="">اختر المادة</option>
        </select>
        
        <button id="connectBtn" onclick="connectWebSocket()">اتصل</button>
        <div id="status">غير متصل</div>
        
        <div id="messages"></div>
        
        <textarea id="questionInput" placeholder="اكتب سؤالك هنا..." rows="3"></textarea>
        <button id="sendBtn" onclick="sendQuestion()" disabled>إرسال</button>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';
        let ws = null;
        let userId = 'user_' + Math.random().toString(36).substr(2, 9);

        // Load agents on page load
        document.addEventListener('DOMContentLoaded', loadAgents);

        async function loadAgents() {
            try {
                const response = await fetch(`${API_BASE}/api/agents`);
                const agents = await response.json();
                
                const select = document.getElementById('agentSelect');
                agents.forEach(agent => {
                    const option = document.createElement('option');
                    option.value = agent.id;
                    option.textContent = agent.name;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading agents:', error);
            }
        }

        function connectWebSocket() {
            const agentId = document.getElementById('agentSelect').value;
            if (!agentId) {
                alert('يرجى اختيار مادة أولاً');
                return;
            }

            ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${agentId}`);
            
            ws.onopen = () => {
                document.getElementById('status').textContent = 'متصل ✅';
                document.getElementById('connectBtn').disabled = true;
                document.getElementById('sendBtn').disabled = false;
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                addMessage(data.type, data.content);
            };
            
            ws.onclose = () => {
                document.getElementById('status').textContent = 'غير متصل ❌';
                document.getElementById('connectBtn').disabled = false;
                document.getElementById('sendBtn').disabled = true;
            };
        }

        function sendQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) return;

            const agentId = document.getElementById('agentSelect').value;
            
            // Add user message to chat
            addMessage('user', question);
            
            // Send to WebSocket
            ws.send(JSON.stringify({
                type: 'question',
                subject: agentId,
                question: question
            }));
            
            // Clear input
            document.getElementById('questionInput').value = '';
        }

        function addMessage(type, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            let sender = '';
            if (type === 'user') sender = 'أنت: ';
            else if (type === 'message') sender = 'المعلم: ';
            else if (type === 'status') sender = 'النظام: ';
            else if (type === 'error') sender = 'خطأ: ';
            
            messageDiv.innerHTML = `<strong>${sender}</strong>${content}`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Allow Enter key to send message
        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendQuestion();
            }
        });
    </script>
</body>
</html>
```

### **4. Flutter/Mobile App**

```dart
// lib/services/tawjihi_api.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class TawjihiAPI {
  static const String baseUrl = 'http://localhost:8000';
  
  static Future<List<Agent>> getAgents() async {
    final response = await http.get(Uri.parse('$baseUrl/api/agents'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Agent.fromJson(json)).toList();
    }
    throw Exception('Failed to load agents');
  }
  
  static Future<MessageResponse> askQuestion(String subject, String question, {String? userId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/ask'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'subject': subject,
        'question': question,
        'user_id': userId,
      }),
    );
    
    if (response.statusCode == 200) {
      return MessageResponse.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to ask question');
  }
}

class TawjihiWebSocket {
  late WebSocketChannel channel;
  
  void connect(String userId, String agentId, Function(Map<String, dynamic>) onMessage) {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$userId/$agentId')
    );
    
    channel.stream.listen((data) {
      final message = json.decode(data);
      onMessage(message);
    });
  }
  
  void sendQuestion(String subject, String question) {
    channel.sink.add(json.encode({
      'type': 'question',
      'subject': subject,
      'question': question,
    }));
  }
  
  void close() {
    channel.sink.close();
  }
}
```

## 🔧 **Environment Configuration**

### **Development**
```javascript
// config/api.js
const config = {
  development: {
    API_BASE: 'http://localhost:8000',
    WS_BASE: 'ws://localhost:8000'
  },
  production: {
    API_BASE: 'https://your-tawjihi-api.railway.app',
    WS_BASE: 'wss://your-tawjihi-api.railway.app'
  }
};

export const API_BASE = config[process.env.NODE_ENV || 'development'].API_BASE;
export const WS_BASE = config[process.env.NODE_ENV || 'development'].WS_BASE;
```

## 🚀 **Next Steps**

1. **Choose your frontend framework** (React, Vue, vanilla JS, etc.)
2. **Copy the appropriate code examples** above
3. **Install frontend dependencies** if needed
4. **Update API URLs** to match your deployment
5. **Test the connection** with your FastAPI backend

Your FastAPI backend is ready to work with any frontend! The examples above show you exactly how to connect. Which frontend framework are you planning to use? 