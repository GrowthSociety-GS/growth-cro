# Sync Protocol - Complete API Reference
## Notion ↔ GrowthCRO Bidirectional Synchronization

**Document Version:** 1.0.0
**Last Updated:** 2026-04-05
**Status:** Production Specification

---

## TABLE OF CONTENTS

1. [Notion API Authentication](#notion-api-authentication)
2. [Pull Protocol (Notion → GrowthCRO)](#pull-protocol-notion--growthcro)
3. [Push Protocol (GrowthCRO → Notion)](#push-protocol-growthcro--notion)
4. [Error Handling & Retry Logic](#error-handling--retry-logic)
5. [Webhook Event Processing](#webhook-event-processing)
6. [Conflict Resolution](#conflict-resolution)
7. [Rate Limiting & Performance](#rate-limiting--performance)
8. [Monitoring & Alerting](#monitoring--alerting)

---

## NOTION API AUTHENTICATION

### Setup

**1. Create Integration in Notion**

```
Notion Workspace Settings
→ Integrations
→ Create New Integration
→ Name: GrowthCRO Sync Engine
→ Capabilities: Read, Update, Insert
→ Copy Internal Integration Token
```

**2. Environment Configuration**

```bash
# .env file for GrowthCRO backend
NOTION_API_KEY=secret_xxx...
NOTION_API_VERSION=2024-02-15
NOTION_WORKSPACE_ID=abc123def456
NOTION_AI_INSIGHTS_DB_ID=db_xyz789...
NOTION_SYNC_LOG_DB_ID=db_log_...
```

**3. Share Integration with Target Databases**

In Notion: Each target database must have GrowthCRO integration granted access
- Click "Share" on database
- Find "GrowthCRO Sync Engine"
- Grant read/write access

### Request Headers (All API Calls)

```http
GET /v1/databases/{database_id}
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json
User-Agent: GrowthCRO/1.0
```

---

## PULL PROTOCOL (Notion → GrowthCRO)

### 1. Fetch Workspace Structure

**Endpoint:** `GET /v1/search`

**Purpose:** Discover all databases tagged for sync

```http
POST /v1/search
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json

{
  "query": "growth_crm",
  "sort": {
    "direction": "descending",
    "timestamp": "last_edited_time"
  }
}
```

**Response:**

```json
{
  "object": "list",
  "results": [
    {
      "object": "database",
      "id": "a1b2c3d4e5f6g7h8",
      "title": [{"plain_text": "CRO Templates"}],
      "parent": {"type": "workspace"},
      "last_edited_time": "2026-04-05T14:32:00Z",
      "icon": null,
      "cover": null,
      "properties": {
        "Name": {"id": "title", "type": "title", ...},
        "Category": {"id": "cat_", "type": "select", ...},
        "Last Updated": {"id": "update_", "type": "last_edited_time", ...}
      }
    },
    ...
  ],
  "next_cursor": null,
  "has_more": false
}
```

**Python Implementation:**

```python
from notion_client import Client

def fetch_workspace_structure():
    """
    Get all databases to sync.
    Tag: databases must have 'growth_crm' tag or be in a GrowthCRO folder.
    """

    client = Client(auth=NOTION_API_KEY)

    try:
        response = client.search(
            query='growth_crm',
            sort={
                'direction': 'descending',
                'timestamp': 'last_edited_time'
            },
            page_size=100
        )

        databases = [r for r in response['results']
                     if r['object'] == 'database']

        return {
            'success': True,
            'databases': databases,
            'count': len(databases),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        log_error(f'Fetch workspace structure failed: {e}')
        return {'success': False, 'error': str(e)}
```

### 2. Fetch Database Pages (with Delta Sync)

**Endpoint:** `POST /v1/databases/{database_id}/query`

**Purpose:** Get all pages + modifications since last sync

```http
POST /v1/databases/a1b2c3d4e5f6g7h8/query
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json

{
  "filter": {
    "property": "last_edited_time",
    "last_edited_time": {
      "after": "2026-04-05T10:00:00Z"
    }
  },
  "sorts": [
    {
      "property": "last_edited_time",
      "direction": "descending"
    }
  ],
  "page_size": 100,
  "start_cursor": null
}
```

**Response:**

```json
{
  "object": "list",
  "results": [
    {
      "object": "page",
      "id": "page_123",
      "created_time": "2026-03-15T08:00:00Z",
      "last_edited_time": "2026-04-05T14:30:00Z",
      "last_edited_by": {
        "object": "user",
        "id": "user_abc123"
      },
      "created_by": {
        "object": "user",
        "id": "user_xyz789"
      },
      "archived": false,
      "parent": {
        "type": "database_id",
        "database_id": "a1b2c3d4e5f6g7h8"
      },
      "properties": {
        "Name": {
          "id": "title",
          "type": "title",
          "title": [
            {
              "type": "text",
              "text": {
                "content": "Checkout Flow Best Practices",
                "link": null
              },
              "plain_text": "Checkout Flow Best Practices"
            }
          ]
        },
        "Category": {
          "id": "cat_select",
          "type": "select",
          "select": {
            "id": "option_1",
            "name": "Best Practice",
            "color": "blue"
          }
        },
        "Tags": {
          "id": "tags_multi",
          "type": "multi_select",
          "multi_select": [
            {"id": "tag_1", "name": "e-commerce", "color": "green"},
            {"id": "tag_2", "name": "friction", "color": "red"}
          ]
        }
      }
    }
  ],
  "next_cursor": "page_token_next_100",
  "has_more": true
}
```

**Python Implementation (with Pagination):**

```python
def fetch_database_pages_delta(database_id, last_sync_time=None):
    """
    Fetch pages modified since last sync (delta sync).
    Returns pages + pagination cursor for resuming.
    """

    client = Client(auth=NOTION_API_KEY)
    all_pages = []
    start_cursor = None

    if last_sync_time is None:
        last_sync_time = (datetime.now() - timedelta(hours=6)).isoformat()

    while True:
        try:
            response = client.databases.query(
                database_id=database_id,
                filter={
                    'property': 'last_edited_time',
                    'last_edited_time': {
                        'after': last_sync_time
                    }
                },
                sorts=[{
                    'property': 'last_edited_time',
                    'direction': 'descending'
                }],
                page_size=100,
                start_cursor=start_cursor
            )

            all_pages.extend(response['results'])

            if not response['has_more']:
                break

            start_cursor = response['next_cursor']

        except Exception as e:
            log_error(f'Fetch database pages failed: {e}')
            break

    return all_pages
```

### 3. Fetch Page Blocks (Full Content)

**Endpoint:** `GET /v1/blocks/{page_id}/children`

**Purpose:** Extract all text, code, tables from a page

```http
GET /v1/blocks/page_123/children
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json
```

**Response (Excerpt):**

```json
{
  "object": "list",
  "results": [
    {
      "object": "block",
      "id": "block_heading1",
      "type": "heading_1",
      "heading_1": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Checkout Friction Patterns",
              "link": null
            },
            "plain_text": "Checkout Friction Patterns"
          }
        ],
        "is_toggleable": false,
        "color": "default"
      }
    },
    {
      "object": "block",
      "id": "block_para1",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "High abandonment rates during payment step occur when:",
              "link": null
            }
          }
        ]
      }
    },
    {
      "object": "block",
      "id": "block_list1",
      "type": "bulleted_list_item",
      "bulleted_list_item": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Payment method options are unclear",
              "link": null
            }
          }
        ]
      }
    },
    {
      "object": "block",
      "id": "block_code1",
      "type": "code",
      "code": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "<button class=\"checkout-cta high-contrast\">Complete Purchase</button>",
              "link": null
            }
          }
        ],
        "language": "html",
        "caption": []
      }
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

**Python Block Extraction:**

```python
def extract_page_blocks(page_id):
    """
    Recursively fetch all blocks in a page, handling nested blocks.
    """

    client = Client(auth=NOTION_API_KEY)
    all_blocks = []
    start_cursor = None

    def fetch_block_recursively(parent_id, depth=0):
        """Helper to handle nested blocks (e.g., toggle lists)."""

        nonlocal start_cursor

        try:
            response = client.blocks.children.list(
                block_id=parent_id,
                page_size=100,
                start_cursor=start_cursor
            )

            for block in response['results']:

                # Convert Notion block to standardized format
                parsed_block = parse_notion_block(block, depth)
                all_blocks.append(parsed_block)

                # Recursively fetch children if this block has them
                if block['type'] in ['synced_block', 'toggle', 'column_list']:
                    fetch_block_recursively(block['id'], depth+1)

            if response['has_more']:
                start_cursor = response['next_cursor']
                fetch_block_recursively(parent_id, depth)

        except Exception as e:
            log_error(f'Extract blocks from {parent_id} failed: {e}')

    fetch_block_recursively(page_id)
    return all_blocks


def parse_notion_block(block, depth=0):
    """
    Parse Notion block into standardized format for chunking.
    Handles: paragraph, heading, code, table, divider, etc.
    """

    block_type = block['type']
    block_data = block.get(block_type, {})

    # Extract text from rich_text
    text_content = ''
    if 'rich_text' in block_data:
        text_content = ''.join([
            rt.get('plain_text', '') for rt in block_data['rich_text']
        ])

    # Special handling for code blocks
    if block_type == 'code':
        language = block_data.get('language', 'plaintext')
        caption = ''.join([rt.get('plain_text', '') for rt in block_data.get('caption', [])])
        text_content = f"```{language}\n{text_content}\n```"
        if caption:
            text_content += f"\n{caption}"

    # Special handling for tables
    elif block_type == 'table':
        table_rows = []
        # Note: Full table extraction requires additional API calls
        # For now, we'll fetch table data on demand
        text_content = f"[Table: {block_data.get('has_column_header', False)} columns]"

    return {
        'id': block['id'],
        'type': block_type,
        'text': text_content,
        'depth': depth,
        'metadata': {
            'is_toggleable': block_data.get('is_toggleable', False),
            'color': block_data.get('color', 'default'),
            'created_time': block.get('created_time'),
            'last_edited_time': block.get('last_edited_time')
        }
    }
```

### 4. Store Raw Notion Content

**Database Operation:**

```python
def store_notion_content_batch(pages_with_blocks):
    """
    Store fetched Notion content in raw form before processing.
    Uses batch insert for efficiency.
    """

    from psycopg2.extras import execute_values
    import psycopg2

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    rows = []

    for page in pages_with_blocks:

        content_record = {
            'page_id': page['id'],
            'workspace_id': NOTION_WORKSPACE_ID,
            'title': extract_title(page),
            'content_blocks': json.dumps(page['blocks']),
            'metadata': json.dumps({
                'created_time': page['created_time'],
                'last_edited_time': page['last_edited_time'],
                'created_by': page['created_by']['id'],
                'last_edited_by': page['last_edited_by']['id'],
                'properties': page['properties']
            }),
            'status': 'pending_index',
            'notion_created_time': page['created_time'],
            'notion_last_edited_time': page['last_edited_time']
        }

        rows.append((
            content_record['page_id'],
            content_record['workspace_id'],
            content_record['title'],
            content_record['content_blocks'],
            content_record['metadata'],
            content_record['status'],
            content_record['notion_created_time'],
            content_record['notion_last_edited_time']
        ))

    # Upsert: insert or update on conflict
    insert_query = """
        INSERT INTO notion_content_raw (
            page_id, workspace_id, title, content_blocks,
            metadata, status, notion_created_time, notion_last_edited_time
        ) VALUES %s
        ON CONFLICT (page_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            content_blocks = EXCLUDED.content_blocks,
            metadata = EXCLUDED.metadata,
            notion_last_edited_time = EXCLUDED.notion_last_edited_time,
            last_synced = CURRENT_TIMESTAMP
    """

    try:
        execute_values(cur, insert_query, rows)
        conn.commit()
        log_info(f'Stored {len(rows)} pages in notion_content_raw')
        return {'success': True, 'rows_inserted': len(rows)}

    except Exception as e:
        conn.rollback()
        log_error(f'Store notion content failed: {e}')
        return {'success': False, 'error': str(e)}

    finally:
        cur.close()
        conn.close()
```

---

## PUSH PROTOCOL (GrowthCRO → Notion)

### 1. Create Page in AI Insights Database

**Endpoint:** `POST /v1/pages`

**Purpose:** Push new learning insights as database entries

```http
POST /v1/pages
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json

{
  "parent": {
    "type": "database_id",
    "database_id": "{NOTION_AI_INSIGHTS_DB_ID}"
  },
  "properties": {
    "Insight": {
      "type": "title",
      "title": [
        {
          "type": "text",
          "text": {
            "content": "Checkout Friction: E-commerce Recurring Issue"
          }
        }
      ]
    },
    "Description": {
      "type": "rich_text",
      "rich_text": [
        {
          "type": "text",
          "text": {
            "content": "Pattern detected across 25 audits in e-commerce sector..."
          }
        }
      ]
    },
    "Confidence": {
      "type": "select",
      "select": {
        "name": "high"
      }
    },
    "Applied To": {
      "type": "multi_select",
      "multi_select": [
        {"name": "audit_engine"},
        {"name": "recommender"}
      ]
    },
    "Validation Count": {
      "type": "number",
      "number": 25
    },
    "CVR Impact": {
      "type": "number",
      "number": 3.2
    },
    "Tags": {
      "type": "multi_select",
      "multi_select": [
        {"name": "e-commerce"},
        {"name": "recurring_finding"},
        {"name": "high_impact"}
      ]
    }
  },
  "children": [
    {
      "type": "heading_2",
      "heading_2": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Key Examples"
            }
          }
        ]
      }
    },
    {
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Unclear payment method options"
            }
          }
        ]
      }
    }
  ]
}
```

**Python Implementation:**

```python
def push_learning_to_notion(learning: dict):
    """
    Create new AI insight page in Notion database.

    learning dict should contain:
    - title: str
    - description: str
    - confidence: str (low, medium, high)
    - applied_to: list[str]
    - validation_count: int
    - cvr_impact: float (optional)
    - examples: list[str]
    - tags: list[str]
    """

    client = Client(auth=NOTION_API_KEY)

    # Prepare children blocks from examples
    children_blocks = [
        {
            'object': 'block',
            'type': 'heading_2',
            'heading_2': {
                'rich_text': [{'type': 'text', 'text': {'content': 'Key Examples'}}]
            }
        }
    ]

    for example in learning.get('examples', []):
        children_blocks.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': example}}]
            }
        })

    page_data = {
        'parent': {
            'database_id': NOTION_AI_INSIGHTS_DB_ID
        },
        'properties': {
            'Insight': {
                'title': [{'text': {'content': learning['title']}}]
            },
            'Description': {
                'rich_text': [{'text': {'content': learning['description']}}]
            },
            'Confidence': {
                'select': {'name': learning['confidence']}
            },
            'Applied To': {
                'multi_select': [
                    {'name': module} for module in learning['applied_to']
                ]
            },
            'Validation Count': {
                'number': learning.get('validation_count', 1)
            },
            'CVR Impact': {
                'number': learning.get('cvr_impact', None)
            } if learning.get('cvr_impact') else {},
            'Tags': {
                'multi_select': [
                    {'name': tag} for tag in learning.get('tags', [])
                ]
            }
        },
        'children': children_blocks
    }

    try:
        response = client.pages.create(**page_data)
        new_page_id = response['id']

        log_info(f'Created Notion page {new_page_id} for learning {learning["title"]}')

        # Store reference locally
        update_learning_notion_reference(learning['id'], new_page_id)

        return {
            'success': True,
            'notion_page_id': new_page_id,
            'notion_page_url': f'https://notion.so/{new_page_id.replace("-", "")}'
        }

    except Exception as e:
        log_error(f'Push learning to Notion failed: {e}')
        return {'success': False, 'error': str(e)}
