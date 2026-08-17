# Product Knowledge Base

Drop your life & health insurance product documents here. All `.md`, `.txt`, and `.pdf` files become the agent's product knowledge.

## How It Works

The agent ONLY uses facts from files in this folder. If your knowledge doesn't cover something, the agent defers to your licensed agent—it will not guess, speculate, or invent details.

## What to Include

One file per product line (examples below). Write conversationally as if explaining to a lead:

**Good examples:**
- `term-life-insurance.md` — Who it's for, term lengths, coverage amounts, enrollment process
- `health-plans.md` — Plan tiers, deductibles, what's covered, special situations
- `faq.md` — Answers to common questions your team gets
- `call-process.md` — What happens during the intro call, how long it takes

## What to Exclude

❌ **Never include:**
- Specific premium amounts or "rate sheets" (say "competitive" instead)
- Medical advice or coverage guarantees
- Internal notes or compliance footnotes
- Things you wouldn't say verbatim to a lead
- Anything requiring a license to state

## Quick Start

1. Look at the templates: `example-term-life.md`, `health-insurance.md`
2. Replace them with your products OR add your own `.md` files
3. Test with `/testchat` endpoint (see docs/API.md)

## Customization Guide

For detailed guidance on:
- What to include/exclude for compliance
- How to structure documents
- Testing your knowledge base
- Common pitfalls

See [CUSTOMIZE.md](CUSTOMIZE.md)

## Testing Your Knowledge

```bash
# Create test contact
curl -X POST http://localhost:8000/testchat/new \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","company":"Agency"}'

# Ask a question about your product
curl -X POST http://localhost:8000/testchat/1/message \
  -H "Content-Type: application/json" \
  -d '{"text":"What term lengths do you offer?"}'

# Check if agent uses your knowledge correctly
```

## File Support

- `.md` (Markdown) — Recommended, easiest to edit
- `.txt` (Plain text) — Also supported
- `.pdf` — Install `pypdf`: `pip install pypdf`

All files are loaded automatically on startup.

## Compliance Note

The LLM is hardened to only use knowledge in these files. Anything outside:
- Medical/tax/legal questions → Defers to agent
- Specific quotes → Says agent will cover
- Other insurance companies → Ignores
- Off-topic requests → Politely redirects

This is by design—it keeps the agent focused on your products and compliant.

## Support

- **How do I customize?** → See [CUSTOMIZE.md](CUSTOMIZE.md)
- **Example products** → `example-term-life.md`, `health-insurance.md`
- **API questions?** → See [../docs/API.md](../docs/API.md)
