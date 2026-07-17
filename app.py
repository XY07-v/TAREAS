import os
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId, json_util

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nestle_secret_key_2026")

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['Tareas']
usuarios_col = db['Usuarios']
grupos_col = db['Grupos']  # Nueva colección para los grupos de trabajo

# --- PLANTILLA DEL LOGIN (Estilo Asana Clean) ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Iniciar Sesión - Nestlé Asana</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-50 flex items-center justify-center min-h-screen">
    <div class="bg-white p-10 rounded-2xl shadow-xl border border-gray-100 w-full max-w-md">
        <div class="flex flex-col items-center mb-8">
            <div class="bg-blue-600 text-white p-3 rounded-2xl mb-4 shadow-md shadow-blue-200">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>
            </div>
            <h2 class="text-2xl font-bold text-slate-800">Te damos la bienvenida</h2>
            <p class="text-sm text-gray-500 mt-1">Ingresa a tu espacio de trabajo en Nestlé</p>
        </div>
        
        {% if error %}
            <div class="bg-red-50 text-red-600 p-3 rounded-xl text-xs mb-4 border border-red-100 flex items-center space-x-2">
                <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>
                <span>{{ error }}</span>
            </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Nombre de Usuario</label>
                <input type="text" name="username" required placeholder="nombre.apellido" class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all">
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Contraseña</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all">
            </div>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-all shadow-lg shadow-blue-100 text-sm">
                Iniciar sesión
            </button>
        </form>
    </div>
