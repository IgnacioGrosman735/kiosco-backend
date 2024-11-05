from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import Caja, db


# Crea el Blueprint para caja
caja_bp = Blueprint('caja', __name__)

@caja_bp.route('/caja', methods=['GET'])
def obtener_registros_caja():
    # Obtener todos los registros de la tabla Caja
    registros_caja = Caja.query.order_by(Caja.fecha.desc()).all()

    # Serializar los registros
    resultados = [
        {'id': registro.id,
         'tipo_movimiento': registro.tipo_movimiento,
         'monto': registro.monto,
         'saldo': registro.saldo, 
         'fecha': registro.fecha}
        for registro in registros_caja
    ]

    return jsonify(resultados)

from flask import request

@caja_bp.route('/caja/filtrar', methods=['GET'])
def obtener_registros_por_rango():
    fecha_inicio = request.args.get('fechaInicio')
    fecha_fin = request.args.get('fechaFin')

    # Eliminar la "Z" y convertir las fechas
    fecha_inicio = datetime.fromisoformat(fecha_inicio[:-1])  # Elimina la "Z"
    fecha_fin = datetime.fromisoformat(fecha_fin[:-1])        # Elimina la "Z"

    # Obtener registros en el rango de fechas
    registros_caja = Caja.query.filter(Caja.fecha >= fecha_inicio, Caja.fecha <= fecha_fin).order_by(Caja.fecha.desc()).all()

    # Serializar los registros
    resultados = [
        {'id': registro.id,
         'tipo_movimiento': registro.tipo_movimiento,
         'monto': registro.monto,
         'saldo': registro.saldo, 
         'fecha': registro.fecha}
        for registro in registros_caja
    ]

    return jsonify(resultados)



""" @caja_bp.route('/caja/add-initial', methods=['POST'])
def agregar_saldo_inicial():
    # Definimos el saldo inicial que quieres agregar
    saldo_inicial = 100000

    # Creamos el movimiento para agregar el saldo a la caja
    nuevo_movimiento_caja = Caja(
        tipo_movimiento="saldo_inicial",  # Definimos el tipo de movimiento
        monto=saldo_inicial,              # Monto que corresponde al saldo inicial
        saldo=saldo_inicial,              # Saldo total después de la transacción
        fecha=datetime.now()              # Fecha actual
    )
    db.session.add(nuevo_movimiento_caja)
    db.session.commit()

    return jsonify({'message': 'Saldo inicial agregado a la caja exitosamente'}), 200 """

def registrar_movimiento_caja(tipo_movimiento, monto):
    # Obtener el último saldo registrado
    ultimo_movimiento = Caja.query.order_by(Caja.fecha.desc()).first()
    saldo_actual = float(ultimo_movimiento.saldo if ultimo_movimiento else 0)  # Si no hay movimientos previos, saldo 0

    # Calcular el nuevo saldo
    nuevo_saldo = saldo_actual + float(monto)

    # Crear un nuevo registro en la tabla "caja"
    nuevo_movimiento_caja = Caja(
        tipo_movimiento=tipo_movimiento,
        monto=monto,
        saldo=nuevo_saldo,
        fecha=datetime.now()
    )
    
    db.session.add(nuevo_movimiento_caja)
    db.session.commit()
