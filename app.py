import streamlit as st
import anthropic
import os

# 1. Configuración estética de la página (Estilo PAD - Rojo Borgoña y Oro)
st.set_page_config(
    page_title="PAD Costos Coach",
    page_icon="🎓",
    layout="centered"
)

# Estilo visual personalizado para los títulos y colores corporativos del PAD
st.markdown("""
    <style>
    .main-title {
        color: #8B0000; /* Rojo Borgoña */
        font-family: 'Georgia', serif;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 5px;
    }
    .subtitle {
        color: #D4AF37; /* Dorado */
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">PAD Costos Coach</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tutor Socrático de Contabilidad de Costos • MBA</div>', unsafe_allow_html=True)

# 2. Barra Lateral: Autenticación y selección de material
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Leemos la llave de Anthropic en secreto
    api_key_usuario = st.secrets["ANTHROPIC_API_KEY"]
    
    # Pedimos la contraseña de la clase al usuario
    password_ingresado = st.text_input(
        "Contraseña de acceso:", 
        type="password", 
        placeholder="Ingrese la clave de la clase"
    )
    
    st.divider()
    st.subheader("📚 Material del Curso")
    
    opcion_estudio = st.selectbox(
        "Selecciona el tema a discutir:",
        ["Nota Técnica: Introducción a Costos", "Caso 1: Costeo ABC", "Caso 2: Outsourcing"]
    )
    
    st.info("Este asistente está programado bajo la metodología del PAD para guiarte de forma socrática. No te dará las respuestas directas, te enseñará a pensar.")
# 3. Cargar la Nota Técnica (Nuestra Base de Conocimientos / RAG Local)
def cargar_nota_tecnica():
    # Aseguramos que busque la extensión correcta (.md) que corregimos en el paso anterior
    ruta_archivo = "nota_tecnica_costos.md"
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return f.read()
    return "Error: No se encontró el archivo de la nota técnica."

contenido_nota_tecnica = cargar_nota_tecnica()

# 4. Definir el System Prompt (Framework MIT: Persona, Contexto, Restricciones y Formato)
system_prompt_socratico = f"""
Eres el "PAD Costos Coach", un exigente pero empático Profesor Socrático de Contabilidad de Costos para el MBA del PAD de la Universidad de Piura.

CONTEXTO:
Aquí tienes la BASE DE CONOCIMIENTOS oficial de la materia. Debes anclar todas tus respuestas ESTRICTAMENTE a este contenido:
===
{contenido_nota_tecnica}
===

RESTRICCIONES (Constraints):
1. NUNCA le des un cálculo resuelto o una respuesta numérica directa.
2. Si el alumno te pregunta por una fórmula o resultado (ej. "¿Cómo calculo el punto de equilibrio?"), devuélvele una pregunta que lo obligue a pensar: "¿Qué costos consideras que son fijos en este ejercicio?".
3. Si el alumno hace preguntas fuera de la contabilidad de costos, redirígelo amablemente al tema de estudio.

FORMATO:
- Mantén un tono sumamente profesional, formal (tratando de "usted"), característico de un profesor de alta dirección.
- Sé conciso. Termina tus intervenciones con una (y solo una) pregunta socrática que invite a la reflexión.
"""

# 5. Gestionar el Historial de Chat (Memoria Persistente)
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"role": "assistant", "content": "¡Bienvenido al PAD Costos Coach! Soy su tutor socrático. ¿Con qué concepto o cálculo de la Nota Técnica le gustaría comenzar a debatir hoy?"}
    ]

# Mostrar los mensajes del historial en la pantalla
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. Entrada del usuario y conexión con la API de Claude
if prompt_usuario := st.chat_input("Ej. ¿Cómo diferencio un costo fijo de uno variable?"):
    
    # Mostrar el mensaje del usuario de inmediato
    with st.chat_message("user"):
        st.write(prompt_usuario)
    st.session_state.mensajes.append({"role": "user", "content": prompt_usuario})
    
    # Validar si la contraseña ingresada coincide con el Secreto
    if password_ingresado != st.secrets["PASSWORD_CLASE"]:
        st.warning("🔒 Por favor, ingrese la contraseña correcta en la barra lateral para acceder al Coach.")
        st.stop()
        
    try:
        client = anthropic.Anthropic(api_key=api_key_usuario)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando socráticamente..."):
                
                mensajes_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.mensajes
                    if m["role"] != "assistant" or m != st.session_state.mensajes[0] # Evitamos enviar el saludo inicial como si fuera Claude
                ]
                
                # Llamada a Claude. Usamos Sonnet 3.5 por su alta capacidad de razonamiento.
                # Nota: Si el consumo de tokens es alto, se puede cambiar a "claude-3-haiku-20240307"
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=800,
                    system=system_prompt_socratico,
                    messages=mensajes_api
                )
                
                # Extracción correcta del texto de la respuesta de Claude
                respuesta_texto = response.content[0].text
                st.write(respuesta_texto)
                
        # Guardar la respuesta del bot en el historial
        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
        
    except Exception as e:
        st.error(f"❌ Ocurrió un error de conexión: {e}")
