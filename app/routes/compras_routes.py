from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import Caja, CompraDetalle, Proveedor, db, ProductoProveedor, Producto, Stock, Compra
from app.routes.caja_routes import registrar_movimiento_caja


# Crea el Blueprint para compras
compras_bp = Blueprint('compras', __name__)

#Registrar compra
@compras_bp.route('/compras', methods=['POST'])
def registrar_compra():
    data = request.json
    proveedor_id = data['proveedor_id']
    productos = data['productos']  # Lista de productos

    # Inicializamos el costo total de la compra
    costo_total_compra = 0
    detalles_compra = []  # Lista para guardar los detalles antes de la inserción

    # Procesar los productos recibidos en la compra
    for item in productos:
        producto_id = item['producto_id']
        cantidad = item['cantidad']
        costo_unitario = int(item['costo_unitario'])  # El usuario ingresa este valor

        # Calcular el costo total para el detalle (cantidad * costo_unitario)
        costo_total = cantidad * costo_unitario
        costo_total_compra += costo_total  # Acumular el costo total de la compra

        # Crear un registro en la tabla "compras_detalle"
        detalle = CompraDetalle(
            producto_id=producto_id,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            costo_total=costo_total
        )
        detalles_compra.append(detalle)

        # Actualizar el stock
        stock = Stock.query.filter_by(producto_id=producto_id).first()
        if stock:
            stock.cantidad += cantidad
        else:
            nuevo_stock = Stock(producto_id=producto_id, cantidad=cantidad)
            db.session.add(nuevo_stock)

    # Crear el registro de la compra
    nueva_compra = Compra(
        proveedor_id=proveedor_id,
        costo_total=costo_total_compra,
        fecha=datetime.now()
    )
    db.session.add(nueva_compra)
    db.session.flush()  # Generar el ID de la compra sin hacer commit aún

    # Asignar `compra_id` a los detalles y agregarlos a la sesión
    for detalle in detalles_compra:
        detalle.compra_id = nueva_compra.id
        db.session.add(detalle)

    # Registrar el movimiento en la caja
    registrar_movimiento_caja(tipo_movimiento='compra', monto=-costo_total_compra)

    # Confirmar los cambios en la base de datos
    db.session.commit()

    return jsonify({'message': 'Compra registrada exitosamente'}), 201


@compras_bp.route('/compras/<int:proveedor_id>/productos', methods=['GET'])
def get_productos_por_proveedor(proveedor_id):
    # Consulta que une Producto con ProductoProveedor y filtra por proveedor_id
    productos = db.session.query(Producto).join(ProductoProveedor).filter(ProductoProveedor.proveedor_id == proveedor_id).all()
    # Devuelve la lista de productos en formato JSON
    return jsonify([producto.serialize() for producto in productos])


#Obtiene todas las compras
@compras_bp.route('/compras', methods=['GET'])
def obtener_compras():
    compras = Compra.query.all()
    compras_data = []
    for compra in compras:
        detalles = CompraDetalle.query.filter_by(compra_id=compra.id).all()
        detalles_data = [
            {'producto_id': detalle.producto_id, 'cantidad': detalle.cantidad, 'costo_unitario': detalle.costo_unitario, 'costo_total': detalle.costo_total}
            for detalle in detalles
        ]
        compras_data.append({
            'id': compra.id,
            'proveedor_id': compra.proveedor_id,
            'fecha': compra.fecha.isoformat(),  # Convierte la fecha a un formato ISO
            'costo_total': compra.costo_total,  # Asegúrate de que este sea el nombre correcto de la propiedad en la tabla compras
            'detalles': detalles_data
        })
    return jsonify(compras_data), 200

#Obtiene una compra específica
@compras_bp.route('/compras/<int:compra_id>', methods=['GET'])
def obtener_compra(compra_id):
    compra = Compra.query.get(compra_id)
    if not compra:
        return jsonify({'error': 'Compra no encontrada'}), 404

    detalles = CompraDetalle.query.filter_by(compra_id=compra.id).all()
    detalles_data = [
        {'producto_id': detalle.producto_id, 'cantidad': detalle.cantidad, 'costo_unitario': detalle.costo_unitario, 'costo_total': detalle.costo_total}
            for detalle in detalles
    ]
    compra_data = {
        'id': compra.id,
        'proveedor_id': compra.proveedor_id,
        'fecha': compra.fecha.isoformat(),  # Convierte la fecha a un formato ISO
        'costo_total': compra.costo_total,  # Asegúrate de que este sea el nombre correcto de la propiedad en la tabla compras
        'detalles': detalles_data
    }
    return jsonify(compra_data), 200

