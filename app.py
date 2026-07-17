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

# --- PLANTILLA DEL LOGIN (Liquid Glass Light Style) ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
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
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.05), 
                        inset 0 1px 1px rgba(255, 255, 255, 0.5);
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
                <input type="text" name="username" required placeholder="Tu usuario" class="w-full bg-white/60 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Contraseña</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-white/60 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-md text-xs uppercase tracking-wider mt-2">
                Iniciar Sesión
            </button>
        </form>
    </div>
</body>
</html>
"""

# --- PLANTILLA PRINCIPAL (Liquid Glass Light HTML) ---
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
            background: radial-gradient(circle at 0% 0%, rgba(59, 130, 246, 0.08) 0%, rgba(255, 255, 255, 0) 50%),
                        radial-gradient(circle at 100% 100%, rgba(249, 115, 22, 0.05) 0%, rgba(255, 255, 255, 0) 50%),
                        #f8fafc;
        }
        .liquid-glass-panel {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.04);
        }
        .liquid-glass-card {
            background: rgba(255, 255, 255, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.6);
            transition: all 0.25s ease;
        }
        .liquid-glass-card:hover {
            background: rgba(255, 255, 255, 0.65);
            border: 1px solid rgba(59, 130, 246, 0.2);
            box-shadow: 0 10px 20px -10px rgba(0, 0, 0, 0.05);
        }
        .custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.08); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 0, 0, 0.15); }
    </style>
</head>
<body class="text-slate-700 h-screen overflow-hidden flex p-4 md:p-6 gap-6">

    <!-- BARRA LATERAL (SIDEBAR) -->
    <aside class="w-64 liquid-glass-panel rounded-3xl flex flex-col justify-between h-full flex-shrink-0 overflow-hidden">
        <div>
            <!-- Perfil de Usuario -->
            <div class="p-6 border-b border-slate-200/50 flex items-center space-x-3">
                <img id="myAvatar" src="{{ current_user_avatar }}" class="w-10 h-10 rounded-xl object-cover border border-slate-200 shadow-sm" alt="Mi Foto">
                <div class="truncate">
                    <h1 class="font-bold text-sm tracking-tight text-slate-900">{{ username }}</h1>
                    <span class="text-[9px] font-bold text-blue-600 uppercase tracking-widest">{{ user_role }}</span>
                </div>
            </div>

            <!-- Navegación -->
            <div class="p-4 space-y-1">
                <div class="text-[9px] font-bold text-slate-400 uppercase px-3 mb-2 tracking-wider">Menú Colaborativo</div>
                <button onclick="switchTab('tareasTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold bg-white/60 text-slate-900 shadow-sm transition-all">
                    <i class="fa-solid fa-layer-group text-blue-500"></i>
                    <span>Bandeja de Tareas</span>
                </button>
                <button onclick="switchTab('gruposTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all">
                    <i class="fa-solid fa-users text-purple-500"></i>
                    <span>Ver Grupos y Miembros</span>
                </button>
                {% if user_role == 'admin' %}
                <button onclick="switchTab('adminTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all">
                    <i class="fa-solid fa-user-gear text-orange-500"></i>
                    <span>Administración / Personal</span>
                </button>
                {% endif %}
                <button onclick="switchTab('perfilTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all">
                    <i class="fa-solid fa-user-astronaut text-green-500"></i>
                    <span>Mi Perfil (Foto)</span>
                </button>
            </div>
        </div>

        <div class="p-4 border-t border-slate-200/50">
            <a href="/logout" class="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs transition-colors border border-red-100">
                <i class="fa-solid fa-power-off"></i>
                <span>Cerrar Sesión</span>
            </a>
        </div>
    </aside>

    <!-- ÁREA DE CONTENIDO PRINCIPAL -->
    <main class="flex-grow flex flex-col h-full overflow-hidden">
        
        <!-- ================= TAB: TAREAS ================= -->
        <div id="tareasTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden">
            <!-- Header Tareas -->
            <header class="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-extrabold text-slate-900 tracking-tight">Tareas del Equipo</h2>
                    <p class="text-xs text-slate-500">Doble asignación: Grupo Responsable + Encargado de Tarea</p>
                </div>
                
                <!-- Filtros -->
                <div class="flex items-center gap-3">
                    <select id="filtroGrupo" onchange="applyFilters()" class="text-xs font-semibold text-slate-600 bg-white/70 border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-400">
                        <option value="">Todos los Grupos / Áreas</option>
                        <option value="Varios">Sueltas (Grupo: Varios)</option>
                        {% for g in lista_grupos %}
                            <option value="{{ g.nombre }}">{{ g.nombre }}</option>
                        {% endfor %}
                    </select>
                    <select id="estadoFilter" onchange="applyFilters()" class="text-xs font-semibold text-slate-600 bg-white/70 border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-400">
                        <option value="">Cualquier Estado</option>
                        <option value="pendiente">Pendientes</option>
                        <option value="completado">Completadas</option>
                    </select>
                    <input type="text" id="searchQuery" oninput="applyFilters()" placeholder="Buscar tarea..." class="text-xs text-slate-700 placeholder-slate-400 bg-white/70 border border-slate-200 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-1 focus:ring-blue-400 w-44">
                </div>
            </header>

            <div class="flex-grow flex overflow-hidden gap-6">
                <!-- Listado de Tareas -->
                <div class="flex-grow overflow-y-auto custom-scrollbar space-y-4 pr-1">
                    
                    {% if user_role == 'admin' %}
                    <!-- ACCIÓN ADMIN: Crear Tarea -->
                    <div class="liquid-glass-panel rounded-2xl p-5 mb-4">
                        <h3 class="text-xs font-bold text-blue-600 uppercase tracking-widest mb-4"><i class="fa-solid fa-circle-plus mr-2"></i>Nueva Tarea Con Doble Asignación</h3>
                        <form action="/admin/crear-tarea" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <input type="text" name="descripcion" required placeholder="¿Qué se debe hacer?..." class="bg-white/80 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 placeholder-slate-450 focus:outline-none">
                            
                            <!-- Selección de Área/Grupo -->
                            <select name="grupo_asignado" required class="bg-white/80 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-600 focus:outline-none">
                                <option value="Varios">Grupo/Área: Varios (Sueltas)</option>
                                {% for g in lista_grupos %}
                                    <option value="{{ g.nombre }}">Área: {{ g.nombre }}</option>
                                {% endfor %}
                            </select>

                            <!-- Selección de Responsable -->
                            <select name="persona_asignada" required class="bg-white/80 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-600 focus:outline-none">
                                <option value="">Persona Responsable...</option>
                                {% for u in lista_usuarios %}
                                    <option value="{{ u.username }}">{{ u.username }}</option>
                                {% endfor %}
                            </select>

                            <div class="flex gap-2">
                                <input type="date" name="fecha_entrega" required class="bg-white/80 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-600 focus:outline-none flex-grow">
                                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 rounded-xl text-xs transition-colors">Asignar</button>
                            </div>
                        </form>
                    </div>
                    {% endif %}

                    <!-- Tabla de Tareas Estilo Liquid Claro -->
                    <div class="liquid-glass-panel rounded-2xl overflow-hidden">
                        <table class="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr class="border-b border-slate-200 bg-slate-50/50 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                    <th class="py-3.5 px-6 w-12 text-center">Estado</th>
                                    <th class="py-3.5 px-6">Descripción</th>
                                    <th class="py-3.5 px-6">Área / Grupo</th>
                                    <th class="py-3.5 px-6">Asignado A</th>
                                    <th class="py-3.5 px-6">Vence</th>
                                    <th class="py-3.5 px-6 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody id="tareasTableBody" class="divide-y divide-slate-100">
                                <!-- Cargado dinámicamente -->
                            </tbody>
                        </table>
                    </div>

                </div>

                <!-- PANEL DETALLE LATERAL (Notas y Novedades) -->
                <div id="asanaDetailPanel" class="w-96 liquid-glass-panel rounded-2xl h-full flex flex-col justify-between hidden flex-shrink-0">
                    <div class="p-6 space-y-5 overflow-y-auto custom-scrollbar flex-grow">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] font-bold text-blue-600 uppercase tracking-widest">Panel de Detalle</span>
                            <button onclick="closeDetailPanel()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-times"></i></button>
                        </div>

                        <!-- Edición Avanzada (Solo Admin) -->
                        <div id="editTaskSection" class="hidden space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
                            <span class="text-[10px] font-bold text-orange-600 uppercase tracking-widest">Modificar Tarea</span>
                            
                            <input type="text" id="editDescripcion" class="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                            
                            <div class="space-y-2">
                                <label class="text-[9px] font-bold text-slate-400 block uppercase">Asignación de Grupo y Persona</label>
                                <select id="editGrupo" class="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700">
                                    <option value="Varios">Varios (Sueltas)</option>
                                    {% for g in lista_grupos %}
                                        <option value="{{ g.nombre }}">{{ g.nombre }}</option>
                                    {% endfor %}
                                </select>
                                <select id="editResponsable" class="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700">
                                    {% for u in lista_usuarios %}
                                        <option value="{{ u.username }}">{{ u.username }}</option>
                                    {% endfor %}
                                </select>
                            </div>

                            <input type="date" id="editFecha" class="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700">
                            
                            <button onclick="guardarEdicionTarea()" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-1.5 rounded-lg text-xs transition-colors">Guardar Modificaciones</button>
                        </div>

                        <!-- Detalle lectura -->
                        <div id="readTaskSection" class="space-y-3">
                            <h3 id="detailTitle" class="text-sm font-bold text-slate-900"></h3>
                            <div class="grid grid-cols-2 gap-2 text-xs text-slate-600 bg-white/50 p-3 rounded-lg border border-slate-100">
                                <div><span class="text-[9px] uppercase font-bold text-slate-400 block">Grupo/Área</span><span id="detailGrupo" class="font-semibold">-</span></div>
                                <div><span class="text-[9px] uppercase font-bold text-slate-400 block">Encargado</span><span id="detailAsignado" class="font-semibold">-</span></div>
                            </div>
                        </div>

                        <hr class="border-slate-200">

                        <!-- Novedades -->
                        <div class="space-y-3">
                            <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center">
                                <i class="fa-regular fa-comment-dots mr-2 text-blue-500"></i> Notas y Novedades (Colombia)
                            </h4>
                            <div class="space-y-2">
                                <textarea id="nuevaNotaInput" placeholder="Añadir comentarios, novedades..." rows="2" class="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"></textarea>
                                <button onclick="guardarNovedad()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-1.5 rounded-lg text-xs transition-colors">Guardar Nota</button>
                            </div>

                            <div id="notasContainer" class="space-y-2 max-h-56 overflow-y-auto custom-scrollbar">
                                <!-- Cargado dinámicamente -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ================= TAB: GRUPOS ================= -->
        <div id="gruposTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-6">
                <h2 class="text-2xl font-extrabold text-slate-900 tracking-tight">Grupos de Trabajo / Áreas</h2>
                <p class="text-xs text-slate-500">Visualiza los equipos de trabajo definidos en la organización</p>
            </header>

            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-6">
                <!-- Crear Nuevo Grupo (Solo Admin) -->
                {% if user_role == 'admin' %}
                <div class="liquid-glass-panel rounded-2xl p-5 mb-4 max-w-md">
                    <h3 class="text-xs font-bold text-purple-600 uppercase tracking-widest mb-4"><i class="fa-solid fa-folder-plus mr-2"></i>Crear Nuevo Grupo / Área</h3>
                    <form action="/admin/crear-grupo" method="POST" class="flex gap-2">
                        <input type="text" name="nombre_grupo" required placeholder="Nombre del área (ej: Logística)..." class="bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none flex-grow">
                        <button type="submit" class="bg-purple-600 hover:bg-purple-700 text-white font-bold px-4 rounded-xl text-xs transition-colors">Crear</button>
                    </form>
                </div>
                {% endif %}

                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {% for g in lista_grupos %}
                    <div class="liquid-glass-panel rounded-2xl p-6 space-y-4">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-sm text-slate-900 flex items-center"><i class="fa-solid fa-folder-open mr-2 text-purple-500"></i>{{ g.nombre }}</span>
                            <span class="text-[10px] bg-purple-100 text-purple-700 px-2.5 py-0.5 rounded-full font-mono">{{ g.miembros|length }} Integrantes</span>
                        </div>
                        
                        <div class="space-y-2 pt-2 border-t border-slate-200 max-h-48 overflow-y-auto custom-scrollbar">
                            {% for m in g.miembros %}
                                <div class="flex items-center justify-between text-xs py-1 px-2 hover:bg-slate-100 rounded-lg">
                                    <span class="text-slate-600"><i class="fa-regular fa-user mr-2 text-slate-400"></i>{{ m }}</span>
                                    {% if user_role == 'admin' %}
                                    <button onclick="quitarDeGrupo('{{ g._id }}', '{{ m }}')" class="text-red-500 hover:text-red-700 font-bold" title="Remover del grupo">Quitar</button>
                                    {% endif %}
                                </div>
                            {% else %}
                                <span class="text-xs text-slate-400 italic block">Sin miembros asignados.</span>
                            {% endfor %}
                        </div>

                        {% if user_role == 'admin' %}
                        <form action="/admin/agregar-miembro-grupo" method="POST" class="pt-2 border-t border-slate-200 flex gap-2">
                            <input type="hidden" name="grupo_id" value="{{ g._id }}">
                            <select name="miembro_nuevo" required class="bg-white border border-slate-200 rounded-xl px-2 py-1.5 text-xs text-slate-600 focus:outline-none flex-grow">
                                <option value="">Añadir persona...</option>
                                {% for u in lista_usuarios %}
                                    {% if u.username not in g.miembros %}
                                        <option value="{{ u.username }}">{{ u.username }}</option>
                                    {% endif %}
                                {% endfor %}
                            </select>
                            <button type="submit" class="bg-purple-600 hover:bg-purple-700 text-white font-bold px-3 rounded-xl text-xs transition-colors">+</button>
                        </form>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- ================= TAB: ADMIN (PERSONAL & NUEVO USUARIO) ================= -->
        {% if user_role == 'admin' %}
        <div id="adminTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-6">
                <h2 class="text-2xl font-extrabold text-slate-900 tracking-tight">Administración de Colaboradores</h2>
                <p class="text-xs text-slate-500">Crea nuevos usuarios, edita perfiles, asigna grupos y administra accesos</p>
            </header>

            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-6">
                
                <!-- REGISTRO DE NUEVO COLABORADOR (SOLICITADO) -->
                <div class="liquid-glass-panel rounded-2xl p-6">
                    <h3 class="text-xs font-bold text-blue-600 uppercase tracking-widest mb-4"><i class="fa-solid fa-user-plus mr-2"></i>Registrar Nuevo Colaborador</h3>
                    <form action="/admin/crear-usuario" method="POST" class="grid grid-cols-1 md:grid-cols-5 gap-4">
                        <input type="text" name="nuevo_usuario" required placeholder="Nombre de usuario..." class="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none">
                        <input type="password" name="password" required placeholder="Contraseña..." class="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none">
                        
                        <select name="rol" required class="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-600 focus:outline-none">
                            <option value="user">Colaborador</option>
                            <option value="admin">Administrador</option>
                        </select>

                        <input type="url" name="avatar" placeholder="URL Foto de Perfil (Obligatorio)..." required class="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none">
                        
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors py-2.5">Registrar</button>
                    </form>
                </div>

                <!-- TABLA DE USUARIOS EXISTENTES -->
                <div class="liquid-glass-panel rounded-2xl overflow-hidden">
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="border-b border-slate-200 bg-slate-50/50 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                <th class="py-3.5 px-6">Foto</th>
                                <th class="py-3.5 px-6">Usuario</th>
                                <th class="py-3.5 px-6">Rol</th>
                                <th class="py-3.5 px-6">Grupo Principal</th>
                                <th class="py-3.5 px-6">Estado</th>
                                <th class="py-3.5 px-6 text-right">Acciones de Control</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            {% for u in lista_usuarios_completa %}
                            <tr class="hover:bg-white/50 transition-colors">
                                <td class="py-3 px-6">
                                    <img src="{{ u.avatar or 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&h=100&q=80' }}" class="w-8 h-8 rounded-lg object-cover border border-slate-200 shadow-sm" alt="Foto">
                                </td>
                                <td class="py-3 px-6 font-semibold text-slate-900">{{ u.username }}</td>
                                <td class="py-3 px-6 capitalize text-slate-500">{{ u.rol }}</td>
                                <td class="py-3 px-6">
                                    <span class="text-slate-600 font-semibold">{{ u.grupo_nombre or 'Varios (Persona Sola)' }}</span>
                                </td>
                                <td class="py-3 px-6">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold {{ 'bg-green-100 text-green-700 border border-green-200' if u.activo != False else 'bg-red-100 text-red-700 border border-red-200' }}">
                                        {{ 'Activo' if u.activo != False else 'Inhabilitado' }}
                                    </span>
                                </td>
                                <td class="py-3 px-6 text-right space-x-2">
                                    <button onclick="openEditUserModal('{{ u._id }}', '{{ u.username }}', '{{ u.rol }}', '{{ u.grupo }}', '{{ u.activo }}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-lg transition-all border border-slate-200">Editar / Reset</button>
                                    <button onclick="toggleInhabilitarUser('{{ u._id }}', {{ 'true' if u.activo != False else 'false' }})" class="{{ 'text-red-500 hover:text-red-700' if u.activo != False else 'text-green-600 hover:text-green-700' }} font-bold">
                                        {{ 'Inhabilitar' if u.activo != False else 'Habilitar' }}
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- ================= TAB: MI PERFIL (Foto de Perfil Obligatoria) ================= -->
        <div id="perfilTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-6">
                <h2 class="text-2xl font-extrabold text-slate-900 tracking-tight">Mi Perfil</h2>
                <p class="text-xs text-slate-500">Gestiona tu foto de perfil de colaboración</p>
            </header>

            <div class="max-w-md bg-white/70 border border-slate-200/80 p-6 rounded-2xl shadow-md space-y-6">
                <div class="flex items-center space-x-4">
                    <img id="profilePreview" src="{{ current_user_avatar }}" class="w-20 h-20 rounded-2xl object-cover border border-slate-300 shadow-md" alt="Foto">
                    <div>
                        <h3 class="font-bold text-base text-slate-900">{{ username }}</h3>
                        <p class="text-xs text-slate-500">Rol: {{ user_role }}</p>
                    </div>
                </div>

                <form action="/perfil/actualizar-avatar" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Enlace URL de tu foto de perfil</label>
                        <input type="url" name="avatar_url" required value="{{ current_user_avatar }}" class="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400">
                    </div>
                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition-colors shadow-sm">Actualizar Foto</button>
                </form>
            </div>
        </div>

    </main>

    <!-- MODAL PARA EDITAR USUARIO / RESETEAR PASSWORD (SOLO ADMIN) -->
    <div id="editUserModal" class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 hidden z-50">
        <div class="liquid-glass-panel p-8 rounded-3xl w-full max-w-md text-slate-800 bg-white border border-slate-200">
            <div class="flex justify-between items-center mb-6">
                <h3 class="font-bold text-base text-slate-900">Modificar Colaborador</h3>
                <button onclick="closeEditUserModal()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-times"></i></button>
            </div>
            
            <form action="/admin/editar-colaborador" method="POST" class="space-y-4">
                <input type="hidden" id="editUserId" name="user_id">
                
                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Nombre de Usuario</label>
                    <input type="text" id="editUsernameInput" name="username" readonly class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-500 focus:outline-none">
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Nueva Contraseña (Dejar vacío para no cambiar)</label>
                    <input type="password" name="password" placeholder="Establecer clave nueva" class="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400">
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Rol de Sistema</label>
                    <select id="editUserRol" name="rol" class="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-700 focus:outline-none">
                        <option value="user">Colaborador</option>
                        <option value="admin">Administrador</option>
                    </select>
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Grupo / Área Principal</label>
                    <select id="editUserGrupo" name="grupo_id" class="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-700 focus:outline-none">
                        <option value="">Varios (Ninguno)</option>
                        {% for g in lista_grupos %}
                            <option value="{{ g._id }}">{{ g.nombre }}</option>
                        {% endfor %}
                    </select>
                </div>

                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-xs transition-colors">Guardar Cambios</button>
            </form>
        </div>
    </div>

    <!-- SCRIPT FRONTEND -->
    <script>
        let activeTaskId = null;

        // Cambiar pestañas
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
            document.getElementById(tabId).classList.remove('hidden');

            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-white/60', 'text-slate-900', 'shadow-sm');
                btn.classList.add('text-slate-500');
            });
            event.currentTarget.classList.add('bg-white/60', 'text-slate-900', 'shadow-sm');
            event.currentTarget.classList.remove('text-slate-500');
        }

        // Cargar Tareas dinámicamente
        async function loadTareas(filters = {}) {
            const tbody = document.getElementById('tareasTableBody');
            const params = new URLSearchParams(filters).toString();
            
            try {
                const response = await fetch(`/api/tareas?${params}`);
                const data = await response.json();
                
                tbody.innerHTML = '';

                if (data.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6" class="text-center py-8 text-slate-400 italic">
                                No se encontraron tareas para estos criterios.
                            </td>
                        </tr>`;
                    return;
                }

                data.forEach(tarea => {
                    const mongoId = tarea._id?.$oid || tarea._id || '';
                    const isCompleted = tarea.estado === 'completado';
                    
                    // Colores de los badges del grupo/área asignado
                    let badgeGrupo = '';
                    if (tarea.grupo_asignado && tarea.grupo_asignado !== 'Varios') {
                        badgeGrupo = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 border border-purple-200"><i class="fa-solid fa-users mr-1"></i>${tarea.grupo_asignado}</span>`;
                    } else {
                        badgeGrupo = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200"><i class="fa-solid fa-tags mr-1"></i>Varios</span>`;
                    }

                    // Botón para eliminar tareas (Admin)
                    let deleteButton = '';
                    {% if user_role == 'admin' %}
                    deleteButton = `
                        <button onclick="eliminarTarea('${mongoId}')" class="text-red-500 hover:text-red-700 font-bold ml-2 transition-colors" title="Eliminar tarea">
                            <i class="fa-regular fa-trash-can"></i>
                        </button>
                    `;
                    {% endif %}

                    tbody.innerHTML += `
                        <tr class="hover:bg-white/40 transition-colors cursor-pointer" onclick="openDetailPanel('${mongoId}')">
                            <td class="py-3.5 px-6 text-center" onclick="event.stopPropagation()">
                                <button onclick="toggleCompletado('${mongoId}', '${tarea.estado}')" class="w-5 h-5 rounded-full border-2 ${isCompleted ? 'border-green-500 bg-green-500 text-white' : 'border-slate-300 hover:border-blue-500'} flex items-center justify-center transition-all">
                                    ${isCompleted ? '<i class="fa-solid fa-check text-[10px]"></i>' : ''}
                                </button>
                            </td>
                            <td class="py-3.5 px-6 font-semibold text-slate-800 ${isCompleted ? 'line-through text-slate-400 font-normal' : ''}">
                                ${tarea.descripcion}
                            </td>
                            <td class="py-3.5 px-6">
                                ${badgeGrupo}
                            </td>
                            <td class="py-3.5 px-6">
                                <span class="text-slate-600 font-bold"><i class="fa-regular fa-user mr-1 text-slate-400"></i>${tarea.persona_asignada || 'Sin asignar'}</span>
                            </td>
                            <td class="py-3.5 px-6">
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-50 text-red-600 border border-red-100">
                                    <i class="fa-regular fa-calendar mr-1"></i>${tarea.fecha_entrega}
                                </span>
                            </td>
                            <td class="py-3.5 px-6 text-right" onclick="event.stopPropagation()">
                                <button onclick="openDetailPanel('${mongoId}')" class="text-blue-600 hover:text-blue-700 font-bold">Ver</button>
                                ${deleteButton}
                            </td>
                        </tr>
                    `;
                });

            } catch (error) {
                console.error("Error al cargar tareas", error);
            }
        }

        // Cargar detalles de tarea al panel de Asana
        async function openDetailPanel(id) {
            activeTaskId = id;
            document.getElementById('asanaDetailPanel').classList.remove('hidden');

            try {
                const response = await fetch(`/api/tareas/detalle/${id}`);
                const tarea = await response.json();

                document.getElementById('detailTitle').textContent = tarea.descripcion;
                document.getElementById('detailGrupo').textContent = tarea.grupo_asignado || 'Varios';
                document.getElementById('detailAsignado').textContent = tarea.persona_asignada || 'Sin asignar';

                // Si eres administrador, puedes editar la tarea directamente
                {% if user_role == 'admin' %}
                    document.getElementById('editTaskSection').classList.remove('hidden');
                    document.getElementById('editDescripcion').value = tarea.descripcion;
                    document.getElementById('editGrupo').value = tarea.grupo_asignado || 'Varios';
                    document.getElementById('editResponsable').value = tarea.persona_asignada || '';
                    document.getElementById('editFecha').value = tarea.fecha_entrega || '';
                {% endif %}

                // Render de novedades registradas en hora de Colombia
                const container = document.getElementById('notasContainer');
                container.innerHTML = '';
                if(tarea.novedades && tarea.novedades.length > 0) {
                    tarea.novedades.forEach(n => {
                        container.innerHTML += `
                            <div class="bg-white border border-slate-200/60 rounded-xl p-3 space-y-1">
                                <div class="flex justify-between items-center text-[9px] text-slate-400">
                                    <span class="font-bold text-slate-600">${n.autor}</span>
                                    <span>${n.fecha}</span>
                                </div>
                                <p class="text-xs text-slate-700 leading-relaxed">${n.texto}</p>
                            </div>
                        `;
                    });
                } else {
                    container.innerHTML = '<span class="text-[10px] text-slate-400 italic block text-center py-4">Sin novedades aún.</span>';
                }

            } catch (e) {
                console.error("Error al recuperar el detalle de la tarea", e);
            }
        }

        function closeDetailPanel() {
            document.getElementById('asanaDetailPanel').classList.add('hidden');
            activeTaskId = null;
        }

        async function toggleCompletado(id, estadoActual) {
            const nuevoEstado = estadoActual === 'completado' ? 'pendiente' : 'completado';
            const res = await fetch(`/api/tareas/actualizar`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, estado: nuevoEstado})
            });
            if(res.ok) {
                loadTareas();
                if(activeTaskId === id) openDetailPanel(id);
            }
        }

        async function guardarNovedad() {
            const txt = document.getElementById('nuevaNotaInput').value.trim();
            if(!txt || !activeTaskId) return;

            const res = await fetch(`/api/tareas/novedad`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: activeTaskId, texto: txt})
            });

            if(res.ok) {
                document.getElementById('nuevaNotaInput').value = '';
                openDetailPanel(activeTaskId);
                loadTareas();
            }
        }

        async function guardarEdicionTarea() {
            if(!activeTaskId) return;
            const desc = document.getElementById('editDescripcion').value;
            const grupo = document.getElementById('editGrupo').value;
            const resp = document.getElementById('editResponsable').value;
            const fec = document.getElementById('editFecha').value;

            const res = await fetch(`/api/tareas/editar-completo`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: activeTaskId, descripcion: desc, grupo_asignado: grupo, persona_asignada: resp, fecha: fec})
            });

            if(res.ok) {
                openDetailPanel(activeTaskId);
                loadTareas();
            }
        }

        async function eliminarTarea(id) {
            if(confirm("¿Seguro que deseas eliminar esta tarea permanentemente?")) {
                const res = await fetch(`/api/tareas/eliminar/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    closeDetailPanel();
                    loadTareas();
                }
            }
        }

        function applyFilters() {
            loadTareas({
                grupo: document.getElementById('filtroGrupo').value,
                estado: document.getElementById('estadoFilter').value,
                q: document.getElementById('searchQuery').value
            });
        }

        // Modales de control de usuarios
        function openEditUserModal(id, username, rol, grupo, activo) {
            document.getElementById('editUserModal').classList.remove('hidden');
            document.getElementById('editUserId').value = id;
            document.getElementById('editUsernameInput').value = username;
            document.getElementById('editUserRol').value = rol;
            document.getElementById('editUserGrupo').value = grupo || "";
        }

        function closeEditUserModal() {
            document.getElementById('editUserModal').classList.add('hidden');
        }

        async function toggleInhabilitarUser(id, actualActivo) {
            const actionText = actualActivo ? 'deshabilitar' : 'habilitar';
            if(confirm(`¿Estás seguro de que deseas ${actionText} a este colaborador?`)) {
                window.location.href = `/admin/cambiar-estado-usuario/${id}/${!actualActivo}`;
            }
        }

        async function quitarDeGrupo(grupoId, username) {
            if(confirm(`¿Quieres retirar a ${username} de este grupo de trabajo?`)) {
                window.location.href = `/admin/quitar-miembro-grupo/${grupoId}/${username}`;
            }
        }

        document.addEventListener('DOMContentLoaded', () => loadTareas());
    </script>
</body>
</html>
"""

