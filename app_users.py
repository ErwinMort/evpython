from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
from auth_user import generate_token, hashed_pass, check_password, token_required

SECRET_KEY = "heyADO"

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        iduser INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE,
        idrol INTEGER,
        FOREIGN KEY (idrol) REFERENCES roles(idrol)
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permisos (
            idpermiso INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            idrol INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    
   # Insertamos roles
    cursor.execute("""
        INSERT OR IGNORE INTO roles (nombre) 
        VALUES ('admin'), ('user')
    """)

    # Insertamos permisos
    cursor.execute("""
        INSERT OR IGNORE INTO permisos (nombre) VALUES 
        ('create_user'), ('get_user'), ('update_user'), ('delete_user')
    """)

    # Encriptar la contraseña 
    admin_pass = hashed_pass('1234e')

    # Insertar usuario administrador con idrol correcto
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, email, idrol) 
        VALUES ('Javier', ?, 'javi@gmail.com', (SELECT idrol FROM roles WHERE nombre = 'admin'))
    """, (admin_pass,))

    
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username')or not data.get('email') or not data.get('password'):
        return jsonify({"status": 400, "error": "El usuario y contraseña son requeridos"}), 400
    
    pass_register = hashed_pass(data['password'])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username, password, email, idrol) VALUES (?,?,?,?)',(data['username'], pass_register, data['email'], 2))
        conn.commit()
        conn.close()
        return jsonify({"status": 200, "message": "Usuario registrado correctamente"}), 200
    except:
        return jsonify({"status": 400, "message": "Registro fallido"}), 400
    

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"status": 400, "error": "No puedes dejar las credenciales vacías"}), 400

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user = cursor.execute('SELECT * FROM users WHERE email = ?', (data.get('email'),)).fetchone()
    conn.close()

    if user and check_password(user['password'], data.get('password')):
        token = generate_token(user['email'])
        return jsonify({"status": 200, "token": token, "message": "Inicio de sesión exitoso"}), 200

    return jsonify({"status": 401, "error": "Credenciales incorrectas"}), 401



@app.route('/get_user', methods=['GET'])
@token_required
def get_user(current_email):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT iduser, username, email, idrol FROM users')
    users_data = cursor.fetchall()

    conn.close()

    users = []
    for row in users_data:
        users.append({
            "iduser": row[0],
            "username": row[1],
            "email": row[2],
            "idrol": row[3]
        })

    return jsonify({"status": 200, "message": "Usuarios mostrados correctamente", "data": users}), 200


@app.route('/create_user', methods=['POST'])
@token_required
def create_user(current_email):
    data = request.get_json()

    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"status": 400, "message": "Faltan datos obligatorios"}), 400

    username = data['username']
    email = data['email']
    password = data['password']
    idrol = data.get('idrol', 2)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        hashed_password = hashed_pass(password)

        cursor.execute(
            'INSERT INTO users (username, password, email, idrol) VALUES (?, ?, ?, ?)',
            (username, hashed_password, email, idrol)
        )
        conn.commit()
        usuario_id = cursor.lastrowid

        return jsonify({
            "status": 200,
            "message": "Usuario creado exitosamente",
            "usuario": {
                "iduser": usuario_id,
                "username": username,
                "email": email,
                "idrol": idrol
            }
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({"status": 400, "error": "El email ya existe"}), 400
    finally:
        conn.close()

@app.route('/delete_user/<int:iduser>', methods=['DELETE'])
@token_required
def delete_user(current_email, iduser):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Verificar si el usuario existe
    cursor.execute("SELECT * FROM users WHERE iduser = ?", (iduser,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": 404, "error": "Usuario no encontrado"}), 404

    cursor.execute("DELETE FROM users WHERE iduser = ?", (iduser,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": 200,
        "message": f"Usuario con id {iduser} fue eliminado correctamente"
    }), 200



@app.route('/update_user/<int:iduser>', methods=['PUT'])
@token_required
def update_user(current_email, iduser):
    data = request.get_json()

    if not data:
        return jsonify({"status": 400, "error": "Datos faltantes"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    idrol = data.get('idrol')

    if not (username or email or password or idrol):
        return jsonify({"status": 400, "error": "Se requiere al menos un campo para actualizar"}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE iduser = ?", (iduser,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": 404, "error": "Usuario no encontrado"}), 404

    update_fields = []
    values = []

    if username:
        update_fields.append("username = ?")
        values.append(username)
    if email:
        update_fields.append("email = ?")
        values.append(email)
    if password:
        hashed = hashed_pass(password)
        update_fields.append("password = ?")
        values.append(hashed)
    if idrol:
        update_fields.append("idrol = ?")
        values.append(idrol)

    values.append(iduser)
    sql = f"UPDATE users SET {', '.join(update_fields)} WHERE iduser = ?"

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return jsonify({
            "status": 200,
            "message": f"Usuario con id {iduser} actualizado correctamente"
        }), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": 400, "error": "El username o email ya existe"}), 400
    finally:
        conn.close()    














if __name__ == '__main__':
    init_db()
    app.run(debug=True)