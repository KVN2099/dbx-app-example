import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import backoff
import pandas as pd
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from token_minter import TokenMinter, TokenMinterConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class GenieEnvConfig(BaseModel):
    """
    Configuración para el acceso a la API de Genie cargada desde variables de entorno.
    """

    space_id: str = Field(..., description="Identificador del espacio de Genie")
    host: str = Field(..., description="Nombre de host del workspace de Databricks (sin esquema)")

    @classmethod
    def from_env(cls) -> "GenieEnvConfig":
        return cls(
            space_id=os.environ.get("SPACE_ID"),
            host=os.environ.get("DATABRICKS_HOST"),
        )


class GenieAttachmentText(BaseModel):
    content: Optional[str] = None


class GenieAttachmentQuery(BaseModel):
    query: Optional[str] = None


class GenieAttachment(BaseModel):
    attachment_id: Optional[str] = None
    text: Optional[GenieAttachmentText] = None
    query: Optional[GenieAttachmentQuery] = None

    class Config:
        extra = "allow"


class GenieMessage(BaseModel):
    """
    Representación Pydantic de la carga útil de un mensaje de Genie.
    """

    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[GenieAttachment]] = None

    class Config:
        extra = "allow"


class GenieStartConversationResponse(BaseModel):
    """
    Campos mínimos devueltos al iniciar una conversación.
    """

    conversation_id: str
    message_id: str

    class Config:
        extra = "allow"


class GenieQueryResult(BaseModel):
    """
    Envoltorio alrededor de la carga de resultados de consulta de Genie para hacer
    el acceso más seguro.
    """

    statement_response: Dict[str, Any] = Field(default_factory=dict)

    @property
    def data_array(self) -> List[Any]:
        return self.statement_response.get("result", {}).get("data_array", []) or []

    @property
    def schema(self) -> Dict[str, Any]:
        return self.statement_response.get("manifest", {}).get("schema", {}) or {}


# Initialize configuration using Pydantic
env_config = GenieEnvConfig.from_env()

# Default space configuration coming from environment variables
# This preserves the previous single-space behavior.
SPACE_ID = env_config.space_id
DATABRICKS_HOST = env_config.host

# -----------------------------------------------------------------------------
# Genie spaces configuration
# -----------------------------------------------------------------------------
# You can hardcode additional Genie space IDs here so they are available
# in the UI for switching between spaces.
#
# - "default" keeps using the SPACE_ID from the environment (recommended).
# - For "space_1", "space_2", etc., replace the `space_id` values with your
#   actual Genie space IDs.
#
# Example:
#   "space_1": {
#       "label": "Espacio de Ventas",
#       "space_id": "01234567-89ab-cdef-0123-456789abcdef",
#   },
#
GENIE_SPACES: Dict[str, Dict[str, str]] = {
    "default": {
        "label": "Espacio por defecto",
        "space_id": SPACE_ID or "",
    },
    "space_1": {
        "label": "Productos de Cooperación",
        "space_id": "01f0b3810f34181c9b561f4694316e91",
    },
    "space_2": {
        "label": "Operaciones e Indicadores",
        "space_id": "01f0b384679814598a629ec809482273",
    },
    "space_3": {
        "label": "Operaciones de Préstamos",
        "space_id": "01f0b37b4c24127bb0517f1bd6eed2f1",
    },
    "space_4": {
        "label": "Información Pública y Documentos",
        "space_id": "01f0b384beb41fec93b8dccded07b2c1",
    },
    "space_5": {
        "label": "Adquisiciones y Procesos de Compra",
        "space_id": "01f0b383bdc01c46badd5cd6f99807f0",
    },
}


def resolve_space_id(space_key: Optional[str]) -> str:
    """
    Devuelve el space_id efectivo a utilizar a partir de una clave de espacio.

    Si la clave no existe o no tiene space_id configurado, se usa SPACE_ID
    desde las variables de entorno como valor por defecto.
    """
    if space_key and space_key in GENIE_SPACES:
        candidate = GENIE_SPACES[space_key].get("space_id") or ""
        if candidate.strip():
            return candidate
    # Fallback al comportamiento anterior (un solo espacio vía entorno)
    return SPACE_ID

token_minter_config = TokenMinterConfig.from_env()
token_minter = TokenMinter(config=token_minter_config)


