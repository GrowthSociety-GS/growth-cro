# Connections Manager - GrowthCRO

**Version:** 1.0.0
**Last Updated:** 2026-04-05
**Status:** Production
**Owner:** Growth Society CRO Team

---

## ROLE

Le **Connections Manager** est l'architecte des intégrations du GrowthCRO. Il gère:

- **Configuration & activation** de toutes les connexions externes (Notion, Catchr, Frame.io, Ads Society, Netlify, etc.)
- **Authentification sécurisée** (OAuth 2.0, API keys) avec chiffrement des credentials
- **Gestion du cycle de vie** des connexions (configure → test → connect → monitor → disconnect)
- **Health checks périodiques** pour valider que les connexions restent actives et fonctionnelles
- **Gestion des webhooks** pour les services qui push des données vers GrowthCRO
- **Rate limiting & caching** pour optimiser les appels API et respecter les quotas
- **Fallback strategies** quand une connexion est down
- **Audit trail** de toutes les opérations d'intégration (qui, quand, quoi)

Le Connections Manager est la colonne vertébrale de GrowthCRO. Aucun module ne peut fonctionner sans lui.

---

## ARCHITECTURE GLOBALE

### Flow d'une intégration

```
┌─────────────────────────────────────────────────────────────┐
│                     CONNECTIONS MANAGER                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Config Page   │  │ Test Suite   │  │ Connection Pool  │ │
│  │  (UI/UX)       │  │ (validation)  │  │ (active tunnels) │ │
│  └────────────────┘  └──────────────┘  └──────────────────┘ │
│           │                  │                    │           │
│           └──────────────────┴────────────────────┘           │
│                              │                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Credentials Store (Supabase encrypted)         │  │
│  │  - OAuth tokens (refresh/access)                       │  │
│  │  - API keys (encrypted at rest)                        │  │
│  │  - Webhook secrets                                     │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │      Health Check Engine (runs every 5 min)            │  │
│  │  - Test connectivity to each service                   │  │
│  │  - Validate credentials still valid                    │  │
│  │  - Update status indicators (green/amber/red/grey)    │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │     API Gateway & Rate Limiting                        │  │
│  │  - Route requests to correct service                   │  │
│  │  - Apply rate limits per service                       │  │
│  │  - Cache responses (with TTL)                          │  │
│  │  - Queue overflow requests                             │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                    │
└───────────┼────────────────────────────────────────────────────┘
            │
     ┌──────┴──────┐
     │             │
  ┌──▼───────┐  ┌──▼────────────┐
  │ Webhooks │  │ External APIs  │
  │ (inbound)│  │ (outbound)     │
  └──────────┘  └────────────────┘
```

---

## INTÉGRATIONS DÉTAILLÉES

### P0 - NOTION (Critical)

**Purpose:** Bidirectional sync avec la knowledge base CRO (pages, bases de données, blocks)

#### Authentification
- **Type:** OAuth 2.0 (Server-to-Server Integration)
- **Flow:**
  1. User clique "Connect Notion" sur la connections page
  2. Redirect vers `https://api.notion.com/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&owner=user`
  3. User autorise GrowthCRO à accéder à son workspace Notion
  4. Notion renvoie `code` de courte durée
  5. Backend échange le code contre `access_token` (indéfini) via POST à `https://api.notion.com/v1/oauth/token`
  6. Token stocké encrypté en Supabase avec `workspace_id`, `bot_id`, `user_id`

**Credentials stockés:**
```json
{
  "integration_id": "notion",
  "workspace_id": "xyz...",
  "access_token": "secret_...", // encrypted
  "bot_id": "bot_xyz...",
  "user_id": "user_xyz...",
  "expires_at": null, // Notion tokens don't expire
  "last_validated": "2026-04-05T10:30:00Z",
  "status": "connected"
}
```

#### Endpoints & Rate Limits
- **Base URL:** `https://api.notion.com/v1`
- **Rate Limit:** 3 req/sec (bursting up to 100 req/min)
- **Endpoints nécessaires:**
  - `GET /databases/{database_id}` — Fetch database structure
  - `GET /databases/{database_id}/query` — Query database (CRO strategies, test results)
  - `GET /pages/{page_id}` — Fetch page details
  - `GET /blocks/{block_id}/children` — Fetch block children (paragraphs, lists, etc.)
  - `POST /pages` — Create new page (for AI learnings, insights)
  - `PATCH /pages/{page_id}` — Update page properties (status, tags, performance data)
  - `POST /blocks/{block_id}/children` — Append blocks to page

