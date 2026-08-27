# Herramienta de riesgo SOLDICOM

Aplicacion Streamlit para identificar y priorizar riesgos potenciales de perdida de competencia en acuerdos verticales entre distribuidores mayoristas y minoristas de combustibles liquidos.

## Requisitos

- Python 3.11.
- `uv` 0.11.x. La version usada para generar el archivo de bloqueo es 0.11.7.

## Preparacion del entorno

```powershell
uv sync --locked
```

El entorno virtual se crea en `.venv/` y no debe incorporarse al repositorio.

## Ejecucion local

```powershell
uv run streamlit run app.py
```

Streamlit publica la aplicacion en `http://localhost:8501`.

## Gestion de dependencias

`pyproject.toml` y `uv.lock` son las fuentes canonicas de dependencias. `requirements.txt` se conserva como archivo generado para herramientas que todavia usan `pip`; no debe editarse manualmente.

Para agregar o eliminar una dependencia:

```powershell
uv add nombre-paquete
uv remove nombre-paquete
```

Para actualizar una dependencia concreta:

```powershell
uv lock --upgrade-package nombre-paquete
uv sync --locked
```

Despues de cualquier cambio de dependencias, regenere el archivo compatible con `pip`:

```powershell
uv export --format requirements-txt --no-hashes --output-file requirements.txt
```

## Credenciales de Google Sheets

La aplicacion conserva el contrato de configuracion de `st.secrets`. Cree el archivo local a partir del ejemplo y reemplace todos los marcadores:

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` esta excluido de Git y de la imagen Docker. No incorpore credenciales reales al repositorio.

## Docker

Construya la imagen:

```powershell
docker build -t herramienta-riesgo-soldicom:local .
```

Ejecute el contenedor con Compose despues de crear `.streamlit/secrets.toml`:

```powershell
$env:STREAMLIT_SECRETS_FILE = (Resolve-Path .streamlit/secrets.toml).Path
docker compose up --build -d
```

La aplicacion queda disponible en `http://localhost:8501`. Para usar otro puerto del host, establezca `APP_PORT` antes de ejecutar Compose. `APP_HOST` usa `127.0.0.1` por defecto; en un VPS puede establecerse en `0.0.0.0` si la aplicacion debe exponerse directamente por el puerto publicado.

`STREAMLIT_SECRETS_FILE` es obligatorio y debe contener una ruta absoluta a un archivo existente. Compose lo carga como una configuracion de solo lectura y el servicio rechaza directorios o rutas invalidas.

Verifique el estado del servicio:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8501/_stcore/health
docker compose ps
docker compose logs soldicom
```

Detenga la aplicacion con:

```powershell
docker compose down
```
