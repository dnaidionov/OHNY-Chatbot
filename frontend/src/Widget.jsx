import React, { useState, useEffect, useRef } from "react";

// Configure backend URL here (change to your deployed backend as needed)
const BACKEND_URL =
  (typeof process !== "undefined" && process.env && process.env.REACT_APP_BACKEND_URL) ||
  "http://localhost:8000";

export default function Widget() {
  const [messages, setMessages] = useState([{ id: 1, role: "bot", text: "Hello! Ask me about OHNY Weekend." }]);
  const [input, setInput] = useState("");
  const [style, setStyle] = useState("default");
  const [loading, setLoading] = useState(false);

  // messages container ref for auto-scroll
  const messagesRef = useRef(null);

  const sendMessage = async () => {
    if (!input) return;
    // Always assign a unique id to user messages
    const userMsg = { id: Date.now() + Math.random(), role: "user", text: input };
    setMessages(m => [...m, userMsg]);
    setInput("");
    setLoading(true);

    // Don't send whitespace-only messages
    if (!input.trim()) {
      setLoading(false);
      return;
    }

    try {
      const resp = await fetch(BACKEND_URL + "/v1/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: "demo", message: input, style: style })
      });

      if (!resp.ok) {
        const text = await resp.text().catch(() => null);
        setMessages(m => [...m, { id: Date.now() + Math.random(), role: "bot", text: `Server error: ${resp.status} ${text || resp.statusText}` }]);
        return;
      }

      const data = await resp.json();
      setMessages(m => [...m, { id: Date.now() + Math.random(), role: "bot", text: data.reply }]);
    } catch (e) {
      setMessages(m => [...m, { id: Date.now() + Math.random(), role: "bot", text: "Error: could not reach backend (is it running?)." }]);
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
          <button onClick={sendMessage} disabled={loading || !input.trim()} style={{flex:1, padding:10, background:'#0b5fff', color:'#fff', borderRadius:8}}>{loading? 'Thinking...':'Send'}</button>
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
