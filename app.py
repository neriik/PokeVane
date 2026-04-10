import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card

# --- CONFIGURACIÓN ---
TIPO_CAMBIO = 18.20
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

# --- CSS PARA EL LOOK ELÉCTRICO ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    [data-testid="stMetricLabel"] { color: #3b4cca !important; font-weight: bold; }
    div[data-testid="stMetric"] { 
        background-color: #ffcb05; 
        padding: 20px; 
        border-radius: 20px; 
        border: 3px solid #3b4cca;
    }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    .stAlert { border-radius: 20px; border: 2px solid #ffcb05; background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA CON JOLTEON ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nSubre tu foto para ver cuánto vale tu tesoro.")

st.divider()

# --- PESTAÑAS ---
tab_gal, tab_cam = st.tabs(["📁 Galería (Mejor Enfoque)", "📸 Cámara"])
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
        
        # Recortes de precisión
        rec_nombre = img_redim[40:160, 150:800]
        rec_numero = img_redim[1305:1345, 100:450] 

        def filtro_vane(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        # OCR
        n_txt = pytesseract.image_to_string(filtro_vane(rec_nombre), config='--psm 3').strip()
        u_txt = pytesseract.image_to_string(filtro_vane(rec_numero), config='--psm 3').strip()

        # Limpieza
        nom_l = "".join(filter(str.isalpha, n_txt))
        if any(x in n_txt.lower() for x in ["krok", "rokor", "korok"]): nom_l = "Krokorok"
        
        num_l = "".join(filter(str.isdigit, u_txt.split('/')[0] if '/' in u_txt else u_txt))
        if len(num_l) > 3: num_l = num_l[:3]
        num_l = num_l.lstrip('0')

        if len(nom_l) > 2:
            with st.spinner('🌟 Buscando en la Pokédex...'):
                res = Card.where(q=f'name:"{nom_l}" number:"{num_l}"')
                if not res: res = Card.where(q=f'name:"{nom_l}"')
                
                if res:
                    c = res[0]
                    st.success(f"### 🔴 ¡CARTA LOCALIZADA! 🔴")
                    
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**{c.name}**")
                        st.write(f"Serie: {c.set.name}")
                        st.write(f"ID: #{c.number}/{c.set.printedTotal}")
                    with c2:
                        st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/28.png", width=120)
                        st.caption("¡Sandslash te ayuda!")

                    # Precios
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        v_usd = p.market
                        st.divider()
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${v_usd * TIPO_CAMBIO:.2f}")
                        m2.metric("PRECIO USD", f"${v_usd:.2f}")
                    else:
                        st.warning("💎 Carta encontrada, pero sin precio hoy.")
        
        with st.expander("🛠️ Detalles técnicos"):
            st.image(filtro_vane(rec_nombre), caption=nom_l)
            st.image(filtro_vane(rec_numero), caption=num_l)

    except Exception as e:
        st.error(f"¡Ups! Revisa esto: {e}")
