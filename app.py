import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

# --- CONFIGURACIÓN ---
TIPO_CAMBIO = 18.20
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    div[data-testid="stMetric"] { background-color: #ffcb05; padding: 20px; border-radius: 20px; border: 3px solid #3b4cca; }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nLas cartas 'ex' brillan mucho, intenta que no les dé la luz directo.")

st.divider()

foto_vane = st.file_uploader("Sube tu foto o captura", type=['jpg', 'jpeg', 'png'])

if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
        # Filtro especial para eliminar brillo (morfología)
        kernel = np.ones((2,2), np.uint8)
        final_img = cv2.morphologyEx(gris, cv2.MORPH_OPEN, kernel)
        final_img = cv2.convertScaleAbs(final_img, alpha=1.6, beta=10)

        # 1. RECORTES DE PRECISIÓN PARA EX
        rec_nom = final_img[35:155, 170:750] # Un poco más arriba
        rec_num = final_img[1315:1355, 140:400] # Super ajustado para evitar el texto de abajo
        
        # Lectura con PSM 11 (ideal para texto con ruido)
        nom_txt = pytesseract.image_to_string(rec_nom, config='--psm 3').strip()
        num_txt = pytesseract.image_to_string(rec_num, config='--psm 7').strip()

        # 2. LIMPIEZA DE NOMBRE (Especial Arcanine/EX)
        # Si detectamos "ex" o algo parecido, limpiamos el resto del ruido
        nombre_crudo = nom_txt.replace('\n', ' ')
        palabras = nombre_crudo.split()
        nombre_limpio = ""
        for p in palabras:
            p_limpia = "".join(filter(str.isalpha, p))
            if len(p_limpia) > 2:
                nombre_limpio = p_limpia
                break
        
        if "rcanine" in nombre_limpio.lower(): nombre_limpio = "Arcanine"

        # 3. IDENTIFICACIÓN DE SERIE
        solo_num = ""
        total_set = ""
        
        # Buscamos números ignorando letras (como el "de" que leyó antes)
        nums_encontrados = re.findall(r'\d+', num_txt)
        if len(nums_encontrados) >= 2:
            solo_num = nums_encontrados[0]
            total_set = nums_encontrados[1]
        elif len(nums_encontrados) == 1:
            # Si solo detectó un bloque (ej: 032198), lo dividimos
            n = nums_encontrados[0]
            if len(n) > 3:
                solo_num = n[:3]
                total_set = n[3:]
            else:
                solo_num = n

        with st.expander("🛠️ Ver ajustes técnicos"):
            st.image(rec_nom, caption=f"Nombre: {nombre_limpio}")
            st.image(rec_num, caption=f"Número: {solo_num}/{total_set}")

        if len(nombre_limpio) >= 3:
            with st.spinner('🌟 Buscando en la base de datos...'):
                # Búsqueda por nombre y número
                query = f'name:"{nombre_limpio}" number:"{solo_num}"'
                res = Card.where(q=query)
                
                # Respaldo solo nombre
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio} ex"')
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')

                if res:
                    c = res[0]
                    st.success(f"### 🔴 ¡CARTA LOCALIZADA! 🔴")
                    col_img, col_info = st.columns([1, 1.2])
                    with col_img:
                        st.image(c.images.large)
                    with col_info:
                        st.write(f"### {c.name}")
                        st.write(f"**Expansión:** {c.set.name}")
                        st.write(f"**ID:** #{c.number}/{c.set.printedTotal}")
                        st.write(f"**💎 Rareza:** {c.rarity}")

                    # Precios
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        pr = c.tcgplayer.prices
                        p = getattr(pr, 'holofoil', None) or getattr(pr, 'normal', None) or getattr(pr, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        v_usd = p.market
                        st.divider()
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${v_usd * TIPO_CAMBIO:.2f}")
                        m2.metric("PRECIO USD", f"${v_usd:.2f}")
                    else:
                        st.warning("Carta encontrada, pero sin precio hoy.")
                else:
                    st.error("No pude encontrar la edición exacta.")
    except Exception as e:
        import re # Necesario para la limpieza de números
        st.info("Tip: Intenta que la foto no tenga reflejos de luz.")
