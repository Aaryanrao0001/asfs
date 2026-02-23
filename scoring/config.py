"""Model and scoring configuration."""

MODEL_NAME = "gpt-4o-mini"
ENDPOINT = "https://models.inference.ai.azure.com"

WEIGHTS = {
    "hook": 0.35,
    "retention": 0.25,
    "emotion": 0.20,
    "completion": 0.10,
    "relatability": 0.05,
    "platform": 0.05,
}

HOOK_CAP = 4
EMOTION_CAP = 3
MAX_DURATION = 60

BATCH_SIZE = 5
TEMPERATURE = 0.2
MAX_TOKENS = 2048
