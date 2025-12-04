import json
import os
from typing import List

from pydantic import BaseModel, Field


DEFAULT_SUGGESTIONS: List[str] = [
    "¿Qué conjuntos de datos hay disponibles y cómo se relacionan? Dame un breve resumen.",
    "Muestra los 10 registros principales de una tabla representativa.",
    "¿Cuáles son las principales tendencias o patrones que debería conocer?",
    "Genera una descripción rápida de los cambios recientes en los datos.",
]


class AppConfig(BaseModel):
    """
    Centralized configuration for the Genie Serving App template.

    Values are loaded from environment variables when using `AppConfig.from_env()`,
    with sensible defaults for local development.
    """

    # Branding and labels
    brand_title: str = Field(default="Asistente de IA")
    sidebar_header_text: str = Field(default="Tus conversaciones")
    model_display_name: str = Field(default="Asistente")
    user_display_initial: str = Field(default="Y")
    logout_label: str = Field(default="Cerrar sesión")

    # Welcome content
    welcome_title: str = Field(default="Bienvenido a tu asistente de datos")
    welcome_description: str = Field(
        default="Haz preguntas, explora conjuntos de datos y genera insights."
    )

    # Suggestions: can be overridden via env var, otherwise use generic suggestions
    suggestions: List[str] = Field(
        default_factory=lambda: DEFAULT_SUGGESTIONS.copy()
    )

    # Input/UX text
    input_placeholder: str = Field(default="Haz tu pregunta...")
    disclaimer_text: str = Field(
        default="Revisa siempre la exactitud de las respuestas."
    )

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Build an `AppConfig` instance using environment variables as overrides.

        This preserves the previous behavior where all values were read from `os.environ`
        while now benefiting from Pydantic's validation and `.model_dump()` helpers.
        """
        return cls(
            brand_title=os.environ.get("APP_BRAND_TITLE", "Asistente de IA"),
            sidebar_header_text=os.environ.get(
                "SIDEBAR_HEADER_TEXT", "Tus conversaciones"
            ),
            model_display_name=os.environ.get("MODEL_DISPLAY_NAME", "Asistente"),
            user_display_initial=os.environ.get("USER_DISPLAY_INITIAL", "Y"),
            logout_label=os.environ.get("LOGOUT_LABEL", "Cerrar sesión"),
            welcome_title=os.environ.get(
                "WELCOME_TITLE", "Bienvenido a tu asistente de datos"
            ),
            welcome_description=os.environ.get(
                "WELCOME_DESCRIPTION",
                "Haz preguntas, explora conjuntos de datos y genera insights.",
            ),
            suggestions=cls._load_suggestions_from_env() or DEFAULT_SUGGESTIONS,
            input_placeholder=os.environ.get(
                "INPUT_PLACEHOLDER", "Haz tu pregunta..."
            ),
            disclaimer_text=os.environ.get(
                "DISCLAIMER_TEXT",
                "Revisa siempre la exactitud de las respuestas.",
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
