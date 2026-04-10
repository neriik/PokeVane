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
        
        # Recortes exactos
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1395, 40:350]

        # --- FILTRO EQUILIBRADO (SIN QUEMAR) ---
        def limpiar_suave(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # Solo escala de grises con un poco de nitidez
            return cv2.convertScaleAbs(gris, alpha=1.2, beta=10)

        nom_final = limpiar_suave(rec_nombre)
        num_final = limpiar_suave(rec_numero)

        # Configuramos Tesseract para que sea más tolerante
        nombre_txt = pytesseract.image_to_string(nom_final, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(num_final, config='--psm 7').strip()

        # Limpieza de resultados
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        
        # Si detectamos una parte de Krokorok, lo corregimos
        if any(x in nombre_limpio.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        solo_num = solo_num.lstrip('0')

        # Mostramos la imagen gris (más legible)
        st.image(nom_final, caption=f"Lectura: {nombre_limpio}")
        st.image(num_final, caption=f"Número: {solo_num}")

        if nombre_limpio:
            with st.spinner(f'Buscando {nombre_limpio}...'):
                # Intento 1: Nombre + Número
                q = f'name:"{nombre_limpio}" number:"{solo_num}"'
                res = Card.where(q=q)
                
                # Intento 2: Solo nombre si el número falló
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡Encontrada! {c.name}")
                    st.info(f"Set: {c.set.name}")
                    
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO MXN", f"${mxn:.2f}")
                    else:
                        st.warning("No hay precio de mercado disponible.")
                else:
                    st.error("No se encontró en la base de datos.")
    except Exception as e:
        st.error(f"Error: {e}")
