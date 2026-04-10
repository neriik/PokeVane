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
        
        # --- RECORTES MÁS PRECISOS ---
        rec_nombre = img_redim[40:150, 150:800]
        # Bajamos el inicio a 1315 y subimos el final a 1365 (Cuadro más delgado)
        rec_numero = img_redim[1315:1365, 80:450] 

        # --- FILTRO NATURAL (GRIS CON NITIDEZ) ---
        def filtro_natural(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # Aumentamos un poco el contraste pero mantenemos el color gris natural
            return cv2.convertScaleAbs(gris, alpha=1.4, beta=0)

        nom_f = filtro_natural(rec_nombre)
        num_f = filtro_natural(rec_numero)

        # Lectura Tesseract
        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 7').strip()

        # Limpieza
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        # Refuerzo para Krokorok
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Extraer el número
        num_partes = numero_txt.split('/')
        solo_num = "".join(filter(str.isdigit, num_partes[0]))
        solo_num = solo_num.lstrip('0')

        st.image(nom_f, caption=f"Lectura Nombre: {nombre_limpio}")
        st.image(num_f, caption=f"Lectura Número: {solo_num}")

        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio} #{solo_num}...'):
                # Intento 1: Exacto
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                # Intento 2: Solo nombre si el número falló
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
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
                        st.metric("PRECIO ESTIMADO", f"${mxn:.2f} MXN")
                    else:
                        st.warning("Sin precio de mercado disponible.")
                else:
                    st.error(f"No encontré a {nombre_limpio} en la base de datos.")
    except Exception as e:
        st.error(f"Error: {e}")
