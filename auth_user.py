import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import bcrypt
from dotenv import load_dotenv
import os
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_E")

def generate_token(email):
    payload = {
        'exp': datetime.utcnow() + timedelta(minutes=5),
        'mail': email
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def hashed_pass(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def check_password(hashed_password, user_password):
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not token:
            return jsonify({"status": 400, "error": "Necesitas un token"}), 400
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_mail = data['mail']
        except jwt.ExpiredSignatureError:
            return jsonify({"status": 400, "error": "Token expirado"}), 400
        except jwt.InvalidTokenError:
            return jsonify({"status": 400, "error": "Token inválido"}), 400
        
        return f(current_mail, *args, **kwargs)
    return decorated