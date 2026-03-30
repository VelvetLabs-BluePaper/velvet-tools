# Meta Setup — Guía para el Social Media Agent

## Flujo completo: Crear página FB → Configurar → Instagram → Enlazar

### Prerequisitos (one-time)
- Chrome con `--remote-debugging-port=9222 --remote-allow-origins=*`
- `npm install -g dev-browser && dev-browser install`
- App de Meta "BluePaper" (ID: 897009369997552) en developers.facebook.com
- Usuario con rol Admin/Developer en la app (para dev mode)
- User Access Token con permisos: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `pages_manage_metadata`

### Paso 1: Crear página de Facebook (dev-browser, ~10 seg)

```bash
dev-browser --connect http://localhost:9222 --timeout 30 << 'EOF'
const page = await browser.getPage("create-page");
await page.goto("https://www.facebook.com/pages/creation/");
await page.waitForLoadState("domcontentloaded");
await page.waitForTimeout(2000);

// Llenar nombre
await page.getByRole("textbox", { name: "Nombre de la página (obligatorio)" }).fill("NOMBRE_PAGINA");
await page.waitForTimeout(300);

// Llenar categoría (escribir + seleccionar del dropdown)
const categoryBox = page.getByRole("combobox", { name: "Categoría (obligatorio)" });
await categoryBox.fill("CATEGORIA");
await page.waitForTimeout(1500);
await page.getByText("CATEGORIA_EXACTA").first().click();
await page.waitForTimeout(500);

// Bio (opcional)
await page.getByRole("textbox", { name: "Presentación (opcional)" }).fill("BIO_TEXT");
await page.waitForTimeout(300);

// Crear página
const btn = page.getByRole("button", { name: "Crear página" });
await btn.scrollIntoViewIfNeeded();
await btn.click();
await page.waitForTimeout(5000);

console.log(JSON.stringify({ url: page.url(), title: await page.title() }));
EOF
```

**Resultado**: Facebook redirige a wizard de configuración. El Page ID se obtiene de la URL o via API.

### Notas importantes del proceso:
- `snapshotForAI()` ayuda a descubrir la estructura de la página pero hace timeout en Facebook (~20s)
- `getByRole()` + `fill()` es más confiable que coordenadas
- `scrollIntoViewIfNeeded()` es necesario para botones fuera del viewport
- NO se necesita captcha si la sesión está autenticada con perfil real
- Facebook genera un avatar automático con la inicial del nombre

### Paso 2: Obtener Page ID y Token (Graph API, automático)

```bash
# El User Token ya tiene los permisos (del OAuth inicial)
USER_TOKEN="EAAM..."

# Obtener TODAS las páginas con sus tokens
curl -s "https://graph.facebook.com/v25.0/me/accounts?access_token=$USER_TOKEN"
# Retorna: { data: [{ name, id, access_token, category }, ...] }

# Buscar la página recién creada por nombre
PAGE_ID=$(curl -s "https://graph.facebook.com/v25.0/me/accounts?access_token=$USER_TOKEN" | \
  python -c "import json,sys; d=json.load(sys.stdin); print([p['id'] for p in d['data'] if p['name']=='NOMBRE_PAGINA'][0])")

PAGE_TOKEN=$(curl -s "https://graph.facebook.com/v25.0/me/accounts?access_token=$USER_TOKEN" | \
  python -c "import json,sys; d=json.load(sys.stdin); print([p['access_token'] for p in d['data'] if p['name']=='NOMBRE_PAGINA'][0])")
```

### Paso 3: Configurar página via Graph API

```bash
# Subir logo (foto de perfil)
curl -X POST "https://graph.facebook.com/v25.0/$PAGE_ID/photos" \
  -F "source=@logo.png" \
  -F "type=profile_picture" \
  -F "access_token=$PAGE_TOKEN"

# Cambiar información de la página
curl -X POST "https://graph.facebook.com/v25.0/$PAGE_ID" \
  -d "location={\"city\":\"Monterrey\",\"state\":\"Nuevo León\",\"country\":\"Mexico\"}" \
  -d "about=Descripción de la empresa" \
  -d "website=https://ejemplo.com" \
  -d "phone=+528112345678" \
  -d "access_token=$PAGE_TOKEN"

# Publicar primer post
curl -X POST "https://graph.facebook.com/v25.0/$PAGE_ID/feed" \
  -d "message=¡Bienvenidos a nuestra página!" \
  -d "access_token=$PAGE_TOKEN"

# Subir foto con post
curl -X POST "https://graph.facebook.com/v25.0/$PAGE_ID/photos" \
  -F "source=@imagen.jpg" \
  -F "message=Nuestra primera publicación" \
  -F "access_token=$PAGE_TOKEN"
```

### Paso 4: Crear Instagram (via Meta Business Suite browser)

Instagram NO se puede crear via API. Se crea desde:
1. Meta Business Suite > Configuración > Conectar Instagram
2. O desde la app de Instagram directamente

Para automatizarlo via browser:
```bash
dev-browser --connect http://localhost:9222 --timeout 30 << 'EOF'
const page = await browser.getPage("ig-setup");
await page.goto("https://business.facebook.com/latest/settings/instagram_account_v2");
// ... navegar el wizard de conexión
EOF
```

### Paso 5: Enlazar Facebook + Instagram

Una vez que la cuenta de IG existe, se vincula con la página:
```bash
# Vincular IG con FB Page
curl -X POST "https://graph.facebook.com/v25.0/$PAGE_ID" \
  -d "instagram_business_account=$IG_ACCOUNT_ID" \
  -d "access_token=$PAGE_TOKEN"

# O via Meta Business Suite UI (más confiable)
```

### Permisos necesarios (App Review)

| Permiso | Para qué | ¿Requiere App Review? |
|---------|----------|----------------------|
| pages_show_list | Listar páginas | No (dev mode OK) |
| pages_read_engagement | Leer métricas | No (dev mode OK) |
| pages_manage_posts | Publicar contenido | Sí (pero dev mode OK para admins) |
| pages_manage_metadata | Cambiar info de página | Sí (pero dev mode OK para admins) |
| instagram_basic | Info de IG | Sí |
| instagram_content_publish | Publicar en IG | Sí |

**CLAVE**: En Development Mode, usuarios con rol Admin/Developer en la app pueden usar TODOS los permisos sin App Review.

### Dev Mode vs Live Mode

- **Dev Mode**: Solo funciona para usuarios con rol en la app. Ideal para setup inicial y testing.
- **Live Mode**: Requiere App Review. Necesario cuando clientes externos autorizan la app.
- **Estrategia**: Usar Dev Mode para todo el setup de VelvetLabs. Solicitar App Review solo cuando BluePaper necesite manejar páginas de clientes externos.

### Tokens y seguridad

- **User Token**: Expira en ~60 días. Se puede extender a long-lived.
- **Page Token**: Obtenido de /me/accounts. Expira cuando el User Token expira.
- **System User Token**: NUNCA expira. Ideal para producción.
- **Aislamiento**: Usar Employee System User asignado solo a páginas específicas.
