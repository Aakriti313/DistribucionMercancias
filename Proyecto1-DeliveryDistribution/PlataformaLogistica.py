from conexionDB import obtener_conexion
import pandas as pd  # type: ignore
import statsmodels.api as sm  # type: ignore
import tkinter as tk
from tkinter import ttk, messagebox
import folium  # type: ignore
from sqlalchemy import create_engine
from io import BytesIO
from PIL import Image, ImageTk  # type: ignore
import webbrowser
import matplotlib as plt
import heapq
from datetime import date
import random
#--------------------------------------------------------

#VENTANA PRINCIPAL
root = tk.Tk()
root.title("Plataforma Logística")
root.geometry("700x400")
root.config(bg="#79a8d7")

#FRAME PRINCIPAL
frame_principal = tk.Frame(root, bg="#79a8d7")
frame_principal.pack(pady=50)

#--------------------------------------------------------

#MENÚ BOTONES
def mostrar_boton_principal():
    for widget in frame_principal.winfo_children():
        widget.destroy()

    boton_ver_tabla = tk.Button(frame_principal, text="Mostrar Pedidos", command=mostrar_pedidos)
    boton_ver_tabla.pack(pady=10)

    boton_calcular_rutas = tk.Button(frame_principal, text="Calcular Rutas", command=calcular_y_mostrar_rutas)
    boton_calcular_rutas.pack(pady=10)
    
    boton_ver_mapa = tk.Button(frame_principal, text="Mapa Puntos Entregas", command=mostrar_mapa_destinos)
    boton_ver_mapa.pack(pady=10)

    # Botón de cerrar
    boton_cerrar = tk.Button(frame_principal, text="Cerrar App", command=confirmar_cierre, bg="red", fg="white")
    boton_cerrar.pack(pady=10)

#--------------------------------------------------------

#CREDENCIALES
def mostrar_vista_credenciales():
    label_usuario = tk.Label(frame_principal, text="Usuario:", bg="#79a8d7", fg="black")
    label_usuario.grid(row=0, column=0, padx=10, pady=10)

    global entry_usuario
    entry_usuario = tk.Entry(frame_principal, bg="#79a8d7", fg="black")
    entry_usuario.grid(row=0, column=1, padx=10, pady=10)

    label_contrasena = tk.Label(frame_principal, text="Contraseña:", bg="#79a8d7", fg="black")
    label_contrasena.grid(row=1, column=0, padx=10, pady=10)

    global entry_contrasena
    entry_contrasena = tk.Entry(frame_principal, show="*", bg="#79a8d7", fg="black")
    entry_contrasena.grid(row=1, column=1, padx=10, pady=10)

    #Botón de registrar
    boton_registro = tk.Button(frame_principal, text="Registrar", command=registrar_usuario)
    boton_registro.grid(row=2, column=0, padx=10, pady=20)

    # Botón de cerrar
    boton_cerrar = tk.Button(frame_principal, text="Cerrar App", command=confirmar_cierre, bg="red", fg="white")
    boton_cerrar.grid(row=2, column=1, padx=10, pady=20)


#CONFIRAMCIÓN DE CIERRE
def confirmar_cierre():
    respuesta = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas cerrar la aplicación?")
    if respuesta:
        root.destroy()


#REGISTRAR USUARIO
def registrar_usuario():
    usuario = entry_usuario.get()
    contrasena = entry_contrasena.get()

    if usuario == "admin" and contrasena == "123":
        messagebox.showinfo("Éxito", "Usuario registrado correctamente!")
        
        for widget in frame_principal.winfo_children():
            widget.destroy()
        
        mostrar_boton_principal()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

#--------------------------------------------------------

# --- PEDIDOS ---

#OBTENER PEDIDOS
def tabla_pedidos():
    conn = obtener_conexion()
    if conn is None:
        return None
    
    query = """ 
    SELECT fecha_pedido, id_destino, COUNT(*) AS total_pedidos,
    GROUP_CONCAT(id_pedido ORDER BY id_pedido) AS ids_pedidos FROM  plataforma_logistica.pedidos
    GROUP BY fecha_pedido, id_destino ORDER BY fecha_pedido, id_destino;
    """

    tabla_pedidos = pd.read_sql(query, conn)
    conn.close()
    return tabla_pedidos


