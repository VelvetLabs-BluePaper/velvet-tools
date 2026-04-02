"""
WhatsApp Intent Router — Ventas / Soporte / Social Media
Extiende el MessageRouter de BluePaper para detectar intención via Haiku.

Flujo:
  1. Mensaje llega al webhook
  2. ¿Tiene suscripción activa?
     NO → route: "sales" (ElevenLabs/Ana)
     SÍ → Haiku detecta intención:
       - "soporte" → Support handler (ElevenLabs voz + texto)
       - "social_media" → Social Media handler (Graph API, texto, double opt-in)
       - "ambiguo" → Asume soporte (fallback)

Aprobado por Nina con 3 reglas:
  1. Fallback a soporte si intención no es clara
  2. Double opt-in para acciones en redes sociales
  3. No tocar producción sin validar en sandbox

Autor: Velvet
Fecha: 2026-04-02
"""
import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("whatsapp.router")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# System prompt for intent detection (~200 tokens)
INTENT_PROMPT = """Eres un clasificador de intención para BluePaper (agencia web).
El cliente tiene una suscripción activa. Clasifica su mensaje en UNA categoría:

- "soporte": problemas con su página web, no carga, errores, cambiar contraseña, ajustes técnicos, preguntas sobre su servicio
- "social_media": quiere publicar algo en redes, cambiar foto de perfil/portada de FB/IG, pedir contenido para redes, ver estadísticas de redes
- "ventas": quiere contratar algo nuevo, preguntar precios de otros servicios, upgrade de plan
- "ambiguo": no queda claro qué necesita

Responde SOLO con la categoría, nada más. Ejemplo: soporte"""


async def detect_intent(message: str) -> str:
    """
    Detect intent using Claude Haiku. Cost: ~$0.001 per call.
    Returns: "soporte", "social_media", "ventas", or "ambiguo"
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — defaulting to soporte")
        return "soporte"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": HAIKU_MODEL,
                    "max_tokens": 10,
                    "system": INTENT_PROMPT,
                    "messages": [{"role": "user", "content": message}],
                },
            )
            data = resp.json()
            intent = data["content"][0]["text"].strip().lower()

            # Validate intent
            valid = {"soporte", "social_media", "ventas", "ambiguo"}
            if intent not in valid:
                logger.warning("Invalid intent '%s' — fallback to soporte", intent)
                return "soporte"

            logger.info("Intent detected: %s", intent)
            return intent

    except Exception as e:
        logger.error("Intent detection failed: %s — fallback to soporte", e)
        return "soporte"


class IntentRouter:
    """
    Extended WhatsApp message router with intent detection.

    Usage:
        router = IntentRouter(db_client)
        result = await router.route("+5215512345678", "Quiero cambiar mi logo de Instagram")
        # → {"route": "social_media", "intent": "social_media", "subscription": {...}}
    """

    def __init__(self, db_client):
        self.db = db_client

    async def route(self, whatsapp_number: str, message_text: str) -> dict:
        """Route an incoming WhatsApp message."""
        subscription = self._find_active_subscription(whatsapp_number)

        if not subscription:
            # No subscription → Sales
            return {"route": "sales", "intent": "ventas"}

        # Active subscriber → detect intent
        intent = await detect_intent(message_text)

        if intent == "ambiguo":
            # Fallback to soporte (Nina's rule #1)
            return {
                "route": "soporte",
                "intent": "ambiguo",
                "subscription": subscription,
            }

        if intent == "ventas":
            # Upsell — route to sales but with subscription context
            return {
                "route": "sales",
                "intent": "ventas",
                "subscription": subscription,
            }

        # soporte or social_media
        return {
            "route": intent,
            "intent": intent,
            "subscription": subscription,
        }

    def _find_active_subscription(self, whatsapp_number: str) -> Optional[dict]:
        """Find active subscription by WhatsApp number."""
        result = (
            self.db.table("subscriptions")
            .select("*, sites(*, leads(*))")
            .eq("status", "active")
            .execute()
        )
        if not result.data:
            return None

        for sub in result.data:
            site = sub.get("sites") or {}
            lead = site.get("leads") or {}
            if lead.get("whatsapp_number") == whatsapp_number:
                return sub
        return None


# ─── Social Media Handler ───

SOCIAL_SYSTEM_PROMPT = """Eres el asistente de redes sociales de BluePaper. El cliente tiene una página de Facebook y/o Instagram que tú administras.

