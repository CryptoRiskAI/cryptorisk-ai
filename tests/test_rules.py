"""
test_rules.py — Tests for the deterministic risk scoring engine.

Function under test: aplicar_reglas(df) → df enriched with:
    Score Total       — integer sum of 6 PESOS sub-scores (max 60)
    Score Normalizado — float in [0, 100]
    Nivel de Riesgo   — "Alto" | "Medio" | "Bajo"
    Recomendación     — non-empty string

Thresholds (from app.py):
    Alto  : Score Normalizado >= 66
    Medio : Score Normalizado >= 33
    Bajo  : Score Normalizado <  33

PESOS max values per dimension (must sum to SCORE_MAXIMO = 60):
    Algoritmo 10 · Criticidad 10 · Sensibilidad 10 ·
    Retención 10 · Exposición 10 · Migración 10
"""

import pytest
import pandas as pd

from conftest import make_row, make_valid_df
from app import aplicar_reglas, validar_inventario, PESOS, SCORE_MAXIMO


# ── Helper: build a 1-row validated DataFrame from field overrides ───────────

def _single(overrides: dict) -> pd.DataFrame:
    """Return a 1-row validated DataFrame constructed from make_row(**overrides)."""
    df = pd.DataFrame([make_row(**overrides)])
    validated, _ = validar_inventario(df)
    return validated


# ═══════════════════════════════════════════════════════════════════════════
# 1. SCORE CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreCalculation:

    def test_maximum_risk_asset_scores_60(self):
        """
        Purpose:  All six dimensions at their highest value must yield Score Total = 60
                  and Score Normalizado = 100.0.
        Expected: RSA-2048(10) + Alta(10) + Secreto(10) + >20(10) + Alta(10) + Alta(10) = 60.
        Why:      The score ceiling anchors the normalization formula. A wrong ceiling
                  propagates a proportional error to every other asset in the system.
        """
        df = _single({"Algoritmo": "RSA-2048", "Criticidad": "Alta",
                      "Sensibilidad": "Secreto", "Retención (años)": ">20",
                      "Exposición": "Alta", "Migración": "Alta"})
        result = aplicar_reglas(df)
        assert result["Score Total"].iloc[0] == 60
        assert result["Score Normalizado"].iloc[0] == 100.0

    def test_minimum_risk_asset_score(self):
        """
        Purpose:  All dimensions at their minimum value must yield the correct floor.
        Expected: PQC(0) + Baja(2) + Público(1) + <5(1) + Baja(2) + Baja(2) = 8 → 13.3.
        Why:      Validates the lower bound; ensures PQC is truly zero-risk as designed.
        """
        df = _single({"Algoritmo": "PQC", "Criticidad": "Baja",
                      "Sensibilidad": "Público", "Retención (años)": "<5",
                      "Exposición": "Baja", "Migración": "Baja"})
        result = aplicar_reglas(df)
        assert result["Score Total"].iloc[0] == 8
        assert result["Score Normalizado"].iloc[0] == pytest.approx(13.3, abs=0.1)

    def test_known_combination_matches_hand_calculation(self):
        """
        Purpose:  Verify an intermediate score against a manual calculation.
        Expected: AES-256(2)+Media(5)+Confidencial(7)+5-10(4)+Media(5)+Baja(2) = 25 → 41.7.
        Why:      End-to-end traceability — proves the formula is not silently altered.
        """
        df = _single({"Algoritmo": "AES-256", "Criticidad": "Media",
                      "Sensibilidad": "Confidencial", "Retención (años)": "5-10",
                      "Exposición": "Media", "Migración": "Baja"})
        result = aplicar_reglas(df)
        assert result["Score Total"].iloc[0] == 25
        assert result["Score Normalizado"].iloc[0] == pytest.approx(41.7, abs=0.1)

    def test_score_normalizado_always_in_0_100(self, df_valid):
        """
        Purpose:  No asset may produce a score outside the 0-100 range.
        Expected: All Score Normalizado values satisfy 0 ≤ x ≤ 100.
        Why:      An out-of-range score would silently mis-classify risk levels.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        assert (result["Score Normalizado"] >= 0).all()
        assert (result["Score Normalizado"] <= 100).all()

    def test_score_total_is_always_integer(self, df_valid):
        """
        Purpose:  Every PESOS value is an integer; their sum must also be integer-valued.
        Expected: Score Total column has no fractional part.
        Why:      Confirms the scoring uses exact integer arithmetic, not floating-point.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        assert (result["Score Total"] == result["Score Total"].astype(int)).all()

    def test_score_total_never_exceeds_score_maximo(self, df_valid):
        """
        Purpose:  Score Total must never exceed SCORE_MAXIMO (60).
        Expected: All Score Total values are ≤ 60.
        Why:      Exceeding the maximum would produce Score Normalizado > 100, breaking charts.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        assert (result["Score Total"] <= SCORE_MAXIMO).all()

    def test_scoring_is_deterministic(self, df_valid):
        """
        Purpose:  Applying the rules twice to the same input must produce identical output.
        Expected: Two calls produce DataFrames that are equal cell-by-cell.
        Why:      Determinism is an explicit design requirement of this project. If the
                  score changes between runs, the prioritization list is unreliable.
        """
        validated, _ = validar_inventario(df_valid)
        result1 = aplicar_reglas(validated)
        result2 = aplicar_reglas(validated)
        pd.testing.assert_frame_equal(result1, result2)


# ═══════════════════════════════════════════════════════════════════════════
# 2. RISK CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class TestRiskClassification:

    def test_alto_threshold(self):
        """
        Purpose:  Score Normalizado = 100 must be classified as 'Alto'.
        Expected: Nivel de Riesgo = 'Alto'.
        Why:      Alto threshold is ≥ 66; 100 is well above it.
        """
        df = _single({"Algoritmo": "RSA-2048", "Criticidad": "Alta",
                      "Sensibilidad": "Secreto", "Retención (años)": ">20",
                      "Exposición": "Alta", "Migración": "Alta"})
        result = aplicar_reglas(df)
        assert result["Nivel de Riesgo"].iloc[0] == "Alto"

    def test_medio_classification(self):
        """
        Purpose:  Score Normalizado ≈ 41.7 (between 33 and 66) must be 'Medio'.
        Expected: Nivel de Riesgo = 'Medio'.
        Why:      Medium-risk assets are the majority in any real inventory; correct
                  classification is essential for meaningful migration planning.
        """
        df = _single({"Algoritmo": "AES-256", "Criticidad": "Media",
                      "Sensibilidad": "Confidencial", "Retención (años)": "5-10",
                      "Exposición": "Media", "Migración": "Baja"})
        result = aplicar_reglas(df)
        assert result["Nivel de Riesgo"].iloc[0] == "Medio"

    def test_bajo_classification(self):
        """
        Purpose:  Score Normalizado ≈ 13.3 (< 33) must be classified as 'Bajo'.
        Expected: Nivel de Riesgo = 'Bajo'.
        Why:      Correctly identifying safe assets avoids unnecessary migration effort.
        """
        df = _single({"Algoritmo": "PQC", "Criticidad": "Baja",
                      "Sensibilidad": "Público", "Retención (años)": "<5",
                      "Exposición": "Baja", "Migración": "Baja"})
        result = aplicar_reglas(df)
        assert result["Nivel de Riesgo"].iloc[0] == "Bajo"

    def test_all_risk_levels_are_valid_strings(self, df_valid):
        """
        Purpose:  Every row in a full dataset must receive one of the three valid levels.
        Expected: Nivel de Riesgo values are a subset of {'Alto', 'Medio', 'Bajo'}.
        Why:      Any value outside these three would break dashboard filters, charts,
                  and the recommendation lookup.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        valid_levels = {"Alto", "Medio", "Bajo"}
        assert set(result["Nivel de Riesgo"].unique()).issubset(valid_levels)


