import React, { useState } from "react";

export default function Widget() {
  const [messages, setMessages] = useState([{role: "bot", text: "Hello! Ask me about OHNY Weekend."}]);
  const [input, setInput] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [loading, setLoading] = useState(false);

  const presets = [
    { label: "Saturday Morning", start: "2025-10-04T09:00", end: "2025-10-04T12:00" },
    { label: "Saturday Afternoon", start: "2025-10-04T12:00", end: "2025-10-04T17:00" },
    { label: "Sunday Morning", start: "2025-10-05T09:00", end: "2025-10-05T12:00" },
    { label: "Sunday Afternoon", start: "2025-10-05T12:00", end: "2025-10-05T17:00" }
  ];

  const applyPreset = (preset) => {
    setStartTime(preset.start);
    setEndTime(preset.end);
  };

  const sendMessage = async () => {
    if (!input) return;
    const userMsg = {role: "user", text: input};
    setMessages(m => [...m, userMsg]);
    setInput("");
    setLoading(true);

    const query = new URLSearchParams();
    if (startTime) query.append("start_time", startTime);
    if (endTime) query.append("end_time", endTime);

    try {
      const resp = await fetch(`http://localhost:8000/v1/message?${query.toString()}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: "demo", message: input})
      });
      const data = await resp.json();
      setMessages(m => [...m, {role: "bot", text: data.reply}]);
    } catch (e) {
      setMessages(m => [...m, {role: "bot", text: "Error: could not reach backend (is it running?)."}]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{position:'fixed', right:20, bottom:20, width:360, border:'1px solid #ddd', borderRadius:12, boxShadow:'0 6px 24px rgba(0,0,0,0.12)', background:'#fff'}}>
      <div style={{padding:10, borderTopLeftRadius:12, borderTopRightRadius:12, background:'#f3f4f6', fontWeight:700}}>OHNY Bot</div>
      <div style={{padding:10, height:320, overflowY:'auto'}}>
        {messages.map((m,i)=> (
          <div key={i} style={{marginBottom:8}}>
            <div style={{fontSize:12, color:m.role==='bot'?'#0b5fff':'#111'}}>{m.text}</div>
          </div>
        ))}
      </div>
      <div style={{padding:10, borderTop:'1px solid #eee'}}>
        <input type="text" placeholder="Ask a question..." value={input} onChange={e=>setInput(e.target.value)} style={{width:'100%', padding:8, marginBottom:8, boxSizing:'border-box'}} />
        <div style={{display:'flex', gap:8, marginBottom:8}}>
          <input type="datetime-local" value={startTime} onChange={e=>setStartTime(e.target.value)} style={{flex:1, padding:8}} />
          <input type="datetime-local" value={endTime} onChange={e=>setEndTime(e.target.value)} style={{flex:1, padding:8}} />
        </div>
        <div style={{display:'flex', gap:6, marginBottom:8}}>
          {presets.map((p,i)=> (<button key={i} onClick={()=>applyPreset(p)} style={{padding:'6px 8px', background:'#eee', borderRadius:6}}>{p.label}</button>))}
        </div>
        <div style={{display:'flex', gap:8}}>
          <button onClick={sendMessage} disabled={loading} style={{flex:1, padding:10, background:'#0b5fff', color:'#fff', borderRadius:8}}>{loading? 'Thinking...':'Send'}</button>
        </div>
      </div>
    </div>
  );
}
