# VelvetTools — Herramientas compartidas de VelvetLabs
# Repo: VelvetLabs-BluePaper/velvet-tools
# Stack: Node.js + Python | Herramientas cross-proyecto

## Propósito
Infraestructura compartida que usan todos los agentes de VelvetLabs:
- **browser/**: Automatización de browser (dev-browser + CDP)
- **social/**: Social Media Agent (FB, IG, X, LinkedIn)
- **integrations/**: Conectores compartidos (APIs, webhooks)

## Reglas
- Este repo NO es un producto — es tooling interno
- Cada herramienta debe ser autocontenida y documentada
- Los agentes (Velvet, Exo, Nebular, Nina) importan lo que necesitan
- Tests obligatorios para cada herramienta

## Browser Automation
- **dev-browser**: CLI principal para acciones rápidas (Playwright sandbox)
- **CDP raw**: Fallback para páginas pesadas (Facebook, Meta Business Suite)
- **snapshotForAI()**: Clave para navegar menús dinámicos
- Chrome debe correr con `--remote-debugging-port=9222 --remote-allow-origins=*`

## Social Media Agent
- Fase 1: Setup via browser (crear páginas, obtener API tokens)
- Fase 2: Operación via API (publicar contenido, analytics)
- Plataformas: Meta (FB/IG), X, LinkedIn
