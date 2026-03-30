# System Users y Business Manager — Arquitectura de Aislamiento

## Resumen ejecutivo
Para proteger los activos personales de Eder y escalar el Social Media Agent a múltiples clientes, usamos **Employee System Users** en un Business Manager dedicado a BluePaper.

## Arquitectura recomendada

```
Meta Business Manager "BluePaper"
│  (Eder = Admin)
│
├── System User "social-media-agent" (Employee)
│   ├── Asignado a: Página VelvetLabs
│   ├── Asignado a: Páginas de clientes
│   └── NO tiene acceso a: Páginas personales de Eder
│
├── App "BluePaper" (ID: 897009369997552)
│   └── Permisos: pages_manage_posts, pages_manage_metadata, instagram_*
│
└── Asset Groups (opcional, para organizar por cliente)
    ├── Grupo "VelvetLabs" → páginas de VelvetLabs
    └── Grupo "Cliente X" → páginas del cliente X
```

## System Users

### ¿Qué son?
Cuentas especiales sin perfil personal, diseñadas para acceso programático via API.

### Tipos
- **Admin System User**: Ve TODO en el BM. NO usar para el agente.
- **Employee System User**: Solo ve los activos asignados. USAR ESTE.

### Crear System User
```
# Via API
POST https://graph.facebook.com/v25.0/{business-id}/system_users
  ?name=social-media-agent
  &role=EMPLOYEE
  &access_token={admin_token}
```

### Asignar páginas al System User
```
# Solo las páginas que el agente puede tocar
POST https://graph.facebook.com/v25.0/{page-id}/assigned_users
  ?user={system-user-id}
  &tasks=MANAGE,CREATE_CONTENT,MODERATE,ADVERTISE,ANALYZE
  &access_token={admin_token}
```

### Token del System User
- Se genera en Business Settings > System Users > Generate Token
- **NUNCA EXPIRA** (a menos que se revoque o elimine el System User)
- Ideal para producción — no hay que renovar cada 60 días

## Aislamiento de seguridad

### Employee System User = Zero-Knowledge
Un Employee System User:
- ✅ SOLO puede ver/modificar páginas explícitamente asignadas
- ✅ NO puede descubrir otras páginas del BM
- ✅ NO puede ver la cuenta personal de Eder
- ❌ Un Admin System User VE TODO — nunca usar para el agente

### Safe-List en código (doble seguridad)
```python
ALLOWED_PAGE_IDS = load_from_database("bluepaper_client_pages")

def validate_page_access(page_id):
    if page_id not in ALLOWED_PAGE_IDS:
        raise SecurityError(f"Page {page_id} not in whitelist")
```

## Flujo de cliente

### Onboarding (cliente nuevo)
1. Crear página via browser automation
2. Reclamar página al BM: `POST /{business-id}/owned_pages?page_id={id}`
3. Asignar al System User del agente
4. Si el cliente tiene cuenta FB, agregarlo como Editor de su página

### Activo (cliente con servicio)
- El agente publica via System User Token
- El cliente puede editar su página como Editor
- BluePaper mantiene la propiedad en el BM

### Offboarding (cliente se va)
1. Verificar que el cliente tiene admin access en la página
2. Transferir propiedad: `DELETE /{business-id}/owned_pages?page_id={id}`
3. La página pasa al control personal del cliente
4. Periodo de espera: hasta 7 días

## Página creation via API
La creación de páginas via API está restringida por Meta. El approach actual (dev-browser) es el correcto:
1. Crear via browser → obtener Page ID
2. Reclamar al BM via API
3. Asignar al System User

## Business Manager secundario
- Un usuario puede tener hasta 2 BMs
- Recomendado: BM dedicado a BluePaper, separado de activos personales
- Crear en: business.facebook.com/overview
