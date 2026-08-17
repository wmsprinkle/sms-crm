# SMS Booking CRM

Autonomous SMS appointment setter. A CSV of warm, opted-in leads goes in;
booked meetings come out. The agent texts each lead, converses toward a
booking, sends a scheduling link, and stops when they book. Compliance
(STOP + quiet hours) gates every send.

CSV in -> drip + conversation -> booking link -> meeting on the calendar.

## What you need from Telnyx

1. **Telnyx account + V2 API key** (Keys & Credentials) -> `TELNYX_API_KEY`
2. **Account Public Key** (same page) -> `TELNYX_PUBLIC_KEY` (verifies webhooks)
3. **Messaging Profile**, API V2 -> `TELNYX_MESSAGING_PROFILE_ID`
4. **10DLC long-code number** assigned to that profile -> `TELNYX_FROM_NUMBER`
5. **10DLC brand + campaign registration**. Register the use case that matches
   warm-lead conversational booking (not promotional marketing). Required for
   US A2P deliverability; takes a few days.
6. **Inbound webhook URL** on the messaging profile ->
   `https://your-domain/webhooks/telnyx` (use an ngrok URL in development).

Also needed: a cheap OpenAI-compatible LLM key (DeepSeek by default) and, if
you want the booking loop closed automatically, a Calendly token + event type.

## Run it locally (no accounts needed)

A fresh clone runs with zero configuration. `DRY_RUN=true` is the default,
so no SMS is sent: messages are logged as if delivered. The database
defaults to a local SQLite file. This is enough to import CSVs, run the
drip worker, drive the agent, and hit every endpoint.

    pip install -r requirements.txt
    python -m scripts.seed        # creates a sample 4-step sequence
    uvicorn app.main:app --reload # http://localhost:8000/docs

Import a test CSV and watch the worker "send" (logged, not real):

    curl -F file=@leads.csv -F sequence_id=1 \
         -F 'mapping={"phone":"Phone","first_name":"First"}' \
         http://localhost:8000/imports

## Run with Docker (Postgres included)

    cp .env.example .env          # DRY_RUN=true still works with no keys
    docker compose up --build     # Postgres + app on :8000
    docker compose exec app python -m scripts.seed

## Go live (when you have a Telnyx number)

1. Fill the Telnyx + LLM values in `.env` and set `DRY_RUN=false`.
2. Expose the app on a public HTTPS URL (a host in production, or
   `ngrok http 8000` in development).
3. Put `https://<that-url>/webhooks/telnyx` on your messaging profile.
4. Text your number and watch a reply come back.

## Self-hosting / giving this to others

Everything is configured through `.env`, so each person runs their own
isolated instance with their own credentials. To let someone self-host:
share this repo, they `cp .env.example .env`, add their own Telnyx number,
LLM key, and booking link, and run `docker compose up`. No shared servers,
no central account. Their data stays in their own Postgres.

## Endpoints

- `POST /webhooks/telnyx`   inbound SMS + delivery receipts (signature-verified)
- `POST /webhooks/booking`  Calendly invitee.created -> marks contact booked
- `POST /imports`           upload a CSV (file, sequence_id, mapping JSON)
- `GET  /contacts/metrics`  dashboard numbers
- `GET  /contacts`          lead list (optional ?status=)
- `GET  /contacts/{id}/thread`  full conversation
- `GET  /contacts/drafts`   agent drafts awaiting approval
- `POST /drafts/{id}/approve` | `/discard`   approve or drop a draft

## Import a CSV

    curl -F file=@leads.csv \
         -F sequence_id=1 \
         -F 'mapping={"phone":"Phone","first_name":"First","company":"Company"}' \
         -F source=q3-warm \
         http://localhost:8000/imports

Any mapped column beyond phone/first_name is stored on the contact and usable
as a {{merge}} token in sequence steps.

## The two leashes

- `AUTO_SEND=false` -> the agent drafts replies and holds them; approve from
  `/contacts/drafts` + `/drafts/{id}/approve`. Flip to `true` once you trust it.
- Compliance is the last gate before every send, in both the worker and the
  reply path. STOP opts a lead out and halts all their sequences instantly.

## Structure

    app/
      config.py            settings from .env
      db.py                SQLAlchemy engine/session
      models.py            Contact, Sequence, Step, Enrollment, Message, Booking
      agent.py             inbound -> decide -> send/draft (compliance-gated)
      ingest/csv_import.py normalize phones, dedupe, enroll
      services/
        telnyx_client.py   send SMS + Ed25519 webhook verify
        llm.py             cheap LLM decision (OpenAI-compatible)
        compliance.py      STOP + quiet hours
        merge.py           {{merge}} fields
        booking/           base + calendly + static providers
      routers/             webhooks, imports, contacts, drafts
      worker/scheduler.py  drip loop (APScheduler, every 30s)
    scripts/seed.py        sample warm re-engagement sequence

Swap `Base.metadata.create_all` for Alembic before production.

## CRM console added in this build

Open `http://localhost:8000/` after starting the app. The console is now backed by the real database/API rather than mock JavaScript data. It includes:

- live metrics, searchable contacts, conversation threads, delivery/draft status
- server-sent event refreshes for new messages/bookings plus a polling fallback
- pause/resume controls per contact and manual replies
- runtime Auto-send toggle (resets to `.env` value when the process restarts)
- CSV upload with browser-side column detection/mapping and automatic enrollment
- sequence list/editor and new-sequence creation
- live activity feed for inbound/outbound/draft/booking events

Additional endpoints:

- `GET /activity` and `GET /events`
- `GET/POST/PUT /sequences`
- `GET /runtime` and `POST /runtime/auto-send`
- `POST /contacts/{id}/pause`, `/resume`, and `/send`

The inbound Telnyx path now stores the provider message id on inbound messages, so webhook retries are actually idempotent. AI-classified opt-outs also halt active/paused enrollments.
