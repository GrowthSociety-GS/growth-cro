# Connections Manager - Memory & State

**Template for connection state & context management**

---

## CONNECTION STATE TRACKING

This file serves as a template for how the Connections Manager tracks the state of each integration in persistent memory.

### State Structure

```json
{
  "workspace_id": "uuid",
  "connections": {
    "notion": {
      "status": "connected|pending|error|disconnected",
      "status_code": "green|amber|red|grey",
      "last_validated": "2026-04-05T10:30:00Z",
      "last_error": null,
      "last_error_at": null,
      "consecutive_failures": 0,
      "config": {
        "workspace_id": "notion_workspace_xyz",
        "bot_id": "notion_bot_xyz",
        "workspace_name": "My Workspace"
      },
      "credentials": {
        "access_token": "secret_...", // encrypted in DB
        "expires_at": null
      },
      "usage": {
        "api_calls_today": 156,
        "rate_limit_remaining": 844,
        "rate_limit_reset": "2026-04-05T23:59:59Z"
      },
      "sync_status": {
        "last_pull": "2026-04-05T10:25:00Z",
        "last_push": "2026-04-05T10:20:00Z",
        "databases_synced": 3,
        "pages_synced": 127
      },
      "health_check": {
        "endpoint": "GET /users/me",
        "response_time_ms": 145,
        "status_code": 200
      }
    },
    "catchr": {
      "status": "connected",
      "status_code": "green",
      "last_validated": "2026-04-05T10:28:00Z",
      "config": {
        "workspace_id": "catchr_workspace_xyz"
      },
      "connected_platforms": [
        {
          "id": "google_analytics_4",
          "name": "Website GA4",
          "status": "connected",
          "last_synced": "2026-04-05T10:25:00Z"
        },
        {
          "id": "meta_ads",
          "name": "Meta Business",
          "status": "pending_authorization",
          "last_error": "Token expired - user must re-authorize"
        }
      ],
      "usage": {
        "api_calls_today": 234,
        "rate_limit_remaining": 1766,
        "rate_limit_reset": "2026-04-05T23:59:59Z"
      }
    },
    "frameio": {
      "status": "error",
      "status_code": "red",
      "last_validated": "2026-04-05T09:30:00Z",
      "last_error": "401 Unauthorized",
      "last_error_at": "2026-04-05T09:30:00Z",
      "consecutive_failures": 3,
      "config": {
        "user_id": "frameio_user_xyz"
      },
      "health_check": {
        "endpoint": "GET /v2/me",
        "response_time_ms": 0,
        "status_code": 401
      }
    }
  }
}
```

---

## CONTEXT CACHE

### Notion Data Cache

```json
{
  "notion_databases": {
    "cro_strategies_db_id": {
      "name": "CRO Strategies",
      "updated_at": "2026-04-05T10:25:00Z",
      "ttl": 3600000,
      "properties": {
        "Name": { "type": "title" },
        "Status": { "type": "select", "options": ["Draft", "Active", "Paused", "Archived"] },
        "CVR Lift": { "type": "number", "format": "percent" }
      }
    }
  },
  "notion_pages": {
    "page_id_xyz": {
      "title": "A/B Test - CTA Color",
      "database": "cro_strategies_db_id",
      "updated_at": "2026-04-05T10:20:00Z",
      "ttl": 1800000,
      "content_hash": "abc123def456" // for detecting changes
    }
  }
}
```

### Catchr Metrics Cache

```json
{
  "catchr_metrics": {
    "conversion_rate_2026-04-01_2026-04-05": {
      "metric": "conversion_rate",
      "date_range": ["2026-04-01", "2026-04-05"],
      "data": [ /* metric values */ ],
      "cached_at": "2026-04-05T10:25:00Z",
      "ttl": 300000 // 5 min
    }
  }
}
```

---

## OPERATIONAL STATE

### Rate Limiting

```json
{
  "rate_limits": {
    "notion": {
      "tokens_available": 245,
      "last_refill": "2026-04-05T10:29:30Z",
      "capacity": 3,
      "refill_rate_per_second": 3,
      "burst_capacity": 100
    },
    "catchr": {
      "tokens_available": 58,
      "last_refill": "2026-04-05T10:29:00Z",
      "capacity": 60,
      "refill_rate_per_minute": 60
    }
  }
}
```

### Request Queue

```json
{
  "queued_requests": [
    {
      "id": "req_xyz1",
      "integration": "notion",
      "endpoint": "GET /databases/db_id/query",
      "timestamp": "2026-04-05T10:30:15Z",
      "retry_count": 0,
      "max_retries": 3,
      "status": "pending"
    },
    {
      "id": "req_xyz2",
      "integration": "catchr",
      "endpoint": "GET /metrics/conversion_rate",
      "timestamp": "2026-04-05T10:30:20Z",
      "retry_count": 1,
      "max_retries": 3,
      "status": "pending"
    }
  ]
}
```