class GenieClient:
    def __init__(self, host: str, space_id: str):
        self.host = host
        self.space_id = space_id
        self.update_headers()
        
        self.base_url = f"https://{host}/api/2.0/genie/spaces/{space_id}"
    
    def update_headers(self) -> None:
        """Actualiza las cabeceras con un token fresco desde token_minter"""
        self.headers = {
            "Authorization": f"Bearer {token_minter.get_token()}",
            "Content-Type": "application/json"
        }
    
    @backoff.on_exception(
        backoff.expo,
        Exception,  
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def start_conversation(self, question: str) -> GenieStartConversationResponse:
        """Inicia una nueva conversación con la pregunta proporcionada"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/start-conversation"
        payload = {"content": question}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return GenieStartConversationResponse.parse_obj(response.json())
    
    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def send_message(self, conversation_id: str, message: str) -> GenieMessage:
        """Envía un mensaje de seguimiento a una conversación existente"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages"
        payload = {"content": message}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return GenieMessage.parse_obj(response.json())

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def get_message(self, conversation_id: str, message_id: str) -> GenieMessage:
        """Obtiene los detalles de un mensaje específico"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return GenieMessage.parse_obj(response.json())

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def get_query_result(self, conversation_id: str, message_id: str, attachment_id: str) -> Dict[str, Any]:
        """Obtiene el resultado de la consulta utilizando el endpoint attachment_id"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        parsed = GenieQueryResult.parse_obj(response.json())

        # Maintain the original return structure while leveraging Pydantic parsing
        return {
            "data_array": parsed.data_array,
            "schema": parsed.schema,
        }

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def execute_query(self, conversation_id: str, message_id: str, attachment_id: str) -> Dict[str, Any]:
        """Ejecuta una consulta utilizando el endpoint attachment_id"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/execute-query"
        
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    

    def wait_for_message_completion(self, conversation_id: str, message_id: str, timeout: int = 300, poll_interval: int = 2) -> GenieMessage:
        """
        Espera a que un mensaje alcance un estado terminal (COMPLETED, ERROR, etc.).
        
        Args:
            conversation_id: ID de la conversación
            message_id: ID del mensaje
            timeout: Tiempo máximo de espera en segundos
            poll_interval: Tiempo entre comprobaciones de estado en segundos
            
        Returns:
            El mensaje completado
        """
        
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < timeout:
            message = self.get_message(conversation_id, message_id)
            status = message.status

            if status in ["COMPLETED", "ERROR", "FAILED"]:
                return message
                
            time.sleep(poll_interval)
            attempt += 1
            
        raise TimeoutError(f"Message processing timed out after {timeout} seconds")

def start_new_conversation(
    question: str,
    space_key: Optional[str] = None,
) -> Tuple[Optional[str], Union[str, pd.DataFrame], Optional[str]]:
    """
    Inicia una nueva conversación con Genie.
    
    Args:
        question: La pregunta inicial
        
    Returns:
        Tupla que contiene:
        - conversation_id: El nuevo ID de conversación
        - response: Respuesta en texto o DataFrame
        - query_text: Texto de la consulta SQL si aplica; de lo contrario None
    """
    # Resuelve el espacio en el que se ejecutará la conversación
    space_id = resolve_space_id(space_key)
    client = GenieClient(
        host=DATABRICKS_HOST,
        space_id=space_id,
    )
    
    try:
        # Inicia una nueva conversación
        response = client.start_conversation(question)
        conversation_id = response.conversation_id
        message_id = response.message_id
        
        # Espera a que el mensaje se complete
        complete_message = client.wait_for_message_completion(conversation_id, message_id)
        
        # Procesa la respuesta
        result, query_text = process_genie_response(client, conversation_id, message_id, complete_message)
        
        return conversation_id, result, query_text
        
    except Exception as e:
        return None, f"Lo siento, se ha producido un error: {str(e)}. Inténtalo de nuevo.", None

def continue_conversation(
    conversation_id: str,
    question: str,
    space_key: Optional[str] = None,
) -> Tuple[Union[str, pd.DataFrame], Optional[str]]:
    """
    Envía un mensaje de seguimiento en una conversación existente.
    
    Args:
        conversation_id: ID de la conversación existente
        question: Pregunta de seguimiento
        
    Returns:
        Tupla que contiene:
        - response: Respuesta en texto o DataFrame
        - query_text: Texto de la consulta SQL si aplica; de lo contrario None
    """
    logger.info(f"Continuing conversation {conversation_id} with question: {question[:30]}...")
    
    # Resuelve el espacio en el que se continuará la conversación
    space_id = resolve_space_id(space_key)
    client = GenieClient(
        host=DATABRICKS_HOST,
        space_id=space_id,
    )
    
    try:
        # Envía un mensaje de seguimiento en la conversación existente
        response = client.send_message(conversation_id, question)
        message_id = response.message_id
        
        # Espera a que el mensaje se complete
        complete_message = client.wait_for_message_completion(conversation_id, message_id)
        
        # Procesa la respuesta
        result, query_text = process_genie_response(client, conversation_id, message_id, complete_message)
        
        return result, query_text
        
    except Exception as e:
        # Maneja errores específicos
        if "429" in str(e) or "Too Many Requests" in str(e):
            return "Lo siento, el sistema está experimentando una alta demanda. Inténtalo de nuevo en unos momentos.", None
        elif "Conversation not found" in str(e):
            return "Lo siento, la conversación anterior ha expirado. Vuelve a enviar tu consulta para iniciar una nueva conversación.", None
        else:
            logger.error(f"Error continuing conversation: {str(e)}")
            return f"Lo siento, se ha producido un error: {str(e)}", None

def process_genie_response(
    client: GenieClient,
    conversation_id: str,
    message_id: str,
    complete_message: GenieMessage,
) -> Tuple[Union[str, pd.DataFrame], Optional[str]]:
    """
    Procesa la respuesta de Genie
    
    Args:
        client: Instancia de GenieClient
        conversation_id: ID de la conversación
        message_id: ID del mensaje
        complete_message: Respuesta del mensaje completado
        
    Returns:
        Tupla que contiene:
        - result: Respuesta en texto o DataFrame
        - query_text: Texto de la consulta SQL si aplica; de lo contrario None
    """
    # Comprueba primero los adjuntos
    attachments = complete_message.attachments or []
    for attachment in attachments:
        attachment_id = attachment.attachment_id

        # Si hay contenido de texto en el adjunto, lo devuelve
        if attachment.text and attachment.text.content:
            return attachment.text.content, None

        # Si hay una consulta, obtiene el resultado
        if attachment.query:
            query_text = attachment.query.query or ""
            if not attachment_id:
                continue

            query_result = client.get_query_result(conversation_id, message_id, attachment_id)

            data_array = query_result.get("data_array", [])
            schema = query_result.get("schema", {})
            columns = [col.get("name") for col in schema.get("columns", [])]

            # Si tenemos datos, los devuelve como DataFrame
            if data_array:
                # Si no hay columnas en el esquema, crea columnas genéricas
                if not columns and data_array and len(data_array) > 0:
                    columns = [f"column_{i}" for i in range(len(data_array[0]))]

                df = pd.DataFrame(data_array, columns=columns)
                return df, query_text

    # Si no hay adjuntos o datos en los adjuntos, devuelve el contenido de texto
    if complete_message.content is not None:
        return complete_message.content, None

    return "No hay respuesta disponible", None

def genie_query(
    question: str,
    space_key: Optional[str] = None,
) -> Union[Tuple[str, Optional[str]], Tuple[pd.DataFrame, str]]:
    """
    Punto de entrada principal para consultar a Genie.
    
    Args:
        question: La pregunta que se quiere hacer
        
    Returns:
        Tupla que contiene:
        - (text_response, None) para respuestas de texto
        - (dataframe, sql_query) para respuestas con datos
    """
    try:
        # Inicia una nueva conversación para cada consulta
        conversation_id, result, query_text = start_new_conversation(
            question,
            space_key=space_key,
        )

        # Devolvemos la respuesta tal cual la envía Genie (texto o DataFrame),
        # incluso si en algunos casos pudiera coincidir con la pregunta original.
        return result, query_text
            
    except Exception as e:
        logger.error(f"Error en la conversación: {str(e)}. Inténtalo de nuevo.")
        return f"Lo siento, se ha producido un error: {str(e)}. Inténtalo de nuevo.", None