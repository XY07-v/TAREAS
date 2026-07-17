import os
import json
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId, json_util

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nestle_liquid_light_2026")

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['Tareas']
usuarios_col = db['Usuarios']
grupos_col = db['Grupos']

# Zona horaria de Colombia nativa (UTC -5)
CO_TZ = timezone(timedelta(hours=-5))

# --- PLANTILLA DEL LOGIN ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - Nestlé Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            background-attachment: fixed;
        }
        .liquid-glass-light {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.6);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.5);
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="liquid-glass-light p-8 md:p-10 rounded-3xl w-full max-w-md text-slate-800">
        <div class="flex flex-col items-center mb-8">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center mb-4 shadow-md shadow-blue-500/20">
                <span class="text-2xl font-extrabold text-white tracking-wider">N</span>
            </div>
            <h2 class="text-2xl font-extrabold tracking-tight text-slate-900">Nestlé Portal</h2>
            <p class="text-xs text-slate-500 mt-1.5">Liquid Glass Light Edition</p>
        </div>
        
        {% if error %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-700 p-3.5 rounded-2xl text-xs mb-5 flex items-center space-x-2">
                <span>⚠️ {{ error }}</span>
            </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Usuario</label>
                <input type="text" name="username" required placeholder="Tu usuario" class="w-full bg-white/60 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Contraseña</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-white/60 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-md text-xs uppercase tracking-wider mt-2">
                Iniciar Sesión
            </button>
        </form>
    </div>
</body>
</html>
"""

# --- PLANTILLA PRINCIPAL ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nestlé Light Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at 0% 0%, rgba(59, 130, 246, 0.05) 0%, rgba(255, 255, 255, 0) 50%), #f8fafc;
        }
        .liquid-glass-panel {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.04);
        }
        .sidebar-expanded { w-64; }
        .sidebar-collapsed { w-20; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.08); border-radius: 10px; }
    </style>
</head>
<body class="text-slate-700 h-screen overflow-hidden flex flex-col md:flex-row p-2 md:p-4 gap-4 md:gap-6">

    <!-- BOTÓN MENÚ MÓVIL -->
    <div class="md:hidden flex items-center justify-between p-2 bg-white/80 backdrop-blur-md rounded-2xl border border-slate-200">
        <div class="flex items-center space-x-2">
            <span class="font-extrabold text-sm text-slate-900 tracking-tight">Nestlé Light</span>
        </div>
        <button onclick="toggleMobileMenu()" class="p-2 text-slate-700 focus:outline-none">
            <i class="fa-solid fa-bars text-lg"></i>
        </button>
    </div>

    <!-- BARRA LATERAL (SIDEBAR DINÁMICA) -->
    <aside id="mainSidebar" class="hidden md:flex flex-col justify-between h-full flex-shrink-0 overflow-hidden liquid-glass-panel rounded-3xl transition-all duration-300 w-64">
        <div>
            <!-- Header de la Barra Lateral -->
            <div class="p-4 border-b border-slate-200/50 flex items-center justify-between">
                <div class="flex items-center space-x-3 sidebar-hideable">
                    <img src="{{ current_user_avatar }}" class="w-8 h-8 rounded-xl object-cover border border-slate-200 shadow-sm">
                    <div class="truncate w-32">
                        <h1 class="font-bold text-xs text-slate-900 truncate">{{ username }}</h1>
                        <span class="text-[8px] font-bold text-blue-600 uppercase tracking-widest">{{ user_role }}</span>
                    </div>
                </div>
                <button onclick="toggleSidebarCollapse()" class="p-1.5 hover:bg-slate-200/50 rounded-lg text-slate-500 mx-auto md:mx-0">
                    <i id="collapseIcon" class="fa-solid fa-chevron-left text-xs"></i>
                </button>
            </div>

            <!-- Navegación -->
            <div class="p-3 space-y-1">
                <button onclick="switchTab('tareasTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold bg-white/60 text-slate-900 shadow-sm transition-all justify-start">
                    <i class="fa-solid fa-layer-group text-blue-500 w-4 text-center"></i>
                    <span class="sidebar-hideable">Bandeja de Tareas</span>
                </button>
                <button onclick="switchTab('gruposTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all justify-start">
                    <i class="fa-solid fa-users text-purple-500 w-4 text-center"></i>
                    <span class="sidebar-hideable">Grupos y Miembros</span>
                </button>
                {% if user_role == 'admin' %}
                <button onclick="switchTab('adminTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all justify-start">
                    <i class="fa-solid fa-user-gear text-orange-500 w-4 text-center"></i>
                    <span class="sidebar-hideable">Administrar Personal</span>
                </button>
                {% endif %}
                <button onclick="switchTab('perfilTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all justify-start">
                    <i class="fa-solid fa-user-astronaut text-green-500 w-4 text-center"></i>
                    <span class="sidebar-hideable">Mi Perfil</span>
                </button>
            </div>
        </div>

        <div class="p-3 border-t border-slate-200/50">
            <a href="/logout" class="w-full flex items-center justify-center space-x-2 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs border border-red-100">
                <i class="fa-solid fa-power-off"></i>
                <span class="sidebar-hideable">Salir</span>
            </a>
        </div>
    </aside>

    <!-- CONTENIDO PRINCIPAL -->
    <main class="flex-grow flex flex-col h-full overflow-hidden w-full">
        
        <!-- TAB TAREAS -->
        <div id="tareasTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden">
            <header class="mb-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                <div>
                    <h2 class="text-xl font-extrabold text-slate-900 tracking-tight">Tareas Activas</h2>
                </div>
                
                <!-- Filtros del Tablero -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <select id="filtroGrupo" onchange="actualizarFiltrosResponsable(); applyFilters();" class="text-xs font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl px-3 py-2 focus:outline-none">
                        <option value="">Todos los Grupos / Áreas</option>
                        <option value="Varios">Sueltas (Varios)</option>
                        {% for g in lista_grupos %}
                            <option value="{{ g.nombre }}">{{ g.nombre }}</option>
                        {% endfor %}
                    </select>
                    
                    <select id="filtroResponsable" onchange="applyFilters()" class="text-xs font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl px-3 py-2 focus:outline-none">
                        <option value="">Cualquier Responsable</option>
                        <!-- Filtrado por JS en tiempo real -->
                    </select>

                    <select id="estadoFilter" onchange="applyFilters()" class="text-xs font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl px-3 py-2 focus:outline-none">
                        <option value="">Cualquier Estado</option>
                        <option value="pendiente">Pendientes</option>
                        <option value="completado">Completadas</option>
                    </select>
                </div>
            </header>

            <div class="flex-grow flex flex-col lg:flex-row overflow-hidden gap-4">
                <div class="flex-grow overflow-y-auto custom-scrollbar space-y-4 pr-1">
                    
                    {% if user_role == 'admin' %}
                    <!-- CREACIÓN DE TAREA INTELIGENTE -->
                    <div class="liquid-glass-panel rounded-2xl p-4">
                        <h3 class="text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-3">Nueva Tarea Con Asignación Cruzada</h3>
                        <form action="/admin/crear-tarea" method="POST" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            <input type="text" name="descripcion" required placeholder="Descripción de la tarea..." class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none">
                            
                            <select id="crearTareaGrupo" name="grupo_asignado" required onchange="filtrarUsuariosPorGrupoForm('crearTareaGrupo', 'crearTareaResponsable')" class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-600 focus:outline-none">
                                <option value="Varios">Grupo/Área: Varios (Sueltas)</option>
                                {% for g in lista_grupos %}
                                    <option value="{{ g.nombre }}">{{ g.nombre }}</option>
                                {% endfor %}
                            </select>

                            <select id="crearTareaResponsable" name="persona_asignada" required class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-600 focus:outline-none">
                                <option value="">Selecciona Responsable...</option>
                                {% for u in lista_usuarios %}
                                    <option value="{{ u.username }}">{{ u.username }}</option>
                                {% endfor %}
                            </select>

                            <div class="flex gap-2">
                                <input type="date" name="fecha_entrega" required class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-600 focus:outline-none flex-grow">
                                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 rounded-xl text-xs transition-colors">Asignar</button>
                            </div>
                        </form>
                    </div>
                    {% endif %}

                    <!-- TABLA RESPONSIVA -->
                    <div class="liquid-glass-panel rounded-2xl overflow-x-auto custom-scrollbar">
                        <table class="w-full text-left border-collapse text-xs min-w-[600px]">
                            <thead>
                                <tr class="border-b border-slate-200 bg-slate-50/50 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                    <th class="py-3 px-4 w-12 text-center">Estado</th>
                                    <th class="py-3 px-4">Descripción</th>
                                    <th class="py-3 px-4">Área / Grupo</th>
                                    <th class="py-3 px-4">Responsable</th>
                                    <th class="py-3 px-4">Vence</th>
                                    <th class="py-3 px-4 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody id="tareasTableBody" class="divide-y divide-slate-100"></tbody>
                        </table>
                    </div>
                </div>

                <!-- DETALLE LATERAL -->
                <div id="asanaDetailPanel" class="w-full lg:w-80 liquid-glass-panel rounded-2xl h-full flex flex-col justify-between hidden flex-shrink-0">
                    <div class="p-4 space-y-4 overflow-y-auto custom-scrollbar flex-grow">
                        <div class="flex items-center justify-between">
                            <span class="text-[9px] font-bold text-blue-600 uppercase tracking-widest">Detalles</span>
                            <button onclick="closeDetailPanel()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-times"></i></button>
                        </div>

                        {% if user_role == 'admin' %}
                        <div id="editTaskSection" class="hidden space-y-2 bg-white/50 p-3 rounded-xl border border-slate-200">
                            <input type="text" id="editDescripcion" class="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-800">
                            <select id="editGrupo" onchange="filtrarUsuariosPorGrupoForm('editGrupo', 'editResponsable')" class="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-700"></select>
                            <select id="editResponsable" class="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-700"></select>
                            <input type="date" id="editFecha" class="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-700">
                            <button onclick="guardarEdicionTarea()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-1 rounded-lg text-xs transition-colors">Guardar</button>
                        </div>
                        {% endif %}

                        <div id="readTaskSection" class="space-y-2">
                            <h3 id="detailTitle" class="text-xs font-bold text-slate-900"></h3>
                            <p class="text-[11px] text-slate-500">Grupo: <span id="detailGrupo" class="font-bold text-slate-700"></span> | Encargado: <span id="detailAsignado" class="font-bold text-slate-700"></span></p>
                        </div>

                        <div class="space-y-2 pt-2 border-t border-slate-200">
                            <textarea id="nuevaNotaInput" placeholder="Añadir novedad..." rows="2" class="w-full bg-white border border-slate-200 rounded-xl p-2 text-xs text-slate-800 resize-none focus:outline-none"></textarea>
                            <button onclick="guardarNovedad()" class="bg-slate-800 text-white font-bold px-3 py-1 rounded-lg text-xs transition-colors">Añadir Nota</button>
                            <div id="notasContainer" class="space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB GRUPOS -->
        <div id="gruposTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-4">
                <h2 class="text-xl font-extrabold text-slate-900 tracking-tight">Estructura Organizacional</h2>
            </header>
            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-4">
                {% if user_role == 'admin' %}
                <form action="/admin/crear-grupo" method="POST" class="flex gap-2 max-w-sm">
                    <input type="text" name="nombre_grupo" required placeholder="Nombre del área..." class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none flex-grow">
                    <button type="submit" class="bg-purple-600 text-white font-bold px-4 rounded-xl text-xs">Crear Grupo</button>
                </form>
                {% endif %}

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {% for g in lista_grupos %}
                    <div class="liquid-glass-panel rounded-2xl p-4 space-y-2">
                        <div class="flex justify-between items-center border-b pb-2">
                            <span class="font-bold text-xs text-slate-900"><i class="fa-solid fa-users text-purple-500 mr-1.5"></i>{{ g.nombre }}</span>
                            <span class="text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-mono">{{ g.miembros|length }}</span>
                        </div>
                        <div class="space-y-1 max-h-32 overflow-y-auto custom-scrollbar text-xs">
                            {% for m in g.miembros %}
                            <div class="flex justify-between items-center bg-white/40 px-2 py-1 rounded-lg">
                                <span>{{ m }}</span>
                                {% if user_role == 'admin' %}
                                <button onclick="window.location.href='/admin/quitar-miembro-grupo/{{ g._id }}/{{ m }}'" class="text-red-500 font-bold hover:underline">Quitar</button>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                        {% if user_role == 'admin' %}
                        <form action="/admin/agregar-miembro-grupo" method="POST" class="flex gap-1 pt-2">
                            <input type="hidden" name="grupo_id" value="{{ g._id }}">
                            <select name="miembro_nuevo" required class="bg-white border border-slate-200 rounded-lg text-xs px-2 py-1 flex-grow">
                                <option value="">Añadir...</option>
                                {% for u in lista_usuarios %}
                                    {% if u.username not in g.miembros %}
                                        <option value="{{ u.username }}">{{ u.username }}</option>
                                    {% endif %}
                                {% endfor %}
                            </select>
                            <button type="submit" class="bg-purple-600 text-white px-2.5 rounded-lg text-xs">+</button>
                        </form>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- TAB ADMIN (CON ELIMINACIÓN TOTAL SOLICITADA) -->
        {% if user_role == 'admin' %}
        <div id="adminTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-4"><h2 class="text-xl font-extrabold text-slate-900 tracking-tight">Administración de Cuentas</h2></header>
            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-4">
                
                <div class="liquid-glass-panel rounded-2xl p-4">
                    <h3 class="text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-2">Crear Nuevo Colaborador</h3>
                    <form action="/admin/crear-usuario" method="POST" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                        <input type="text" name="nuevo_usuario" required placeholder="Usuario..." class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none">
                        <input type="password" name="password" required placeholder="Clave..." class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none">
                        <select name="rol" class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none"><option value="user">Colaborador</option><option value="admin">Administrador</option></select>
                        <input type="url" name="avatar" required placeholder="URL Foto Perfil..." class="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none">
                        <button type="submit" class="bg-blue-600 text-white font-bold rounded-xl text-xs py-2">Registrar</button>
                    </form>
                </div>

                <div class="liquid-glass-panel rounded-2xl overflow-x-auto">
                    <table class="w-full text-left border-collapse text-xs min-w-[500px]">
                        <thead>
                            <tr class="border-b border-slate-200 bg-slate-50/50 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                <th class="py-3 px-4">Usuario</th>
                                <th class="py-3 px-4">Rol</th>
                                <th class="py-3 px-4 text-right">Acciones de Control</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            {% for u in lista_usuarios_completa %}
                            <tr class="hover:bg-white/40">
                                <td class="py-2.5 px-4 font-semibold text-slate-900">{{ u.username }}</td>
                                <td class="py-2.5 px-4 capitalize text-slate-500">{{ u.rol }}</td>
                                <td class="py-2.5 px-4 text-right space-x-2">
                                    <button onclick="eliminarUsuarioTotal('{{ u._id }}')" class="text-red-600 hover:text-red-800 font-bold border border-red-200 bg-red-50 px-2 py-1 rounded-lg">Eliminar Cuenta</button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- TAB PERFIL -->
        <div id="perfilTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <div class="max-w-md liquid-glass-panel p-6 rounded-2xl space-y-4">
                <h3 class="font-bold text-slate-900">Personalizar Perfil</h3>
                <form action="/perfil/actualizar-avatar" method="POST" class="space-y-2">
                    <input type="url" name="avatar_url" required value="{{ current_user_avatar }}" class="w-full bg-white border border-slate-200 rounded-xl p-2 text-xs">
                    <button type="submit" class="bg-slate-900 text-white text-xs px-4 py-2 rounded-xl">Guardar Enlace de Foto</button>
                </form>
            </div>
        </div>

    </main>

    <script>
        // Data inyectada de Grupos y Miembros para filtros instantáneos Cruzados
        const dataGrupos = {{ lista_grupos_json | safe }};
        const todosLosUsuarios = {{ lista_usuarios_json | safe }};
        let activeTaskId = null;

        function toggleSidebarCollapse() {
            const sidebar = document.getElementById('mainSidebar');
            const icon = document.getElementById('collapseIcon');
            const elements = document.querySelectorAll('.sidebar-hideable');

            if (sidebar.classList.contains('w-64')) {
                sidebar.classList.replace('w-64', 'w-20');
                icon.classList.replace('fa-shadow-left', 'fa-chevron-right');
                elements.forEach(el => el.classList.add('hidden'));
            } else {
                sidebar.classList.replace('w-20', 'w-64');
                icon.classList.replace('fa-chevron-right', 'fa-shadow-left');
                elements.forEach(el => el.classList.remove('hidden'));
            }
        }

        function toggleMobileMenu() {
            const sidebar = document.getElementById('mainSidebar');
            sidebar.classList.toggle('hidden');
            sidebar.classList.toggle('w-full');
            sidebar.classList.toggle('fixed');
            sidebar.classList.toggle('z-40');
            sidebar.classList.toggle('inset-0');
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            document.getElementById(tabId).classList.remove('hidden');
            if(window.innerWidth < 768) toggleMobileMenu();
        }

        // Filtro Dinámico del Panel de Búsqueda de la Bandeja de Tareas
        function actualizarFiltrosResponsable() {
            const grupoSeleccionado = document.getElementById('filtroGrupo').value;
            const selectResp = document.getElementById('filtroResponsable');
            
            selectResp.innerHTML = '<option value="">Cualquier Responsable</option>';
            
            let miembrosFiltrados = [];
            if (!grupoSeleccionado) {
                miembrosFiltrados = todosLosUsuarios.map(u => u.username);
            } else if (grupoSeleccionado === 'Varios') {
                miembrosFiltrados = todosLosUsuarios.map(u => u.username);
            } else {
                const grupoObj = dataGrupos.find(g => g.nombre === grupoSeleccionado);
                if (grupoObj) miembrosFiltrados = grupoObj.miembros || [];
            }

            miembrosFiltrados.forEach(m => {
                selectResp.innerHTML += `<option value="${m}">${m}</option>`;
            });
        }

        // Sincronización cruzada para formularios de creación y edición
        function filtrarUsuariosPorGrupoForm(grupoSelectId, responsableSelectId, usuarioActual = "") {
            const gNombre = document.getElementById(grupoSelectId).value;
            const rSelect = document.getElementById(responsableSelectId);
            rSelect.innerHTML = '';

            let filtrados = [];
            if(gNombre === "Varios" || !gNombre) {
                filtrados = todosLosUsuarios.map(u => u.username);
            } else {
                const gObj = dataGrupos.find(g => g.nombre === gNombre);
                if(gObj) filtrados = gObj.miembros || [];
            }

            filtrados.forEach(m => {
                const sel = m === usuarioActual ? 'selected' : '';
                rSelect.innerHTML += `<option value="${m}" ${sel}>${m}</option>`;
            });
        }

        async function loadTareas(filters = {}) {
            const tbody = document.getElementById('tareasTableBody');
            const params = new URLSearchParams(filters).toString();
            const response = await fetch(`/api/tareas?${params}`);
            const data = await response.json();
            
            tbody.innerHTML = '';
            data.forEach(t => {
                const id = t._id?.$oid || t._id;
                const isComp = t.estado === 'completado';
                
                tbody.innerHTML += `
                    <tr class="hover:bg-white/40 cursor-pointer" onclick="openDetailPanel('${id}')">
                        <td class="py-3 px-4 text-center" onclick="event.stopPropagation()">
                            <button onclick="toggleCompletado('${id}', '${t.estado}')" class="w-4 h-4 rounded-full border-2 ${isComp ? 'bg-green-500 border-green-500 text-white' : 'border-slate-300'} flex items-center justify-center">
                                ${isComp ? '<i class="fa-solid fa-check text-[8px]"></i>' : ''}
                            </button>
                        </td>
                        <td class="py-3 px-4 font-semibold ${isComp ? 'line-through text-slate-400' : ''}">${t.descripcion}</td>
                        <td class="py-3 px-4"><span class="bg-purple-50 text-purple-700 font-bold px-2 py-0.5 rounded-full text-[10px]">${t.grupo_asignado}</span></td>
                        <td class="py-3 px-4 font-bold text-slate-600">${t.persona_asignada}</td>
                        <td class="py-3 px-4"><span class="text-red-600 font-semibold bg-red-50 px-2 py-0.5 rounded text-[10px]">${t.fecha_entrega}</span></td>
                        <td class="py-3 px-4 text-right" onclick="event.stopPropagation()">
                            <button onclick="eliminarTarea('${id}')" class="text-red-500 font-bold text-xs"><i class="fa-regular fa-trash-can"></i></button>
                        </td>
                    </tr>
                `;
            });
        }

        function applyFilters() {
            loadTareas({
                grupo: document.getElementById('filtroGrupo').value,
                responsable: document.getElementById('filtroResponsable').value,
                estado: document.getElementById('estadoFilter').value
            });
        }

        async function openDetailPanel(id) {
            activeTaskId = id;
            document.getElementById('asanaDetailPanel').classList.remove('hidden');
            const res = await fetch(`/api/tareas/detalle/${id}`);
            const t = await res.json();

            document.getElementById('detailTitle').textContent = t.descripcion;
            document.getElementById('detailGrupo').textContent = t.grupo_asignado;
            document.getElementById('detailAsignado').textContent = t.persona_asignada;

            {% if user_role == 'admin' %}
                document.getElementById('editTaskSection').classList.remove('hidden');
                document.getElementById('editDescripcion').value = t.descripcion;
                
                let editGrupoSelect = document.getElementById('editGrupo');
                editGrupoSelect.innerHTML = '<option value="Varios">Varios</option>';
                dataGrupos.forEach(g => {
                    const sel = g.nombre === t.grupo_asignado ? 'selected' : '';
                    editGrupoSelect.innerHTML += `<option value="${g.nombre}" ${sel}>${g.nombre}</option>`;
                });

                filtrarUsuariosPorGrupoForm('editGrupo', 'editResponsable', t.persona_asignada);
                document.getElementById('editFecha').value = t.fecha_entrega;
            {% endif %}

            const nContainer = document.getElementById('notasContainer');
            nContainer.innerHTML = '';
            if(t.novedades) {
                t.novedades.forEach(n => {
                    nContainer.innerHTML += `<div class="bg-white p-2 rounded-xl text-[11px] border border-slate-100"><strong>${n.autor}:</strong> ${n.texto}</div>`;
                });
            }
        }

        async function toggleCompletado(id, est) {
            await fetch('/api/tareas/actualizar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, estado: est === 'completado' ? 'pendiente' : 'completado'})
            });
            applyFilters();
        }

        async function guardarNovedad() {
            const txt = document.getElementById('nuevaNotaInput').value.trim();
            if(!txt || !activeTaskId) return;
            await fetch('/api/tareas/novedad', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: activeTaskId, texto: txt})
            });
            document.getElementById('nuevaNotaInput').value = '';
            openDetailPanel(activeTaskId);
        }

        async function guardarEdicionTarea() {
            await fetch('/api/tareas/editar-completo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: activeTaskId,
                    descripcion: document.getElementById('editDescripcion').value,
                    grupo_asignado: document.getElementById('editGrupo').value,
                    persona_asignada: document.getElementById('editResponsable').value,
                    fecha: document.getElementById('editFecha').value
                })
            });
            openDetailPanel(activeTaskId);
            applyFilters();
        }

        async function eliminarTarea(id) {
            if(confirm("¿Eliminar esta tarea definitivamente?")) {
                await fetch(`/api/tareas/eliminar/${id}`, {method: 'DELETE'});
                document.getElementById('asanaDetailPanel').classList.add('hidden');
                applyFilters();
            }
        }

        function eliminarUsuarioTotal(id) {
            if(confirm("¿Estás absolutamente seguro de eliminar esta cuenta del sistema? Esta acción no se puede deshacer.")) {
                window.location.href = `/admin/eliminar-usuario-total/${id}`;
            }
        }

        function closeDetailPanel() { document.getElementById('asanaDetailPanel').classList.add('hidden'); }

        document.addEventListener('DOMContentLoaded', () => {
            actualizarFiltrosResponsable();
            filtrarUsuariosPorGrupoForm('crearTareaGrupo', 'crearTareaResponsable');
            loadTareas();
        });
    </script>
</body>
</html>
"""

# --- AUXILIARES SERIALIZACIÓN ---
def obtener_listas_json():
    usuarios = list(usuarios_col.find({"rol": "user"}, {"username": 1}))
    grupos = list(grupos_col.find({}))
    
    for g in grupos:
        g['_id'] = str(g['_id'])
    for u in usuarios:
        u['_id'] = str(u['_id'])
        
    return json.dumps(usuarios), json.dumps(grupos)

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    lista_usuarios = list(usuarios_col.find({"rol": "user"}))
    lista_grupos = list(grupos_col.find({}))
    
    lista_usuarios_completa = []
    for u in usuarios_col.find({}):
        u['_id'] = str(u['_id'])
        lista_usuarios_completa.append(u)
        
    current_user = usuarios_col.find_one({"username": session['username']})
    avatar = current_user.get('avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&h=100&q=80')

    u_json, g_json = obtener_listas_json()

    return render_template_string(
        HTML_TEMPLATE,
        username=session['username'],
        user_role=session['rol'],
        current_user_avatar=avatar,
        lista_usuarios=lista_usuarios,
        lista_grupos=lista_grupos,
        lista_usuarios_completa=lista_usuarios_completa,
        lista_usuarios_json=u_json,
        lista_grupos_json=g_json
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = usuarios_col.find_one({"username": request.form.get('username'), "password": request.form.get('password')})
        if user:
            session['username'] = user['username']
            session['rol'] = user['rol']
            return redirect(url_for('index'))
        return render_template_string(LOGIN_TEMPLATE, error="Credenciales inválidas")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/perfil/actualizar-avatar', methods=['POST'])
def actualizar_avatar():
    if 'username' in session:
        usuarios_col.update_one({"username": session['username']}, {"$set": {"avatar": request.form.get('avatar_url')}})
    return redirect(url_for('index'))

# --- ACCIONES EXCLUSIVAS DE ADMINISTRADOR ---

@app.route('/admin/crear-usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') == 'admin':
        usuarios_col.insert_one({
            "username": request.form.get('nuevo_usuario'),
            "password": request.form.get('password'),
            "rol": request.form.get('rol'),
            "avatar": request.form.get('avatar'),
            "activo": True
        })
    return redirect(url_for('index'))

@app.route('/admin/eliminar-usuario-total/<id>', methods=['GET'])
def eliminar_usuario_total(id):
    if session.get('rol') == 'admin':
        usuarios_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))

