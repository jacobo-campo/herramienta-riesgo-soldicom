"""Persistencia local y exportacion del historico de evaluaciones.

El modulo usa exclusivamente :mod:`sqlite3` de la biblioteca estandar. Cada
operacion abre y cierra su propia conexion para que las sesiones de Streamlit
no compartan objetos ``Connection`` entre hilos.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sqlite3
import sys
import threading
import uuid
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from numbers import Integral, Real
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
BUSY_TIMEOUT_MS = 5_000
DEFAULT_DB_PATH = Path("data/historico.sqlite3")
DB_PATH_ENV_VAR = "HISTORY_DB_PATH"


DATABASE_COLUMNS = (
    "evaluation_id",
    "created_at_utc",
    "puntaje_contractual",
    "ajuste_no_competencia_pct",
    "puntaje_no_competencia_raw",
    "indice_no_competencia",
    "gamma_no_competencia",
    "factor_ajuste_no_competencia",
    "puntaje_final",
    "probabilidad_pct",
    "semaforo",
    "bucket",
    "sicom",
    "nombre_eds",
    "bandera_eds",
    "departamento",
    "municipio",
    "numero_competidores",
    "alpha_1",
    "alpha_2",
    "alpha_3",
    "valor_exclusividad",
    "valor_tipo_duracion",
    "valor_duracion_meses",
    "valor_penalidades",
    "valor_clausulas_precio",
    "valor_control_operativo",
    "valor_sancion_mayorista",
    "valor_datos_compartidos",
    "valor_notificacion_tercero",
    "valor_mejora_oferta_mayorista",
    "valor_precio_bajo_margen",
    "valor_tribunal_sin_arreglo",
)


CSV_HEADERS = (
    "ID_evaluacion",
    "Fecha y Hora UTC",
    "Puntaje_contractual",
    "Ajuste_no_competencia_%",
    "Puntaje_no_competencia_raw",
    "Indice_no_competencia",
    "Gamma_no_competencia",
    "Factor_ajuste_no_competencia",
    "Puntaje_final",
    "Probabilidad_%",
    "Semáforo",
    "Bucket",
    "SICOM",
    "Nombre_EDS",
    "Bandera_EDS",
    "Departamento",
    "Municipio",
    "Numero_competidores",
    "ALPHA_1",
    "ALPHA_2",
    "ALPHA_3",
    "valor_exclusividad",
    "valor_tipo_duracion",
    "valor_duracion_meses",
    "valor_penalidades",
    "valor_clausulas_precio",
    "valor_control_operativo",
    "valor_sancion_mayorista",
    "valor_datos_compartidos",
    "valor_notificacion_tercero",
    "valor_mejora_oferta_mayorista",
    "valor_precio_bajo_margen",
    "valor_tribunal_sin_arreglo",
)


CREATE_EVALUATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id TEXT NOT NULL PRIMARY KEY
        CHECK (
            length(evaluation_id) = 36
            AND substr(evaluation_id, 9, 1) = '-'
            AND substr(evaluation_id, 14, 1) = '-'
            AND substr(evaluation_id, 19, 1) = '-'
            AND substr(evaluation_id, 24, 1) = '-'
        ),
    created_at_utc TEXT NOT NULL
        CHECK (substr(created_at_utc, -1, 1) = 'Z'),
    puntaje_contractual REAL NOT NULL
        CHECK (puntaje_contractual BETWEEN 0.0 AND 100.0),
    ajuste_no_competencia_pct REAL NOT NULL
        CHECK (ajuste_no_competencia_pct BETWEEN 0.0 AND 100.0),
    puntaje_no_competencia_raw REAL NOT NULL
        CHECK (puntaje_no_competencia_raw BETWEEN 0.0 AND 1.0),
    indice_no_competencia REAL NOT NULL
        CHECK (indice_no_competencia BETWEEN 0.0 AND 1.0),
    gamma_no_competencia REAL NOT NULL
        CHECK (gamma_no_competencia BETWEEN 0.0 AND 1.0),
    factor_ajuste_no_competencia REAL NOT NULL
        CHECK (factor_ajuste_no_competencia BETWEEN 1.0 AND 2.0),
    puntaje_final REAL NOT NULL
        CHECK (puntaje_final BETWEEN 0.0 AND 100.0),
    probabilidad_pct REAL NOT NULL
        CHECK (probabilidad_pct BETWEEN 0.0 AND 100.0),
    semaforo TEXT NOT NULL
        CHECK (semaforo IN ('RIESGO BAJO', 'RIESGO MEDIO', 'RIESGO ALTO')),
    bucket TEXT NOT NULL
        CHECK (bucket IN ('Bajo', 'Medio', 'Alto')),
    sicom TEXT NOT NULL
        CHECK (length(trim(sicom)) > 0),
    nombre_eds TEXT NOT NULL,
    bandera_eds TEXT NOT NULL,
    departamento TEXT NOT NULL,
    municipio TEXT NOT NULL,
    numero_competidores INTEGER NOT NULL
        CHECK (numero_competidores >= 0),
    alpha_1 REAL NOT NULL CHECK (alpha_1 BETWEEN 0.0 AND 1.0),
    alpha_2 REAL NOT NULL CHECK (alpha_2 BETWEEN 0.0 AND 1.0),
    alpha_3 REAL NOT NULL CHECK (alpha_3 BETWEEN 0.0 AND 1.0),
    valor_exclusividad TEXT NOT NULL,
    valor_tipo_duracion TEXT NOT NULL,
    valor_duracion_meses INTEGER NOT NULL
        CHECK (valor_duracion_meses BETWEEN 0 AND 240),
    valor_penalidades TEXT NOT NULL,
    valor_clausulas_precio TEXT NOT NULL,
    valor_control_operativo TEXT NOT NULL,
    valor_sancion_mayorista TEXT NOT NULL,
    valor_datos_compartidos TEXT NOT NULL,
    valor_notificacion_tercero TEXT NOT NULL,
    valor_mejora_oferta_mayorista TEXT NOT NULL,
    valor_precio_bajo_margen TEXT NOT NULL,
    valor_tribunal_sin_arreglo TEXT NOT NULL
) STRICT
"""