#MOSTRAR PEDIDOS
def mostrar_pedidos():
    for widget in frame_principal.winfo_children():
        widget.destroy()
    
    frame_tabla = tk.Frame(frame_principal, bg="#79a8d7", padx=20, pady=20)
    frame_tabla.pack(expand=True, fill="both", padx=10, pady=10)

    boton_volver = tk.Button(frame_tabla, text="Volver", command=mostrar_boton_principal, bg="#d9e6f2", fg="black")
    boton_volver.pack(pady=10, anchor="ne")

    df = tabla_pedidos()
    if df is not None:
        tabla = ttk.Treeview(frame_tabla, columns=("Fecha", "Destino", "Total Pedidos", "IDs Pedidos"), show="headings")
        tabla.heading("Fecha", text="Fecha Pedido")
        tabla.heading("Destino", text="ID Destino")
        tabla.heading("Total Pedidos", text="Total Pedidos")
        tabla.heading("IDs Pedidos", text="IDs de Pedidos")
        
        for i, row in df.iterrows():
            tabla.insert("", "end", values=(row["fecha_pedido"], row["id_destino"], row["total_pedidos"], row["ids_pedidos"]))
        
        tabla.pack(expand=True, fill="both", pady=10)
    else:
        messagebox.showerror("Error", "No se pudo cargar la tabla de pedidos.")

#--------------------------------------------------------

# --- MOSTRAR MAPA DESTINOS ---
def mostrar_mapa_destinos():
    for widget in frame_principal.winfo_children():
        widget.destroy()

    boton_volver = tk.Button(frame_principal, text="Volver", command=mostrar_boton_principal)
    boton_volver.pack(pady=10, anchor="ne")

    conn = obtener_conexion()
    if conn is None:
        print("Error: No se pudo conectar a la base de datos.")
        return

    query = """SELECT nombre, latitud, longitud FROM plataforma_logistica.ciudades"""
    try:
        destinos = pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        conn.close()
        return

    conn.close()

    mapa = folium.Map(location=[40.4637, -3.7492], zoom_start=6)

    for _, row in destinos.iterrows():
        try:
            latitud = row['latitud']
            longitud = row['longitud']
            nombre = row['nombre']
            color = "green" if nombre.lower() == "mataro" else "blue"

            folium.Marker([latitud, longitud], popup=nombre, icon=folium.Icon(color=color)).add_to(mapa)
        except KeyError:
            pass

    mapa.save("mapa_destinos.html")
    webbrowser.open("mapa_destinos.html")

#--------------------------------------------------------

# --- MOSTRAR MAPA RUTAS ---

#GRAFO DISTÁNCIAS
def grafo_distancias():
    conn = obtener_conexion()
    grafo = {}
    try:
        query = "SELECT ciudad1, ciudad2, distancia FROM plataforma_logistica.distancias;"
        cursor = conn.cursor()
        cursor.execute(query)
        resultados = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        distancias_df = pd.DataFrame(resultados, columns=columnas)
        
        for _, fila in distancias_df.iterrows():
            ciudad1, ciudad2, distancia = fila['ciudad1'], fila['ciudad2'], fila['distancia']
            if ciudad1 not in grafo:
                grafo[ciudad1] = []
            if ciudad2 not in grafo:
                grafo[ciudad2] = []
            grafo[ciudad1].append((ciudad2, distancia))
            grafo[ciudad2].append((ciudad1, distancia))
    finally:
        conn.close()
    return grafo


#ALGORITMO DIJKSTRA
def dijkstra(grafo, inicio, destino):
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[inicio] = 0
    predecesores = {nodo: None for nodo in grafo}
    cola_prioridad = [(0, inicio)]

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

    ruta = []
    nodo = destino
    while nodo is not None:
        ruta.insert(0, nodo)
        nodo = predecesores[nodo]

    return ruta, distancias[destino]


#CALCULAR RUTAS ÓPTIMAS
def calcular_ruta_para_pedidos(pedidos):
    grafo = grafo_distancias()
    rutas = []

    for pedido in pedidos:
        inicio = 2  #ciudad base Mataró ID=2
        destino = pedido['destino']
        ruta_optima, distancia_total = dijkstra(grafo, inicio, destino)
        rutas.append({
            'pedido_id': pedido['id_pedido'],
            'cliente': pedido['cliente'],
            'destino': destino,
            'ruta': ruta_optima,
            'distancia_total': distancia_total
        })

    return rutas


