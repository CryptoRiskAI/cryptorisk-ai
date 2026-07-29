"""
test_validation.py — Tests for the inventory validation layer.

Function under test: validar_inventario(df) → (df_valido | None, list[str])

The function performs three checks in order:
  1. Schema check  — all 13 required columns must be present
  2. Domain check  — every categorical cell must match its allowed values
  3. Null check    — no required cell may be null or NaN

A failing schema check returns (None, errors) immediately.
Failing domain/null rows are excluded from df_valido; the rest pass through.
"""

import pytest
import pandas as pd
import numpy as np

from conftest import make_row, make_valid_df
from app import validar_inventario, COLUMNAS_ESPERADAS, DOMINIOS_VALIDOS


# ═══════════════════════════════════════════════════════════════════════════
# 1. HAPPY PATH
# ═══════════════════════════════════════════════════════════════════════════

class TestValidInventory:

    def test_all_valid_rows_pass(self, df_valid):
        """
        Purpose:  A well-formed inventory must pass with zero errors.
        Expected: df_valido has the same row count as the input; errores is [].
        Why:      Baseline smoke test. If this fails, every other result is suspect.
        """
        df_valido, errores = validar_inventario(df_valid)
        assert len(df_valido) == len(df_valid)
        assert errores == []

    def test_all_required_columns_present_in_output(self, df_valid):
        """
        Purpose:  Validation must not drop or rename any column.
        Expected: All 13 required columns survive in df_valido.
        Why:      Scoring and clustering reference columns by their exact names.
        """
        df_valido, _ = validar_inventario(df_valid)
        for col in COLUMNAS_ESPERADAS:
            assert col in df_valido.columns, f"Column '{col}' is missing from output"

    def test_index_is_reset_in_output(self, df_valid):
        """
        Purpose:  The output index must start at 0 and be contiguous.
        Expected: df_valido.index equals RangeIndex(0, n).
        Why:      Streamlit dataframes and downstream .iloc calls expect a clean index.
        """
        df_valido, _ = validar_inventario(df_valid)
        assert list(df_valido.index) == list(range(len(df_valido)))


# ═══════════════════════════════════════════════════════════════════════════
# 2. MISSING COLUMNS
# ═══════════════════════════════════════════════════════════════════════════

class TestMissingColumns:

    def test_missing_one_column_returns_none(self, df_valid):
        """
        Purpose:  A missing required column is a hard schema failure.
        Expected: df_valido is None; errores is non-empty.
        Why:      Returning an empty DataFrame here would silently score 0
                  for every asset — wrong output is worse than no output.
        """
        df_broken = df_valid.drop(columns=["Algoritmo"])
        df_valido, errores = validar_inventario(df_broken)
        assert df_valido is None
        assert len(errores) > 0

    def test_missing_column_error_names_the_column(self, df_valid):
        """
        Purpose:  The error message must name the missing column.
        Expected: 'Criticidad' appears in the error string.
        Why:      An evaluator or end-user needs actionable feedback, not a generic message.
        """
        df_broken = df_valid.drop(columns=["Criticidad"])
        _, errores = validar_inventario(df_broken)
        assert any("Criticidad" in e for e in errores)

    def test_missing_multiple_columns_all_reported_at_once(self, df_valid):
        """
        Purpose:  All missing columns must be reported in a single error pass.
        Expected: Both 'Algoritmo' and 'Exposición' appear in the combined error output.
        Why:      Users should not need to fix one column, re-upload, and discover the next.
        """
        df_broken = df_valid.drop(columns=["Algoritmo", "Exposición"])
        _, errores = validar_inventario(df_broken)
        combined = " ".join(errores)
        assert "Algoritmo" in combined
        assert "Exposición" in combined


# ═══════════════════════════════════════════════════════════════════════════
# 3. INVALID CATEGORICAL VALUES
# ═══════════════════════════════════════════════════════════════════════════