#### Data Model

**Collections clés à syncer:**

1. **CRO Strategies** (database)
   ```
   ├─ Name (title)
   ├─ Status (select: Draft, Active, Paused, Archived)
   ├─ Client (relation)
   ├─ Test Type (select: A/B, Multivariate, Holdout)
   ├─ Expected Lift (%)
   ├─ Start Date
   ├─ End Date
   ├─ Performance Data (JSON block with metrics)
   └─ AI Insights (rich text, updated by GrowthCRO)
   ```

2. **Test Results** (database)
   ```
   ├─ Strategy (relation)
   ├─ Variant (text)
   ├─ Sample Size
   ├─ Conversion Rate
   ├─ Statistical Significance
   ├─ Winner (select: Control, Challenger A, Challenger B)
   └─ Conclusion (rich text)
   ```

3. **Knowledge Base** (pages hierarchy)
   - CRO Best Practices
   - Industry Benchmarks
   - Client Case Studies
   - Hypothesis Library

#### Sync Strategy

**Pull (Notion → GrowthCRO):**
- Tous les 30min: fetch databases & pages modifiés
- Indexer le contenu dans la mémoire du Connections Manager pour recherche rapide
- Créer des notifications si status strategy change ou new test results

**Push (GrowthCRO → Notion):**
- Quand l'AI Learning Engine génère une insight, créer une page dans "AI Learnings"
- Mettre à jour les properties de stratégie avec les métriques en temps réel
- Append rich text blocks avec les observations et recommandations

#### Error Handling
```
Cas d'erreur courants:
- 401 Unauthorized → Token expiré/révoqué → mark as "pending" (amber)
- 403 Forbidden → Workspace access revoked → mark as "error" (red)
- 429 Too Many Requests → Rate limit hit → back-off exponential (1s, 2s, 4s, 8s)
- Connection timeout → Service down → mark as "error" (red), retry after 5min
- Invalid page_id → Notion page deleted → log warning, skip sync
```

#### Webhook Handling
Notion envoie webhooks pour certains événements (si option "subscriptions" activée). Setup:
- **Endpoint:** `https://growthcro.internal/webhooks/notion`
- **Events:** `database.updated`, `page.updated`, `database.deleted`
- **Validation:** Vérifier header `X-Notion-Signature` (HMAC-SHA256)
- **Retry policy:** Notion retry 3x avec backoff exponentiel

---

### P0 - CATCHR (Critical)

**Purpose:** Agrégateur analytics pour 80+ platforms (Google Analytics, Meta, TikTok, Shopify, etc.)

#### Authentification
- **Type:** API Key (REST API + Webhooks)
- **API Key:** Fourni par Catchr via dashboard
- **Flow:**
  1. Admin GrowthCRO crée un app dans Catchr dashboard
  2. Copie l'API Key (ex: `cat_prod_xyz...`)
  3. Stocke en Supabase encrypté avec `workspace_id`

**Credentials stockés:**
```json
{
  "integration_id": "catchr",
  "api_key": "cat_prod_xyz...", // encrypted
  "workspace_id": "xyz...",
  "connected_platforms": [
    {
      "id": "google_analytics_4",
      "property_id": "123456789",
      "status": "connected"
    },
    {
      "id": "meta_ads",
      "business_id": "xyz...",
      "status": "pending" // awaiting user to authorize on Meta
    }
  ],
  "last_validated": "2026-04-05T10:30:00Z",
  "status": "connected"
}
```

#### Endpoints & Rate Limits
- **Base URL:** `https://api.catchr.io/v2`
- **Rate Limit:** 60 req/min (per API key)
- **Endpoints nécessaires:**
  - `GET /sources` — List connected analytics platforms
  - `GET /sources/{source_id}/status` — Check if a platform is still authorized
  - `GET /metrics/{metric_key}` — Fetch metric data (CVR, CPA, ROI, etc.)
    - Query params: `start_date`, `end_date`, `breakdown` (by campaign, platform, etc.)
  - `GET /attributions` — Multi-touch attribution data
  - `GET /health` — Service health check

**Example Request:**
```bash
curl -H "Authorization: Bearer cat_prod_xyz..." \
  "https://api.catchr.io/v2/metrics/conversion_rate?start_date=2026-03-01&end_date=2026-04-05&breakdown=platform"
```

#### Data Model

Catchr agrège ces data points clés:

```
┌─ Campaign Performance
│  ├─ Impressions
│  ├─ Clicks
│  ├─ CTR
│  ├─ Spend
│  ├─ Conversions
│  ├─ CVR (Conversion Rate)
│  ├─ CPA (Cost Per Acquisition)
│  ├─ ROI
│  └─ ROAS (Return on Ad Spend)
│
├─ Attribution
│  ├─ First-Touch (which platform gave first impression)
│  ├─ Last-Touch (which platform gave last click)
│  ├─ Linear (equal credit to all touchpoints)
│  ├─ Time-Decay (credit decreases over time)
│  └─ Custom Models (ML-based)
│
└─ Source Breakdowns
   ├─ Google Analytics 4 (sessions, users, events)
   ├─ Meta Ads (campaign, ad set, ad level)
   ├─ Google Ads (campaign, ad group level)
   ├─ TikTok Ads (campaign level)
   ├─ Shopify (orders, revenue, AOV)
   └─ ... (80+ other platforms)
```

#### Sync Strategy

**Pull (Catchr → GrowthCRO):**
- **Real-time (via webhooks):** Catchr push new conversion/transaction data
- **Daily (batch):** Full sync of all metrics pour yesterday
- **On-demand:** User clicks "Refresh" on dashboard, fetch latest 24h data
- **Cache:** Store last 90 days in local cache with 5min TTL

**Usage by modules:**
- **Dashboard (Performance Widget):** Fetch last 7d performance, refresh every 30s (with cache)
- **AI Learning Engine:** Pull performance data for tested strategies to calculate statistical significance
- **Client Context:** Pull CVR & CPA data for client comparison/benchmarking

#### Error Handling
```
Cas d'erreur courants:
- 401 Unauthorized → API key invalid or revoked → mark as "error" (red)
- 403 Forbidden → Rate limit exceeded → queue request, retry after 60s
- 404 Not Found → Source/metric doesn't exist → log warning, skip
- 500 Service Error → Catchr API down → mark as "error" (red), retry after 5min
- Platform auth revoked (e.g., Meta) → 403 from Catchr → Update connected_platforms[].status to "pending"
```

#### Webhook Handling
Catchr peut envoyer webhooks quand:
- Nouvelle conversion reçue
- Attribut d'une conversion change (ex: user corrigé)
- Platform auth revoked

**Endpoint:** `https://growthcro.internal/webhooks/catchr`
**Validation:** Header `X-Catchr-Signature` (HMAC-SHA256 of request body)
**Retry policy:** Catchr retry 3x avec backoff exponentiel

---

### P1 - FRAME.IO (Important)

**Purpose:** Gestion des assets vidéo/visuels (review, feedback, versioning)

#### Authentification
- **Type:** OAuth 2.0 (Frame.io API v2)
- **Flow:** Similar to Notion
  1. User clique "Connect Frame.io"
  2. Redirect vers `https://frameio.com/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&redirect_uri=<REDIRECT_URI>`
  3. User autorise GrowthCRO
  4. Exchange code pour access_token via POST à `https://api.frame.io/oauth/token`
  5. Token stocké encrypté

**Credentials:**
```json
{
  "integration_id": "frameio",
  "access_token": "fio_xyz...", // encrypted
  "user_id": "frameio_user_xyz",
  "refresh_token": "fio_refresh_xyz...", // encrypted
  "expires_at": "2026-05-05T10:30:00Z",
  "last_validated": "2026-04-05T10:30:00Z",
  "status": "connected"
}
```

#### Endpoints & Rate Limits
- **Base URL:** `https://api.frame.io`
- **Rate Limit:** 1000 req/hour
- **Endpoints:**
  - `GET /v2/teams/{team_id}` — Get team info
  - `GET /v2/projects` — List all projects
  - `GET /v2/projects/{project_id}` — Get project details
  - `GET /v2/assets/{asset_id}` — Get asset (video, image)
  - `POST /v2/assets` — Upload new asset
  - `POST /v2/projects` — Create new project
  - `GET /v2/comments?asset_id={asset_id}` — Get feedback/comments on asset

#### Data Model
```
Project (folder for a client or campaign)
├─ Assets (videos, images)
│  ├─ Metadata (title, duration, resolution, created_at, updated_at)
│  ├─ Comments (feedback from team members)
│  └─ Versions (history of changes)
└─ Team Members (who can access)
```

#### Usage
- **Asset Library:** Store GrowthCRO-created creatives (landing page screenshots, explainer videos)
- **Client Context:** Fetch brand assets (logos, color palettes, brand videos) from client's Frame.io project
- **Collaboration:** Link to Frame.io assets in test results for easy review

