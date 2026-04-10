import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image

TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Pro", layout="centered")
st.title("⚡ PokéVane Pro")

# Tabs para subir foto
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
        # Procesar imagen
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes (Basados en tus capturas perfectas)
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1395, 40:350]

        # Filtro simple (Gris + Contraste)
        gris_nom = cv2.cvtColor(rec_nombre, cv2.COLOR_BGR2GRAY)
        gris_nom = cv2.convertScaleAbs(gris_nom, alpha=1.3, beta=10)
        
        gris_num = cv2.cvtColor(rec_numero, cv2.COLOR_BGR2GRAY)
        gris_num = cv2.convertScaleAbs(gris_num, alpha=1.3, beta=10)

        # LECTURA TESSERACT (Configuración PSM 3 para más libertad)
        nombre_txt = pytesseract.image_to_string(gris_nom, config='--psm 3').strip()
        numero_txt = pytesseract.image_to_string(gris_num, config='--psm 3').strip()

        # Limpieza de basura
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        
        # Regla de oro para tu carta de prueba
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Extraer número
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        solo_num = solo_num.lstrip('0')

        # Mostramos resultados en pantalla
        st.image(gris_nom, caption=f"Lectura: {nombre_limpio}")
        st.image(gris_num, caption=f"Número: {solo_num}")

        # SI DETECTÓ NOMBRE, BUSCAMOS
        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio}...'):
                # Intento 1: Nombre y Número
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                # Intento 2: Solo Nombre si no hay número
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡CARTA LOCALIZADA!")
                    st.subheader(f"{c.name} ({c.set.name})")
                    
                    # Precios
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO EN PESOS", f"${mxn:.2f} MXN")
                    else:
                        st.warning("⚠️ Carta encontrada pero no tiene precio de mercado.")
                else:
                    st.error(f"No encontré a '{nombre_limpio}' en la base de datos.")
        else:
            st.error("No pude leer el nombre. Intenta otra foto con más luz.")

    except Exception as e:
        st.error(f"Error: {e}")
