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

# Configuración de logging mejorada
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

# Definir la API key directamente (no recomendado para producción)
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
st.set_page_config(page_title="Analizador Inteligente de Facturas", layout="wide")

# Estilos personalizados
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    :root {
        --primary-color: #3A5199;
        --secondary-color: #4CAF50;
        --background-color: #f5f5f5;
        --text-color: #333;
        --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    body {
        font-family: 'Roboto', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
        line-height: 1.6;
    }
    
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    h1, h2, h3 {
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    h1 {
        font-size: 2.5em;
        margin-top: 2rem;
    }
    
    h2 {
        font-size: 2em;
        margin-top: 1.5rem;
    }
    
    h3 {
        font-size: 1.5em;
        margin-top: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        border-radius: 10px;
        background-color: var(--secondary-color);
        color: white;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        box-shadow: var(--box-shadow);
    }
    
    .stDownloadButton > button {
        width: 100%;
        padding: 0.75rem;
        border-radius: 10px;
        background-color: #008CBA;
        color: white;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background-color: #007B9A;
        box-shadow: var(--box-shadow);
    }
    
    .info-box, .success-box, .warning-box, .factura-details, .asiento-contable, .resumen-general {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--box-shadow);
    }
    
    .success-box {
        border-left: 6px solid var(--secondary-color);
        color: #155724;
    }
    
    .warning-box {
        border-left: 6px solid #ffc107;
        color: #856404;
    }
    
    .dataframe {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid #ddd;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 1.5rem;
        box-shadow: var(--box-shadow);
    }
    
    .dataframe th, .dataframe td {
        text-align: left;
        padding: 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .dataframe th {
        background-color: var(--primary-color);
        color: white;
        font-weight: bold;
    }
    
    .dataframe tr:last-child td {
        border-bottom: none;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .dataframe tr:hover {
        background-color: #e9ecef;
    }
    
    .menu-horizontal {
        display: flex;
        justify-content: center;
        background-color: var(--primary-color);
        padding: 1rem 0;
        margin-bottom: 2rem;
        box-shadow: var(--box-shadow);
    }
    
    .menu-item {
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        margin: 0 0.5rem;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    
    .menu-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Ocultar elementos no deseados */
    #MainMenu, footer, header, [data-testid="stToolbar"] {display: none !important;}
    .stDeployButton {display: none !important;}
</style>
""", unsafe_allow_html=True)

# Menú horizontal
st.markdown("""
<nav class="menu-horizontal">
    <a href="#" class="menu-item">Inicio</a>
    <a href="#sobre-nosotros" class="menu-item">Sobre Nosotros</a>
    <a href="#contacto" class="menu-item">Contacto</a>
</nav>
""", unsafe_allow_html=True)

# Título y descripción
st.markdown("<h1>EINNOVA | Analizador y Transformador Inteligente de Facturas</h1>", unsafe_allow_html=True)
st.markdown("<h2>Transforma tus Facturas con un Solo Click</h2>", unsafe_allow_html=True)

# Sección de carga de archivo
st.markdown("<h3>📤 Sube tu Factura</h3>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Selecciona tu factura en PDF", type="pdf")

def process_factura(pdf_content):
    with st.spinner("Analizando la factura con IA..."):
        try:
            json_data = generate_json_from_pdf(pdf_content)
            
            if json_data is None:
                st.error("No se pudo generar el análisis. Por favor, revisa los logs para más detalles.")
                return

            df = pd.DataFrame([json_data])
            
            st.markdown("<h3>🧾 Detalles de la Factura</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='factura-details'>
                <p><strong>Tipo de servicio/producto:</strong> {json_data.get('tipo_servicio', 'No especificado')}</p>
                <p><strong>Tipo de pago:</strong> {json_data.get('tipo_pago', 'No especificado')}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h3>📝 Asiento Contable</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='asiento-contable'>
                <p>{json_data.get('asiento_contable', 'No se pudo generar el asiento contable')}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h3>📊 Resumen General</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='resumen-general'>
                <p>{df['resumen'].iloc[0] if 'resumen' in df.columns else 'No se pudo generar el resumen general'}</p>
            </div>
            """, unsafe_allow_html=True)

            # Mostrar el DataFrame
            st.markdown("<h3>🔍 Conjunto generado</h3>", unsafe_allow_html=True)
            st.dataframe(df)

            # Gráfico de ejemplo (ajusta según los datos reales de tu JSON)
            if 'importe_total' in json_data:
                fig = px.pie(names=['IVA', 'Base Imponible'], values=[json_data.get('iva', 0), json_data.get('base_imponible', 0)])
                fig.update_layout(
                    title_text='Desglose de la Factura',
                    title_font_size=20,
                    height=500,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Análisis de Factura')
                st.download_button(
                    label="📥 Descargar Informe Excel",
                    data=output.getvalue(),
                    file_name="analisis_factura.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col2:
                if st.button("🔄 Reprocesar Factura"):
                    st.warning("Reprocesando la factura...")
                    process_factura(pdf_content)

        except Exception as e:
            st.error(f"Ocurrió un error durante el procesamiento: {str(e)}")
            logger.exception("Error detallado:")

if uploaded_file is not None:
    try:
        pdf_content = read_pdf(uploaded_file)
        st.markdown('<div class="success-box">✅ PDF leído correctamente</div>', unsafe_allow_html=True)
        logger.info(f"Contenido del PDF: {pdf_content[:500]}...")

        if st.button("🔍 Analizar Factura", key="analyze_button"):
            process_factura(pdf_content)

    except Exception as e:
        st.markdown(f'<div class="warning-box">❌ Error al leer el archivo PDF: {str(e)}</div>', unsafe_allow_html=True)
        logger.exception("Error detallado al leer PDF:")

# Sección "Sobre Nosotros"
st.markdown("<h2 id='sobre-nosotros'>Sobre Nosotros</h2>", unsafe_allow_html=True)
st.markdown("""
    <div class="info-box">
        <p>Einnova es una empresa líder en innovación tecnológica, especializada en soluciones 
        de vanguardia para la gestión empresarial. Nuestro Analizador y Transformador Inteligente 
        de Facturas representa la culminación de años de investigación y desarrollo en el campo 
        de la inteligencia artificial y el procesamiento de documentos.</p>
        
        <p>Con un equipo multidisciplinario de expertos en tecnología, contabilidad y análisis 
        de datos, ofrecemos una herramienta que no solo simplifica la gestión de facturas, sino 
        que también proporciona insights valiosos para la toma de decisiones empresariales.</p>
        
        <p>Nuestra misión es empoderar a las empresas con tecnología inteligente, permitiéndoles 
        optimizar sus procesos, reducir errores y liberar recursos para enfocarse en su crecimiento 
        y expansión.</p>
    </div>
""", unsafe_allow_html=True)

# Sección de Contacto
st.markdown("<h2 id='contacto'>Contacto</h2>", unsafe_allow_html=True)
st.markdown("""
    <div class="info-box">
        <p>Estamos aquí para ayudarte. Si tienes preguntas, necesitas soporte técnico o quieres 
        saber más sobre cómo nuestras soluciones pueden beneficiar a tu empresa, no dudes en 
        contactarnos:</p>
        <ul>
            <li>📧 Email: info@einnova.com</li>
            <li>📞 Teléfono: +34 912 345 678</li>
            <li>🏢 Dirección: Calle Innovación, 123, 28001 Madrid, España</li>
        </ul>
        <p>Nuestro equipo de atención al cliente está disponible de lunes a viernes, 
        de 9:00 a 18:00 horas (CET).</p>
    </div>
""", unsafe_allow_html=True)

# Formulario de contacto
st.markdown("<h3>Envíanos un mensaje</h3>", unsafe_allow_html=True)
with st.form("contact_form"):
    nombre = st.text_input("Nombre")
    email = st.text_input("Email")
    mensaje = st.text_area("Mensaje")
    submit_button = st.form_submit_button("Enviar mensaje")

    if submit_button:
        # Aquí puedes agregar la lógica para manejar el envío del formulario
        st.success("Gracias por tu mensaje. Nos pondremos en contacto contigo pronto.")

# Footer
st.markdown("""
    <hr>
    <p style='text-align: center; color: #7f8c8d;'>
        © 2024 Einnova - Analizador y Transformador Inteligente de Facturas. 
        Todos los derechos reservados.
    </p>
""", unsafe_allow_html=True)
