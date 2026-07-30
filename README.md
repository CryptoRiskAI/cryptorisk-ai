# CryptoRisk AI

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)

Una herramienta de evaluación de riesgos criptográficos frente a la computación cuántica que puntúa, agrupa y prioriza activos criptográficos según su preparación para la migración.

---

## Descripción General

CryptoRisk AI evalúa un inventario sintético de activos criptográficos frente a la amenaza de la computación cuántica, específicamente el riesgo de ataques *harvest now, decrypt later* (HNDL). Para cada activo, aplica un modelo determinista de puntuación a través de seis dimensiones de riesgo —incluyendo la vulnerabilidad del algoritmo frente al algoritmo de Shor y la exposición en la red— para generar una puntuación de riesgo explicable y normalizada. Posteriormente, los activos se agrupan utilizando K-Means para facilitar la planificación de la migración.

El proyecto fue desarrollado como un MVP académico para la **Cyber Quantum Summer School**.

---

## Características

- **Validación del conjunto de datos** — aplica un esquema obligatorio de 13 columnas y valida los valores categóricos frente a dominios predefinidos antes de ejecutar cualquier análisis.
- **Puntuación determinista de riesgo** — calcula una puntuación ponderada de riesgo a través de seis dimensiones, normalizada en una escala de 0 a 100, sin utilizar aleatoriedad ni modelos de aprendizaje automático para el cálculo.
- **Clasificación del riesgo** — clasifica cada activo como Riesgo Alto, Medio o Bajo según umbrales de puntuación.
- **Agrupamiento con K-Means** — agrupa los activos según su perfil de riesgo, seleccionando automáticamente el número óptimo de clústeres (k = 2, 3 o 4) mediante la puntuación *silhouette*.
- **Panel interactivo** — aplicación en Streamlit que muestra métricas principales, un ranking de los 10 activos con mayor riesgo, gráficos de distribución por riesgo y clústeres, además de la tabla completa del inventario.
- **Recomendaciones de migración** — genera una recomendación textual determinista para cada activo según su nivel de riesgo, utilizando el modelo de Mosca (x + y > z) como criterio de priorización.
- **Exportación de resultados** — permite descargar el inventario puntuado y agrupado en formato CSV.
- **Generación de datos sintéticos** — generador reproducible (semilla = 42) que crea un inventario de 60 activos para pruebas y demostraciones.

---

## Estructura del Proyecto

```text
cryptorisk-ai/
├── .github/
│   └── workflows/
│       └── tests.yml              # Pipeline de CI (GitHub Actions, ubuntu-latest)
├── LICENSE
├── README.md
├── pytest.ini                     # Configuración de pytest
├── requirements.txt               # Dependencias fijadas
├── data/
│   └── README.md                  # Documentación y licencia del conjunto de datos
├── modelo/
│   ├── app.py                     # Dashboard en Streamlit — punto de entrada principal
│   ├── inventario_sintetico.csv   # Conjunto de datos sintético de 60 activos (semilla=42)
│   ├── proyectoquantum.py         # Generación de datos, validación, puntuación y agrupamiento
│   ├── Explicacion.md             # Notas técnicas de la metodología (Español)
│   └── test.py                    # Prueba básica de Streamlit
└── tests/
    ├── conftest.py                # Fixtures compartidos y mock de Streamlit
    ├── test_validation.py         # Pruebas de validación del esquema y dominios (16 pruebas)
    ├── test_rules.py              # Pruebas de puntuación y clasificación (13 pruebas)
    ├── test_clustering.py         # Pruebas del flujo de K-Means (9 pruebas)
    └── test_error_scenarios.py    # Modos de fallo documentados y limitaciones conocidas (11 pruebas)
```

---

## Tecnologías

