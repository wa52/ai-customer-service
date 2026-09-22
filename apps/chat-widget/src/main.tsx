import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type Message = { role: 'customer' | 'assistant'; content: string };
const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Hello — I can help with products, materials, MOQ, specifications, and quotation requests.' }]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { fetch(`${API}/chat/sessions`, { method: 'POST' }).then((res) => res.json()).then((data) => setSessionId(data.id)); }, []);
  async function send() {
    const content = input.trim();
    if (!content || !sessionId || busy) return;
    setInput(''); setMessages((current) => [...current, { role: 'customer', content }]); setBusy(true);
    const response = await fetch(`${API}/chat/messages`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, content }) });
    const data = await response.json(); setMessages((current) => [...current, { role: 'assistant', content: data.message.content }]); setBusy(false);
  }
  return <div className="widget"><header><div className="mark">✦</div><div><strong>Product concierge</strong><small>Online · AI assisted</small></div><button>×</button></header><section className="messages">{messages.map((message, index) => <div key={index} className={`message ${message.role}`}><p>{message.content}</p></div>)}{busy && <div className="typing">Checking the best way to help…</div>}</section><footer><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask about a product…" /><button onClick={send}>Send ↗</button></footer></div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);

