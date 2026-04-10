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
        
        # --- RECORTES SOLICITADOS POR NERI ---
        # Nombre: Mantenemos el área segura
        rec_nombre = img_redim[40:160, 150:800]
        
        # Número: Subimos la ubicación y ampliamos 10px la altura
        # Antes era [1315:1345], ahora [1305:1345] para subirlo y darle aire
        rec_numero = img_redim[1305:1345, 100:450] 

        def filtro_n(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        nom_f = filtro_n(rec_nombre)
        num_f = filtro_n(rec_numero)

        # Lectura con configuración PSM 3 (más flexible para detectar texto)
        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 3').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 3').strip()

        # Limpieza de Nombre
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Limpieza de Número (Buscamos solo el primer bloque antes de la diagonal)
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        # Si leyó algo muy largo, tomamos solo los primeros 3 dígitos
        if len(solo_num) > 3: solo_num = solo_num[:3]
        solo_num = solo_num.lstrip('0')

        st.image(nom_f, caption=f"Lectura Nombre: {nombre_limpio}")
        st.image(num_f, caption=f"Lectura Número: {solo_num}")

        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio} #{solo_num}...'):
                # Prioridad 1: Nombre y Número
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                # Prioridad 2: Solo nombre (Respaldo)
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡CARTA LOCALIZADA!")
                    st.subheader(f"{c.name}")
                    st.info(f"Expansión: {c.set.name} (#{c.number}/{c.set.printedTotal})")
                    
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO MXN", f"${mxn:.2f}")
                else:
                    st.error(f"No encontré a {nombre_limpio} en la base de datos.")
        else:
            st.error("No pude leer el nombre. Revisa el enfoque.")

    except Exception as e:
        st.error(f"Error: {e}")
