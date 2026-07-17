import os
import json
import pandas as pd
from flask import Flask, render_template_string, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId, json_util
from io import BytesIO

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['Tareas']

# --- PLANTILLA HTML (Integrada para fácil despliegue) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Tareas - Nestlé DB</title>
    <!-- Usamos Tailwind CSS para un diseño moderno y rápido sin hojas de estilo pesadas -->
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
                <h1 class="text-xl font-bold tracking-wide">Nestlé DB - Panel de Tareas</h1>
            </div>
            <div class="text-sm bg-blue-800 px-3 py-1.5 rounded-full">
                <i class="fa-solid fa-database mr-1"></i> Conectado a MongoDB
            </div>
        </header>

        <!-- Contenido Principal -->
        <main class="flex-grow p-6 max-w-7xl mx-auto w-full">
            <!-- Tarjetas de Resumen / Filtros -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
                <h2 class="text-lg font-semibold mb-4 text-gray-700 flex items-center">
                    <i class="fa-solid fa-filter mr-2 text-blue-600"></i> Filtros de Búsqueda
                </h2>
                
                <form id="filterForm" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Estado de Tarea</label>
                        <select id="estadoFilter" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Todos</option>
                            <option value="pendiente">Pendiente</option>
                            <option value="completado">Completado</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Buscar por ID o Nombre</label>
                        <input type="text" id="searchQuery" placeholder="Escribe para buscar..." class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div class="flex items-end">
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                            <i class="fa-solid fa-magnifying-glass"></i>
                            <span>Aplicar Filtros</span>
                        </button>
                    </div>
                </form>
            </div>

            <!-- Tabla de Datos -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <h3 class="font-bold text-gray-800 text-lg">Listado de Tareas</h3>
                    <span id="recordCount" class="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full font-medium">0 registros</span>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-50 text-gray-400 text-xs uppercase font-semibold border-b border-gray-100">
                                <th class="py-3.5 px-6">ID Tarea</th>
                                <th class="py-3.5 px-6">Descripción</th>
                                <th class="py-3.5 px-6">Estado</th>
                                <th class="py-3.5 px-6">Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="tareasTableBody" class="divide-y divide-gray-100 text-sm">
                            <!-- Los datos se inyectarán dinámicamente con JS -->
                            <tr>
                                <td colspan="4" class="text-center py-8 text-gray-400">
                                    <i class="fa-solid fa-circle-notch animate-spin text-2xl mb-2 block"></i>
                                    Cargando tareas de la base de datos...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="bg-gray-100 border-t border-gray-200 text-center py-4 text-xs text-gray-500">
            &copy; 2026 Nestlé DB Admin. Todos los derechos reservados.
        </footer>
    </div>

    <!-- Lógica de Control en Frontend (JS) -->
    <script>
        // Función para cargar tareas desde nuestra API de Flask
        async function loadTareas(filters = {}) {
            const tbody = document.getElementById('tareasTableBody');
            const recordCount = document.getElementById('recordCount');
            
            // Construir Query Params
            const params = new URLSearchParams(filters).toString();
            
            try {
                const response = await fetch(`/api/tareas?${params}`);
                const data = await response.json();
                
                tbody.innerHTML = '';
                recordCount.textContent = `${data.length} registros`;

                if (data.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="4" class="text-center py-8 text-gray-500">
                                <i class="fa-solid fa-folder-open text-3xl mb-2 text-gray-300 block"></i>
                                No se encontraron tareas que coincidan con la búsqueda.
                            </td>
                        </tr>`;
                    return;
                }

                data.forEach(tarea => {
                    const statusClass = tarea.estado === 'completado' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800';

                    // Convertir ID de Mongo para mostrar
                    const mongoId = tarea._id?.$oid || tarea._id || 'N/A';

                    tbody.innerHTML += `
                        <tr class="hover:bg-gray-50/75 transition-colors">
                            <td class="py-4 px-6 font-mono text-xs text-blue-600">${mongoId.substring(0, 8)}...</td>
                            <td class="py-4 px-6 text-gray-700">${tarea.descripcion || 'Sin descripción'}</td>
                            <td class="py-4 px-6">
                                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass}">
                                    ${tarea.estado || 'pendiente'}
                                </span>
                            </td>
                            <td class="py-4 px-6">
                                <button onclick="verDetalle('${mongoId}')" class="text-blue-600 hover:text-blue-800 font-medium hover:underline text-xs">
                                    <i class="fa-regular fa-eye mr-1"></i> Ver Detalles
                                </button>
                            </td>
                        </tr>
                    `;
                });

            } catch (error) {
                console.error("Error al cargar tareas:", error);
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-8 text-red-500">
                            <i class="fa-solid fa-triangle-exclamation text-3xl mb-2 block"></i>
                            Ocurrió un error al cargar los datos desde el servidor.
                        </td>
                    </tr>`;
            }
        }

        // Listener del Formulario de Filtros
        document.getElementById('filterForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const estado = document.getElementById('estadoFilter').value;
            const search = document.getElementById('searchQuery').value;
            
            loadTareas({ estado: estado, q: search });
        });

        // Detalle de tarea (ejemplo de interacción rápida)
        function verDetalle(id) {
            alert("Consultando detalles del ID en MongoDB: " + id);
        }

        // Carga inicial al abrir la página
        document.addEventListener('DOMContentLoaded', () => loadTareas());
    </script>
</body>
</html>
"""

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    # Renderizamos la interfaz HTML directamente
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    """
    Endpoint tipo API para que el HTML consulte los datos de forma asíncrona.
    Soporta filtros rápidos de búsqueda.
    """
    query = {}
    
    # Filtro por estado
    estado = request.args.get('estado')
    if estado:
        query['estado'] = estado
        
    # Filtro por texto libre (búsqueda)
    search_q = request.args.get('q')
    if search_q:
        # Busca texto que contenga el término (case-insensitive)
        query['descripcion'] = {'$regex': search_q, '$options': 'i'}

    # Traemos las tareas (limitado a 50 para optimizar el rendimiento inicial)
    tareas = list(visitas_col.find(query).limit(50))
    
    # Serializar BSON de MongoDB a formato JSON estándar
    return json_util.dumps(tareas), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    # Habilitamos modo debug para facilitar el desarrollo en local
    app.run(debug=True, port=5000)
