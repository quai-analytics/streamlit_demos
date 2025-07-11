import pandas as pd
import re
from thefuzz import fuzz, process
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

def str_to_bool(x):
    """Convierte un valor a booleano de forma robusta y concisa.
    Maneja strings ('yes', 'true', 't', '1'), números y valores nulos (NaN).
    Un valor nulo o una cadena no reconocida se evalúa como `False`.
    Cualquier número distinto de cero se evalúa como `True`.
    """
    if pd.isna(x):
        return False
    if isinstance(x, str):
        return x.strip().lower() in {'yes', 'true', 't', '1'}
    return bool(x)

#############################################################################
def extract_numeric(value):
    """
    Extrae un valor numérico como float de una entrada, manejando diferentes formatos.

    Esta función intenta convertir la entrada a un float. Si la entrada ya es un int o float,
    simplemente la convierte a float. Si es una cadena, intenta extraer un número,
    reemplazando primero las comas por puntos para manejar decimales.
    Si la conversión falla o no se encuentra un número válido en la cadena, devuelve np.nan.

    Args:
        value: El valor de entrada, que puede ser un int, float o una cadena.

    Returns:
        float: El valor numérico extraído como float, o np.nan si no se puede extraer.

    Examples:
        >>> extract_numeric(123)
        123.0
        >>> extract_numeric(3.1415)
        3.1415
        >>> extract_numeric("123,45")
        123.45
        >>> extract_numeric("abc")
        nan
        >>> extract_numeric(None)
        nan
        >>> extract_numeric("63.00 m2")
        63.0
        >>> extract_numeric("Size: 150.5")
        150.5
    """
    if pd.isna(value): # Maneja NaN/None primero
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(',', '.')
        # Busca un patrón numérico (con o sin signo, con o sin decimales)
        match = re.search(r'[-+]?\d*\.?\d+', text)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                pass # Esto no debería ocurrir si la regex es correcta, pero por seguridad
    return np.nan

#############################################################################
def group_similar_locations(locations, threshold=80):
    """
    Agrupa nombres de locaciones similares de una lista.

    Args:
        locations (list): Una lista de strings con los nombres de las locaciones.
        threshold (int): El umbral de similitud (0-100) para considerar dos
                         nombres como parte del mismo grupo.

    Returns:
        list: Una lista de listas, donde cada sublista es un grupo de
              nombres de locaciones similares.
    """
     # Eliminar duplicados exactos y ordenar para consistencia
    unique_locations = sorted(list(set(locations)))
    
    groups = []
    processed_indices = set()

    for i, loc1 in enumerate(unique_locations):
        if i in processed_indices:
            continue

        # Empezar un nuevo grupo con la locación actual
        current_group = [loc1]
        processed_indices.add(i)

        # Comparar con el resto de las locaciones
        for j, loc2 in enumerate(unique_locations):
            if j <= i or j in processed_indices:
                continue
            
            # Usamos token_set_ratio que es bueno para palabras en diferente orden
            # o cuando una cadena es un subconjunto de la otra.
            similarity_score = fuzz.token_set_ratio(loc1, loc2)
            
            if similarity_score >= threshold:
                current_group.append(loc2)
                processed_indices.add(j)
        
        groups.append(current_group)
        
    return groups

#############################################################################
def plot_categorical_distribution_with_nulls(data_series, series_name="Variable", figsize = (10, 6)):
    """
    Visualiza la distribución de una variable categórica y muestra la cantidad de valores nulos.

    Args:
        data_series (pd.Series): La serie de pandas con los datos categóricos.
        series_name (str): El nombre de la variable para usar en los títulos del gráfico.
    """
    # 1. Calcular la cantidad y el porcentaje de valores nulos
    null_count = data_series.isnull().sum()
    total_count = len(data_series)
    null_percentage = (null_count / total_count) * 100 if total_count > 0 else 0

    # 2. Crear la visualización
    plt.figure(figsize=figsize)
    
    # Usar seaborn para crear un countplot.
    # Se usa dropna() para que el gráfico solo muestre la distribución de los valores existentes.
    sns.countplot(y=data_series.dropna(), order=data_series.value_counts().index)

    # 3. Añadir títulos y etiquetas informativas
    plt.title(
        f'Distribución de {series_name}\n'
        f'Valores Nulos: {null_count} ({null_percentage:.2f}%)',
        fontsize=16
    )
    plt.xlabel('Frecuencia', fontsize=12)
    plt.ylabel(f'Categoría de {series_name}', fontsize=12)
    plt.grid(axis='x', alpha=0.75) # Cuadrícula en el eje x para el countplot

    # Ajustar el layout para evitar que las etiquetas se superpongan si hay muchas categorías
    plt.tight_layout()

    # 4. Mostrar el gráfico
    plt.show()

