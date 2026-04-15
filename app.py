import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración corporativa
st.set_page_config(page_title="Dashboard El Tejar", layout="wide")

# LOGIN
def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
    if not st.session_state["login_ok"]:
        st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario == "presidente" and password == "Tejar2026":
                st.session_state["login_ok"] = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

if check_password():
    st.title("📊 Informe Diario de Actividades")
    st.subheader("Fecha: 14 de Abril de 2026")
    
    # KPIs SUPERIORES con datos reales del informe
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orujo Recibido (Hoy)", "2,299,900 kg") # [cite: 27]
    c2.metric("Existencias Hueso", "27,694,950 kg") # 
    c3.metric("Energía Baena 25MW", "450,634 kWh", "+34,465") # 
    c4.metric("Aceite Ext. Tejar", "31,800 kg", "-11,600", delta_color="inverse") # 

    st.markdown("---")

    # GRÁFICOS
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.write("### ⚡ Generación Eléctrica vs Óptimo (kWh)")
        # Datos del informe 
        df_elec = pd.DataFrame({
            "Planta": ["Vetejar 12.6", "Baena 25MW", "Algodonales 5.3"],
            "Real": [226344, 450634, 119229],
            "Óptimo": [223608, 416169, 105737]
        })
        fig = px.bar(df_elec, x="Planta", y=["Real", "Óptimo"], barmode="group", color_discrete_sequence=['#2E7D32', '#A5D6A7'])
        st.plotly_chart(fig, use_container_width=True)

    with col_der:
        st.write("### 📢 Noticias y Resumen")
        st.success("**Nota del día:** La generación eléctrica ha sido excelente, especialmente en Baena 25MW y Algodonales, superando ambos sus valores óptimos.")
        st.info("💡 **Dato clave:** Las existencias de hoja de olivo ascienden a 57,655,131 kg.")
        
        st.markdown("""
        **Noticias del Sector:**
        * [Evolución precio biomasa 2026](#)
        * [Nuevas ayudas a extractoras](#)
        """)
