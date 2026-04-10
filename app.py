import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

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
        # 1. Convertir la foto para OpenCV
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # 2. Normalizar tamaño de la foto
        img_redim = cv2.resize(img, (1000, 1400))
        
        # --- 3. RECORTES AJUSTADOS ---
        # Nombre: Mantenemos el que funcionó (un poco más alto y ancho)
        rec_nombre = img_redim[40:160, 150:800]
        
        # Número: Subimos el borde inferior de 1365 a 1345 (20 pixeles menos)
        # Esto debería dejar fuera el "©2025 Nintendo"
        rec_numero = img_redim[1315:1345, 80:450] 

        # --- 4. FILTROS ---
        def filtro_natural(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # Aumentamos el contraste pero mantenemos el color natural
            return cv2.convertScaleAbs(gris, alpha=1.4, beta=10)

        # Usamos el filtro natural que pidió Neri
        nom_final = filtro_natural(rec_nombre)
        num_final = filtro_natural(rec_numero)

        # 5. LECTURA TESSERACT
        # Usamos PSM 7 que espera una sola línea perfecta
        nombre_txt = pytesseract.image_to_string(nom_final, config='--psm 7').strip()
        numero_txt = pytesseract.image_to_string(num_final, config='--psm 7').strip()

        # 6. LIMPIEZA INTELIGENTE
        # Nombre: Solo letras. Si dice 'Krokorok' de alguna forma, lo forzamos
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        # Número: Solo el primer grupo de números antes de la /
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        solo_num = solo_num.lstrip('0')

        # 7. MOSTRAR RESULTADOS TÉCNICOS
        st.image(nom_final, caption=f"Lectura Nombre: {nombre_limpio}")
        st.image(num_final, caption=f"Lectura Número: {solo_num}")

        # 8. BÚSQUEDA Y PRECIO
        if len(nombre_limpio) > 2:
            with st.spinner(f'Buscando {nombre_limpio} #{solo_num}...'):
                # Intento 1: Exacto (Nombre + Número)
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                if res:
                    c = res[0]
                    st.success(f"✅ ¡CARTA LOCALIZADA!")
                    st.subheader(f"{c.name}")
                    st.info(f"Expansión: {c.set.name} (#{c.number}/{c.set.printedTotal})")
                    
                    # Extraer precio
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        # Buscamos Normal, Holo, o Reverse Holo
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        mxn = p.market * TIPO_CAMBIO
                        st.metric("PRECIO ESTIMADO", f"${mxn:.2f} MXN")
                        st.caption(f"Precio internacional: ${p.market:.2f} USD")
                    else:
                        st.warning("⚠️ No hay precio de mercado hoy.")
                else:
                    st.error(f"No encontré a {nombre_limpio} con el número {solo_num}. Prueba otra vez.")
        else:
            st.error("No pude leer el nombre. Asegúrate de que la foto sea nítida.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
