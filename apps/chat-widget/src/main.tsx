import { StrictMode, useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import './catalog.css';
import './support.css';

type VisionMatch = CatalogProduct & { image_id?: string; description?: string; similarity?: number };
type Message = { role: 'customer' | 'assistant'; content: string; attachmentUrl?: string; products?: CatalogProduct[] };
type CatalogProduct = { sku: string; name: string; display_name?: string; category: string; material?: string; plating?: string; color?: string; size?: string; moq?: number | null; reference_price?: number | null; currency?: string; image_url?: string; source_url?: string; source_name?: string };
const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8011/api/v1';

const categories = [
  { id: '', label: '全部款式' },
  { id: 'ring', label: '戒指' },
  { id: 'bracelet', label: '手链' },
  { id: 'necklace', label: '项链' },
  { id: 'jewelry', label: '其他饰品' },
];

function ProductSite() {
  const [items, setItems] = useState<CatalogProduct[]>([]);
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [supportOpen, setSupportOpen] = useState(false);
  const pageSize = 24;

  useEffect(() => {
    const timer = window.setTimeout(() => { setSubmittedQuery(query.trim()); setPage(1); }, 220);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (submittedQuery) params.set('q', submittedQuery);
    if (category) params.set('category', category);
    setLoading(true); setError('');
    fetch(`${API}/products?${params}`).then(async (response) => {
      if (!response.ok) throw new Error(response.status === 503 ? '产品目录暂时无法连接，请检查后台数据源。' : '产品加载失败，请稍后重试。');
      return response.json();
    }).then((data) => { setItems(data.items); setTotal(data.total); }).catch((reason: unknown) => {
      setItems([]); setTotal(0); setError(reason instanceof Error ? reason.message : '产品加载失败，请稍后重试。');
    }).finally(() => setLoading(false));
  }, [category, page, submittedQuery]);

  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  return <main className="catalog-site">
    <button className="support-launcher" type="button" aria-label={supportOpen ? '关闭 AI 导购' : '打开 AI 导购'} aria-expanded={supportOpen} aria-controls="support-chat-panel" onClick={() => setSupportOpen((open) => !open)}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13v-1a8 8 0 0 1 16 0v1M4 12h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-5Zm16 0h-3a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-5Z" /></svg>
      <span>AI 导购</span>
    </button>
    {supportOpen && <div id="support-chat-panel" className="support-panel"><App compact onClose={() => setSupportOpen(false)} /></div>}
    <div className="catalog-topline"><span>DESIGN NOTES · JEWELRY</span><span>公开目录参考 · 非正式报价</span></div>
    <nav className="catalog-nav"><a className="catalog-wordmark" href="/products">FORMA<span> / </span>OBJECTS</a><div className="catalog-navlinks"><a className="nav-active" href="#collection">产品目录</a><a href="#about">关于材质</a><a href="#support-chat-panel" onClick={(event) => { event.preventDefault(); setSupportOpen(true); }}>在线客服 ↗</a></div><a className="catalog-contact" href="#support-chat-panel" onClick={(event) => { event.preventDefault(); setSupportOpen(true); }}>咨询选款 <span>↗</span></a></nav>
    <section className="catalog-hero">
      <div className="hero-copy"><span className="catalog-kicker"><i /> MATERIAL · FORM · EVERYDAY</span><h1>让日常的<br /><em>光泽</em>有迹可循。</h1><p>从简洁线条到细节镶嵌，浏览公开珠宝目录，发现适合下一次灵感的款式。</p><a className="hero-cta" href="#collection">探索产品目录 <span>↓</span></a><div className="hero-note"><strong>2,223</strong><span>款公开目录参考<br />价格与库存以供应商为准</span></div></div>
      <div className="hero-art"><div className="hero-image-frame">{items[0]?.image_url && <img src={items[0].image_url} alt={items[0].display_name || items[0].name} onError={(event) => { event.currentTarget.parentElement?.classList.add('image-missing'); event.currentTarget.style.display = 'none'; }} />}</div><div className="hero-stamp"><span>FORM<br />STUDY</span><b>OBJECT 01</b></div><span className="hero-caption">PUBLIC CATALOG<br />STYLE REFERENCE</span></div>
    </section>
    <section className="catalog-assurance" id="about"><div><span className="assurance-index">A / MATERIAL</span><strong>材质与工艺</strong><p>按公开商品页所示信息展示；具体规格请以原始来源为准。</p></div><div><span className="assurance-index">B / REFERENCE</span><strong>参考价格</strong><p>展示公开参考价，不代表本店报价、库存或供货承诺。</p></div><div><span className="assurance-index">C / ASSIST</span><strong>选款协助</strong><p>告诉我们品类与偏好，客服可以继续帮你筛选。</p></div></section>
    <section className="catalog-collection" id="collection">
      <div className="collection-heading"><div><span className="catalog-kicker"><i /> THE COLLECTION</span><h2>产品目录 <span>({total.toLocaleString()})</span></h2></div><label className="catalog-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索款式、材质或编号" /><kbd>↵</kbd></label></div>
      <div className="catalog-filters"><div className="category-tabs">{categories.map((item) => <button key={item.id || 'all'} className={category === item.id ? 'selected' : ''} onClick={() => { setCategory(item.id); setPage(1); }}>{item.label}</button>)}</div><span className="result-count">{loading ? '正在载入…' : `显示 ${items.length} / ${total} 款`}</span></div>
      {error ? <div className="catalog-state catalog-error">{error}</div> : loading && !items.length ? <div className="catalog-state">正在为你整理目录…</div> : !items.length ? <div className="catalog-state">没有找到匹配款式。试试其他关键词或分类。</div> : <div className="product-grid">{items.map((product, index) => <article className="product-card" key={product.sku}>
        <a className="product-image" href={product.source_url || '#'} target={product.source_url ? '_blank' : undefined} rel="noreferrer" aria-label={`前往 ${product.name} 购买页面`}><span className="product-index">{String((page - 1) * pageSize + index + 1).padStart(3, '0')}</span><span className="product-source">公开参考</span>{product.image_url ? <img src={product.image_url} alt={product.name} loading="lazy" onError={(event) => { event.currentTarget.parentElement?.classList.add('image-missing'); event.currentTarget.style.display = 'none'; }} /> : <span className="image-fallback">{product.category}</span>}{product.source_url && <span className="product-buy-cta">前往购买 ↗</span>}</a>
        <div className="product-meta"><div><span className="product-category">{categories.find((item) => item.id === product.category)?.label || product.category}</span><span className="product-sku">{product.sku}</span></div><a href="#support-chat-panel" aria-label="咨询这款产品" onClick={(event) => { event.preventDefault(); setSupportOpen(true); }}>＋</a></div><h3>{product.display_name || product.name}</h3><div className="product-specs">{[product.material, product.plating, product.color, product.size].filter(Boolean).slice(0, 3).join(' · ') || '规格以来源页面为准'}</div><div className="product-bottom"><strong>{product.reference_price != null ? `${product.currency || 'USD'} ${product.reference_price.toFixed(2)}` : '询问参考价'}</strong>{product.moq ? <span>MOQ {product.moq}</span> : <span>公开目录</span>}</div>
      </article>)}</div>}
      {pageCount > 1 && <div className="catalog-pagination"><button disabled={page <= 1 || loading} onClick={() => { setPage((current) => current - 1); document.getElementById('collection')?.scrollIntoView({ behavior: 'smooth' }); }}>← 上一页</button><span>{page} <i>/</i> {pageCount}</span><button disabled={page >= pageCount || loading} onClick={() => { setPage((current) => current + 1); document.getElementById('collection')?.scrollIntoView({ behavior: 'smooth' }); }}>下一页 →</button></div>}
    </section>
    <footer className="catalog-footer"><a className="catalog-wordmark" href="/products">FORMA<span> / </span>OBJECTS</a><p>公开产品信息与价格均保留来源属性，仅作目录参考。</p><a href="#support-chat-panel" onClick={(event) => { event.preventDefault(); setSupportOpen(true); }}>需要帮助？联系在线客服 ↗</a></footer>
  </main>;
}

function App({ compact = false, onClose }: { compact?: boolean; onClose?: () => void }) {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Hello — I can help with products, materials, MOQ, specifications, and quotation requests.' }]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [modelConfigured, setModelConfigured] = useState<boolean | null>(null);
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState('');
  const messagesRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    fetch(`${API}/chat/sessions`, { method: 'POST' }).then((res) => res.json()).then((data) => setSessionId(data.id)).catch(() => undefined);
    fetch(`${API}/admin/config`).then((res) => res.json()).then((data) => setModelConfigured(Boolean(data.configured))).catch(() => setModelConfigured(false));
  }, []);
  useEffect(() => {
    const messageList = messagesRef.current;
    if (messageList) messageList.scrollTop = messageList.scrollHeight;
  }, [messages, busy]);
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
      const products = matches.filter((match) => Boolean(match.sku)).slice(0, 3);
      const chinese = /[\u4e00-\u9fff]/.test(input) || /^zh(?:-|$)/i.test(navigator.language);
      const summary = products.length
        ? chinese
          ? `找到 ${products.length} 款相似商品，已按图片相似度排序。点击商品卡片查看公开供应商商品页与下单信息；参考价格及供货情况以供应商页面为准。`
          : `I found ${products.length} similar products, ranked by image similarity. Select a card for the supplier's product and ordering page; confirm pricing and availability with the supplier.`
        : matches.length
        ? chinese
          ? `找到 ${matches.length} 张相似参考图片：${matches.slice(0, 3).map((match) => match.image_id ?? match.category ?? '参考款').join('、')}。这些来自公开图片数据集，可供款式参考。`
          : `I found ${matches.length} visually similar styles: ${matches.slice(0, 3).map((match) => match.image_id ?? match.category ?? 'catalog style').join(', ')}. These are public reference images for inspiration.`
        : chinese ? '暂时没有找到相似图片。你可以告诉我品类或材质，我再帮你缩小范围。' : 'I could not find a close visual match yet. Please share the category or material and I can narrow the search.';
      setMessages((current) => [...current, { role: 'assistant', content: summary, products }]);
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', content: error instanceof Error ? error.message : 'Image search is temporarily unavailable.' }]);
    } finally { setBusy(false); }
  }
  async function send() {
    const content = input.trim();
    if (!content || !sessionId || busy) return;
    setInput(''); setMessages((current) => [...current, { role: 'customer', content }]); setBusy(true);
    setMessages((current) => [...current, { role: 'assistant', content: '' }]);
    try {
      const response = await fetch(`${API}/chat/messages/stream`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, content }) });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      if (!response.body) throw new Error('Streaming is unavailable');
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; let streamed = '';
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n'); buffer = events.pop() ?? '';
        for (const event of events) {
          if (event.startsWith('event: products')) {
            const dataLine = event.split('\n').find((line) => line.startsWith('data: '));
            if (dataLine) {
              const products = JSON.parse(dataLine.slice(6)) as CatalogProduct[];
              setMessages((current) => current.map((message, index) => index === current.length - 1 && message.role === 'assistant' ? { ...message, products } : message));
            }
            continue;
          }
          if (event.startsWith('event: error')) {
            const dataLine = event.split('\n').find((line) => line.startsWith('data: '));
            const detail = dataLine ? JSON.parse(dataLine.slice(6)).message : undefined;
            throw new Error(detail ?? 'The assistant is temporarily unavailable');
          }
          if (!event.startsWith('event: token')) continue;
          const dataLine = event.split('\n').find((line) => line.startsWith('data: ')); if (!dataLine) continue;
          streamed += JSON.parse(dataLine.slice(6)).text;
          setMessages((current) => [...current.slice(0, -1), { role: 'assistant', content: streamed }]);
        }
      }
    } catch (error) {
      const chinese = /[\u4e00-\u9fff]/.test(content);
      const detail = error instanceof Error ? error.message : 'connection error';
      const localizedDetail = chinese && detail === 'The assistant timed out or is temporarily unavailable.'
        ? '模型暂时没有响应，请稍后重试。'
        : detail;
      const message = `${chinese ? '暂时无法发送消息' : 'Could not send your message'}: ${localizedDetail}`;
      setMessages((current) => [...current.slice(0, -1), { role: 'assistant', content: message }]);
    } finally { setBusy(false); }
  }
  return <div className={`widget${compact ? ' support-chat' : ''}`}><header><div className="mark">✦</div><div><strong>Product concierge</strong><small>{modelConfigured === false ? 'Online · Basic catalog mode' : 'Online · AI assisted'}</small></div><button type="button" aria-label="关闭客服" onClick={onClose}>×</button></header><section className="messages" ref={messagesRef}>{messages.map((message, index) => <div key={index} className={`message ${message.role}`}>{message.attachmentUrl && <img className="attachment" src={message.attachmentUrl} alt="Uploaded product reference" />}<p>{message.content}</p>{Boolean(message.products?.length) && <div className="chat-recommendations">{message.products?.slice(0, 3).map((product) => <a className="chat-product-card" href={product.source_url || '#'} target={product.source_url ? '_blank' : undefined} rel="noreferrer" key={product.sku}>{product.image_url ? <img src={product.image_url} alt="" loading="lazy" /> : <span className="chat-product-placeholder">✦</span>}<span className="chat-product-info"><strong>{product.display_name || product.name}</strong><small>{product.sku}</small><small>{product.reference_price != null ? `参考价 ${product.currency || 'USD'} ${product.reference_price.toFixed(2)}` : '公开目录参考'}</small>{'similarity' in product && typeof product.similarity === 'number' && <small>图片相似度 {(product.similarity * 100).toFixed(0)}%</small>}</span>{product.source_url && <span className="chat-product-cta">前往购买 ↗</span>}</a>)}</div>}</div>)}{busy && <div className="typing">Checking the best way to help…</div>}</section><footer>{imagePreview && <div className="image-draft"><img src={imagePreview} alt="Selected product reference" /><button type="button" onClick={clearImage} aria-label="Remove selected image">×</button></div>}<div className="composer"><input className="file-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseImage} id="product-image" /><label className="attach-button" htmlFor="product-image" aria-label="Upload product image" title="Upload product image">⌁</label><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask about a product…" /></div><button onClick={image ? searchImage : send} disabled={busy || (!input.trim() && !image)}>{image ? 'Find ↗' : 'Send ↗'}</button></footer></div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode>{window.location.pathname.startsWith('/products') ? <ProductSite /> : <App />}</StrictMode>);
