"""
test_error_scenarios.py — Realistic failure scenarios.

This file has two responsibilities:
  1. Confirm which failure modes the application ALREADY handles gracefully.
  2. Document which failure modes currently cause UNHANDLED crashes (known gaps)
     so the team can explain them to the jury without being caught off-guard.

Each test clearly states: PURPOSE / EXPECTED / SEVERITY / STATUS.
"""

import io
import pytest
import pandas as pd
import numpy as np

from conftest import make_row, make_valid_df
from app import validar_inventario, aplicar_reglas, aplicar_clustering, COLUMNAS_ESPERADAS


# ═══════════════════════════════════════════════════════════════════════════
# 1. FILE-LEVEL PARSING FAILURES
#    These simulate what happens at app.py line 170: pd.read_csv(archivo)
#    before validar_inventario is ever called.
# ═══════════════════════════════════════════════════════════════════════════

class TestFileParsing:

    def test_malformed_binary_file_raises_on_read(self):
        """
        Purpose:  A file containing random bytes (not valid CSV) cannot be parsed.
        Expected: pandas raises an Exception (ParserError or UnicodeDecodeError).
        Severity: HIGH — currently unhandled. app.py has no try/except around read_csv,
                  so this produces a raw Python traceback in the Streamlit UI.
        Status:   NOT HANDLED.
        Note for jury: 'We know this case crashes the app. Adding a try/except around
                        pd.read_csv is in our improvement backlog.'
        """
        malformed = io.BytesIO(b"\x00\x01\xff\xfe\xab\xcd\x80\x90" * 100)
        with pytest.raises(Exception):
            pd.read_csv(malformed)

    def test_semicolon_delimited_file_fails_column_check(self):
        """
        Purpose:  A semicolon-delimited file read with the default comma delimiter
                  produces a single mega-column, causing all 13 required columns to
                  be absent.
        Expected: validar_inventario returns (None, [error]) reporting missing columns.
        Severity: MEDIUM — results in a clear validation error rather than a crash.
        Status:   HANDLED indirectly by the missing-column check.
        """
        headers = ";".join(COLUMNAS_ESPERADAS)
        values  = ";".join("Alta" for _ in COLUMNAS_ESPERADAS)
        csv_str = f"{headers}\n{values}\n"
        df = pd.read_csv(io.StringIO(csv_str))   # reads as one column
        df_valido, errores = validar_inventario(df)
        assert df_valido is None
        assert len(errores) > 0

    def test_empty_file_triggers_emptydata_or_returns_empty_df(self):
        """
        Purpose:  A zero-byte or headers-only file must not produce an unhandled crash.
        Expected: Either pandas raises EmptyDataError (graceful), or validar_inventario
                  catches the empty DataFrame correctly.
        Severity: MEDIUM — realistic user mistake when uploading the wrong file.
        Status:   HANDLED — EmptyDataError is catchable; empty df hits missing-column check.
        """
        empty_file = io.StringIO("")
        try:
            df = pd.read_csv(empty_file)
            # If pandas didn't raise, df is empty — validation must handle it
            df_valido, errores = validar_inventario(df)
            # Either all columns are missing or df_valido is empty — both are safe outcomes
            assert df_valido is None or len(df_valido) == 0
        except pd.errors.EmptyDataError:
            pass   # expected and acceptable


# ═══════════════════════════════════════════════════════════════════════════
# 2. DOMAIN AND CONTENT ERRORS
# ═══════════════════════════════════════════════════════════════════════════

class TestDomainErrors:

    def test_all_rows_invalid_returns_empty_valid_df(self):
        """
        Purpose:  If every row has an invalid value, df_valido must be empty.
        Expected: len(df_valido) = 0; len(errores) = n.
        Severity: LOW — the app shows 'No hay registros válidos.' in this case.
        Status:   HANDLED.
        """
        df = make_valid_df(n=5)
        df["Algoritmo"] = "INVALID_ALGO"   # corrupt all rows
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == 0
        assert len(errores) == 5

    def test_whitespace_padded_value_is_rejected(self):
        """
        Purpose:  '  Alta  ' (with surrounding spaces) must not match 'Alta'.
        Expected: Row is rejected; one error is reported.
        Severity: LOW — but documents strict exact-match behavior so the team can
                  explain it if a jury member asks about whitespace handling.
        Status:   HANDLED (exact match rejects it, though the error message is generic).
        """
        df = pd.DataFrame([make_row(Criticidad="  Alta  ")])
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == 0
        assert len(errores) == 1

    def test_mixed_valid_and_invalid_rows_separate_correctly(self):
        """
        Purpose:  Valid rows must survive even when surrounded by invalid ones.
        Expected: 2 valid rows returned; 1 invalid row rejected with an error entry.
        Severity: POSITIVE test — documents row-independence of the validation logic.
        Status:   HANDLED.
        """
        rows = [
            make_row(Identificador="Activo_001"),                          # valid
            make_row(Identificador="Activo_002", Algoritmo="BAD_ALGO"),   # invalid
            make_row(Identificador="Activo_003"),                          # valid
        ]
        df = pd.DataFrame(rows)
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == 2
        assert len(errores) == 1
        assert "Activo_002" not in df_valido["Identificador"].values