```

### 2. Update Page Properties

**Endpoint:** `PATCH /v1/pages/{page_id}`

**Purpose:** Update learning confidence, validation count when validated

```http
PATCH /v1/pages/abc123def456
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json

{
  "properties": {
    "Confidence": {
      "select": {"name": "high"}
    },
    "Validation Count": {
      "number": 35
    }
  }
}
```

**Python Implementation:**

```python
def update_learning_in_notion(notion_page_id, updates: dict):
    """
    Update properties of existing Notion page (learning validation).
    """

    client = Client(auth=NOTION_API_KEY)

    properties_update = {}

    if 'confidence' in updates:
        properties_update['Confidence'] = {
            'select': {'name': updates['confidence']}
        }

    if 'validation_count' in updates:
        properties_update['Validation Count'] = {
            'number': updates['validation_count']
        }

    if 'cvr_impact' in updates:
        properties_update['CVR Impact'] = {
            'number': updates['cvr_impact']
        }

    try:
        client.pages.update(
            page_id=notion_page_id,
            properties=properties_update
        )

        log_info(f'Updated Notion page {notion_page_id}')
        return {'success': True}

    except Exception as e:
        log_error(f'Update Notion page failed: {e}')
        return {'success': False, 'error': str(e)}
```

---

## ERROR HANDLING & RETRY LOGIC

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Log + continue |
| 400 | Bad Request | Log + don't retry (fix API call) |
| 401 | Unauthorized | Rotate API key + retry once |
| 403 | Forbidden | Integration doesn't have access (add in Notion) |
| 429 | Rate Limited | Exponential backoff (see Rate Limiting) |
| 500 | Server Error | Exponential backoff, max 5 retries |
| 503 | Unavailable | Exponential backoff, max 3 retries |

### Retry Strategy

```python
def api_call_with_retry(func, max_retries=5, base_delay=1):
    """
    Wrapper for Notion API calls with exponential backoff.
    """

    for attempt in range(max_retries):
        try:
            return func()

        except APIErrorCode.RateLimited:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                log_warn(f'Rate limited. Retrying in {delay:.1f}s...')
                time.sleep(delay)
            else:
                raise

        except APIErrorCode.InternalServerError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                log_warn(f'Server error. Retrying in {delay:.1f}s...')
                time.sleep(delay)
            else:
                raise

        except APIErrorCode.Unauthorized:
            log_error('Unauthorized. API key may be expired.')
            raise

        except Exception as e:
            log_error(f'Unexpected error: {e}')
            if attempt < max_retries - 1 and is_retryable_error(e):
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise

    raise Exception(f'Max retries ({max_retries}) exceeded')