| Biblioteca | Función |
|---|---|
| [Python 3.8+](https://www.python.org/) | Lenguaje principal |
| [Streamlit](https://streamlit.io/) | Dashboard web interactivo |
| [pandas](https://pandas.pydata.org/) | Carga, validación y manipulación de datos |
| [NumPy](https://numpy.org/) | Operaciones numéricas |
| [scikit-learn](https://scikit-learn.org/) | Agrupamiento K-Means, StandardScaler y puntuación silhouette |

---

## Requisitos Previos

Antes de ejecutar el proyecto, asegúrate de tener instalado el siguiente software:

- **Python 3.10 o superior**
- **Git**

Verifica la instalación de Python:

### Windows

```powershell
py --version
```

o

```powershell
python --version
```

### Linux / macOS

```bash
python3 --version
```

---

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/CryptoRiskAI/cryptorisk-ai.git
cd cryptorisk-ai
```

### Windows

Instala las dependencias requeridas utilizando el lanzador de Python:

```powershell
py -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
```

> **Nota**
>
> Se recomienda utilizar `python -m pip` (o `py -m pip` en Windows), ya que garantiza que los paquetes se instalen en el mismo intérprete de Python que ejecutará la aplicación.

---

## Ejecución del Proyecto

Ya se incluye un conjunto de datos de ejemplo en:

```text
modelo/inventario_sintetico.csv
```

No es necesario generar datos para la demostración.

### Windows

Inicia el dashboard con:

```powershell
py -m streamlit run modelo/app.py
```

### Linux / macOS

```bash
python3 -m streamlit run modelo/app.py
```

La aplicación estará disponible en:

```text
http://localhost:8501
```

Utiliza el cargador de archivos de la barra lateral para abrir:

```text
modelo/inventario_sintetico.csv
```

### Opcional — Regenerar el conjunto de datos

Si deseas reproducir el inventario sintético desde cero:

#### Windows

```powershell
py modelo/proyectoquantum.py
```

#### Linux / macOS

```bash
python3 modelo/proyectoquantum.py
```

El generador utiliza una semilla aleatoria fija (`42`), garantizando resultados reproducibles.

---

## Flujo de Trabajo

```text
proyectoquantum.py          modelo/app.py
──────────────────          ─────────────────────────────────────────────
Generar 60 activos     →    Cargar CSV desde la barra lateral
sintéticos (semilla=42)     │
                             ├─ Validar esquema (13 columnas y dominios)
                             ├─ Puntuar cada activo (6 dimensiones ponderadas)
                             ├─ Normalizar puntuaciones a una escala de 0–100
                             ├─ Clasificar nivel de riesgo (Alto / Medio / Bajo)
                             ├─ Agrupar activos con K-Means (k=2,3,4)
                             └─ Mostrar dashboard + exportar resultados en CSV
```

**Dimensiones de la puntuación de riesgo** — cada una se puntúa de 0 a 10, con un máximo total de 60 puntos:

| Dimensión | Justificación |
|---|---|
| Algoritmo | Vulnerabilidad cuántica — RSA-2048 y ECC-P256 son vulnerables al algoritmo de Shor; los algoritmos PQC obtienen riesgo cero. |
| Exposición | Probabilidad de interceptación de los datos; impulsa la amenaza HNDL. |
| Criticidad | Importancia operativa del activo. |
| Sensibilidad | Nivel de clasificación de la información (Secreta → Pública). |
| Retención | Años durante los cuales los datos deben permanecer confidenciales. |
| Migración | Complejidad para migrar desde el algoritmo criptográfico actual. |

---

## Organización del Repositorio

| Ruta | Propósito |
|---|---|
| `modelo/app.py` | Dashboard de Streamlit. Contiene la interfaz, la validación, la puntuación y la lógica de agrupamiento. Es el punto de entrada principal de la aplicación. |
| `modelo/proyectoquantum.py` | Generador del inventario sintético. También contiene implementaciones documentadas de los módulos de validación, puntuación y agrupamiento. |
| `modelo/Explicacion.md` | Explicación técnica del motor de riesgo y de la metodología de agrupamiento en español. Incluye la justificación del uso de la puntuación silhouette y la referencia al modelo de Mosca. |
| `modelo/test.py` | Prueba mínima de Streamlit para verificar que el framework se inicia correctamente. |
| `data/README.md` | Describe el esquema del conjunto de datos, las definiciones de las columnas y los valores permitidos. Especifica que no se incluyen activos criptográficos reales, claves ni datos personales. |

---

## Mejoras Futuras

- **Arquitectura modular** — extraer la lógica de validación, puntuación y agrupamiento en módulos independientes (`src/validacion.py`, `src/reglas.py`, `src/clustering.py`) para facilitar su reutilización y pruebas.
- **Desglose de subpuntuaciones** — mostrar en el dashboard las seis puntuaciones individuales por dimensión para ofrecer explicaciones de riesgo más detalladas.
- **Cálculo del modelo de Mosca** — implementar dinámicamente la desigualdad completa de Mosca (x + y > z) para cada activo, donde x representa el horizonte de seguridad requerido, y el tiempo estimado de migración y z la proyección temporal de la amenaza cuántica.
- **Soporte para inventarios reales** — ampliar el esquema y la validación para admitir inventarios criptográficos reales anonimizados además de datos sintéticos.
- **Pipeline automatizado** — añadir un punto de entrada de un solo comando que genere el conjunto de datos y ejecute el dashboard sin requerir el proceso manual de dos pasos.

---

## Equipo

| Nombre | Rol |
|---|---|
| _Nancy Janneth Cicua Rodriguez_ | _Conjunto de datos_ |
| _Jose David Espinel Cortes_ | _Seguridad_ |
| _Laura Sofia Sanchez Soto_ | _Dashboard_ |
| _Yury Dayana Velasquez Alvarez_ | _Pruebas_ |

---

## Reproducibilidad

El proyecto fue clonado, instalado y ejecutado correctamente en un entorno Windows limpio utilizando únicamente las instrucciones proporcionadas en este repositorio. Esta validación confirmó que la aplicación puede reproducirse sin requerir pasos de configuración ocultos más allá de instalar Python y Git.

---

## Recomendaciones

Mejoras sugeridas para futuras versiones:

| Elemento | Descripción |
|---|---|
| Capturas del dashboard | Incluir capturas de pantalla o un GIF corto de la aplicación para mejorar la presentación del repositorio. |
| Soporte con Docker | Una configuración con Docker podría simplificar el despliegue y mejorar aún más la reproducibilidad en futuras versiones. |

---

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE).