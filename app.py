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
    st.write("### ✨ ¡Hola Vane! \nEscanea tu carta para encontrar su edición exacta.")

st.divider()

foto_vane = st.file_uploader("Sube tu foto o captura", type=['jpg', 'jpeg', 'png'])

if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
        final_img = cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        # 1. Recortes
        rec_nom = final_img[40:160, 150:800]
        rec_num = final_img[1300:1375, 50:600] # Ampliamos un poco para captar el total
        
        nom_txt = pytesseract.image_to_string(rec_nom, config='--psm 3').strip()
        num_txt = pytesseract.image_to_string(rec_num, config='--psm 3').strip()

        # 2. Limpieza de Nombre
        nombre = "".join(filter(str.isalpha, nom_txt))
        if any(x in nom_txt.lower() for x in ["krok", "rokor", "korok"]): nombre = "Krokorok"

        # 3. IDENTIFICACIÓN DE SERIE COMPLETA (Eje: 005/198)
        solo_num = ""
        total_set = ""
        
        if "/" in num_txt:
            partes = num_txt.split('/')
            solo_num = "".join(filter(str.isdigit, partes[0]))
            total_set = "".join(filter(str.isdigit, partes[1]))
        else:
            # Si no leyó la diagonal, intentamos extraer los números que haya
            nums = "".join(filter(str.isdigit, num_txt))
            if len(nums) >= 4: # Probablemente leyó algo como 005198
                solo_num = nums[:3].lstrip('0')
                total_set = nums[3:]
            else:
                solo_num = nums.lstrip('0')

        # Limpiar ceros a la izquierda para la búsqueda
        solo_num = solo_num.lstrip('0') if solo_num else ""

        with st.expander("🛠️ Ver qué está leyendo PokéVane"):
            st.image(rec_nom, caption=f"Detectado: {nombre}")
            st.image(rec_num, caption=f"Detectado: {solo_num} de {total_set}")

        if len(nombre) >= 3:
            with st.spinner(f'Buscando {nombre} #{solo_num}/{total_set}...'):
                # BÚSQUEDA NIVEL MAESTRO: Nombre + Número + Total del Set
                query = f'name:"{nombre}" number:"{solo_num}"'
                if total_set:
                    query += f' set.printedTotal:{total_set}'
                
                res = Card.where(q=query)
                
                # Respaldo por si el total del set falló
                if not res:
                    res = Card.where(q=f'name:"{nombre}" number:"{solo_num}"')

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
                        st.write(f"**💎 Rareza:** {c.rarity if c.rarity else 'Común'}")

                    # Precios
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        pr = c.tcgplayer.prices
                        p = getattr(pr, 'normal', None) or getattr(pr, 'holofoil', None) or getattr(pr, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        v_usd = p.market
                        st.divider()
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${v_usd * TIPO_CAMBIO:.2f}")
                        m2.metric("PRECIO USD", f"${v_usd:.2f}")
                    else:
                        st.warning("Carta encontrada, pero no tiene precio de mercado.")
                else:
                    st.error(f"No encontré la edición exacta de {nombre}.")
        else:
            st.warning("⚠️ No pude leer el nombre. Intenta otra foto.")

    except Exception as e:
        st.info("💡 Tip: Asegúrate de que la carta esté bien derecha.")
