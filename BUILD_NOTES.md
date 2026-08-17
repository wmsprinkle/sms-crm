# Build notes — 2026-08-14

This pass turns the prototype CRM console into a real frontend for the existing FastAPI backend.

## Added
- Real dashboard metrics and contact data
- Search/filtering and full conversation threads
- Live activity feed + Server-Sent Events refresh
- CSV import modal with column mapping and sequence selection
- Sequence list/editor/create APIs and UI
- Contact pause/resume controls
- Manual message send path
- Runtime Auto-send toggle
- Better draft metadata

## Fixed
- Telnyx inbound message IDs are now persisted, so webhook retry deduplication works
- AI-classified opt-outs now halt active/paused sequence enrollments
- Removed dependency on the old mock-data dashboard and its dead Drip Credits JavaScript

## Still before production
- Verify Calendly webhook signatures before trusting booking webhooks
- Move from `Base.metadata.create_all()` to Alembic migrations for schema versioning
- Add authentication/authorization before exposing the CRM to the public internet
- Persist runtime settings if you want Auto-send changes to survive process restarts