# --- INICIALIZAR ELEMENTOS BASE (ADMIN) ---
def inicializar_sistema():
    if usuarios_col.count_documents({}) == 0:
        usuarios_col.insert_one({
            "username": "admin",
            "password": "123",
            "rol": "admin",
            "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
            "activo": True
        })

# --- CONTROLADORES DE FLASK ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    lista_usuarios = list(usuarios_col.find({"rol": "user"}, {"password": 0}))
    lista_grupos = list(grupos_col.find({}))
    
    lista_usuarios_completa = []
    for u in usuarios_col.find({}):
        u['_id'] = str(u['_id'])
        if u.get('grupo'):
            g = grupos_col.find_one({"_id": ObjectId(u['grupo'])})
            u['grupo_nombre'] = g['nombre'] if g else None
        lista_usuarios_completa.append(u)
        
    current_user = usuarios_col.find_one({"username": session['username']})
    avatar = current_user.get('avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80')

    return render_template_string(
        HTML_TEMPLATE,
        username=session['username'],
        user_role=session['rol'],
        current_user_avatar=avatar,
        lista_usuarios=lista_usuarios,
        lista_grupos=lista_grupos,
        lista_usuarios_completa=lista_usuarios_completa
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    inicializar_sistema()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = usuarios_col.find_one({"username": username, "password": password})
        
        if user:
            if user.get('activo') == False:
                return render_template_string(LOGIN_TEMPLATE, error="Tu cuenta ha sido inhabilitada. Contacta al administrador.")
                
            session['username'] = user['username']
            session['rol'] = user['rol']
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Nombre de usuario o contraseña incorrectos")
            
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ACTUALIZAR FOTO ---
@app.route('/perfil/actualizar-avatar', methods=['POST'])
def actualizar_avatar():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    url = request.form.get('avatar_url')
    if url:
        usuarios_col.update_one(
            {"username": session['username']},
            {"$set": {"avatar": url}}
        )
    return redirect(url_for('index'))

# --- CONTROL DE ADMINISTRACIÓN Y COLABORADORES ---

@app.route('/admin/crear-usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    username = request.form.get('nuevo_usuario')
    password = request.form.get('password')
    rol = request.form.get('rol', 'user')
    avatar_url = request.form.get('avatar')

    if username and password:
        usuarios_col.update_one(
            {"username": username},
            {"$set": {
                "password": password, 
                "rol": rol, 
                "avatar": avatar_url or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
                "activo": True
            }},
            upsert=True
        )
            
    return redirect(url_for('index'))

@app.route('/admin/editar-colaborador', methods=['POST'])
def editar_colaborador():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    user_id = request.form.get('user_id')
    password = request.form.get('password')
    rol = request.form.get('rol')
    grupo_id = request.form.get('grupo_id')

    if user_id:
        update_data = {"rol": rol, "grupo": grupo_id}
        if password:
            update_data["password"] = password

        usuarios_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        # Vincular automáticamente al grupo de trabajo
        if grupo_id:
            user_doc = usuarios_col.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                grupos_col.update_one(
                    {"_id": ObjectId(grupo_id)},
                    {"$addToSet": {"miembros": user_doc['username']}}
                )

    return redirect(url_for('index'))

@app.route('/admin/cambiar-estado-usuario/<id>/<activo>', methods=['GET'])
def cambiar_estado_usuario(id, activo):
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    is_active = activo == 'true'
    usuarios_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"activo": is_active}}
    )
    return redirect(url_for('index'))

