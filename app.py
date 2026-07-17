import os
import json
from datetime import datetime
import pytz  # Para manejar con precisión la hora de Colombia
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId, json_util

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nestle_liquid_secret_2026")

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['Tareas']
usuarios_col = db['Usuarios']
grupos_col = db['Grupos']

# Zona horaria de Colombia
CO_TZ = pytz.timezone('America/Bogota')

# --- PLANTILLA DEL LOGIN (Liquid Glass Style) ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Iniciar Sesión - Nestlé Liquid</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at 10% 20%, rgba(0, 149, 218, 0.15) 0%, rgba(0, 0, 0, 0) 40%),
                        radial-gradient(circle at 90% 80%, rgba(251, 146, 60, 0.1) 0%, rgba(0, 0, 0, 0) 50%),
                        #0f172a;
        }
        .liquid-glass {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="liquid-glass p-8 md:p-10 rounded-3xl w-full max-w-md text-white">
        <div class="flex flex-col items-center mb-8">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
                <span class="text-2xl font-extrabold tracking-wider">N</span>
            </div>
            <h2 class="text-2xl font-extrabold tracking-tight">Nestlé Workspace</h2>
            <p class="text-xs text-slate-400 mt-1.5">Diseño Liquid Glass • Workspace Profesional</p>
        </div>
        
        {% if error %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-300 p-3.5 rounded-2xl text-xs mb-5 flex items-center space-x-2">
                <i class="fa-solid fa-circle-exclamation text-red-400"></i>
                <span>{{ error }}</span>
            </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Usuario</label>
                <input type="text" name="username" required placeholder="Tu usuario" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Contraseña</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-blue-500/10 text-xs uppercase tracking-wider mt-2">
                Entrar al Portal
            </button>
        </form>
    </div>
</body>
</html>
"""

# --- PLANTILLA PRINCIPAL (HTML Liquid Glass) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nestlé Liquid Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at 0% 0%, rgba(30, 64, 175, 0.12) 0%, rgba(0, 0, 0, 0) 45%),
                        radial-gradient(circle at 100% 100%, rgba(249, 115, 22, 0.08) 0%, rgba(0, 0, 0, 0) 50%),
                        #0b0f19;
        }
        .liquid-glass-panel {
            background: rgba(255, 255, 255, 0.015);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .liquid-glass-card {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid rgba(255, 255, 255, 0.04);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .liquid-glass-card:hover {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.09);
        }
        .custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
    </style>
</head>
<body class="text-slate-100 h-screen overflow-hidden flex p-4 md:p-6 gap-6">

    <!-- BARRA LATERAL (SIDEBAR) -->
    <aside class="w-64 liquid-glass-panel rounded-3xl flex flex-col justify-between h-full flex-shrink-0 overflow-hidden">
        <div>
            <!-- Perfil / Logo -->
            <div class="p-6 border-b border-white/5 flex items-center space-x-3">
                <img id="myAvatar" src="{{ current_user_avatar }}" class="w-10 h-10 rounded-xl object-cover border border-white/10" alt="Mi Foto">
                <div class="truncate">
                    <h1 class="font-bold text-sm tracking-tight text-white">{{ username }}</h1>
                    <span class="text-[9px] font-bold text-blue-400 uppercase tracking-widest">{{ user_role }}</span>
                </div>
            </div>

            <!-- Navegación -->
            <div class="p-4 space-y-1">
                <div class="text-[9px] font-bold text-slate-500 uppercase px-3 mb-2 tracking-wider">Módulos</div>
                <button onclick="switchTab('tareasTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold bg-white/5 text-white transition-all">
                    <i class="fa-solid fa-layer-group text-blue-400"></i>
                    <span>Bandeja de Tareas</span>
                </button>
                <button onclick="switchTab('gruposTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-all">
                    <i class="fa-solid fa-users text-purple-400"></i>
                    <span>Ver Grupos y Miembros</span>
                </button>
                {% if user_role == 'admin' %}
                <button onclick="switchTab('adminTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-all">
                    <i class="fa-solid fa-user-gear text-orange-400"></i>
                    <span>Administración de Personal</span>
                </button>
                {% endif %}
                <button onclick="switchTab('perfilTab')" class="tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-all">
                    <i class="fa-solid fa-user-astronaut text-green-400"></i>
                    <span>Mi Perfil (Foto)</span>
                </button>
            </div>
        </div>

        <div class="p-4 border-t border-white/5">
            <a href="/logout" class="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-300 font-bold text-xs transition-colors border border-red-500/10">
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
                    <h2 class="text-2xl font-extrabold text-white tracking-tight">Mis Tareas Colaborativas</h2>
                    <p class="text-xs text-slate-400">Gestión de actividades de grupos e individuales</p>
                </div>
                
                <!-- Filtros Liquid Glass -->
                <div class="flex items-center gap-3">
                    <select id="filtroGrupo" onchange="applyFilters()" class="text-xs font-semibold text-slate-300 bg-white/5 border border-white/10 rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500">
                        <option value="" class="bg-slate-900">Todos los Grupos / Individual</option>
                        <option value="individual" class="bg-slate-900">Solo Individuales (Sin Grupo)</option>
                        {% for g in lista_grupos %}
                            <option value="{{ g.nombre }}" class="bg-slate-900">{{ g.nombre }}</option>
                        {% endfor %}
                    </select>
                    <select id="estadoFilter" onchange="applyFilters()" class="text-xs font-semibold text-slate-300 bg-white/5 border border-white/10 rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500">
                        <option value="" class="bg-slate-900">Cualquier Estado</option>
                        <option value="pendiente" class="bg-slate-900">Pendientes</option>
                        <option value="completado" class="bg-slate-900">Completadas</option>
                    </select>
                    <input type="text" id="searchQuery" oninput="applyFilters()" placeholder="Buscar tarea..." class="text-xs text-white placeholder-slate-500 bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 w-44">
                </div>
            </header>

            <div class="flex-grow flex overflow-hidden gap-6">
                <!-- Listado de Tareas -->
                <div class="flex-grow overflow-y-auto custom-scrollbar space-y-4 pr-1">
                    
                    {% if user_role == 'admin' %}
                    <!-- ACCIÓN ADMIN: Crear Tarea -->
                    <div class="liquid-glass-panel rounded-2xl p-5 mb-4">
                        <h3 class="text-xs font-bold text-blue-400 uppercase tracking-widest mb-4"><i class="fa-solid fa-circle-plus mr-2"></i>Nueva Tarea</h3>
                        <form action="/admin/crear-tarea" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <input type="text" name="descripcion" required placeholder="Descripción de la tarea..." class="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none">
                            <select name="asignado_tipo_id" required class="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-300 focus:outline-none">
                                <option value="" class="bg-slate-900 text-slate-400">Asignar a...</option>
                                <optgroup label="Colaboradores Individuales" class="bg-slate-900 text-white">
                                    {% for u in lista_usuarios %}
                                        <option value="user:{{ u.username }}">{{ u.username }}</option>
                                    {% endfor %}
                                </optgroup>
                                <optgroup label="Grupos" class="bg-slate-900 text-white">
                                    {% for g in lista_grupos %}
                                        <option value="group:{{ g.nombre }}">{{ g.nombre }}</option>
                                    {% endfor %}
                                </optgroup>
                            </select>
                            <div class="flex gap-2">
                                <input type="date" name="fecha_entrega" required class="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-300 focus:outline-none flex-grow">
                                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 rounded-xl text-xs transition-colors">Asignar</button>
                            </div>
                        </form>
                    </div>
                    {% endif %}

                    <!-- Tabla de Tareas Estilo Liquid -->
                    <div class="liquid-glass-panel rounded-2xl overflow-hidden">
                        <table class="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr class="border-b border-white/5 bg-white/2 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                    <th class="py-3.5 px-6 w-12 text-center">Check</th>
                                    <th class="py-3.5 px-6">Descripción</th>
                                    <th class="py-3.5 px-6">Origen de Asignación</th>
                                    <th class="py-3.5 px-6">Fecha de Entrega</th>
                                    <th class="py-3.5 px-6">Novedades</th>
                                    <th class="py-3.5 px-6 text-right">Detalle</th>
                                </tr>
                            </thead>
                            <tbody id="tareasTableBody" class="divide-y divide-white/5">
                                <!-- Cargado dinámicamente -->
                            </tbody>
                        </table>
                    </div>

                </div>

                <!-- PANEL DETALLE LATERAL (Slide-out de Asana) -->
                <div id="asanaDetailPanel" class="w-96 liquid-glass-panel rounded-2xl h-full flex flex-col justify-between hidden flex-shrink-0">
                    <div class="p-6 space-y-5 overflow-y-auto custom-scrollbar flex-grow">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Actividad Detallada</span>
                            <button onclick="closeDetailPanel()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-times"></i></button>
                        </div>

                        <!-- Edición de Tarea (Solo Admin) -->
                        <div id="editTaskSection" class="hidden space-y-3 bg-white/5 p-4 rounded-xl border border-white/5">
                            <span class="text-[10px] font-bold text-orange-400 uppercase tracking-widest">Editar Tarea (Admin)</span>
                            <input type="text" id="editDescripcion" class="w-full bg-slate-900 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white">
                            <div class="grid grid-cols-2 gap-2">
                                <input type="date" id="editFecha" class="bg-slate-900 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
                                <select id="editAsignado" class="bg-slate-900 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
                                    {% for u in lista_usuarios %}
                                        <option value="user:{{ u.username }}">Individual: {{ u.username }}</option>
                                    {% endfor %}
                                    {% for g in lista_grupos %}
                                        <option value="group:{{ g.nombre }}">Grupo: {{ g.nombre }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <button onclick="guardarEdicionTarea()" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-1.5 rounded-lg text-xs transition-colors">Actualizar Tarea</button>
                        </div>

                        <!-- Info de solo lectura -->
                        <div id="readTaskSection" class="space-y-3">
                            <h3 id="detailTitle" class="text-sm font-bold text-white"></h3>
                            <div class="flex gap-4 text-xs text-slate-400">
                                <div><span class="font-semibold text-slate-200">Asignado:</span> <span id="detailAsignado">-</span></div>
                                <div><span class="font-semibold text-slate-200">Entrega:</span> <span id="detailFechaText">-</span></div>
                            </div>
                        </div>

                        <hr class="border-white/5">

                        <!-- Conversaciones / Comentarios -->
                        <div class="space-y-3">
                            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center">
                                <i class="fa-regular fa-comment-dots mr-2 text-blue-400"></i> Novedades (Hora Col)
                            </h4>
                            <div class="space-y-2">
                                <textarea id="nuevaNotaInput" placeholder="Añadir una nota o novedad..." rows="2" class="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"></textarea>
                                <button onclick="guardarNovedad()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-1.5 rounded-lg text-xs transition-colors">Enviar Nota</button>
                            </div>

                            <div id="notasContainer" class="space-y-2 max-h-56 overflow-y-auto custom-scrollbar">
                                <!-- Inyección -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ================= TAB: GRUPOS ================= -->
        <div id="gruposTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-6">
                <h2 class="text-2xl font-extrabold text-white tracking-tight">Grupos de Trabajo</h2>
                <p class="text-xs text-slate-400">Detalles de las agrupaciones y sus integrantes en el sistema</p>
            </header>

            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {% for g in lista_grupos %}
                    <div class="liquid-glass-panel rounded-2xl p-6 space-y-4">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-sm text-white flex items-center"><i class="fa-solid fa-folder-open mr-2 text-purple-400"></i>{{ g.nombre }}</span>
                            <span class="text-[10px] bg-purple-500/10 border border-purple-500/20 text-purple-300 px-2.5 py-0.5 rounded-full font-mono">{{ g.miembros|length }} Miembros</span>
                        </div>
                        
                        <!-- Lista de Integrantes de este Grupo -->
                        <div class="space-y-2 pt-2 border-t border-white/5 max-h-48 overflow-y-auto custom-scrollbar">
                            {% for m in g.miembros %}
                                <div class="flex items-center justify-between text-xs py-1 px-2 hover:bg-white/2 rounded-lg">
                                    <span class="text-slate-300"><i class="fa-regular fa-user mr-2 text-slate-500"></i>{{ m }}</span>
                                    {% if user_role == 'admin' %}
                                    <button onclick="quitarDeGrupo('{{ g._id }}', '{{ m }}')" class="text-red-400 hover:text-red-600 font-bold" title="Remover del grupo">Quitar</button>
                                    {% endif %}
                                </div>
                            {% else %}
                                <span class="text-xs text-slate-500 italic block">No hay miembros en este grupo.</span>
                            {% endfor %}
                        </div>

                        {% if user_role == 'admin' %}
                        <!-- Añadir miembro rápido -->
                        <form action="/admin/agregar-miembro-grupo" method="POST" class="pt-2 border-t border-white/5 flex gap-2">
                            <input type="hidden" name="grupo_id" value="{{ g._id }}">
                            <select name="miembro_nuevo" required class="bg-white/5 border border-white/10 rounded-xl px-2 py-1.5 text-xs text-slate-300 focus:outline-none flex-grow">
                                <option value="" class="bg-slate-900 text-slate-400">Añadir usuario...</option>
                                {% for u in lista_usuarios %}
                                    {% if u.username not in g.miembros %}
                                        <option value="{{ u.username }}" class="bg-slate-900">{{ u.username }}</option>
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

        <!-- ================= TAB: ADMIN (PERSONAL) ================= -->
        {% if user_role == 'admin' %}
        <div id="adminTab" class="tab-content flex-grow flex flex-col h-full overflow-hidden hidden">
            <header class="mb-6">
                <h2 class="text-2xl font-extrabold text-white tracking-tight">Administración de Personal</h2>
                <p class="text-xs text-slate-400">Modifica, deshabilita y administra accesos de usuarios</p>
            </header>

            <div class="flex-grow overflow-y-auto custom-scrollbar space-y-6">
                <div class="liquid-glass-panel rounded-2xl overflow-hidden">
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="border-b border-white/5 bg-white/2 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                <th class="py-3.5 px-6">Foto</th>
                                <th class="py-3.5 px-6">Usuario</th>
                                <th class="py-3.5 px-6">Rol</th>
                                <th class="py-3.5 px-6">Grupo Principal</th>
                                <th class="py-3.5 px-6">Estado</th>
                                <th class="py-3.5 px-6 text-right">Acciones de Control</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5">
                            {% for u in lista_usuarios_completa %}
                            <tr class="hover:bg-white/1 transition-colors">
                                <td class="py-3 px-6">
                                    <img src="{{ u.avatar or 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&h=100&q=80' }}" class="w-8 h-8 rounded-lg object-cover border border-white/10" alt="Foto">
                                </td>
                                <td class="py-3 px-6 font-semibold text-white">{{ u.username }}</td>
                                <td class="py-3 px-6 capitalize text-slate-400">{{ u.rol }}</td>
                                <td class="py-3 px-6">
                                    <span class="text-slate-300 font-mono">{{ u.grupo_nombre or 'Persona Sola' }}</span>
                                </td>
                                <td class="py-3 px-6">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold {{ 'bg-green-500/10 text-green-400 border border-green-500/10' if u.activo != False else 'bg-red-500/10 text-red-400 border border-red-500/10' }}">
                                        {{ 'Activo' if u.activo != False else 'Inhabilitado' }}
                                    </span>
                                </td>
                                <td class="py-3 px-6 text-right space-x-2">
                                    <button onclick="openEditUserModal('{{ u._id }}', '{{ u.username }}', '{{ u.rol }}', '{{ u.grupo }}', '{{ u.activo }}')" class="bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg transition-all">Editar / Reset</button>
                                    <button onclick="toggleInhabilitarUser('{{ u._id }}', {{ 'true' if u.activo != False else 'false' }})" class="{{ 'text-red-400 hover:text-red-500' if u.activo != False else 'text-green-400 hover:text-green-500' }} font-bold">
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
                <h2 class="text-2xl font-extrabold text-white tracking-tight">Mi Perfil</h2>
                <p class="text-xs text-slate-400">Actualiza tu información y tu foto de perfil de colaboración</p>
            </header>

            <div class="max-w-md bg-white/5 border border-white/10 p-6 rounded-2xl shadow-xl space-y-6">
                <div class="flex items-center space-x-4">
                    <img id="profilePreview" src="{{ current_user_avatar }}" class="w-20 h-20 rounded-2xl object-cover border border-white/20 shadow-lg" alt="Foto">
                    <div>
                        <h3 class="font-bold text-base text-white">{{ username }}</h3>
                        <p class="text-xs text-slate-400">Rol: {{ user_role }}</p>
                    </div>
                </div>

                <form action="/perfil/actualizar-avatar" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Enlace URL de tu foto de perfil</label>
                        <input type="url" name="avatar_url" required value="{{ current_user_avatar }}" class="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500">
                    </div>
                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition-colors">Guardar Avatar</button>
                </form>
            </div>
        </div>

    </main>

    <!-- MODAL PARA EDITAR USUARIO / RESETEAR PASSWORD (SOLO ADMIN) -->
    <div id="editUserModal" class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center p-4 hidden z-50">
        <div class="liquid-glass p-8 rounded-3xl w-full max-w-md text-white border border-white/10">
            <div class="flex justify-between items-center mb-6">
                <h3 class="font-bold text-base">Modificar Colaborador</h3>
                <button onclick="closeEditUserModal()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-times"></i></button>
            </div>
            
            <form action="/admin/editar-colaborador" method="POST" class="space-y-4">
                <input type="hidden" id="editUserId" name="user_id">
                
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nombre de Usuario</label>
                    <input type="text" id="editUsernameInput" name="username" readonly class="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-xs text-slate-400 focus:outline-none">
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nueva Contraseña (Dejar en blanco si no cambia)</label>
                    <input type="password" name="password" placeholder="Establecer nueva clave" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-white focus:outline-none">
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Rol de Sistema</label>
                    <select id="editUserRol" name="rol" class="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none">
                        <option value="user">Colaborador</option>
                        <option value="admin">Administrador</option>
                    </select>
                </div>

                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Grupo Principal</label>
                    <select id="editUserGrupo" name="grupo_id" class="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none">
                        <option value="">Ninguno (Persona Sola)</option>
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

        // Cambiar pestañas laterales
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
            document.getElementById(tabId).classList.remove('hidden');

            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-white/5', 'text-white');
                btn.classList.add('text-slate-400');
            });
            event.currentTarget.classList.add('bg-white/5', 'text-white');
            event.currentTarget.classList.remove('text-slate-400');
        }

        // Cargar Tareas
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
                            <td colspan="6" class="text-center py-8 text-slate-500 italic">
                                No se encontraron tareas.
                            </td>
                        </tr>`;
                    return;
                }

                data.forEach(tarea => {
                    const mongoId = tarea._id?.$oid || tarea._id || '';
                    const isCompleted = tarea.estado === 'completado';
                    const nNovedades = tarea.novedades ? tarea.novedades.length : 0;
                    
                    // Identificación de origen visualmente claro para el usuario
                    let badgeOrigen = '';
                    if (tarea.tipo_asignacion === 'group') {
                        badgeOrigen = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/10"><i class="fa-solid fa-users mr-1"></i>${tarea.asignado_a}</span>`;
                    } else {
                        badgeOrigen = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-500/10 text-slate-300 border border-slate-500/10"><i class="fa-solid fa-user mr-1"></i>Individual</span>`;
                    }

                    tbody.innerHTML += `
                        <tr class="hover:bg-white/2 transition-colors cursor-pointer" onclick="openDetailPanel('${mongoId}')">
                            <td class="py-3 px-6 text-center" onclick="event.stopPropagation()">
                                <button onclick="toggleCompletado('${mongoId}', '${tarea.estado}')" class="w-5 h-5 rounded-full border-2 ${isCompleted ? 'border-green-500 bg-green-500 text-white' : 'border-slate-600 hover:border-blue-500'} flex items-center justify-center transition-all">
                                    ${isCompleted ? '<i class="fa-solid fa-check text-[10px]"></i>' : ''}
                                </button>
                            </td>
                            <td class="py-3 px-6 font-semibold text-slate-200 ${isCompleted ? 'line-through text-slate-500' : ''}">
                                ${tarea.descripcion}
                            </td>
                            <td class="py-3 px-6">
                                ${badgeOrigen}
                            </td>
                            <td class="py-3 px-6">
                                <span class="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-red-500/10 text-red-300 border border-red-500/10">
                                    <i class="fa-regular fa-calendar mr-1"></i>${tarea.fecha_entrega}
                                </span>
                            </td>
                            <td class="py-3 px-6 text-slate-400">
                                <i class="fa-regular fa-comment-dots mr-1 text-slate-500"></i>${nNovedades} notas
                            </td>
                            <td class="py-3 px-6 text-right" onclick="event.stopPropagation()">
                                <button onclick="openDetailPanel('${mongoId}')" class="text-blue-400 hover:text-blue-300 font-bold">Ver</button>
                            </td>
                        </tr>
                    `;
                });

            } catch (error) {
                console.error("Error cargando tareas", error);
            }
        }

        async function openDetailPanel(id) {
            activeTaskId = id;
            document.getElementById('asanaDetailPanel').classList.remove('hidden');

            try {
                const response = await fetch(`/api/tareas/detalle/${id}`);
                const tarea = await response.json();

                document.getElementById('detailTitle').textContent = tarea.descripcion;
                document.getElementById('detailAsignado').textContent = `${tarea.asignado_a} (${tarea.tipo_asignacion})`;
                document.getElementById('detailFechaText').textContent = tarea.fecha_entrega;

                // Si eres admin, puedes ver y usar el panel de edición directa
                {% if user_role == 'admin' %}
                    document.getElementById('editTaskSection').classList.remove('hidden');
                    document.getElementById('editDescripcion').value = tarea.descripcion;
                    document.getElementById('editFecha').value = tarea.fecha_entrega;
                    document.getElementById('editAsignado').value = `${tarea.tipo_asignacion}:${tarea.asignado_a}`;
                {% endif %}

                // Novedades
                const container = document.getElementById('notasContainer');
                container.innerHTML = '';
                if(tarea.novedades && tarea.novedades.length > 0) {
                    tarea.novedades.forEach(n => {
                        container.innerHTML += `
                            <div class="bg-white/2 border border-white/5 rounded-xl p-3 space-y-1">
                                <div class="flex justify-between items-center text-[9px] text-slate-500">
                                    <span class="font-bold text-slate-300">${n.autor}</span>
                                    <span>${n.fecha} (Col)</span>
                                </div>
                                <p class="text-xs text-slate-300 leading-relaxed">${n.texto}</p>
                            </div>
                        `;
                    });
                } else {
                    container.innerHTML = '<span class="text-[10px] text-slate-500 italic block text-center py-4">Sin novedades aún.</span>';
                }

            } catch (e) {
                console.error("Error cargando detalle", e);
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
            const fec = document.getElementById('editFecha').value;
            const asig = document.getElementById('editAsignado').value;

            const res = await fetch(`/api/tareas/editar-completo`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: activeTaskId, descripcion: desc, fecha: fec, asignado: asig})
            });

            if(res.ok) {
                openDetailPanel(activeTaskId);
                loadTareas();
            }
        }

        // Filtros rápidos
        function applyFilters() {
            loadTareas({
                grupo: document.getElementById('filtroGrupo').value,
                estado: document.getElementById('estadoFilter').value,
                q: document.getElementById('searchQuery').value
            });
        }

        // Modales de Usuario
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
            const m = actualActivo ? '¿Estás seguro de inhabilitar este usuario? No podrá iniciar sesión.' : '¿Deseas reactivar al usuario?';
            if(confirm(m)) {
                window.location.href = `/admin/cambiar-estado-usuario/${id}/${!actualActivo}`;
            }
        }

        async function quitarDeGrupo(grupoId, username) {
            if(confirm(`¿Quieres retirar a ${username} de este grupo?`)) {
                window.location.href = `/admin/quitar-miembro-grupo/${grupoId}/${username}`;
            }
        }

        document.addEventListener('DOMContentLoaded', () => loadTareas());
    </script>
</body>
</html>
"""

# --- INICIALIZAR ELEMENTOS BASE ---
def inicializar_sistema():
    if usuarios_col.count_documents({}) == 0:
        usuarios_col.insert_one({
            "username": "admin",
            "password": "123",
            "rol": "admin",
            "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
            "activo": True
        })

# --- CONTROLADORES Y SESIONES (FLASK) ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    lista_usuarios = list(usuarios_col.find({"rol": "user"}, {"password": 0}))
    lista_grupos = list(grupos_col.find({}))
    
    # Datos completos de usuarios con información del grupo para el panel del admin
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

# --- ACCIONES DE PERFIL ---

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

# --- ACCIONES ADMINISTRATIVAS ---

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

@app.route('/admin/crear-usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    username = request.form.get('nuevo_usuario')
    password = request.form.get('password')
    rol = request.form.get('rol', 'user')
    grupo_id = request.form.get('grupo_id')

    if username and password:
        usuarios_col.update_one(
            {"username": username},
            {"$set": {
                "password": password, 
                "rol": rol, 
                "grupo": grupo_id,
                "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
                "activo": True
            }},
            upsert=True
        )
        if grupo_id:
            grupos_col.update_one(
                {"_id": ObjectId(grupo_id)},
                {"$addToSet": {"miembros": username}}
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
        
        # Sincronizar el miembro en el grupo si aplica
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

@app.route('/admin/crear-tarea', methods=['POST'])
def crear_tarea():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    descripcion = request.form.get('descripcion')
    asignado_tipo_id = request.form.get('asignado_tipo_id')
    fecha_entrega = request.form.get('fecha_entrega')

    if descripcion and asignado_tipo_id:
        tipo, valor = asignado_tipo_id.split(':', 1)
        visitas_col.insert_one({
            "descripcion": descripcion,
            "asignado_a": valor,
            "tipo_asignacion": tipo,
            "fecha_entrega": fecha_entrega,
            "estado": "pendiente",
            "novedades": []
        })
        
    return redirect(url_for('index'))

# --- API ENDPOINTS (RESPUESTAS AJAX) ---

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    if 'username' not in session:
        return jsonify([]), 401
        
    query = {}
    username = session['username']
    
    # Filtrado base por Roles
    if session.get('rol') != 'admin':
        mis_grupos_docs = list(grupos_col.find({"miembros": username}))
        mis_grupos_nombres = [g['nombre'] for g in mis_grupos_docs]
        
        query['$or'] = [
            {"asignado_a": username, "tipo_asignacion": "user"},
            {"asignado_a": {"$in": mis_grupos_nombres}, "tipo_asignacion": "group"}
        ]
        
    # Filtro específico de origen de grupo (Individual o Nombre del Grupo)
    grupo_filtro = request.args.get('grupo')
    if grupo_filtro:
        if grupo_filtro == 'individual':
            query['tipo_asignacion'] = 'user'
            if session.get('rol') != 'admin':
                query['asignado_a'] = username
        else:
            query['asignado_a'] = grupo_filtro
            query['tipo_asignacion'] = 'group'

    # Filtros de búsqueda y estado
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
    
    # Hora de Colombia precisa
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
    fecha = data.get('fecha')
    asig_raw = data.get('asignado') # Formato 'tipo:valor'

    if tarea_id and desc and asig_raw:
        tipo, valor = asig_raw.split(':', 1)
        visitas_col.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {
                "descripcion": desc,
                "fecha_entrega": fecha,
                "asignado_a": valor,
                "tipo_asignacion": tipo
            }}
        )
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
