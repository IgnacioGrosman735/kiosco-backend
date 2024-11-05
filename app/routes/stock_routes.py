from flask import Blueprint, request, jsonify
from app import db
from app.models import Stock, Producto
from decimal import Decimal

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/stock', methods=['GET'])
def obtener_stock():
    # Realizamos un join entre Stock y Producto
    registros_stock = db.session.query(Stock, Producto).join(Producto, Stock.producto_id == Producto.id).all()

    # Serializamos los registros obtenidos
    resultados = [
        {
            "id": stock.id,
            "producto_id": stock.producto_id,
            "producto_nombre": producto.nombre,
            "cantidad": stock.cantidad
        }
        for stock, producto in registros_stock
    ]

    return jsonify(resultados)