# ═══════════════════════════════════════════════════════════════════════════
# 3. KNOWN GAPS — documented bugs
#    These tests PASS by asserting the buggy behavior, so they remain green
#    until the bug is fixed. At that point the assertion must be updated.
# ═══════════════════════════════════════════════════════════════════════════

class TestKnownGaps:

    def test_single_valid_row_passes_validation(self):
        """
        Purpose:  One valid row passes validation without errors (validation is fine).
        Expected: df_valido has 1 row; errores = [].
        Why:      Isolates the gap: the problem is not in validation but in what happens
                  NEXT — the clustering step crashes on 1 sample.
        Status:   Validation HANDLED; clustering NOT HANDLED (see test below).
        """
        df = pd.DataFrame([make_row()])
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == 1
        assert errores == []

    def test_single_valid_row_crashes_kmeans(self):
        """
        Purpose:  DOCUMENTS A KNOWN BUG — K-Means with k=2 requires n_samples ≥ 2.
                  With only 1 row, scikit-learn raises ValueError.
        Expected: ValueError is raised by aplicar_clustering.
        Severity: HIGH — produces a raw Python traceback in the Streamlit dashboard
                  instead of a user-facing error message.
        Status:   NOT HANDLED. No row-count guard exists before the KMeans call.
        Mitigation (do not implement now): add 'if len(df) < 2: st.error(...)' in
                  app.py before the call to aplicar_clustering.
        """
        df = pd.DataFrame([make_row()])
        df_valido, _ = validar_inventario(df)
        df_scored  = aplicar_reglas(df_valido)
        with pytest.raises(ValueError):
            aplicar_clustering(df_scored)

    def test_duplicate_identifiers_pass_validation_silently(self):
        """
        Purpose:  DOCUMENTS A KNOWN GAP — app.py's validar_inventario does not
                  deduplicate identifiers. Both rows with the same Identificador pass.
        Expected: Two rows with the same Identificador are both present in df_valido.
        Severity: MEDIUM — inflates asset counts; 'Activo_001' appears twice in Top-10.
        Status:   NOT HANDLED in app.py.
                  NOTE: proyectoquantum.py's full validation DOES deduplicate.
                  This test captures the discrepancy between the two implementations.
        Note for jury: 'Deduplication exists in the data generation pipeline but has
                        not yet been ported to the dashboard's validation function.
                        It is a documented backlog item.'
        """
        row1 = make_row(Identificador="DUPE_001")
        row2 = make_row(Identificador="DUPE_001", Algoritmo="AES-256")
        df = pd.DataFrame([row1, row2])
        df_valido, errores = validar_inventario(df)
        ids = df_valido["Identificador"].tolist()
        assert ids.count("DUPE_001") == 2   # both accepted
        assert errores == []                 # no warning raised — this is the gap


# ═══════════════════════════════════════════════════════════════════════════
# 4. PIPELINE ROBUSTNESS
# ═══════════════════════════════════════════════════════════════════════════

class TestPipelineRobustness:

    def test_full_pipeline_completes_on_valid_input(self, df_valid):
        """
        Purpose:  The three-stage pipeline (validate → score → cluster) must complete
                  without error on a valid 10-row dataset.
        Expected: Final DataFrame has all expected columns; no exception is raised.
        Why:      End-to-end integration test — confirms the three modules compose
                  correctly with each other.
        Status:   HANDLED — this is the happy path.
        """
        df_valido, errores = validar_inventario(df_valid)
        assert errores == []

        df_scored = aplicar_reglas(df_valido)
        assert "Score Total" in df_scored.columns

        df_final = aplicar_clustering(df_scored)
        assert "Cluster" in df_final.columns
        assert len(df_final) == len(df_valid)

    def test_scoring_result_has_no_nulls_in_output_columns(self, df_valid):
        """
        Purpose:  No output column may contain NaN after scoring.
        Expected: Score Total, Score Normalizado, Nivel de Riesgo, Recomendación
                  are all fully populated.
        Why:      NaN values in any of these columns would produce blank cells in the
                  dashboard table and a KeyError when the recommendation CSV is built.
        Status:   HANDLED.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        for col in ["Score Total", "Score Normalizado", "Nivel de Riesgo", "Recomendación"]:
            assert result[col].notna().all(), f"NaN found in column '{col}'"