#### Error Handling
- 401 → Token expired → Refresh via refresh_token
- 403 → User removed from workspace → Mark as "error"
- 429 → Rate limit → Queue requests
- Connection error → Retry after 5min

---

### P1 - ADS SOCIETY (Important)

**Purpose:** Proprietary ad platform data (campaigns, creatives, audiences, performance)

#### Authentification
- **Type:** Custom API (REST + API Key)
- **API Key:** Provided by Ads Society team (internal)
- **Format:** `Header: Authorization: Bearer ads_soc_prod_xyz...`

**Credentials:**
```json
{
  "integration_id": "ads_society",
  "api_key": "ads_soc_prod_xyz...", // encrypted
  "account_id": "ads_acct_xyz...",
  "workspace_id": "xyz...",
  "last_validated": "2026-04-05T10:30:00Z",
  "status": "connected"
}
```

#### Endpoints & Rate Limits
- **Base URL:** `https://api.ads-society.internal/v1`
- **Rate Limit:** 100 req/sec
- **Endpoints:**
  - `GET /campaigns` — List campaigns (status, spend, performance)
  - `GET /campaigns/{campaign_id}` — Campaign details (targeting, budget, metrics)
  - `GET /creatives` — List creatives (ads, images, copy variations)
  - `GET /audiences` — List audience segments
  - `GET /metrics/{campaign_id}` — Performance metrics (impressions, clicks, conversions)

#### Usage
- **Client Context:** Fetch traffic data (impressions, clicks, spend) for context
- **Dashboard:** Display ads performance widget (last 7d, 30d, MTD)
- **AI Learning Engine:** Analyze creative performance by variant

#### Error Handling
- 401 → API key invalid → Mark as "error"
- 500 → Service down → Retry after 5min
- Connection timeout → Retry with exponential backoff

---

### P1 - NETLIFY (Important)

**Purpose:** Deployment de pages générées (HTML landing pages, test variants)

#### Authentification
- **Type:** OAuth 2.0 (Netlify API)
- **Flow:** Similar to Notion/Frame.io
- **Personal Access Token alternative:** User can paste token directly (for testing/dev)

**Credentials:**
```json
{
  "integration_id": "netlify",
  "access_token": "nf_xyz...", // encrypted
  "user_id": "netlify_user_xyz",
  "refresh_token": null, // Netlify tokens don't expire
  "last_validated": "2026-04-05T10:30:00Z",
  "status": "connected"
}
```

#### Endpoints & Rate Limits
- **Base URL:** `https://api.netlify.com/api/v1`
- **Rate Limit:** 200 req/min
- **Endpoints:**
  - `GET /sites` — List all sites
  - `POST /sites` — Create new site
  - `POST /sites/{site_id}/deploys` — Create deploy (upload HTML/CSS/JS)
  - `PATCH /sites/{site_id}` — Update site config (domain, build settings)
  - `GET /sites/{site_id}/deploys/{deploy_id}` — Check deploy status

#### Data Model
```
Site
├─ Name (auto-generated: "growthcro-test-xyz")
├─ Domain (auto-assigned: xyz.netlify.app OR custom domain)
├─ Deploys
│  ├─ Timestamp
│  ├─ Status (building, live, failed)
│  ├─ Files uploaded (HTML, CSS, JS)
│  └─ URL
└─ Team/Collaborators
```

#### Usage
- **GSG (Growth Strategy Generator):** When GSG generates a landing page, deploy it via Netlify
- **A/B Testing:** Deploy control + challengers, get unique URLs
- **QA:** Preview pages before running ads

#### Error Handling
- 401 → Token invalid → Mark as "error"
- 403 → User doesn't have permission to deploy → Mark as "error"
- 422 → Invalid site config → Log error, ask user to review
- 500 → Netlify API down → Retry after 5min

---

### P2 - VERCEL (Nice-to-have)

**Purpose:** Alternative to Netlify for deployment

#### Minimal integration:
- OAuth 2.0
- Endpoints: `POST /v13/deployments`, `GET /v13/deployments/{id}`
- Same deployment flow as Netlify
- Fallback when Netlify unavailable

---

### P2 - CLOUDFLARE (Nice-to-have)

**Purpose:** CDN + custom domain management

#### Minimal integration:
- API Key authentication
- Endpoints: `POST /zones/{zone_id}/dns_records`, `PATCH /zones/{zone_id}/settings`
- Used when deploying with custom domain

---

### P2 - SLACK (Nice-to-have)