# ═══════════════════════════════════════════════════════════════════════════
# 3. RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

class TestRecommendations:

    def test_every_row_has_a_recommendation(self, df_valid):
        """
        Purpose:  The Recomendación column must be filled for every row, with no
                  null or empty-string values.
        Expected: No NaN, no empty strings.
        Why:      The download CSV and dashboard table both display this column;
                  blank recommendations would look broken to evaluators.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        assert result["Recomendación"].notna().all()
        assert (result["Recomendación"].str.strip() != "").all()

    def test_alto_recommendation_references_mosca(self):
        """
        Purpose:  The high-risk recommendation must reference the Mosca criterion,
                  as stated in Explicacion.md and the project methodology.
        Expected: The word 'Mosca' or 'migración' appears in the recommendation text.
        Why:      This test connects the code output to the documented methodology —
                  it is the kind of check an academic evaluator would perform manually.
        """
        df = _single({"Algoritmo": "RSA-2048", "Criticidad": "Alta",
                      "Sensibilidad": "Secreto", "Retención (años)": ">20",
                      "Exposición": "Alta", "Migración": "Alta"})
        result = aplicar_reglas(df)
        rec = result["Recomendación"].iloc[0]
        assert "Mosca" in rec or "migración" in rec.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 4. OUTPUT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

class TestOutputStructure:

    def test_required_columns_added(self, df_valid):
        """
        Purpose:  The four documented output columns must exist after scoring.
        Expected: All four column names are present.
        Why:      The Streamlit dashboard references them by exact name; a typo here
                  would raise a KeyError at runtime during a demo.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        for col in ["Score Total", "Score Normalizado", "Nivel de Riesgo", "Recomendación"]:
            assert col in result.columns

    def test_row_count_unchanged_by_scoring(self, df_valid):
        """
        Purpose:  Scoring must not drop or duplicate rows.
        Expected: Output row count equals validated input row count.
        Why:      A silent row drop would produce a shorter Top-10 ranking without
                  any error message.
        """
        validated, _ = validar_inventario(df_valid)
        result = aplicar_reglas(validated)
        assert len(result) == len(validated)
