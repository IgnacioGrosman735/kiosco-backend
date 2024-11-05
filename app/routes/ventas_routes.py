from collections import defaultdict
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import Caja, CompraDetalle, Proveedor, db, ProductoProveedor, Producto, Stock, Compra, Venta, VentaDetalle
from app.routes.caja_routes import registrar_movimiento_caja
from sqlalchemy import text


# Crea el Blueprint para ventas
ventas_bp = Blueprint('ventas', __name__)

#Registrar venta
@ventas_bp.route('/ventas', methods=['POST'])
def registrar_venta():
    data = request.json
    cliente_id = data['cliente_id']
    productos = data['productos']  # Lista de productos

    # Inicializamos el precio total de la venta
    valor_total_venta = 0
    detalles_venta = []  # Lista para guardar los detalles antes de la inserción

    # Procesar los productos recibidos en la venta
    for item in productos:
        producto_id = item['producto_id']
        cantidad = item['cantidad']
        precio_unitario = float(item['precio_venta']) 

        # Calcular la venta total para el detalle (cantidad * precio_unitario)
        venta_total = cantidad * precio_unitario
        valor_total_venta += venta_total  

        # Crear un registro en la tabla "ventas_detalle"
        detalle = VentaDetalle(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            venta_total=venta_total
        )
        detalles_venta.append(detalle)

        # Actualizar el stock
        stock = Stock.query.filter_by(producto_id=producto_id).first()
        if stock:
            stock.cantidad -= cantidad

    # Crear el registro de la venta
    nueva_venta = Venta(
        cliente_id=cliente_id,
        venta_total=valor_total_venta,
        fecha=datetime.now()
    )
    db.session.add(nueva_venta)
    db.session.flush()  # Generar el ID de la venta sin hacer commit aún

    # Asignar `venta_id` a los detalles y agregarlos a la sesión
    for detalle in detalles_venta:
        detalle.venta_id = nueva_venta.id
        db.session.add(detalle)

    # Registrar el movimiento en la caja
    registrar_movimiento_caja(tipo_movimiento='venta', monto=+valor_total_venta)

    # Confirmar los cambios en la base de datos
    db.session.commit()

    return jsonify({'message': 'Venta registrada exitosamente'}), 201


#Obtiene todas las ventas
@ventas_bp.route('/ventas', methods=['GET'])
def obtener_ventas():
    ventas = Venta.query.all()
    ventas_data = []
    for venta in ventas:
        detalles = VentaDetalle.query.filter_by(venta_id=venta.id).all()
        detalles_data = [
            {'producto_id': detalle.producto_id, 'cantidad': detalle.cantidad, 'precio_unitario': detalle.precio_unitario, 'venta_total': detalle.venta_total}
            for detalle in detalles
        ]
        ventas_data.append({
            'id': venta.id,
            'cliente_id': venta.cliente_id,
            'fecha': venta.fecha.isoformat(),  # Convierte la fecha a un formato ISO
            'venta_total': venta.venta_total,  
            'detalles': detalles_data
        })
    return jsonify(ventas_data), 200


#Obtiene una compra específica
@ventas_bp.route('/ventas/<int:venta_id>', methods=['GET'])
def obtener_venta(venta_id):
    venta = Venta.query.get(venta_id)
    if not venta:
        return jsonify({'error': 'Venta no encontrada'}), 404

    detalles = VentaDetalle.query.filter_by(venta_id=venta_id).all()
    detalles_data = [
        {'producto_id': detalle.producto_id, 'cantidad': detalle.cantidad, 'precio_unitario': detalle.precio_unitario, 'venta_total': detalle.venta_total}
            for detalle in detalles
    ]
    venta_data = {
        'id': venta.id,
        'cliente_id': venta.cliente_id,
        'fecha': venta.fecha.isoformat(),  # Convierte la fecha a un formato ISO
        'venta_total': venta.venta_total,
        'detalles': detalles_data
    }
    return jsonify(venta_data), 200


#Rutas para el Pivot Grid

