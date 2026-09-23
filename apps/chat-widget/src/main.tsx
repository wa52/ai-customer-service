import { StrictMode, useEffect, useState } from 'react';
import type { ChangeEvent } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type VisionMatch = { image_id?: string; category?: string; description?: string; similarity?: number; source_url?: string };
type Message = { role: 'customer' | 'assistant'; content: string; attachmentUrl?: string };
const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8011/api/v1';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Hello — I can help with products, materials, MOQ, specifications, and quotation requests.' }]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState('');

  useEffect(() => { fetch(`${API}/chat/sessions`, { method: 'POST' }).then((res) => res.json()).then((data) => setSessionId(data.id)); }, []);
  function chooseImage(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    if (!selected.type.startsWith('image/')) return;
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImage(selected); setImagePreview(URL.createObjectURL(selected));
  }
  function clearImage() {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImage(null); setImagePreview('');
  }
  async function searchImage() {
    if (!image || !sessionId || busy) return;
    const preview = imagePreview;
    const form = new FormData(); form.append('session_id', sessionId); form.append('image', image);
    setBusy(true); setMessages((current) => [...current, { role: 'customer', content: 'I uploaded a product image for similar styles.', attachmentUrl: preview }]); clearImage();
    try {
      const response = await fetch(`${API}/chat/upload-image`, { method: 'POST', body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? 'Image search failed');
      const matches = (data.data?.matches ?? []) as VisionMatch[];
      const summary = matches.length
        ? `I found ${matches.length} visually similar styles: ${matches.slice(0, 3).map((match) => match.image_id ?? match.category ?? 'catalog style').join(', ')}. These are public reference images for inspiration.`
        : 'I could not find a close visual match yet. Please share the category or material and I can narrow the search.';
      setMessages((current) => [...current, { role: 'assistant', content: summary }]);
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', content: error instanceof Error ? error.message : 'Image search is temporarily unavailable.' }]);
    } finally { setBusy(false); }
  }
  async function send() {
    const content = input.trim();
    if (!content || !sessionId || busy) return;
    setInput(''); setMessages((current) => [...current, { role: 'customer', content }]); setBusy(true);
    const response = await fetch(`${API}/chat/messages/stream`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, content }) });
    if (!response.body) throw new Error('Streaming is unavailable');
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; let streamed = '';
    setMessages((current) => [...current, { role: 'assistant', content: '' }]);
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n'); buffer = events.pop() ?? '';
      for (const event of events) {
        if (!event.startsWith('event: token')) continue;
        const dataLine = event.split('\n').find((line) => line.startsWith('data: ')); if (!dataLine) continue;
        streamed += JSON.parse(dataLine.slice(6)).text;
        setMessages((current) => [...current.slice(0, -1), { role: 'assistant', content: streamed }]);
      }
    }
    setBusy(false);
  }
  return <div className="widget"><header><div className="mark">✦</div><div><strong>Product concierge</strong><small>Online · AI assisted</small></div><button aria-label="Close">×</button></header><section className="messages">{messages.map((message, index) => <div key={index} className={`message ${message.role}`}>{message.attachmentUrl && <img className="attachment" src={message.attachmentUrl} alt="Uploaded product reference" />}<p>{message.content}</p></div>)}{busy && <div className="typing">Checking the best way to help…</div>}</section><footer>{imagePreview && <div className="image-draft"><img src={imagePreview} alt="Selected product reference" /><button type="button" onClick={clearImage} aria-label="Remove selected image">×</button></div>}<div className="composer"><input className="file-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseImage} id="product-image" /><label className="attach-button" htmlFor="product-image" aria-label="Upload product image" title="Upload product image">⌁</label><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask about a product…" /></div><button onClick={image ? searchImage : send} disabled={busy || (!input.trim() && !image)}>{image ? 'Find ↗' : 'Send ↗'}</button></footer></div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
