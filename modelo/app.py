# app.py — CryptoRisk AI Dashboard
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

st.set_page_config(page_title="CryptoRisk AI", layout="wide")
st.title("CryptoRisk AI — Priorización de activos criptográficos")

# -------------------- TEMA CYBERPUNK / BLADE RUNNER --------------------
st.markdown("""
<style>

/* Fondo general de la app */
.stApp {
    background-color: #0a0e17;
    color: #e6f1ff;
}

/* Título principal con glow cian */
h1 {
    color: #08f7fe !important;
    text-shadow: 0 0 8px #08f7fe, 0 0 20px rgba(8, 247, 254, 0.4);
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
    border-bottom: 1px solid #08f7fe;
    padding-bottom: 10px;
}

/* Subtítulos con glow magenta, más sutil */
h2, h3 {
    color: #fe53bb !important;
    text-shadow: 0 0 6px rgba(254, 83, 187, 0.5);
    font-family: 'Courier New', monospace;
}

/* Tarjetas de métricas (st.metric) */
div[data-testid="stMetric"] {
    background-color: #131a2b;
    border: 1px solid #08f7fe;
    border-radius: 6px;
    padding: 12px;
    box-shadow: 0 0 10px rgba(8, 247, 254, 0.15);
}
div[data-testid="stMetricValue"] {
    color: #08f7fe !important;
}
div[data-testid="stMetricLabel"] {
    color: #e6f1ff !important;
}

/* Tablas / dataframes */
div[data-testid="stDataFrame"] {
    border: 1px solid #fe53bb;
    border-radius: 4px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #05070d;
    border-right: 1px solid #08f7fe;
}

/* Botón de descarga */
div[data-testid="stDownloadButton"] button {
    background-color: #131a2b;
    color: #f9c80e;
    border: 1px solid #f9c80e;
    text-shadow: 0 0 4px #f9c80e;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #f9c80e;
    color: #0a0e17;
}

</style>
""", unsafe_allow_html=True)

# -------------------- PESOS Y FUNCIONES (idénticos al notebook) --------------------
PESOS = {
    "Algoritmo": {"RSA-2048": 10, "ECC-P256": 8, "AES-256": 2, "SHA-256": 5, "PQC": 0},
    "Criticidad": {"Alta": 10, "Media": 5, "Baja": 2},
    "Sensibilidad": {"Secreto": 10, "Confidencial": 7, "Interno": 4, "Público": 1},
    "Retención (años)": {">20": 10, "10-20": 7, "5-10": 4, "<5": 1},
    "Exposición": {"Alta": 10, "Media": 5, "Baja": 2},
    "Migración": {"Alta": 10, "Media": 5, "Baja": 2},
}
SCORE_MAXIMO = sum(max(v.values()) for v in PESOS.values())

COLUMNAS_ESPERADAS = [
    "Identificador", "Tipo de activo", "Servicio", "Uso criptográfico",
    "Algoritmo", "Tamaño de clave", "Exposición", "Criticidad",
    "Sensibilidad", "Retención (años)", "Dependencia de proveedor",
    "Migración", "Vigencia"
]

DOMINIOS_VALIDOS = {
    "Algoritmo": {"RSA-2048", "ECC-P256", "AES-256", "SHA-256", "PQC"},
    "Criticidad": {"Alta", "Media", "Baja"},
    "Sensibilidad": {"Secreto", "Confidencial", "Interno", "Público"},
    "Retención (años)": {">20", "10-20", "5-10", "<5"},
    "Exposición": {"Alta", "Media", "Baja"},
    "Migración": {"Alta", "Media", "Baja"},
    "Dependencia de proveedor": {"Alta", "Media", "Baja"},
    "Vigencia": {"Vigente", "Próximo a expirar", "Expirado"},
}

def validar_inventario(df):
    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if faltantes:
        return None, [f"Faltan columnas: {', '.join(faltantes)}"]
    errores = []
    validos = []
    for idx, fila in df.iterrows():
        motivo = None
        if fila[COLUMNAS_ESPERADAS].isnull().any():
            motivo = "valores vacíos"
        if motivo is None:
            for col, vals in DOMINIOS_VALIDOS.items():
                if fila[col] not in vals:
                    motivo = f"valor inválido en {col}"
                    break
        if motivo is None:
            validos.append(idx)
        else:
            errores.append(f"Fila {idx}: {motivo}")
    return df.loc[validos].reset_index(drop=True), errores

