import openai
import json



def generate_json_from_pdf(pdf_content):
    prompt = f"""
    Analiza el siguiente contenido de una factura PDF y genera un JSON estructurado y detallado. Sé muy preciso y asegúrate de que cada clave tenga un único valor, no listas. Incluye toda la información relevante de la factura.

    Además, realiza las siguientes tareas específicas:
    1. Identifica el tipo de servicio recibido o producto comprado y devuélvelo con el formato "tipo: [descripción breve]".
    2. Identifica el tipo de pago realizado entre estas opciones: pago en efectivo, pago por recibo domiciliado, pago por transferencia y pago por tarjeta. Devuélvelo con el formato "pago: [tipo de pago]". En caso de que no se especifique decir quue no se muestra.
    3. Basándote en la información anterior, proporciona el asiento contable que mejor se ajuste según la contabilidad española. Incluye solo el campo y el valor.

    Contenido del PDF:
    {pdf_content}

    Genera un JSON que incluya todos estos detalles de manera estructurada y precisa.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en contabilidad y análisis de facturas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Temperatura baja para mayor precisión
        )

        # Extraer el contenido JSON de la respuesta
        json_content = response.choices[0].message['content']
        
        # Intentar parsear el JSON para verificar su validez
        parsed_json = json.loads(json_content)
        
        return json.dumps(parsed_json, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error al generar el JSON: {str(e)}"  