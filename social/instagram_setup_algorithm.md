# Algoritmo: Crear y Vincular Instagram para Cliente

## Prerequisitos
- Facebook Page del cliente ya creada
- Email del cliente creado en bp-accounts.com (Cloudflare)
- Contraseña generada y guardada en Supabase (social_accounts)
- Acceso IMAP a social@getbluepaper.com para códigos de verificación

## Paso 1: Crear cuenta de Instagram
**URL**: `instagram.com/accounts/emailsignup/`
**Método**: Coworker (Computer Use) — Instagram bloquea CDP/dev-browser en formularios

1. Navegar a instagram.com/accounts/emailsignup/
2. Llenar campos:
   - Email: `{cliente}@bp-accounts.com`
   - Contraseña: generada automáticamente (24 chars, letras+números+símbolos)
   - Nombre: `{nombre_negocio}`
   - Username: `{username}` (verificar disponibilidad)
   - Fecha nacimiento: 1 de enero de 2000 (estándar)
3. Click "Enviar"
4. Esperar código de verificación en email (IMAP → social@getbluepaper.com)
5. Extraer código de 6 dígitos del email de Instagram
6. Ingresar código en Instagram
7. Cuenta creada

## Paso 2: Convertir a cuenta profesional (Negocio)
**URL**: `instagram.com/accounts/convert_to_professional_account/`
**Método**: Coworker O CDP (DOM resolve funciona parcialmente)

1. Navegar a instagram.com/accounts/convert_to_professional_account/
2. Seleccionar "Negocio" (radio button)
3. Click "Siguiente"
4. Página informativa → Click "Siguiente"
5. Seleccionar categoría (según el tipo de negocio del cliente)
6. Click "Listo"

## Paso 3: Vincular con Facebook Page
**Método**: Coworker — requiere navegar UI de Facebook

1. Ir a facebook.com/profile.php?id={page_id}
2. Cambiar a modo admin de la página
3. Menú → "Promocionar publicación de Instagram"
4. Redirige a Settings → Instagram → "Conectar cuenta"
5. Click "Conectar"
6. Confirmar vinculación con la cuenta de IG recién creada
7. Confirmar mensajería de Instagram

## Paso 4: Configurar perfil de Instagram
**Método**: Graph API (con System User Token)

```bash
# Subir foto de perfil (misma que FB page)
POST /{ig-user-id}/media
  ?image_url={logo_url}
  &access_token={system_user_token}

# Actualizar bio
POST /{ig-user-id}
  ?biography={bio}
  &access_token={system_user_token}
```

## Paso 5: Guardar en Supabase
```sql
UPDATE social_accounts
SET ig_account_id = '{ig_user_id}',
    status = 'active',
    updated_at = now()
WHERE email = '{cliente}@bp-accounts.com'
  AND platform = 'instagram';
```

## Paso 6: Reclamar al Business Manager
```bash
POST /{business-id}/owned_pages
  ?page_id={page_id}
  &access_token={system_user_token}
```

## Notas técnicas
- Instagram BLOQUEA: insertText, Input events en formularios de signup
- Instagram PERMITE: DOM resolve clicks en radio buttons y botones de navegación
- Facebook BLOQUEA: clicks programáticos en diálogos de OAuth
- Facebook PERMITE: DOM resolve clicks en la mayoría de botones internos
- CDP funciona para navegación y screenshots, NO para llenar formularios de Meta
- Coworker (Computer Use, MacBook) resuelve TODOS los bloqueos porque ve píxeles reales

## Tiempos estimados
- Con Coworker: ~2 minutos total (automatizado)
- Sin Coworker: ~5 minutos (parcialmente manual)
- Via API solamente: NO POSIBLE (Instagram no tiene API de creación de cuentas)