INSERT_EVALUATION_SQL = f"""
INSERT INTO evaluations ({", ".join(DATABASE_COLUMNS)})
VALUES ({", ".join("?" for _ in DATABASE_COLUMNS)})
ON CONFLICT(evaluation_id) DO NOTHING
"""


_REAL_FIELDS = {
    "puntaje_contractual",
    "ajuste_no_competencia_pct",
    "puntaje_no_competencia_raw",
    "indice_no_competencia",
    "gamma_no_competencia",
    "factor_ajuste_no_competencia",
    "puntaje_final",
    "probabilidad_pct",
    "alpha_1",
    "alpha_2",
    "alpha_3",
}
_INTEGER_FIELDS = {"numero_competidores", "valor_duracion_meses"}
_TEXT_FIELDS = set(DATABASE_COLUMNS) - _REAL_FIELDS - _INTEGER_FIELDS - {
    "evaluation_id",
    "created_at_utc",
}

_initialization_lock = threading.Lock()
_initialized_paths: set[Path] = set()


class HistoryStorageError(RuntimeError):
    """Error de configuracion o integridad del historico."""


class UnsupportedSchemaVersionError(HistoryStorageError):
    """La base usa una version que esta aplicacion no puede administrar."""


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    evaluation_id: str
    created_at_utc: str
    puntaje_contractual: float
    ajuste_no_competencia_pct: float
    puntaje_no_competencia_raw: float
    indice_no_competencia: float
    gamma_no_competencia: float
    factor_ajuste_no_competencia: float
    puntaje_final: float
    probabilidad_pct: float
    semaforo: str
    bucket: str
    sicom: str
    nombre_eds: str
    bandera_eds: str
    departamento: str
    municipio: str
    numero_competidores: int
    alpha_1: float
    alpha_2: float
    alpha_3: float
    valor_exclusividad: str
    valor_tipo_duracion: str
    valor_duracion_meses: int
    valor_penalidades: str
    valor_clausulas_precio: str
    valor_control_operativo: str
    valor_sancion_mayorista: str
    valor_datos_compartidos: str
    valor_notificacion_tercero: str
    valor_mejora_oferta_mayorista: str
    valor_precio_bajo_margen: str
    valor_tribunal_sin_arreglo: str


