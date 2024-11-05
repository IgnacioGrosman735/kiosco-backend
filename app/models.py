from app import db, bcrypt, login_manager
from flask_login import UserMixin #Clase que se utiliza para simplificar la implementación del modelo de usuario. 
from datetime import datetime
from decimal import Decimal

#Creamos el modelo de usuario
class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, index=True)#El index se agrega para mejorar la velocidad de consulta en la tabla
    password = db.Column(db.String(265))

    def check_password(self, password):#Retorna True o False si la contraseña que recibe es igual a la de la base de datos
        return bcrypt.check_password_hash(self.password, password)
    
    @classmethod
    def create_user(cls, nombre, email, password):
        user = cls(
            nombre=nombre,
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8")
        )

        db.session.add(user)
        db.session.commit()
        return user

#Creamos este cargador para que cuando nosotros llamemos al decorador login_required, que es el
# que nos permite proteger las rutas de Flask, el llame a login_manager y a través del id este le 
# diga si el usuario está activo o no    
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.String(100), nullable=False)
    venta_total = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.DateTime, default=datetime.now)
    
    # Relación uno a muchos con VentaDetalle
    detalles = db.relationship('VentaDetalle', backref='venta', lazy=True)
    
    # Relación con el modelo Cliente
    """ proveedor = db.relationship('Proveedor', backref=db.backref('compras', lazy=True)) """

    """ def __repr__(self):
        return f'<Venta Producto ID: {self.producto_id}, Cantidad: {self.cantidad}>' """

class VentaDetalle(db.Model):
    __tablename__ = 'detalles_ventas'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    venta_total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relación con el modelo Producto
    producto = db.relationship('Producto', backref=db.backref('detalles_venta', lazy=True))

    def __repr__(self):
        return f'<VentaDetalle {self.id} - Producto {self.producto_id} - Cantidad {self.cantidad}>'

from datetime import datetime

class Compra(db.Model):
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    costo_total = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.DateTime, default=datetime.now)
    
    # Relación uno a muchos con CompraDetalle
    detalles = db.relationship('CompraDetalle', backref='compra', lazy=True)
    
    # Relación con el modelo Proveedor
    proveedor = db.relationship('Proveedor', backref=db.backref('compras', lazy=True))

    def __repr__(self):
        return f'<Compra {self.id} - Proveedor {self.proveedor_id}>'

class CompraDetalle(db.Model):
    __tablename__ = 'detalles_compras'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    costo_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    costo_total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relación con el modelo Producto
    producto = db.relationship('Producto', backref=db.backref('detalles', lazy=True))

    def __repr__(self):
        return f'<CompraDetalle {self.id} - Producto {self.producto_id} - Cantidad {self.cantidad}>'

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False, unique=True)
    cantidad = db.Column(db.Integer, nullable=False)

    # Relación con el modelo Producto
    producto = db.relationship('Producto', backref=db.backref('stock', lazy='joined'))

    def __repr__(self):
        return f'<Stock Producto {self.producto_id} - Cantidad {self.cantidad}>'


class Caja(db.Model):
    __tablename__ = 'caja'
    id = db.Column(db.Integer, primary_key=True)
    tipo_movimiento = db.Column(db.String(10), nullable=False)  # 'ingreso' o 'egreso'
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    saldo = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Caja {self.id} - Tipo {self.tipo} - Monto {self.monto}>'

    


class Proveedor(db.Model):
    
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    cuit = db.Column(db.String(100), nullable=False)
    razon_social = db.Column(db.String(100), nullable=False)
    condicion_fiscal = db.Column(db.String(200))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))
    
    # Relación uno-a-muchos con ProductoProveedor
    producto_proveedor = db.relationship('ProductoProveedor', back_populates='proveedor')

    def __repr__(self):
        return f'<Proveedor {self.razon_social}>'


class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(50), nullable=True)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria": self.categoria
        }
    
    # Relación uno-a-muchos con ProductoProveedor
    producto_proveedor = db.relationship(
        'ProductoProveedor', 
        back_populates='producto')

    def __repr__(self):
        return f'<Producto {self.nombre}>'
    

class ProductoProveedor(db.Model):

    __tablename__ = 'producto_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)

    # Relación con Producto
    producto = db.relationship('Producto', back_populates='producto_proveedor') #relationship() es una función de SQLAlchemy utilizada para establecer relaciones entre modelos en una base de datos
       
    # Relación con Proveedor
    proveedor = db.relationship('Proveedor', back_populates='producto_proveedor')