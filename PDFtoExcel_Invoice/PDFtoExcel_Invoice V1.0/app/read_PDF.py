import tkinter as tk
from tkinter import filedialog
import PyPDF2

def seleccionar_pdf():
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de tkinter
    ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
    if ruta_archivo:
        leer_pdf(ruta_archivo)
    root.destroy()

def leer_pdf(ruta_archivo):
    try:
        with open(ruta_archivo, 'rb') as archivo:
            lector_pdf = PyPDF2.PdfReader(archivo)
            num_paginas = len(lector_pdf.pages)
            
            print(f"\nContenido del archivo PDF: {ruta_archivo}\n")
            print("-" * 50)
            
            for pagina in range(num_paginas):
                contenido = lector_pdf.pages[pagina].extract_text()
                print(f"\nPágina {pagina + 1}:\n")
                print(contenido)
                print("-" * 50)
    except Exception as e:
        print(f"Error al leer el archivo PDF: {str(e)}")