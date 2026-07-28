# **CryptoRisk AI**





###### ¿Qué hace esta interfaz?


A partir de un archivo elaborado en Google Colab inicialmente con los parámetros establecidos en el dcoumento y en el formulario como punto de partida y posteriormente con su ejecución a través de un app.py, se genera un archivo de tipo CSV con un inventario de 60 elementos para calcular el porcentaje de riesgo, agrupar los archivos con K-Means y presentar los resultados en un dashboard en interactivo señalando los 10 elementos que requieren más atención según el puntaje obtenido.



###### ¿Cómo se ejecuta este elemento?


Usando Streamlit (una biblioteca libre de código abierto para Python que permite crear aplicaciones web interactivas).
Con los comandos señalados posteriormente es como se inicia este entorno virtual:

    pip install streamlit pandas numpy scikit-learn
    # intalación de la biblioteca de streamlit por cmd
    
    streamlit run app.py
    # Ejecución directa una vez se dirija a la carpeta destino (cmd).

El archivo sintético elaborado por el equipo y de extensnión CSV es cargado con las columnas correspondientes según el diccionario de datos (Identificador, Tipo de activo, Servicio, Uso criptográfico, Algoritmo, Tamaño de clave, Exposición, Criticidad, Sensibilidad, Retención (años), Dependencia de proveedor, Migración, Vigencia).

El motor de riesgo es el resultado de la suma de 6 subpuntajes con una escala del 0-10 (aclaración que esta fue tomada por los integrantes).



###### ¿Por qué algoritmo y exposición son los de mayir peso?


Siguiendo el criterio de los elementos de apoyo y adjuntos en la bibliografía, el riesgo de un ataque de "harvest now, decrypt later" depende de: interceptación del dato (exposición) y que el algoritmo que lo proteja sea descrifrable en un futuro por una computadora cuántica (algoritmo; tomando por caso RSA/ECC vulnerable al algoritmo de Shor).



###### K-means


Estandarizar los subpuntajes con StandardScaler y se prueba k-means con k=2,3 y 4, seleccionando el mejor k segun Silhouette Score (métrica usada para medir la calidad de un modelo de agrupamiento y saber su viabilidad. Medidos entre valores de -1 a 1). Según el dataset usado, el mejor k=3 con Silhoutte de 0.16.

Nota del valor: 0.16 es bajo en términos absolutos, esperado al ser categóricos convertidos a puntajes ordinales y más en su aleatoriedad. No obstante el nivel de riesgo sigue siendo el criterio principal; el clúster es interpretativo.

