from flask import Flask, request, jsonify, Blueprint
from app.models import User, Producto, Venta, Proveedor, Caja, Compra
from app import bcrypt
from flask_login import login_user, logout_user, login_required
from decimal import Decimal

from app import db

auth = Blueprint('register', __name__)

@auth.route('/register', methods=['POST'])
def register_user():
    data = request.json  # Recibe los datos en formato JSON
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    # Validaciones del lado del servidor
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El correo electrónico ya está registrado"}), 400
    
    # Crear el nuevo usuario
    new_user = User.create_user(nombre=nombre, email=email, password=password)
    
    return jsonify({"message": "Usuario creado exitosamente"}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Login failed. Check your credentials.'}), 401

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

