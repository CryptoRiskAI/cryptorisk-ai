# CryptoRisk AI

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)

A post-quantum cryptographic risk assessment tool that scores, clusters, and prioritizes cryptographic assets for migration readiness.

---

## Overview

CryptoRisk AI evaluates a synthetic inventory of cryptographic assets against the threat of quantum computing, specifically the risk of *harvest now, decrypt later* (HNDL) attacks. For each asset, it applies a deterministic scoring model across six risk dimensions — including algorithm vulnerability to Shor's algorithm and network exposure — to produce an explainable, normalized risk score. Assets are then grouped using K-Means clustering to support migration planning.

The project was developed as an academic MVP for the Cyber Quantum Summer School.

---

## Features

- **Dataset validation** — enforces a 13-column schema and validates categorical values against defined domains before any analysis runs
- **Deterministic risk scoring** — computes a weighted risk score across six dimensions, normalized to a 0–100 scale, with no randomness or ML model involved in the scoring itself
- **Risk classification** — classifies each asset as High, Medium, or Low risk based on score thresholds
- **K-Means clustering** — groups assets by risk profile, automatically selecting the optimal number of clusters (k = 2, 3, or 4) using the silhouette score
- **Interactive dashboard** — Streamlit application displaying key metrics, a top-10 highest-risk ranking, risk and cluster distribution charts, and a full inventory table
- **Migration recommendations** — generates a deterministic textual recommendation for each asset based on its risk level, referencing the Mosca model (x + y > z) as a prioritization criterion
- **Results export** — downloads the scored and clustered inventory as a CSV file
- **Synthetic data generation** — reproducible generator (seed = 42) that produces a 60-asset inventory for testing and demonstration

---

## Project Structure

```
cryptorisk-ai/
├── .github/
│   └── workflows/
│       └── tests.yml              # CI pipeline (GitHub Actions, ubuntu-latest)
├── LICENSE
├── README.md
├── pytest.ini                     # pytest configuration
├── requirements.txt               # Pinned dependencies
├── data/
│   └── README.md                  # Dataset documentation and licensing
├── modelo/
│   ├── app.py                     # Streamlit dashboard — main application entry point
│   ├── inventario_sintetico.csv   # Pre-built synthetic 60-asset dataset (seed=42)
│   ├── proyectoquantum.py         # Synthetic data generator, validation, scoring, clustering
│   ├── Explicacion.md             # Technical methodology notes (Spanish)
│   └── test.py                    # Streamlit smoke test
└── tests/
    ├── conftest.py                # Shared fixtures and Streamlit mock
    ├── test_validation.py         # Schema and domain validation tests (16 tests)
    ├── test_rules.py              # Risk scoring and classification tests (13 tests)
    ├── test_clustering.py         # K-Means clustering pipeline tests (9 tests)
    └── test_error_scenarios.py    # Documented failure modes and known gaps (11 tests)
```

---

## Technologies