# --- CONTROL DE GRUPOS ---

@app.route('/admin/crear-grupo', methods=['POST'])
def crear_grupo():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
    
    nombre_grupo = request.form.get('nombre_grupo')
    if nombre_grupo:
        grupos_col.update_one(
            {"nombre": nombre_grupo},
            {"$set": {"nombre": nombre_grupo, "miembros": []}},
            upsert=True
        )
    return redirect(url_for('index'))

@app.route('/admin/agregar-miembro-grupo', methods=['POST'])
def agregar_miembro_grupo():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    grupo_id = request.form.get('grupo_id')
    miembro_nuevo = request.form.get('miembro_nuevo')

    if grupo_id and miembro_nuevo:
        grupos_col.update_one(
            {"_id": ObjectId(grupo_id)},
            {"$addToSet": {"miembros": miembro_nuevo}}
        )
    return redirect(url_for('index'))

@app.route('/admin/quitar-miembro-grupo/<grupo_id>/<username>', methods=['GET'])
def quitar_miembro_grupo(grupo_id, username):
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    grupos_col.update_one(
        {"_id": ObjectId(grupo_id)},
        {"$pull": {"miembros": username}}
    )
    return redirect(url_for('index'))

# --- CONTROL DE TAREAS ---

@app.route('/admin/crear-tarea', methods=['POST'])
def crear_tarea():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    descripcion = request.form.get('descripcion')
    grupo_asignado = request.form.get('grupo_asignado', 'Varios') # Si es suelta, va a 'Varios'
    persona_asignada = request.form.get('persona_asignada')
    fecha_entrega = request.form.get('fecha_entrega')

    if descripcion:
        visitas_col.insert_one({
            "descripcion": descripcion,
            "grupo_asignado": grupo_asignado,
            "persona_asignada": persona_asignada,
            "fecha_entrega": fecha_entrega,
            "estado": "pendiente",
            "novedades": []
        })
        
    return redirect(url_for('index'))

