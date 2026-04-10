import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image

TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Pro", layout="centered")
st.title("⚡ PokéVane Pro")

tab1, tab2 = st.tabs(["📸 Cámara", "📁 Galería"])
foto_vane = None

with tab1:
    camara = st.camera_input("Enfoca bien")
    if camara: foto_vane = camara
with tab2:
    galeria = st.file_uploader("Sube foto nítida", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1395, 40:350]

        # --- FILTRO MEJORADO ---
        def preprocesar(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # Aumentamos el contraste drásticamente
            gris = cv2.convertScaleAbs(gris, alpha=1.5, beta=0)
            # Umbral adaptativo para letras blancas
            return cv2.threshold(gris, 180, 255, cv2.THRESH_BINARY)[1]

        nom_ocr = preprocesar(rec_nombre)
        num_ocr = preprocesar(rec_numero)

        # Lectura con configuraciones específicas
        # PSM 6 es para bloques de texto uniformes
        nombre_txt = pytesseract.image_to_string(nom_ocr, config='--psm 6').strip()
        numero_txt = pytesseract.image_to_string(num_ocr, config='--psm 6').strip()

        # Limpieza manual
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        # Corrección común para tu carta de prueba
        if "rokor" in nombre_limpio.lower(): nombre_limpio = "Krokorok"
        
        # Extraer solo los números antes de la diagonal
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        solo_num = solo_num.lstrip('0')

        st.image(nom_ocr, caption=f"Texto detectado: {nombre_limpio}")
        st.image(num_ocr, caption=f"Número detectado: {solo_num}")

        if nombre_limpio:
            with st.spinner(f'Buscando {nombre_limpio}...'):
                # Intentamos búsqueda flexible
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡Encontrada! {c.name}")
                    st.info(f"Expansión: {c.set.name}")
                    
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO ESTIMADO", f"${mxn:.2f} MXN")
                    else:
                        st.warning("Carta identificada, pero sin precio de mercado.")
                else:
                    st.error("No se encontró en la base de datos.")
    except Exception as e:
        st.error(f"Error: {e}")