#Obtener ventas agrupadas
@ventas_bp.route('/pivot-ventas', methods=['GET'])
def obtener_ventas_agrupadas():
    # Consulta SQL directa
    query = text("""
    WITH ventas_por_dia AS (
        SELECT 
            p.categoria AS categoria,
            p.nombre AS producto,
            v.fecha AS fecha_venta,
            SUM(dv.cantidad) AS total_unidades,
            SUM(dv.cantidad * dv.precio_unitario) AS total_venta
        FROM 
            ventas v
        JOIN 
            detalles_ventas dv ON v.id = dv.venta_id
        JOIN 
            productos p ON dv.producto_id = p.id
        GROUP BY 
            p.categoria, p.nombre, v.fecha
    ),
    ventas_por_mes AS (
        SELECT 
            DATE_TRUNC('month', v.fecha) AS mes_venta,
            SUM(dv.cantidad) AS total_unidades_mes,
            SUM(dv.cantidad * dv.precio_unitario) AS total_venta_mes
        FROM 
            ventas v
        JOIN 
            detalles_ventas dv ON v.id = dv.venta_id
        GROUP BY 
            mes_venta
    )
    SELECT 
        vd.categoria, vd.producto, vd.fecha_venta, 
        vd.total_unidades, vd.total_venta,
        vm.mes_venta, vm.total_unidades_mes, vm.total_venta_mes
    FROM 
        ventas_por_dia vd
    LEFT JOIN 
        ventas_por_mes vm ON DATE_TRUNC('month', vd.fecha_venta) = vm.mes_venta
    ORDER BY 
        vd.categoria, vd.fecha_venta;
    """)
    
    # Ejecutar la consulta SQL
    result = db.session.execute(query).fetchall()
    
    # Formatear los resultados en una lista de diccionarios
    ventas_agrupadas = [
        {
            "categoria": row[0],
            "producto": row[1],
            "fecha_venta": row[2].strftime('%Y-%m-%d'),
            "total_unidades": int(row[3]),
            "total_venta": float(row[4]),
            "mes_venta": row[5].strftime('%Y-%m') if row[5] else None,  # Opcional
            "total_unidades_mes": int(row[6]) if row[6] else 0,
            "total_venta_mes": float(row[7]) if row[7] else 0.0
        }
        for row in result
    ]

    return jsonify(ventas_agrupadas)


# Obtener ventas agrupadas por mes y producto
@ventas_bp.route('/grafico-ventas', methods=['GET'])
def obtener_ventas_grafico():
    # Consulta SQL directa
    query = text("""
    SELECT 
        TO_CHAR(v.fecha, 'Month') AS fecha,
        p.nombre AS producto,
        SUM(dv.venta_total) AS total_venta
    FROM 
        ventas v
    JOIN 
        detalles_ventas dv ON v.id = dv.venta_id
    JOIN 
        productos p ON dv.producto_id = p.id
    GROUP BY 
        TO_CHAR(v.fecha, 'Month'), p.nombre
    ORDER BY 
        fecha;
    """)

    # Ejecuta la consulta y obtiene los resultados
    resultados = db.session.execute(query).fetchall()

    # Procesa los resultados en el formato deseado
    ventas_por_mes = defaultdict(dict)

    for row in resultados:
        mes = row[0].strip()       # Primer campo: 'fecha'
        producto = row[1] 
        total_venta = float(row[2])

        # Asigna el total de cada producto en el mes correspondiente
        ventas_por_mes[mes][producto] = total_venta

    # Convierte el defaultdict a un diccionario normal y agrega la fecha en cada entrada
    ventas_formateadas = [{"fecha": mes, **productos} for mes, productos in ventas_por_mes.items()]

    # Retorna los datos en formato JSON
    return jsonify(ventas_formateadas)


# Obtener productos y sus categorías
@ventas_bp.route('/productos-categorias', methods=['GET'])
def obtener_productos_categorias():
    # Consulta SQL para obtener productos con sus categorías
    query = text ("""
    SELECT 
        nombre AS producto,
        categoria
    FROM 
        productos
    ORDER BY 
        categoria, producto;
    """)

    # Ejecuta la consulta y obtiene los resultados
    resultados = db.session.execute(query).fetchall()

    # Formatea los resultados en una lista de diccionarios
    productos_categorias = [{"producto": row[0], "categoria": row[1]} for row in resultados]

    return jsonify(productos_categorias)