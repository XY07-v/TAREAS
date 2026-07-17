import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO GLASSMORPHISM
# ==========================================
st.set_page_config(
    page_title="GlassAsana - Admin de Tareas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para lograr el efecto "Glassmorphism" (vidrio esmerilado)
st.markdown("""
<style>
    /* Fondo general con un gradiente moderno y dinámico */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
        color: #f1f5f9;
    }
    
    /* Contenedores con efecto de vidrio esmerilado (Glassmorphism) */
    div[data-testid="stVerticalBlock"] > div:has(div.glass-card) {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Clases auxiliares para HTML personalizado */
    .glass-header {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
    }
    
    .glass-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85em;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Personalización de botones */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DATOS (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("asana_glass.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            rol TEXT NOT NULL -- 'admin' o 'usuario'
        )
    """)
    
    # Tabla de Grupos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    """)
    
    # Tabla de Miembros de Grupos (Muchos a Muchos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS miembros_grupo (
            grupo_id INTEGER,
            username TEXT,
            FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
            FOREIGN KEY(username) REFERENCES usuarios(username) ON DELETE CASCADE,
            PRIMARY KEY (grupo_id, username)
        )
    """)
    
    # Tabla de Tareas (Estilo Asana)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            grupo_id INTEGER,
            asignado_a TEXT,
            fecha_entrega TEXT,
            prioridad TEXT, -- 'Alta', 'Media', 'Baja'
            estado TEXT, -- 'Por Hacer', 'En Progreso', 'Listo'
            progreso INTEGER DEFAULT 0, -- 0 a 100%
            FOREIGN KEY(grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
            FOREIGN KEY(asignado_a) REFERENCES usuarios(username)
        )
    """)
    
    # Crear Administrador por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios VALUES ('admin', 'admin123', 'admin')")
        
    conn.commit()
    return conn

conn = init_db()

# ==========================================
# 3. CONTROL DE SESIÓN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.rol = None

