import streamlit as st
from supabase import create_client, Client

# ==========================================
# 1. CONSTANTES Y CONFIGURACIÓN INICIAL
# ==========================================
SUPABASE_URL = "https://myfhphhabwdeoclioohz.supabase.co"
SUPABASE_KEY = "sb_publishable_zusAZIHZX8hmc7NSg1_vLA_gh1jELGS"

st.set_page_config(
    page_title="MediCuidado",
    page_icon="🏥",
    layout="wide"
)

# ==========================================
# 2. CONEXIÓN A BASE DE DATOS Y ESTADO DE SESIÓN
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Error al conectar con Supabase. Revisa tus credenciales.")
    supabase = None

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None



def vista_login_registro():
    """Maneja el inicio de sesión y registro para usuarios no autenticados."""
    st.title("🏥 Bienvenido a MediCuidado")
    
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse (Pacientes)"])

    # --- PARA QUE LOS USUARIOS PUEDAN INICIAR SESION EN LA APP ---
    with tab_login:
        with st.form("form_login"):
            cedula_login = st.text_input("Cédula")
            clave_login = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Ingresar", use_container_width=True)

        if btn_login:
            res = supabase.table("personas").select("*").eq("cedula", cedula_login).eq("clave", clave_login).execute()
            if res.data:
                st.session_state["usuario_logueado"] = res.data[0]
                st.success("¡Bienvenido/a!")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

    # --- PARA QUE LOS PACIENTES PUEDAN REGISTRARSE CORRECTAMENTE EN LA APP ---
    with tab_registro:
        with st.form("form_registro", clear_on_submit=True):
            nombre = st.text_input("Nombre y Apellido Completo")
            cedula = st.text_input("Número de Cédula")
            clave = st.text_input("Contraseña", type="password")
            confirmar = st.text_input("Confirmar Contraseña", type="password")
            
            btn_registro = st.form_submit_button("Crear Cuenta de Paciente", use_container_width=True)

        if btn_registro:
            if not nombre or not cedula or not clave:
                st.warning("Completa todos los campos.")
            elif clave != confirmar:
                st.error("Las contraseñas no coinciden.")
            else:
                nuevo_paciente = {
                    "nombre": nombre,
                    "cedula": cedula,
                    "clave": clave,
                    "rol": "paciente"
                }
                try:
                    supabase.table("personas").insert(nuevo_paciente).execute()
                    st.success("Cuenta creada exitosamente. Inicia sesión en la pestaña al lado.")
                except Exception as ex:
                    st.error(f"Error al crear la cuenta: {ex}")


