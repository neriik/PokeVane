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
        
        # --- RECORTE CALIBRADO ---
        # Nombre: Un poco más alto para captar bien las letras
        rec_nombre = img_redim[40:160, 150:800]
        # Número: Más a la IZQUIERDA (desde 150) para captar el 058/086 completo
        rec_numero = img_redim[1300:1375, 150:550] 

        # --- FILTRO DE ALTO CONTRASTE (PARA LETRAS BLANCAS) ---
        def filtro_fuerte(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # Invertimos para que las letras blancas sean negras (clave para OCR)
            _, binaria = cv2.threshold(gris, 150, 255, cv2.THRESH_BINARY_INV)
            return binaria

        nom_f = filtro_fuerte(rec_nombre)
        num_f = filtro_fuerte(rec_numero)

        # Configuramos Tesseract para buscar una sola línea
        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 7').strip()

        # Limpieza inteligente
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Extraer el número (el 058)
        partes = numero_txt.split('/')
        solo_num = "".join(filter(str.isdigit, partes[0]))
        solo_num = solo_num.lstrip('0')

        st.image(nom_f, caption=f"Lectura Nombre: {nombre_limpio}")
        st.image(num_f, caption=f"Lectura Número: {solo_num}")

        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio} #{solo_num}...'):
                # Búsqueda Exacta
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
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
                        st.warning("Sin precio disponible.")
                else:
                    st.error(f"No encontré a {nombre_limpio} #{solo_num}. Prueba otra vez.")
    except Exception as e:
        st.error(f"Error: {e}")
