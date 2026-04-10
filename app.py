import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

# --- CONFIGURACIÓN ESTÉTICA ---
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Gold", page_icon="✨", layout="centered")

# Estilo personalizado para ponerlo "bonito"
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    .stAlert { border-radius: 15px; }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("✨ PokéVane Gold Edition")
st.write("---")

# --- MENÚ DE ENTRADA (Galería primero por default) ---
tab_galeria, tab_camara = st.tabs(["📁 Subir de Galería", "📸 Usar Cámara"])

foto_vane = None

with tab_galeria:
    galeria = st.file_uploader("Selecciona la mejor foto de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_camara:
    st.info("Nota: Para mejor enfoque, usa la galería.")
    camara = st.camera_input("Escanear")
    if camara: foto_vane = camara

# --- LÓGICA DE PROCESAMIENTO ---
if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes calibrados (Los que funcionaron perfecto)
        rec_nombre = img_redim[40:160, 150:800]
        rec_numero = img_redim[1305:1345, 100:450] 

        def filtro_vane(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        nom_f = filtro_vane(rec_nombre)
        num_f = filtro_vane(rec_numero)

        # Lectura
        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 3').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 3').strip()

        # Limpieza
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        if len(solo_num) > 3: solo_num = solo_num[:3]
        solo_num = solo_num.lstrip('0')

        if len(nombre_limpio) > 2:
            with st.spinner('🌟 ¡Buscando en la Pokédex de precios...!'):
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.balloons() # ¡Efecto de globos para Vane!
                    
                    st.success(f"### ✅ ¡CARTA LOCALIZADA!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Nombre:** {c.name}")
                        st.write(f"**Serie:** {c.set.name}")
                    with col2:
                        st.write(f"**ID:** #{c.number}/{c.set.printedTotal}")
                    
                    # Precios
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        val_usd = p.market
                        val_mxn = val_usd * TIPO_CAMBIO
                        
                        st.divider()
                        # MÉTRICAS LINDAS
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${val_mxn:.2f}")
                        m2.metric("PRECIO USD", f"${val_usd:.2f}")
                        st.caption("✨ Precios basados en TCGPlayer Market Price")
                    else:
                        st.warning("💎 Carta identificada, pero no tiene un precio de mercado activo.")
                else:
                    st.error("❌ No encontré esa carta. Intenta con una foto más clara.")
        
        # Mostrar recortes al final (como modo técnico para ti, Neri)
        with st.expander("🛠️ Ver detalles técnicos"):
            st.image(nom_f, caption=f"Lectura: {nombre_limpio}")
            st.image(num_f, caption=f"Número: {solo_num}")

    except Exception as e:
        st.error(f"¡Ups! Algo falló: {e}")
