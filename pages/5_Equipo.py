
import streamlit as st
from PIL import Image

st.title("Equipo del Proyecto")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.image("assets/WhatsApp Image 2026-06-03 at 6.25.28 PM.jpeg", width=200)
    st.subheader("Carolina Bechara")
    st.markdown("Comerciante Internacional — Área Comercial")

with col2:
    img = Image.open("assets/IMG_3866 (1).jpg").rotate(-90, expand=True)
    st.image(img, width=200)
    st.subheader("Santiago Cano")
    st.markdown("Comerciante Internacional — Área Comercial")