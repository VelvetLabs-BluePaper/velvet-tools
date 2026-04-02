# Algoritmo Completo: Social Media Agent — De 0 a Página Operativa

## Resumen
Este algoritmo documenta TODOS los pasos para crear la presencia de un cliente
en Facebook e Instagram, desde cero hasta publicar contenido.
El agente de Social Media (Coworker en MacBook) ejecuta estos pasos autónomamente.

---

## FASE 1: Preparación (100% API, automático)

### 1.1 Crear email del cliente
**Método**: Cloudflare API
```bash
POST /zones/{zone_id}/email/routing/rules
{
  "name": "{cliente}",
  "matchers": [{"field": "to", "value": "{cliente}@bp-accounts.com"}],
  "actions": [{"type": "forward", "value": ["social@getbluepaper.com"]}]
}
```
**Resultado**: {cliente}@bp-accounts.com → social@getbluepaper.com

### 1.2 Generar contraseña segura
**Método**: Python
```python
import secrets, string
pw = 'Vlt' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(14)) + '!3Kz'
```

### 1.3 Guardar en Supabase
**Método**: SQL via psql o API
```sql
INSERT INTO social_accounts (platform, username, email, password_encrypted, status)
VALUES ('instagram', '{username}', '{cliente}@bp-accounts.com',
        crypt('{password}', gen_salt('bf', 12)), 'pending_creation');
```

---

## FASE 2: Crear página de Facebook (dev-browser, ~10 seg)

### 2.1 Navegar a facebook.com/pages/creation/
**Método**: dev-browser (Playwright)
```javascript
const page = await browser.getPage("create-page");
await page.goto("https://www.facebook.com/pages/creation/");
```

### 2.2 Llenar formulario
```javascript
await page.getByRole("textbox", { name: "Nombre de la página" }).fill("{nombre}");
const cat = page.getByRole("combobox", { name: "Categoría" });
await cat.fill("{categoria}");
await page.waitForTimeout(1500);
await page.getByText("{categoria_exacta}").first().click();
await page.getByRole("textbox", { name: "Presentación" }).fill("{bio}");
```

### 2.3 Crear página
```javascript
const btn = page.getByRole("button", { name: "Crear página" });
await btn.scrollIntoViewIfNeeded();
await btn.click();
```
**Resultado**: Page ID en la URL de redirección

### 2.4 Obtener Page Token automático
**Método**: Graph API con System User Token (NUNCA EXPIRA)
```bash
GET /me/accounts?access_token={SYSTEM_USER_TOKEN}
# Retorna el page token para la nueva página
```

### 2.5 Configurar página via API
```bash
# Logo
POST /{page_id}/photos?source=@logo.png&type=profile_picture&access_token={page_token}

# Ubicación
POST /{page_id}?location={"city":"Monterrey","state":"Nuevo León","country":"Mexico"}&access_token={page_token}

# Info adicional se configura en el mismo POST
```

### 2.6 Reclamar página al Business Manager
```bash
POST /{business_id}/owned_pages?page_id={page_id}&access_token={system_user_token}
```

---

## FASE 3: Crear cuenta de Instagram (Coworker, ~2 min)

### 3.1 Navegar al formulario de registro
**URL**: `instagram.com/accounts/emailsignup/`
**Método**: Coworker (Computer Use) — Instagram BLOQUEA CDP en formularios de signup

### 3.2 Llenar formulario
- Email: `{cliente}@bp-accounts.com`
- Contraseña: la generada en paso 1.2
- Nombre: `{nombre_negocio}`
- Username: `{username}` (verificar disponibilidad)
- Fecha de nacimiento: **1 de enero de 2000** (estándar para todas las cuentas)

### 3.3 Obtener código de verificación
**Método**: IMAP (automático)
```python
import imaplib, email, re
mail = imaplib.IMAP4_SSL("imap.hostinger.com", 993)
mail.login("social@getbluepaper.com", "{password}")
mail.select('INBOX')
status, msgs = mail.search(None, '(FROM "instagram")')
# Extraer código de 6 dígitos del último email
```

### 3.4 Ingresar código
**Método**: Coworker ingresa el código en el campo de verificación

---

## FASE 4: Convertir a cuenta profesional (CDP parcial + Coworker)

### 4.1 Navegar a conversión
**URL**: `instagram.com/accounts/convert_to_professional_account/`
**Método**: CDP funciona para navegación

### 4.2 Seleccionar "Negocio"
**Método**: CDP DOM resolve funciona
```python
dom_click('Negocio')  # Selecciona radio button
dom_click('Siguiente')  # Avanza
```

### 4.3 Página informativa
```python
dom_click('Siguiente')  # Skip info page
```

