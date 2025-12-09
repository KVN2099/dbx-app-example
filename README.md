## Aplicación Databricks Genie Space – Plantilla Vibe‑Code

Este repositorio es una **plantilla de Databricks App respaldada por un Genie Space** que puedes **“vibe codear” desde Cursor**: personalizar el texto de la UI, el wiring y el comportamiento de forma conversacional mientras la aplicación se comunica con Databricks Genie.

Está diseñada como un punto de partida que:
- **Envuelve un Genie Space** como motor principal de razonamiento/consultas.
- **Expone una UI moderna en Dash** que puedes retocar y re‑tematizar rápidamente.
- **Mantiene la configuración en variables de entorno** para pasar entre dev/stage/prod sin cambios de código.
- **Se integra bien con Cursor + GitHub MCP** para un desarrollo y documentación “AI‑nativos”.

---

## Estructura del proyecto

- **Root**
  - **`README.md`**: Este archivo – documentación de alto nivel, configuración e instrucciones de uso.
  - **`dbx_apps_instructions.md`**: **Buenas prácticas compartidas de Databricks Apps** – configuración, seguridad, uso de UC y guía de despliegue para todas las apps de este workspace.
  - **`genie_serving_app/`**: Implementación real de la app de Genie Space (UI en Dash + cliente de Genie + configuración).

- **`genie_serving_app/`**
  - **`app.py`**: **Punto de entrada** de Dash y UI principal; conecta la entrada del usuario con `genie_room.genie_query`, renderiza el chat, tablas y “Generate Insights”.
  - **`genie_room.py`**: **Cliente de Genie Space + orquestación**:
    - Gestiona OAuth mediante `TokenMinter`.
    - Llama a las APIs REST de Genie Space (iniciar conversación, enviar mensajes, recuperar resultados de consulta).
    - Normaliza las respuestas a **texto Markdown** o **Pandas DataFrames** para la UI.
  - **`config.py`**: **`AppConfig`** basado en Pydantic con branding, texto de bienvenida, sugerencias y copy de UX cargados desde variables de entorno (con valores seguros por defecto).
  - **`token_minter.py`**: **`TokenMinter`** basado en Pydantic que usa las **credenciales OAuth de cliente de Databricks** para acuñar y refrescar continuamente los tokens de API del workspace.
  - **`app.yaml`**: **Manifiesto mínimo de runtime de Databricks App**:
    - Especifica el comando (`python app.py`) y la variable de entorno principal (`SPACE_ID`).
    - Usado por Databricks Apps para ejecutar este proyecto como una app.
  - **`requirements.txt`**: **Dependencias de runtime de Python** de la app (Dash, backoff, etc.).
  - **`assets/`**: Ficheros estáticos consumidos por Dash:
    - **`style.css`**: Estilos globales de la app, layout y tema.
    - **Iconos/Imágenes** (por ejemplo, `genie_logo.png`, `menu_icon.svg`, `send_icon.svg`): Usados en el chat, la barra lateral y los botones.
    - **`table*.png` / imágenes de troubleshooting**: Ejemplos de capturas y assets de UI.

---

## Configuración y uso (Cursor + Databricks + MCP)

### 1. Clonar el repo y crear el fichero de entorno

- **Clona el repositorio** en tu máquina local.
- **Crea un fichero de entorno** en la raíz del proyecto (o donde prefieras que Cursor lo cargue), basado en una plantilla:
  - Si ya tienes un `.env.example` en otro sitio, **cópialo aquí** y adáptalo.
  - En caso contrario, crea `.env` manualmente con las claves requeridas (ver “Requisitos y variables de entorno” más abajo).

Cursor (y `python-dotenv` en `app.py` / `genie_room.py` / `token_minter.py`) cargará estas variables cuando ejecutes o depures la app.

### 2. Configurar el servidor GitHub MCP en Cursor

Este proyecto está pensado para ser **operado por IA a través de Cursor** usando un **servidor GitHub MCP** (consulta la guía oficial [Install GitHub MCP Server in Cursor](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md)):

- En **Cursor → Settings → MCP**:
  - **Activa el servidor GitHub MCP** (si aún no lo está).
  - Asegúrate de que tiene **acceso a este repo** para que el agente pueda:
    - Leer/escribir ficheros.
    - Abrir/modificar PRs.
    - Mantener la documentación (incluido este `README.md`) sincronizada con los cambios.

