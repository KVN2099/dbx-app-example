Databricks Apps – Reglas básicas y buenas prácticas

Propósito
- Establecer estándares claros y reutilizables para construir Databricks Apps que puedan dar soporte a múltiples casos de uso.
- Garantizar que las Apps sean seguras, configurables, observables y fáciles de desplegar en distintos entornos.

Ámbito
- Se aplica a Apps que utilizan Genie Space (para experiencias conversacionales/agents) y Model Serving (para inferencia online).
- Complementa la guía de proyecto en `templates/instructions.md`.

Principios básicos
1) Configuración primero (Configuration‑First)
   - Todos los valores específicos de entorno deben externalizarse (variables de entorno, secretos o ficheros de configuración). Nada de IDs de workspace, tokens o nombres de catálogos hard‑codeados.
   - Usa la clase de configuración `dbx_apps_config.py` para cargar/validar la configuración.

2) Centradas en Unity Catalog
   - Utiliza Unity Catalog para datos, features, modelos y gobierno.
   - Referencia los assets con nombres totalmente calificados (`<catalog>.<schema>.<name>`).

3) Seguras por defecto (Secure by Default)
   - Almacena las credenciales en Databricks Secrets; nunca en control de versiones.
   - Aplica el principio de mínimo privilegio (service principals, tokens con scope, ACLs de tablas, permisos de modelos).

4) Observabilidad y trazabilidad
   - Registra experimentos y modelos con MLflow; incluye los URIs de run y de modelo en los logs.
   - Emite logs estructurados (JSON siempre que sea posible) e incluye IDs de petición en las llamadas de serving.

5) Paridad de entornos e idempotencia
   - Mantén `dev`, `staging` y `prod` lo más similares posible.
   - Provisiona recursos mediante código/notebooks idempotentes (seguros de re‑ejecutar).

6) Recursos modulares
   - Trata Genie Space y Model Serving como módulos intercambiables con su propia configuración.
   - Evita el acoplamiento fuerte entre la capa de UI/agent y los endpoints de serving.

Guía de arquitectura de Apps
- Núcleo de la App: lógica de negocio, adaptadores a Genie Space y Model Serving, y carga de configuración.
- Capa de recursos:
  - Genie Space para orquestación conversacional, tools y personas.
  - Endpoints de Model Serving para inferencia de baja latencia (LLMs o modelos personalizados).
- Datos y modelos: gestionados en Unity Catalog; versionados mediante Delta/MLflow.

Convenciones de configuración
- Usa `DatabricksAppConfig` desde `dbx_apps_config.py`.
- Admite tres fuentes (en este orden de prioridad):
  1. Variables de entorno (se recomienda el prefijo `APP_`)
  2. Fichero de configuración JSON (en el repo para la estructura, no para secretos)
  3. Defaults programáticos (seguros y no sensibles)

Variables de entorno recomendadas (prefijo `APP_`)
- Workspace y UC: `WORKSPACE_URL`, `CATALOG`, `SCHEMA`, `VOLUME`
- Genie Space: `GENIE_SPACE_ID`, `GENIE_SPACE_NAME`, `GENIE_DEFAULT_PERSONA`, `GENIE_TOOLS` (CSV)
- Model Serving: `SERVING_ENDPOINT`, `SERVING_RATE_LIMIT_RPS`, `SERVING_CONCURRENCY`
- Secrets: `SECRETS_SCOPE` (y los nombres de claves que use tu código)

Seguridad y secretos
- Los access tokens y API keys deben venir de Databricks Secrets o de variables de entorno a nivel de workspace configuradas en Jobs/Apps.
- Nunca registres secretos en bruto. Enmascáralos antes de loguearlos.

Buenas prácticas para Genie Space
- Mantén las tools al mínimo y bien definidas. Solo habilita lo que el space necesite.
- Define una persona por defecto alineada con el propósito de la App.
- Valida el ID/nombre del space en el arranque; falla rápido si está mal configurado.

Buenas prácticas para Model Serving
- Prefiere endpoints con nombre y modelos versionados o reglas de routing.
- Define valores conservadores para rate limits y concurrencia; hazlos configurables por entorno.
- Incluye tiempos de petición/respuesta y códigos de estado en los logs.

Despliegue y operaciones
- Empaqueta la configuración junto con el artefacto desplegable de la App. Evita cambios de código para cambiar de entorno.
- Usa Databricks Workflows (u otro orquestador que prefieras) para aprovisionamiento, smoke tests y rollbacks.
- Añade health checks para los endpoints de serving durante el arranque.

Uso de la clase de configuración
- Importa y carga la configuración al inicio del entrypoint de tu App. Ejemplo:

```python
from templates.databricks_apps.dbx_apps_config import DatabricksAppConfig

config = DatabricksAppConfig.from_env(prefix="APP_")
config.validate()

# Ejemplo: acceso a identificadores unificados de recursos
uc_location = f"{config.catalog}.{config.schema}"
serving_endpoint = config.model_serving.endpoint_name
genie_space_id = config.genie_space.space_id
```

Conjunto mínimo de variables de entorno (por entorno)
```
APP_WORKSPACE_URL=https://<your-workspace-url>
APP_CATALOG=<catalog>
APP_SCHEMA=<schema>
APP_GENIE_SPACE_ID=<space-id>
APP_SERVING_ENDPOINT=<endpoint-name>
```

Quality Gates
- Lint: asegúrate de que no hay errores de linter en los ficheros nuevos/modificados.
- Validación estática de configuración: `config.validate()` es obligatorio en el arranque.
- Guardas en tiempo de ejecución: comprueba la accesibilidad de recursos externos (por ejemplo, salud del endpoint de serving) antes de habilitar el acceso a usuarios.

Documentación
- Mantén este archivo actualizado a medida que la App evolucione.
- Documenta cualquier nuevo campo de configuración requerido/opcional y los comportamientos por defecto.

