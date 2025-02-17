import pandas as pd
import streamlit as st
import base64

# Cargar la base de datos desde el archivo Excel
def cargar_base_datos():
    try:
        base_datos = pd.read_excel("ventosas.xlsx")
        base_datos.columns = base_datos.columns.str.lower()  # Convertir nombres de columnas a minúsculas
        return base_datos
    except FileNotFoundError:
        st.error("El archivo 'ventosas.xlsx' no se encontró. Asegúrate de que esté en la misma carpeta que este programa.")
        return pd.DataFrame()

# Calcular la fuerza de succión teórica según las condiciones
def calcular_fuerza_succion(masa, aceleracion, ventosas, coef_seguridad, pick, mov, gravedad, tiposuperficie_valor):
    if aceleracion == 0:
        st.error("La aceleración no puede ser 0. Por favor, ingrese un valor válido.")
        return 0

    if pick == "Vertical":
        if mov == "Dirección Vertical":
            fuerza_total = masa * (aceleracion + gravedad / tiposuperficie_valor) * coef_seguridad
        elif mov == "Dirección Horizontal":
            fuerza_total = masa * (aceleracion + gravedad / tiposuperficie_valor) * coef_seguridad
        else:  # "2 Direcciones y rotación"
            fuerza_total = (masa / tiposuperficie_valor) * (gravedad / aceleracion) * coef_seguridad
    else:  # Horizontal
        if mov == "Dirección Vertical":
            fuerza_total = masa * (aceleracion + gravedad) * coef_seguridad
        elif mov == "Dirección Horizontal":
            fuerza_total = masa * (aceleracion + gravedad / tiposuperficie_valor) * coef_seguridad
        else:  # "2 Direcciones y rotación"
            fuerza_total = (masa / tiposuperficie_valor) * (gravedad / aceleracion) * coef_seguridad

    fuerza_por_ventosa = fuerza_total / ventosas
    return fuerza_por_ventosa

# Filtrar ventosas por fuerza y otros parámetros
def filtrar_ventosas(base_datos, fuerza_requerida, material, superficie, aplicacion):
    condiciones = []

    # Filtro por fuerza mínima
    if "fuerza_succion" in base_datos.columns:
        condiciones.append(base_datos["fuerza_succion"] >= fuerza_requerida)

    # Filtro por material
    if material and material != "Seleccionar":
        condiciones.append(base_datos["material"].str.contains(material, case=False, na=False))
    # Filtro por superficie
    if superficie and superficie != "Seleccionar":
        condiciones.append(base_datos["superficie"].str.contains(superficie, case=False, na=False))
    # Filtro por aplicación
    if aplicacion and aplicacion != "Seleccionar":
        condiciones.append(base_datos["aplicaciones"].str.contains(aplicacion, case=False, na=False))

    # Aplicar todos los filtros
    if condiciones:
        resultado = base_datos
        for condicion in condiciones:
            resultado = resultado[condicion]
        return resultado

    return base_datos

# Configuración de la aplicación Streamlit
st.set_page_config(page_title="Micro, Calculadora de vacío")

def get_image_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    

# Agregar una imagen de fondo usando CSS
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://imgur.com/a/aKyjHwx");
        background-size: cover;
        background-position: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Contenido de la aplicación
st.title("Selector de Ventosas")
st.write("Bienvenido a la calculadora de vacío.")

# Cargar la base de datos
base_datos = cargar_base_datos()

# Diccionarios para valores de coeficientes y superficies
coef_seguridad_dict = {
    "Piezas críticas, heterogéneas o porosas": 1.5,
    "Rugosas": 2.0
}

tiposuperficie_dict = {
    "Aceitada": 0.1,
    "Mojada": 0.2,
    "Madera, cristal, metal, piedra": 0.5,
    "Rugosa": 0.6
}

# Almacenar fuerza en sesión para mantener los cálculos entre pasos
if "fuerza_calculada" not in st.session_state:
    st.session_state.fuerza_calculada = None

# Paso 1: Calcular fuerza teórica
st.write("### Paso 1: Calcular la fuerza de succión teórica")
with st.form(key="fuerza_form"):
    ventosas = st.number_input("Número de ventosas:", min_value=1, step=1)
    masa = st.number_input("Masa del objeto (kg):", min_value=0.0, step=0.5)
    aceleracion = st.number_input("Aceleración de la instalación (m/s²):", min_value=0.0, step=0.1)
    pick = st.selectbox("Posición de la pieza al ser tomada:", ["Vertical", "Horizontal"])
    mov = st.selectbox("De qué manera se moverá la pieza:", ["Dirección Vertical", "Dirección Horizontal", "2 Direcciones y rotación"])
    superficie_opcion = st.selectbox("Tipo de superficie:", ["Seleccionar"] + list(tiposuperficie_dict.keys()))
    coef_seguridad_opcion = st.selectbox("Coeficiente de seguridad:", ["Seleccionar"] + list(coef_seguridad_dict.keys()))
    submit_fuerza = st.form_submit_button(label="Calcular fuerza")

if submit_fuerza:
    coef_seguridad = coef_seguridad_dict.get(coef_seguridad_opcion, 1)
    tiposuperficie_valor = tiposuperficie_dict.get(superficie_opcion, 1)
    gravedad = 9.81  # Constante de gravedad
    st.session_state.fuerza_calculada = calcular_fuerza_succion(masa, aceleracion, ventosas, coef_seguridad, pick, mov, gravedad, tiposuperficie_valor)
    st.session_state.ventosas = ventosas
    st.write(f"### Fuerza de succión teórica por ventosa: `{st.session_state.fuerza_calculada:.2f} N`")

# Mostrar el cálculo si ya existe
if st.session_state.fuerza_calculada is not None and not submit_fuerza:
    st.write(f"### Fuerza de succión teórica por ventosa: `{st.session_state.fuerza_calculada:.2f} N`")

# Paso 2: Filtrar ventosas
if st.session_state.fuerza_calculada is not None:
    st.write("### Paso 2: Seleccionar las características de la ventosa")
    with st.form(key="ventosas_form"):
        material = st.selectbox("Material de la ventosa:", ["Seleccionar"] + ["NBR", "Silicona", "HT1", "Elastodur", "EPDM", "NK"])
        superficie = st.selectbox("Superficie:", ["Seleccionar"] + ["Plana", "Irregular", "Curva", "Flexible"])
        aplicacion = st.selectbox("Aplicación:", ["Seleccionar"] + ["Bolsas", "Capsulas", "Carton", "Chapa", "Chapa con fuerte abombamiento", "Con companesacion de altura", "Geometrias complejas", "Ligeramente rugosas", "Lisas", "Láminas", "Muy rugosas", "Papel", "Piezas alargadas", "Piezas estrechas", "Piezas estructuradas", "Plastico"])
        submit_ventosa = st.form_submit_button(label="Buscar Ventosas")

    if submit_ventosa:
        resultados = filtrar_ventosas(base_datos, st.session_state.fuerza_calculada, material, superficie, aplicacion)
        if not resultados.empty:
            st.write("### Ventosas recomendadas:")
            st.dataframe(resultados)
        else:
            st.write(":x: **No se encontraron ventosas que cumplan con los requisitos exactos.**")
