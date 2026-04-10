import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image

# Configuración básica
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Pro", layout="centered")
st.title("⚡ PokéVane Pro")

# Pestañas para subir foto
tab1, tab2 = st.tabs(["📸 Cámara Directa", "📁 Galería"])
foto_vane = None

with tab1:
    camara = st.camera_input("Enfoca bien el nombre")
    if camara: foto_vane = camara
with tab2:
    galeria = st.file_uploader("Sube una foto nítida", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

if foto_vane:
    try:
        # Procesar imagen
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes optimizados
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1395, 40:350]

        # OCR
        gris_nom = cv2.cvtColor(rec_nombre, cv2.COLOR_BGR2GRAY)
        limpia_nom = cv2.threshold(gris_nom, 150, 255, cv2.THRESH_BINARY_INV)[1]
        
        gris_num = cv2.cvtColor(rec_numero, cv2.COLOR_BGR2GRAY)
        limpia_num = cv2.threshold(gris_num, 150, 255, cv2.THRESH_BINARY_INV)[1]

        nombre_txt = pytesseract.image_to_string(limpia_nom, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(limpia_num, config='--psm 7').strip()

        # Limpieza
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        solo_num = numero_txt.split('/')[0] if '/' in numero_txt else numero_txt
        solo_num = "".join(filter(str.isdigit, solo_num)) # Solo números

        # Mostrar recortes para control
        st.image(rec_nombre, caption=f"Nombre detectado: {nombre_limpio}")
        st.image(rec_numero, caption=f"Número detectado: {solo_num}")

        if nombre_limpio:
            with st.spinner('Buscando en la base de datos...'):
                # Intento 1: Nombre + Número
                q = f'name:"{nombre_limpio}" number:"{solo_num}"'
                res = Card.where(q=q)
                
                # Intento 2 (Respaldo): Solo nombre si el número falló
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡Encontrada! {c.name} ({c.set.name})")
                    
                    # Extraer precio
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO ESTIMADO", f"${mxn:.2f} MXN")
                    else:
                        st.info("No hay precio de mercado actual, pero la carta es real.")
                else:
                    st.error("No encontré la carta en la base de datos. Intenta otra foto.")
    except Exception as e:
        st.error(f"Error técnico: {e}")