**Purpose:** Notifications & alerts (strategy results, errors, milestones)

#### Minimal integration:
- OAuth 2.0 or Webhook URL
- Endpoints: `POST /api/chat.postMessage`, `POST /api/files.upload`
- Setup channel: #growthcro-alerts
- Send notifications on: strategy completed, high CVR lift, connection error, etc.

---

### P2 - GOOGLE ANALYTICS (Nice-to-have)

**Purpose:** Direct GA4 data access (if Catchr insufficient)

#### Minimal integration:
- OAuth 2.0
- Endpoint: `GET /v1beta/properties/{property_id}:runReport`
- Used as fallback if Catchr doesn't cover a client's GA setup

---

### P2 - GOOGLE ADS (Nice-to-have)

**Purpose:** Direct Google Ads data (if Catchr insufficient)

#### Minimal integration:
- OAuth 2.0
- Endpoint: `GET /v17/customers/{customer_id}/google_ads_fields`
- Used as fallback for Google Ads-specific insights

---

### P2 - META ADS (Nice-to-have)

**Purpose:** Direct Meta Ads data (if Catchr insufficient)

#### Minimal integration:
- OAuth 2.0
- Endpoint: `GET /{ad_account_id}/insights`
- Used as fallback for Meta-specific insights

---

## GESTION DU CYCLE DE VIE

### État d'une connexion

```
DISCONNECTED (grey)
     ↓
    CONFIGURE (user fills form + submits)
     ↓
   PENDING (amber) ← awaiting user OAuth consent OR credential test
     ↓ (user completes OAuth OR credentials valid)
  TESTING (amber) ← running health checks
     ↓
CONNECTED (green) ← healthy, ready to use
     ↓ (periodic health checks pass)
    HEALTHY (green) ← confirmed still working
     ↓ (health check fails OR token expires OR error in API call)
   ERROR (red) ← user must reconnect OR review credentials
     ↓
    DISCONNECT (user clicks "Disconnect")
     ↓
 DISCONNECTED (grey)
```

### Workflow: Connect a new integration

**1. Configuration**
- User goes to Settings → Connections
- Clicks "Add Connection"
- Selects integration type (e.g., "Notion")
- Form appears with instructions:
  - For OAuth: "Click 'Authorize' to open Notion login"
  - For API Key: "Paste your API key"
  - For credentials: "Enter username/password" (rare)

**2. Authentication**
- OAuth: Redirect to service login, user approves scopes, return with auth code
- API Key: User pastes key, stored encrypted immediately
- Credentials: User submits, tested immediately

**3. Testing**
- Run test API call to service:
  - Notion: `GET /users/me`
  - Catchr: `GET /health`
  - Frame.io: `GET /me` (get current user)
  - Netlify: `GET /user` (get current user)
- If test passes → move to CONNECTED
- If test fails → show error message, move to ERROR

**4. Monitoring**
- Health check engine runs every 5min
- Tests each connected integration
- If fails 3x in a row (15min) → mark as ERROR, notify user

**5. Disconnection**
- User clicks "Disconnect" on connection card
- Credentials deleted from Supabase
- All API tokens revoked (where possible)
- Status moved to DISCONNECTED

---

## STATUS INDICATORS & UI/UX

### Connection Card (UI)

```
┌────────────────────────────────────────────────────────┐
│ [Notion Logo] Notion                         [⋮ menu]  │
│ ✓ Connected (last validated 5 min ago)                │
│                                                         │
│ Workspace: My Growth CRO Workspace                     │
│ Bot: GrowthCRO Integration                             │
│                                                         │
│ [Disconnect]  [Test Connection]  [View Logs]           │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ [Catchr Logo] Catchr                       [⋮ menu]   │
│ ⚠ Pending (awaiting Meta ads authorization)           │
│                                                         │
│ Connected Platforms: Google Analytics 4, TikTok Ads    │
│ Pending Platforms: Meta Ads                            │
│                                                         │
│ [Reconnect Meta]  [Manage Platforms]  [View Logs]      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ [Frame.io Logo] Frame.io                   [⋮ menu]   │
│ ✗ Error (token expired - 3 hours ago)                  │
│                                                         │
│ Last Error: 401 Unauthorized                           │
│                                                         │
│ [Reconnect]  [View Logs]  [Delete]                     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ [Netlify Logo] Netlify                     [⋮ menu]   │
│ ○ Not Connected                                        │
│                                                         │
│ [Connect]  [View Docs]                                 │
└────────────────────────────────────────────────────────┘
```