@dataclass(frozen=True, slots=True)
class DatabaseCheck:
    path: Path
    schema_version: int
    journal_mode: str
    synchronous: int
    busy_timeout_ms: int
    integrity: str
    row_count: int


def new_evaluation_id() -> str:
    """Genera un identificador canonico para una evaluacion nueva."""

    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """Devuelve la fecha UTC actual en ISO-8601, terminada en ``Z``."""

    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def resolve_database_path(database: str | os.PathLike[str] | None = None) -> Path:
    """Resuelve la ruta explicita, la variable de entorno o el valor por defecto."""

    raw_path = database if database is not None else os.getenv(DB_PATH_ENV_VAR)
    path = Path(raw_path) if raw_path else DEFAULT_DB_PATH
    return path.expanduser().resolve()


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1_000)
    connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _validate_schema(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(evaluations)").fetchall()
    actual_columns = tuple(row[1] for row in table_info)
    if actual_columns != DATABASE_COLUMNS:
        raise HistoryStorageError(
            "El esquema de evaluations no coincide con la version esperada"
        )

    if any(row[2] not in {"TEXT", "REAL", "INTEGER"} for row in table_info):
        raise HistoryStorageError("El esquema contiene tipos SQLite inesperados")


def initialize_database(
    database: str | os.PathLike[str] | None = None,
) -> Path:
    """Crea o valida la base, activa WAL y deja el esquema en version 1."""

    path = resolve_database_path(database)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(_connect(path)) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        if str(journal_mode).lower() != "wal":
            raise HistoryStorageError("SQLite no pudo activar journal_mode=WAL")

        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version not in {0, SCHEMA_VERSION}:
            raise UnsupportedSchemaVersionError(
                f"Version de esquema no soportada: {version}"
            )

        with connection:
            connection.execute(CREATE_EVALUATIONS_TABLE_SQL)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS ix_evaluations_created_at "
                "ON evaluations(created_at_utc)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS ix_evaluations_sicom "
                "ON evaluations(sicom)"
            )
            _validate_schema(connection)
            if version == 0:
                connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    return path


def _ensure_initialized(path: Path) -> None:
    with _initialization_lock:
        if path not in _initialized_paths or not path.exists():
            initialize_database(path)
            _initialized_paths.add(path)


def _canonical_uuid(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("evaluation_id debe ser texto")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as error:
        raise ValueError("evaluation_id no es un UUID valido") from error
    canonical = str(parsed)
    if value.lower() != canonical:
        raise ValueError("evaluation_id debe usar el formato UUID canonico")
    return canonical


def _canonical_utc(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("created_at_utc debe ser texto ISO-8601")

    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError("created_at_utc no es una fecha ISO-8601 valida") from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("created_at_utc debe incluir zona horaria")

    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _record_mapping(record: HistoryRecord | Mapping[str, Any]) -> dict[str, Any]:
    values = asdict(record) if isinstance(record, HistoryRecord) else dict(record)
    expected = set(DATABASE_COLUMNS)
    actual = set(values)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"Campos invalidos; faltantes={missing}, adicionales={extra}")

    values["evaluation_id"] = _canonical_uuid(values["evaluation_id"])
    values["created_at_utc"] = _canonical_utc(values["created_at_utc"])

    for field in _REAL_FIELDS:
        value = values[field]
        if isinstance(value, (str, bytes, bool)) or not isinstance(value, Real):
            raise TypeError(f"{field} debe ser numerico")
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError(f"{field} debe ser finito")
        values[field] = normalized

    for field in _INTEGER_FIELDS:
        value = values[field]
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"{field} debe ser entero")
        values[field] = int(value)

    for field in _TEXT_FIELDS:
        if not isinstance(values[field], str):
            raise TypeError(f"{field} debe ser texto")

    return values


