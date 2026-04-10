import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

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
        
        # --- RECORTE QUIRÚRGICO ---
        # Subimos el borde inferior de 1395 a 1360 para EVITAR el año ©2025
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1360, 240:480] # Más a la derecha para captar el 058/086 mejor

        def limpiar(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        nom_f = limpiar(rec_nombre)
        num_f = limpiar(rec_numero)

        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 7').strip()

        # Limpieza inteligente
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Extraer solo el primer grupo de números (el 058)
        numeros_encontrados = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        # Si el número es muy largo (como el año), nos quedamos solo con los últimos 3 dígitos
        solo_num = numeros_encontrados[-3:] if len(numeros_encontrados) > 3 else numeros_encontrados
        solo_num = solo_num.lstrip('0')

        st.image(nom_f, caption=f"Nombre: {nombre_limpio}")
        st.image(num_f, caption=f"Número: {solo_num}")

        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio} #{solo_num}...'):
                # Intento 1: Nombre + Número (Exacto)
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                if res:
                    # Si hay varios, buscamos el que coincida mejor con el total (086)
                    c = res[0]
                    st.success(f"✅ ¡CARTA LOCALIZADA!")
                    st.subheader(f"{c.name}")
                    st.info(f"Expansión: {c.set.name} (#{c.number}/{c.set.printedTotal})")
                    
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        prices = c.tcgplayer.prices
                        p = getattr(prices, 'normal', None) or getattr(prices, 'holofoil', None) or getattr(prices, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO EN PESOS", f"${mxn:.2f} MXN")
                    else:
                        st.warning("Sin precio de mercado disponible.")
                else:
                    st.error(f"No encontré a {nombre_limpio} con el número {solo_num}.")
    except Exception as e:
        st.error(f"Error: {e}")
