import React, { useState, useEffect, useRef } from "react";

// Configure backend URL here (change to your deployed backend as needed)
const BACKEND_URL =
  (typeof process !== "undefined" && process.env && process.env.REACT_APP_BACKEND_URL) ||
  "http://localhost:8000";

// Generate and persist a session id
const generateSessionId = () => Date.now() + '-' + Math.floor(Math.random() * 10000);

export default function Widget() {
  // Add sessionId state: try to read from localStorage, or generate a new one
  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem("session_id");
    if (saved) return saved;
    const newId = generateSessionId();
    localStorage.setItem("session_id", newId);
    return newId;
  });

  const [messages, setMessages] = useState([{ id: 1, role: "bot", text: "Hello! Ask me about OHNY Weekend." }]);
  const [input, setInput] = useState("");
  const [style, setStyle] = useState("default");
  const [loading, setLoading] = useState(false);

  // messages container ref for auto-scroll
  const messagesRef = useRef(null);

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || loading) return;

    // Add user message
    const userMessage = { id: Date.now(), role: "user", text: trimmedInput };
    setMessages(prev => [...prev, userMessage]);
    setInput(""); // Clear input
    setLoading(true);

    try {
      const resp = await fetch(`${BACKEND_URL}/v1/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Include session_id in the POST body
        body: JSON.stringify({ message: trimmedInput, style: style, session_id: sessionId })
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(errorText || resp.statusText);
      }

      const data = await resp.json();
      console.log("Backend response:", data);
      // Add bot message with unique id
      const botMessage = { 
        id: Date.now() + 1, 
        role: "bot", 
        text: data.reply || data.message || "No reply received"
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      // Add error message
      const errorMessage = {
        id: Date.now(),
        role: "bot",
        text: `Error: ${error.message || "Could not reach backend"}`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const el = messagesRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  return (
    <div style={{position:'fixed', right:20, bottom:20, width:360, border:'1px solid #ddd', borderRadius:12, boxShadow:'0 6px 24px rgba(0,0,0,0.12)', background:'#fff'}}>
      <div style={{padding:10, borderTopLeftRadius:12, borderTopRightRadius:12, background:'#f3f4f6', fontWeight:700}}>OHNY Bot</div>
      <div ref={messagesRef} style={{padding:10, height:320, overflowY:'auto'}}>
        {messages.map((m) => (
          <div key={m.id} style={{marginBottom:8}}>
            <div style={{fontSize:12, color: m.role === 'bot' ? '#0b5fff' : '#111'}}>{m.text}</div>
          </div>
        ))}
      </div>
      <div style={{padding:10, borderTop:'1px solid #eee'}}>
        <textarea
          aria-label="Ask a question"
          placeholder="Ask a question..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            // Ctrl/Cmd+Enter to submit, Shift+Enter for newline
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
              e.preventDefault();
              sendMessage();
            }
          }}
          rows={3}
          style={{width: '100%', padding: 8, marginBottom: 8, boxSizing: 'border-box', resize: 'vertical'}}
        />
        <div style={{display:'flex', gap:8}}>
          <button onClick={sendMessage} disabled={loading || !input.trim()} style={{flex:1, padding:10, background:'#0b5fff', color:'#fff', borderRadius:8}}>
            {loading ? 'Thinking...' : 'Send'}
          </button>
        </div>
        <select aria-label="Response style" value={style} onChange={e => setStyle(e.target.value)}>
          <option value="default">Default</option>
          <option value="concierge">Concierge</option>
          <option value="tourguide">Tour Guide</option>
          <option value="friendly">Friendly & Helpful</option>
          <option value="family">Family-Friendly</option>
        </select>
      </div>
    </div>
  );
}
