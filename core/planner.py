
PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "create_plan",
        "description": (
            "Create a short user-facing plan before starting a "
            "multi-step task. Use only when multiple meaningful "
            "steps are required. Do not use for simple questions "
            "or a single action."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "tool",
                                    "analysis",
                                    "response"
                                ]
                            },
                            "description": {
                                "type": "string",
                                "minLength": 1
                            }
                        },
                        "required": ["type", "description"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["steps"],
            "additionalProperties": False
        }
    }
}
