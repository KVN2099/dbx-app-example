import json
import os
from typing import List

from pydantic import BaseModel, Field


DEFAULT_SUGGESTIONS: List[str] = [
    "¿Qué conjuntos de datos hay disponibles y cómo se relacionan? Dame un breve resumen.",
    "Muestra los 10 primeros registros de una tabla representativa.",
    "¿Cuáles son las principales tendencias o patrones que debería conocer?",
    "Genera una vista rápida de los cambios recientes en los datos.",
]


class AppConfig(BaseModel):
    """
    Configuración centralizada para la plantilla de Genie Serving App.

    Los valores se cargan desde variables de entorno cuando se usa `AppConfig.from_env()`,
    con valores predeterminados adecuados para desarrollo local.
    """

    # Branding y etiquetas
    brand_title: str = Field(default="Asistente de IA")
    sidebar_header_text: str = Field(default="Tus conversaciones")
    model_display_name: str = Field(default="Asistente")
    user_display_initial: str = Field(default="T")
    logout_label: str = Field(default="Cerrar sesión")

    # Contenido de bienvenida
    welcome_title: str = Field(default="Bienvenido a tu asistente de datos")
    welcome_description: str = Field(
        default="Haz preguntas, explora conjuntos de datos y genera insights."
    )

    # Sugerencias: se pueden sobrescribir vía variable de entorno; en caso contrario se usan sugerencias genéricas
    suggestions: List[str] = Field(
        default_factory=lambda: DEFAULT_SUGGESTIONS.copy()
    )

    # Texto de entrada/UX
    input_placeholder: str = Field(default="Haz tu pregunta...")
    disclaimer_text: str = Field(
        default="Revisa siempre la exactitud de las respuestas."
    )

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Construye una instancia de `AppConfig` usando variables de entorno como
        valores de sobreescritura.

        Esto preserva el comportamiento anterior donde todos los valores se leían
        desde `os.environ`, beneficiándose ahora de la validación de Pydantic y
        de los métodos auxiliares como `.model_dump()`.
        """
        return cls(
            brand_title=os.environ.get("APP_BRAND_TITLE", "Asistente de IA"),
            sidebar_header_text=os.environ.get(
                "SIDEBAR_HEADER_TEXT", "Tus conversaciones"
            ),
            model_display_name=os.environ.get("MODEL_DISPLAY_NAME", "Asistente"),
            user_display_initial=os.environ.get("USER_DISPLAY_INITIAL", "T"),
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