</body>
</html>
"""

# --- PLANTILLA PRINCIPAL DE ASANA (HTML + TAILWIND) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nestlé Home - Asana Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
</head>
<body class="bg-white text-slate-800 antialiased h-screen overflow-hidden flex">

    <!-- 1. BARRA LATERAL (Asana Sidebar) -->
    <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between border-r border-slate-800 h-full flex-shrink-0">
        <div>
            <!-- Header Sidebar -->
            <div class="p-5 flex items-center justify-between border-b border-slate-800">
                <div class="flex items-center space-x-2.5">
                    <div class="bg-blue-600 text-white font-bold p-1.5 rounded-lg text-sm">N</div>
                    <span class="font-bold text-white text-sm tracking-wide">Nestlé Workspace</span>
                </div>
                <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">v2.0</span>
            </div>

            <!-- Menú Navegación -->
            <div class="p-4 space-y-1">
                <div class="text-[10px] font-bold text-slate-500 uppercase px-3 mb-2">Mi Espacio</div>
                <a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium transition-all">
                    <i class="fa-solid fa-rectangle-list"></i>
                    <span>Mis Tareas</span>
                </a>
            </div>

            <!-- Gestión de Grupos e Integrantes (Solo para Admins) -->
            {% if user_role == 'admin' %}
            <div class="px-4 py-2 border-t border-slate-800 mt-4 space-y-4">
                <div class="text-[10px] font-bold text-slate-500 uppercase px-3">Estructura Nestlé</div>
                
                <!-- Grupos Activos -->
                <div class="space-y-1 max-h-48 overflow-y-auto custom-scrollbar">
                    <span class="text-xs text-slate-400 px-3 block font-semibold">Grupos:</span>
                    {% for g in lista_grupos %}
                        <div class="flex items-center justify-between px-3 py-1 text-xs hover:bg-slate-800 rounded transition-colors text-slate-300">
                            <span><i class="fa-solid fa-users mr-1.5 text-blue-400"></i>{{ g.nombre }}</span>
                            <span class="text-[10px] text-slate-500">({{ g.miembros|length }} p.)</span>
                        </div>
                    {% else %}
                        <span class="text-[10px] text-slate-500 px-3 block italic">No hay grupos creados</span>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Usuario Logueado / Logout -->
        <div class="p-4 border-t border-slate-800 flex items-center justify-between text-sm">
            <div class="flex items-center space-x-3 truncate">
                <div class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-xs uppercase">
                    {{ username[:2] }}
                </div>
                <div class="truncate">
                    <div class="font-medium text-white truncate text-xs">{{ username }}</div>
                    <div class="text-[10px] text-slate-400 capitalize font-mono">{{ user_role }}</div>
                </div>
            </div>
            <a href="/logout" class="text-slate-400 hover:text-red-400 transition-colors p-1.5" title="Cerrar sesión">
                <i class="fa-solid fa-power-off"></i>
            </a>
        </div>
    </aside>

    <!-- 2. CONTENEDOR DE CONTENIDO (Header + Tablas) -->
    <main class="flex-grow flex flex-col h-full overflow-hidden bg-white">
        
        <!-- Header superior -->
        <header class="h-16 border-b border-gray-100 px-8 flex justify-between items-center flex-shrink-0">
            <div>
                <h2 class="text-lg font-bold text-slate-800 flex items-center">
                    <span class="mr-2">Mis Tareas</span>
                    <span class="text-xs font-normal text-slate-400 border border-slate-200 px-2 py-0.5 rounded-full">Lista</span>
                </h2>
            </div>
            <div class="flex items-center space-x-3">
                <!-- Filtros rápidos de Asana -->
                <select id="estadoFilter" onchange="applyFilters()" class="text-xs font-medium text-slate-500 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none transition-all">
                    <option value="">Todo el estado</option>
                    <option value="pendiente">Pendientes</option>
                    <option value="completado">Completados</option>
                </select>
                <input type="text" id="searchQuery" oninput="applyFilters()" placeholder="Buscar tarea..." class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white w-48 transition-all">
            </div>
        </header>

        <!-- Contenedor central (Grid modular) -->
        <div class="flex-grow flex overflow-hidden">
            <!-- Sección Izquierda: Formularios y Listas -->
            <div class="flex-grow p-8 overflow-y-auto custom-scrollbar space-y-6">
                
                {% if user_role == 'admin' %}
                <!-- MÓDULOS DE ADMINISTRADOR (Creación de Grupos, Usuarios y Tareas) -->
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    
                    <!-- 1. Crear Grupos -->
                    <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm space-y-4">
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center">
                            <i class="fa-solid fa-users-rectangle text-blue-500 mr-2"></i> Crear Grupo de Trabajo
                        </h3>
                        <form action="/admin/crear-grupo" method="POST" class="space-y-3">
                            <input type="text" name="nombre_grupo" required placeholder="Ej: Equipo Ventas Bogotá" class="w-full bg-slate-50 border border-gray-100 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white">
                            <button type="submit" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-2 rounded-xl text-xs transition-colors">
                                Guardar Grupo
                            </button>
                        </form>
                    </div>

                    <!-- 2. Crear Usuarios / Añadir a Grupo o Personas Solas -->
                    <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm space-y-4">
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center">
                            <i class="fa-solid fa-user-plus text-blue-500 mr-2"></i> Registrar Integrante
                        </h3>
                        <form action="/admin/crear-usuario" method="POST" class="space-y-3">
                            <div class="grid grid-cols-2 gap-2">
                                <input type="text" name="nuevo_usuario" required placeholder="Usuario" class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                                <input type="password" name="password" required placeholder="Clave" class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <select name="rol" class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                                    <option value="user">Colaborador</option>
                                    <option value="admin">Administrador</option>
                                </select>
                                <select name="grupo_id" class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                                    <option value="">Persona Sola (Sin Grupo)</option>
                                    {% for g in lista_grupos %}
                                        <option value="{{ g._id }}">{{ g.nombre }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <button type="submit" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-2 rounded-xl text-xs transition-colors">
                                Registrar Usuario
                            </button>
                        </form>
                    </div>

                    <!-- 3. Crear y Asignar Tarea (A Grupo o Persona Sola) -->
                    <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm space-y-4">
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center">
                            <i class="fa-solid fa-circle-plus text-blue-500 mr-2"></i> Crear y Asignar Tarea
                        </h3>
                        <form action="/admin/crear-tarea" method="POST" class="space-y-3">
                            <input type="text" name="descripcion" required placeholder="¿Qué tarea deseas asignar?" class="w-full bg-slate-50 border border-gray-100 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white">
                            
                            <div class="grid grid-cols-2 gap-2">
                                <select name="asignado_tipo_id" required class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                                    <option value="">Asignar a...</option>
                                    <!-- Personas Solas / Todos los Usuarios -->
                                    <optgroup label="Colaboradores Individuales">
                                        {% for u in lista_usuarios %}
                                            <option value="user:{{ u.username }}">{{ u.username }}</option>
                                        {% endfor %}
                                    </optgroup>
                                    <!-- Grupos -->
                                    <optgroup label="Grupos de Trabajo">
                                        {% for g in lista_grupos %}
                                            <option value="group:{{ g.nombre }}">{{ g.nombre }}</option>
                                        {% endfor %}
                                    </optgroup>
                                </select>
                                <input type="date" name="fecha_entrega" required class="bg-slate-50 border border-gray-100 rounded-xl px-3 py-2 text-xs text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-xl text-xs transition-colors shadow-sm">
                                Asignar Tarea
                            </button>
                        </form>
                    </div>

                </div>
                {% endif %}

                <!-- TABLA DE LISTADO DE TAREAS ESTILO ASANA -->
                <div class="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse min-w-[600px]">
                            <thead>
                                <tr class="border-b border-gray-100 bg-slate-50 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                    <th class="py-3 px-6 w-12 text-center">Check</th>
                                    <th class="py-3 px-6">Nombre de la Tarea</th>
                                    <th class="py-3 px-6">Asignado a</th>
                                    <th class="py-3 px-6">Fecha de Entrega</th>
                                    <th class="py-3 px-6">Novedades</th>
                                    {% if user_role == 'admin' %}
                                    <th class="py-3 px-6 text-right">Acciones</th>
                                    {% endif %}
                                </tr>
                            </thead>
                            <tbody id="tareasTableBody" class="divide-y divide-gray-100 text-xs text-slate-700">
                                <!-- Datos inyectados de JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

            <!-- Panel Lateral Derecho de Detalle (Modal/Slide-out de Asana) -->
            <div id="asanaDetailPanel" class="w-96 border-l border-gray-100 bg-slate-50 h-full flex flex-col justify-between hidden flex-shrink-0">
                <!-- Contenido Detalle -->
                <div class="p-6 space-y-6 overflow-y-auto custom-scrollbar flex-grow">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-bold text-blue-600 uppercase tracking-widest">Detalle de la tarea</span>
                        <button onclick="closeDetailPanel()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-times text-sm"></i></button>
                    </div>

                    <div>
                        <h3 id="detailTitle" class="text-base font-bold text-slate-800">Cargando...</h3>
                    </div>

                    <!-- Datos rápidos -->
                    <div class="space-y-3 text-xs">
                        <div class="flex items-center text-slate-500">
                            <span class="w-24 font-medium">Asignado:</span>
                            <span id="detailAsignado" class="text-slate-800 font-semibold">-</span>
                        </div>
                        <div class="flex items-center text-slate-500">
                            <span class="w-24 font-medium">Entrega:</span>
                            <span id="detailFecha" class="text-slate-800 font-semibold">-</span>
                        </div>
                    </div>

                    <hr class="border-gray-200">

                    <!-- Sección de Novedades y Notas -->
                    <div class="space-y-3">
                        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center">
                            <i class="fa-regular fa-comments mr-2 text-blue-500"></i> Novedades / Comentarios
                        </h4>
                        <!-- Caja de texto para agregar notas -->
                        <div class="space-y-2">
                            <textarea id="nuevaNotaInput" placeholder="Añadir una nota o novedad..." rows="3" class="w-full bg-white border border-gray-200 rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"></textarea>
                            <button onclick="guardarNovedad()" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-3 py-1.5 rounded-lg text-xs transition-colors self-end">
                                Publicar Nota
                            </button>
                        </div>

                        <!-- Lista de Notas Agregadas -->
                        <div id="notasContainer" class="space-y-2 pt-2 max-h-56 overflow-y-auto custom-scrollbar">
                            <!-- Inyección dinámica con JS -->
                        </div>
                    </div>
                </div>
            </div>

        </div>

    </main>

    <!-- JS de Front-End -->
    <script>
        let currentTaskId = null;

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
                                No tienes tareas asignadas por el momento.
                            </td>
                        </tr>`;
                    return;
                }

                data.forEach(tarea => {
                    const mongoId = tarea._id?.$oid || tarea._id || '';
                    const isCompleted = tarea.estado === 'completado';
                    const nNovedades = tarea.novedades ? tarea.novedades.length : 0;

                    // Formateo de fecha bonita
                    let fechaBonita = tarea.fecha_entrega || 'Sin fecha';

                    tbody.innerHTML += `
                        <tr class="hover:bg-slate-50/75 transition-colors cursor-pointer" onclick="openDetailPanel('${mongoId}')">
                            <!-- Checkbox de Completado de Asana -->
                            <td class="py-3 px-6 text-center" onclick="event.stopPropagation()">
                                <button onclick="toggleCompletado('${mongoId}', '${tarea.estado}')" class="w-5 h-5 rounded-full border-2 ${isCompleted ? 'border-green-500 bg-green-500 text-white' : 'border-slate-300 hover:border-blue-500'} flex items-center justify-center transition-all">
                                    ${isCompleted ? '<i class="fa-solid fa-check text-[10px]"></i>' : ''}
                                </button>
                            </td>
                            <!-- Nombre/Descripción de la tarea -->
                            <td class="py-3 px-6 font-medium text-slate-800 ${isCompleted ? 'line-through text-slate-400' : ''}">
                                ${tarea.descripcion || 'Sin descripción'}
                            </td>
                            <!-- Asignado (Persona o Grupo) -->
                            <td class="py-3 px-6 text-slate-500 font-semibold">
                                <i class="fa-regular ${tarea.asignado_a.startsWith('Grupo') || tarea.asignado_a.includes('Equipo') ? 'fa-folder-open text-blue-500' : 'fa-user text-slate-400'} mr-1.5"></i>
                                ${tarea.asignado_a}
                            </td>
                            <!-- Fecha de entrega -->
                            <td class="py-3 px-6">
                                <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-red-50 text-red-600 border border-red-100">
                                    <i class="fa-regular fa-calendar-days mr-1"></i>${fechaBonita}
                                </span>
                            </td>
                            <!-- Novedades (Comentarios) -->
                            <td class="py-3 px-6 text-slate-400">
                                <i class="fa-regular fa-comment-dots mr-1"></i>${nNovedades} notas
                            </td>
                            <!-- Acciones de admin -->
                            {% if user_role == 'admin' %}
                            <td class="py-3 px-6 text-right" onclick="event.stopPropagation()">
                                <button onclick="eliminarTarea('${mongoId}')" class="text-slate-300 hover:text-red-500 transition-colors p-1">
                                    <i class="fa-regular fa-trash-can"></i>
                                </button>
                            </td>
                            {% endif %}
                        </tr>
                    `;
                });

            } catch (error) {
                console.error("Error cargando tareas", error);
            }
        }

        async function openDetailPanel(id) {
            currentTaskId = id;
            document.getElementById('asanaDetailPanel').classList.remove('hidden');

            try {
                const response = await fetch(`/api/tareas/detalle/${id}`);
                const tarea = await response.json();

                document.getElementById('detailTitle').textContent = tarea.descripcion;
                document.getElementById('detailAsignado').textContent = tarea.asignado_a;
                document.getElementById('detailFecha').textContent = tarea.fecha_entrega || 'Sin fecha';

                // Mostrar comentarios (Novedades)
                const container = document.getElementById('notasContainer');
                container.innerHTML = '';
                
                if (tarea.novedades && tarea.novedades.length > 0) {
                    tarea.novedades.forEach(n => {
                        container.innerHTML += `
                            <div class="bg-white border border-gray-100 rounded-xl p-3 space-y-1 shadow-2xs">
                                <div class="flex justify-between items-center text-[10px] text-slate-400">
                                    <span class="font-bold text-slate-600">${n.autor}</span>
                                    <span>${n.fecha}</span>
                                </div>
                                <p class="text-xs text-slate-700 leading-relaxed">${n.texto}</p>
                            </div>
                        `;
                    });
                } else {
                    container.innerHTML = '<p class="text-[10px] italic text-slate-400 text-center py-4">No hay novedades reportadas en esta tarea.</p>';
                }

            } catch (e) {
                console.error("Error cargando el detalle", e);
            }
        }

        function closeDetailPanel() {
            document.getElementById('asanaDetailPanel').classList.add('hidden');
            currentTaskId = null;
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
                if (currentTaskId === id) openDetailPanel(id);
            }
        }

        async function guardarNovedad() {
            const txt = document.getElementById('nuevaNotaInput').value.trim();
            if(!txt || !currentTaskId) return;

            const res = await fetch(`/api/tareas/novedad`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: currentTaskId, texto: txt})
            });

            if(res.ok) {
                document.getElementById('nuevaNotaInput').value = '';
                openDetailPanel(currentTaskId);
                loadTareas();
            }
        }

        async function eliminarTarea(id) {
            if(confirm("¿Estás seguro de eliminar esta tarea permanentemente?")) {
                const res = await fetch(`/api/tareas/eliminar/${id}`, { method: 'DELETE' });
                if(res.ok) {
                    closeDetailPanel();
                    loadTareas();
                }
            }
        }

        function applyFilters() {
            loadTareas({
                estado: document.getElementById('estadoFilter').value,
                q: document.getElementById('searchQuery').value
            });
        }

        document.addEventListener('DOMContentLoaded', () => loadTareas());
    </script>
</body>
</html>
"""