### 4.4 Seleccionar categoría
**Método**: CDP DOM resolve funciona para categorías predefinidas
```python
dom_click('Producto/servicio')  # O la categoría del cliente
dom_click('Listo')
```

### 4.5 Modal de confirmación
```python
# "¿Cambiar a una cuenta profesional?" → "Continuar"
# Buscar el link dentro del modal
```

### 4.6 Información de contacto
```python
# Click "No usar mi información de contacto" para saltar
# Coordenadas del botón (varía, usar listado de buttons)
```

### 4.7 Confirmación final
- Pantalla: "Tu cuenta de empresa de Instagram está lista"
- Click "Listo"

---

## FASE 5: Vincular Instagram con Facebook (Coworker obligatorio)

### 5.1 Navegar a Facebook como admin de la página
**Método**: Coworker
1. facebook.com/profile.php?id={page_id}
2. Click "Cambiar" para entrar como la página
3. Menú izquierdo → Configuración
4. Instagram → "Conectar cuenta"

### 5.2 Flujo de conexión
1. Modal: "Conectar con Instagram" → Click "Conectar"
2. Redirect a Instagram para autorizar
3. Seleccionar cuenta `{username}`
4. Confirmar vinculación
5. Configuración de mensajes: "Permitir acceso" → "Continuar"

### 5.3 Verificación por WhatsApp
**IMPORTANTE**: Meta puede pedir código de verificación por WhatsApp
- El código llega al número del WhatsApp Business API (WABA ID: 975935938289594)
- El agente debe leer el código del webhook de WhatsApp
- Ingresarlo en el formulario de Facebook
```python
# Leer código de WhatsApp via webhook
# POST /admin/api/whatsapp/webhook recibe el mensaje
# Extraer código de 6 dígitos
# Coworker lo ingresa en el formulario
```

### 5.4 Verificar vinculación via API
```bash
GET /{page_id}?fields=instagram_business_account&access_token={page_token}
# Debe retornar: {"instagram_business_account": {"id": "..."}}
```

---

## FASE 6: Configurar Instagram via API (100% automático)

### 6.1 Subir foto de perfil
```bash
# Instagram no permite cambiar foto via API directamente
# Usar Coworker o la foto se sincroniza desde la página de Facebook
```

### 6.2 Actualizar bio via API
```bash
POST /{ig_user_id}?biography={bio}&access_token={page_token}
```

### 6.3 Publicar primer post
```bash
# Paso 1: Crear media container
POST /{ig_user_id}/media?image_url={url}&caption={texto}&access_token={token}
# Paso 2: Publicar
POST /{ig_user_id}/media_publish?creation_id={container_id}&access_token={token}
```

---

## FASE 7: Guardar todo en Supabase

```sql
UPDATE social_accounts
SET ig_account_id = '{ig_business_id}',
    page_id = '{fb_page_id}',
    page_token_encrypted = crypt('{page_token}', gen_salt('bf', 12)),
    status = 'active',
    updated_at = now()
WHERE email = '{cliente}@bp-accounts.com';
```

---

## Resumen de métodos por paso

| Paso | Método | Tiempo |
|------|--------|--------|
| Email | Cloudflare API | 1s |
| Contraseña | Python | 0s |
| Supabase | SQL | 1s |
| FB Page | dev-browser | 10s |
| FB Config (logo, bio) | Graph API | 2s |
| FB al Business Manager | Graph API | 1s |
| IG Signup | **Coworker** | 60s |
| IG Código email | IMAP | 5s |
| IG → Profesional | CDP + Coworker | 30s |
| IG ↔ FB vinculación | **Coworker** | 60s |
| WhatsApp código | Webhook | 10s |
| IG Config | Graph API | 2s |
| Supabase update | SQL | 1s |
| **Total** | | **~3 min** |

## Qué funciona con CDP (sin Coworker)
- ✅ Crear FB page (dev-browser)
- ✅ Configurar FB page (Graph API)
- ✅ Leer emails IMAP
- ✅ Convertir IG a profesional (parcial)
- ✅ Publicar contenido (Graph API)

## Qué requiere Coworker (MacBook)
- ❌ Crear cuenta de Instagram (signup form)
- ❌ Vincular IG con FB page (UI de Facebook)
- ❌ Ingresar códigos de verificación en formularios de Meta
- ❌ Resolver captchas si aparecen

## Tokens y credenciales
- **System User Token**: NUNCA expira — usar para todas las operaciones de API
- **IMAP**: social@getbluepaper.com para códigos de verificación de Instagram
- **WhatsApp Webhook**: para códigos de verificación de Facebook
- **Supabase**: contraseñas encriptadas con pgcrypto (bcrypt)
- **Cloudflare API**: para crear emails de clientes