### Status Colors
- **Green (✓):** Connected & healthy
- **Amber (⚠):** Pending authorization OR health check in progress
- **Red (✗):** Error - reconnection needed
- **Grey (○):** Not connected

### Menu Actions (⋮)
- View Logs (show last 50 API calls + responses)
- Test Connection (manual health check)
- Manage Scopes (for OAuth)
- Rotate Credentials (if applicable)
- Disconnect
- Delete (if disconnected)

---

## HEALTH CHECK SYSTEM

### Periodic Health Checks

**Schedule:** Every 5 minutes
**Timeout:** 10 seconds per integration
**Parallelization:** Check all integrations concurrently

**Health Check Logic:**

```javascript
async function healthCheck(integration) {
  try {
    // Test endpoint pour chaque service
    const endpoints = {
      notion: () => GET /users/me,
      catchr: () => GET /health,
      frameio: () => GET /v2/me,
      ads_society: () => GET /health,
      netlify: () => GET /user,
    };

    const response = await fetch(endpoints[integration.type], {
      headers: decryptAndAddAuthHeaders(integration.credentials),
      timeout: 10000,
    });

    if (response.ok) {
      // Mark as healthy
      updateStatus(integration.id, "connected", {
        last_validated: now(),
        consecutive_failures: 0,
      });
    } else if (response.status === 401 || response.status === 403) {
      // Token invalid/expired
      incrementFailures(integration.id);
      if (failures >= 3) {
        updateStatus(integration.id, "error", {
          error_message: "Authentication failed - token may be expired",
        });
        notifyUser(`${integration.name} needs re-authentication`);
      }
    } else {
      incrementFailures(integration.id);
      if (failures >= 3) {
        updateStatus(integration.id, "error", {
          error_message: `Service returned ${response.status}`,
        });
      }
    }
  } catch (error) {
    incrementFailures(integration.id);
    if (failures >= 3) {
      updateStatus(integration.id, "error", {
        error_message: `Connection timeout or network error`,
      });
    }
  }
}
```

### Alerting
- **3+ consecutive failures** → Mark as ERROR, send notification
- **Connection restored** → Mark as CONNECTED, send notification
- **Token about to expire** (if applicable) → Send "reconnect soon" reminder

### Logging
- Every health check logged: `{ integration_id, timestamp, status, response_code, duration_ms }`
- Stored in `connections_health_log` table (rolling 30-day retention)
- Accessible in UI under "View Logs"

---

## SÉCURITÉ

### Credential Storage

**All credentials encrypted at rest in Supabase:**

```
Table: integrations_credentials
├─ id (UUID)
├─ integration_id (string, FK to connections)
├─ workspace_id (UUID, FK to workspaces)
├─ credential_type (enum: oauth_token, api_key, basic_auth)
├─ encrypted_data (bytea) ← All sensitive data here
├─ created_at (timestamp)
├─ updated_at (timestamp)
└─ expires_at (timestamp, nullable)

Encryption: AES-256-GCM with workspace-specific key
Key storage: AWS KMS (managed key per workspace)
```

**Decryption flow:**
1. Request comes in from authenticated user
2. Validate user has workspace access
3. Fetch encryption key from KMS (cached, 1-hour TTL)
4. Decrypt credential_data
5. Use credential in API call
6. Destroy decrypted data from memory immediately

### Token Rotation

**OAuth tokens (Notion, Frame.io, Netlify):**
- Refresh tokens: Store & use to get new access tokens before expiry
- If refresh fails → Mark as ERROR, notify user

**API Keys (Catchr, Ads Society):**
- No automatic rotation (rely on service to invalidate compromised keys)
- Manual rotation: User re-enters key in UI

### Rate Limiting & Quotas

**Per integration:**
```json
{
  "notion": { "limit": 3, "per_seconds": 1, "burst": 100 },
  "catchr": { "limit": 60, "per_minutes": 1 },
  "frameio": { "limit": 1000, "per_hours": 1 },
  "netlify": { "limit": 200, "per_minutes": 1 }
}
```

**Implementation:** Token bucket algorithm in Redis
```
redis_key: connections:rate_limit:{integration_id}:{workspace_id}
value: { tokens_available, last_refill }

Check before request:
  if (tokens_available > 0) {
    tokens_available--;
    make request;
  } else {
    queue request for retry after 1 sec;
  }
```

### Audit Trail

