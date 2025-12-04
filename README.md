## Aplicación Databricks con Genie Space – Plantilla de Vibe‑Code

Este repositorio es una **plantilla de Aplicación Databricks respaldada por Genie Space** que puedes **“vibe codear” desde Cursor**: personalizar el texto de la interfaz, el wiring y el comportamiento de forma conversacional mientras la app habla con Databricks Genie y (opcionalmente) con un endpoint de Model Serving.

Está diseñada como un punto de partida que:
- **Envuelve un Genie Space** como motor principal de razonamiento/consultas.
- **Expone una UI moderna en Dash** que puedes re‑diseñar y ajustar rápidamente.
- **Mantiene la configuración en variables de entorno** para moverte entre dev/stage/prod sin cambios de código.
- **Se integra bien con Cursor + GitHub MCP** para desarrollo y documentación “AI‑native”.

---

## Estructura del proyecto

- **Root**
  - **`README.md`**: Este archivo – documentación de alto nivel, configuración y uso.
  - **`dbx_apps_instructions.md`**: **Buenas prácticas de Databricks Apps** compartidas – configuración, seguridad, uso de UC y guía de despliegue para todas las apps de este workspace.
  - **`genie_serving_app/`**: Implementación real de la app de Genie Space (UI en Dash + cliente de Genie + configuración).

- **`genie_serving_app/`**
  - **`app.py`**: **Punto de entrada** de Dash y UI principal; conecta la entrada del usuario con `genie_room.genie_query`, renderiza el chat, tablas y el botón de “Generar insights”.
  - **`genie_room.py`**: **Cliente y orquestación de Genie Space**:
    - Gestiona OAuth mediante `TokenMinter`.
    - Llama a las APIs REST de Genie Space (iniciar conversación, enviar mensajes, obtener resultados de consultas).
    - Normaliza las respuestas en **texto Markdown** o **Pandas DataFrames** para la UI.
  - **`config.py`**: **`AppConfig`** basado en Pydantic con branding, texto de bienvenida, sugerencias y copy de UX cargado desde variables de entorno (con valores seguros por defecto).
  - **`token_minter.py`**: **`TokenMinter`** basado en Pydantic que usa credenciales OAuth de Databricks para crear y renovar continuamente tokens de API del workspace.
  - **`app.yaml`**: **Manifiesto mínimo de runtime de Databricks App**:
    - Especifica el comando (`python app.py`) y las variables de entorno principales (`SPACE_ID`, `SERVING_ENDPOINT_NAME`).
    - Lo usa Databricks Apps para ejecutar este proyecto como una app.
  - **`requirements.txt`**: Dependencias de **runtime de Python** para la app (Dash, backoff, etc.).
  - **`assets/`**: Ficheros estáticos consumidos por Dash:
    - **`style.css`**: Estilos, layout y tema de la app.
    - **Iconos/Imágenes** (por ejemplo, `genie_logo.png`, `menu_icon.svg`, `send_icon.svg`): Usados para la UI de chat, sidebar y botones.
    - **`table*.png` / imágenes de troubleshooting**: Capturas de ejemplo y otros assets de UI.

---

## Configuración y uso (Cursor + Databricks + MCP)

### 1. Clonar el repo y crear el archivo de entorno

- **Clona el repositorio** en tu máquina local.
- **Crea un archivo de entorno** en la raíz del proyecto (o donde prefieras que Cursor lo lea), a partir de una plantilla:
  - Si ya tienes un `.env.example` en otro lugar, **cópialo aquí** y adáptalo.
  - En caso contrario, crea `.env` manualmente con las claves requeridas (ver “Requisitos y variables de entorno” más abajo).

Cursor (y `python-dotenv` en `app.py` / `genie_room.py` / `token_minter.py`) cargará estas variables cuando ejecutes o depures la app.

### 2. Configurar el servidor GitHub MCP en Cursor

Este proyecto está pensado para ser **operado por IA desde Cursor** usando un **servidor GitHub MCP** (ver la guía oficial [Install GitHub MCP Server in Cursor](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md)):

- En **Cursor → Settings → MCP**:
  - **Activa el servidor GitHub MCP** (si aún no lo está).
  - Asegúrate de que tiene **acceso a este repo** para que el agente pueda:
    - Leer/escribir ficheros.
    - Abrir/modificar PRs.
    - Mantener la documentación (incluido este `README.md`) sincronizada con los cambios.

Esto te permite “vibe codear” la app pidiéndole al agente que:
- Actualice el copy de la UI.
- Añada nuevos callbacks o componentes.
- Ajuste el wiring con Genie/serving.

### 3. Añadir la documentación de Databricks CLI al indexado y a los docs de Cursor

Para obtener **ayuda contextual de alta calidad** mientras modificas la app:

- En **Cursor → Settings → Indexing / Docs** (el nombre puede variar según la versión):
  - **Añade la documentación de Databricks CLI / Databricks** como fuente de documentación, por ejemplo la referencia de comandos [Databricks CLI commands](https://docs.databricks.com/aws/en/dev-tools/cli/commands):
    - Documentación de Databricks CLI y SDK (incluida la referencia de comandos anterior).
    - Documentación de Databricks Apps y Genie Space.
  - Asegúrate de que Cursor puede **usar esos docs** mientras trabajas en este proyecto.

Esto ayuda al agente a responder preguntas como:
- Cómo configurar clientes OAuth.
- Cómo son los endpoints y payloads de Genie Spaces.
- Cómo desplegar Databricks Apps y definir variables de entorno.

### 4. Ejecutar en local

- Crea/activa un entorno de Python (3.10+ recomendado) e instala las dependencias:

```bash
cd "Test Vibe Code App"
python -m venv .venv
source .venv/bin/activate
pip install -r genie_serving_app/requirements.txt
pip install databricks-sdk python-dotenv pandas requests pydantic
```

- Exporta o asegúrate de que `.env` contiene las variables requeridas (ver abajo).
- Ejecuta:

```bash
cd genie_serving_app
python app.py
```

Dash iniciará un servidor local (por defecto `http://127.0.0.1:8050`); ábrelo en un navegador para usar la UI de chat.

### 5. Desplegar como Databricks App

- Asegúrate de que `app.yaml` tiene los valores correctos para **`SPACE_ID`** y **`SERVING_ENDPOINT_NAME`** (o sobrescríbelos mediante variables de entorno del workspace).
- Sigue el flujo de despliegue de **Databricks Apps** de tu workspace:
  - Crea una App apuntando a este repo.
  - Configura **variables de entorno y secretos** en la configuración de la App (ver sección siguiente).
  - Inicia la App y valida su funcionamiento desde el navegador.

Para estándares globales de entorno (UC, secretos, logging, etc.), consulta `dbx_apps_instructions.md`.

---

## Requisitos y variables de entorno

### Python y librerías

- **Python**: se recomienda 3.10+.
- **Dependencias principales** (desde `genie_serving_app/requirements.txt` + runtime):
  - **Dash y ecosistema**: `dash`, `dash-bootstrap-components`, `dash-core-components`, `dash-html-components`, `dash-table`, `dash_ag_grid`, `dash_mantine_components`, `dash-leaflet`, `dash-iconify`
  - **Infra/lógica**: `backoff`, `python-dotenv`, `pydantic`, `pandas`, `requests`, `databricks-sdk`

### Variables de entorno requeridas (conjunto mínimo)

Estas se:
- Cargan desde `.env` mediante `python-dotenv`, o
- Se definen como variables de entorno en Databricks Apps / Jobs.

- **Genie / workspace de Databricks**
  - **`DATABRICKS_HOST`**: Host del workspace **sin esquema**, por ejemplo `my-workspace.cloud.databricks.com`.
  - **`SPACE_ID`**: **ID del Space de Genie** con el que habla esta app (también referenciado en `app.yaml`).
  - **`SERVING_ENDPOINT_NAME`**: (Opcional pero soportado) nombre del endpoint de **Model Serving de Databricks**, usado por `call_llm_for_insights` en `app.py`.

- **Cliente OAuth (para Genie + APIs)**
  - **`DATABRICKS_CLIENT_ID`**: ID de cliente OAuth con acceso a Genie / APIs del workspace.
  - **`DATABRICKS_CLIENT_SECRET`**: Secreto de cliente OAuth.

- **Overrides de UI / branding** (todos opcionales; tienen valores por defecto en `AppConfig`):
  - **`APP_BRAND_TITLE`**: Texto en la barra superior (por ejemplo, “Genie Data Copilot”).
  - **`SIDEBAR_HEADER_TEXT`**: Cabecera del sidebar sobre la lista de conversaciones.
  - **`MODEL_DISPLAY_NAME`**: Etiqueta mostrada junto al avatar del modelo.
  - **`USER_DISPLAY_INITIAL`**: Inicial del avatar del usuario (por defecto `"Y"`).
  - **`LOGOUT_LABEL`**: Texto del botón de cierre de sesión.
  - **`WELCOME_TITLE`**, **`WELCOME_DESCRIPTION`**: Texto destacado de bienvenida.
  - **`DEFAULT_SUGGESTIONS`**: Lista JSON o cadena `q1||q2||q3||q4` con las preguntas sugeridas de bienvenida.
  - **`INPUT_PLACEHOLDER`**, **`DISCLAIMER_TEXT`**: Placeholder del input y nota de descargo bajo el área de entrada.

### Requisitos del lado de Databricks

- Un **Genie Space** configurado con:
  - **Herramientas y acceso a datos** adecuados para tu caso de uso.
  - Permisos para que el cliente OAuth pueda iniciar conversaciones y ejecutar consultas.
- (Opcional) **Endpoint de Model Serving** para `call_llm_for_insights`:
  - Un endpoint con nombre que exponga un LLM o modelo capaz de consumir el prompt tabular en CSV.

---

## Resumen por archivo

- **`dbx_apps_instructions.md`**
  - **Guía global de Databricks Apps**:
    - Config‑first, centrado en UC, seguro por defecto.
    - Cómo usar `DatabricksAppConfig` (si decides introducirlo aquí).
    - Variables de entorno recomendadas, uso de secretos, logging y patrones de despliegue.

- **`genie_serving_app/app.py`**
  - Define el **layout de la app en Dash**: barra de navegación, sidebar, panel de bienvenida, historial de chat, input fijo y modales.
  - Implementa el **grafo de callbacks**:
    - Gestiona los botones de sugerencias y la entrada de texto libre.
    - Llama a `genie_query` y renderiza **Markdown** o **tablas de Dash**.
    - Gestiona sesiones/lista de chats, feedback de pulgar arriba/abajo, estado de consulta en curso y personalización del mensaje de bienvenida.
  - Llama a **Model Serving de Databricks** vía `databricks-sdk` para la funcionalidad tabular de “Generar insights”.

- **`genie_serving_app/genie_room.py`**
  - Implementa **`GenieClient`** con:
    - Refresco de tokens mediante `TokenMinter` en cada llamada.
    - Métodos REST: `start_conversation`, `send_message`, `get_message`, `get_query_result`, `execute_query`, `wait_for_message_completion`.
  - Helpers de alto nivel:
    - `start_new_conversation`, `continue_conversation`, `genie_query`.
    - `process_genie_response` para devolver **texto** o un **`pandas.DataFrame` + SQL**.

- **`genie_serving_app/config.py`**
  - Modelo Pydantic **`AppConfig`**:
    - Centraliza todo el copy de la UI y los valores por defecto de sugerencias.
    - `from_env()` lee valores de variables de entorno y recurre a los defaults documentados cuando faltan.
  - Mantiene el resto del código limpio al concentrar el texto de branding en un solo lugar.

- **`genie_serving_app/token_minter.py`**
  - **`TokenMinterConfig`** basado en Pydantic para cargar la configuración OAuth (opcionalmente con `.from_env()`).
  - **`TokenMinter`**:
    - Llama a `https://<DATABRICKS_HOST>/oidc/v1/token` con client credentials.
    - Almacena un access token y lo renueva automáticamente ~5 minutos antes de su expiración usando un lock.

- **`genie_serving_app/app.yaml`**
  - **Definición mínima de App** para Databricks Apps:
    - Ejecuta `python app.py`.
    - Define **`SPACE_ID`** y **`SERVING_ENDPOINT_NAME`** (sobrescribibles en la UI de configuración de la App).

- **`genie_serving_app/requirements.txt`**
  - Versiones de librerías necesarias para ejecutar la app.

- **`genie_serving_app/assets/`**
  - Carpeta estándar de estáticos de Dash:
    - `style.css` para estilos.
    - Iconos e imágenes usados en la UI.

---

## Ideas de “Vibe Coding” y otros temas

- **Cambiar el tema de la app**:
  - Usa Cursor para modificar `assets/style.css` y los campos de branding de `AppConfig`.
  - Cambia texto/contenido (prompts de bienvenida, disclaimers, etiquetas del sidebar) vía variables de entorno o directamente en `config.py`, y luego pide al agente que propague los cambios.

- **Extender el comportamiento de Genie**:
  - Añade nuevos botones que llamen a `genie_query` con prompts preconfigurados.
  - Extiende `process_genie_response` para obtener metadatos de tabla más ricos o salidas listas para gráficos.

- **Telemetría y logging**:
  - Añade logging estructurado (JSON) en `genie_room.py` y `app.py`.
  - Usa MLflow o tablas en UC para registrar conversaciones/respuestas si necesitas auditoría o analítica.

- **Endurecimiento de despliegue**:
  - Sigue `dbx_apps_instructions.md` para:
    - Paridad entre entornos (dev/stage/prod).
    - Scopes de secretos y control de acceso con principios sólidos.
    - Health checks y smoke tests antes de exponer la app a usuarios finales.

Usa este README como **fuente única de la verdad** sobre cómo está cableada la app de Genie Space y cómo extenderla de forma segura. A medida que personalices el comportamiento, mantén este archivo actualizado para que futuras sesiones de “vibe coding” sigan bien fundamentadas. 

