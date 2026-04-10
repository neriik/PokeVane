import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

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
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nEscanea cualquier carta. Si no la leo a la primera, intenta acercarte al nombre.")

st.divider()

tab_gal, tab_cam = st.tabs(["📁 Galería", "📸 Cámara"])
foto_vane = None

with tab_gal:
    galeria = st.file_uploader("Sube tu foto aquí", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria
with tab_cam:
    camara = st.camera_input("Escanear ahora")
    if camara: foto_vane = camara

if foto_vane:
    try:
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Filtro de nitidez
        gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
        final_img = cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        # --- ESTRATEGIA DE LECTURA ---
        # 1. Intentamos los recortes que calibramos (Plan A)
        rec_nom = final_img[40:160, 150:800]
        rec_num = final_img[1300:1370, 50:500]
        
        nom_txt = pytesseract.image_to_string(rec_nom, config='--psm 3').strip()
        num_txt = pytesseract.image_to_string(rec_num, config='--psm 3').strip()

        # Limpieza básica
        def limpiar_nom(t):
            res = "".join(filter(str.isalpha, t))
            if any(x in t.lower() for x in ["krok", "rokor", "korok"]): return "Krokorok"
            return res

        nombre = limpiar_nom(nom_txt)
        numero = "".join(filter(str.isdigit, num_txt.split('/')[0] if '/' in num_txt else num_txt))[:3].lstrip('0')

        # 2. SI EL PLAN A FALLA (PLAN B: Leer toda la franja superior)
        if len(nombre) < 3:
            franja_sup = final_img[30:250, 50:950]
            nom_txt_b = pytesseract.image_to_string(franja_sup, config='--psm 11').strip()
            nombre = limpiar_nom(nom_txt_b)

        # Mostramos qué estamos viendo
        with st.expander("🛠️ Ver qué está leyendo PokéVane"):
            st.image(rec_nom, caption=f"Detectado arriba: {nombre}")
            st.image(rec_num, caption=f"Detectado abajo: {numero}")

        if len(nombre) >= 3:
            with st.spinner(f'Buscando {nombre}...'):
                # Búsqueda flexible
                query = f'name:"{nombre}"'
                if numero: query += f' number:"{numero}"'
                
                res = Card.where(q=query)
                
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
                        st.write(f"**💎 Rareza:** {c.rarity if c.rarity else 'N/A'}")

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
                    st.error(f"No encontré a '{nombre}' en la base de datos. Revisa si el nombre está bien escrito.")
        else:
            st.warning("⚠️ No pude leer el nombre. Intenta que el nombre del Pokémon se vea muy grande en la foto.")

    except Exception as e:
        # Esto evita el error rojo feo y nos da una pista
        st.info("💡 Tip: Asegúrate de que la carta esté bien derecha y con buena luz.")
        print(f"Error técnico: {e}")
