import sqlite3
from flask import Flask, render_template, g, request, redirect, url_for, flash, session
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'supersecreto'  # Cambia esto en producción
DATABASE = 'autos.db'

# Opciones fijas de medio de pago
MEDIOS_PAGO = ['Transferencia', 'Tarjeta de crédito', 'Tarjeta de débito', 'Efectivo']

# --- Funciones de base de datos ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Tabla autos con campo foto
    c.execute('''CREATE TABLE IF NOT EXISTS autos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        anio INTEGER NOT NULL,
        kilometraje INTEGER NOT NULL,
        patente TEXT NOT NULL,
        precio INTEGER NOT NULL,
        foto TEXT
    )''')
    # Tabla clientes
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        telefono TEXT NOT NULL,
        direccion TEXT NOT NULL,
        contrasena TEXT NOT NULL
    )''')
    # Poblar autos si está vacío
    c.execute('SELECT COUNT(*) FROM autos')
    if c.fetchone()[0] == 0:
        autos_ejemplo = [
            ('Toyota', 'Corolla', 2018, 45000, 'ABCD12', 9500000, 'corolla2018.jpg'),
            ('Hyundai', 'Accent', 2019, 38000, 'EFGH34', 8700000, 'accent2019.jpg'),
            ('Chevrolet', 'Sail', 2017, 52000, 'IJKL56', 6900000, 'sail2017.jpg'),
            ('Kia', 'Rio', 2020, 21000, 'MNOP78', 10500000, 'rio2020.jpg'),
            ('Nissan', 'Versa', 2016, 60000, 'QRST90', 6300000, 'versa2016.jpg'),
            ('Mazda', '3', 2018, 41000, 'UVWX12', 9900000, 'mazda3_2018.jpg'),
            ('Ford', 'Fiesta', 2015, 75000, 'YZAB34', 5700000, 'fiesta2015.jpg'),
            ('Peugeot', '208', 2019, 33000, 'CDEF56', 8800000, '208_2019.jpg'),
            ('Volkswagen', 'Gol', 2017, 54000, 'GHIJ78', 7100000, 'gol2017.jpg'),
            ('Renault', 'Symbol', 2018, 47000, 'KLMN90', 8000000, 'symbol2018.jpg')
        ]
        c.executemany('INSERT INTO autos (marca, modelo, anio, kilometraje, patente, precio, foto) VALUES (?, ?, ?, ?, ?, ?, ?)', autos_ejemplo)
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Rutas ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/autos')
def autos():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, marca, modelo, anio, kilometraje, patente, precio, foto FROM autos')
    autos = c.fetchall()
    return render_template('autos.html', autos=autos)

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    db = get_db()
    c = db.cursor()
    resultados = []
    modelo = request.form.get('modelo', '')
    marca = request.form.get('marca', '')
    anio = request.form.get('anio', '')
    precio = request.form.get('precio', '')
    # Obtener todas las marcas para el select
    c.execute('SELECT DISTINCT marca FROM autos ORDER BY marca')
    marcas = [row[0] for row in c.fetchall()]
    if request.method == 'POST':
        query = 'SELECT id, marca, modelo, anio, kilometraje, patente, precio, foto FROM autos WHERE 1=1'
        params = []
        if marca:
            query += ' AND marca = ?'
            params.append(marca)
        if modelo:
            query += ' AND modelo LIKE ?'
            params.append(f'%{modelo}%')
        if anio:
            query += ' AND anio = ?'
            params.append(anio)
        if precio:
            query += ' AND precio <= ?'
            params.append(precio)
        c.execute(query, params)
        resultados = c.fetchall()
    return render_template('buscar.html', resultados=resultados, modelo=modelo, marca=marca, marcas=marcas, anio=anio, precio=precio)

# --- Clientes ---
@app.route('/clientes/registro', methods=['GET', 'POST'])
def registro_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        contrasena = request.form['contrasena']
        db = get_db()
        c = db.cursor()
        try:
            c.execute('INSERT INTO clientes (nombre, correo, telefono, direccion, contrasena) VALUES (?, ?, ?, ?, ?)',
                      (nombre, correo, telefono, direccion, contrasena))
            db.commit()
            flash('Registro exitoso. Ahora puedes ingresar.', 'success')
            return redirect(url_for('login_cliente'))
        except sqlite3.IntegrityError:
            flash('El correo ya está registrado.', 'danger')
    return render_template('registro_cliente.html')

@app.route('/clientes/login', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        db = get_db()
        c = db.cursor()
        c.execute('SELECT id, nombre FROM clientes WHERE correo = ? AND contrasena = ?', (correo, contrasena))
        cliente = c.fetchone()
        if cliente:
            session['cliente_id'] = cliente[0]
            session['cliente_nombre'] = cliente[1]
            flash('Ingreso exitoso. ¡Bienvenido, {}!'.format(cliente[1]), 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login_cliente.html')

@app.route('/clientes/logout')
def logout_cliente():
    session.pop('cliente_id', None)
    session.pop('cliente_nombre', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('index'))

@app.route('/clientes')
def clientes():
    return render_template('clientes_menu.html')

# --- Carrito ---
@app.route('/agregar_carrito/<int:auto_id>')
def agregar_carrito(auto_id):
    if 'cliente_id' not in session:
        flash('Debes ingresar como cliente para agregar autos al carrito.', 'danger')
        return redirect(url_for('login_cliente'))
    carrito = session.get('carrito', [])
    if auto_id not in carrito:
        carrito.append(auto_id)
    session['carrito'] = carrito
    flash('Auto agregado al carrito.', 'success')
    return redirect(url_for('autos'))

@app.route('/eliminar_carrito/<int:auto_id>')
def eliminar_carrito(auto_id):
    carrito = session.get('carrito', [])
    if auto_id in carrito:
        carrito.remove(auto_id)
        session['carrito'] = carrito
        flash('Auto eliminado del carrito.', 'info')
    return redirect(url_for('carrito'))

@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'cliente_id' not in session:
        flash('Debes ingresar como cliente para ver el carrito.', 'danger')
        return redirect(url_for('login_cliente'))
    db = get_db()
    c = db.cursor()
    carrito = session.get('carrito', [])
    autos = []
    total = 0
    if carrito:
        q = f"SELECT id, marca, modelo, anio, kilometraje, patente, precio, foto FROM autos WHERE id IN ({','.join(['?']*len(carrito))})"
        c.execute(q, carrito)
        autos = c.fetchall()
        total = sum(auto[6] for auto in autos)
    if request.method == 'POST':
        medio_pago = request.form['medio_pago']
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cliente_id = session['cliente_id']
        for auto in autos:
            c.execute('''CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                auto_id INTEGER,
                fecha TEXT,
                valor INTEGER,
                medio_pago TEXT
            )''')
            c.execute('INSERT INTO compras (cliente_id, auto_id, fecha, valor, medio_pago) VALUES (?, ?, ?, ?, ?)',
                      (cliente_id, auto[0], fecha, auto[6], medio_pago))
        db.commit()
        session['carrito'] = []
        flash('¡Compra realizada con éxito!', 'success')
        return redirect(url_for('autos'))
    return render_template('carrito.html', autos=autos, total=total, medios_pago=MEDIOS_PAGO)

@app.route('/consultas', methods=['GET', 'POST'])
def consultas():
    db = get_db()
    c = db.cursor()
    opcion = request.form.get('opcion', 'cliente')
    resultados = []
    total_diario = total_mensual = total_general = None
    if opcion == 'cliente':
        c.execute('''SELECT cl.nombre, a.marca, a.modelo, a.patente, co.fecha, co.valor, co.medio_pago
                     FROM compras co
                     JOIN clientes cl ON co.cliente_id = cl.id
                     JOIN autos a ON co.auto_id = a.id
                     ORDER BY co.fecha DESC''')
        resultados = c.fetchall()
    elif opcion == 'auto':
        c.execute('''SELECT a.marca, a.modelo, co.valor, co.fecha, a.patente
                     FROM compras co
                     JOIN autos a ON co.auto_id = a.id
                     ORDER BY co.fecha DESC''')
        resultados = c.fetchall()
    elif opcion == 'total':
        # Total general
        c.execute('SELECT SUM(valor) FROM compras')
        total_general = c.fetchone()[0] or 0
        # Total diario
        c.execute('SELECT strftime("%Y-%m-%d", fecha) as dia, SUM(valor) FROM compras GROUP BY dia ORDER BY dia DESC')
        total_diario = c.fetchall()
        # Total mensual
        c.execute('SELECT strftime("%Y-%m", fecha) as mes, SUM(valor) FROM compras GROUP BY mes ORDER BY mes DESC')
        total_mensual = c.fetchall()
    return render_template('consultas.html', opcion=opcion, resultados=resultados, total_diario=total_diario, total_mensual=total_mensual, total_general=total_general)

@app.route('/contacto')
def contacto():
    correo = 'ventas@autoventas.cl'
    telefono = '+56 9 1234 5678'
    return render_template('contacto.html', correo=correo, telefono=telefono)

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 