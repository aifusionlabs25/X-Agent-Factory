# 📜 Golden Dossier Schema (v1.0)

**Purpose**: This schema defines the *only* accepted input format for the Universal Factory Orchestrator.
**Enforcement**: Strict. Any deviation will cause the factory to reject the job.

## JSON Structure

```json
{
  "client_profile": {
    "name": "Acme Solar",
    "industry": "Commercial Solar Installation",
    "region": "Phoenix, AZ",
    "url": "https://acmesolar.com"
  },
  "target_audience": {
    "role": "VP of Operations",
    "sector": "Commercial Real Estate",
    "pain_points": [
      "Inverters failing inspection due to wrong firmware",
      "Truck rolls costing $500+ per site visit",
      "Lack of real-time visibility into asset performance"
    ]
  },
  "value_proposition": {
    "core_benefit": "Automated firmware updates and remote diagnostics",
    "metric_proof": "Reduce truck rolls by 40%",
    "software_integration": "ServiceTitan / Procore"
  },
  "offer": {
    "type": "Pilot Program",
    "details": "30-day free usage of the Remote Asset Manager"
  }
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_profile` | Object | Yes | Basic identity of the client we are building the agent *for*. |
| `target_audience` | Object | Yes | Who the agent will be talking *to*. |
| `value_proposition` | Object | Yes | The "Ammo" the agent uses to sell. |
| `offer` | Object | Yes | The Call to Action (CTA). |

## Validation Rules
1.  **No Nulls**: All fields must be populated.
2.  **Pain Points**: Must act as a list of strings (min 1).
3.  **Industry**: Must be specific (e.g., "Commercial Solar" not just "Solar").