Puedes hacer:
- Publicar posts en Facebook e Instagram
- Cambiar foto de perfil o portada
- Actualizar información de la página (bio, horario, ubicación)
- Mostrar estadísticas básicas

REGLAS:
- SIEMPRE confirma antes de ejecutar cualquier acción: "¿Publico esto ahora mismo en tu Instagram?"
- Si el cliente dice "sí", ejecuta la acción
- Si dice algo ambiguo, pregunta de nuevo
- Responde en español mexicano, mensajes cortos (1-3 oraciones)
- NUNCA publiques sin confirmación explícita del cliente"""


async def handle_social_media(
    whatsapp_number: str,
    message_text: str,
    subscription: dict,
    pending_action: Optional[dict] = None,
) -> dict:
    """
    Handle social media requests from WhatsApp.
    Returns: {"reply": str, "action": Optional[dict]}

    If the client confirms a pending action, execute it.
    If not, propose the action and wait for confirmation (double opt-in).
    """
    site = subscription.get("sites") or {}
    lead = site.get("leads") or {}
    client_name = lead.get("business_name", "tu negocio")

    # Check if client is confirming a pending action
    if pending_action:
        confirmation = message_text.strip().lower()
        if confirmation in ("sí", "si", "yes", "dale", "ok", "adelante", "hazlo", "confirmo"):
            # Execute the action
            result = await execute_social_action(pending_action, subscription)
            return {
                "reply": result.get("message", "Listo, acción ejecutada."),
                "action": None,  # Clear pending
            }
        else:
            return {
                "reply": "Entendido, no se realizó ningún cambio. ¿En qué más te puedo ayudar?",
                "action": None,
            }

    # Generate response with Haiku
    context = f"Cliente: {client_name}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": HAIKU_MODEL,
                    "max_tokens": 300,
                    "system": SOCIAL_SYSTEM_PROMPT + "\n" + context,
                    "messages": [{"role": "user", "content": message_text}],
                },
            )
            data = resp.json()
            reply = data["content"][0]["text"]

            # Detect if Haiku proposed an action (contains confirmation question)
            action = None
            if "?" in reply and any(
                kw in reply.lower()
                for kw in ["publico", "cambio", "actualizo", "subo"]
            ):
                action = {
                    "type": "proposed",
                    "original_message": message_text,
                    "proposed_reply": reply,
                }

            return {"reply": reply, "action": action}

    except Exception as e:
        logger.error("Social media handler error: %s", e)
        return {
            "reply": "Disculpa, tuve un problema. ¿Puedes repetir tu solicitud?",
            "action": None,
        }


async def execute_social_action(action: dict, subscription: dict) -> dict:
    """
    Execute a confirmed social media action via Graph API.
    Uses System User Token (never expires).
    """
    # TODO: Implement actual Graph API calls
    # This will use the System User Token stored in env
    # and the page_token from Supabase social_accounts table
    return {
        "success": True,
        "message": "✅ Listo, se realizó el cambio en tu página.",
    }


# ─── Example usage ───

if __name__ == "__main__":
    import asyncio

    async def test():
        # Test intent detection
        tests = [
            "Mi página no carga",
            "Quiero publicar una foto en Instagram",
            "¿Cuánto cuesta el plan premium?",
            "Cambien la foto de mi perfil de Facebook",
            "Hola buenos días",
        ]
        for msg in tests:
            intent = await detect_intent(msg)
            print(f"  '{msg}' → {intent}")

    asyncio.run(test())