# --- API ENDPOINTS ---

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    if 'username' not in session:
        return jsonify([]), 401
        
    query = {}
    username = session['username']
    
    # Si no es admin, solo puede ver sus asignaciones directas o de sus áreas
    if session.get('rol') != 'admin':
        mis_grupos_docs = list(grupos_col.find({"miembros": username}))
        mis_grupos_nombres = [g['nombre'] for g in mis_grupos_docs]
        
        query['$or'] = [
            {"persona_asignada": username},
            {"grupo_asignado": {"$in": mis_grupos_nombres}}
        ]
        
    # Filtro específico de barra de búsqueda / grupo
    grupo_filtro = request.args.get('grupo')
    if grupo_filtro:
        query['grupo_asignado'] = grupo_filtro

    estado = request.args.get('estado')
    if estado:
        query['estado'] = estado
        
    search_q = request.args.get('q')
    if search_q:
        query['descripcion'] = {'$regex': search_q, '$options': 'i'}

    tareas = list(visitas_col.find(query))
    return json_util.dumps(tareas), 200, {'Content-Type': 'application/json'}

@app.route('/api/tareas/detalle/<id>', methods=['GET'])
def get_detalle_tarea(id):
    if 'username' not in session:
        return "No autorizado", 401
        
    tarea = visitas_col.find_one({"_id": ObjectId(id)})
    return json_util.dumps(tarea), 200, {'Content-Type': 'application/json'}

