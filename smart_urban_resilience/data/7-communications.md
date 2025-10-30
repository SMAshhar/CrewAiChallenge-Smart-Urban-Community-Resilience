```json
{
  "status": "failed_to_send",
  "reason": "Communication Tool validation requires 'to' field despite 'recipients' being present, contradicting task instructions and example. Specific 'to' contacts for 'all' or department groups are not available.",
  "dry_run": true,
  "messages_attempted": [
    {
      "id": "msg-wildfire-1",
      "channel": "sms",
      "body": "CRITICAL Wildfire Risk Alert for Suining County! Index 96. Exercise extreme caution. Report any fires immediately. Stay updated on official advisories.",
      "recipients": ["Emergency Services", "all", "Fire Department"]
    },
    {
      "id": "msg-flood-1",
      "channel": "sms",
      "body": "Flood Risk Alert for Suining County! Index 56. Be aware of localized flooding, especially in low-lying areas. Avoid flooded roads. Monitor local news for updates.",
      "recipients": ["Emergency Services", "all", "Public Works"]
    },
    {
      "id": "msg-pollen-1",
      "channel": "sms",
      "body": "High Tree Pollen Count (194) in Suining County. Allergy sufferers advised to limit outdoor activity and take precautions. Consult a doctor if symptoms worsen.",
      "recipients": ["all", "Health Services"]
    },
    {
      "id": "msg-uv-1",
      "channel": "sms",
      "body": "UV Index Alert for Suining County is 6.5. Protect yourself from the sun: wear sunscreen, hats, and protective clothing if outdoors for extended periods.",
      "recipients": ["all"]
    }
  ],
  "sending_results": "Not sent due to validation error: 'to' field required."
}
```