def _text_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def build_evaluation_record(
    res: Mapping[str, Any],
    eds_info: Mapping[str, Any] | None,
    evaluation_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Mapea un resultado de la aplicacion al contrato persistente de 33 campos.

    Los redondeos conservan el historico anterior de Google Sheets. El UUID y
    la fecha pueden suministrarse para que un reintento reconstruya exactamente
    la misma evaluacion; si se omiten, se generan valores nuevos.
    """

    inputs = res.get("inputs", {})
    if not isinstance(inputs, Mapping):
        raise TypeError("res['inputs'] debe ser un mapping")
    eds = eds_info or {}

    record: dict[str, Any] = {
        "evaluation_id": _canonical_uuid(
            evaluation_id if evaluation_id is not None else new_evaluation_id()
        ),
        "created_at_utc": _canonical_utc(
            created_at_utc if created_at_utc is not None else utc_now_iso()
        ),
        "puntaje_contractual": round(
            float(res.get("score_preguntas", res.get("score", 0))), 4
        ),
        "ajuste_no_competencia_pct": round(
            100 * float(res.get("ajuste_no_competencia_aplicado", 0.0)), 6
        ),
        "puntaje_no_competencia_raw": round(
            float(res.get("puntaje_no_competencia", 0.0)), 8
        ),
        "indice_no_competencia": round(
            float(res.get("indice_no_competencia", 0.0)), 8
        ),
        "gamma_no_competencia": round(
            float(res.get("gamma_no_competencia", 0.0)), 8
        ),
        "factor_ajuste_no_competencia": round(
            float(res.get("factor_ajuste_no_competencia", 1.0)), 8
        ),
        "puntaje_final": round(float(res.get("score", 0)), 4),
        "probabilidad_pct": round(100 * float(res.get("p", 0)), 4),
        "semaforo": _text_or_empty(res.get("label", "")),
        "bucket": _text_or_empty(res.get("bucket", "")),
        "sicom": _text_or_empty(eds.get("SICOM", "")),
        "nombre_eds": _text_or_empty(eds.get("NOMBRE COMERCIAL", "")),
        "bandera_eds": _text_or_empty(eds.get("BANDERA", "")),
        "departamento": _text_or_empty(eds.get("DEPARTAMENTO", "")),
        "municipio": _text_or_empty(eds.get("MUNICIPIO", "")),
        "numero_competidores": int(eds.get("COMPETIDORES_IDENTIFICADOS", 0) or 0),
        "alpha_1": round(float(eds.get("ALPHA_1", 0.0) or 0.0), 6),
        "alpha_2": round(float(eds.get("ALPHA_2", 0.0) or 0.0), 6),
        "alpha_3": round(float(eds.get("ALPHA_3", 0.0) or 0.0), 6),
        "valor_exclusividad": _text_or_empty(inputs.get("exclusividad", "")),
        "valor_tipo_duracion": _text_or_empty(inputs.get("tipo_duracion", "")),
        "valor_duracion_meses": int(inputs.get("duracion_meses", 0) or 0),
        "valor_penalidades": _text_or_empty(inputs.get("penalidades", "")),
        "valor_clausulas_precio": _text_or_empty(
            inputs.get("clausulas_precio", "")
        ),
        "valor_control_operativo": _text_or_empty(
            inputs.get("control_operativo", "")
        ),
        "valor_sancion_mayorista": _text_or_empty(
            inputs.get("sancion_mayorista", "")
        ),
        "valor_datos_compartidos": _text_or_empty(
            inputs.get("datos_compartidos", "")
        ),
        "valor_notificacion_tercero": _text_or_empty(
            inputs.get("notificacion_tercero", "")
        ),
        "valor_mejora_oferta_mayorista": _text_or_empty(
            inputs.get("mejora_oferta_mayorista", "")
        ),
        "valor_precio_bajo_margen": _text_or_empty(
            inputs.get("precio_bajo_margen", "")
        ),
        "valor_tribunal_sin_arreglo": _text_or_empty(
            inputs.get("tribunal_sin_arreglo", "")
        ),
    }

    # Esta asercion evita que una futura pregunta se pierda silenciosamente o
    # que el esquema y el constructor diverjan.
    if tuple(record) != DATABASE_COLUMNS:
        raise HistoryStorageError("El builder no coincide con el esquema persistente")
    return record


def insert_evaluation(
    record: HistoryRecord | Mapping[str, Any],
    database: str | os.PathLike[str] | None = None,
) -> bool:
    """Inserta una evaluacion de forma atomica.

    Devuelve ``True`` si se creo la fila y ``False`` si el mismo
    ``evaluation_id`` ya existia. Los demas conflictos de integridad se
    propagan al llamador.
    """

    path = resolve_database_path(database)
    _ensure_initialized(path)
    normalized = _record_mapping(record)
    parameters = tuple(normalized[column] for column in DATABASE_COLUMNS)

    with closing(_connect(path)) as connection:
        with connection:
            cursor = connection.execute(INSERT_EVALUATION_SQL, parameters)
        return cursor.rowcount == 1


def save_evaluation(
    record: HistoryRecord | Mapping[str, Any],
    database: str | os.PathLike[str] | None = None,
) -> bool:
    """Alias de integracion para guardar una evaluacion idempotentemente."""

    return insert_evaluation(record, database)


def count_evaluations(
    database: str | os.PathLike[str] | None = None,
) -> int:
    """Cuenta las evaluaciones guardadas."""

    path = resolve_database_path(database)
    _ensure_initialized(path)
    with closing(_connect(path)) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0])


def check_database(
    database: str | os.PathLike[str] | None = None,
) -> DatabaseCheck:
    """Inicializa y verifica esquema, integridad y configuracion de SQLite."""

    path = resolve_database_path(database)
    _ensure_initialized(path)

    with closing(_connect(path)) as connection:
        _validate_schema(connection)
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        busy_timeout_ms = int(
            connection.execute("PRAGMA busy_timeout").fetchone()[0]
        )
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        row_count = int(
            connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        )

        if version != SCHEMA_VERSION:
            raise UnsupportedSchemaVersionError(
                f"Version de esquema no soportada: {version}"
            )
        if journal_mode.lower() != "wal":
            raise HistoryStorageError("La base no esta operando en modo WAL")
        if synchronous != 2:
            raise HistoryStorageError("La conexion no usa synchronous=FULL")
        if busy_timeout_ms != BUSY_TIMEOUT_MS:
            raise HistoryStorageError("La conexion no usa el busy_timeout esperado")
        if integrity.lower() != "ok":
            raise HistoryStorageError(f"Fallo de integridad SQLite: {integrity}")

        # Adquiere un bloqueo de escritura sin persistir cambios. Esto detecta
        # montajes de solo lectura antes de iniciar Streamlit.
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "UPDATE evaluations SET evaluation_id=evaluation_id WHERE 0"
            )
        finally:
            connection.rollback()

    return DatabaseCheck(
        path=path,
        schema_version=version,
        journal_mode=journal_mode,
        synchronous=synchronous,
        busy_timeout_ms=busy_timeout_ms,
        integrity=integrity,
        row_count=row_count,
    )


def export_csv(
    output: str | os.PathLike[str],
    database: str | os.PathLike[str] | None = None,
) -> int:
    """Exporta una instantanea consistente a CSV UTF-8 con BOM.

    El archivo de destino se reemplaza atomicamente solo despues de completar
    la escritura. Devuelve el numero de filas exportadas.
    """

    path = resolve_database_path(database)
    _ensure_initialized(path)
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.{uuid.uuid4().hex}.tmp")

    query = (
        f"SELECT {', '.join(DATABASE_COLUMNS)} FROM evaluations "
        "ORDER BY created_at_utc, evaluation_id"
    )
    row_count = 0

    try:
        with closing(_connect(path)) as connection:
            cursor = connection.execute(query)
            with temporary_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(CSV_HEADERS)
                for row in cursor:
                    writer.writerow(row)
                    row_count += 1
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary_path, output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return row_count


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Verifica la base SQLite")
    check_parser.add_argument(
        "--database",
        help=f"Ruta de la base (por defecto ${DB_PATH_ENV_VAR} o {DEFAULT_DB_PATH})",
    )

    export_parser = subparsers.add_parser("export", help="Exporta el historico a CSV")
    export_parser.add_argument("--output", required=True, help="Archivo CSV de destino")
    export_parser.add_argument(
        "--database",
        help=f"Ruta de la base (por defecto ${DB_PATH_ENV_VAR} o {DEFAULT_DB_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "check":
            result = check_database(args.database)
            print(
                "OK "
                f"path={result.path} "
                f"schema_version={result.schema_version} "
                f"integrity={result.integrity} "
                f"rows={result.row_count}"
            )
            return 0

        if args.command == "export":
            rows = export_csv(args.output, args.database)
            print(f"OK output={Path(args.output).expanduser().resolve()} rows={rows}")
            return 0
    except (HistoryStorageError, OSError, sqlite3.Error, TypeError, ValueError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