**All connection operations logged:**
```
Table: connections_audit_log
├─ id (UUID)
├─ workspace_id (UUID)
├─ user_id (UUID)
├─ integration_id (string)
├─ action (enum: connect, test, disconnect, rotate_credential)
├─ status (success, failure)
├─ error_message (nullable)
├─ ip_address
├─ user_agent
├─ created_at (timestamp)
└─ metadata (JSON, e.g., { scopes_granted, api_endpoint_called })

Retention: 1 year
Access: Only workspace admins can view
```

---

## RATE LIMITING & CACHING

### Caching Strategy

**Multi-layer cache:**

```
┌─────────────────────────────────────────────────────┐
│          GrowthCRO Application Memory Cache         │
│  (in-memory, 1GB max, TTL 5min per endpoint)       │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│            Redis Distributed Cache                  │
│  (shared across all servers, TTL 30min)            │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│         External API (Notion, Catchr, etc.)        │
└─────────────────────────────────────────────────────┘
```

**Cache policies by integration:**

| Integration | Endpoint | TTL | Invalidation |
|---|---|---|---|
| Notion | GET /databases | 1h | On push or webhook |
| Notion | GET /pages/{id} | 30m | On push or webhook |
| Catchr | GET /metrics | 5m | Manual refresh or webhook |
| Frame.io | GET /projects | 1h | Manual refresh |
| Ads Society | GET /campaigns | 15m | Manual refresh |
| Netlify | GET /sites | 1h | Manual refresh |

**Cache invalidation on change:**
- When user updates data in GrowthCRO, invalidate related cache
- When webhook received from external service, invalidate immediately

### Rate Limit Handling

**When rate limit hit (429 response):**
```javascript
async function makeRequest(integration, endpoint) {
  let retries = 0;
  const maxRetries = 3;

  while (retries < maxRetries) {
    try {
      const response = await apiCall(integration, endpoint);
      if (response.status === 429) {
        // Get retry-after header
        const retryAfter = parseInt(response.headers['retry-after']) || 60;
        await sleep(retryAfter * 1000);
        retries++;
      } else if (response.ok) {
        return response;
      } else {
        throw new ApiError(response.status, response.statusText);
      }
    } catch (error) {
      if (retries < maxRetries) {
        // Exponential backoff: 1s, 2s, 4s
        await sleep(Math.pow(2, retries) * 1000);
        retries++;
      } else {
        throw error;
      }
    }
  }
}
```

**Queue overflow:**
- If rate limit persists, queue request in Redis queue
- Process queue in batches (respecting rate limits)
- Notify user of delayed data refresh

---

## FALLBACK BEHAVIOR

When a connection is down, GrowthCRO gracefully degrades:

| Integration Down | Behavior | User Experience |
|---|---|---|
| **Notion** | Cache previous sync results (max 7 days old) | "Knowledge base data is cached (last updated X hours ago)" |
| **Catchr** | Show cached metrics from last 24h | "Performance data may be delayed" |
| **Frame.io** | Hide asset library section | "Asset library temporarily unavailable" |
| **Ads Society** | Show cached campaign data | "Campaign data may be delayed" |
| **Netlify** | Disable deploy button, show cached deployments | "Unable to deploy new pages right now" |

**Critical connections (P0):**
- If Notion down → Cannot access knowledge base, but AI still works with cached context
- If Catchr down → Cannot run performance analysis, show cached metrics with "STALE" label

**Non-critical connections (P1/P2):**
- If down → Simply disable the feature, show friendly message

---

## WEBHOOK HANDLING

### Receiving Webhooks

**Endpoint:** `POST https://growthcro.internal/webhooks/{integration_id}`

**Common webhook types:**
- Notion: `database.updated`, `page.updated`, `page.created`
- Catchr: `conversion.new`, `platform.disconnected`, `metric.updated`
- Frame.io: `asset.updated`, `comment.created`
- Ads Society: `campaign.status_changed`, `metrics.updated`

### Webhook Validation

**All webhooks must be validated before processing:**

```javascript
function validateWebhookSignature(req) {
  const signature = req.headers['x-signature'] || req.headers['x-notion-signature'];
  const body = req.rawBody; // must capture raw body before JSON parsing

  // Get signing secret from credentials store
  const secret = decryptCredential(req.query.integration_id, 'webhook_secret');

  // Compute expected signature
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');

  if (!crypto.timingSafeEqual(signature, expectedSignature)) {
    throw new Error('Invalid webhook signature');
  }
}
```

### Webhook Processing

