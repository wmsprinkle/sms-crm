# Compliance & Best Practices Guide

This guide helps you use the SMS Appointment CRM responsibly and compliantly when managing customer communications.

## Regulatory Context

SMS appointment setting in the insurance industry is regulated by:

- **TCPA (Telephone Consumer Protection Act)** — US federal law on SMS marketing
- **GDPR (EU)** — If you have EU customers
- **State regulations** — Some states have stricter rules
- **Company policy** — Your agency's own compliance standards

This CRM is built to support compliance, but **you are responsible** for ensuring your use complies with all applicable laws.

## Essential TCPA Compliance

### ✅ What You MUST Have Before Texting

1. **Express written consent** — Each contact must have opted-in
   - Save consent records with timestamp and method
   - Example: "I agree to receive SMS appointment reminders from [Agency]"
   
2. **Clear business identity** — In first message, identify who you are
   - Include your company name and clear opt-out instructions
   - Example: "Hi Sarah, it's Relay from Acme Insurance..."

3. **Accurate routing** — Caller ID / sender ID must be your real number
   - Telnyx 10DLC number assigned to your profile
   - No fake or spoofed numbers

4. **Opt-out respect** — Immediately stop texting anyone who says STOP
   - This CRM handles this automatically
   - Confirm opt-out to the customer ("Got it, no more texts from us")

5. **Message frequency** — Don't spam with excessive messages
   - Reasonable limits: 1-3 per week per contact during active campaign
   - Higher frequency is OK during active booking process
   - Space out drip campaign steps by days, not hours

### ✅ TCPA Best Practices

- **Use conversational tone** — Not robotic or overly promotional
- **Respect quiet hours** — Set `QUIET_HOURS_START` and `QUIET_HOURS_END` appropriately
- **Respond to replies** — When customers text back, engage promptly
- **Clear exit path** — Make it easy to opt-out (reply STOP, not "text X to unsubscribe")
- **No auto-redial** — Never retry failed sends too aggressively

## CRM Compliance Features

The CRM includes these built-in protections:

### STOP Keyword Handling
```
If customer texts: STOP
App automatically: Opts out contact, stops all future messages
```
Always enabled, cannot be disabled.

### Quiet Hours
```
QUIET_HOURS_START=21    # No sends at 9pm or later
QUIET_HOURS_END=9       # No sends before 9am (set to your timezone)
```
Applies to drip campaigns AND manual sends.

### Draft Approval (AUTO_SEND=false)
Review every agent-drafted message before sending:
```
1. Agent drafts reply to customer
2. You review at /contacts/drafts
3. Approve or discard manually
4. Only then is SMS sent
```
Recommended for: Building trust, training the agent, regulatory confidence.

### Message Audit Trail
All messages stored with:
- Timestamp
- Direction (in/out)
- Status (draft → queued → sent → delivered)
- Full text
- Associated contact

Use this to prove compliance if questioned.

### Consent Records
The CRM doesn't store explicit consent dates. **You must**:
1. Keep separate records of how/when each contact opted in
2. Document where the phone number came from
3. Store these outside the CRM for regulatory proof

Example CSV with consent tracking:
```
Phone,First,Company,ConsentDate,ConsentMethod
+15551234567,Sarah,Acme,2026-08-01,Phone referral
+15559876543,James,Tech,2026-08-05,Website signup
```

## Setup Checklist for Going Live

### Before Your First SMS

- [ ] Have **express written consent** for all contacts
- [ ] Confirm your **10DLC campaign is approved** by Telnyx
- [ ] Test with **one contact first** — send/receive/approve workflow
- [ ] Verify **quiet hours are set correctly** for your timezone
- [ ] Configure **AUTO_SEND appropriately**:
  - `false` = review all drafts (safer, more work)
  - `true` = send automatically (faster, requires trust)
- [ ] Document **message templates** you'll use in drip sequences
- [ ] Set **reasonable send rate** (60/min is default max)
- [ ] Have **opt-out / customer support plan** for STOP requests
- [ ] Review **sample conversation** with test contact

### Ongoing Operations

- [ ] **Monitor delivery** — Check Telnyx dashboard weekly
- [ ] **Review metrics** — Are people replying? Booking?
- [ ] **Respect opt-outs** — Verify STOP contacts stay opted out
- [ ] **Audit conversations** — Random sample of live conversations
- [ ] **Keep consent records** — Store separately from CRM
- [ ] **Update product knowledge** — Keep accurate, remove outdated info

### Incident Response

If a customer complains about unsolicited texts:
1. **Immediate**: Opt them out (STOP or manual if system fails)
2. **Same day**: Apologize and explain mistake
3. **Document**: Log when/how the mistake happened
4. **Prevent**: Fix the root cause (wrong list, bad number, etc.)
5. **Retain**: Keep records in case of TCPA claim

## Best Practices by Use Case

### Cold Outreach (Warm Leads)
✅ Use this CRM for: Leads who've shown interest or requested info
❌ Don't use for: Random phone numbers, purchased lists, cold calls

**Required**: Clear, documented consent for each number.

### Re-engagement Campaigns
✅ Use this CRM for: Past customers, policy holders, old leads
❌ Don't use for: Contacts who haven't interacted in 5+ years