```

### Circuit Breaker

```python
class SyncCircuitBreaker:
    """
    Prevent cascading failures: stop syncing if Notion API is down.
    """

    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure = None
        self.state = 'closed'  # closed, open, half_open

    def call(self, func):
        """Wrap function with circuit breaker logic."""

        if self.state == 'open':
            if (datetime.now() - self.last_failure).seconds > self.recovery_timeout:
                self.state = 'half_open'
            else:
                raise Exception('Circuit breaker is open. Notion API unavailable.')

        try:
            result = func()
            self.on_success()
            return result

        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = 'closed'

    def on_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            log_alert(f'Circuit breaker OPEN after {self.failure_count} failures')
```

---

## WEBHOOK EVENT PROCESSING

### Notion Webhook Setup (When Available)

**Register Webhook:**

```python
def register_notion_webhook():
    """
    Set up event subscriptions for Notion pages.
    When pages change, Notion posts to our endpoint.

    Note: Webhooks available in Notion API 2024-04+
    """

    client = Client(auth=NOTION_API_KEY)

    # Register webhook
    webhook_response = client.webhooks.register(
        events=[
            'page.updated',
            'block.updated',
            'database_item.updated'
        ],
        target_url=f'{GROWTHCRO_API_ENDPOINT}/webhooks/notion',
        auth_headers={
            'X-GrowthCRO-Secret': WEBHOOK_SECRET
        }
    )

    return webhook_response