def aplicar_reglas(df):
    df = df.copy()
    def score(fila):
        return sum(PESOS[v][fila[v]] for v in PESOS)
    df["Score Total"] = df.apply(score, axis=1)
    df["Score Normalizado"] = (df["Score Total"] / SCORE_MAXIMO * 100).round(1)
    df["Nivel de Riesgo"] = df["Score Normalizado"].apply(
        lambda x: "Alto" if x >= 66 else ("Medio" if x >= 33 else "Bajo")
    )
    plantillas = {
        "Alto": "Revisar prioritariamente. Evaluar tiempo de migración vs. retención (Mosca).",
        "Medio": "Incluir en plan de migración a mediano plazo.",
        "Bajo": "Sin acción inmediata. Reevaluar en próximo ciclo."
    }
    df["Recomendación"] = df["Nivel de Riesgo"].map(plantillas)
    return df

def aplicar_clustering(df):
    cols = list(PESOS.keys())
    matriz = np.array([[PESOS[c][fila[c]] for c in cols] for _, fila in df.iterrows()])
    matriz = StandardScaler().fit_transform(matriz)
    mejor_k, mejor_score, mejor_etiquetas = 2, -1, None
    for k in range(2, 5):
        modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
        etiquetas = modelo.fit_predict(matriz)
        sil = silhouette_score(matriz, etiquetas)
        if sil > mejor_score:
            mejor_k, mejor_score, mejor_etiquetas = k, sil, etiquetas
    df = df.copy()
    df["Cluster"] = mejor_etiquetas
    df.attrs["mejor_k"] = mejor_k
    df.attrs["silhouette"] = round(mejor_score, 3)
    return df

# -------------------- INTERFAZ --------------------
st.sidebar.header("Carga de inventario")
archivo = st.sidebar.file_uploader("Sube el CSV del inventario", type=["csv"])

if archivo is not None:
    df_raw = pd.read_csv(archivo)
    df_valido, errores = validar_inventario(df_raw)

    if df_valido is None or len(df_valido) == 0:
        st.error("No hay registros válidos.")
        if errores:
            st.write(errores)
    else:
        df = aplicar_reglas(df_valido)
        df = aplicar_clustering(df)

        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Registros válidos", len(df))
        col2.metric("Mejor k", df.attrs["mejor_k"])
        col3.metric("Silhouette", df.attrs["silhouette"])
        col4.metric("Activos Alto riesgo", (df["Nivel de Riesgo"] == "Alto").sum())

        # Ranking prioritario
        st.subheader("Ranking prioritario (Top 10)")
        ranking = df.sort_values("Score Total", ascending=False).head(10).reset_index(drop=True)
        st.dataframe(
            ranking[["Identificador", "Algoritmo", "Criticidad", "Exposición",
                     "Score Total", "Nivel de Riesgo", "Cluster", "Recomendación"]],
            use_container_width=True, hide_index=True
        )

        # Distribuciones
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribución por Nivel de Riesgo")
            st.bar_chart(df["Nivel de Riesgo"].value_counts(), color="#08f7fe")
        with c2:
            st.subheader("Distribución por Cluster")
            st.bar_chart(df["Cluster"].value_counts(), color="#fe53bb")

        # Perfiles de clúster
        st.subheader("Perfiles de los clústeres")
        st.markdown("""
        - **Cluster 0 – Exposición residual**: algoritmos de menor riesgo cuántico, pero alta exposición.
        - **Cluster 1 – Migración diferida**: algoritmos clásicos en contextos de baja criticidad/exposición.
        - **Cluster 2 – Prioridad crítica**: algoritmos vulnerables + alta criticidad + alta exposición + larga retención.
        """)

        # Tabla completa
        with st.expander("Ver inventario completo enriquecido"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Descarga
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar resultados (CSV)", csv, "cryptorisk_resultados.csv", "text/csv")

else:
    st.info("Sube el archivo `inventario_sintetico.csv` para comenzar.")
