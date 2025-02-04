import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import webbrowser
import re

# Lista para almacenar los enlaces guardados
productos_guardados = []
# Variable para llevar el seguimiento de la página actual
pagina_actual = 6

# Función para buscar precios en Amazon.es y extraer datos automáticamente
def buscar_precios():
    global pagina_actual
    palabra_clave = entrada_palabra_clave.get().strip()
    if palabra_clave:
        etiqueta_resultado.config(text=f"Buscando precios para: {palabra_clave} en Amazon.es")

        # Configuración del navegador con Selenium
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Ejecutar en modo headless
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        productos_guardados.clear()  # Limpiar resultados anteriores

        # Iterar por las primeras 5 páginas de resultados
        for pagina in range(1, 6):
            url = f'https://www.amazon.es/s?k={palabra_clave.replace(" ", "+")}&page={pagina}'
            driver.get(url)
            time.sleep(3)  # Esperar para que la página cargue

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            productos = soup.find_all('div', {'data-component-type': 's-search-result'})

            for producto in productos:
                nombre = producto.h2.text.strip() if producto.h2 else 'Sin nombre'
                enlace_tag = producto.find('a', href=True)
                enlace = 'https://www.amazon.es' + enlace_tag['href'] if enlace_tag else 'Sin enlace'
                precio_tag = producto.find('span', 'a-offscreen')
                precio = precio_tag.text.strip() if precio_tag else '0 €'

                # Calcular €/kg y €/L si es posible
                precio_por_kg, precio_por_l = extraer_precio_por_unidad(nombre, precio)

                productos_guardados.append({
                    "nombre": nombre,
                    "precio": precio,
                    "link": enlace,
                    "precio_kg": precio_por_kg,
                    "precio_l": precio_por_l
                })

        driver.quit()
        pagina_actual = 6  # Reiniciar el contador de páginas
        actualizar_lista_productos()
    else:
        etiqueta_resultado.config(text="Por favor, introduce una palabra clave.")

# Función para cargar más productos
def cargar_mas_productos():
    global pagina_actual
    palabra_clave = entrada_palabra_clave.get().strip()
    if palabra_clave:
        etiqueta_resultado.config(text=f"Cargando más productos para: {palabra_clave} (página {pagina_actual})")

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = f'https://www.amazon.es/s?k={palabra_clave.replace(" ", "+")}&page={pagina_actual}'
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        productos = soup.find_all('div', {'data-component-type': 's-search-result'})

        for producto in productos:
            nombre = producto.h2.text.strip() if producto.h2 else 'Sin nombre'
            enlace_tag = producto.find('a', href=True)
            enlace = 'https://www.amazon.es' + enlace_tag['href'] if enlace_tag else 'Sin enlace'
            precio_tag = producto.find('span', 'a-offscreen')
            precio = precio_tag.text.strip() if precio_tag else '0 €'

            # Calcular €/kg y €/L si es posible
            precio_por_kg, precio_por_l = extraer_precio_por_unidad(nombre, precio)

            productos_guardados.append({
                "nombre": nombre,
                "precio": precio,
                "link": enlace,
                "precio_kg": precio_por_kg,
                "precio_l": precio_por_l
            })

        driver.quit()
        pagina_actual += 1
        actualizar_lista_productos()

# Función para extraer precio por kg o por L
def extraer_precio_por_unidad(nombre, precio):
    nombre = nombre.lower()
    precio_numerico = extraer_precio(precio)

    # Buscar patrones de cantidad y unidad
    patrones = [
        (r'(\d+(?:[.,]\d+)?)\s?(kg|kilogramo|kilogramos)', 'kg'),
        (r'(\d+(?:[.,]\d+)?)\s?(g|gramo|gramos)', 'g'),
        (r'(\d+(?:[.,]\d+)?)\s?(l|litro|litros)', 'l'),
        (r'(\d+(?:[.,]\d+)?)\s?(ml|mililitro|mililitros)', 'ml')
    ]

    for patron, unidad in patrones:
        match = re.search(patron, nombre)
        if match:
            cantidad = float(match.group(1).replace(',', '.'))

            if unidad == 'kg':
                return round(precio_numerico / cantidad, 2), ''
            elif unidad == 'g':
                return round(precio_numerico / (cantidad / 1000), 2), ''
            elif unidad == 'l':
                return '', round(precio_numerico / cantidad, 2)
            elif unidad == 'ml':
                return '', round(precio_numerico / (cantidad / 1000), 2)

    return '', ''

