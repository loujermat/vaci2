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
    fuerza_maxima = fuerza_requerida + fuerza_requerida * 0.20
    # Filtro por fuerza mínima
    if "fuerza_succion" in base_datos.columns:
        condiciones.append((base_datos["fuerza_succion"] >= fuerza_requerida) & (base_datos["fuerza_succion"] <= fuerza_maxima))

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
        background-image: url("https://i.imgur.com/sYH7TOr.png");
        background-size: cover;
        background-position: center;
    }

    /* Cambiar el color del texto en general */
    html, body, .stMarkdown, .stText, .stTitle, .stHeader, .stSubheader, 
    .stCaption, .stSuccess, .stError, .stWarning, .stInfo {
        color: white !important;
    }

    /* Cambiar color de las etiquetas en los widgets */
    label, .stRadio, .stSelectbox label, .stNumberInput label, .stTextInput label {
        color: white !important;
    }

    /* Cambiar color de los placeholders en los inputs */
    input::placeholder, textarea::placeholder {
        color: white !important;
        opacity: 0.8 !important;
    }
    /* Cambiar color del título */
    h1 {
        color: white !important;
    }

    /* Cambiar color de las opciones en el st.radio */
    div[role="radiogroup"] label {
        color: white !important;
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

# Paso 1: Calcular o ingresar fuerza de succión
st.write("### Paso 1: Determinar la fuerza de succión por ventosa")

# Guardar el método seleccionado en el estado de la sesión
if "metodo_fuerza" not in st.session_state:
    st.session_state.metodo_fuerza = "Calcular"

# Cambiar el método dinámicamente
st.session_state.metodo_fuerza = st.radio(
    "Seleccione cómo desea determinar la fuerza de succión:",
    ("Calcular", "Ingresar manualmente"),
    index=0 if st.session_state.metodo_fuerza == "Calcular" else 1
)

if st.session_state.metodo_fuerza == "Calcular":
    # Campos para cálculo
    with st.form(key="calculo_form"):
        ventosas = st.number_input("Número de ventosas:", min_value=1, step=1)
        masa = st.number_input("Masa del objeto (kg):", min_value=0.0, step=0.5)
        aceleracion = st.number_input("Aceleración de la instalación (m/s²):", min_value=0.0, step=0.1)
        pick = st.selectbox("Posición de la pieza al ser tomada:", ["Vertical", "Horizontal"])
        mov = st.selectbox("De qué manera se moverá la pieza:", ["Dirección Vertical", "Dirección Horizontal", "2 Direcciones y rotación"])
        superficie_opcion = st.selectbox("Tipo de superficie:", ["Seleccionar"] + list(tiposuperficie_dict.keys()))
        coef_seguridad_opcion = st.selectbox("Coeficiente de seguridad:", ["Seleccionar"] + list(coef_seguridad_dict.keys()))
        submit_fuerza = st.form_submit_button(label="Calcular fuerza")

    if submit_fuerza:
        if superficie_opcion != "Seleccionar" and coef_seguridad_opcion != "Seleccionar":
            coef_seguridad = coef_seguridad_dict[coef_seguridad_opcion]
            tiposuperficie_valor = tiposuperficie_dict[superficie_opcion]
            gravedad = 9.81  # Constante de gravedad
            st.session_state.fuerza_calculada = calcular_fuerza_succion(
                masa, aceleracion, ventosas, coef_seguridad, pick, mov, gravedad, tiposuperficie_valor
            )
            st.session_state.ventosas = ventosas
            st.success(f"Fuerza calculada: `{st.session_state.fuerza_calculada:.2f} N`")
        else:
            st.error("Por favor, seleccione todos los parámetros necesarios para el cálculo.")

elif st.session_state.metodo_fuerza == "Ingresar manualmente":
    # Campo para ingresar fuerza manualmente
    with st.form(key="manual_form"):
        fuerza_manual = st.number_input("Fuerza de succión necesaria por ventosa (N):", min_value=0, step=100)
        submit_fuerza_manual = st.form_submit_button(label="Guardar fuerza manual")

    if submit_fuerza_manual:
        st.session_state.fuerza_calculada = fuerza_manual
        st.success(f"Fuerza ingresada manualmente: `{st.session_state.fuerza_calculada:.2f} N`")

# Mostrar la fuerza calculada o ingresada si ya existe
if st.session_state.fuerza_calculada is not None:
    st.write(f"### Fuerza de succión por ventosa: `{st.session_state.fuerza_calculada:.2f} N`")

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