#OBTENER CIUDADES
def obtener_ciudades():
    conn = obtener_conexion()
    ciudades = {}
    try:
        query = "SELECT id_ciudades, nombre, latitud, longitud FROM plataforma_logistica.ciudades;"
        ciudades_df = pd.read_sql(query, conn)
        for _, fila in ciudades_df.iterrows():
            ciudades[fila['id_ciudades']] = {
                'nombre': fila['nombre'],
                'coords': [fila['latitud'], fila['longitud']]
            }
    finally:
        conn.close()
    return ciudades


#COLOR ALEATORIO
def generar_color_random():
    return "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


#VISUALIZAR MAPA DE RUTAS
def visualizar_rutas(rutas):
    ciudades = obtener_ciudades()
    mapa = folium.Map(location=ciudades[2]['coords'], zoom_start=6)

    for ciudad in ciudades.values():
        folium.Marker(location=ciudad['coords'], popup=ciudad['nombre']).add_to(mapa)

    for ruta in rutas:
        color_ruta = generar_color_random()
        for j in range(len(ruta['ruta']) - 1):
            origen = ciudades[ruta['ruta'][j]]['coords']
            destino = ciudades[ruta['ruta'][j + 1]]['coords']
            folium.PolyLine([origen, destino], color=color_ruta, weight=3, opacity=0.6).add_to(mapa)

    mapa.save("rutas_pedidos_colores.html")


#OBTENER FECHA MÁX/MIN CADUCIDAD PEDIDIDOS
def fecha_caducidad():
    conn = obtener_conexion()
    if conn is None:
        return None

    query = """
    SELECT p.fecha_pedido, p.id_destino, COUNT(*) AS total_pedidos,
    GROUP_CONCAT(p.id_pedido ORDER BY p.id_pedido) AS ids_pedidos,
    MAX(prod.caducidad_desde_fabricacion) AS fecha_fabricacion_max,
    MIN(prod.caducidad_desde_fabricacion) AS fecha_fabricacion_min FROM plataforma_logistica.pedidos p
    JOIN plataforma_logistica.producto prod ON p.id_producto = prod.id_producto GROUP BY p.fecha_pedido, 
    p.id_destino ORDER BY p.fecha_pedido, p.id_destino;
    """

    fecha_caducidad = pd.read_sql(query, conn)
    conn.close()
    return fecha_caducidad


