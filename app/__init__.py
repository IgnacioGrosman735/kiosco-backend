import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
from flask_cors import CORS

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "authentication.log_in_user"
login_manager.session_protection = "strong" #Es un parámetro que permite definir que tan fuerte va a ser la protección del login_manager

#Fabrica de aplicaciones. Crea y configura una instancia de la aplicación Flask
def create_app(): #Este parámetro indica si la configuración es desarrollo o producción
    app = Flask(__name__)
    app.config.from_object(Config)#Carga la configuración de la aplicación
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app)
    
    from app.register_routes import auth
    app.register_blueprint(auth)  # Asegúrate de registrar las rutas

    from .routes.proveedores_routes import proveedores_bp
    app.register_blueprint(proveedores_bp)

    from .routes.stock_routes import stock_bp
    app.register_blueprint(stock_bp)
    
    from .routes.productos_routes import productos_bp
    app.register_blueprint(productos_bp)

    from .routes.compras_routes import compras_bp
    app.register_blueprint(compras_bp)

    from .routes.caja_routes import caja_bp
    app.register_blueprint(caja_bp)

    from .routes.ventas_routes import ventas_bp
    app.register_blueprint(ventas_bp)

    
    return app

