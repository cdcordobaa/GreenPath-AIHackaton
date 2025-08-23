AFFECTED_TO_TRIGGERS_JSON = {
  "type": "object",
  "properties": {
    "summary_by_theme": {"type": "array", "items": {"type": "object"}},
    "legal_triggers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "trigger": {"type": "string"},
          "context": {"type": "string"},
          "priority": {"type": "string"}
        },
        "required": ["trigger","context","priority"]
      }
    }
  },
  "required": ["legal_triggers"]
}

LEGAL_REQUIREMENTS_JSON = {
  "type": "object",
  "properties": {
    "requirements": {
      "type":"array",
      "items": {
        "type":"object",
        "properties": {
          "ref":{"type":"string"},
          "action":{"type":"string"},
          "when":{"type":"string"},
          "docs":{"type":"array","items":{"type":"string"}},
          "risk":{"type":"string"}
        },
        "required":["ref","action"]
      }
    }
  },
  "required": ["requirements"]
}


