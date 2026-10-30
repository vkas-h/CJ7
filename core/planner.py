PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "create_plan",
        "description": (
            "Create a short user-facing plan before starting a "
            "multi-step task. Use this only when the user's request "
            "requires multiple meaningful steps."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
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
                                "type": "string"
                            }
                        },
                        "required": [
                            "type",
                            "description"
                        ]
                    },
                    "description": (
                        "2 to 5 concise meaningful task phases. "
                        "Each step must have a type and description."
                    )
                }
            },
            "required": ["steps"]
        }
    }
}