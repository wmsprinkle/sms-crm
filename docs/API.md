# API Reference

This document describes all available endpoints in the SMS Appointment CRM.

## Base URL

```
http://localhost:8000
```

## Webhooks

### POST /webhooks/telnyx
**Webhook endpoint for inbound SMS and delivery receipts from Telnyx.**

Handles:
- Inbound SMS messages (message.received events)
- Delivery receipts (message.sent, message.finalized events)

**Authentication**: Signature verification (Ed25519)

**Headers required**:
- `telnyx-signature-ed25519`: Message signature
- `telnyx-timestamp`: Message timestamp

**Request body** (from Telnyx):
```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "id": "message_id",
      "from": {"phone_number": "+1234567890"},
      "text": "Customer message",
      "to": []
    }
  }
}
```

**Response**:
```json
{"ok": true}
```

**Note**: This endpoint is idempotent (same message ID won't be processed twice).

---

### POST /webhooks/booking
**Webhook endpoint for Calendly booking confirmations.**

Handles Calendly `invitee.created` events and updates contact status to "booked".

**Request body** (from Calendly):
```json
{
  "event_type": "invitee.created",
  "payload": {
    "email": "...",
    "scheduled_event": {
      "uri": "https://calendly.com/...",
      "start_time": "2026-08-17T14:00:00Z",
      "status": "active"
    },
    "custom_questions_answers": [
      {
        "question": "Contact ID",
        "answer": "123"
      }
    ]
  }
}
```

**Response**:
```json
{"ok": true}
```

---

## Contacts

### GET /contacts/metrics
**Get aggregate metrics for the CRM.**

No authentication required.

**Response**:
```json
{
  "contacts": 42,
  "by_status": {
    "active": 20,
    "engaged": 15,
    "booked": 7,
    "optout": 0
  },
  "booked": 7,
  "sent": 142,
  "delivery_rate": 0.987
}
```

**Fields**:
- `contacts`: Total unique contacts
- `by_status`: Breakdown by contact status
- `booked`: Contacts with confirmed bookings
- `sent`: Outbound SMS sent (queued, sent, delivered)
- `delivery_rate`: Proportion of sent messages with delivery status

---

### GET /contacts
**List contacts with optional filtering.**

**Query parameters**:
- `status` (optional): Filter by status (active, engaged, booked, optout)

**Response**:
```json
[
  {
    "id": 1,
    "name": "Sarah",
    "phone": "+15551234567",
    "status": "active",
    "tags": ["vip", "referred"]
  }
]
```

Returns up to 100 most recent contacts.

---

### GET /contacts/{contact_id}/thread
**Get full conversation history for a contact.**

**Path parameters**:
- `contact_id`: Contact ID

**Response**:
```json
[
  {
    "direction": "in",
    "body": "Hi, tell me more",
    "status": null,
    "at": "2026-08-17T12:00:00.000Z"
  },
  {
    "direction": "out",
    "body": "Would you like to schedule a call?",
    "status": "delivered",
    "at": "2026-08-17T12:00:05.000Z"
  }
]
```

Returns all messages for this contact, oldest first.

---

### GET /contacts/drafts
**Get all pending agent-drafted messages awaiting approval.**

Only returns drafts when `AUTO_SEND=false`.

**Response**:
```json
[
  {
    "id": 5,
    "contact_id": 2,
    "body": "Great! Would Tuesday at 2pm work?"
  }
]
```

---

## Drafts

### POST /drafts/{message_id}/approve
**Approve and send a draft message.**

Requires `AUTO_SEND=false` configuration.

**Path parameters**:
- `message_id`: Draft message ID

**Response**:
```json
{
  "ok": true,
  "telnyx_id": "msg_xyz123"
}
```

**Side effects**:
- Sets message status to "queued"
- Stores Telnyx message ID
- Compliance checks run (STOP, quiet hours)

---

### POST /drafts/{message_id}/discard
**Discard a draft message without sending.**

**Path parameters**:
- `message_id`: Draft message ID

**Response**:
```json
{"ok": true}
```

**Side effects**:
- Deletes the message record

---

## Imports

### POST /imports
**Import leads from a CSV file.**

**Form parameters**:
- `file` (required, multipart): CSV file
- `sequence_id` (required, int): ID of sequence to enroll into
- `mapping` (required, JSON): Field mapping
- `source` (optional, string): Import source identifier

**Mapping example**:
```json
{
  "phone": "Phone",
  "first_name": "First Name",
  "company": "Company",
  "industry": "Industry"
}
```

Supported mapping keys:
- `phone` (required): Phone number column
- `first_name` (optional): Contact's first name
- Any other key: stored in contact.fields for {{merge}} tokens

**Response**:
```json
{
  "imported": 42,
  "skipped": 2,
  "duplicates": 1,
  "errors": [
    "Row 5: invalid phone number '+abc'",
    "Row 10: phone column 'Phone' not found"
  ]
}
```

**Errors array** (up to 10):
- Included if there were validation issues
- Shows row number and specific reason

---

## Test Chat (DRY_RUN only)

These endpoints are ONLY available when `DRY_RUN=true`.

### POST /testchat/new
**Create a test contact for interactive testing.**

**Request body**:
```json
{
  "name": "Alex",
  "company": "Acme Corp"
}
```

**Response**:
```json
{
  "id": 123,
  "name": "Alex",
  "phone": "+15550001000"
}
```

---

### POST /testchat/{contact_id}/message
**Send a test message from a contact.**

The agent will process this as an inbound message and may draft a reply.

**Path parameters**:
- `contact_id`: Contact ID

**Request body**:
```json
{
  "text": "Hi, I'm interested in life insurance"
}
```

**Response**:
```json
{
  "opted_out": false,
  "status": "engaged",
  "messages": [
    {
      "id": 100,
      "direction": "in",
      "body": "Hi, I'm interested...",
      "status": null
    },
    {
      "id": 101,
      "direction": "out",
      "body": "Great! Would a quick call work?",
      "status": "draft"
    }
  ]
}
```

Returns only NEW messages created by this request (not full history).

---

## Health & Status

### GET /health
**Health check endpoint for monitoring and load balancers.**

**Response (success, 200)**:
```json
{
  "ok": true,
  "dry_run": true
}
```

**Response (failure, 503)**:
```json
{
  "ok": false,
  "error": "database error: connection refused"
}
```

Returns 503 if database is unavailable.

---

## Error Responses

All endpoints return appropriate HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (invalid format or parameters) |
| 403 | Forbidden (e.g., test endpoint in production) |
| 404 | Not found |
| 409 | Conflict (e.g., compliance gate blocked send) |
| 422 | Validation error |
| 500 | Server error |
| 503 | Service unavailable (database down) |

**Error response format**:
```json
{
  "detail": "Detailed error message"
}
```

---

## Rate Limiting

No built-in rate limiting; configure at load balancer level if needed.

Default throughput is controlled by:
- `SEND_RATE_PER_MINUTE`: Max SMS per minute (default 60)
- `WORKER_INTERVAL_SECONDS`: Worker poll frequency (default 30s)

---

## Authentication

Most endpoints require no authentication (webhook signature provides security on `/webhooks/`).

For self-hosted setups, consider adding:
- API key validation
- OAuth2 / JWT tokens
- IP whitelist

See deployment docs for guidance.

---

## Example Workflows

### Import and Auto-Send Workflow

```bash
# 1. Seed a sequence
python -m scripts.seed

# 2. Import leads
curl -X POST http://localhost:8000/imports \
  -F "file=@leads.csv" \
  -F "sequence_id=1" \
  -F 'mapping={"phone":"Phone","first_name":"First"}'

# 3. Monitor metrics
curl http://localhost:8000/contacts/metrics

# 4. Check conversation thread
curl http://localhost:8000/contacts/1/thread
```

### Draft Review Workflow (AUTO_SEND=false)

```bash
# 1. Get pending drafts
DRAFT=$(curl http://localhost:8000/contacts/drafts | jq '.[0]')

# 2. Review draft message
echo $DRAFT | jq '.body'

# 3. Approve or discard
curl -X POST http://localhost:8000/drafts/$(echo $DRAFT | jq '.id')/approve
# or
curl -X POST http://localhost:8000/drafts/$(echo $DRAFT | jq '.id')/discard
```

### Interactive Testing (DRY_RUN=true)

```bash
# 1. Create test contact
CONTACT=$(curl -X POST http://localhost:8000/testchat/new \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","company":"Corp"}')

CID=$(echo $CONTACT | jq '.id')

# 2. Send test message
curl -X POST http://localhost:8000/testchat/$CID/message \
  -H "Content-Type: application/json" \
  -d '{"text":"Hi, tell me about your products"}'

# 3. View results
curl http://localhost:8000/contacts/$CID/thread
```

---

## OpenAPI / Swagger

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These are auto-generated from FastAPI route definitions.
