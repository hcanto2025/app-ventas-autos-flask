import os
import sqlite3

# Ruta a la base de datos y a la carpeta de fotos
DB_PATH = 'autos.db'
FOTOS_DIR = os.path.join('static', 'fotos')

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Obtener todos los autos
c.execute('SELECT id, marca, modelo FROM autos')
autos = c.fetchall()

# Listar todos los archivos de la carpeta de fotos
fotos = os.listdir(FOTOS_DIR)

def normalizar(texto):
    return texto.lower().replace(' ', '')

# Actualizar la columna foto para cada auto
for auto in autos:
    auto_id, marca, modelo = auto
    nombre_busqueda = normalizar(marca) + normalizar(modelo)
    foto_encontrada = None
    for foto in fotos:
        if nombre_busqueda in normalizar(foto):
            foto_encontrada = foto
            break
    if foto_encontrada:
        c.execute('UPDATE autos SET foto = ? WHERE id = ?', (foto_encontrada, auto_id))
        print(f'Auto {marca} {modelo}: foto actualizada a {foto_encontrada}')
    else:
        print(f'Auto {marca} {modelo}: foto NO encontrada')

conn.commit()
conn.close()
print("Actualización terminada.")