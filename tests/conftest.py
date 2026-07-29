"""
conftest.py — Shared setup, helpers, and fixtures for the CryptoRisk AI test suite.

WHY THE STREAMLIT MOCK IS NECESSARY
------------------------------------
app.py executes Streamlit calls at module level (set_page_config, title, sidebar,
file_uploader). Importing the file outside a running Streamlit server would crash the
test runner. By replacing the 'streamlit' entry in sys.modules with a MagicMock before
the import, all st.* calls become silent no-ops. Crucially, file_uploader is set to
return None so the UI branch (if archivo is not None:) is never entered, and the pure-
Python functions — validar_inventario, aplicar_reglas, aplicar_clustering — are
imported cleanly without any modification to the application code.

This is the MINIMUM required intervention: zero changes to app.py.
"""

import sys
import os
from unittest.mock import MagicMock

# ── Mock streamlit BEFORE any import from app.py ────────────────────────────
_mock_st = MagicMock()
_mock_st.sidebar.file_uploader.return_value = None  # keeps the UI branch inactive
sys.modules["streamlit"] = _mock_st

# ── Make modelo/ importable without a package prefix ────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modelo"))

import pytest
import pandas as pd
import numpy as np

from app import (
    validar_inventario,
    aplicar_reglas,
    aplicar_clustering,
    PESOS,
    COLUMNAS_ESPERADAS,
    DOMINIOS_VALIDOS,
    SCORE_MAXIMO,
)


# ── Data helpers (used by tests directly, not as fixtures) ───────────────────

def make_row(**overrides) -> dict:
    """Return one fully valid asset row as a dict. Override any field as needed.

    Note: 'Retención (años)' contains a non-ASCII character and a space, so it
    cannot be a Python keyword argument. Use the unpacking form:
        make_row(**{"Retención (años)": "<5"})
    """
    base = {
        "Identificador":            "Activo_001",
        "Tipo de activo":           "Certificado digital",
        "Servicio":                 "TLS",
        "Uso criptográfico":        "Cifrado en tránsito",
        "Algoritmo":                "RSA-2048",
        "Tamaño de clave":          "2048 bits",
        "Exposición":               "Alta",
        "Criticidad":               "Alta",
        "Sensibilidad":             "Secreto",
        "Retención (años)":         ">20",
        "Dependencia de proveedor": "Alta",
        "Migración":                "Alta",
        "Vigencia":                 "Vigente",
    }
    base.update(overrides)
    return base


def make_valid_df(n: int = 10, start_id: int = 1) -> pd.DataFrame:
    """Return a valid DataFrame with n rows and unique identifiers.

    Cycles through algorithms and risk levels to produce realistic variation,
    which is important for K-Means to find meaningful cluster structure.
    """
    algos = list(PESOS["Algoritmo"].keys())   # 5 values
    crits = list(PESOS["Criticidad"].keys())  # 3 values
    expos = list(PESOS["Exposición"].keys())  # 3 values
    rets  = list(PESOS["Retención (años)"].keys())  # 4 values

    rows = []
    for i in range(n):
        rows.append(make_row(
            Identificador=f"Activo_{start_id + i:03d}",
            Algoritmo=algos[i % len(algos)],
            Criticidad=crits[i % len(crits)],
            Exposición=expos[i % len(expos)],
            **{"Retención (años)": rets[i % len(rets)]},
        ))
    return pd.DataFrame(rows)


# ── Pytest fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def df_valid() -> pd.DataFrame:
    """A small (10-row) fully valid inventory DataFrame."""
    return make_valid_df(n=10)


@pytest.fixture
def df_validated(df_valid) -> pd.DataFrame:
    """The 10-row DataFrame after passing through validar_inventario."""
    validated, _ = validar_inventario(df_valid)
    return validated


@pytest.fixture
def df_scored(df_validated) -> pd.DataFrame:
    """The validated DataFrame after scoring rules have been applied."""
    return aplicar_reglas(df_validated)


@pytest.fixture
def df_clustered(df_scored) -> pd.DataFrame:
    """The scored DataFrame after K-Means clustering has been applied."""
    return aplicar_clustering(df_scored)
