import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
import re

# --- CONFIGURACIÓN ---
TIPO_CAMBIO = 18.20
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

# --- CSS LOOK ELÉCTRICO ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    div[data-testid="stMetric"] { background-color: #ffcb05; padding: 20px; border-radius: 20px; border: 3px solid #3b4cca; }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    .stAlert { border-radius: 20px; border: 2px solid #ffcb05; background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nSubre tu foto y deja que Jolteon use su ataque 'Súper Definición'.")

st.divider()

tab_gal, tab_manual = st.tabs(["📁 Subir de Galería", "⌨️ Búsqueda Manual"])
foto_vane = None
manual_ready = False

with tab_gal:
    galeria = st.file_uploader("Selecciona la mejor foto de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_manual:
    m_nom = st.text_input("Nombre del Pokémon", placeholder="Ej: Arcanine")
    m_num = st.text_input("Número de carta", placeholder="Ej: 32")
    m_tot = st.text_input("Total del set (Opcional)", placeholder="Ej: 198")
    if st.button("Buscar ahora 🔍"): manual_ready = True

# --- PROCESAMIENTO ---
if foto_vane or manual_ready:
    try:
        nombre_l, numero_l, total_l = "", "", ""

        if manual_ready:
            nombre_l, numero_l, total_l = m_nom, m_num, m_tot
        else:
            # 1. Convertir imagen
            file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            img_redim = cv2.resize(img, (1000, 1400)) # Agrandamos para más definición
            
            # --- MOTOR DE SÚPER DEFINICIÓN DE DANTE ---
            gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
            
            # PASO A: Borrar ruido respetando bordes (Filtro Bilateral)
            # (d=9, sigmaColor=75, sigmaSpace=75 es el punto dulce)
            denoised = cv2.bilateralFilter(gris, 9, 75, 75)
            
            # PASO B: Afilado (Sharpening)
            # Creamos una máscara para resaltar bordes
            kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharp)
            
            # PASO C: Brillo sutil (el que calibramos antes)
            final_img = cv2.convertScaleAbs(sharpened, alpha=1.2, beta=10)

            # Recortes
            rec_nom = final_img[35:160, 150:850]
            rec_num = final_img[1300:1375, 80:550] # Un pelín más ancho para el 058
            
            # Lectura Tesseract
            # PSM 3 es robusto; PSM 7 es para una línea perfecta
            n_txt = pytesseract.image_to_string(rec_nom, config='--psm 3').strip()
            u_txt = pytesseract.image_to_string(rec_num, config='--psm 7').strip()

            # Limpieza
            nombre_l = "".join(filter(str.isalpha, n_txt.split()[0] if n_txt else ""))
            # Refuerzos de inteligencia
            if "rcanine" in n_txt.lower(): nombre_l = "Arcanine"
            if "krok" in n_txt.lower(): nombre_l = "Krokorok"
            if "cacne" in n_txt.lower(): nombre_l = "Cacnea"

            # Limpieza de números (Buscamos solo el primer grupo de números antes de la /)
            solo_num = "".join(filter(str.isdigit, u_txt.split('/')[0] if '/' in u_txt else u_txt))
            # Si leyó algo muy largo, tomamos solo los primeros 3 dígitos
            if len(solo_num) > 3: solo_num = solo_num[:3]
            numero_l = solo_num.lstrip('0')

            with st.expander("🛠️ Ver ajustes técnicos (Súper Definición Activa)"):
                st.image(rec_nom, caption=f"Leído: {nombre_l}")
                st.image(rec_num, caption=f"Leído: {numero_l}")

        # --- BÚSQUEDA ---
        if len(nombre_l) >= 2:
            with st.spinner('🌟 Buscando en la Pokédex...'):
                q = f'name:"{nombre_l}" number:"{numero_l}"'
                res = Card.where(q=q)
                
                # Respaldos
                if not res: res = Card.where(q=f'name:"{nombre_l}"')
                
                if res:
                    c = res[0]
                    st.success(f"### 🔴 ¡CARTA LOCALIZADA! 🔴")
                    col1, col2 = st.columns([1, 1.2])
                    with col1:
                        st.image(c.images.large)
                    with col2:
                        st.write(f"### {c.name}")
                        st.write(f"**Set:** {c.set.name}")
                        st.write(f"**ID:** #{c.number}/{c.set.printedTotal}")
                        st.write(f"**💎 Rareza:** {c.rarity if c.rarity else 'Común'}")
                    
                    st.divider()
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        pr = c.tcgplayer.prices
                        p = getattr(pr, 'normal', None) or getattr(pr, 'holofoil', None) or getattr(pr, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        v_usd = p.market
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${v_usd * TIPO_CAMBIO:.2f}")
                        m2.metric("PRECIO USD", f"${v_usd:.2f}")
                    else:
                        st.warning("Sin precio disponible.")
                else:
                    st.error("No encontré la carta exacta en la base de datos.")
        else:
            if foto_vane: st.warning("⚠️ No pude leer el nombre. Intenta otra foto.")

    except Exception as e:
        st.error(f"Error: {e}")
