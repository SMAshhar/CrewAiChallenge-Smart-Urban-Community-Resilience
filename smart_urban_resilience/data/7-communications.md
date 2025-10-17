```json
{
  "alerts": [
    {
      "alert_id": "AQ-CO-20251017-001",
      "timestamp": "2025-10-17T14:28:00Z",
      "type": "Air Quality Alert",
      "severity": "High",
      "subject": "High Carbon Monoxide Levels Detected in Karachi",
      "message": "ALERT: Elevated carbon monoxide levels detected in Karachi. Potential health risk, especially for children, elderly, and those with respiratory issues. Stay indoors when possible. Ensure proper ventilation. Seek medical attention if experiencing symptoms like headache, dizziness, or nausea.",
      "location": "Karachi",
      "affected_areas": "Karachi (General)",
      "recipients": {
        "citizens": {
          "channel": [
            "Mobile App",
            "SMS",
            "Social Media (Facebook, Twitter)",
            "Local Radio",
            "Local TV"
          ],
          "segments": [
            "All Residents",
            "Registered Users with Respiratory Conditions",
            "Residents in High-Traffic Areas"
          ]
        },
        "departments": [
          {
            "department_name": "Karachi Metropolitan Corporation (KMC)",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Coordinate public awareness campaigns and resource deployment."
          },
          {
            "department_name": "Health Department",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Prepare healthcare facilities for potential increase in respiratory cases."
          },
          {
            "department_name": "Traffic Police",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Manage traffic flow to reduce emissions in congested areas."
          }
        ]
      },
       "expiry": "2025-10-18T02:00:00Z"
    },
    {
      "alert_id": "ENV-UV-20251017-002",
      "timestamp": "2025-10-17T14:28:00Z",
      "type": "Environmental Alert",
      "severity": "Medium",
      "subject": "High UV Index Warning for Karachi",
      "message": "WARNING: High UV Index (8.3) in Karachi today. Increased risk of sunburn and skin damage. Limit sun exposure, especially between 10 AM and 4 PM. Wear sunscreen, hats, and protective clothing.",
      "location": "Karachi",
      "affected_areas": "Karachi (General)",
      "recipients": {
        "citizens": {
          "channel": [
            "Mobile App",
            "Social Media (Facebook, Twitter)",
            "Local Radio"
          ],
          "segments": [
            "All Residents",
            "Parents of Young Children",
            "Outdoor Workers"
          ]
        },
        "departments": [
          {
            "department_name": "Parks and Recreation Department",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Post advisories at parks and recreational facilities."
          },
          {
            "department_name": "Education Department",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Inform schools about sun safety precautions for outdoor activities."
          }
        ]
      },
      "expiry": "2025-10-17T20:00:00Z"
    },
    {
      "alert_id": "ENV-PL-20251017-003",
      "timestamp": "2025-10-17T14:28:00Z",
      "type": "Environmental Alert",
      "severity": "Medium",
      "subject": "Elevated Pollen Levels in Karachi",
      "message": "ADVISORY: Elevated grass and tree pollen levels in Karachi. Allergy sufferers should take preventative measures such as medication and limiting outdoor exposure. Monitor pollen forecasts for updates.",
      "location": "Karachi",
      "affected_areas": "Karachi (General)",
      "recipients": {
        "citizens": {
          "channel": [
            "Mobile App",
            "Social Media (Facebook, Twitter)"
          ],
          "segments": [
            "Registered Users with Allergies",
            "Residents near Parks and Green Spaces"
          ]
        },
        "departments": [
          {
            "department_name": "Health Department",
            "channel": [
              "Internal Communication System"
            ],
            "responsibility": "Alert clinics and pharmacies about potential increase in allergy-related visits and medication demand."
          }
        ]
      },
      "expiry": "2025-10-19T14:28:00Z"
    }
  ]
}
```