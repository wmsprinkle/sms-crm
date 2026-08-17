# Customizing Your Product Knowledge

The agent uses files in this folder to understand your insurance products and answer customer questions accurately. The LLM includes this knowledge in its system prompt, so it only suggests actions based on what's in these files.

## How It Works

1. Files are loaded and passed to the LLM decision engine
2. Agent answers questions ONLY using information here
3. Anything not in these files → agent defers to licensed agent call
4. URLs in responses are blocked; only the booking link can be sent

## Customization Steps

### 1. Replace the Examples
The default files (`example-term-life.md`, `health-insurance.md`) are templates. Replace or expand them with your actual products:

- Product names and features
- Plan tiers and pricing (general ranges, not specific quotes)
- Eligibility rules
- Enrollment timelines
- Company-specific policies

### 2. Be Specific But Safe
Good sections:
- What the product covers (high level)
- Term/duration options
- Eligibility categories
- How to enroll
- When to expect decisions

Avoid:
- Specific premium amounts (say "competitively priced" or "low cost")
- Guarantees or promises
- Medical/tax/financial advice
- Anything requiring a license to state

### 3. Keep It Conversational
The agent extracts key facts and speaks naturally. Write as if explaining to a friend:
- "We offer term life policies with 10, 20, and 30 year options"
- NOT "Pursuant to policy XYZ-123, the insured may elect..."

### 4. Use Markdown Sections
The parser extracts headers and content:
```markdown
## Section Title
Details here.
```

### 5. Test It
After editing, create a test lead and ask questions:
```bash
curl -X POST http://localhost:8000/testchat/new \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","company":"Agency"}'

curl -X POST http://localhost:8000/testchat/1/message \
  -H "Content-Type: application/json" \
  -d '{"text":"What term lengths do you offer?"}'
```

Check the response to see if the agent uses your knowledge correctly.

## File Naming
Files can be named anything: `products.md`, `term-life.md`, `faq.md`, etc. All `.md` files in this folder are included.

## Disabling a Product
Rename the file (e.g., `old-product.md.bak`) or delete it. The next time the app starts, it won't be loaded.

## Questions the Agent Deflects
The LLM is instructed to defer to a call for:
- Specific premiums or rate quotes
- Medical/underwriting decisions
- Tax or legal questions
- Coverage limits or guarantees
- Anything outside the KNOWLEDGE section

This is by design — only licensed agents answer those.
