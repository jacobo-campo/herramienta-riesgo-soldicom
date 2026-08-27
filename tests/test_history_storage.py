from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import history_storage as storage


def make_record(index: int = 0, **changes: object) -> storage.HistoryRecord:
    values: dict[str, object] = {
        "evaluation_id": storage.new_evaluation_id(),
        "created_at_utc": f"2026-08-27T19:{index % 60:02d}:00-05:00",
        "puntaje_contractual": 45.25,
        "ajuste_no_competencia_pct": 12.5,
        "puntaje_no_competencia_raw": 0.125,
        "indice_no_competencia": 0.5,
        "gamma_no_competencia": 1 / 3,
        "factor_ajuste_no_competencia": 1.125,
        "puntaje_final": 50.90625,
        "probabilidad_pct": 57.75,
        "semaforo": "RIESGO MEDIO",
        "bucket": "Medio",
        "sicom": f"00{index:04d}",
        "nombre_eds": f"EDS {index}",
        "bandera_eds": "PRUEBA",
        "departamento": "BOGOTA D.C.",
        "municipio": "BOGOTA",
        "numero_competidores": 4,
        "alpha_1": 0.5,
        "alpha_2": 0.5,
        "alpha_3": 0.5,
        "valor_exclusividad": "Sí",
        "valor_tipo_duracion": "Plazo fijo",
        "valor_duracion_meses": 24,
        "valor_penalidades": "No",
        "valor_clausulas_precio": "Sí",
        "valor_control_operativo": "No",
        "valor_sancion_mayorista": "No",
        "valor_datos_compartidos": "Sí",
        "valor_notificacion_tercero": "No",
        "valor_mejora_oferta_mayorista": "Sí",
        "valor_precio_bajo_margen": "No",
        "valor_tribunal_sin_arreglo": "No",
    }
    values.update(changes)
    return storage.HistoryRecord(**values)  # type: ignore[arg-type]


class HistoryStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.database = self.root / "nested" / "historico.sqlite3"

    def test_builder_preserves_all_33_fields_and_rounding(self) -> None:
        evaluation_id = "12345678-1234-4234-9234-123456789abc"
        result = {
            "score_preguntas": 45.123456,
            "ajuste_no_competencia_aplicado": 0.123456789,
            "puntaje_no_competencia": 0.123456789,
            "indice_no_competencia": 0.4987654321,
            "gamma_no_competencia": 1 / 3,
            "factor_ajuste_no_competencia": 1.123456789,
            "score": 50.987654,
            "p": 0.57891234,
            "label": "RIESGO MEDIO",
            "bucket": "Medio",
            "inputs": {
                "exclusividad": "Sí",
                "tipo_duracion": "Plazo fijo",
                "duracion_meses": 24,
                "penalidades": "No",
                "clausulas_precio": "Sí",
                "control_operativo": "No",
                "sancion_mayorista": "No",
                "datos_compartidos": "Sí",
                "notificacion_tercero": "No",
                "mejora_oferta_mayorista": "Sí",
                "precio_bajo_margen": "No",
                "tribunal_sin_arreglo": "No",
            },
        }
        eds_info = {
            "SICOM": "001234",
            "NOMBRE COMERCIAL": "Estación Águila",
            "BANDERA": "PRUEBA",
            "DEPARTAMENTO": "BOGOTA D.C.",
            "MUNICIPIO": "BOGOTA",
            "COMPETIDORES_IDENTIFICADOS": 4,
            "ALPHA_1": 0.123456789,
            "ALPHA_2": 0.234567891,
            "ALPHA_3": 0.345678912,
        }

        record = storage.build_evaluation_record(
            result,
            eds_info,
            evaluation_id=evaluation_id,
            created_at_utc="2026-08-27T19:00:00-05:00",
        )

        self.assertEqual(tuple(record), storage.DATABASE_COLUMNS)
        self.assertEqual(len(record), 33)
        self.assertEqual(record["evaluation_id"], evaluation_id)
        self.assertEqual(record["created_at_utc"], "2026-08-28T00:00:00.000000Z")
        self.assertEqual(record["puntaje_contractual"], 45.1235)
        self.assertEqual(record["ajuste_no_competencia_pct"], 12.345679)
        self.assertEqual(record["puntaje_no_competencia_raw"], 0.12345679)
        self.assertEqual(record["indice_no_competencia"], 0.49876543)
        self.assertEqual(record["gamma_no_competencia"], 0.33333333)
        self.assertEqual(record["factor_ajuste_no_competencia"], 1.12345679)
        self.assertEqual(record["puntaje_final"], 50.9877)
        self.assertEqual(record["probabilidad_pct"], 57.8912)
        self.assertEqual(record["sicom"], "001234")
        self.assertEqual(record["alpha_1"], 0.123457)
        self.assertEqual(record["alpha_2"], 0.234568)
        self.assertEqual(record["alpha_3"], 0.345679)
        self.assertEqual(record["valor_duracion_meses"], 24)
        self.assertTrue(storage.save_evaluation(record, self.database))

    def test_schema_has_33_columns_settings_and_indexes(self) -> None:
        path = storage.initialize_database(self.database)
        result = storage.check_database(path)

        self.assertEqual(len(storage.DATABASE_COLUMNS), 33)
        self.assertEqual(len(storage.CSV_HEADERS), 33)
        self.assertEqual(result.schema_version, 1)
        self.assertEqual(result.journal_mode.lower(), "wal")
        self.assertEqual(result.synchronous, 2)
        self.assertEqual(result.busy_timeout_ms, 5_000)
        self.assertEqual(result.integrity, "ok")
        self.assertEqual(result.row_count, 0)

        with closing(sqlite3.connect(path)) as connection:
            columns = connection.execute("PRAGMA table_info(evaluations)").fetchall()
            indexes = {
                row[1] for row in connection.execute("PRAGMA index_list(evaluations)")
            }

        self.assertEqual(tuple(row[1] for row in columns), storage.DATABASE_COLUMNS)
        self.assertIn("ix_evaluations_created_at", indexes)
        self.assertIn("ix_evaluations_sicom", indexes)

    def test_types_semantics_and_utc_normalization(self) -> None:
        record = make_record(7)
        self.assertTrue(storage.insert_evaluation(record, self.database))

        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute(
                """
                SELECT
                    evaluation_id,
                    created_at_utc,
                    sicom,
                    typeof(puntaje_final),
                    typeof(numero_competidores),
                    typeof(valor_exclusividad)
                FROM evaluations
                """
            ).fetchone()

        self.assertEqual(row[0], record.evaluation_id)
        self.assertEqual(row[1], "2026-08-28T00:07:00.000000Z")
        self.assertEqual(row[2], "000007")
        self.assertEqual(row[3:], ("real", "integer", "text"))

    def test_constraints_reject_invalid_row_and_transaction_rolls_back(self) -> None:
        valid = make_record()
        invalid = replace(valid, evaluation_id=storage.new_evaluation_id(), puntaje_final=101.0)

        self.assertTrue(storage.insert_evaluation(valid, self.database))
        with self.assertRaises(sqlite3.IntegrityError):
            storage.insert_evaluation(invalid, self.database)

        self.assertEqual(storage.count_evaluations(self.database), 1)

        invalid_sicom = replace(
            valid,
            evaluation_id=storage.new_evaluation_id(),
            sicom="   ",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            storage.insert_evaluation(invalid_sicom, self.database)
        self.assertEqual(storage.count_evaluations(self.database), 1)

        invalid_duration = replace(
            valid,
            evaluation_id=storage.new_evaluation_id(),
            valor_duracion_meses=241,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            storage.insert_evaluation(invalid_duration, self.database)
        self.assertEqual(storage.count_evaluations(self.database), 1)

        invalid_duration = replace(
            valid,
            evaluation_id=storage.new_evaluation_id(),
            valor_duracion_meses=241,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            storage.insert_evaluation(invalid_duration, self.database)
        self.assertEqual(storage.count_evaluations(self.database), 1)

    def test_invalid_uuid_and_naive_timestamp_are_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            storage.insert_evaluation(
                replace(make_record(), evaluation_id="not-a-uuid"), self.database
            )
        with self.assertRaises(ValueError):
            storage.insert_evaluation(
                replace(make_record(), created_at_utc="2026-08-27T19:00:00"),
                self.database,
            )
        self.assertEqual(storage.count_evaluations(self.database), 0)

    def test_same_uuid_is_idempotent(self) -> None:
        record = make_record()
        self.assertTrue(storage.insert_evaluation(record, self.database))
        self.assertFalse(storage.insert_evaluation(record, self.database))
        self.assertEqual(storage.count_evaluations(self.database), 1)

    def test_30_threads_can_make_multiple_inserts(self) -> None:
        storage.initialize_database(self.database)

        def insert_batch(worker: int) -> int:
            inserted = 0
            for offset in range(4):
                record = make_record(worker, sicom=f"{worker:04d}-{offset}")
                inserted += storage.insert_evaluation(record, self.database)
            return inserted

        with ThreadPoolExecutor(max_workers=30) as executor:
            inserted = sum(executor.map(insert_batch, range(30)))

        self.assertEqual(inserted, 120)
        self.assertEqual(storage.count_evaluations(self.database), 120)
        self.assertEqual(storage.check_database(self.database).integrity, "ok")

    def test_export_is_utf8_bom_complete_and_ordered(self) -> None:
        later = make_record(2, nombre_eds="Estación Ñandú")
        earlier = make_record(1, nombre_eds="Estación Águila")
        storage.insert_evaluation(later, self.database)
        storage.insert_evaluation(earlier, self.database)

        output = self.root / "exports" / "historico.csv"
        count = storage.export_csv(output, self.database)

        self.assertEqual(count, 2)
        self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
        with output.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))

        self.assertEqual(tuple(rows[0]), storage.CSV_HEADERS)
        self.assertEqual(rows[0][10], "Semáforo")
        self.assertEqual(len(rows[0]), 33)
        self.assertEqual(len(rows[1]), 33)
        self.assertEqual(rows[1][13], "Estación Águila")
        self.assertEqual(rows[2][13], "Estación Ñandú")

    def test_cli_check_and_export(self) -> None:
        self.assertEqual(
            storage.main(["check", "--database", str(self.database)]), 0
        )
        output = self.root / "cli.csv"
        self.assertEqual(
            storage.main(
                [
                    "export",
                    "--output",
                    str(output),
                    "--database",
                    str(self.database),
                ]
            ),
            0,
        )
        self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
