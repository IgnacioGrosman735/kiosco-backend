from flask import Blueprint, request, jsonify
from app.models import Proveedor, db, ProductoProveedor, Producto


# Crea el Blueprint para productos
productos_bp = Blueprint('productos', __name__)

# Obtener todos los productos
@productos_bp.route('/productos', methods=['GET'])
def obtener_productos():
    try:
        # Consulta para traer productos y sus IDs de proveedores
        productos = (
            db.session.query(
                Producto, 
                ProductoProveedor.proveedor_id
            )
            .join(ProductoProveedor, Producto.id == ProductoProveedor.producto_id)
            .all()
        )

        # Serializar los datos
        resultado = [
            {
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'categoria': producto.categoria,
                'precio_venta': producto.precio_venta,
                'proveedor_id': proveedor_id  # Solo el ID del proveedor
            }
            for producto, proveedor_id in productos
        ]

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Obtener un producto por ID
@productos_bp.route('/productos/<int:id>', methods=['GET'])
def get_producto(id):
    producto = Producto.query.get_or_404(id)
    return jsonify(producto.serialize())

@productos_bp.route('/productos', methods=['POST'])
def create_producto():
    data = request.json
    
    # Verificar que el proveedor existe
    proveedor = Proveedor.query.get(data.get('proveedor_id'))
    if not proveedor:
        return jsonify({"error": "El proveedor no existe."}), 400

    try:       
        # Crear el nuevo producto
        nuevo_producto = Producto(
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion'),
            categoria=data.get('categoria'),
            precio_venta=data.get('precio_venta')
        )
        db.session.add(nuevo_producto)
        db.session.commit()  # Confirmar la creación del producto para obtener el ID

        # Crear el registro en la tabla intermedia con el ID del producto recién creado
        producto_proveedor = ProductoProveedor(
            producto_id=nuevo_producto.id,  # ID del producto recién creado
            proveedor_id=data.get('proveedor_id'),  # ID del proveedor
        )
        
        db.session.add(producto_proveedor)
        db.session.commit()  # Confirmar la creación de la relación

        return jsonify({"message": "Producto y relación proveedor creados con éxito"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@productos_bp.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    # Obtener el producto por ID o devolver un error 404 si no existe
    producto = Producto.query.get_or_404(id)
    data = request.json

    try:
        # Actualizar los campos del producto con los valores recibidos o mantener los existentes
        producto.nombre = data.get('nombre', producto.nombre)
        producto.descripcion = data.get('descripcion', producto.descripcion)
        producto.categoria = data.get('categoria', producto.categoria)
        producto.precio_venta = data.get('precio_venta', producto.precio_venta)

        # Guardar los cambios en la base de datos
        db.session.commit()

        # Preparar la respuesta con la información actualizada
        response = {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "categoria": producto.categoria,
            "precio_venta": producto.precio_venta
        }

        # Retornar la respuesta personalizada
        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

# Eliminar un producto
@productos_bp.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    producto = Producto.query.get_or_404(id)

    # Eliminar registros en la tabla intermedia
    producto_proveedores = ProductoProveedor.query.filter_by(producto_id=id).all()
    for pp in producto_proveedores:
        db.session.delete(pp)
    
    # Eliminar el producto
    db.session.delete(producto)
    db.session.commit()
    return jsonify({'message': 'Producto eliminado'}), 204