import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image

# Configuración inicial
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Pro", page_icon="⚡")
st.title("⚡ PokéVane Pro v1.0")
st.write("Hola Vane, toma una foto a tu carta para valuarla.")

# El botón que abre la cámara en el iPhone 16
foto_vane = st.camera_input("Enfoca el nombre y el número")

if foto_vane:
    # Convertir la foto para que OpenCV la entienda
    file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    img_redim = cv2.resize(img, (1000, 1400))

    # Recortes (Basados en lo que calibramos hoy)
    rec_nombre = img_redim[45:145, 180:750]
    rec_numero = img_redim[1300:1395, 40:350]

    # Procesamiento
    gris_nom = cv2.cvtColor(rec_nombre, cv2.COLOR_BGR2GRAY)
    _, limpia_nom = cv2.threshold(gris_nom, 150, 255, cv2.THRESH_BINARY_INV)
    lectura_nom = pytesseract.image_to_string(limpia_nom, config='--psm 7').strip()

    gris_num = cv2.cvtColor(rec_numero, cv2.COLOR_BGR2GRAY)
    _, limpia_num = cv2.threshold(gris_num, 150, 255, cv2.THRESH_BINARY_INV)
    lectura_num = pytesseract.image_to_string(limpia_num, config='--psm 7').strip()

    # Limpieza
    nombre_limpio = "".join(filter(str.isalpha, lectura_nom))
    solo_num = lectura_num.split('/')[0] if '/' in lectura_num else lectura_num
    solo_num = solo_num.lstrip('0')

    if nombre_limpio:
        st.subheader(f"🔍 Detectado: {nombre_limpio} #{solo_num}")
        try:
            query = f'name:"{nombre_limpio}" number:"{solo_num}"'
            resultados = Card.where(q=query)
            if resultados:
                c = resultados[0]
                st.success(f"✅ ¡Localizada! - {c.set.name}")
                
                # Precios
                p = None
                if c.tcgplayer and c.tcgplayer.prices:
                    prices = c.tcgplayer.prices
                    p = getattr(prices, 'normal', None) or getattr(prices, 'holofoil', None)
                
                if p and hasattr(p, 'market'):
                    val_usd = p.market
                    st.metric("Valor en Pesos", f"${val_usd * TIPO_CAMBIO:.2f} MXN")
                    st.info(f"Precio en USD: ${val_usd:.2f}")
                else:
                    st.warning("No hay precio de mercado disponible.")
            else:
                st.error("No encontré la carta exacta. Revisa el enfoque.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")