# Función para actualizar la tabla de productos en la interfaz
def actualizar_lista_productos():
    for item in tree.get_children():
        tree.delete(item)
    for producto in productos_guardados:
        tree.insert("", "end", values=(producto['nombre'], producto['precio'], producto['precio_kg'], producto['precio_l'], producto['link']))

# Función para abrir el enlace en el navegador al hacer doble clic
def abrir_enlace(event):
    item = tree.selection()
    if item:
        enlace = tree.item(item, 'values')[4]
        if enlace != 'Sin enlace':
            webbrowser.open_new_tab(enlace)

# Función para extraer el valor numérico del precio
def extraer_precio(precio_str):
    match = re.search(r'\d+[\.,]?\d*', precio_str.replace('.', '').replace(',', '.'))
    return float(match.group()) if match else 0.0

# Funciones para ordenar

def ordenar_por_precio_mayor():
    productos_guardados.sort(key=lambda x: extraer_precio(x['precio']), reverse=True)
    actualizar_lista_productos()

def ordenar_por_precio_menor():
    productos_guardados.sort(key=lambda x: extraer_precio(x['precio']))
    actualizar_lista_productos()

def ordenar_por_precio_kg():
    productos_guardados.sort(key=lambda x: x['precio_kg'] if isinstance(x['precio_kg'], float) else float('inf'))
    actualizar_lista_productos()

def ordenar_por_precio_l():
    productos_guardados.sort(key=lambda x: x['precio_l'] if isinstance(x['precio_l'], float) else float('inf'))
    actualizar_lista_productos()

# Configuración de la interfaz gráfica
ventana = tk.Tk()
ventana.title("Buscador de Precios Automático en Amazon.es")
ventana.geometry("1000x600")

# Etiqueta y entrada para la palabra clave
etiqueta_palabra_clave = ttk.Label(ventana, text="Introduce una palabra clave:")
etiqueta_palabra_clave.pack(pady=10)

entrada_palabra_clave = ttk.Entry(ventana, width=50)
entrada_palabra_clave.pack(pady=5)

# Botón de búsqueda
boton_buscar = ttk.Button(ventana, text="Buscar en Amazon.es", command=buscar_precios)
boton_buscar.pack(pady=5)

# Botón para cargar más productos
boton_cargar_mas = ttk.Button(ventana, text="Cargar Más Productos", command=cargar_mas_productos)
boton_cargar_mas.pack(pady=5)

# Botones para ordenar por precio
frame_botones = ttk.Frame(ventana)
frame_botones.pack(pady=5)

boton_ordenar_mayor = ttk.Button(frame_botones, text="Ordenar por Precio (Mayor a Menor)", command=ordenar_por_precio_mayor)
boton_ordenar_mayor.pack(side="left", padx=5)

boton_ordenar_menor = ttk.Button(frame_botones, text="Ordenar por Precio (Menor a Mayor)", command=ordenar_por_precio_menor)
boton_ordenar_menor.pack(side="left", padx=5)

boton_ordenar_kg = ttk.Button(frame_botones, text="Ordenar por €/kg", command=ordenar_por_precio_kg)
boton_ordenar_kg.pack(side="left", padx=5)

boton_ordenar_l = ttk.Button(frame_botones, text="Ordenar por €/L", command=ordenar_por_precio_l)
boton_ordenar_l.pack(side="left", padx=5)

# Etiqueta para mostrar el estado de la búsqueda
etiqueta_resultado = ttk.Label(ventana, text="", justify="left")
etiqueta_resultado.pack(pady=10)

# Tabla para mostrar los productos guardados
columnas = ("Nombre", "Precio", "€/kg", "€/L", "Enlace")
tree = ttk.Treeview(ventana, columns=columnas, show='headings')

# Definición de los encabezados de la tabla
for col in columnas:
    tree.heading(col, text=col)
    tree.column(col, width=180 if col != "Precio" else 100)

# Barra de desplazamiento para la tabla
scrollbar = ttk.Scrollbar(ventana, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)

# Asociar evento de doble clic para abrir el enlace
tree.bind("<Double-1>", abrir_enlace)

# Posicionamiento de la tabla y la barra de desplazamiento
tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

ventana.mainloop()
