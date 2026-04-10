import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image

# TIPO DE CAMBIO
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Pro", layout="centered")

st.title("⚡ PokéVane Pro")
st.write("Mejores resultados: Usa fotos nítidas y bien iluminadas.")

# --- OPCIONES DE ENTRADA ---
tab1, tab2 = st.tabs(["📸 Usar Cámara", "📁 Subir Foto"])

foto_vane = None

with tab1:
    camara = st.camera_input("Enfoca el nombre y el número")
    if camara:
        foto_vane = camara

with tab2:
    galeria = st.file_uploader("Selecciona una foto de tu galería", type=['jpg', 'jpeg', 'png'])
    if galeria:
        foto_vane = galeria

# --- PROCESAMIENTO ---
if foto_vane:
    try:
        # Convertir a imagen de OpenCV
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # Normalizar tamaño para que los recortes funcionen
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes (Ajustados según nuestras pruebas exitosas)
        rec_nombre = img_redim[45:155, 180:780]
        rec_numero = img_redim[1300:1395, 40:350]

        # Procesamiento para OCR
        def limpiar_imagen(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.threshold(gris, 150, 255, cv2.THRESH_BINARY_INV)[1]

        nom_ocr = limpiar_imagen(rec_nombre)
        num_ocr = limpiar_imagen(rec_numero)

        # Mostrar qué está viendo la app para que Vane sepa si enfocó bien
        st.image(rec_nombre, caption="Lo que PokéVane leyó arriba")
        
        # Lectura Tesseract
        lectura_nom = pytesseract.image_to_string(nom_ocr, config='--psm 7').strip()
        lectura_num = pytesseract.image_to_string(num_ocr, config='--psm 7').strip()

        # Limpieza de datos
        nombre_limpio = "".join(filter(str.isalpha, lectura_nom))
        # Si detectamos Krokorok o algo similar, lo forzamos (opcional)
        if "Krokorok" in nombre_limpio: nombre_limpio = "Krokorok"
        
        solo_num = lectura_num.split('/')[0] if '/' in lectura_num else lectura_num
        solo_num = solo_num.lstrip('0')

        if nombre_limpio:
            st.divider()
            st.header(f"🔍 {nombre_limpio} #{solo_num}")
            
            with st.spinner('Consultando base de datos mundial...'):
                query = f'name:"{nombre_limpio}" number:"{solo_num}"'
                resultados = Card.where(q=query)
                
                if resultados:
                    c = resultados[0]
                    st.success(f"✅ ¡CARTA ENCONTRADA! ({c.set.name})")
                    
                    # Precios
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        precios = c.tcgplayer.prices
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        val_usd = p.market
                        st.metric("VALOR ACTUAL (MXN)", f"${val_usd * TIPO_CAMBIO:.2f}")
                        st.caption(f"Valor internacional: ${val_usd:.2f} USD")
                    else:
                        st.warning("⚠️ No hay precio de mercado hoy.")
                else:
                    st.error("No se encontró la carta exacta. Prueba con una foto más clara.")
    except Exception as e:
        st.error(f"Hubo un detalle: {e}")
