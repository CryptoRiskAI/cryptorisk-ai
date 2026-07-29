"""
test_clustering.py — Tests for the K-Means clustering pipeline.

Function under test: aplicar_clustering(df) → df enriched with:
    Cluster column            — integer in [0, mejor_k - 1]
    df.attrs["mejor_k"]       — int in {2, 3, 4}, selected by highest silhouette
    df.attrs["silhouette"]    — float in [-1.0, 1.0]

The function evaluates k ∈ {2, 3, 4} with random_state=42 and selects the k
that maximises the silhouette score. All cluster assignments use StandardScaler
on the 6 PESOS sub-score columns.

NOTE: tests in this file require at least 2 valid rows to reach the clustering
step. The fixture df_scored in conftest.py provides 10 rows.
"""

import pytest
import pandas as pd

from conftest import make_valid_df
from app import validar_inventario, aplicar_reglas, aplicar_clustering


# ═══════════════════════════════════════════════════════════════════════════
# 1. OUTPUT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

class TestClusterOutputStructure:

    def test_cluster_column_is_added(self, df_scored):
        """
        Purpose:  aplicar_clustering must add a 'Cluster' column to the DataFrame.
        Expected: 'Cluster' key exists in result.columns.
        Why:      The dashboard bar chart and inventory table reference this column
                  by exact name. Its absence raises a KeyError at render time.
        """
        result = aplicar_clustering(df_scored)
        assert "Cluster" in result.columns

    def test_mejor_k_stored_in_attrs(self, df_scored):
        """
        Purpose:  The chosen k must be stored in df.attrs so the dashboard metric
                  card can display it.
        Expected: df.attrs["mejor_k"] exists and is an int.
        Why:      app.py line 184 reads df.attrs["mejor_k"] directly; a missing key
                  raises KeyError and crashes the metric display.
        """
        result = aplicar_clustering(df_scored)
        assert "mejor_k" in result.attrs
        assert isinstance(result.attrs["mejor_k"], int)

    def test_silhouette_stored_in_attrs(self, df_scored):
        """
        Purpose:  The silhouette score must be stored in df.attrs for the metric card.
        Expected: df.attrs["silhouette"] exists and is a float.
        Why:      app.py line 185 reads df.attrs["silhouette"] directly.
        """
        result = aplicar_clustering(df_scored)
        assert "silhouette" in result.attrs
        assert isinstance(result.attrs["silhouette"], float)


# ═══════════════════════════════════════════════════════════════════════════
# 2. CLUSTER LABEL VALIDITY
# ═══════════════════════════════════════════════════════════════════════════

class TestClusterLabelValidity:

    def test_k_is_within_evaluated_range(self, df_scored):
        """
        Purpose:  The selected k must come from the evaluated set {2, 3, 4}.
        Expected: mejor_k ∈ {2, 3, 4}.
        Why:      The algorithm only evaluates these three values; any result outside
                  this range indicates a logic error in the k-selection loop.
        """
        result = aplicar_clustering(df_scored)
        assert result.attrs["mejor_k"] in {2, 3, 4}

    def test_cluster_labels_within_expected_range(self, df_scored):
        """
        Purpose:  Cluster labels must be integers from 0 to mejor_k - 1.
        Expected: min(Cluster) = 0, max(Cluster) = mejor_k - 1.
        Why:      Out-of-range labels would silently corrupt the cluster distribution
                  chart and could make cluster profile descriptions reference non-existent
                  groups.
        """
        result = aplicar_clustering(df_scored)
        k = result.attrs["mejor_k"]
        assert result["Cluster"].min() == 0
        assert result["Cluster"].max() == k - 1

    def test_silhouette_is_in_valid_mathematical_range(self, df_scored):
        """
        Purpose:  The silhouette coefficient is bounded to [-1, 1] by definition.
        Expected: -1.0 ≤ silhouette ≤ 1.0.
        Why:      A value outside this range indicates a bug in the scaling or scoring
                  step that feeds the clustering matrix.
        """
        result = aplicar_clustering(df_scored)
        sil = result.attrs["silhouette"]
        assert -1.0 <= sil <= 1.0

    def test_every_row_has_a_cluster_label(self, df_scored):
        """
        Purpose:  K-Means assigns a label to every sample. No row should be unlabelled.
        Expected: Cluster column has no NaN values.
        Why:      A NaN cluster label causes the bar chart to display a missing series
                  and corrupts the full inventory table.
        """
        result = aplicar_clustering(df_scored)
        assert result["Cluster"].notna().all()


# ═══════════════════════════════════════════════════════════════════════════
# 3. DATA INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════

class TestDataIntegrity:

    def test_row_count_preserved(self, df_scored):
        """
        Purpose:  Clustering assigns a label to every row; no row may be dropped.
        Expected: Output row count equals input row count.
        Why:      A silent row drop would cause the dashboard to show fewer assets
                  than were loaded, with no error message.
        """
        result = aplicar_clustering(df_scored)
        assert len(result) == len(df_scored)

    def test_only_cluster_column_is_added(self, df_scored):
        """
        Purpose:  Clustering must add exactly one new column: 'Cluster'.
        Expected: The set difference between output and input columns is {'Cluster'}.
        Why:      Unexpected extra columns would appear in the full inventory CSV export
                  and could confuse downstream consumers of the download.
        """
        cols_before = set(df_scored.columns)
        result = aplicar_clustering(df_scored)
        new_cols = set(result.columns) - cols_before
        assert new_cols == {"Cluster"}

    def test_existing_scores_are_not_modified(self, df_scored):
        """
        Purpose:  Clustering must not overwrite or alter any existing column values.
        Expected: Score Total column is identical before and after clustering.
        Why:      If clustering modified scores, the Top-10 ranking shown on the
                  dashboard would be inconsistent with the cluster view.
        """
        result = aplicar_clustering(df_scored)
        pd.testing.assert_series_equal(
            df_scored["Score Total"].reset_index(drop=True),
            result["Score Total"].reset_index(drop=True),
        )

    def test_clustering_is_deterministic(self, df_scored):
        """
        Purpose:  Two consecutive calls on the same input must produce identical cluster
                  assignments because KMeans uses random_state=42.
        Expected: Cluster columns from both calls are equal element-by-element.
        Why:      Determinism is a documented design requirement. Non-deterministic
                  clustering would mean two professors evaluating the same CSV see
                  different results, undermining reproducibility claims.
        """
        result1 = aplicar_clustering(df_scored)
        result2 = aplicar_clustering(df_scored)
        pd.testing.assert_series_equal(
            result1["Cluster"].reset_index(drop=True),
            result2["Cluster"].reset_index(drop=True),
        )