```

**Webhook Handler:**

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhooks/notion', methods=['POST'])
def handle_notion_webhook():
    """
    Handle real-time Notion events.
    """

    # Verify signature
    signature = request.headers.get('X-Notion-Signature')
    if not verify_notion_signature(signature, request.data):
        return {'error': 'Invalid signature'}, 403

    event = request.json

    if event['type'] == 'page.updated':
        handle_page_updated(event['data']['page_id'])

    elif event['type'] == 'block.updated':
        # Find parent page + trigger reindex
        page_id = find_parent_page(event['data']['block_id'])
        queue_page_reindex(page_id)

    return {'status': 'received'}, 200
```

---

## CONFLICT RESOLUTION

### Priority Rules

```python
def resolve_sync_conflict(notion_version, gc_version, conflict_type):
    """
    Apply conflict resolution rules based on content type.
    """

    rules = {
        'manual_notion_content': {
            'rule': 'Notion authoritative',
            'logic': lambda n, g: n,
            'reason': 'User-created content in Notion is source of truth'
        },
        'auto_generated_content': {
            'rule': 'GrowthCRO authoritative',
            'logic': lambda n, g: g,
            'reason': 'Auto-generated content GrowthCRO is source of truth'
        },
        'shared_reference': {
            'rule': 'Flag for review',
            'logic': lambda n, g: {'notion': n, 'gc': g, 'conflict': True},
            'reason': 'Both modified - needs human decision'
        },
        'metadata_only': {
            'rule': 'Merge (timestamps)',
            'logic': lambda n, g: merge_metadata(n, g),
            'reason': 'Merge last_edited_time and authors'
        }
    }

    rule = rules.get(conflict_type, rules['shared_reference'])

    resolved = rule['logic'](notion_version, gc_version)

    log_conflict({
        'type': conflict_type,
        'notion_value': notion_version,
        'gc_value': gc_version,
        'resolved': resolved,
        'rule_applied': rule['rule'],
        'reason': rule['reason']
    })

    return resolved, rule['rule']
```