@app.route('/api/tareas/actualizar', methods=['POST'])
def actualizar_tarea():
    if 'username' not in session:
        return "No autorizado", 401
        
    data = request.json
    tarea_id = data.get('id')
    nuevo_estado = data.get('estado')
    
    visitas_col.update_one(
        {"_id": ObjectId(tarea_id)},
        {"$set": {"estado": nuevo_estado}}
    )
    return jsonify({"status": "success"})

@app.route('/api/tareas/novedad', methods=['POST'])
def agregar_novedad():
    if 'username' not in session:
        return "No autorizado", 401
        
    data = request.json
    tarea_id = data.get('id')
    texto_nota = data.get('texto')
    
    # Hora local de Colombia usando timedelta nativo de forma limpia
    fecha_colombia = datetime.now(CO_TZ).strftime("%Y-%m-%d %I:%M %p")
    
    novedad = {
        "autor": session['username'],
        "fecha": fecha_colombia,
        "texto": texto_nota
    }
    
    visitas_col.update_one(
        {"_id": ObjectId(tarea_id)},
        {"$push": {"novedades": novedad}}
    )
    return jsonify({"status": "success"})

@app.route('/api/tareas/editar-completo', methods=['POST'])
def editar_completo_tarea():
    if session.get('rol') != 'admin':
        return "No autorizado", 403
        
    data = request.json
    tarea_id = data.get('id')
    desc = data.get('descripcion')
    grupo = data.get('grupo_asignado')
    persona = data.get('persona_asignada')
    fecha = data.get('fecha')

    if tarea_id:
        visitas_col.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {
                "descripcion": desc,
                "grupo_asignado": grupo,
                "persona_asignada": persona,
                "fecha_entrega": fecha
            }}
        )
    return jsonify({"status": "success"})

@app.route('/api/tareas/eliminar/<id>', methods=['DELETE'])
def eliminar_tarea(id):
    if session.get('rol') != 'admin':
        return "No autorizado", 403
        
    visitas_col.delete_one({"_id": ObjectId(id)})
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
