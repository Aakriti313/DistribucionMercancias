from conexionDB import obtener_conexion
import folium
import heapq  # Para Dijkstra
from datetime import date
import random


# Obtener ciudades y sus coordenadas desde la base de datos
def obtener_ciudades():
    conexion = obtener_conexion()
    ciudades = {}
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_ciudades, nombre, latitud, longitud FROM ciudades;")
        resultados = cursor.fetchall()
        for fila in resultados:
            ciudades[fila['id_ciudades']] = {
                'nombre': fila['nombre'],
                'coords': [fila['latitud'], fila['longitud']]
            }
    finally:
        cursor.close()
        conexion.close()
    return ciudades


# Obtener el grafo de distancias desde la base de datos
def obtener_grafo_distancias():
    conexion = obtener_conexion()
    grafo = {}
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT ciudad1, ciudad2, distancia FROM distancias;")
        resultados = cursor.fetchall()
        for fila in resultados:
            ciudad1, ciudad2, distancia = fila['ciudad1'], fila['ciudad2'], fila['distancia']
            if ciudad1 not in grafo:
                grafo[ciudad1] = []
            if ciudad2 not in grafo:
                grafo[ciudad2] = []
            grafo[ciudad1].append((ciudad2, distancia))
            grafo[ciudad2].append((ciudad1, distancia))  # Grafo no dirigido
    finally:
        cursor.close()
        conexion.close()
    return grafo


# Algoritmo de Dijkstra para encontrar la ruta más corta
def dijkstra(grafo, inicio, destino):
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[inicio] = 0
    predecesores = {nodo: None for nodo in grafo}
    cola_prioridad = [(0, inicio)]  # (distancia acumulada, nodo actual)
   
    while cola_prioridad:
        distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)
       
        if nodo_actual == destino:
            break
       
        if distancia_actual > distancias[nodo_actual]:
            continue
       
        for vecino, peso in grafo[nodo_actual]:
            distancia_nueva = distancia_actual + peso
            if distancia_nueva < distancias[vecino]:
                distancias[vecino] = distancia_nueva
                predecesores[vecino] = nodo_actual
                heapq.heappush(cola_prioridad, (distancia_nueva, vecino))
   
    # Reconstruir la ruta óptima
    ruta = []
    nodo = destino
    while nodo is not None:
        ruta.insert(0, nodo)
        nodo = predecesores[nodo]
   
    return ruta, distancias[destino]


# Obtener pedidos desde la base de datos
def obtener_pedidos():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_pedido, p.fecha_pedido, p.cantidad,
                   c.nombre AS cliente, d.id_destino AS destino,
                   prod.nombre AS producto
            FROM Pedidos p
            JOIN Clientes c ON p.id_cliente = c.id_cliente
            JOIN Destinos d ON p.id_destino = d.id_destino
            JOIN Producto prod ON p.id_producto = prod.id_producto
        """)
        pedidos = cursor.fetchall()
        return pedidos
    finally:
        cursor.close()
        conexion.close()


# Calcular rutas óptimas para cada pedido
def calcular_ruta_para_pedidos(pedidos):
    grafo_distancias = obtener_grafo_distancias()
    rutas = []
   
    for pedido in pedidos:
        inicio = 2  # Suponiendo que todas las rutas parten de una ciudad base (ID 1)
        destino = pedido['destino']  # ID del destino del pedido
        ruta_optima, distancia_total = dijkstra(grafo_distancias, inicio, destino)
        rutas.append({
            'pedido_id': pedido['id_pedido'],
            'cliente': pedido['cliente'],
            'destino': destino,
            'ruta': ruta_optima,
            'distancia_total': distancia_total
        })
   
    return rutas


# Ejecución principal
pedidos = obtener_pedidos()
rutas_pedidos = calcular_ruta_para_pedidos(pedidos)


import random
import folium


# Función para generar un color aleatorio en formato hexadecimal
def generar_color_aleatorio():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


# Visualizar las rutas en un mapa con colores aleatorios
def visualizar_rutas(rutas):
    ciudades = obtener_ciudades()
    mapa = folium.Map(location=ciudades[2]['coords'], zoom_start=6)  # Centro en ciudad base (ID 1)
   
    # Añadir todas las ciudades al mapa
    for ciudad in ciudades.values():
        folium.Marker(location=ciudad['coords'], popup=ciudad['nombre']).add_to(mapa)


    # Dibujar rutas para cada pedido con colores aleatorios
    for ruta in rutas:
        color_ruta = generar_color_aleatorio()  # Generar un color aleatorio para cada ruta
        for j in range(len(ruta['ruta']) - 1):
            origen = ciudades[ruta['ruta'][j]]['coords']
            destino = ciudades[ruta['ruta'][j + 1]]['coords']
            folium.PolyLine([origen, destino], color=color_ruta, weight=3, opacity=0.6).add_to(mapa)


    # Guardar el mapa
    mapa.save("rutas_pedidos_colores.html")

# Asegúrate de llamar a la función con las rutas calculadas
visualizar_rutas(rutas_pedidos)

# Mostrar las rutas calculadas
for ruta in rutas_pedidos:
    print(f"Pedido {ruta['pedido_id']} - Cliente: {ruta['cliente']} - Ruta: {ruta['ruta']} - Distancia: {ruta['distancia_total']} km")