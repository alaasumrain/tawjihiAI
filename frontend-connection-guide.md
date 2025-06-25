# 🔗 Frontend-Backend Connection Guide

## 📡 **Your FastAPI Backend Endpoints**

Your backend is ready and provides these endpoints:

```
GET    /api/agents                  - Get available agents (math, arabic, english)
GET    /api/conversations/{user_id} - Get user's conversation history  
POST   /api/auth/login             - User authentication
POST   /api/ask                    - Ask a question to an agent
GET    /health                     - Health check
WebSocket /ws/{user_id}/{agent_id} - Real-time chat
```

## 🌐 **CORS Already Configured**

Your backend has CORS enabled for all origins (already set up):
```python
allow_origins=["*"]  # Frontend can connect from anywhere
```

## 📱 **Frontend Connection Examples**

### **1. React/Next.js Example**

```jsx
// api/tawjihi.js
const API_BASE = 'http://localhost:8000';

// Get available agents
export const getAgents = async () => {
  const response = await fetch(`${API_BASE}/api/agents`);
  return response.json();
};

// Ask a question (REST API)
export const askQuestion = async (subject, question, userId = null) => {
  const response = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject, question, user_id: userId })
  });
  return response.json();
};

// WebSocket for real-time chat
export class TawjihiWebSocket {
  constructor(userId, agentId, onMessage) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${agentId}`);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data); // Handle incoming messages
    };
  }
  
  sendQuestion(subject, question) {
    this.ws.send(JSON.stringify({
      type: 'question',
      subject,
      question
    }));
  }
}
```

**React Component:**
```jsx
import React, { useState, useEffect } from 'react';

function TawjihiChat() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [ws, setWs] = useState(null);

  // Load agents when component mounts
  useEffect(() => {
    fetch('http://localhost:8000/api/agents')
      .then(res => res.json())
      .then(setAgents);
  }, []);

  const connectWebSocket = () => {
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);
    const websocket = new WebSocket(`ws://localhost:8000/ws/${userId}/${selectedAgent}`);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };
    
    setWs(websocket);
  };

  const sendQuestion = () => {
    if (ws && question.trim()) {
      ws.send(JSON.stringify({
        type: 'question',
        subject: selectedAgent,
        question: question
      }));
      setQuestion('');
    }
  };

  return (
    <div>
      <h1>🎓 نظام التوجيهي الذكي</h1>
      
      <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
        <option value="">اختر المادة</option>
        {agents.map(agent => (
          <option key={agent.id} value={agent.id}>{agent.name}</option>
        ))}
      </select>
      
      <button onClick={connectWebSocket}>اتصل</button>
      
      <div>
        {messages.map((msg, i) => (
          <div key={i}>{msg.content}</div>
        ))}
      </div>
      
      <input 
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="اكتب سؤالك هنا..."
      />
      <button onClick={sendQuestion}>إرسال</button>
    </div>
  );
}
```

### **2. Vanilla JavaScript (Simple HTML)**

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>🎓 نظام التوجيهي الذكي</title>
</head>
<body>
    <h1>🎓 نظام التوجيهي الذكي</h1>
    
    <select id="agentSelect">
        <option value="">اختر المادة</option>
    </select>
    
    <button onclick="connectWebSocket()">اتصل</button>
    <div id="status">غير متصل</div>
    
    <div id="messages"></div>
    
    <input type="text" id="questionInput" placeholder="اكتب سؤالك هنا...">
    <button onclick="sendQuestion()">إرسال</button>

    <script>
        let ws = null;
        let userId = 'user_' + Math.random().toString(36).substr(2, 9);

        // Load agents on page load
        fetch('http://localhost:8000/api/agents')
            .then(res => res.json())
            .then(agents => {
                const select = document.getElementById('agentSelect');
                agents.forEach(agent => {
                    const option = document.createElement('option');
                    option.value = agent.id;
                    option.textContent = agent.name;
                    select.appendChild(option);
                });
            });

        function connectWebSocket() {
            const agentId = document.getElementById('agentSelect').value;
            if (!agentId) return alert('يرجى اختيار مادة أولاً');

            ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${agentId}`);
            
            ws.onopen = () => {
                document.getElementById('status').textContent = 'متصل ✅';
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML += `<div><strong>${data.type}:</strong> ${data.content}</div>`;
            };
        }

        function sendQuestion() {
            const question = document.getElementById('questionInput').value;
            const agentId = document.getElementById('agentSelect').value;
            
            if (ws && question) {
                ws.send(JSON.stringify({
                    type: 'question',
                    subject: agentId,
                    question: question
                }));
                document.getElementById('questionInput').value = '';
            }
        }
    </script>
</body>
</html>
```

### **3. Vue.js Example**

```javascript
// Vue 3 Composition API
import { ref, onMounted } from 'vue'

export default {
  setup() {
    const agents = ref([])
    const selectedAgent = ref('')
    const question = ref('')
    const messages = ref([])
    const ws = ref(null)

    onMounted(async () => {
      const response = await fetch('http://localhost:8000/api/agents')
      agents.value = await response.json()
    })

    const connectWebSocket = () => {
      const userId = 'user_' + Math.random().toString(36).substr(2, 9)
      ws.value = new WebSocket(`ws://localhost:8000/ws/${userId}/${selectedAgent.value}`)
      
      ws.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        messages.value.push(data)
      }
    }

    const sendQuestion = () => {
      if (ws.value && question.value) {
        ws.value.send(JSON.stringify({
          type: 'question',
          subject: selectedAgent.value,
          question: question.value
        }))
        question.value = ''
      }
    }

    return {
      agents,
      selectedAgent,
      question,
      messages,
      connectWebSocket,
      sendQuestion
    }
  }
}
```

## 📱 **Mobile App (Flutter)**

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class TawjihiAPI {
  static const String baseUrl = 'http://localhost:8000';
  
  // Get agents
  static Future<List<dynamic>> getAgents() async {
    final response = await http.get(Uri.parse('$baseUrl/api/agents'));
    return json.decode(response.body);
  }
  
  // Ask question via REST
  static Future<Map<String, dynamic>> askQuestion(String subject, String question) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/ask'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'subject': subject,
        'question': question,
      }),
    );
    return json.decode(response.body);
  }
}

// WebSocket for real-time chat
class TawjihiWebSocket {
  late WebSocketChannel channel;
  
  void connect(String userId, String agentId) {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$userId/$agentId')
    );
  }
  
  void sendQuestion(String subject, String question) {
    channel.sink.add(json.encode({
      'type': 'question',
      'subject': subject,
      'question': question,
    }));
  }
}
```

## 🔧 **Configuration for Production**

When you deploy, update the URLs:

```javascript
// config.js
const config = {
  development: {
    API_BASE: 'http://localhost:8000',
    WS_BASE: 'ws://localhost:8000'
  },
  production: {
    API_BASE: 'https://your-app.railway.app',  // Your deployed backend
    WS_BASE: 'wss://your-app.railway.app'     // WebSocket over HTTPS
  }
};

export const API_BASE = config[process.env.NODE_ENV].API_BASE;
export const WS_BASE = config[process.env.NODE_ENV].WS_BASE;
```

## 🚀 **Quick Start Steps**

1. **Start your FastAPI backend**: `uvicorn main:app --port 8000`
2. **Choose a frontend approach** from the examples above
3. **Copy the relevant code** for your framework
4. **Test the connection** by loading agents and sending messages
5. **Build your UI** around the API calls and WebSocket

Your backend is ready to work with ANY frontend! Which framework are you planning to use? 