#OBTENER DATOS DE PEDIDOS
def obtener_pedidos():
    conn = obtener_conexion()
    try:
        query = """ 
        SELECT p.id_pedido, p.fecha_pedido, p.cantidad,
            c.nombre AS cliente, d.id_destino AS destino,
            prod.nombre AS producto
        FROM plataforma_logistica.Pedidos p
        JOIN plataforma_logistica.Clientes c ON p.id_cliente = c.id_cliente
        JOIN plataforma_logistica.Destinos d ON p.id_destino = d.id_destino
        JOIN plataforma_logistica.Producto prod ON p.id_producto = prod.id_producto
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        pedidos = cursor.fetchall()
        return pedidos
    finally:
        conn.close()


#IMPRIMIR LISTADO DE RUTAS
def imprimir_rutas(rutas):
    ciudades = obtener_ciudades()

    # Usar un conjunto para eliminar rutas duplicadas
    rutas_unicas = set()
    for ruta in rutas:
        # Obtener los nombres de las ciudades en la ruta
        nombres_ruta = tuple(ciudades[ciudad_id]['nombre'] for ciudad_id in ruta['ruta'])
        distancia_total = ruta['distancia_total']
        # Añadir una representación única de la ruta al conjunto
        rutas_unicas.add((nombres_ruta, distancia_total))
    
    # Imprimir las rutas únicas
    for i, (nombres_ruta, distancia_total) in enumerate(rutas_unicas, start=1):
        ruta_str = f"Ruta n°{i}: " + " -> ".join(nombres_ruta) + f" | Kilómetros totales: {distancia_total} km"
        print(ruta_str)


#CALCULAR TIEMPO RUTA
def calcular_tiempo_rutas(rutas):
    velocidad = 120  # Velocidad en km/h
    horas_conduccion_diaria = 8  # Máximo de horas de conducción por día
    descanso_diario = 16  # Horas de descanso obligatorio

    # Usar un conjunto para almacenar rutas únicas
    rutas_unicas = set()
    for ruta in rutas:
        # Crear una representación única de la ruta como tupla
        representacion_ruta = tuple(ruta['ruta']), ruta['distancia_total']
        rutas_unicas.add(representacion_ruta)

    # Calcular tiempo para las rutas únicas
    for i, (ruta, distancia_total) in enumerate(rutas_unicas, start=1):
        tiempo_total_horas = distancia_total / velocidad  # Tiempo total en horas
        
        # Calcular días completos de conducción
        dias_completos = int(tiempo_total_horas // horas_conduccion_diaria)
        horas_restantes = tiempo_total_horas % horas_conduccion_diaria

        # Calcular tiempo total con descansos
        if tiempo_total_horas <= horas_conduccion_diaria:
            # Si la ruta toma menos de 8 horas, no requiere descanso
            dias = 0
            horas = tiempo_total_horas
        else:
            # Si hay días completos, calcular el tiempo de descanso
            tiempo_descanso = dias_completos * descanso_diario
            if horas_restantes > 0:
                tiempo_descanso += descanso_diario  # Agregar un día de descanso si quedan horas restantes
            tiempo_total = tiempo_total_horas + tiempo_descanso  # Tiempo total incluyendo descansos

            # Convertir a días y horas
            dias = int(tiempo_total // 24)
            horas = tiempo_total % 24

        # Imprimir el resultado
        if dias == 0:
            print(f"Ruta n°{i}: {distancia_total} km | Tiempo estimado: {horas:.2f} horas")
        else:
            print(f"Ruta n°{i}: {distancia_total} km | Tiempo estimado: {dias} días y {horas:.2f} horas")


#CALCULAR RUTAS
def calcular_rutas():
    pedidos = obtener_pedidos()
    rutas_pedidos = calcular_ruta_para_pedidos(pedidos)

    if rutas_pedidos:
        imprimir_rutas(rutas_pedidos)

        calcular_tiempo_rutas(rutas_pedidos)
        visualizar_rutas(rutas_pedidos)
        messagebox.showinfo("Rutas", "Las rutas han sido calculadas y visualizadas.")
        webbrowser.open("rutas_pedidos_colores.html")
    else:
        messagebox.showerror("Error", "No se encontraron rutas para mostrar.")


#MOSTRAR RUTAS
def calcular_y_mostrar_rutas():
    for widget in frame_principal.winfo_children():
        widget.destroy()

    label_costo_km = tk.Label(frame_principal, text="Costo por km:", bg="#79a8d7", fg="black")
    label_costo_km.grid(row=0, column=0, padx=10, pady=10)

    entry_costo_km = tk.Entry(frame_principal, bg="#79a8d7", fg="black")
    entry_costo_km.grid(row=0, column=1, padx=10, pady=10)

    label_capacidad_camion = tk.Label(frame_principal, text="Capacidad Camión:", bg="#79a8d7", fg="black")
    label_capacidad_camion.grid(row=1, column=0, padx=10, pady=10)

    entry_capacidad_camion = tk.Entry(frame_principal, bg="#79a8d7", fg="black")
    entry_capacidad_camion.grid(row=1, column=1, padx=10, pady=10)

    label_velocidad_media = tk.Label(frame_principal, text="Velocidad Media:", bg="#79a8d7", fg="black")
    label_velocidad_media.grid(row=2, column=0, padx=10, pady=10)

    entry_velocidad_media = tk.Entry(frame_principal, bg="#79a8d7", fg="black")
    entry_velocidad_media.grid(row=2, column=1, padx=10, pady=10)

    boton_volver = tk.Button(frame_principal, text="Volver", command=mostrar_boton_principal, bg="#d9e6f2", fg="black")
    boton_volver.grid(row=3, column=0, padx=10, pady=20, sticky="w")

    boton_calcular_rutas = tk.Button(frame_principal, text="Calcular Rutas", command=calcular_rutas, bg="#d9e6f2", fg="black")
    boton_calcular_rutas.grid(row=3, column=1, padx=10, pady=20, sticky="e")

#--------------------------------------------------------------------------

#EMPEZAR PROGRAMA
#Llama a las credenciales
mostrar_vista_credenciales()
#Inicia el programa
root.mainloop()