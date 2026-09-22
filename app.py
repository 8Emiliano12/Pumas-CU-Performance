import streamlit as st
from supabase import create_client, Client

# Configuración inicial de interfaz
st.set_page_config(
    page_title="Pumas CU // Human Performance",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estética minimalista oscura tipo 11 Humans
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stApp {
        background-color: #090d16;
        color: #f3f4f6;
    }
    .card-ficha {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background-color: #1e3a8a;
        color: #60a5fa;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Conexión persistente a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# Navegación por Roles
st.sidebar.markdown("## **PUMAS CU**\n*Human Intelligence System*")
rol = st.sidebar.radio("Modo de Acceso:", ["Atleta (Evaluación)", "Psicología (Supervisión & IA)"])

# ----------------------------------------------------
# VISTA 1: ATLETA (CATÁLOGO, FICHA Y APLICACIÓN)
# ----------------------------------------------------
if rol == "Atleta (Evaluación)":
    st.markdown("<span class='badge'>Batería Psicométrica Estandarizada</span>", unsafe_allow_html=True)
    st.title("Catálogo de Instrumentos Clínico-Deportivos")
    
    # Cargar pruebas desde Supabase
    pruebas_res = supabase.table("catalogo_pruebas").select("*").execute()
    pruebas = pruebas_res.data

    if not pruebas:
        st.warning("No se encontraron pruebas registradas en el catálogo.")
        st.stop()

    opciones_pruebas = {p["nombre_oficial"]: p for p in pruebas}
    seleccion = st.selectbox("Selecciona el instrumento a realizar:", list(opciones_pruebas.keys()))
    prueba_activa = opciones_pruebas[seleccion]

    # Ficha Técnica estilo 11 Humans
    st.markdown(f"""
        <div class="card-ficha">
            <h2 style="color: #ffffff; margin-top: 0;">{prueba_activa['nombre_oficial']} ({prueba_activa['codigo']})</h2>
            <p style="color: #9ca3af; font-size: 0.95rem;"><strong>Autores:</strong> {prueba_activa['autores']} ({prueba_activa['año_creacion']})</p>
            <p style="color: #60a5fa; font-size: 0.85rem;"><strong>Baremos y Validación:</strong> {prueba_activa['poblacion_validacion']}</p>
            <hr style="border-color: #1f2937; margin: 16px 0;">
            <p><strong>¿Qué mide?:</strong> {prueba_activa['que_mide']}</p>
            <p style="font-size: 0.85rem; color: #9ca3af;"><strong>Bibliografía Básica:</strong> {prueba_activa['bibliografia_basica']}</p>
            <p style="font-size: 0.85rem; color: #fbbf24;"><strong>Tiempo estimado de respuesta:</strong> ~{prueba_activa['tiempo_estimado_min']} minutos</p>
        </div>
    """, unsafe_allow_html=True)

    # Formulario interactivo
    with st.form("form_aplicacion"):
        st.subheader("Registro de Datos del Atleta")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo:")
            posicion = st.selectbox("Posición:", ["QB", "RB", "WR", "OL", "DL", "LB", "DB", "K/P"])
        with col2:
            unidad = st.selectbox("Unidad:", ["Ofensiva", "Defensiva", "Equipos Especiales"])
            carrera = st.text_input("Facultad y Carrera:")

        st.write("---")
        st.subheader("Reactivos (Escala de 0 = Nunca a 4 = Muy a menudo)")
        
        reactivos = prueba_activa["reactivos_json"]
        respuestas = {}
        escala = {
            "0 - Nunca": 0,
            "1 - Casi nunca": 1,
            "2 - De vez en cuando": 2,
            "3 - A menudo": 3,
            "4 - Muy a menudo": 4
        }

        for r in reactivos:
            val = st.select_slider(
                f"**Item {r['id']}:** {r['texto']}",
                options=list(escala.keys()),
                value="2 - De vez en cuando",
                key=f"item_{r['id']}"
            )
            num = escala[val]
            respuestas[f"item_{r['id']}"] = (4 - num) if r.get("invertida", False) else num

        enviar = st.form_submit_button("Finalizar y Enviar a Revisión")

        if enviar:
            if not nombre.strip():
                st.error("Ingresa el nombre completo del atleta para continuar.")
            else:
                # 1. Guardar atleta en Supabase
                atleta = supabase.table("atletas").insert({
                    "nombre_completo": nombre,
                    "posicion": posicion,
                    "unidad": unidad,
                    "facultad_carrera": carrera
                }).execute().data[0]

                # 2. Scoring PSS-10
                puntaje_total = sum(respuestas.values())
                if puntaje_total <= 13:
                    cat, sem = "Bajo Estrés", "verde"
                elif puntaje_total <= 26:
                    cat, sem = "Estrés Moderado", "amarillo"
                else:
                    cat, sem = "Estrés Elevado", "rojo"

                # 3. Borrador preliminar de IA
                borrador_ia = f"""[ANÁLISIS PRELIMINAR GENERADO POR IA]
Atleta: {nombre} | Posición: {posicion} ({unidad}) | Carrera: {carrera}
Puntaje Total PSS-10: {puntaje_total}/40 ({cat}) - Nivel de Alerta: {sem.upper()}

- Observación Funcional: El deportista presenta un nivel de estrés percibido clasificado como {cat.lower()}. En periodos de alta exigencia táctica o semanas de evaluación académica, se sugiere vigilar la concentración y la retención del playbook.
- Sugerencia Operativa para Staff: Mantener comunicación de vestidor y evaluar si la carga académica actual coincide con sobrecargas de práctica."""

                # 4. Enviar a Supabase para visto bueno clínico
                supabase.table("evaluaciones_atleta").insert({
                    "atleta_id": atleta["id"],
                    "prueba_id": prueba_activa["id"],
                    "respuestas_crudas": respuestas,
                    "puntajes_escalares": {"puntaje_total": puntaje_total, "categoria": cat},
                    "interpretacion_ia": borrador_ia,
                    "estado_revision": "pendiente_revision",
                    "estatus_semaforo": sem
                }).execute()

                st.success("✅ Evaluación registrada correctamente y canalizada a psicología para su visto bueno.")

# ----------------------------------------------------
# VISTA 2: PANEL DEL PSICÓLOGO (VISTO BUENO CLÍNICO)
# ----------------------------------------------------
elif rol == "Psicología (Supervisión & IA)":
    st.markdown("<span class='badge' style='background-color: #065f46; color: #34d399;'>Supervisión Clínica</span>", unsafe_allow_html=True)
    st.title("Panel de Aprobación // Human-in-the-Loop")
    st.write("Supervisa, ajusta y valida las interpretaciones preliminares antes de emitir los reportes al staff.")

    pendientes = supabase.table("evaluaciones_atleta").select("*, atletas(*)").eq("estado_revision", "pendiente_revision").execute().data

    if not pendientes:
        st.info("No hay evaluaciones pendientes de validación.")
    else:
        for ev in pendientes:
            nombre_atl = ev["atletas"]["nombre_completo"]
            pos_atl = ev["atletas"]["posicion"]
            cat_atl = ev["puntajes_escalares"]["categoria"]

            with st.expander(f"📋 {nombre_atl} — {pos_atl} [{cat_atl}]", expanded=True):
                st.markdown(f"**Semáforo Asignado:** `{ev['estatus_semaforo']}` | **Fecha:** {ev['created_at']}")
                st.info(ev["interpretacion_ia"])

                with st.form(f"form_revision_{ev['id']}"):
                    notas_ajustadas = st.text_area("Ajuste Clínico / Dictamen Final:", value=ev["interpretacion_ia"], height=160)
                    firma = st.text_input("Firma de Validación:", value="Lic. Emiliano Guarneros")
                    decision = st.selectbox("Resolución:", ["Aprobar y Emitir al Staff", "Rechazar"])

                    if st.form_submit_button("Validar y Firmar"):
                        estado = "aprobado" if decision == "Aprobar y Emitir al Staff" else "rechazado"
                        supabase.table("evaluaciones_atleta").update({
                            "notas_psicologo": notas_ajustadas,
                            "firma_profesional": firma,
                            "estado_revision": estado
                        }).eq("id", ev["id"]).execute()
                        st.success("Evaluación validada con éxito.")
                        st.rerun()
