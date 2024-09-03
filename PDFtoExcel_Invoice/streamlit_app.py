import streamlit as st
import pypdf
import json
import pandas as pd
import io
from openai import OpenAI
import logging
import traceback
import re
import plotly.express as px

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar un manejador de logging para Streamlit
class StreamlitHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        st.error(log_entry)

streamlit_handler = StreamlitHandler()
streamlit_handler.setLevel(logging.ERROR)
logger.addHandler(streamlit_handler)

# Definir la API key (usar st.secrets en producción)
client = OpenAI(api_key=st.secrets["API_KEY"])

def read_pdf(file):
    pdf_reader = pypdf.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_json_from_text(text):
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group()
    return None

def generate_json_from_pdf(pdf_content):
    prompt = f"""
    Analiza minuciosamente el siguiente contenido de una factura PDF y genera un JSON estructurado y detallado. Sé extremadamente preciso y asegúrate de que cada clave tenga un único valor, no listas. Incluye absolutamente toda la información relevante de la factura.

    Realiza las siguientes tareas específicas con máxima precisión:
    1. Identifica el tipo de servicio recibido o producto comprado y devuélvelo con el formato "tipo: [descripción breve y precisa]".
    2. Identifica el tipo de pago realizado entre estas opciones: pago en efectivo, pago por recibo domiciliado, pago por transferencia y pago por tarjeta. Devuélvelo con el formato "pago: [tipo de pago]". Si no se especifica, indica "pago: no especificado".
    3. Basándote en la información anterior, proporciona el asiento contable que mejor se ajuste según la contabilidad española. El asiento contable debe ser una cadena de texto con el siguiente formato:
       "asiento_contable: (DEBE) Cuenta1 XXXX€ (Número), Cuenta2 YYYY€ (Número) a (HABER) Cuenta3 ZZZZ€ (Número), Cuenta4 WWWW€ (Número)"
       Donde las cuentas deben ser específicas del Plan General Contable español, los importes deben cuadrar, y se debe incluir el número de cuenta entre paréntesis. Incluye todos los detalles, como descuentos si los hubiera.
    4. Genera un resumen general que incluya una descripción de la factura, un resumen del asiento contable e información tributaria y fiscal para gestionar la factura.

    Contenido del PDF:
    {pdf_content}

    Genera un JSON que incluya todos estos detalles de manera estructurada y precisa. Asegúrate de que cada campo tenga un valor único y específico. SOLO DEVUELVE EL JSON, sin ningún texto adicional antes o después.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto contable de alta precisión especializado en análisis detallado de facturas y contabilidad española. Debes generar únicamente un JSON válido sin ningún texto adicional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        json_content = response.choices[0].message.content.strip()
        logger.info(f"JSON content generated: {json_content[:500]}...")
        
        json_string = extract_json_from_text(json_content)
        if json_string is None:
            logger.error("No se pudo extraer un JSON válido de la respuesta.")
            return None

        try:
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError as je:
            logger.error(f"Error al decodificar JSON: {str(je)}")
            logger.error(f"Contenido JSON que causó el error: {json_string}")
            return None
    except Exception as e:
        logger.error(f"Error al generar el JSON: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None



# Configuración de la página
st.set_page_config(page_title="Herramientas PDF", layout="wide")

# Ocultar el menú principal
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Estilos personalizados actualizados
st.markdown("""
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: white;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1 {
        color: #333;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    .subtitle {
        color: #666;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 40px;
    }
    .tool-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
    }
    .tool-card {
        background-color: #f0f2f5;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
        width: calc(33.333% - 20px);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .tool-card:hover {
        transform: translateY(-5px);
    }
    .tool-icon {
        font-size: 3em;
        margin-bottom: 10px;
    }
    .tool-title {
        font-weight: bold;
        margin-bottom: 10px;
    }
    .tool-description {
        font-size: 0.9em;
        color: #666;
    }
    .stButton>button {
        background-color: #e74c3c;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 20px;
        padding: 10px 20px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #c0392b;
    }
</style>
""", unsafe_allow_html=True)

# Título y subtítulo
st.markdown("<h1>Herramientas online para amantes de los PDF</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Herramientas online y completamente gratuitas para unir PDF, separar PDF, comprimir PDF, convertir documentos Office a PDF, PDF a JPG y JPG a PDF. No se necesita instalación.</p>", unsafe_allow_html=True)

# Definir las herramientas
tools = [
    {"name": "Unir PDF", "icon": "🔗", "description": "Une PDFs en el orden que prefieras. ¡Rápido y fácil!"},
    {"name": "Dividir PDF", "icon": "✂️", "description": "Extrae una o varias páginas de tu PDF o convierte cada página del PDF en un archivo PDF independiente."},
    {"name": "Comprimir PDF", "icon": "📦", "description": "Consigue que tu documento PDF pese menos y, al mismo tiempo, mantener la máxima calidad posible. Optimiza tus archivos PDF."},
    {"name": "PDF a Word", "icon": "📄", "description": "Convierte fácilmente tus archivos PDF a DOCX de WORD editables."},
    {"name": "PDF a PowerPoint", "icon": "📊", "description": "Convierte tus archivos PDF a presentaciones PPTX de POWERPOINT."},
    {"name": "PDF a Excel", "icon": "📈", "description": "Extrae directamente datos de PDF a Excel en pocos segundos."}
]

# Crear la cuadrícula de herramientas
st.markdown("<div class='tool-grid'>", unsafe_allow_html=True)
for tool in tools:
    st.markdown(f"""
        <div class='tool-card'>
            <div class='tool-icon'>{tool['icon']}</div>
            <div class='tool-title'>{tool['name']}</div>
            <div class='tool-description'>{tool['description']}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
]

# Crear la cuadrícula de herramientas
st.markdown("<div class='tool-grid'>", unsafe_allow_html=True)
for tool in tools:
    st.markdown(f"""
        <div class='tool-card'>
            <div class='tool-icon'>{tool['icon']}</div>
            <div class='tool-title'>{tool['name']}</div>
            <div class='tool-description'>{tool['description']}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Sección de carga de archivo (oculta por defecto)
if st.button("Cargar PDF"):
    uploaded_file = st.file_uploader("Selecciona tu PDF", type="pdf")
    if uploaded_file is not None:
        pdf_content = read_pdf(uploaded_file)
        st.success("PDF cargado correctamente")
        if st.button("Analizar PDF"):
            # Aquí iría la lógica de análisis del PDF
            st.info("Analizando PDF...")
            # Simulación de análisis (reemplazar con la lógica real)
            st.json({
                "nombre_archivo": uploaded_file.name,
                "num_paginas": 5,
                "tamaño": "1.2 MB"
            })

# Footer
st.markdown("""
<hr>
<p style='text-align: center; color: #7f8c8d;'>© 2024 Herramientas PDF. Todos los derechos reservados.</p>
""", unsafe_allow_html=True)