@app.route('/admin/crear-grupo', methods=['POST'])
def crear_grupo():
    if session.get('rol') == 'admin':
        grupos_col.insert_one({"nombre": request.form.get('nombre_grupo'), "miembros": []})
    return redirect(url_for('index'))

@app.route('/admin/agregar-miembro-grupo', methods=['POST'])
def agregar_miembro_grupo():
    if session.get('rol') == 'admin':
        grupos_col.update_one({"_id": ObjectId(request.form.get('grupo_id'))}, {"$addToSet": {"miembros": request.form.get('miembro_nuevo')}})
    return redirect(url_for('index'))

@app.route('/admin/quitar-miembro-grupo/<grupo_id>/<username>', methods=['GET'])
def quitar_miembro_grupo(grupo_id, username):
    if session.get('rol') == 'admin':
        grupos_col.update_one({"_id": ObjectId(grupo_id)}, {"$pull": {"miembros": username}})
    return redirect(url_for('index'))

@app.route('/admin/crear-tarea', methods=['POST'])
def crear_tarea():
    if session.get('rol') == 'admin':
        visitas_col.insert_one({
            "descripcion": request.form.get('descripcion'),
            "grupo_asignado": request.form.get('grupo_asignado'),
            "persona_asignada": request.form.get('persona_asignada'),
            "fecha_entrega": request.form.get('fecha_entrega'),
            "estado": "pendiente",
            "novedades": []
        })
    return redirect(url_for('index'))

