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
