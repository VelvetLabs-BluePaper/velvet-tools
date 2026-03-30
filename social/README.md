# Social Media Agent — VelvetTools

Agente autónomo para gestionar presencia en redes sociales de VelvetLabs.

## Flujo
1. **Setup** (browser): Crear páginas, configurar perfil, obtener API tokens
2. **Operación** (API): Publicar contenido, programar posts, analytics

## Plataformas
- Meta (Facebook + Instagram) via Graph API
- X (Twitter) via API v2
- LinkedIn via API

## Archivos
- `meta_setup.js` — Setup de páginas FB/IG via browser
- `meta_api.py` — Publicación de contenido via Graph API
- `config.json` — Tokens y page IDs (gitignored)