```javascript
async function handleWebhook(req) {
  const { integration_id } = req.query;
  const { event, data } = req.body;

  // Validate signature
  validateWebhookSignature(req);

  // Process event
  switch(integration_id) {
    case 'notion':
      if (event === 'page.updated') {
        // Invalidate cache for this page
        await cache.invalidate(`notion:page:${data.page_id}`);
        // Queue sync for related modules
        await queue.push({ type: 'notion_sync', page_id: data.page_id });
      }
      break;

    case 'catchr':
      if (event === 'conversion.new') {
        // Real-time conversion event
        await updateMetricsCache(data);
        // Notify dashboard to refresh
        await notifyDashboard({ type: 'metrics_updated' });
      }
      break;

    // ... more cases
  }

  // Return 200 OK immediately
  res.status(200).json({ ok: true });
}
```

### Retry Policy
- **Idempotent processing:** Use `event_id` deduplication
- **Dead letter queue:** If webhook fails to process, store in DLQ for manual review
- **Idempotency key:** Webhook can be retried without duplicate side effects

---

## MONITORING & OBSERVABILITY

### Metrics to track

```
connections:health_check_duration_ms (histogram)
connections:api_calls_total (counter)
  labels: integration, method, status_code
connections:api_errors_total (counter)
  labels: integration, error_type
connections:webhook_received_total (counter)
  labels: integration, event_type
connections:credential_rotations_total (counter)
  labels: integration
connections:rate_limit_hits_total (counter)
  labels: integration
```

### Logs
- Structured JSON logs with `integration_id`, `timestamp`, `level`, `message`, `context`
- Store in ELK stack or similar
- Searchable UI in Connections Manager

### Alerts
- Connection down for 15+ minutes → PagerDuty alert
- Rate limit hit 3+ times in 1 hour → Slack notification
- Webhook processing failure → Log to error channel
- Token about to expire → Email user

---

## API REFERENCE (for modules using Connections Manager)

### Core Functions

```javascript
// Get a single metric from Catchr
const cvr = await connections.getCatchrMetric('conversion_rate', {
  start_date: '2026-04-01',
  end_date: '2026-04-05',
  breakdown: 'campaign',
});

// Fetch from Notion
const strategies = await connections.getNotionDatabase('CRO Strategies');

// Deploy to Netlify
const deployment = await connections.deployToNetlify({
  site_name: 'growthcro-test-abc123',
  html_content: '<html>...',
  css_content: 'body { ... }',
});

// Sync data to Notion
await connections.updateNotionPage('page_id', {
  properties: {
    'CVR Lift': '+12.5%',
    'Status': 'Completed',
  },
  content: '## AI Insights\n...',
});

// Get connection status
const status = await connections.getStatus('catchr');
// returns: { status: 'connected', last_validated: '...', error: null }

// Check if integration is healthy before using
const isHealthy = await connections.isHealthy('notion');
if (!isHealthy) {
  logger.warn('Notion is down, using cached context');
  return getCachedNotionData();
}
```

---

## TROUBLESHOOTING

### Common Issues

**"Connection Pending" for >5 minutes**
- Check if user completed OAuth flow in browser
- Check browser console for JavaScript errors
- Verify redirect URI configured correctly in OAuth app settings

**"Token Expired" (401 error)**
- For OAuth: Click "Reconnect" to get new token via refresh_token
- For API Key: Paste new key in connection settings

**"Rate Limit Exceeded"**
- Wait 1 minute before next request
- Check Connections → View Logs to see usage
- Consider reducing sync frequency

**"Health Check Failed"**
- Service may be temporarily down
- Check service status page (notion.com, api.catchr.io, etc.)
- Try clicking "Test Connection" manually
- If persists, disconnect & reconnect

**"Webhook Not Received"**
- Verify webhook endpoint is publicly accessible
- Check Webhook Logs in Connections Manager
- Verify signature validation not rejecting valid webhooks
- Re-register webhook in external service settings

---

## ROADMAP

**Phase 1 (Current):** Notion, Catchr, Frame.io, Ads Society, Netlify
**Phase 2:** Slack, Google Analytics, Google Ads, Meta Ads
**Phase 3:** Vercel, Cloudflare, custom webhook integrations, API marketplace
**Phase 4:** SSO for GrowthCRO users, advanced permission model

---

## REFERENCES

- See `integrations_spec.md` for detailed API specifications
- See `memory.md` for connection state & context management
- Supabase docs: https://supabase.com/docs
- Notion API: https://developers.notion.com
- Catchr API: https://docs.catchr.io
- Frame.io API: https://developer.frame.io
- Netlify API: https://docs.netlify.com/api/get-started