#Eliminar compra
@compras_bp.route('/compras/<int:compra_id>', methods=['DELETE'])
def eliminar_compra(compra_id):
    # Buscar la compra por ID
    compra = Compra.query.get(compra_id)
    
    if not compra:
        return jsonify({'error': 'Compra no encontrada'}), 404

    # Obtener los detalles de la compra
    detalles_compra = CompraDetalle.query.filter_by(compra_id=compra_id).all()

    # Revertir el stock para cada producto en los detalles de la compra
    for detalle in detalles_compra:
        stock = Stock.query.filter_by(producto_id=detalle.producto_id).first()
        if stock:
            stock.cantidad -= detalle.cantidad  # Revertir la cantidad agregada al stock

    # Eliminar los detalles de la compra
    for detalle in detalles_compra:
        db.session.delete(detalle)

    # CAJA
    # Usamos el costo total de la compra para revertir el saldo
    monto_compra = float(compra.costo_total)  # Obtén el costo total de la compra
    # Revertir el saldo sumando el monto de la compra al saldo actual
    registrar_movimiento_caja(tipo_movimiento='ajuste', monto=monto_compra)

    # Eliminar la compra
    db.session.delete(compra)

    # Confirmar todos los cambios
    db.session.commit()

    return jsonify({'message': 'Compra eliminada exitosamente'}), 200

#Editar compra
@compras_bp.route('/compras/<int:compra_id>', methods=['PUT'])
def editar_compra(compra_id):
    # Obtener la compra existente
    compra = Compra.query.get(compra_id)
    
    if not compra:
        return jsonify({'error': 'Compra no encontrada'}), 404

    # Obtener los datos de la solicitud
    data = request.json
    proveedor_id = data['proveedor_id']
    productos = data['productos']  # Lista de productos

    # Obtener los detalles anteriores de la compra
    detalles_compra = CompraDetalle.query.filter_by(compra_id=compra_id).all()

    # Revertir el stock para los productos de la compra anterior
    for detalle in detalles_compra:
        stock = Stock.query.filter_by(producto_id=detalle.producto_id).first()
        if stock:
            # Restar la cantidad que se agregó al stock cuando se creó la compra
            stock.cantidad -= detalle.cantidad

    # Eliminar los detalles de la compra anterior
    for detalle in detalles_compra:
        db.session.delete(detalle)

    # Calcular el nuevo costo total de la compra
    nuevo_costo_total = sum(item['cantidad'] * item['precio'] for item in productos)

    # Actualizar la compra
    compra.proveedor_id = proveedor_id
    compra.costo_total = nuevo_costo_total
    compra.fecha = datetime.now()  # Opcional: actualizar la fecha si es necesario

    # Insertar los nuevos detalles de la compra y actualizar el stock
    for item in productos:
        producto_id = item['producto_id']
        cantidad = item['cantidad']
        costo_unitario = item['precio']

        # Crear el nuevo detalle de la compra
        nuevo_detalle = CompraDetalle(
            compra_id=compra.id,
            producto_id=producto_id,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            costo_total=cantidad * costo_unitario
        )
        db.session.add(nuevo_detalle)

        # Actualizar el stock con las nuevas cantidades
        stock = Stock.query.filter_by(producto_id=producto_id).first()
        if stock:
            # Aumentar la nueva cantidad en el stock
            stock.cantidad += cantidad
        else:
            # Si no existe el stock, lo creamos
            nuevo_stock = Stock(producto_id=producto_id, cantidad=cantidad)
            db.session.add(nuevo_stock)

    # CAJA
    # Primero revertimos el movimiento anterior usando el costo_total original
    monto = float(compra.costo_total * -1)
    registrar_movimiento_caja(tipo_movimiento='ajuste', monto=monto)
    # Luego registramos el nuevo movimiento con el costo actualizado
    registrar_movimiento_caja(tipo_movimiento='compra', monto=-nuevo_costo_total)

    # Confirmar los cambios
    db.session.commit()

    return jsonify({'message': 'Compra actualizada exitosamente'}), 200


