# Integrations Specification - Detailed API Reference

**Version:** 1.0.0
**Last Updated:** 2026-04-05
**Audience:** Developers integrating with Connections Manager

---

## TABLE OF CONTENTS

1. [Notion API Spec](#notion-api-spec)
2. [Catchr API Spec](#catchr-api-spec)
3. [Frame.io API Spec](#frameio-api-spec)
4. [Ads Society API Spec](#ads-society-api-spec)
5. [Netlify API Spec](#netlify-api-spec)
6. [Error Code Reference](#error-code-reference)
7. [Webhook Specifications](#webhook-specifications)

---

## NOTION API SPEC

### OAuth 2.0 Setup

**Client Registration:**
```
Application Name: GrowthCRO
Redirect URIs: https://growthcro.internal/auth/notion/callback
Capabilities Required:
  ✓ Read
  ✓ Update
  ✓ Insert
  ✓ Create
```

**OAuth Flow:**

```bash
# Step 1: Redirect user to authorization endpoint
https://api.notion.com/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&owner=user

# Step 2: User logs in and grants permissions on Notion
# Notion redirects to:
https://growthcro.internal/auth/notion/callback?code=<CODE>&state=<STATE>

# Step 3: Exchange code for access token (backend)
POST https://api.notion.com/v1/oauth/token
Content-Type: application/json
{
  "grant_type": "authorization_code",
  "code": "<CODE>",
  "redirect_uri": "https://growthcro.internal/auth/notion/callback",
  "client_id": "<CLIENT_ID>",
  "client_secret": "<CLIENT_SECRET>"
}

# Response:
{
  "access_token": "secret_...",
  "token_type": "bearer",
  "bot_id": "bot_...",
  "workspace_id": "...",
  "workspace_name": "My Workspace",
  "workspace_icon": "https://...",
  "owner": {
    "type": "user",
    "user": {
      "id": "user_...",
      "object": "user",
      "name": "User Name",
      "avatar_url": "https://..."
    }
  }
}
```

### API Endpoints

#### Get Current User/Bot
```
GET https://api.notion.com/v1/users/me
Headers:
  Authorization: Bearer secret_...
  Notion-Version: 2022-06-28

Response 200:
{
  "object": "user",
  "id": "bot_...",
  "type": "bot",
  "bot": {
    "owner": {
      "type": "workspace"
    }
  }
}
```

#### Query Database
```
POST https://api.notion.com/v1/databases/{database_id}/query
Headers:
  Authorization: Bearer secret_...
  Content-Type: application/json
  Notion-Version: 2022-06-28

Body:
{
  "filter": {
    "property": "Status",
    "select": {
      "equals": "Active"
    }
  },
  "sorts": [
    {
      "property": "Created Time",
      "direction": "descending"
    }
  ],
  "page_size": 100,
  "start_cursor": null
}

Response 200:
{
  "object": "list",
  "results": [
    {
      "object": "page",
      "id": "page_...",
      "created_time": "2026-04-01T10:00:00.000Z",
      "last_edited_time": "2026-04-05T14:30:00.000Z",
      "properties": {
        "Name": {
          "id": "title",
          "type": "title",
          "title": [
            {
              "type": "text",
              "text": { "content": "A/B Test - CTA Color" }
            }
          ]
        },
        "Status": {
          "id": "abc",
          "type": "select",
          "select": { "name": "Active", "color": "green" }
        },
        "CVR Lift": {
          "id": "def",
          "type": "number",
          "number": 0.125
        }
      }
    }
  ],
  "next_cursor": "abc123",
  "has_more": true
}
```

#### Get Database
```
GET https://api.notion.com/v1/databases/{database_id}
Headers:
  Authorization: Bearer secret_...
  Notion-Version: 2022-06-28

Response 200:
{
  "object": "database",
  "id": "database_id",
  "created_time": "2026-01-01T00:00:00.000Z",
  "last_edited_time": "2026-04-05T10:00:00.000Z",
  "title": [
    {
      "type": "text",
      "text": { "content": "CRO Strategies" }
    }
  ],
  "properties": {
    "Name": {
      "id": "title",
      "name": "Name",
      "type": "title"
    },
    "Status": {
      "id": "status",
      "name": "Status",
      "type": "select",
      "select": {
        "options": [
          { "id": "1", "name": "Draft", "color": "blue" },
          { "id": "2", "name": "Active", "color": "green" },
          { "id": "3", "name": "Paused", "color": "yellow" },
          { "id": "4", "name": "Archived", "color": "gray" }
        ]
      }
    },
    "CVR Lift": {
      "id": "number",
      "name": "CVR Lift",
      "type": "number",
      "number": { "format": "percent" }
    }
  }
}
```

#### Get Page
```
GET https://api.notion.com/v1/pages/{page_id}
Headers:
  Authorization: Bearer secret_...
  Notion-Version: 2022-06-28

Response 200:
{
  "object": "page",
  "id": "page_id",
  "parent": {
    "type": "database_id",
    "database_id": "database_id"
  },
  "properties": {
    "Name": { "type": "title", "title": [ ... ] },
    "Status": { "type": "select", "select": { "name": "Active" } }
  }
}
```

#### Get Block Children
```
GET https://api.notion.com/v1/blocks/{block_id}/children
Headers:
  Authorization: Bearer secret_...
  Notion-Version: 2022-06-28

Query Params:
  page_size: 100
  start_cursor: (optional)

Response 200:
{
  "object": "list",
  "results": [
    {
      "object": "block",
      "id": "block_...",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          {
            "type": "text",
            "text": { "content": "This is a paragraph" }
          }
        ]
      }
    },
    {
      "object": "block",
      "id": "block_...",
      "type": "heading_2",
      "heading_2": {
        "rich_text": [
          {
            "type": "text",
            "text": { "content": "Section Title" }
          }
        ]
      }
    }
  ],
  "has_more": false
}
```

#### Create Page
```
POST https://api.notion.com/v1/pages
Headers:
  Authorization: Bearer secret_...
  Content-Type: application/json
  Notion-Version: 2022-06-28

Body:
{
  "parent": {
    "type": "database_id",
    "database_id": "database_id"
  },
  "properties": {
    "Name": {
      "title": [
        {
          "type": "text",
          "text": { "content": "New Test Result" }
        }
      ]
    },
    "Status": {
      "select": { "name": "Completed" }
    },
    "CVR Lift": {
      "number": 0.25
    }
  },
  "children": [
    {
      "object": "block",
      "type": "heading_1",
      "heading_1": {
        "rich_text": [
          { "type": "text", "text": { "content": "Test Results" } }
        ]
      }
    },
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          { "type": "text", "text": { "content": "This test showed a 25% CVR lift..." } }
        ]
      }
    }
  ]
}

Response 200:
{
  "object": "page",
  "id": "page_...",
  "created_time": "2026-04-05T14:30:00.000Z",
  "last_edited_time": "2026-04-05T14:30:00.000Z",
  "properties": { ... }
}
```

#### Update Page Properties
```
PATCH https://api.notion.com/v1/pages/{page_id}
Headers:
  Authorization: Bearer secret_...
  Content-Type: application/json
  Notion-Version: 2022-06-28

Body:
{
  "properties": {
    "Status": {
      "select": { "name": "Completed" }
    },
    "CVR Lift": {
      "number": 0.25
    }
  }
}

Response 200:
{
  "object": "page",
  "id": "page_id",
  "properties": { ... }
}
```

#### Append Block Children
```
PATCH https://api.notion.com/v1/blocks/{block_id}/children
Headers:
  Authorization: Bearer secret_...
  Content-Type: application/json
  Notion-Version: 2022-06-28

Body:
{
  "children": [
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          { "type": "text", "text": { "content": "New insight..." } }
        ]
      }
    }
  ]
}

Response 200:
{
  "object": "block",
  "id": "block_id",
  "children": [...]
}
```

### Rate Limits
- **Limit:** 3 requests/second (per integration token)
- **Burst:** Up to 100 requests/minute
- **Quota:** 100,000 requests/month (soft limit)
- **Response header:** `RateLimit-Remaining`, `RateLimit-Reset`

### Error Codes

| Code | Meaning | Action |
|---|---|---|
| 400 | Invalid request | Fix request body, retry |
| 401 | Unauthorized | Token expired/invalid, reconnect |
| 403 | Forbidden | Workspace access revoked, reconnect |
| 404 | Not found | Page/database deleted, skip |
| 409 | Conflict | Version mismatch, retry with updated version |
| 429 | Rate limited | Wait 60s, then retry |
| 500 | Service error | Retry after 5min |

---

## CATCHR API SPEC

### Authentication

**API Key Header:**
```
Authorization: Bearer cat_prod_xyz...
```

### Endpoints

#### Health Check
```
GET https://api.catchr.io/v2/health
Headers:
  Authorization: Bearer cat_prod_xyz...

Response 200:
{
  "status": "operational",
  "uptime_percent": 99.95,
  "services": {
    "google_analytics": "operational",
    "meta_ads": "operational",
    "tiktok_ads": "operational",
    "shopify": "operational"
  }
}
```

#### List Connected Sources
```
GET https://api.catchr.io/v2/sources
Headers:
  Authorization: Bearer cat_prod_xyz...

Response 200:
{
  "sources": [
    {
      "id": "ga4_prop_123456",
      "type": "google_analytics_4",
      "name": "Website GA4",
      "status": "connected",
      "last_synced": "2026-04-05T10:30:00Z",
      "metrics": ["users", "sessions", "conversions", "revenue"]
    },
    {
      "id": "meta_ads_acct_xyz",
      "type": "meta_ads",
      "name": "Meta Business Account",
      "status": "pending_authorization", // user must re-auth
      "error": "Token expired"
    }
  ]
}
```

#### Get Source Status
```
GET https://api.catchr.io/v2/sources/{source_id}/status
Headers:
  Authorization: Bearer cat_prod_xyz...

Response 200:
{
  "id": "ga4_prop_123456",
  "type": "google_analytics_4",
  "status": "connected",
  "authorized_at": "2026-01-01T10:00:00Z",
  "last_synced": "2026-04-05T10:30:00Z",
  "next_sync": "2026-04-05T11:00:00Z",
  "error": null
}

Response 401/403:
{
  "error": "source_unauthorized",
  "message": "Authorization expired or revoked for this source"
}
```

#### Get Metric Data
```
GET https://api.catchr.io/v2/metrics/{metric_key}
Headers:
  Authorization: Bearer cat_prod_xyz...

Query Params:
  start_date: 2026-04-01 (ISO 8601 date)
  end_date: 2026-04-05
  breakdown: campaign|platform|source|medium (optional)
  sources: ga4_prop_123456,meta_ads_acct_xyz (comma-separated, optional)
  compare_period: previous_period|year_over_year (optional)

Examples:
  /metrics/conversion_rate
  /metrics/conversion_rate?breakdown=platform
  /metrics/conversion_rate?start_date=2026-04-01&end_date=2026-04-05&breakdown=campaign&sources=meta_ads_acct_xyz
  /metrics/revenue?breakdown=source&compare_period=previous_period

Metric Keys Available:
  - conversion_rate (%)
  - cost_per_acquisition ($ or currency)
  - return_on_ad_spend (%)
  - return_on_investment (%)
  - click_through_rate (%)
  - impression_share (%)
  - average_order_value ($)
  - customer_lifetime_value ($)
  - revenue ($)
  - profit ($)
  - margin (%)
  - cost ($ or currency)
  - impressions
  - clicks
  - conversions
  - users
  - sessions
  - bounce_rate (%)
  - avg_session_duration (seconds)

Response 200:
{
  "metric": "conversion_rate",
  "data": [
    {
      "date": "2026-04-01",
      "value": 0.035, // 3.5%
      "confidence_interval": [0.033, 0.037]
    },
    {
      "date": "2026-04-02",
      "value": 0.038,
      "confidence_interval": [0.036, 0.040]
    }
  ],
  "summary": {
    "period": "2026-04-01 to 2026-04-05",
    "avg": 0.0365,
    "min": 0.032,
    "max": 0.041,
    "trend": "up" // or "down", "stable"
  }
}

// With breakdown
{
  "metric": "conversion_rate",
  "breakdown": "platform",
  "data": {
    "google_ads": [
      { "date": "2026-04-01", "value": 0.042 },
      { "date": "2026-04-02", "value": 0.045 }
    ],
    "meta_ads": [
      { "date": "2026-04-01", "value": 0.028 },
      { "date": "2026-04-02", "value": 0.031 }
    ],
    "tiktok_ads": [
      { "date": "2026-04-01", "value": 0.022 },
      { "date": "2026-04-02", "value": 0.025 }
    ]
  },
  "summary": { ... }
}

// With comparison
{
  "metric": "conversion_rate",
  "comparison": "previous_period",
  "data": [
    {
      "date": "2026-04-01",
      "current": 0.035,
      "previous": 0.032,
      "change_pct": 9.4 // (0.035 - 0.032) / 0.032 * 100
    }
  ],
  "summary": {
    "current_avg": 0.0365,
    "previous_avg": 0.0342,
    "change_pct": 6.7
  }
}
```

#### Get Attribution Data
```
GET https://api.catchr.io/v2/attributions
Headers:
  Authorization: Bearer cat_prod_xyz...

Query Params:
  start_date: 2026-04-01
  end_date: 2026-04-05
  model: first_touch|last_touch|linear|time_decay|position_based (default: last_touch)
  sources: (optional, comma-separated)

Response 200:
{
  "model": "time_decay",
  "period": "2026-04-01 to 2026-04-05",
  "conversions_total": 12345,
  "by_source": {
    "google_ads": {
      "attributed_conversions": 4560,
      "percentage": 37.0,
      "revenue": 68400
    },
    "meta_ads": {
      "attributed_conversions": 3704,
      "percentage": 30.0,
      "revenue": 55560
    },
    "organic": {
      "attributed_conversions": 2469,
      "percentage": 20.0,
      "revenue": 37035
    },
    "direct": {
      "attributed_conversions": 1232,
      "percentage": 10.0,
      "revenue": 18480
    }
  },
  "by_channel": {
    "paid_search": {
      "attributed_conversions": 6172,
      "percentage": 50.0
    },
    "social": {
      "attributed_conversions": 3704,
      "percentage": 30.0
    },
    "organic": {
      "attributed_conversions": 2469,
      "percentage": 20.0
    }
  }
}
```

### Rate Limits
- **Limit:** 60 requests/minute
- **Burst:** Up to 10 requests/second
- **Response headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Error Codes

| Code | Meaning | Action |
|---|---|---|
| 400 | Invalid metric/date range | Review query params |
| 401 | API key invalid/expired | Update API key |
| 429 | Rate limited | Wait 60s, retry |
| 503 | Service unavailable | Retry after 5min |

---

## FRAME.IO API SPEC

### OAuth 2.0 Setup

**Authorization Endpoint:**
```
https://frameio.com/oauth/authorize?
  client_id=<CLIENT_ID>&
  response_type=code&
  redirect_uri=https://growthcro.internal/auth/frameio/callback&
  scope=default&
  state=<STATE>
```

**Token Exchange:**
```
POST https://api.frame.io/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=<CODE>&
client_id=<CLIENT_ID>&
client_secret=<CLIENT_SECRET>&
redirect_uri=https://growthcro.internal/auth/frameio/callback

Response:
{
  "access_token": "fio_xyz...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "fio_refresh_xyz...",
  "scope": "default"
}
```

### Endpoints

#### Get Current User
```
GET https://api.frame.io/v2/me
Headers:
  Authorization: Bearer fio_xyz...

Response 200:
{
  "id": "user_xyz",
  "name": "John Doe",
  "email": "john@example.com",
  "account": {
    "id": "account_xyz",
    "name": "Growth Society"
  }
}
```

#### List Projects
```
GET https://api.frame.io/v2/projects
Headers:
  Authorization: Bearer fio_xyz...

Query Params:
  account_id: (required, from /me response)

Response 200:
{
  "results": [
    {
      "id": "proj_xyz",
      "name": "Brand Assets 2026",
      "created_at": "2026-01-01T10:00:00Z",
      "updated_at": "2026-04-05T10:30:00Z",
      "team": {
        "id": "team_xyz",
        "name": "Growth Team"
      }
    }
  ]
}
```

#### Get Project
```
GET https://api.frame.io/v2/projects/{project_id}
Headers:
  Authorization: Bearer fio_xyz...

Response 200:
{
  "id": "proj_xyz",
  "name": "Brand Assets 2026",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-04-05T10:30:00Z",
  "team": { "id": "team_xyz", "name": "Growth Team" },
  "members": [
    {
      "id": "member_xyz",
      "user": { "name": "John Doe", "email": "john@example.com" },
      "role": "owner"
    }
  ]
}
```

#### List Assets
```
GET https://api.frame.io/v2/assets
Headers:
  Authorization: Bearer fio_xyz...

Query Params:
  project_id: proj_xyz (required)
  include: comments,versions (optional)

Response 200:
{
  "results": [
    {
      "id": "asset_xyz",
      "name": "Homepage Mockup v3.mp4",
      "type": "file", // or "folder"
      "file_type": "video/mp4",
      "filesize": 524288000,
      "duration": 45.5,
      "width": 1920,
      "height": 1080,
      "created_at": "2026-04-01T10:00:00Z",
      "updated_at": "2026-04-05T10:30:00Z",
      "versions": [
        {
          "id": "ver_xyz1",
          "name": "v1",
          "created_at": "2026-04-01T10:00:00Z",
          "created_by": { "name": "Jane Doe" }
        },
        {
          "id": "ver_xyz3",
          "name": "v3",
          "created_at": "2026-04-05T10:30:00Z",
          "created_by": { "name": "John Doe" }
        }
      ],
      "comments_count": 5
    }
  ]
}
```

#### Get Asset
```
GET https://api.frame.io/v2/assets/{asset_id}
Headers:
  Authorization: Bearer fio_xyz...

Response 200:
{
  "id": "asset_xyz",
  "name": "Homepage Mockup v3.mp4",
  "type": "file",
  "file_type": "video/mp4",
  "filesize": 524288000,
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-05T10:30:00Z"
}
```

#### Create Project
```
POST https://api.frame.io/v2/projects
Headers:
  Authorization: Bearer fio_xyz...
  Content-Type: application/json

Body:
{
  "name": "GrowthCRO Test Creatives",
  "team_id": "team_xyz"
}

Response 201:
{
  "id": "proj_new_xyz",
  "name": "GrowthCRO Test Creatives",
  "created_at": "2026-04-05T14:30:00Z"
}
```

#### Upload Asset
```
POST https://api.frame.io/v2/assets
Headers:
  Authorization: Bearer fio_xyz...
  Content-Type: multipart/form-data

Form Fields:
  project_id: proj_xyz
  file: <binary file data>
  name: Homepage Mockup.mp4

Response 201:
{
  "id": "asset_new_xyz",
  "name": "Homepage Mockup.mp4",
  "status": "uploading", // or "processing", "ready"
  "created_at": "2026-04-05T14:30:00Z"
}
```

#### Get Comments
```
GET https://api.frame.io/v2/comments
Headers:
  Authorization: Bearer fio_xyz...

Query Params:
  asset_id: asset_xyz

Response 200:
{
  "results": [
    {
      "id": "comment_xyz",
      "text": "Love the new color scheme!",
      "created_by": { "name": "Jane Doe", "email": "jane@example.com" },
      "created_at": "2026-04-05T10:00:00Z",
      "timestamp": 45.5 // for videos, comment timestamp
    }
  ]
}
```

### Rate Limits
- **Limit:** 1000 requests/hour
- **Response headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`

### Error Codes

| Code | Meaning | Action |
|---|---|---|
| 401 | Unauthorized | Refresh token, reconnect |
| 404 | Not found | Project/asset deleted, skip |
| 429 | Rate limited | Wait and retry |
| 503 | Service unavailable | Retry after 5min |

---

## ADS SOCIETY API SPEC

### Authentication

**Bearer Token Header:**
```
Authorization: Bearer ads_soc_prod_xyz...
```

### Endpoints

#### Health Check
```
GET https://api.ads-society.internal/v1/health
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Response 200:
{
  "status": "operational"
}
```

#### List Campaigns
```
GET https://api.ads-society.internal/v1/campaigns
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Query Params:
  account_id: ads_acct_xyz (optional, defaults to authenticated account)
  status: draft|active|paused|archived (optional, comma-separated)
  limit: 100 (default)
  offset: 0

Response 200:
{
  "campaigns": [
    {
      "id": "camp_xyz1",
      "name": "Homepage CTA Test - March 2026",
      "account_id": "ads_acct_xyz",
      "status": "active",
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-04-05T10:30:00Z",
      "budget": 5000,
      "spend": 3245.67,
      "impressions": 145230,
      "clicks": 2840,
      "conversions": 145,
      "ctr": 0.0196,
      "cpc": 1.14,
      "cpa": 22.39,
      "roas": 2.15
    },
    {
      "id": "camp_xyz2",
      "name": "Product Page Copy Test - April 2026",
      "account_id": "ads_acct_xyz",
      "status": "draft",
      "created_at": "2026-04-01T10:00:00Z",
      "budget": 3000,
      "spend": 0
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

#### Get Campaign
```
GET https://api.ads-society.internal/v1/campaigns/{campaign_id}
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Response 200:
{
  "id": "camp_xyz1",
  "name": "Homepage CTA Test - March 2026",
  "status": "active",
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-04-05T10:30:00Z",
  "budget": {
    "total": 5000,
    "daily": 50
  },
  "targeting": {
    "platforms": ["meta", "google"],
    "locations": ["US", "CA"],
    "age_range": "25-54",
    "interests": ["technology", "business"]
  },
  "performance": {
    "impressions": 145230,
    "clicks": 2840,
    "conversions": 145,
    "spend": 3245.67,
    "revenue": 6991.25,
    "ctr": 0.0196,
    "cpc": 1.14,
    "cpa": 22.39,
    "roas": 2.15
  },
  "variants": [
    {
      "id": "var_xyz_control",
      "name": "Control - Original CTA",
      "type": "control",
      "impressions": 72615,
      "conversions": 65,
      "ctr": 0.0189,
      "cpa": 25.12
    },
    {
      "id": "var_xyz_challenger",
      "name": "Challenger - New CTA",
      "type": "challenger",
      "impressions": 72615,
      "conversions": 80,
      "ctr": 0.0203,
      "cpa": 20.29
    }
  ]
}
```

#### Get Metrics
```
GET https://api.ads-society.internal/v1/campaigns/{campaign_id}/metrics
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Query Params:
  start_date: 2026-04-01 (ISO date)
  end_date: 2026-04-05
  group_by: day|week|campaign (default: day)

Response 200:
{
  "campaign_id": "camp_xyz1",
  "metrics": [
    {
      "date": "2026-04-01",
      "impressions": 23450,
      "clicks": 460,
      "conversions": 24,
      "spend": 525.60,
      "revenue": 576.00,
      "ctr": 0.0196,
      "cpa": 21.90,
      "roas": 1.10
    },
    {
      "date": "2026-04-02",
      "impressions": 24120,
      "clicks": 480,
      "conversions": 26,
      "spend": 547.20,
      "revenue": 624.00,
      "ctr": 0.0199,
      "cpa": 21.05,
      "roas": 1.14
    }
  ]
}
```

#### List Creatives
```
GET https://api.ads-society.internal/v1/creatives
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Query Params:
  account_id: ads_acct_xyz
  campaign_id: camp_xyz1 (optional)
  type: image|video|carousel (optional)

Response 200:
{
  "creatives": [
    {
      "id": "cre_xyz1",
      "campaign_id": "camp_xyz1",
      "name": "Homepage Banner - Control v1",
      "type": "image",
      "url": "https://assets.ads-society.internal/cre_xyz1.jpg",
      "copy": "Discover Growth Strategies That Drive Results",
      "cta": "Learn More",
      "created_at": "2026-03-01T10:00:00Z"
    },
    {
      "id": "cre_xyz2",
      "campaign_id": "camp_xyz1",
      "name": "Homepage Banner - Challenger v1",
      "type": "image",
      "url": "https://assets.ads-society.internal/cre_xyz2.jpg",
      "copy": "Transform Your CRO Strategy in 30 Days",
      "cta": "Start Free Trial",
      "created_at": "2026-03-15T10:00:00Z"
    }
  ]
}
```

#### List Audiences
```
GET https://api.ads-society.internal/v1/audiences
Headers:
  Authorization: Bearer ads_soc_prod_xyz...

Query Params:
  account_id: ads_acct_xyz

Response 200:
{
  "audiences": [
    {
      "id": "aud_xyz1",
      "name": "High-Value Customers (LTV > $5k)",
      "type": "custom", // or "lookalike", "interest"
      "size": 12450,
      "created_at": "2026-02-01T10:00:00Z"
    }
  ]
}
```

### Rate Limits
- **Limit:** 100 requests/second
- **Burst:** 500 requests/second

### Error Codes

| Code | Meaning | Action |
|---|---|---|
| 400 | Invalid params | Review request |
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check permissions |
| 429 | Rate limited | Exponential backoff |
| 500 | Server error | Retry after 5min |

---

## NETLIFY API SPEC

### Authentication

**Personal Access Token:**
```
Authorization: Bearer nf_xyz...
```

### Endpoints

#### Get Current User
```
GET https://api.netlify.com/api/v1/user
Headers:
  Authorization: Bearer nf_xyz...

Response 200:
{
  "id": "user_xyz",
  "email": "user@example.com",
  "full_name": "User Name"
}
```

#### List Sites
```
GET https://api.netlify.com/api/v1/sites
Headers:
  Authorization: Bearer nf_xyz...

Query Params:
  filter: all|owned|collaborator (default: all)
  name: (optional, search by name)
  limit: 30

Response 200:
{
  "sites": [
    {
      "id": "site_xyz1",
      "name": "growthcro-test-abc123",
      "url": "https://growthcro-test-abc123.netlify.app",
      "custom_domain": "test.growthcro.internal",
      "created_at": "2026-04-01T10:00:00Z",
      "updated_at": "2026-04-05T10:30:00Z",
      "state": "ready", // or "building", "error"
      "build": {
        "id": "deploy_xyz1",
        "state": "ready",
        "created_at": "2026-04-05T10:30:00Z"
      }
    }
  ]
}
```

#### Create Site
```
POST https://api.netlify.com/api/v1/sites
Headers:
  Authorization: Bearer nf_xyz...
  Content-Type: application/json

Body:
{
  "name": "growthcro-test-abc123",
  "custom_domain": "test.growthcro.internal"
}

Response 201:
{
  "id": "site_xyz_new",
  "name": "growthcro-test-abc123",
  "url": "https://growthcro-test-abc123.netlify.app",
  "state": "new"
}
```

#### Create Deploy
```
POST https://api.netlify.com/api/v1/sites/{site_id}/deploys
Headers:
  Authorization: Bearer nf_xyz...
  Content-Type: application/json

Body:
{
  "files": {
    "index.html": "<html>...</html>",
    "styles.css": "body { ... }",
    "script.js": "// code"
  }
}

Response 201:
{
  "id": "deploy_xyz_new",
  "site_id": "site_xyz_new",
  "url": "https://deploy_abc.netlify.app",
  "state": "uploading", // or "building", "ready", "error"
  "created_at": "2026-04-05T14:30:00Z",
  "updated_at": "2026-04-05T14:31:00Z"
}
```

#### Get Deploy Status
```
GET https://api.netlify.com/api/v1/sites/{site_id}/deploys/{deploy_id}
Headers:
  Authorization: Bearer nf_xyz...

Response 200:
{
  "id": "deploy_xyz_new",
  "state": "ready",
  "url": "https://growthcro-test-abc123.netlify.app",
  "published_at": "2026-04-05T14:31:00Z"
}
```

#### Update Site
```
PATCH https://api.netlify.com/api/v1/sites/{site_id}
Headers:
  Authorization: Bearer nf_xyz...
  Content-Type: application/json

Body:
{
  "name": "growthcro-test-v2",
  "custom_domain": "test-v2.growthcro.internal"
}

Response 200:
{
  "id": "site_xyz",
  "name": "growthcro-test-v2",
  "custom_domain": "test-v2.growthcro.internal"
}
```

### Rate Limits
- **Limit:** 200 requests/minute
- **Response headers:** `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`

### Error Codes

| Code | Meaning | Action |
|---|---|---|
| 401 | Unauthorized | Check token |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Site doesn't exist |
| 422 | Invalid params | Review request |
| 500 | Service error | Retry after 5min |

---

## ERROR CODE REFERENCE

### HTTP Status Codes

| Code | Category | Handling |
|---|---|---|
| 200-299 | Success | Continue |
| 400-499 | Client Error | Usually retriable after fix or manual action |
| 401 | Authentication Error | Reconnect/refresh token |
| 403 | Authorization Error | Check permissions, reconnect |
| 404 | Not Found | Skip/delete local reference |
| 429 | Rate Limit | Exponential backoff + queue |
| 500-599 | Server Error | Exponential backoff, retry after 5min |
| Timeout | Network Error | Exponential backoff |

### Common Error Responses

**Notion:**
```json
{
  "object": "error",
  "status": 400,
  "code": "invalid_request_body",
  "message": "Invalid request body"
}
```

**Catchr:**
```json
{
  "error": "invalid_metric",
  "message": "The metric 'unknown_metric' does not exist"
}
```

**Frame.io:**
```json
{
  "error": "unauthorized",
  "message": "You are not authorized to access this resource"
}
```

**Netlify:**
```json
{
  "code": 422,
  "message": "Name is invalid (too long)"
}
```

---

## WEBHOOK SPECIFICATIONS

### Notion Webhooks

**Supported Events:**
- `page.created`
- `page.updated`
- `database.created`
- `database.deleted`

**Signature Validation:**
```
Header: X-Notion-Signature
Format: HMAC-SHA256(request_body, webhook_secret)

Verification:
  computed_signature = hmac_sha256(raw_body, secret)
  timing_safe_compare(computed_signature, header_signature)
```

**Example Webhook Payload:**
```json
{
  "object": "event",
  "id": "evt_xyz",
  "created_timestamp": "2026-04-05T14:30:00.000Z",
  "type": "page.updated",
  "page": {
    "id": "page_id",
    "parent": {
      "type": "database_id",
      "database_id": "db_id"
    },
    "properties": {
      "Status": {
        "type": "select",
        "select": { "name": "Completed" }
      }
    }
  }
}
```

### Catchr Webhooks

**Supported Events:**
- `conversion.new`
- `conversion.updated`
- `metric.updated`
- `source.disconnected`

**Signature Validation:**
```
Header: X-Catchr-Signature
Format: HMAC-SHA256(request_body, webhook_secret)
```

**Example Payload:**
```json
{
  "event_id": "evt_xyz",
  "event_type": "conversion.new",
  "timestamp": "2026-04-05T14:30:00Z",
  "source": "meta_ads",
  "conversion": {
    "id": "conv_xyz",
    "value": 99.99,
    "currency": "USD"
  }
}
```

### Processing Requirements
- Validate signature BEFORE processing
- Idempotent processing (use event_id for deduplication)
- Return 200 OK within 30 seconds
- No side effects in validation; queue actual processing

---

**End of Integrations Specification**
