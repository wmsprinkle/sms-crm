# Documentation

## Quick Start
- **[Main README.md](../README.md)** — Overview and quick start
- **[API.md](API.md)** — Complete API endpoint reference
- **[TELNYX_SETUP.md](TELNYX_SETUP.md)** — Configure SMS provider
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Production deployment guide

## For Setup
- **[TELNYX_SETUP.md](TELNYX_SETUP.md)** — Step-by-step Telnyx configuration
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Local, Docker, and cloud deployment

## For Development
- **[API.md](API.md)** — Endpoint reference, examples, error codes
- **[../knowledge/CUSTOMIZE.md](../knowledge/CUSTOMIZE.md)** — Customize product knowledge

## Common Tasks

**Import CSV leads:**
```bash
curl -F file=@leads.csv \
     -F sequence_id=1 \
     -F 'mapping={"phone":"Phone","first_name":"First"}' \
     http://localhost:8000/imports
```

**Check system health:**
```bash
curl http://localhost:8000/health
```

**View metrics:**
```bash
curl http://localhost:8000/contacts/metrics
```

**Run test flow:**
```bash
bash scripts/test_flow.sh
```

See [API.md](API.md) for complete endpoint documentation.
