import json
import os
from typing import List

from pydantic import BaseModel, Field


DEFAULT_SUGGESTIONS: List[str] = [
    "What datasets are available and how are they related? Give me a brief summary.",
    "Show the top 10 records from a representative table.",
    "What are key trends or patterns I should know about?",
    "Generate a quick overview of recent changes in the data.",
]


class AppConfig(BaseModel):
    """
    Centralized configuration for the Genie Serving App template.

    Values are loaded from environment variables when using `AppConfig.from_env()`,
    with sensible defaults for local development.
    """

    # Branding and labels
    brand_title: str = Field(default="AI Assistant")
    sidebar_header_text: str = Field(default="Your conversations")
    model_display_name: str = Field(default="Assistant")
    user_display_initial: str = Field(default="Y")
    logout_label: str = Field(default="Logout")

    # Welcome content
    welcome_title: str = Field(default="Welcome to your data assistant")
    welcome_description: str = Field(
        default="Ask questions, explore datasets, and generate insights."
    )

    # Suggestions: can be overridden via env var, otherwise use generic suggestions
    suggestions: List[str] = Field(
        default_factory=lambda: DEFAULT_SUGGESTIONS.copy()
    )

    # Input/UX text
    input_placeholder: str = Field(default="Ask your question...")
    disclaimer_text: str = Field(
        default="Always review the accuracy of responses."
    )

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Build an `AppConfig` instance using environment variables as overrides.

        This preserves the previous behavior where all values were read from `os.environ`
        while now benefiting from Pydantic's validation and `.model_dump()` helpers.
        """
        return cls(
            brand_title=os.environ.get("APP_BRAND_TITLE", "AI Assistant"),
            sidebar_header_text=os.environ.get(
                "SIDEBAR_HEADER_TEXT", "Your conversations"
            ),
            model_display_name=os.environ.get("MODEL_DISPLAY_NAME", "Assistant"),
            user_display_initial=os.environ.get("USER_DISPLAY_INITIAL", "Y"),
            logout_label=os.environ.get("LOGOUT_LABEL", "Logout"),
            welcome_title=os.environ.get(
                "WELCOME_TITLE", "Welcome to your data assistant"
            ),
            welcome_description=os.environ.get(
                "WELCOME_DESCRIPTION",
                "Ask questions, explore datasets, and generate insights.",
            ),
            suggestions=cls._load_suggestions_from_env() or DEFAULT_SUGGESTIONS,
            input_placeholder=os.environ.get(
                "INPUT_PLACEHOLDER", "Ask your question..."
            ),
            disclaimer_text=os.environ.get(
                "DISCLAIMER_TEXT",
                "Always review the accuracy of responses.",
            ),
        )

    @staticmethod
    def _load_suggestions_from_env() -> List[str]:
        raw = os.environ.get("DEFAULT_SUGGESTIONS")
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and all(isinstance(i, str) for i in parsed):
                return parsed
        except Exception:
            # Support a simple delimiter fallback: "q1||q2||q3||q4"
            parts = [p.strip() for p in raw.split("||") if p and p.strip()]
            if len(parts) >= 1:
                return parts
        return []