| Library | Role |
|---|---|
| [Python 3.8+](https://www.python.org/) | Core language |
| [Streamlit](https://streamlit.io/) | Interactive web dashboard |
| [pandas](https://pandas.pydata.org/) | Data loading, validation, and manipulation |
| [NumPy](https://numpy.org/) | Numerical operations |
| [scikit-learn](https://scikit-learn.org/) | K-Means clustering, StandardScaler, silhouette score |

---

## Prerequisites

Before running the project, ensure the following software is installed:

- **Python 3.10 or newer**
- **Git**

Verify your Python installation:

### Windows

```powershell
py --version
```

or

```powershell
python --version
```

### Linux / macOS

```bash
python3 --version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/CryptoRiskAI/cryptorisk-ai.git
cd cryptorisk-ai
```

### Windows

Install the required dependencies using the Python launcher:

```powershell
py -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
```

> **Note**
>
> Using `python -m pip` (or `py -m pip` on Windows) is recommended because it guarantees that the packages are installed into the same Python interpreter used to run the application.

---

## Running the Project

A sample dataset is already included at:

```
modelo/inventario_sintetico.csv
```

No data generation is required for the demonstration.

### Windows

Launch the dashboard using:

```powershell
py -m streamlit run modelo/app.py
```

### Linux / macOS

```bash
python3 -m streamlit run modelo/app.py
```

The application will be available at:

```
http://localhost:8501
```

Use the sidebar file uploader to load:

```
modelo/inventario_sintetico.csv
```

### Optional — Regenerate the dataset

If you want to reproduce the synthetic inventory from scratch:

#### Windows

```powershell
py modelo/proyectoquantum.py
```

#### Linux / macOS

```bash
python3 modelo/proyectoquantum.py
```

The generator uses a fixed random seed (`42`), ensuring reproducible results.

---

## Workflow

```
proyectoquantum.py          modelo/app.py
──────────────────          ─────────────────────────────────────────────
Generate 60 synthetic  →    Upload CSV via sidebar
assets (seed=42)            │
                            ├─ Validate schema (13 columns, domain values)
                            ├─ Score each asset (6 weighted dimensions)
                            ├─ Normalize scores to 0–100 scale
                            ├─ Classify risk level (Alto / Medio / Bajo)
                            ├─ Cluster assets with K-Means (k=2,3,4)
                            └─ Render dashboard + export results CSV
```

**Risk scoring dimensions** — each scored 0–10 and summed to a maximum of 60:

| Dimension | Rationale |
|---|---|
| Algorithm | Quantum vulnerability — RSA-2048 and ECC-P256 are broken by Shor's algorithm; PQC algorithms score zero risk |
| Exposure | Likelihood of data interception; drives the HNDL threat |
| Criticality | Operational importance of the asset |
| Sensitivity | Data classification level (Secret → Public) |
| Retention | Years the data must remain confidential |
| Migration | Complexity of migrating away from the current algorithm |

---

## Repository Organization

| Path | Purpose |
|---|---|
| `modelo/app.py` | Streamlit dashboard. Contains the UI, validation, scoring, and clustering logic. This is the application entry point. |
| `modelo/proyectoquantum.py` | Synthetic inventory generator. Also contains documented implementations of the validation, scoring, and clustering modules. |
| `modelo/Explicacion.md` | Technical explanation of the risk engine and clustering methodology in Spanish. Covers the silhouette score rationale and the Mosca model reference. |
| `modelo/test.py` | Minimal Streamlit smoke test — verifies the framework launches correctly. |
| `data/README.md` | Describes the dataset schema, column definitions, and domain values. States that no real cryptographic assets, keys, or personal data are included. |

---

## Future Improvements

- **Modular source layout** — extract the validation, scoring, and clustering logic into importable modules (`src/validacion.py`, `src/reglas.py`, `src/clustering.py`) so they can be tested and reused independently
- **Sub-score breakdown** — display the six individual dimension scores per asset in the dashboard to make the risk explanation more granular
- **Mosca computation** — implement the full Mosca inequality (x + y > z) dynamically per asset, where x is the required data security horizon, y is the estimated migration duration, and z is the projected quantum threat timeline
- **Real inventory support** — extend the schema and validation to support anonymized real-world cryptographic inventories in addition to synthetic data
- **Automated pipeline** — add a single-command entrypoint that generates the dataset and launches the dashboard without the two-step manual process

---

## Team

| Name | Role |
|---|---|
| _Nancy Janneth Cicua Rodriguez_ | _Dataset_ |
| _Jose David Espinel Cortes_ | _Security_ |
| _Laura Sofia Sanchez Soto_ | _Dashboard_ |
| _Yury Dayana Velasquez Alvarez_ | _Testing_ |

---

## Reproducibility

The project was successfully cloned, installed, and executed on a clean Windows environment using only the instructions provided in this repository. This validation confirmed that the application can be reproduced without requiring any hidden setup steps beyond installing Python and Git.

---

## Recommendations

Suggested improvements for future iterations:

| Item | Description |
|---|---|
| Dashboard screenshots | Include screenshots or a short GIF of the application to improve repository presentation. |
| Docker support | A Docker configuration could simplify deployment and further improve reproducibility in future versions. |

---

## License

This project is released under the [MIT License](LICENSE).