# --- INICIALIZAR BASE DE DATOS ---
def inicializar_db_defectos():
    # Admin por defecto si no hay usuarios en la colección
    if usuarios_col.count_documents({}) == 0:
        usuarios_col.insert_one({
            "username": "admin",
            "password": "123",
            "rol": "admin"
        })

# --- CONTROLLER / RUTAS DE ACCESO (FLASK) ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Datos de gestión para el administrador
    lista_usuarios = list(usuarios_col.find({"rol": "user"}, {"password": 0}))
    lista_grupos = list(grupos_col.find({}))
    
    return render_template_string(
        HTML_TEMPLATE,
        username=session['username'],
        user_role=session['rol'],
        lista_usuarios=lista_usuarios,
        lista_grupos=lista_grupos
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    inicializar_db_defectos()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = usuarios_col.find_one({"username": username, "password": password})
        if user:
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

# --- MÉTODOS DE ADMINISTRACIÓN DE GRUPOS, USUARIOS Y TAREAS ---

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

@app.route('/admin/crear-usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    username = request.form.get('nuevo_usuario')
    password = request.form.get('password')
    rol = request.form.get('rol', 'user')
    grupo_id = request.form.get('grupo_id') # Campo opcional

    if username and password:
        # Guardar o actualizar usuario
        usuarios_col.update_one(
            {"username": username},
            {"$set": {"password": password, "rol": rol, "grupo": grupo_id}},
            upsert=True
        )
        
        # Si se seleccionó un grupo para este usuario
        if grupo_id:
            grupos_col.update_one(
                {"_id": ObjectId(grupo_id)},
                {"$addToSet": {"miembros": username}}
            )
            
    return redirect(url_for('index'))

@app.route('/admin/crear-tarea', methods=['POST'])
def crear_tarea():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    descripcion = request.form.get('descripcion')
    asignado_tipo_id = request.form.get('asignado_tipo_id') # Formato 'user:username' o 'group:nombre_grupo'
    fecha_entrega = request.form.get('fecha_entrega')

    if descripcion and asignado_tipo_id:
        tipo, valor = asignado_tipo_id.split(':', 1)
        
        # Almacenamos la tarea en Mongo
        visitas_col.insert_one({
            "descripcion": descripcion,
            "asignado_a": valor,
            "tipo_asignacion": tipo, # 'user' o 'group'
            "fecha_entrega": fecha_entrega,
            "estado": "pendiente",
            "novedades": [] # Notas internas de Asana
        })
        
    return redirect(url_for('index'))

# --- ENDPOINTS API (RESPUESTAS DINÁMICAS AJAX) ---

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    if 'username' not in session:
        return jsonify([]), 401
        
    query = {}
    
    # REGLA DE ROL:
    # Si es usuario normal, solo ve las asignadas a él individualmente O a cualquier grupo del que es miembro.
    if session.get('rol') != 'admin':
        username = session['username']
        
        # Encontrar grupos de los que es miembro
        mis_grupos_docs = list(grupos_col.find({"miembros": username}))
        mis_grupos_nombres = [g['nombre'] for g in mis_grupos_docs]
        
        # Consultar tareas que coincidan con su nombre de usuario o sus grupos
        query['$or'] = [
            {"asignado_a": username, "tipo_asignacion": "user"},
            {"asignado_a": {"$in": mis_grupos_nombres}, "tipo_asignacion": "group"}
        ]
        
    # Filtros extra
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
    
    novedad = {
        "autor": session['username'],
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "texto": texto_nota
    }
    
    visitas_col.update_one(
        {"_id": ObjectId(tarea_id)},
        {"$push": {"novedades": novedad}}
    )
    return jsonify({"status": "success"})

@app.route('/api/tareas/eliminar/<id>', methods=['DELETE'])
def eliminar_tarea(id):
    if session.get('rol') != 'admin':
        return "No autorizado", 403
        
    visitas_col.delete_one({"_id": ObjectId(id)})
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