---

## RATE LIMITING & PERFORMANCE

### Notion API Rate Limits

**Limits (as of Feb 2024):**
- 3 requests/second per integration
- 30-minute rolling window
- Burst capacity: up to 10 requests/second

**Optimization Strategy:**

```python
from ratelimit import limits, sleep_and_retry

CALLS_PER_SECOND = 2
CALLS_PER_MINUTE = 100

@sleep_and_retry
@limits(calls=CALLS_PER_SECOND, period=1)
def rate_limited_notion_call():
    """Decorator ensures rate limit compliance."""
    pass

def batch_notion_operations(operations, batch_size=50):
    """
    Batch operations to minimize API calls.
    E.g., fetch 100 pages in 2 calls (50 page_size each).
    """

    results = []

    for i in range(0, len(operations), batch_size):
        batch = operations[i:i+batch_size]

        for op in batch:
            rate_limited_notion_call()
            result = op['func'](*op['args'])
            results.append(result)

        # Log progress
        log_info(f'Processed {len(results)}/{len(operations)} operations')

    return results
```

### Performance Metrics

```python
def sync_performance_monitoring():
    """
    Track sync duration, API calls, errors for optimization.
    """

    metrics = {
        'sync_start': datetime.now(),
        'pages_fetched': 0,
        'pages_indexed': 0,
        'embeddings_generated': 0,
        'api_calls': 0,
        'api_errors': 0,
        'total_duration_seconds': 0
    }

    # ... during sync, update metrics ...

    metrics['total_duration_seconds'] = (
        datetime.now() - metrics['sync_start']
    ).total_seconds()

    # Log to monitoring system
    log_metrics({
        'event': 'sync_completed',
        'pages_per_second': metrics['pages_fetched'] / metrics['total_duration_seconds'],
        'api_calls_per_page': metrics['api_calls'] / metrics['pages_fetched'],
        'errors': metrics['api_errors'],
        'timestamp': datetime.now().isoformat()
    })

    return metrics
```