### Webhook Inbox

```json
{
  "webhooks_received": [
    {
      "id": "wh_xyz1",
      "integration": "notion",
      "event_type": "page.updated",
      "timestamp": "2026-04-05T10:30:00Z",
      "signature_valid": true,
      "status": "processing",
      "payload": { /* webhook data */ }
    }
  ]
}
```

---

## ANALYTICS & OBSERVABILITY

### Connection Health History

```json
{
  "health_checks": [
    {
      "timestamp": "2026-04-05T10:30:00Z",
      "integration": "notion",
      "status": "healthy",
      "response_time_ms": 145,
      "endpoint_tested": "GET /users/me"
    },
    {
      "timestamp": "2026-04-05T10:25:00Z",
      "integration": "notion",
      "status": "healthy",
      "response_time_ms": 132,
      "endpoint_tested": "GET /users/me"
    }
  ]
}
```

### API Usage Analytics

```json
{
  "api_usage": {
    "notion": {
      "calls_today": 156,
      "calls_this_hour": 24,
      "error_rate": 0.02,
      "avg_response_time_ms": 142,
      "breakdown": {
        "GET /databases/{id}/query": 45,
        "PATCH /pages/{id}": 32,
        "GET /pages/{id}": 28,
        "POST /pages": 12,
        "other": 39
      }
    }
  }
}
```

---

## SECURITY & AUDIT

### Recent Operations Log

```json
{
  "audit_log": [
    {
      "timestamp": "2026-04-05T14:30:00Z",
      "user_id": "user_xyz",
      "action": "connect",
      "integration": "notion",
      "status": "success",
      "ip_address": "192.168.1.1"
    },
    {
      "timestamp": "2026-04-05T14:25:00Z",
      "user_id": "user_xyz",
      "action": "test_connection",
      "integration": "catchr",
      "status": "success",
      "ip_address": "192.168.1.1"
    },
    {
      "timestamp": "2026-04-05T14:20:00Z",
      "user_id": "user_abc",
      "action": "disconnect",
      "integration": "frameio",
      "status": "success",
      "ip_address": "192.168.1.2"
    }
  ]
}
```

### Credential Rotation History

```json
{
  "credential_rotations": {
    "netlify": {
      "last_rotated": "2026-04-01T10:00:00Z",
      "rotated_by": "user_xyz",
      "schedule": "monthly", // or "on_demand"
      "next_rotation_due": "2026-05-01T10:00:00Z"
    }
  }
}
```

---

## SYSTEM STATE DURING OPERATIONS

### During OAuth Flow

```json
{
  "oauth_sessions": {
    "session_xyz": {
      "integration": "notion",
      "state": "awaiting_callback",
      "initiated_at": "2026-04-05T14:30:00Z",
      "expires_at": "2026-04-05T14:35:00Z",
      "workspace_id": "workspace_xyz",
      "user_id": "user_xyz"
    }
  }
}
```

### During Deployment

```json
{
  "deployments_in_progress": [
    {
      "id": "deploy_xyz1",
      "integration": "netlify",
      "site_name": "growthcro-test-abc123",
      "status": "deploying",
      "started_at": "2026-04-05T14:30:00Z",
      "files_count": 3,
      "uploaded_files": 2,
      "estimated_completion": "2026-04-05T14:31:30Z"
    }
  ]
}
```

---

## NOTIFICATION STATE

### Pending Alerts

```json
{
  "pending_alerts": [
    {
      "id": "alert_xyz1",
      "type": "connection_error",
      "integration": "frameio",
      "severity": "high",
      "message": "Frame.io connection has been down for 45 minutes",
      "triggered_at": "2026-04-05T10:15:00Z",
      "sent_to": null,
      "status": "pending_send"
    },
    {
      "id": "alert_xyz2",
      "type": "rate_limit_warning",
      "integration": "notion",
      "severity": "medium",
      "message": "Notion rate limit at 95% of capacity",
      "triggered_at": "2026-04-05T10:28:00Z",
      "sent_to": null,
      "status": "pending_send"
    }
  ]
}
```

---

## NOTES FOR IMPLEMENTATION

This memory structure should be:

1. **Persisted:** Store in Supabase (encrypted for sensitive data)
2. **Cached:** In-memory cache with Redis for fast access
3. **Real-time Updated:** Via webhooks and periodic health checks
4. **Queryable:** Support filtering by integration, status, time range
5. **Expirable:** TTLs for cached data (5min for metrics, 1h for config)
6. **Auditable:** Full history available for compliance/debugging

### Key Tables Needed

- `connections_state` — Current status of each integration
- `connections_health_check_log` — Historical health checks
- `connections_api_usage_log` — API call tracking
- `connections_audit_log` — User actions
- `connections_cache` — Cached external data (TTL-based)
- `webhooks_received` — Incoming webhooks (for replay if needed)

---

**This template documents the shape and content of connection state. Implement with your chosen persistence layer.**
