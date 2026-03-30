# Browser Automation — VelvetTools

Automatización de browser para agentes de VelvetLabs.

## Requisitos
- `npm install -g dev-browser && dev-browser install`
- Chrome con `--remote-debugging-port=9222 --remote-allow-origins=*`
- Python 3.10+ con `websocket-client` (para CDP fallback)

## Uso rápido
```bash
# Conectar a Chrome y navegar
dev-browser --connect http://localhost:9222 --timeout 30 << 'EOF'
const page = await browser.getPage("main");
await page.goto("https://example.com");
const snapshot = await page.snapshotForAI();
console.log(snapshot.full);
EOF
```

## Archivos
- `navigator.js` — Navegador dinámico para menús (Meta Business Suite, etc.)
- `cdp_fallback.py` — Fallback CDP raw para páginas pesadas