class TestInvalidCategoricalValues:

    def test_unknown_algorithm_rejects_row(self, df_valid):
        """
        Purpose:  'RSA-4096' is not in PESOS["Algoritmo"]; the row must be rejected.
        Expected: df_valido has one fewer row; one error is reported.
        Why:      If an unknown algorithm reached scoring, PESOS[col][value] would
                  raise KeyError and crash the entire application silently mid-run.
        """
        df = df_valid.copy()
        df.loc[0, "Algoritmo"] = "RSA-4096"
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 1
        assert len(errores) == 1

    def test_invalid_criticidad_rejects_row(self, df_valid):
        """
        Purpose:  'Muy Alta' is not in the Criticidad domain.
        Expected: That row is rejected; the rest pass.
        Why:      Same KeyError risk as above — all PESOS lookups must be guarded by domain checks.
        """
        df = df_valid.copy()
        df.loc[0, "Criticidad"] = "Muy Alta"
        df_valido, _ = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 1

    def test_error_message_identifies_the_bad_column(self, df_valid):
        """
        Purpose:  The error must name the column that failed domain validation.
        Expected: 'Sensibilidad' appears in the error string for a bad Sensibilidad value.
        Why:      Actionable error messages reduce the time to fix real-world data.
        """
        df = df_valid.copy()
        df.loc[0, "Sensibilidad"] = "Ultra Secreto"
        _, errores = validar_inventario(df)
        assert any("Sensibilidad" in e for e in errores)

    def test_multiple_invalid_rows_all_reported(self, df_valid):
        """
        Purpose:  Validation must scan every row, not stop at the first error.
        Expected: All three invalid rows appear in errores; three valid rows are lost.
        Why:      Stopping at the first error forces repeated upload cycles to fix the same file.
        """
        df = df_valid.copy()
        df.loc[0, "Algoritmo"]  = "UNKNOWN"
        df.loc[1, "Criticidad"] = "UNKNOWN"
        df.loc[2, "Exposición"] = "UNKNOWN"
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 3
        assert len(errores) == 3

    def test_case_sensitive_value_is_rejected(self, df_valid):
        """
        Purpose:  'alta' (lowercase) must not pass — domain matching is case-sensitive.
        Expected: Row is rejected with one error.
        Why:      CSV exports from different tools often change casing; this documents
                  the strict matching behavior so the team can explain it to the jury.
        """
        df = df_valid.copy()
        df.loc[0, "Criticidad"] = "alta"
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 1
        assert len(errores) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 4. NULL VALUES
# ═══════════════════════════════════════════════════════════════════════════

class TestNullValues:

    def test_none_in_required_column_rejects_row(self, df_valid):
        """
        Purpose:  A Python None in a required column must reject the row.
        Expected: df_valido has one fewer row.
        Why:      PESOS[col][None] raises KeyError; the null check must fire first.
        """
        df = df_valid.copy()
        df.loc[0, "Criticidad"] = None
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 1
        assert len(errores) == 1

    def test_nan_in_required_column_rejects_row(self, df_valid):
        """
        Purpose:  np.nan (how pandas internally represents missing values) must be
                  treated identically to None.
        Expected: Row is rejected with one error.
        Why:      pd.isnull() catches both; this test confirms the implementation uses it.
        """
        df = df_valid.copy()
        df.loc[0, "Algoritmo"] = np.nan
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid) - 1
        assert len(errores) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 5. EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_extra_columns_are_accepted(self, df_valid):
        """
        Purpose:  Real-world inventories often carry extra metadata columns.
        Expected: Validation passes; extra columns are preserved in df_valido.
        Why:      The app should be permissive on input (accept extras) and strict on
                  output (require the 13 mandatory columns).
        """
        df = df_valid.copy()
        df["metadata_extra"] = "some value"
        df_valido, errores = validar_inventario(df)
        assert len(df_valido) == len(df_valid)
        assert errores == []
        assert "metadata_extra" in df_valido.columns

    def test_empty_dataframe_does_not_crash(self):
        """
        Purpose:  A CSV with only headers and no data rows must not crash the application.
        Expected: Returns an empty df_valido (not None) with no errors.
        Why:      Empty uploads are a realistic demo scenario. A crash would be
                  particularly embarrassing because the app itself shows an empty-state
                  message — the user should never see a traceback.
        """
        df_empty = pd.DataFrame(columns=COLUMNAS_ESPERADAS)
        df_valido, errores = validar_inventario(df_empty)
        assert df_valido is not None
        assert len(df_valido) == 0
        assert errores == []

    def test_duplicate_identifiers_both_pass_through(self, df_valid):
        """
        Purpose:  DOCUMENTS A KNOWN GAP — app.py does not deduplicate identifiers.
        Expected: Both rows with the same Identificador are accepted as valid.
        Why:      This test captures the current behavior so the team can explain it
                  to the jury. The full validation in proyectoquantum.py DOES deduplicate;
                  app.py currently does not. This is a documented backlog item.
        """
        df = df_valid.copy()
        df.loc[0, "Identificador"] = df.loc[1, "Identificador"]  # force a duplicate
        df_valido, errores = validar_inventario(df)
        dup_id = df.loc[1, "Identificador"]
        assert df_valido["Identificador"].tolist().count(dup_id) == 2
        assert errores == []  # no warning is raised — this is the gap
