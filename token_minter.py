import logging
import os
import threading
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class TokenMinterConfig(BaseModel):
    """
    Modelo Pydantic para la configuración del cliente OAuth de Databricks.
    """

    client_id: str = Field(..., description="ID de cliente OAuth de Databricks")
    client_secret: str = Field(..., description="Secreto de cliente OAuth de Databricks")
    host: str = Field(..., description="Nombre de host del workspace de Databricks (sin esquema)")

    @classmethod
    def from_env(cls) -> "TokenMinterConfig":
        """
        Carga la configuración desde variables de entorno.

        Variables esperadas:
        - DATABRICKS_CLIENT_ID
        - DATABRICKS_CLIENT_SECRET
        - DATABRICKS_HOST
        """
        return cls(
            client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
            client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
            host=os.environ.get("DATABRICKS_HOST"),
        )


class TokenMinter:
    """
    Gestiona la generación y renovación de tokens OAuth para Databricks.

    Utiliza `TokenMinterConfig` (Pydantic) para la configuración y
    actualiza el token automáticamente antes de que caduque.
    """

    def __init__(self, config: TokenMinterConfig):
        self.config = config
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.host = config.host
        self.token = None
        self.expiry_time = None
        self.lock = threading.RLock()
        self._refresh_token()
        
    def _refresh_token(self) -> None:
        """Método interno para actualizar el token OAuth"""
        url = f"https://{self.host}/oidc/v1/token"
        auth = (self.client_id, self.client_secret)
        data = {'grant_type': 'client_credentials', 'scope': 'all-apis'}
        
        try:
            response = requests.post(url, auth=auth, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            with self.lock:
                self.token = token_data.get('access_token')
                # Set expiry time to 55 minutes (slightly less than the 60-minute expiry)
                self.expiry_time = datetime.now() + timedelta(minutes=55)
                
            logger.info("Token OAuth de Databricks actualizado correctamente")
        except Exception as e:
            logger.error(f"No se pudo actualizar el token OAuth de Databricks: {str(e)}")
            raise
    
    def get_token(self) -> str:
        """
        Obtiene un token válido, actualizándolo si es necesario.
        
        Returns:
            str: El token OAuth válido actual
        """
        with self.lock:
            # Comprueba si el token ha caducado o está a punto de caducar (en 5 minutos)
            if not self.token or not self.expiry_time or datetime.now() + timedelta(minutes=5) >= self.expiry_time:
                self._refresh_token()
            return self.token