---

## MONITORING & ALERTING

### Key Metrics to Track

```python
MONITORED_METRICS = {
    'sync_success_rate': 'Should be > 99%',
    'sync_duration_seconds': 'Should be < 300s for full sync',
    'pages_indexed_per_sync': 'Track growth',
    'embedding_errors': 'Alert if > 0',
    'api_rate_limit_hits': 'Alert if frequent',
    'conflict_count': 'Track manual reviews needed',
    'learning_insights_generated': 'Track learning velocity'
}

def setup_monitoring():
    """
    Configure alerting for critical failures.
    """

    alerts = {
        'sync_failure': {
            'condition': 'success_rate < 0.95',
            'channels': ['slack', 'pagerduty'],
            'severity': 'critical'
        },
        'rate_limit_exceeded': {
            'condition': 'rate_limit_hits > 10 in 1 hour',
            'channels': ['slack'],
            'severity': 'warning'
        },
        'embedding_failures': {
            'condition': 'embedding_errors > 0',
            'channels': ['pagerduty'],
            'severity': 'critical'
        },
        'sync_timeout': {
            'condition': 'sync_duration > 600 seconds',
            'channels': ['slack'],
            'severity': 'warning'
        }
    }

    return alerts
```

---

**End of Sync Protocol Reference**