# --- ENDPOINTS API ---

@app.route('/api/tareas')
def get_tareas():
    query = {}
    
    # Restricción de rol
    if session.get('rol') != 'admin':
        username = session['username']
        mis_grupos = [g['nombre'] for g in grupos_col.find({"miembros": username})]
        query['$or'] = [{"persona_asignada": username}, {"grupo_asignado": {"$in": mis_grupos}}]

    grupo = request.args.get('grupo')
    if grupo: query['grupo_asignado'] = grupo
    
    responsable = request.args.get('responsable')
    if responsable: query['persona_asignada'] = responsable
    
    estado = request.args.get('estado')
    if estado: query['estado'] = estado

    return json_util.dumps(list(visitas_col.find(query))), 200, {'Content-Type': 'application/json'}

@app.route('/api/tareas/detalle/<id>')
def get_detalle(id):
    return json_util.dumps(visitas_col.find_one({"_id": ObjectId(id)})), 200, {'Content-Type': 'application/json'}

@app.route('/api/tareas/actualizar', methods=['POST'])
def actualizar_estado():
    visitas_col.update_one({"_id": ObjectId(request.json.get('id'))}, {"$set": {"estado": request.json.get('estado')}})
    return jsonify({"status": "ok"})

@app.route('/api/tareas/novedad', methods=['POST'])
def agregar_novedad():
    fecha_colombia = datetime.now(CO_TZ).strftime("%Y-%m-%d %I:%M %p")
    visitas_col.update_one({"_id": ObjectId(request.json.get('id'))}, {"$push": {"novedades": {"autor": session['username'], "fecha": fecha_colombia, "texto": request.json.get('texto')}}})
    return jsonify({"status": "ok"})

@app.route('/api/tareas/editar-completo', methods=['POST'])
def editar_completo():
    if session.get('rol') == 'admin':
        data = request.json
        visitas_col.update_one({"_id": ObjectId(data.get('id'))}, {"$set": {"descripcion": data.get('descripcion'), "grupo_asignado": data.get('grupo_asignado'), "persona_asignada": data.get('persona_asignada'), "fecha_entrega": data.get('fecha')}})
    return jsonify({"status": "ok"})

@app.route('/api/tareas/eliminar/<id>', methods=['DELETE'])
def eliminar_tarea(id):
    if session.get('rol') == 'admin': visitas_col.delete_one({"_id": ObjectId(id)})
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
