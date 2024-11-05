from flask import Blueprint, request, jsonify
from app.models import Proveedor, db, ProductoProveedor, Producto


# Crea el Blueprint para proveedores
proveedores_bp = Blueprint('proveedores', __name__)

# Ruta para obtener todos los proveedores
@proveedores_bp.route('/proveedores', methods=['GET'])
def obtener_proveedores():
    proveedores = Proveedor.query.all()
    resultado = [{"id": p.id, "cuit": p.cuit, "razon_social": p.razon_social, "condicion_fiscal": p.condicion_fiscal, 
                  "direccion": p.direccion, "telefono": p.telefono, "email": p.email} for p in proveedores]
    return jsonify(resultado)


# Ruta para crear un nuevo proveedor
@proveedores_bp.route('/proveedores', methods=['POST'])
def crear_proveedor():
    data = request.json
    nuevo_proveedor = Proveedor(
        cuit=data.get('cuit'),
        razon_social=data.get('razon_social'),
        condicion_fiscal=data.get('condicion_fiscal'),
        direccion=data.get('direccion'),
        telefono=data.get('telefono'),
        email=data.get('email')
    )
    db.session.add(nuevo_proveedor)
    db.session.commit()
    return jsonify({"message": "Proveedor creado exitosamente"}), 201

@proveedores_bp.route('/proveedores/<int:proveedor_id>/productos', methods=['GET'])
def obtener_productos_por_proveedor(proveedor_id):
    # Consultar la tabla intermedia ProductoProveedor con un JOIN para obtener los productos y sus nombres
    productos_proveedor = db.session.query(ProductoProveedor).join(Producto).filter(
        ProductoProveedor.proveedor_id == proveedor_id).all()

    if not productos_proveedor:
        return jsonify({"message": "No se encontraron productos para este proveedor"}), 404

    # Crear una lista de los productos con su información
    productos = []
    for producto_proveedor in productos_proveedor:
        producto = {
            'id': producto_proveedor.producto.id,
            'nombre': producto_proveedor.producto.nombre,  # Accedes al nombre del producto desde la relación
            'precio': float(producto_proveedor.precio)
        }
        productos.append(producto)

    # Devolver la lista de productos
    return jsonify(productos)

# Ruta para obtener un proveedor específico por ID
@proveedores_bp.route('/proveedores/<int:id>', methods=['GET'])
def obtener_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    resultado = {
        "id": proveedor.id,
        "cuit": proveedor.cuit,
        "razon_social": proveedor.razon_social,
        "condicion_fiscal": proveedor.condicion_fiscal,
        "direccion": proveedor.direccion,
        "telefono": proveedor.telefono,
        "email": proveedor.email
    }
    return jsonify(resultado)


# Ruta para actualizar un proveedor existente
@proveedores_bp.route('/proveedores/<int:id>', methods=['PUT'])
def actualizar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    data = request.json
    proveedor.cuit = data.get('cuit', proveedor.cuit)
    proveedor.razon_social = data.get('razon_social', proveedor.razon_social)
    proveedor.condicion_fiscal = data.get('condicion_fiscal', proveedor.condicion_fiscal)
    proveedor.direccion = data.get('direccion', proveedor.direccion)
    proveedor.telefono = data.get('telefono', proveedor.telefono)
    proveedor.email = data.get('email', proveedor.email)
    
    db.session.commit()
    return jsonify({"message": "Proveedor actualizado exitosamente"})


# Ruta para eliminar un proveedor
@proveedores_bp.route('/proveedores/<int:id>', methods=['DELETE'])
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    return jsonify({"message": "Proveedor eliminado exitosamente"})