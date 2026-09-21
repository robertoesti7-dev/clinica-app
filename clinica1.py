import streamlit as st
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN A SUPABASE
# ==========================================
SUPABASE_URL = "https://myfhphhabwdeoclioohz.supabase.co"
SUPABASE_KEY = "sb_publishable_zusAZIHZX8hmc7NSg1_vLA_gh1jELGS"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Error al conectar con Supabase. Revisa tus credenciales.")

st.set_page_config(
    page_title="ClinicaApp",
    page_icon="🏥",
    layout="wide"
)

# Inicializar la sesión de forma segura
if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None


# ==========================================
# 2. VISTAS SEGÚN EL ROL DE USUARIO
# ==========================================

def vista_admin():
    st.header("⚙️ Panel de Administración General")
    usuario_actual = st.session_state["usuario_logueado"]
    
    p_res = supabase.table("personas").select("id", count="exact").eq("rol", "paciente").execute()
    total_pacientes = p_res.count if p_res.count is not None else 0

    c_res = supabase.table("consultas").select("id", count="exact").execute()
    total_turnos = c_res.count if c_res.count is not None else 0

    caja_res = supabase.table("caja").select("tipo, monto").execute()
    balance_total = 0.0
    if caja_res.data:
        for mov in caja_res.data:
            monto = float(mov.get("monto", 0))
            if mov.get("tipo") in ["venta", "cobro", "ingreso"]:
                balance_total += monto
            elif mov.get("tipo") in ["compra", "egreso", "gasto"]:
                balance_total -= monto

    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Registrados", f"{total_pacientes}")
    col2.metric("Turnos Registrados", f"{total_turnos}")
    col3.metric("Balance General Consolidado", f"₲ {balance_total:,.0f}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Personas", "👨‍⚕️ Doctores", "📊 Caja General", "➕ Crear Personal"])
    
    with tab1:
        st.subheader("Lista de Personas Registradas")
        res = supabase.table("personas").select("id, nombre, cedula, rol").execute()
        if res.data:
            st.dataframe(res.data, use_container_width=True)
            
            st.divider()
            st.subheader("🗑️ Eliminar Usuario")
            st.caption("Copia el ID exacto del usuario de la tabla superior para proceder con la eliminación.")
            
            with st.form("form_eliminar_usuario"):
                id_usuario_a_borrar = st.text_input("ID del Usuario a Eliminar")
                pass_admin_eliminar = st.text_input("Ingresa tu contraseña de Administrador para confirmar", type="password")
                btn_ejecutar_borrado = st.form_submit_button("Eliminar Usuario", type="primary")
                
            if btn_ejecutar_borrado:
                if not id_usuario_a_borrar or not pass_admin_eliminar:
                    st.warning("Completa todos los campos.")
                elif pass_admin_eliminar != usuario_actual.get("clave"):
                    st.error("Contraseña de administrador incorrecta.")
                else:
                    try:
                        supabase.table("doctores").delete().eq("persona_id", id_usuario_a_borrar).execute()
                        supabase.table("personas").delete().eq("id", id_usuario_a_borrar).execute()
                        st.success("¡Usuario eliminado correctamente del sistema!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar el usuario: {e}")
        else:
            st.info("No hay usuarios registrados aún.")

    with tab2:
        st.subheader("Lista de Doctores y Especialidades")
        doc_res = supabase.table("doctores").select("*").execute()
        if doc_res.data:
            st.dataframe(doc_res.data, use_container_width=True)
        else:
            st.info("No hay doctores registrados en la tabla 'doctores'.")

    with tab3:
        st.subheader("Movimientos de Caja General y Limpieza")
        caja_res_all = supabase.table("caja").select("*").execute()
        if caja_res_all.data:
            st.dataframe(caja_res_all.data, use_container_width=True)
            
            st.divider()
            if st.button("🗑️ Vaciar / Limpiar Balance de Caja", key="btn_init_limpiar_caja"):
                st.session_state["confirmar_limpieza_caja"] = True
                
            if st.session_state.get("confirmar_limpieza_caja", False):
                st.warning("⚠️ **ADVERTENCIA:** Estás a punto de vaciar y eliminar todos los registros de la caja. Esta acción no se puede deshacer.")
                with st.form("form_confirmar_admin_caja"):
                    pass_admin = st.text_input("Ingresa tu contraseña de Administrador para confirmar", type="password")
                    btn_ejecutar_limpieza = st.form_submit_button("Confirmar y Vaciar Caja", type="primary")
                    
                if btn_ejecutar_limpieza:
                    if pass_admin == usuario_actual.get("clave"):
                        try:
                            ids_a_borrar = [row["id"] for row in caja_res_all.data]
                            for row_id in ids_a_borrar:
                                supabase.table("caja").delete().eq("id", row_id).execute()
                                
                            st.success("¡La caja se ha vaciado correctamente!")
                            st.session_state["confirmar_limpieza_caja"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al limpiar la caja: {e}")
                    else:
                        st.error("Contraseña de administrador incorrecta.")
        else:
            st.info("No hay registros en caja.")

    with tab4:
        st.subheader("Registrar Nuevo Personal / Doctor")
        with st.form("form_registro_personal", clear_on_submit=True):
            nombre_p = st.text_input("Nombre y Apellido Completo")
            cedula_p = st.text_input("Número de Cédula")
            clave_p = st.text_input("Contraseña", type="password")
            rol_p = st.selectbox("Rol Asignado", ["doctor", "admin"])
            especialidad_p = st.text_input("Especialidad (Solo si el rol es Doctor)", placeholder="Ej: Pediatra")
            telefono_p = st.text_input("Teléfono (Opcional)")
            
            btn_personal = st.form_submit_button("Registrar Personal", use_container_width=True)

        if btn_personal:
            if not nombre_p or not cedula_p or not clave_p:
                st.warning("Completa todos los campos obligatorios.")
            else:
                nuevo_staff = {
                    "nombre": nombre_p,
                    "cedula": cedula_p,
                    "clave": clave_p,
                    "rol": rol_p
                }
                res_persona = supabase.table("personas").insert(nuevo_staff).execute()
                
                if rol_p == "doctor" and res_persona.data:
                    persona_id = res_persona.data[0]["id"]
                    esp = especialidad_p if especialidad_p else "Médico General"
                    
                    supabase.table("doctores").insert({
                        "persona_id": persona_id,
                        "nombre": nombre_p,
                        "especialidad": esp,
                        "telefono": telefono_p,
                        "activo": True
                    }).execute()
                
                st.success(f"Usuario registrado exitosamente con el rol `{rol_p.upper()}`.")


def vista_doctor():
    st.header("🩺 Panel del Médico")
    usuario = st.session_state["usuario_logueado"]
    
    doc_res = supabase.table("doctores").select("id, nombre").eq("persona_id", usuario["id"]).execute()
    doctor_info = doc_res.data[0] if doc_res.data else None
    
    tab1, tab2, tab3 = st.tabs(["📅 Consultas Agendadas", "📝 Historial y Diagnóstico", "💰 Mi Liquidación"])
    
    personas_res = supabase.table("personas").select("id, nombre").execute()
    dict_personas = {p["id"]: p["nombre"] for p in personas_res.data} if personas_res.data else {}

    with tab1:
        st.subheader("Agenda de Citas (Ordenadas por Fecha y Hora)")
        query = supabase.table("consultas").select("*").order("fecha_hora", desc=False)
        if doctor_info:
            query = query.eq("doctor_id", doctor_info["id"])
            
        citas_res = query.execute()
        
        if citas_res.data:
            datos_formateados = []
            for item in citas_res.data:
                paciente_nombre = dict_personas.get(item.get("paciente_id"), "Paciente no especificado")
                datos_formateados.append({
                    "ID Consulta": item["id"],
                    "Paciente": paciente_nombre,
                    "Especialidad": item.get("especialidad", "General"),
                    "Síntomas": item.get("sintomas", "Sin especificar"),
                    "Fecha y Hora": item.get("fecha_hora"),
                    "Estado": item.get("estado")
                })
            st.dataframe(datos_formateados, use_container_width=True)
        else:
            st.info("No tienes consultas agendadas actualmente.")
        
    with tab2:
        st.subheader("Registrar Diagnóstico")
        with st.form("form_diagnostico", clear_on_submit=True):
            consulta_id = st.text_input("ID de la Consulta (copia el ID desde la pestaña Consultas Agendadas)")
            diagnostico_txt = st.text_area("Diagnóstico / Notas Médicas")
            btn_diag = st.form_submit_button("Guardar Diagnóstico", use_container_width=True)
            
        if btn_diag:
            if consulta_id and diagnostico_txt:
                supabase.table("consultas").update({
                    "diagnostico": diagnostico_txt,
                    "estado": "completada"
                }).eq("id", consulta_id).execute()
                st.success("Diagnóstico guardado correctamente.")
                st.rerun()
            else:
                st.warning("Completa todos los campos.")

        st.divider()
        st.subheader("📋 Historial de Diagnósticos Realizados")
        query_diag = supabase.table("consultas").select("*").order("fecha_hora", desc=True)
        if doctor_info:
            query_diag = query_diag.eq("doctor_id", doctor_info["id"])
        
        historial_res = query_diag.execute()
        diagnosticos_previos = [c for c in historial_res.data if c.get("diagnostico") and c.get("diagnostico") != "None"]
        
        if diagnosticos_previos:
            for item in diagnosticos_previos:
                paciente_nombre = dict_personas.get(item.get("paciente_id"), "Paciente no especificado")
                with st.container(border=True):
                    st.write(f"👤 **Paciente:** {paciente_nombre}")
                    st.write(f"📅 **Fecha y Hora:** {item.get('fecha_hora')}")
                    st.write(f"📝 **Síntomas:** {item.get('sintomas', 'Sin especificar')}")
                    st.write(f"🏥 **Diagnóstico:** {item.get('diagnostico') or 'Sin diagnóstico'}")
        else:
            st.info("Aún no has registrado ningún diagnóstico.")

    with tab3:
        st.subheader("📊 Resumen Financiero y Honorarios Médicos")
        st.caption("Costo por consulta: ₲ 250.000 | Descuento aplicado: 40% por limpieza y mantenimiento de local (60% neto para el médico).")
        
        if doctor_info:
            citas_doc = supabase.table("consultas").select("*").eq("doctor_id", doctor_info["id"]).execute()
            total_consultas = len(citas_doc.data) if citas_doc.data else 0
            
            monto_bruto = total_consultas * 250000
            monto_descuento_40 = monto_bruto * 0.40
            monto_neto_doctor = monto_bruto * 0.60
            
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Consultas Totales", f"{total_consultas}")
            col_d2.metric("Retención Mantenimiento (40%)", f"₲ {monto_descuento_40:,.0f}")
            col_d3.metric("Honorarios Libres (60%)", f"₲ {monto_neto_doctor:,.0f}")
            
            st.divider()
            st.write("#### Detalle por Turno Registrado")
            if citas_doc.data:
                detalle_tabla = []
                for idx, c in enumerate(citas_doc.data, 1):
                    detalle_tabla.append({
                        "#": idx,
                        "Fecha": c.get("fecha_hora"),
                        "Costo Total": "₲ 250.000",
                        "Retención 40% (Gastos)": "₲ 100.000",
                        "Ganancia Neta 60%": "₲ 150.000",
                        "Estado Cita": c.get("estado")
                    })
                st.dataframe(detalle_tabla, use_container_width=True)
        else:
            st.warning("No se encontró el perfil de doctor asociado a esta cuenta.")


def vista_paciente():
    st.header("👤 Portal del Paciente")
    usuario = st.session_state["usuario_logueado"]
    
    tab1, tab2 = st.tabs(["📅 Mis Citas", "➕ Agendar Turno"])
    
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
                            if st.button("Sí, cancelar", key=f"conf_canc_{item['id']}"):
                                supabase.table("consultas").update({"estado": "cancelada"}).eq("id", item["id"]).execute()
                                st.success("Cita cancelada correctamente.")
                                st.session_state[f"dialog_cancel_{item['id']}"] = False
                                st.rerun()
                                
                        with b_col2:
                            if st.button("Reprogramar", key=f"conf_reprog_{item['id']}"):
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
# 3. CONTROL DE NAVEGACIÓN Y SESIÓN
# ==========================================

if st.session_state["usuario_logueado"]:
    usuario = st.session_state["usuario_logueado"]
    
    with st.sidebar:
        st.title("🏥 ClinicaApp")
        st.write(f"👤 **{usuario['nombre']}**")
        st.caption(f"Rol: `{usuario['rol'].upper()}`")
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["usuario_logueado"] = None
            st.rerun()

    rol = usuario["rol"]
    if rol == "admin":
        vista_admin()
    elif rol == "doctor":
        vista_doctor()
    elif rol == "paciente":
        vista_paciente()

else:
    st.title("🏥 Bienvenido/a a ClinicaApp")
    
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse (Pacientes)"])

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

    with tab_registro:
        with st.form("form_registro", clear_on_submit=True):
            nombre = st.text_input("Nombre y Apellido Completo")
            cedula = st.text_input("Número de Cédula")
            clave = st.text_input("Contraseña", type="password")
            confirmar = st.text_input("Confirmar Contraseña", type="password")
            
            rol_publico = "paciente"
            
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
                    "rol": rol_publico
                }
                supabase.table("personas").insert(nuevo_paciente).execute()
                st.success("Cuenta creada exitosamente. Inicia sesión en la pestaña al lado.")
