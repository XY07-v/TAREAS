import os
import json
import pandas as pd
from flask import Flask, render_template_string, request, jsonify, make_response, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId, json_util

app = Flask(__name__)
# Usamos una clave secreta para manejar las sesiones de usuario (login)
app.secret_key = os.environ.get("SECRET_KEY", "nestle_secret_key_2026")

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['Tareas']
usuarios_col = db['Usuarios']  # Nueva colección para gestionar tus usuarios

# --- PLANTILLA HTML DINÁMICA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Tareas - Nestlé DB</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 font-sans text-gray-800">

    <div class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="bg-blue-900 text-white shadow-md py-4 px-6 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="bg-white p-2 rounded-lg">
                    <span class="text-blue-900 font-bold text-xl">N</span>
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-wide">Nestlé DB</h1>
                    <p class="text-xs text-blue-200">Rol: <span class="capitalize font-semibold text-white">{{ user_role }}</span> ({{ username }})</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <span class="text-xs bg-blue-800 px-3 py-1.5 rounded-full">
                    <i class="fa-solid fa-database mr-1"></i> Conectado
                </span>
                <a href="/logout" class="text-sm bg-red-600 hover:bg-red-700 px-3 py-1.5 rounded-lg transition-colors font-medium">
                    <i class="fa-solid fa-right-from-bracket mr-1"></i> Salir
                </a>
            </div>
        </header>

        <!-- Contenido Principal -->
        <main class="flex-grow p-6 max-w-7xl mx-auto w-full">
            
            {% if user_role == 'admin' %}
            <!-- ================= VISTA DE ADMINISTRADOR ================= -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <!-- Crear Usuario -->
                <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 class="text-base font-bold mb-4 text-gray-700 flex items-center">
                        <i class="fa-solid fa-user-plus mr-2 text-blue-600"></i> Crear Nuevo Usuario
                    </h2>
                    <form action="/admin/crear-usuario" method="POST" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Nombre de Usuario</label>
                            <input type="text" name="nuevo_usuario" required placeholder="Ej: juan_perez" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Contraseña</label>
                            <input type="password" name="password" required placeholder="••••••••" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Rol</label>
                            <select name="rol" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="user">Usuario Estándar</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors">
                            Guardar Usuario
                        </button>
                    </form>
                </div>

                <!-- Crear/Asignar Tarea -->
                <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
                    <h2 class="text-base font-bold mb-4 text-gray-700 flex items-center">
                        <i class="fa-solid fa-circle-plus mr-2 text-blue-600"></i> Crear y Asignar Tarea
                    </h2>
                    <form action="/admin/crear-tarea" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="md:col-span-2">
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Descripción de la Tarea</label>
                            <input type="text" name="descripcion" required placeholder="Ej: Realizar inventario de lácteos en Punto de Venta Centro" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Asignar a</label>
                            <select name="asignado_a" required class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="">Selecciona un usuario...</option>
                                {% for u in lista_usuarios %}
                                    <option value="{{ u.username }}">{{ u.username }} ({{ u.rol }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="flex items-end">
                            <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white font-medium text-sm px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                                <i class="fa-solid fa-plus"></i>
                                <span>Crear e Inicializar</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            {% endif %}

            <!-- ================= LISTADO DE TAREAS (Para ambos roles) ================= -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
                <h2 class="text-lg font-semibold mb-4 text-gray-700 flex items-center">
                    <i class="fa-solid fa-filter mr-2 text-blue-600"></i> Filtrar Mis Tareas
                </h2>
                <form id="filterForm" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Estado</label>
                        <select id="estadoFilter" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Todos</option>
                            <option value="pendiente">Pendiente</option>
                            <option value="completado">Completado</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Búsqueda rápida</label>
                        <input type="text" id="searchQuery" placeholder="Buscar por descripción..." class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div class="flex items-end">
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                            <i class="fa-solid fa-magnifying-glass"></i>
                            <span>Filtrar</span>
                        </button>
                    </div>
                </form>
            </div>

            <!-- Tabla de Datos -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <h3 class="font-bold text-gray-800 text-lg">
                        {% if user_role == 'admin' %} Todas las Tareas del Sistema {% else %} Mis Tareas Asignadas {% endif %}
                    </h3>
                    <span id="recordCount" class="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full font-medium">0 registros</span>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-50 text-gray-400 text-xs uppercase font-semibold border-b border-gray-100">
                                <th class="py-3.5 px-6">ID Tarea</th>
                                <th class="py-3.5 px-6">Descripción</th>
                                <th class="py-3.5 px-6">Asignada a</th>
                                <th class="py-3.5 px-6">Estado</th>
                                <th class="py-3.5 px-6">Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="tareasTableBody" class="divide-y divide-gray-100 text-sm">
                            <tr>
                                <td colspan="5" class="text-center py-8 text-gray-400">
                                    Cargando información...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <!-- Script del Frontend -->
    <script>
        async function loadTareas(filters = {}) {
            const tbody = document.getElementById('tareasTableBody');
            const recordCount = document.getElementById('recordCount');
            const params = new URLSearchParams(filters).toString();
            
            try {
                const response = await fetch(`/api/tareas?${params}`);
                const data = await response.json();
                
                tbody.innerHTML = '';
                recordCount.textContent = `${data.length} registros`;

                if (data.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center py-8 text-gray-400">
                                No se encontraron tareas.
                            </td>
                        </tr>`;
                    return;
                }

                data.forEach(tarea => {
                    const statusClass = tarea.estado === 'completado' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800';

                    const mongoId = tarea._id?.$oid || tarea._id || '';

                    // Si es usuario normal, le permitimos cambiar el estado.
                    // Si es admin, solo observa o borra.
                    let accionesHtml = '';
                    if ("{{ user_role }}" === "admin") {
                        accionesHtml = `
                            <button onclick="eliminarTarea('${mongoId}')" class="text-red-600 hover:text-red-800 font-medium text-xs">
                                <i class="fa-solid fa-trash mr-1"></i> Eliminar
                            </button>
                        `;
                    } else {
                        accionesHtml = `
                            <select onchange="actualizarEstado('${mongoId}', this.value)" class="bg-gray-50 border border-gray-200 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-blue-500">
                                <option value="pendiente" ${tarea.estado === 'pendiente' ? 'selected' : ''}>Pendiente</option>
                                <option value="completado" ${tarea.estado === 'completado' ? 'selected' : ''}>Completado</option>
                            </select>
                        `;
                    }

                    tbody.innerHTML += `
                        <tr class="hover:bg-gray-50/75 transition-colors">
                            <td class="py-4 px-6 font-mono text-xs text-blue-600">${mongoId.substring(0, 8)}...</td>
                            <td class="py-4 px-6 text-gray-700">${tarea.descripcion || 'Sin descripción'}</td>
                            <td class="py-4 px-6 font-semibold text-gray-600">${tarea.asignado_a || 'Sin asignar'}</td>
                            <td class="py-4 px-6">
                                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass}">
                                    ${tarea.estado || 'pendiente'}
                                </span>
                            </td>
                            <td class="py-4 px-6">${accionesHtml}</td>
                        </tr>
                    `;
                });

            } catch (error) {
                console.error(error);
            }
        }

        async function actualizarEstado(id, nuevoEstado) {
            const res = await fetch(`/api/tareas/actualizar`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, estado: nuevoEstado})
            });
            if(res.ok) loadTareas();
        }

        async function eliminarTarea(id) {
            if(confirm("¿Estás seguro de eliminar esta tarea?")) {
                const res = await fetch(`/api/tareas/eliminar/${id}`, { method: 'DELETE' });
                if(res.ok) loadTareas();
            }
        }

        document.getElementById('filterForm').addEventListener('submit', function(e) {
            e.preventDefault();
            loadTareas({
                estado: document.getElementById('estadoFilter').value,
                q: document.getElementById('searchQuery').value
            });
        });

        document.addEventListener('DOMContentLoaded', () => loadTareas());
    </script>
</body>
</html>
"""

# --- PLANTILLA DEL LOGIN ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Iniciar Sesión - Nestlé DB</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-xl shadow-xl w-full max-w-md">
        <h2 class="text-2xl font-bold text-center text-slate-800 mb-6">Panel de Acceso Nestlé</h2>
        
        {% if error %}
            <div class="bg-red-100 text-red-700 p-3 rounded-lg text-sm mb-4">{{ error }}</div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-xs font-semibold text-gray-600 uppercase mb-1">Usuario</label>
                <input type="text" name="username" required placeholder="Escribe tu usuario" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
                <label class="block text-xs font-semibold text-gray-600 uppercase mb-1">Contraseña</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition-colors text-sm">
                Ingresar al Sistema
            </button>
        </form>
    </div>
</body>
</html>
"""

# --- INICIALIZAR ADMINISTRADOR POR DEFECTO ---
def inicializar_admin_defecto():
    # Creamos un usuario administrador de forma automática si no existe ningún usuario
    if usuarios_col.count_documents({}) == 0:
        usuarios_col.insert_one({
            "username": "admin",
            "password": "123",  # Contraseña inicial de prueba
            "rol": "admin"
        })

# --- RUTAS DE CONTROL DE ACCESO ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Traemos todos los usuarios para que el Administrador pueda asignarle tareas
    lista_usuarios = list(usuarios_col.find({}, {"password": 0}))
    return render_template_string(
        HTML_TEMPLATE, 
        username=session['username'], 
        user_role=session['rol'],
        lista_usuarios=lista_usuarios
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    inicializar_admin_defecto()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = usuarios_col.find_one({"username": username, "password": password})
        if user:
            session['username'] = user['username']
            session['rol'] = user['rol']
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Credenciales inválidas, intenta de nuevo.")
            
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- RUTAS ADMINISTRADOR (CREACIONES) ---

@app.route('/admin/crear-usuario', methods=['POST'])
def crear_usuario():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    nuevo_user = request.form.get('nuevo_usuario')
    password = request.form.get('password')
    rol = request.form.get('rol', 'user')

    # Guardamos en nuestra colección de MongoDB
    if nuevo_user and password:
        usuarios_col.update_one(
            {"username": nuevo_user},
            {"$set": {"password": password, "rol": rol}},
            upsert=True
        )
    return redirect(url_for('index'))

@app.route('/admin/crear-tarea', methods=['POST'])
def crear_tarea():
    if session.get('rol') != 'admin':
        return "Acceso denegado", 403
        
    descripcion = request.form.get('descripcion')
    asignado_a = request.form.get('asignado_a')

    if descripcion and asignado_a:
        visitas_col.insert_one({
            "descripcion": descripcion,
            "asignado_a": asignado_a,
            "estado": "pendiente"
        })
    return redirect(url_for('index'))

# --- ENDPOINTS API ---

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    if 'username' not in session:
        return jsonify([]), 401
        
    query = {}
    
    # REGLA DE ROL: El usuario normal solo puede ver sus propias tareas asignadas
    if session.get('rol') != 'admin':
        query['asignado_a'] = session['username']
        
    # Filtros extra del buscador
    estado = request.args.get('estado')
    if estado:
        query['estado'] = estado
        
    search_q = request.args.get('q')
    if search_q:
        query['descripcion'] = {'$regex': search_q, '$options': 'i'}

    tareas = list(visitas_col.find(query))
    return json_util.dumps(tareas), 200, {'Content-Type': 'application/json'}

@app.route('/api/tareas/actualizar', methods=['POST'])
def actualizar_tarea():
    if 'username' not in session:
        return "No autorizado", 401
        
    data = request.json
    tarea_id = data.get('id')
    nuevo_estado = data.get('estado')
    
    # Modificar en MongoDB
    visitas_col.update_one(
        {"_id": ObjectId(tarea_id)},
        {"$set": {"estado": nuevo_estado}}
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
