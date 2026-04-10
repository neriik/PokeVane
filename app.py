import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

# --- CONFIGURACIÓN ESTÉTICA ---
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Gold", page_icon="✨", layout="centered")

# Estilo corregido (Cambiado unsafe_allow_stdio por unsafe_allow_html)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black', sans-serif; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ PokéVane Gold Edition")
st.write("---")

# --- MENÚ DE ENTRADA ---
tab_galeria, tab_camara = st.tabs(["📁 Subir de Galería", "📸 Usar Cámara"])

foto_vane = None

with tab_galeria:
    galeria = st.file_uploader("Selecciona la mejor foto de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_camara:
    st.info("💡 Tip: Para mejor enfoque, usa la cámara normal y sube la foto desde Galería.")
    camara = st.camera_input("Escanear")
    if camara: foto_vane = camara

# --- LÓGICA DE PROCESAMIENTO ---
if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes calibrados
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
            with st.spinner('🌟 ¡Consultando la Pokédex...!'):
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    st.balloons() # ¡Efecto de globos!
                    
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
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${val_mxn:.2f}")
                        m2.metric("PRECIO USD", f"${val_usd:.2f}")
                        st.caption("✨ Precios basados en TCGPlayer Market Price")
                    else:
                        st.warning("💎 Carta identificada, pero no tiene un precio de mercado activo.")
                else:
                    st.error("❌ No encontré esa carta. Revisa que el nombre y el número se vean bien.")
        
        # Detalles técnicos escondidos
        with st.expander("🛠️ Ver ajustes técnicos"):
            st.image(nom_f, caption=f"Lectura Nombre: {nombre_limpio}")
            st.image(num_f, caption=f"Lectura Número: {solo_num}")

    except Exception as e:
        st.error(f"¡Ups! Algo falló en el escaneo: {e}")
