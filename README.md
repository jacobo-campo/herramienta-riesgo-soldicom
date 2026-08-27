# Herramienta de riesgo SOLDICOM

Aplicación Streamlit para identificar y priorizar riesgos potenciales de pérdida de competencia en acuerdos verticales entre distribuidores mayoristas y minoristas de combustibles líquidos.

Los datos de referencia continúan en `assets/BASE_EDS.xlsx`. Cada evaluación calculada se registra en una base SQLite local. Google Sheets y las credenciales de Google no son necesarios.

## Requisitos de desarrollo

- Python 3.11.
- `uv` 0.11.x. El archivo de bloqueo fue generado con `uv` 0.11.7.

Instale las dependencias bloqueadas:

```powershell
uv sync --locked
```

El entorno virtual se crea en `.venv/` y no debe incorporarse al repositorio.

## Ejecución en desarrollo

Inicialice y compruebe la base local:

```powershell
uv run python -m history_storage check
```

Inicie Streamlit:

```powershell
uv run streamlit run app.py
```

La aplicación queda disponible en `http://localhost:8501`. En desarrollo, la ruta predeterminada del histórico es `data/historico.sqlite3`; puede cambiarse con `HISTORY_DB_PATH`.

## Gestión de dependencias

`pyproject.toml` y `uv.lock` son las fuentes canónicas. `requirements.txt` se conserva como un archivo generado para herramientas que todavía usan `pip` y no debe editarse manualmente.

Para agregar, eliminar o actualizar una dependencia:

```powershell
uv add nombre-paquete
uv remove nombre-paquete
uv lock --upgrade-package nombre-paquete
uv sync --locked
```

Después de cualquier cambio, regenere el archivo compatible con `pip`:

```powershell
uv export --locked --format requirements-txt --no-hashes --output-file requirements.txt
```

## Exportar el histórico

La exportación produce un CSV UTF-8 con encabezados. En desarrollo:

```powershell
New-Item -ItemType Directory -Force exports
uv run python -m history_storage export --output exports/historico.csv
```

Para seleccionar otra base explícitamente:

```powershell
uv run python -m history_storage export --database C:\ruta\historico.sqlite3 --output exports\historico.csv
```

Desde el contenedor puede dejarse el CSV en el directorio persistente del host:

```bash
docker compose exec -T soldicom /app/.venv/bin/python -m history_storage export --output /app/data/historico.csv
```

## Docker local

El contenedor se ejecuta como el usuario no privilegiado `10001:10001`. El directorio de datos se monta desde el host; Compose no lo crea automáticamente para evitar que quede con un propietario incorrecto.

En PowerShell:

```powershell
New-Item -ItemType Directory -Force data
$env:SOLDICOM_DATA_DIR = (Resolve-Path .\data).Path
docker compose config --quiet
docker compose up --build -d
docker compose ps
Invoke-WebRequest -UseBasicParsing http://localhost:8501/_stcore/health
```

En Linux, prepare primero los permisos:

```bash
install -d -o 10001 -g 10001 -m 750 ./data
export SOLDICOM_DATA_DIR="$(pwd)/data"
docker compose up --build -d
curl -fsS http://127.0.0.1:8501/_stcore/health
```

El arranque ejecuta `python -m history_storage check` antes de iniciar Streamlit. Si la ruta no existe, no es escribible o la base no supera la comprobación, el contenedor termina en lugar de arrancar con un histórico inutilizable.

Para consultar registros y detener la aplicación:

```powershell
docker compose logs --tail 100 soldicom
docker compose down
```

`docker compose down` no elimina el histórico porque es un bind mount. No borre manualmente el directorio configurado en `SOLDICOM_DATA_DIR`.

## Producción en un VPS

La configuración de producción añade Caddy como proxy inverso. Streamlit permanece publicado únicamente en `127.0.0.1:8501`; Caddy expone los puertos TCP `80` y `443`, obtiene el certificado TLS y reenvía las solicitudes a `soldicom:8501`. La aplicación queda pública y no incorpora autenticación; la base SQLite no se publica por HTTP.

Antes de iniciar:

1. Verifique que `srv1935559.hstgr.cloud` resuelva a la IP pública `2.25.121.127`.
2. Permita tráfico entrante TCP en los puertos `22`, `80` y `443` en el firewall de Hostinger.
3. No publique directamente el puerto `8501` en Internet.
4. Cree un usuario administrativo no root con llave SSH y compruebe su acceso en una segunda terminal. Solo después de esa verificación desactive el login directo de root y la autenticación SSH por contraseña.

Desde el repositorio clonado en el VPS:

```bash
cd /opt/vertico/herramienta-riesgo-soldicom
install -d -o 10001 -g 10001 -m 750 /opt/vertico/data
cp .env.example .env
nano .env
```

Establezca en `.env` el nombre real del dominio, sin `https://`:

```dotenv
APP_HOST=127.0.0.1
APP_PORT=8501
SOLDICOM_DATA_DIR=/opt/vertico/data
HISTORY_DB_PATH=/app/data/historico.sqlite3
APP_DOMAIN=srv1935559.hstgr.cloud
```

Valide y levante ambos servicios:

```bash
docker compose -f docker-compose.yml -f compose.production.yml config --quiet
docker compose -f docker-compose.yml -f compose.production.yml up --build -d
docker compose -f docker-compose.yml -f compose.production.yml ps
curl -fsS http://127.0.0.1:8501/_stcore/health
curl -fsS "https://$(sed -n 's/^APP_DOMAIN=//p' .env)/_stcore/health"
```

La URL pública inicial será `https://srv1935559.hstgr.cloud`. Revise los registros si algún servicio no queda saludable:

```bash
docker compose -f docker-compose.yml -f compose.production.yml logs --tail 100 soldicom caddy
```

Para actualizar una instalación existente:

```bash
cd /opt/vertico/herramienta-riesgo-soldicom
git pull --ff-only origin main
docker compose -f docker-compose.yml -f compose.production.yml build --pull
docker compose -f docker-compose.yml -f compose.production.yml up -d --remove-orphans
```

La reconstrucción de la imagen no modifica `/opt/vertico/data`.

## Persistencia y copias de seguridad

SQLite usa también archivos auxiliares `historico.sqlite3-wal` y `historico.sqlite3-shm`. Por eso se monta la carpeta completa `/app/data`, no únicamente el archivo principal. La base debe permanecer en el disco local del VPS; no debe ubicarse sobre NFS, SMB ni otro sistema de archivos de red.

**Persistencia no equivale a backup.** El bind mount evita perder datos cuando se reemplaza un contenedor, pero no protege frente a eliminación accidental, daño del disco o pérdida del VPS. Poner la aplicación en producción sin copias verificadas implica aceptar la pérdida total del histórico ante cualquiera de esos eventos.

Una copia consistente puede hacerse mientras la aplicación está activa con la utilidad `sqlite3` y su comando de backup en línea:

```bash
apt-get update && apt-get install -y sqlite3
install -d -o root -g root -m 700 /opt/vertico/backups
umask 077
backup="/opt/vertico/backups/historico-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
sqlite3 /opt/vertico/data/historico.sqlite3 ".timeout 5000" ".backup '$backup'"
test "$(sqlite3 "$backup" 'PRAGMA integrity_check;')" = "ok"
```

No use `cp` sobre la base mientras la aplicación esté activa. Automatice el backup, defina una retención y copie periódicamente una versión fuera del VPS; una copia en el mismo disco no cubre la pérdida del servidor.

Para restaurar, valide primero la copia, detenga `soldicom`, conserve una copia del estado actual y reemplace la base con el UID/GID `10001:10001`. Elimine únicamente los archivos auxiliares de esa base antes de volver a iniciar:

```bash
sqlite3 /ruta/al/backup.sqlite3 'PRAGMA integrity_check;'
docker compose -f docker-compose.yml -f compose.production.yml stop soldicom
install -o 10001 -g 10001 -m 600 /ruta/al/backup.sqlite3 /opt/vertico/data/historico.sqlite3.restore
mv -f /opt/vertico/data/historico.sqlite3.restore /opt/vertico/data/historico.sqlite3
rm -f /opt/vertico/data/historico.sqlite3-wal /opt/vertico/data/historico.sqlite3-shm
docker compose -f docker-compose.yml -f compose.production.yml up -d soldicom
```

Compruebe después el healthcheck y una exportación del histórico.