**Required**: Some prior relationship; confirmation they want updates.

### Booking Confirmations
✅ Use this CRM for: Sending booking links, appointment reminders
❌ Don't use for: Spamming booking links repeatedly

**Required**: Customer just requested a booking; send link promptly.

### Drip Sequences
✅ Use this CRM for: 3-5 message sequences over 2-3 weeks
❌ Don't use for: Daily messages or more than weekly frequency

**Required**: Set reasonable delays between steps (e.g., 48 hours, 5 days, etc.).

## Product Knowledge Compliance

Your product knowledge files (in `knowledge/` folder) are part of your compliance:

### ✅ What To Include
- General product descriptions (who it's for, what it covers)
- Enrollment timeline (how fast can someone apply?)
- Eligibility basics (you must be X age, Y employment status)
- Comparison with competitor products (if accurate)
- FAQs about the product

### ❌ What NOT To Include
- Specific premium amounts ("$50/month") — too prone to misquoting
- Coverage guarantees ("You'll never pay out of pocket")
- Medical advice ("This is perfect for diabetics")
- Tax advice ("You can deduct premiums")
- Promises requiring underwriting ("Everyone qualifies")

**The Rule**: If a licensed agent wouldn't say it casually to a cold lead, don't put it in the agent's knowledge.

### Testing Compliance
Before going live, ask your product knowledge test messages:
1. "How much does this cost?" — Should defer to agent, not quote
2. "Can I use this for X medical condition?" — Should defer to agent
3. "What does this cover?" — Should answer clearly from knowledge
4. "How do I apply?" — Should explain enrollment process

If the agent strays from your knowledge or makes promises, edit the knowledge files.

## State-Specific Considerations

Different states may have stricter rules. Common variations:

### Hawaii
- SMS marketing heavily restricted
- Recommend `AUTO_SEND=false` (review all messages)

### California
- Consumer Privacy Act (CCPA) adds requirements
- Document consent explicitly
- Honor do-not-contact requests quickly

### New York
- Strict consent requirements
- Consider written opt-in above SMS opt-in

### Other States
- Some require specific identifiers in sender ID
- Some restrict times (similar to TCPA quiet hours)

**Action**: Check your state's regulations before launch. If unsure, err on the side of caution.

## GDPR (EU Customers)

If you have EU contacts:
- Get **explicit opt-in** (not opt-out)
- Document the **legal basis** (contract performance, consent, etc.)
- Honor **deletion requests** immediately
- Respect **marketing preference** (business SMS only, no promo)

This CRM doesn't include GDPR consent management. If you serve EU customers, add a consent management layer.

## Logging & Audit Trail

The CRM logs all:
- Inbound/outbound messages with timestamps
- Delivery status changes
- Contact status changes (opt-out, etc.)
- API calls and user actions

**Recommendation**: Archive these monthly for compliance proof:
```bash
# Export monthly backup
docker compose exec db pg_dump -U crm crm > backup-2026-08.sql
```

If sued under TCPA, these logs show you acted in good faith.

## Common Compliance Mistakes

### ❌ Mistake: No opt-in consent
**Risk**: TCPA violation, fines $500-1500 per SMS
**Fix**: Verify consent for every contact before importing

### ❌ Mistake: Texting after STOP
**Risk**: TCPA violation, triple damages
**Fix**: CRM handles this (enabled by default), but verify in logs

### ❌ Mistake: Texting outside quiet hours
**Risk**: Violates company policy, customer complaints
**Fix**: Set `QUIET_HOURS_START` and `QUIET_HOURS_END` correctly

### ❌ Mistake: Sending quotes/advice in knowledge base
**Risk**: Regulatory complaint, compliance request
**Fix**: Review knowledge files; defer quotes to agent call

### ❌ Mistake: Changing marketing message without approval
**Risk**: Different campaign than customers consented to
**Fix**: Update consent records if changing campaign purpose

### ❌ Mistake: No opt-out response
**Risk**: Customer frustration, poor reputation
**Fix**: Auto-send confirmation when contact opts out

## Recommended: Approval Workflow

For maximum compliance confidence, use `AUTO_SEND=false`:

```env
AUTO_SEND=false
```

Then:
1. **Agent drafts** response automatically
2. **You review** at http://localhost:8000/contacts/drafts
3. **You approve or discard** before sending
4. **You have full audit trail** of who approved what

This takes more work but gives you:
- Full control over messaging
- Proof of review (if questioned)
- Training opportunity for your team
- Reduced risk of accidental violations

## Support & Questions

- **Compliance lawyer**: Consult for your specific state/situation
- **Telnyx support**: Questions about 10DLC or campaign registration
- **CRM documentation**: See [../docs/README.md](../docs/README.md)
- **Product knowledge**: See [../knowledge/CUSTOMIZE.md](../knowledge/CUSTOMIZE.md)

## Summary

✅ **The CRM supports compliance**, but you must:
1. Ensure valid consent for every contact
2. Keep accurate audit logs
3. Respect STOP and quiet hours
4. Keep product knowledge factual
5. Use appropriate send rates and frequency
6. Document your process

**The bottom line**: This is a conversation tool, not a spam tool. Use it to have real conversations with people who want to hear from you, and you'll stay compliant and effective.