def login_user(username, password):
    cursor = conn.cursor()
    cursor.execute("SELECT rol FROM usuarios WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.rol = user[0]
        st.rerun()
    else:
        st.error("Usuario o contraseña incorrectos")

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.rol = None
    st.rerun()

# ==========================================
# 4. INTERFAZ DE LOGIN (PANTALLA DE INICIO)
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="glass-header"><h1>🔮 GlassAsana</h1><p>Gestión de proyectos con diseño transparente y elegante</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            username_input = st.text_input("Usuario", key="login_user")
            password_input = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", use_container_width=True):
                login_user(username_input, password_input)
                
        with tab2:
            reg_user = st.text_input("Nuevo Usuario", key="reg_user")
            reg_pass = st.text_input("Nueva Contraseña", type="password", key="reg_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (reg_user, reg_pass, 'usuario'))
                    conn.commit()
                    st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                except sqlite3.IntegrityError:
                    st.error("El nombre de usuario ya existe.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. MENÚ DE NAVEGACIÓN (SESIÓN INICIADA)
# ==========================================
st.sidebar.markdown(f"### 👤 Bienvenido, **{st.session_state.username}**")
st.sidebar.markdown(f'<span class="glass-badge">Rol: {st.session_state.rol.upper()}</span>', unsafe_allow_html=True)
st.sidebar.write("---")

# Opciones de menú según el Rol
menu_options = ["📋 Mi Tablero (Tareas)", "👥 Grupos"]
if st.session_state.rol == 'admin':
    menu_options.append("⚙️ Panel de Control (Admin)")

choice = st.sidebar.radio("Navegación", menu_options)

if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    logout_user()

# ==========================================
# 6. SECCIÓN: GRUPOS
# ==========================================
if choice == "👥 Grupos":
    st.markdown("## 👥 Grupos de Trabajo")
    
    # Si es Admin, puede crear grupos y asignar personas
    if st.session_state.rol == 'admin':
        with st.expander("➕ Crear Nuevo Grupo de Trabajo"):
            col_g1, col_g2 = st.columns([1, 2])
            with col_g1:
                nuevo_grupo = st.text_input("Nombre del Grupo")
            with col_g2:
                desc_grupo = st.text_input("Descripción breve")
            if st.button("Crear Grupo"):
                if nuevo_grupo:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO grupos (nombre, descripcion) VALUES (?, ?)", (nuevo_grupo, desc_grupo))
                        conn.commit()
                        st.success(f"Grupo '{nuevo_grupo}' creado con éxito.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El grupo ya existe.")
        
        # Asignar miembros a grupos
        with st.expander("👤 Asignar Miembros a Grupo"):
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM grupos")
            todos_grupos = cursor.fetchall()
            cursor.execute("SELECT username FROM usuarios WHERE rol = 'usuario'")
            todos_usuarios = [r[0] for r in cursor.fetchall()]
            
            if todos_grupos and todos_usuarios:
                grupo_seleccionado = st.selectbox("Selecciona el Grupo", todos_grupos, format_func=lambda x: x[1])
                user_seleccionado = st.selectbox("Selecciona el Usuario", todos_usuarios)
                
                if st.button("Añadir al Grupo"):
                    try:
                        cursor.execute("INSERT INTO miembros_grupo VALUES (?, ?)", (grupo_seleccionado[0], user_seleccionado))
                        conn.commit()
                        st.success(f"¡{user_seleccionado} añadido a {grupo_seleccionado[1]}!")
                    except sqlite3.IntegrityError:
                        st.warning("El usuario ya pertenece a este grupo.")
            else:
                st.info("Crea un grupo y asegúrate de tener usuarios registrados.")

    # Mostrar Grupos a los que pertenece el usuario (o todos si es admin)
    st.write("---")
    st.write("### Mis Grupos Activos")
    cursor = conn.cursor()
    if st.session_state.rol == 'admin':
        cursor.execute("SELECT id, nombre, descripcion FROM grupos")
    else:
        cursor.execute("""
            SELECT g.id, g.nombre, g.descripcion FROM grupos g
            JOIN miembros_grupo mg ON g.id = mg.grupo_id
            WHERE mg.username = ?
        """, (st.session_state.username,))
    
    mis_grupos = cursor.fetchall()
    if mis_grupos:
        for gid, gnom, gdesc in mis_grupos:
            st.markdown(f"""
            <div class="glass-card">
                <h4>📂 {gnom}</h4>
                <p style="color: #cbd5e1;">{gdesc or "Sin descripción"}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar miembros del grupo
            cursor.execute("SELECT username FROM miembros_grupo WHERE grupo_id = ?", (gid,))
            miembros = [r[0] for r in cursor.fetchall()]
            if miembros:
                st.caption(f"👥 Miembros: {', '.join(miembros)}")
            else:
                st.caption("👥 Sin miembros asignados aún.")
    else:
        st.info("No estás asignado a ningún grupo actualmente.")

# ==========================================
# 7. SECCIÓN: TABLERO DE TAREAS (ESTILO ASANA)
# ==========================================
elif choice == "📋 Mi Tablero (Tareas)":
    st.markdown("## 📋 Tablero de Tareas")
    
    # Crear Tarea (Solo Admin o miembros del grupo)
    with st.expander("➕ Crear Nueva Tarea estilo Asana"):
        cursor = conn.cursor()
        if st.session_state.rol == 'admin':
            cursor.execute("SELECT id, nombre FROM grupos")
        else:
            cursor.execute("SELECT g.id, g.nombre FROM grupos g JOIN miembros_grupo mg ON g.id = mg.grupo_id WHERE mg.username = ?", (st.session_state.username,))
        grupos_disponibles = cursor.fetchall()
        
        if grupos_disponibles:
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_titulo = st.text_input("Título de la Tarea")
                t_desc = st.text_area("Descripción de la Tarea")
                t_grupo = st.selectbox("Grupo Destinado", grupos_disponibles, format_func=lambda x: x[1])
            with col_t2:
                # Obtener miembros del grupo seleccionado para asignar la tarea
                cursor.execute("SELECT username FROM miembros_grupo WHERE grupo_id = ?", (t_grupo[0],))
                miembros_del_grupo = [r[0] for r in cursor.fetchall()]
                if not miembros_del_grupo:
                    miembros_del_grupo = [st.session_state.username]
                
                t_asignado = st.selectbox("Asignar A", miembros_del_grupo)
                t_fecha = st.date_input("Fecha de Entrega", datetime.now())
                t_prioridad = st.selectbox("Prioridad", ["Baja", "Media", "Alta"])
                t_estado = st.selectbox("Estado Inicial", ["Por Hacer", "En Progreso", "Listo"])
                
            if st.button("Publicar Tarea en Asana"):
                if t_titulo:
                    cursor.execute("""
                        INSERT INTO tareas (titulo, descripcion, grupo_id, asignado_a, fecha_entrega, prioridad, estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (t_titulo, t_desc, t_grupo[0], t_asignado, str(t_fecha), t_prioridad, t_estado))
                    conn.commit()
                    st.success("Tarea creada exitosamente.")
                    st.rerun()
        else:
            st.warning("Debes pertenecer o crear al menos un grupo para agendar tareas.")

    # Filtros de visualización
    st.write("---")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        filtro_estado = st.multiselect("Filtrar por Estado", ["Por Hacer", "En Progreso", "Listo"], default=["Por Hacer", "En Progreso"])
    with f_col2:
        filtro_prioridad = st.multiselect("Filtrar por Prioridad", ["Baja", "Media", "Alta"], default=["Baja", "Media", "Alta"])

    # Obtención de tareas de los grupos del usuario
    cursor = conn.cursor()
    if st.session_state.rol == 'admin':
        query = "SELECT t.id, t.titulo, t.descripcion, g.nombre, t.asignado_a, t.fecha_entrega, t.prioridad, t.estado, t.progreso FROM tareas t JOIN grupos g ON t.grupo_id = g.id WHERE 1=1"
        params = []
    else:
        query = """
            SELECT t.id, t.titulo, t.descripcion, g.nombre, t.asignado_a, t.fecha_entrega, t.prioridad, t.estado, t.progreso 
            FROM tareas t 
            JOIN grupos g ON t.grupo_id = g.id 
            WHERE t.grupo_id IN (SELECT grupo_id FROM miembros_grupo WHERE username = ?)
        """
        params = [st.session_state.username]

    if filtro_estado:
        query += f" AND t.estado IN ({','.join(['?']*len(filtro_estado))})"
        params.extend(filtro_estado)
    if filtro_prioridad:
        query += f" AND t.prioridad IN ({','.join(['?']*len(filtro_prioridad))})"
        params.extend(filtro_prioridad)

    cursor.execute(query, params)
    tareas = cursor.fetchall()

    # Mostrar Tareas estilo Kanban / Tarjetas Modernas
    if tareas:
        for tid, tit, desc, gnom, asig, fecha, prio, est, prog in tareas:
            st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
            col_card1, col_card2 = st.columns([3, 1])
            
            with col_card1:
                st.markdown(f"### 📌 {tit}")
                st.markdown(f"**Descripción:** {desc or 'Sin descripción disponible.'}")
                st.markdown(f"📂 **Grupo:** `{gnom}` | 👤 **Asignado a:** `{asig}` | 📅 **Entrega:** `{fecha}`")
            
            with col_card2:
                # Color dinámico de la prioridad
                color_prio = "🟢" if prio == "Baja" else "🟡" if prio == "Media" else "🔴"
                st.markdown(f"{color_prio} **Prioridad:** {prio}")
                
                # Actualizar progreso y estado de forma interactiva
                nuevo_est = st.selectbox("Estado", ["Por Hacer", "En Progreso", "Listo"], index=["Por Hacer", "En Progreso", "Listo"].index(est), key=f"est_{tid}")
                nuevo_prog = st.slider("Avance (%)", 0, 100, prog, step=10, key=f"prog_{tid}")
                
                # Botón rápido para guardar cambios en cada tarea
                if st.button("Actualizar Tarea", key=f"btn_{tid}"):
                    cursor.execute("UPDATE tareas SET estado = ?, progreso = ? WHERE id = ?", (nuevo_est, nuevo_prog, tid))
                    conn.commit()
                    st.success("Guardado")
                    st.rerun()
            
            # Barra de Progreso visual elegante
            st.progress(nuevo_prog / 100)
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")
    else:
        st.info("No hay tareas que coincidan con los filtros aplicados.")

# ==========================================
# 8. SECCIÓN: PANEL DE CONTROL (SÓLO ADMIN)
# ==========================================
elif choice == "⚙️ Panel de Control (Admin)":
    st.markdown("## ⚙️ Panel de Control del Administrador")
    
    # Vista general rápida de usuarios registrados
    st.write("### Usuarios Registrados")
    df_users = pd.read_sql_query("SELECT username, rol FROM usuarios", conn)
    st.dataframe(df_users, use_container_width=True)
    
    # Eliminar grupos o tareas para mantenimiento
    st.write("### Acciones de Limpieza")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM grupos")
    grupos_eliminar = cursor.fetchall()
    
    if grupos_eliminar:
        del_grupo = st.selectbox("Selecciona un grupo para eliminar permanentemente", grupos_eliminar, format_func=lambda x: x[1])
        if st.button("⚠️ Eliminar Grupo"):
            cursor.execute("DELETE FROM grupos WHERE id = ?", (del_grupo[0],))
            conn.commit()
            st.success("Grupo eliminado exitosamente.")
            st.rerun()
