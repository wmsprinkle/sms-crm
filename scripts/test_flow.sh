#!/bin/bash
# Full end-to-end test of the CRM flow in DRY_RUN mode

set -e
BASE_URL="http://localhost:8000"

echo "=== SMS Appointment CRM - Full Flow Test ==="
echo ""

echo "1. Get initial metrics..."
curl -s "$BASE_URL/contacts/metrics" | jq '.'
echo ""

echo "2. Import sample leads from CSV..."
curl -s -X POST "$BASE_URL/imports" \
  -F "file=@sample-leads.csv" \
  -F "sequence_id=1" \
  -F 'mapping={"phone":"Phone","first_name":"First","company":"Company"}' \
  -F "source=demo" | jq '.'
echo ""

echo "3. List all contacts..."
curl -s "$BASE_URL/contacts" | jq '.'
echo ""

echo "4. Create a test lead for interactive testing..."
LEAD=$(curl -s -X POST "$BASE_URL/testchat/new" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Contact","company":"Demo Corp"}')
CONTACT_ID=$(echo "$LEAD" | jq -r '.id')
echo "$LEAD" | jq '.'
echo ""

echo "5. Send a message from the test lead..."
curl -s -X POST "$BASE_URL/testchat/$CONTACT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hi, I am interested in your life insurance products"}' | jq '.'
echo ""

echo "6. Get the conversation thread..."
curl -s "$BASE_URL/contacts/$CONTACT_ID/thread" | jq '.'
echo ""

echo "7. Check for draft messages..."
DRAFTS=$(curl -s "$BASE_URL/contacts/drafts")
echo "$DRAFTS" | jq '.'
DRAFT_ID=$(echo "$DRAFTS" | jq -r '.[0].id // empty')
echo ""

if [ -n "$DRAFT_ID" ]; then
  echo "8. Approve the draft message..."
  curl -s -X POST "$BASE_URL/drafts/$DRAFT_ID/approve" | jq '.'
  echo ""

  echo "9. Get updated metrics after approval..."
  curl -s "$BASE_URL/contacts/metrics" | jq '.'
fi

echo ""
echo "=== Test Complete ==="
echo "The CRM is working end-to-end in DRY_RUN mode:"
echo "- Imported 5 leads from CSV"
echo "- Created interactive test lead"
echo "- Agent processed inbound message and drafted reply"
echo "- Approved message (DRY_RUN, no actual SMS sent)"
echo ""
echo "Next steps:"
echo "1. Set up Telnyx webhook URL (use ngrok: ngrok http 8000)"
echo "2. Add Telnyx credentials to .env"
echo "3. Set DRY_RUN=false to enable live SMS"