Esto te permite “vibe codear” la app pidiéndole al agente que:
- Actualice el texto de la UI.
- Añada nuevos callbacks o widgets.
- Ajuste el wiring de Genie y la lógica de backend.

### 3. Añadir la documentación de Databricks CLI al indexado y a los docs de Cursor

Para obtener **ayuda contextual de alta calidad** mientras ajustas la app:

- En **Cursor → Settings → Indexing / Docs** (el nombre puede variar según la versión):
  - **Añade la documentación de Databricks CLI / Databricks** como fuente de documentación, por ejemplo la referencia de CLI [Databricks CLI commands](https://docs.databricks.com/aws/en/dev-tools/cli/commands):
    - Documentación de Databricks CLI y SDK (incluida la referencia anterior de comandos).
    - Documentación de Databricks Apps y Genie Space.
  - Asegúrate de que Cursor puede **usar esa documentación** mientras trabajas en este proyecto.

Esto ayuda al agente a responder preguntas como:
- Cómo configurar clientes OAuth.
- Cómo son los endpoints y payloads de Genie Spaces.
- Cómo desplegar Databricks Apps y configurar variables de entorno.

### 4. Ejecutar en local

- Crea/activa un entorno de Python (se recomienda 3.10+) e instala las dependencias:

```bash
cd "Test Vibe Code App"
python -m venv .venv
source .venv/bin/activate
pip install -r genie_serving_app/requirements.txt
pip install databricks-sdk python-dotenv pandas requests pydantic
```

- Exporta o asegúrate de que `.env` contiene las variables requeridas (ver más abajo).
- Ejecuta:

```bash
cd genie_serving_app
python app.py
```

Dash arrancará un servidor local (por defecto `http://127.0.0.1:8050`); ábrelo en un navegador para usar la UI de chat.

### 5. Desplegar como Databricks App

- Asegúrate de que `app.yaml` tiene el **`SPACE_ID`** correcto (o sobrescríbelo mediante variables de entorno del workspace).
- Sigue el **flujo de despliegue de Databricks Apps** de tu workspace:
  - Crea una App apuntando a este repo.
  - Configura **variables de entorno y secretos** en la configuración de la App (ver siguiente sección).
  - Inicia la App y valídala desde un navegador.

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
- Definen como variables de entorno en Databricks Apps / Jobs.

- **Genie / workspace de Databricks**
  - **`DATABRICKS_HOST`**: Host del workspace **sin esquema**, por ejemplo `my-workspace.cloud.databricks.com`.
  - **`SPACE_ID`**: **Space ID** de Genie con el que habla esta app (también referenciado en `app.yaml`).
  
- **Cliente OAuth (para Genie + APIs)**
  - **`DATABRICKS_CLIENT_ID`**: ID de cliente OAuth con acceso a Genie / APIs del workspace.
  - **`DATABRICKS_CLIENT_SECRET`**: Secreto de cliente OAuth.

- **Overrides de UI / branding** (todos opcionales; si faltan, se usan los valores por defecto de `AppConfig`):
  - **`APP_BRAND_TITLE`**: Texto en la barra de navegación superior (por ejemplo “Genie Data Copilot”).
  - **`SIDEBAR_HEADER_TEXT`**: Cabecera de la barra lateral sobre la lista de conversaciones.
  - **`MODEL_DISPLAY_NAME`**: Etiqueta que se muestra junto al avatar del modelo.
  - **`USER_DISPLAY_INITIAL`**: Inicial del avatar de usuario (por defecto `"T"`).
  - **`LOGOUT_LABEL`**: Texto del botón de cierre de sesión.
  - **`WELCOME_TITLE`**, **`WELCOME_DESCRIPTION`**: Texto principal de bienvenida.
  - **`DEFAULT_SUGGESTIONS`**: Lista JSON o cadena `q1||q2||q3||q4` de prompts de sugerencias de bienvenida.
  - **`INPUT_PLACEHOLDER`**, **`DISCLAIMER_TEXT`**: Placeholder del input y disclaimer bajo el área de entrada.

### Requisitos del lado de Databricks

- Un **Genie Space** configurado con:
  - **Herramientas** y **acceso a datos** adecuados para tu caso de uso.
  - Permisos para que el cliente OAuth pueda iniciar conversaciones y ejecutar consultas.

---

## Resumen archivo por archivo

- **`dbx_apps_instructions.md`**
  - Guías globales de **Databricks Apps**:
    - Config‑first, centrado en UC, seguro por defecto.
    - Cómo usar `DatabricksAppConfig` (si decides introducirlo aquí).
    - Variables de entorno recomendadas, uso de secretos, logging y patrones de despliegue.
  
- **`genie_serving_app/app.py`**
  - Define el **layout de la app Dash**: navbar, barra lateral, panel de bienvenida, historial de chat, input fijo y modales.
  - Implementa el **grafo de callbacks**:
    - Maneja los botones de sugerencias y la entrada de texto libre.
    - Llama a `genie_query` y renderiza **Markdown** o **tablas de Dash**.
    - Gestiona sesiones/lista de chats, feedback de pulgar arriba/abajo, estado de ejecución de consultas y personalización del mensaje de bienvenida.
  - Gestiona todas las interacciones con Genie para análisis conversacional y visualización de tablas.

- **`genie_serving_app/genie_room.py`**
  - Implementa **`GenieClient`** con:
    - Refresco de token vía `TokenMinter` en cada llamada.
    - Métodos REST: `start_conversation`, `send_message`, `get_message`, `get_query_result`, `execute_query`, `wait_for_message_completion`.
  - Helpers de alto nivel:
    - `start_new_conversation`, `continue_conversation`, `genie_query`.
    - `process_genie_response` para devolver **texto o un `pandas.DataFrame` + SQL**.

- **`genie_serving_app/config.py`**
  - Modelo Pydantic **`AppConfig`**:
    - Centraliza todo el copy de la UI y los valores por defecto de sugerencias.
    - `from_env()` extrae valores de variables de entorno y recurre a valores por defecto documentados si faltan.
  - Mantiene el resto del código limpio al concentrar el texto de branding en un único lugar.

- **`genie_serving_app/token_minter.py`**
  - **`TokenMinterConfig`** basado en Pydantic para cargar la configuración OAuth (opcionalmente con `.from_env()`).
  - **`TokenMinter`**:
    - Se comunica con `https://<DATABRICKS_HOST>/oidc/v1/token` usando credenciales de cliente.
    - Almacena un token de acceso y lo renueva automáticamente ~5 minutos antes de que caduque mediante un lock.
  
- **`genie_serving_app/app.yaml`**
  - Definición mínima de **App para Databricks Apps**:
    - Ejecuta `python app.py`.
    - Define **`SPACE_ID`** (puede sobrescribirse en la UI de configuración de la App).
  
- **`genie_serving_app/requirements.txt`**
  - Versiones de librerías principales necesarias para ejecutar la app.
  
- **`genie_serving_app/assets/`**
  - Carpeta estática estándar de Dash:
    - `style.css` para estilos.
    - Iconos e imágenes usados en la UI.

---

## Ideas de “Vibe Coding” / Otros temas

- **Cambiar el tema de la app**:
  - Usa Cursor para modificar `assets/style.css` y los campos de branding de `AppConfig`.
  - Cambia el texto/contenido (prompts de bienvenida, disclaimers, etiquetas de la barra lateral) mediante variables de entorno o directamente en `config.py`, y luego pide al agente que propague los cambios.
  
- **Extender el comportamiento de Genie**:
  - Añade nuevos botones que llamen a `genie_query` con prompts predefinidos.
  - Extiende `process_genie_response` para obtener metadatos de tabla más ricos o salidas listas para gráficas.
  
- **Telemetría y logging**:
  - Conecta logging estructurado (JSON) en `genie_room.py` y `app.py`.
  - Usa MLflow o tablas en UC para seguir conversaciones/respuestas si necesitas auditoría o analítica.
  
- **Endurecimiento del despliegue**:
  - Sigue `dbx_apps_instructions.md` para:
    - Paridad entre entornos (dev/stage/prod).
    - Scopes de secretos y control de acceso basado en principios.
    - Health checks y smoke tests antes de exponer a usuarios finales.
  
Usa este README como **única fuente de verdad** sobre cómo está cableada la app de Genie Space y cómo extenderla de forma segura. A medida que personalices el comportamiento, mantén este archivo actualizado para que futuras sesiones de “vibe coding” sigan bien fundamentadas. 