#############################################################################
def plot_numeric_distribution_and_boxplot(data_series, series_name="Variable"):
    """
    Visualiza la distribución de una variable numérica con un histograma y un boxplot,
    y muestra la cantidad de valores nulos.

    Args:
        data_series (pd.Series): La serie de pandas con los datos numéricos.
        series_name (str): El nombre de la variable para usar en los títulos del gráfico.
    """
    # 1. Calcular la cantidad y el porcentaje de valores nulos
    null_count = data_series.isnull().sum()
    total_count = len(data_series)
    null_percentage = (null_count / total_count) * 100 if total_count > 0 else 0


    fig, (ax_hist, ax_box) = plt.subplots(2, 1, figsize=(10, 5), sharex=True,
                                            gridspec_kw={'height_ratios': [5, 1]})
        
        # Ajustar el espacio entre subplots
    plt.subplots_adjust(hspace=0.4)
    sns.histplot(data_series.dropna(), kde=True, bins=30, ax=ax_hist)
    ax_hist.set_title(
        f'Distribución de {series_name}\n'
        f'Valores Nulos: {null_count} ({null_percentage:.2f}%)',
        fontsize=16
    )
    ax_hist.set_xlabel('') # Eliminar etiqueta x para evitar superposición con el boxplot
    ax_hist.set_ylabel('Frecuencia', fontsize=12)
    ax_hist.grid(axis='y', alpha=0.5)

    sns.boxplot(x=data_series.dropna(), ax=ax_box)
    ax_box.set_xlabel(f'Valor de {series_name}', fontsize=12)
    ax_box.set_ylabel('Boxplot', fontsize=12)
    ax_box.grid(axis='x', alpha=0.5) # Cuadrícula en el eje x para el boxplot


    # 5. Mostrar el gráfico
    plt.tight_layout() # Ajustar automáticamente los parámetros de la subtrama para que encajen en el área de la figura.
    plt.show()

#############################################################################
def extract_property_features(description_text):
    """
    Extrae características clave de una descripción de propiedad a partir de texto.

    Analiza una cadena de texto para identificar si la propiedad incluye:
    - Una 'den' (estudio/sala adicional).
    - Un 'loft' (asumiendo que 'bayloft' se refiere a 'loft').
    - Si es una propiedad 'commercial' (comercial).
    - La cantidad de baños ('bath').

    Args:
        description_text (str): La descripción de la propiedad como una cadena de texto.

    Returns:
        pd.Series: Una Serie de Pandas con las siguientes características:
            - 'bayloft' (bool): True si se detecta 'loft'.
            - 'den' (bool): True si se detecta 'den'.
            - 'bath' (float): Cantidad de baños detectada. Por defecto es 1.0.
            - 'bedroom' (float): Cantidad de habitaciones. Por defecto es 1.0, o 0.0 si es comercial.
    """
    # Inicializamos los valores por defecto. Usamos np.nan para 'bath'
    # ya que es un valor numérico y np.nan es el estándar para datos faltantes.
    has_den = False
    num_baths = 1.0
    is_commercial = False
    has_loft = False
    num_bedrooms = 1.0

    if isinstance(description_text, str):
        text_lower = description_text.lower()

        # Buscar si tiene 'den'
        has_den = 'den' in text_lower

        # Buscar si tiene 'loft'
        has_loft = 'loft' in text_lower

        # Buscar si es comercial
        is_commercial = 'commercial' in text_lower
        is_commercial = 'ofic' in text_lower

        # BUscar si tiene guest room
        is_guest = 'guest' in text_lower


        if is_commercial:
            num_bedrooms = 0.0

        else:
            # Buscar cantidad de habitaciones (ej: '2 bdrm', '3 bedrooms', etc.)
            # La expresión regular busca un número entero.
            bedroom_match = re.search(r'([0-9]+)\s*(bed|bdrm|bedrooms|bedroom|hab|habitación|habitaciones|cuarto|cuartos)', text_lower)
            if bedroom_match:
                num_bedrooms = float(bedroom_match.group(1))
                if is_guest:
                    num_bedrooms += 1.0


        # Buscar cantidad de baños (ej: '2 bath', '1.5 baños', '3 baños', etc.)
        # La expresión regular busca un número (entero o decimal, con punto o coma)
        # seguido de una palabra relacionada con baños.
        # Se usa r'' para raw string para evitar problemas con backslashes.
        bath_match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s*(bath|baños|banos|bano|baño)', text_lower)
        if bath_match:
            # Reemplazar coma por punto para asegurar la conversión a float
            num_baths = float(bath_match.group(1).replace(',', '.'))
        # Si no se encuentra un patrón claro de baños, num_baths permanece como np.nan.
        # Esto es más seguro que intentar extraer cualquier número o devolver 0
        # si no hay un contexto claro de "baños".

    return pd.Series({
        'bayloft': has_loft, # Usar el nombre de variable actualizado
        'den': has_den,
        'bath': num_baths,
        'commercial': is_commercial,
        'bedroom' : num_bedrooms
    })