def vista_paciente():
    """Portal del Paciente: Ver, agendar, reprogramar y cancelar citas médicas."""
    st.header("👤 Portal del Paciente")
    usuario = st.session_state["usuario_logueado"]
    
    tab1, tab2 = st.tabs(["📅 Mis Citas", "➕ Agendar Turno"])
    
    # --- LOS PACIENTES PUEDEN VER LAS CITAS AGENDADAS,
    # PUEDEN CANCELAR LAS CITAS Y PUEDEN REPROGRAMAR LAS CITAS EN VEZ DE CANCELARLAS ---
    with tab1:
        st.subheader("Próximas Citas Médicas")
        citas_res = supabase.table("consultas").select("*").eq("paciente_id", usuario["id"]).order("fecha_hora", desc=False).execute()
        doctores_res = supabase.table("doctores").select("id, nombre").execute()
        dict_doctores = {d["id"]: d["nombre"] for d in doctores_res.data} if doctores_res.data else {}
        
        if citas_res.data:
            for item in citas_res.data:
                doctor_nombre = dict_doctores.get(item.get("doctor_id"), "Por asignar")
                estado_cita = item.get("estado", "pendiente")
                
                with st.container(border=True):
                    col_info, col_action = st.columns([3, 1])
                    
                    with col_info:
                        st.write(f"👨‍⚕️ **Doctor:** {doctor_nombre} ({item.get('especialidad', 'General')})")
                        st.write(f"📝 **Síntomas:** {item.get('sintomas', 'Sin especificar')}")
                        st.write(f"📋 **Diagnóstico:** {item.get('diagnostico') or 'Pendiente / Sin diagnóstico'}")
                        st.write(f"📅 **Fecha y Hora:** {item.get('fecha_hora')}")
                        st.write(f"💰 **Costo:** ₲ 250.000 | **Estado:** `{estado_cita}`")
                    
                    with col_action:
                        if estado_cita == "pendiente":
                            if st.button("❌ Cancelar Turno", key=f"btn_ini_cancel_{item['id']}"):
                                st.session_state[f"dialog_cancel_{item['id']}"] = True
                                st.session_state[f"dialog_reprog_{item['id']}"] = False
                    
                    if st.session_state.get(f"dialog_cancel_{item['id']}", False):
                        st.warning("⚠️ ¿Estás seguro que quieres cancelar la cita?")
                        b_col1, b_col2 = st.columns(2)
                        
                        with b_col1:
                            if st.button("Cancelar cita", key=f"conf_canc_{item['id']}"):
                                supabase.table("consultas").update({"estado": "cancelada"}).eq("id", item["id"]).execute()
                                st.success("Cita cancelada correctamente.")
                                st.session_state[f"dialog_cancel_{item['id']}"] = False
                                st.rerun()
                                
                        with b_col2:
                            if st.button("Reprogramar cita", key=f"conf_reprog_{item['id']}"):
                                st.session_state[f"dialog_cancel_{item['id']}"] = False
                                st.session_state[f"dialog_reprog_{item['id']}"] = True
                                st.rerun()

                    if st.session_state.get(f"dialog_reprog_{item['id']}", False):
                        st.info(f"🔄 **Reprogramar cita con:** {doctor_nombre}")
                        with st.form(f"form_reprog_{item['id']}"):
                            nuevo_fecha = st.date_input("Nueva Fecha")
                            nuevo_hora = st.time_input("Nueva Hora")
                            btn_guardar_reprog = st.form_submit_button("Guardar Nueva Fecha y Hora", use_container_width=True)
                            
                        if btn_guardar_reprog:
                            nueva_fh_formateada = f"{nuevo_fecha} {nuevo_hora.strftime('%H:%M:%S')}"
                            supabase.table("consultas").update({"fecha_hora": nueva_fh_formateada}).eq("id", item["id"]).execute()
                            st.success("¡Cita reprogramada exitosamente!")
                            st.session_state[f"dialog_reprog_{item['id']}"] = False
                            st.rerun()
        else:
            st.info("No tienes citas agendadas actualmente.")
        
    # --- LOS PACIENTES PUEDEN CREAR UNA CITA ---
    with tab2:
        st.subheader("Reservar Turno Médico")
        st.info("ℹ️ **Información importante:** El costo de la consulta es de **₲ 250.000** y se abona directamente en caja al llegar a la clínica el día de tu turno.")
        
        doc_res = supabase.table("doctores").select("id, nombre, especialidad").eq("activo", True).execute()
        doctores_lista = doc_res.data if doc_res.data else []

        with st.form("form_cita", clear_on_submit=True):
            if doctores_lista:
                opciones_doctores = {
                    f"{doc['nombre']} ({doc['especialidad']})": doc for doc in doctores_lista
                }
                doctor_sel_str = st.selectbox("Seleccionar Doctor / Especialidad", list(opciones_doctores.keys()))
            else:
                st.warning("No hay doctores disponibles en este momento. Selecciona una especialidad general:")
                especialidad_sel = st.selectbox("Especialidad Médica", [
                    "Médico General", "Nutricionista", "Pediatra", "Fisioterapeuta", "Oncólogo"
                ])

            sintomas_txt = st.text_area("Síntomas o Motivo de Consulta", placeholder="Describe brevemente tus síntomas...")
            
            col_f, col_h = st.columns(2)
            with col_f:
                fecha = st.date_input("Fecha de la Cita")
            with col_h:
                hora = st.time_input("Hora de la Cita")
                
            btn_reserva = st.form_submit_button("Confirmar Reserva de Turno", use_container_width=True)

        if btn_reserva:
            fecha_hora_formateada = f"{fecha} {hora.strftime('%H:%M:%S')}"
            nueva_consulta = {
                "paciente_id": usuario["id"],
                "fecha_hora": fecha_hora_formateada,
                "sintomas": sintomas_txt,
                "estado": "pendiente",
                "costo_total": 250000
            }
            if doctores_lista:
                doctor_obj = opciones_doctores[doctor_sel_str]
                nueva_consulta["doctor_id"] = doctor_obj["id"]
                nueva_consulta["especialidad"] = doctor_obj["especialidad"]
            else:
                nueva_consulta["especialidad"] = especialidad_sel

            try:
                res = supabase.table("consultas").insert(nueva_consulta).execute()
                if res.data:
                    supabase.table("caja").insert({"tipo": "cobro", "monto": 250000}).execute()
                    st.success("¡Turno agendado exitosamente! Te esperamos en la clínica.")
                    st.rerun()
            except Exception as err:
                st.error(f"Error al registrar la cita: {err}")


# ==========================================
# VER QUE ROL ACCEDE
# ==========================================

def main():
    if not supabase:
        st.stop()

    if st.session_state["usuario_logueado"]:
        usuario = st.session_state["usuario_logueado"]
        
        # --- MUESTRA ESA BARRA QUE SALE A LA IZQUIERDA ---
        with st.sidebar:
            st.title("🏥 ClinicaApp")
            st.write(f"👤 **{usuario['nombre']}**")
            st.caption(f"Rol: `{usuario['rol'].upper()}`")
            st.divider()
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state["usuario_logueado"] = None
                st.rerun()

        # --- ENRUTAMIENTO POR ROL ---
        rol = usuario["rol"]
        if rol == "paciente":
            vista_paciente()
        else:
            st.warning(f"Iniciaste sesión como `{rol.upper()}`.  En mantenimiento, vuelva pronto. Inicia sesión con una cuenta de paciente para acceder.")
    else:
        vista_login_registro()


if __name__ == "__main__":
    main()
