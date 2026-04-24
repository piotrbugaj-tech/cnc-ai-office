require('dotenv').config();
const express = require('express');
const https   = require('https');
const http    = require('http');
const path    = require('path');

const OLLAMA_HOST = process.env.OLLAMA_HOST || '127.0.0.1';
const OLLAMA_PORT = parseInt(process.env.OLLAMA_PORT || '11434', 10);

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

if (!process.env.ANTHROPIC_API_KEY) {
  console.warn('\n⚠️  ANTHROPIC_API_KEY nie ustawiony!');
  console.warn('   Skopiuj: cp .env.example .env  i wpisz klucz.\n');
}

app.post('/api/messages', (req, res) => {
  const body = JSON.stringify(req.body);
  const options = {
    hostname: 'api.anthropic.com',
    path:     '/v1/messages',
    method:   'POST',
    headers: {
      'Content-Type':      'application/json',
      'Content-Length':    Buffer.byteLength(body),
      'x-api-key':         process.env.ANTHROPIC_API_KEY || '',
      'anthropic-version': '2023-06-01'
    }
  };

  const proxyReq = https.request(options, proxyRes => {
    let data = '';
    proxyRes.on('data', chunk => { data += chunk; });
    proxyRes.on('end', () => {
      try {
        res.status(proxyRes.statusCode).json(JSON.parse(data));
      } catch {
        res.status(500).json({ error: { message: 'Parse error from Anthropic API' } });
      }
    });
  });

  proxyReq.on('error', err => {
    res.status(500).json({ error: { message: err.message } });
  });

  proxyReq.write(body);
  proxyReq.end();
});

// ── Ollama proxy ──────────────────────────────────────────────────────────────
function ollamaRequest(method, urlPath, body, res) {
  const bodyBuf = body ? Buffer.from(JSON.stringify(body)) : null;
  const opts = {
    hostname: OLLAMA_HOST,
    port:     OLLAMA_PORT,
    path:     urlPath,
    method,
    headers: { 'Content-Type': 'application/json',
               ...(bodyBuf ? { 'Content-Length': bodyBuf.length } : {}) }
  };
  const req = http.request(opts, pr => {
    let d = '';
    pr.on('data', c => { d += c; });
    pr.on('end', () => {
      try { res.status(pr.statusCode).json(JSON.parse(d)); }
      catch { res.status(500).json({ error: 'Ollama parse error' }); }
    });
  });
  req.on('error', e => res.status(503).json({ error: 'Ollama unavailable: ' + e.message }));
  if (bodyBuf) req.write(bodyBuf);
  req.end();
}

// List locally installed models
app.get('/api/ollama/models', (_req, res) => ollamaRequest('GET', '/api/tags', null, res));

// Chat (force stream:false so we get a single JSON response)
app.post('/api/ollama/chat', (req, res) => {
  ollamaRequest('POST', '/api/chat', { ...req.body, stream: false }, res);
});

// Health-check (used by the UI status dot)
app.get('/api/ollama/health', (_req, res) => ollamaRequest('GET', '/api/tags', null, res));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  const url = `http://localhost:${PORT}`;
  console.log(`\n🏭  CNC AI Office  →  ${url}\n`);
  import('open').then(m => m.default(url)).catch(() => {});
});
