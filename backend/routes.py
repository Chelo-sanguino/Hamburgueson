from flask import Blueprint, request, jsonify
from models import db, Caja, Producto, Venta, DetalleVenta, Extra
from datetime import datetime
from sqlalchemy import func, extract
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import simpleSplit
import io

api_bp = Blueprint('api', __name__)


# --- CONTROL DE CAJA ---
@api_bp.route('/caja/abrir', methods=['POST'])
def abrir_caja():
    # Verificamos si ya hay una caja abierta
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    if caja_abierta:
        # Si ya existe una, devolvemos un mensaje informativo en lugar de error
        return jsonify({"mensaje": "La caja ya se encuentra abierta", "id": caja_abierta.id}), 200
    
    monto_inicial = request.json.get('monto_inicial', 0.0)
    nueva_caja = Caja(monto_inicial=monto_inicial, estado='Abierta')
    db.session.add(nueva_caja)
    db.session.commit()
    
    return jsonify({"mensaje": "Caja abierta correctamente", "id": nueva_caja.id}), 201

@api_bp.route('/caja/estado', methods=['GET'])
def estado_caja():
    # Buscamos si hay alguna caja abierta en este momento
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    
    if caja_abierta:
        return jsonify({"abierta": True, "monto_inicial": caja_abierta.monto_inicial}), 200
    else:
        return jsonify({"abierta": False}), 200

# --- CONTROL DE VENTAS ---
@api_bp.route('/venta/nueva', methods=['POST'])
def nueva_venta():
    # 1. Validar que la caja esté abierta
    caja_activa = Caja.query.filter_by(estado='Abierta').first()
    if not caja_activa:
        return jsonify({"error": "No se puede registrar ventas con la caja cerrada"}), 400

    datos = request.json
    total_venta = 0
    
    # 2. Generar número de pedido correlativo
    ultimo_pedido = Venta.query.order_by(Venta.id.desc()).first()
    nuevo_num_pedido = (ultimo_pedido.numero_pedido + 1) if ultimo_pedido else 1

    nueva_venta = Venta(
        numero_pedido=nuevo_num_pedido,
        total=0, # Se actualiza al final
        metodo_pago=datos.get('metodo_pago', 'Efectivo'),
        caja_id=caja_activa.id
    )
    db.session.add(nueva_venta)
    db.session.flush() # Para obtener el ID de la venta antes de procesar detalles

    # 3. Procesar los productos enviados desde el frontend
    for item in datos.get('productos', []):
        prod = Producto.query.get(item['id'])
        if not prod:
            continue

        precio_unitario_final = prod.precio_base
        
        detalle = DetalleVenta(
            venta_id=nueva_venta.id,
            producto_id=prod.id,
            cantidad=item['cantidad'],
            observaciones=item.get('observaciones', ''),
            subtotal=0 
        )

        # 4. Procesar Extras e incrementar el precio
        for extra_id in item.get('extras', []):
            ext = Extra.query.get(extra_id)
            if ext:
                precio_unitario_final += ext.precio
                detalle.extras.append(ext)

        # Cálculo final del renglón
        detalle.subtotal = precio_unitario_final * item['cantidad']
        total_venta += detalle.subtotal
        db.session.add(detalle)

    # 5. Guardar total final de la venta
    nueva_venta.total = total_venta
    db.session.commit()

    return jsonify({
        "mensaje": "Venta registrada con éxito", 
        "pedido_nro": nuevo_num_pedido, 
        "total": total_venta,
        "venta_id": nueva_venta.id 
    }), 201
@api_bp.route('/venta/ticket/<int:venta_id>', methods=['GET'])
def imprimir_ticket(venta_id):
    venta = Venta.query.get(venta_id)
    if not venta:
        return jsonify({"error": "Venta no encontrada"}), 404

    ancho = 58 * mm
    # MEJORA: Aumentamos a 25 * mm por producto para dar más espacio a los Combos y Salsas
    alto = (70 + (len(venta.detalles) * 28)) * mm 
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    
    dibujar_contenido_ticket(c, venta, ancho, alto, modo="cliente")
    c.showPage() 
    dibujar_contenido_ticket(c, venta, ancho, alto, modo="cocina")
    c.showPage() 

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

# FUNCIÓN AUXILIAR PARA EVITAR REPETIR CÓDIGO
def dibujar_contenido_ticket(c, venta, ancho, alto, modo="cliente"):
    y = alto - 10 * mm
    
    titulo = "HAMBURGUESON" if modo == "cliente" else "--- COCINA ---"
    c.setFont("Helvetica-Bold", 12 if modo == "cocina" else 10)
    c.drawCentredString(ancho/2, y, titulo)
    
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 11 if modo == "cocina" else 8)
    c.drawCentredString(ancho/2, y, f"Pedido #: {venta.numero_pedido}")
    
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(5 * mm, y, f"Fecha: {venta.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
    y -= 4 * mm
    c.drawString(5 * mm, y, "-" * 35)
    y -= 6 * mm

    for detalle in venta.detalles:
        prod = Producto.query.get(detalle.producto_id)
        
        texto_prod = f"{detalle.cantidad}x {prod.nombre}"
        fuente_p = "Helvetica-Bold"
        # MEJORA: Letra más grande para cocina
        tamano_p = 11 if modo == "cocina" else 9
        
        ancho_texto = ancho - (22 * mm if modo == "cliente" else 5 * mm)
        lineas = simpleSplit(texto_prod, fuente_p, tamano_p, ancho_texto)
        
        y_ini = y
        for linea in lineas:
            c.setFont(fuente_p, tamano_p)
            c.drawString(5 * mm, y, linea)
            y -= 4 * mm

        if modo == "cliente":
            c.setFont("Helvetica-Bold", 9)
            # MEJORA: Alineación exacta del subtotal
            c.drawRightString(ancho - 5 * mm, y_ini, f"{detalle.subtotal:.2f}")

        # Salsas y Extras
        if detalle.extras:
            y -= 1 * mm
            for extra in detalle.extras:
                c.setFont("Helvetica-Oblique", 7 if modo == "cliente" else 8)
                c.drawString(8 * mm, y, f"+ {extra.nombre}")
                y -= 3.5 * mm
            
        # Observaciones
        if detalle.observaciones:
            c.setFont("Helvetica-BoldOblique", 8 if modo == "cocina" else 7)
            # Resaltamos visualmente la nota para el chef
            c.drawString(8 * mm, y, f"NOTA: {detalle.observaciones}")
            y -= 4 * mm
        
        y -= 4 * mm # Espacio extra entre productos distintos

    # Pie del Ticket
    if modo == "cliente":
        c.drawString(5 * mm, y, "=" * 35)
        y -= 6 * mm
        c.setFont("Helvetica-Bold", 12) 
        c.drawString(5 * mm, y, "TOTAL:")
        c.drawRightString(ancho - 5 * mm, y, f"{venta.total:.2f} Bs.")
        
        # --- NUEVO: IMPRIMIR EL MÉTODO DE PAGO ---
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5 * mm, y, f"PAGO: {venta.metodo_pago.upper()}")
        
        y -= 8 * mm
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(ancho/2, y, "¡Gracias por su preferencia!")
    else:
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(ancho/2, y, "--- FIN DE ORDEN ---")

@api_bp.route('/stats/mensual', methods=['GET'])
def estadisticas_mensuales():
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

   # 1. Calcular Ganancia Total del Mes
    ganancia_total = db.session.query(func.sum(Venta.total)).filter(
        extract('month', Venta.fecha_hora) == mes_actual,
        extract('year', Venta.fecha_hora) == anio_actual
    ).scalar() or 0.0

    # 2. Ranking de todos los productos
    stats = db.session.query(
        Producto.nombre, 
        func.sum(DetalleVenta.cantidad).label('total_vendido'),
        Producto.es_semanal
    ).join(DetalleVenta).join(Venta).filter(
        extract('month', Venta.fecha_hora) == mes_actual,
        extract('year', Venta.fecha_hora) == anio_actual
    ).group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).all()

    if not stats:
        return jsonify({"mensaje": "Sin datos", "ganancia_total": 0}), 200

    # 3. Filtrar el especial semanal más pedido
    especiales = [s for s in stats if s[2] == True]
    top_semanal = especiales[0] if especiales else ("Ninguno", 0)

    return jsonify({
        "ganancia_total": round(ganancia_total, 2),
        "mas_vendido": {"nombre": stats[0][0], "cantidad": stats[0][1]},
        "menos_vendido": {"nombre": stats[-1][0], "cantidad": stats[-1][1]},
        "top_semanal": {"nombre": top_semanal[0], "cantidad": top_semanal[1]}
    })

@api_bp.route('/producto/semanal', methods=['GET'])
def obtener_semanal():
    hamburguesa = Producto.query.filter_by(es_semanal=True).first()
    if not hamburguesa:
        return jsonify({"error": "No hay una hamburguesa semanal asignada"}), 404
    
    return jsonify({
        "nombre": hamburguesa.nombre,
        "precio": hamburguesa.precio_base
    })

@api_bp.route('/admin/configurar-semanal', methods=['POST'])
def configurar_semanal():
    datos = request.json
    nombre = datos.get('nombre')
    precio = datos.get('precio')

    if not nombre or precio is None:
        return jsonify({"error": "Faltan datos (nombre o precio)"}), 400

    try:
        # 1. Quitamos la estrella a TODOS de forma explícita
        productos_semanales = Producto.query.filter_by(es_semanal=True).all()
        for p in productos_semanales:
            p.es_semanal = False
        
        # 2. Buscamos el producto por nombre (exacto)
        hamburguesa = Producto.query.filter_by(nombre=nombre).first()

        if hamburguesa:
            hamburguesa.precio_base = precio
            hamburguesa.es_semanal = True
        else:
            # Si no existe, lo creamos de cero
            hamburguesa = Producto(
                nombre=nombre, 
                precio_base=precio, 
                categoria="Hamburguesas", 
                es_semanal=True
            )
            db.session.add(hamburguesa)

        # 3. FORZAMOS EL COMMIT
        db.session.commit()
        return jsonify({"mensaje": f"¡{nombre} ahora es el especial semanal!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api_bp.route('/productos', methods=['GET'])
def listar_productos():
    # Filtrar para que solo devuelva los que tienen activo=True
    productos = Producto.query.filter_by(activo=True).all()
    return jsonify([{
        "id": p.id,
        "nombre": p.nombre,
        "precio": p.precio_base,
        "categoria": p.categoria,
        "es_semanal": p.es_semanal
    } for p in productos])

@api_bp.route('/productos', methods=['POST'])
def crear_producto():
    datos = request.json
    nuevo = Producto(
        nombre=datos['nombre'],
        precio_base=datos['precio'],
        categoria=datos.get('categoria', 'Varios'),
        es_semanal=False
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Producto creado con éxito"}), 201


@api_bp.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    datos = request.json
    producto.nombre = datos.get('nombre', producto.nombre)
    producto.precio_base = datos.get('precio', producto.precio_base)
    producto.categoria = datos.get('categoria', producto.categoria)
    
    db.session.commit()
    return jsonify({"mensaje": "Producto actualizado correctamente"})

# ELIMINAR PRODUCTO
@api_bp.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    try:
        # Intentamos borrarlo físicamente de la base de datos
        db.session.delete(producto)
        db.session.commit()
        return jsonify({"mensaje": "Producto eliminado definitivamente"})
    except:
        # Si da error (porque ya se vendió antes), hacemos el "Borrado Lógico"
        db.session.rollback()
        producto.activo = False
        producto.es_semanal = False # Le quitamos la estrella por si acaso
        db.session.commit()
        return jsonify({"mensaje": "Producto archivado correctamente (ya tenía ventas registradas)"}), 200
    
# --- GESTIÓN DE EXTRAS ---
@api_bp.route('/extras', methods=['GET'])
def listar_extras():
    extras = Extra.query.all()
    return jsonify([{
        "id": e.id,
        "nombre": e.nombre,
        "precio": e.precio
    } for e in extras])

@api_bp.route('/extras', methods=['POST'])
def crear_extra():
    datos = request.json
    nuevo = Extra(nombre=datos['nombre'], precio=datos['precio'])
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Extra creado"}), 201

@api_bp.route('/caja/cerrar', methods=['POST'])
def cerrar_caja():
    caja = Caja.query.filter_by(estado='Abierta').first()
    if not caja:
       return jsonify({
        "mensaje": "Caja cerrada exitosamente",
        "caja_id": caja.id, # <-- ESTA LÍNEA ES NUEVA Y VITAL
        "resumen": {
            "inicial": caja.monto_inicial,
            "ventas_efectivo": total_efectivo,
            "ventas_qr": total_qr,
            "ventas_tarjeta": total_tarjeta,
            "total_en_caja": monto_final_esperado
        }
    }), 200

    # 1. Calculamos totales por método de pago
    ventas = Venta.query.filter_by(caja_id=caja.id).all()
    
    total_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'Efectivo')
    total_qr = sum(v.total for v in ventas if v.metodo_pago == 'QR')
    total_tarjeta = sum(v.total for v in ventas if v.metodo_pago == 'Tarjeta') # Futuro
    
    monto_final_esperado = caja.monto_inicial + total_efectivo

    # 2. Cerramos la caja
    caja.estado = 'Cerrada'
    caja.fecha_cierre = datetime.now()
    # Guardamos el desglose en un campo de notas o similar si tu modelo lo permite
    db.session.commit()

    return jsonify({
        "mensaje": "Caja cerrada exitosamente",
        "caja_id": caja.id, 
        "resumen": {
            "inicial": caja.monto_inicial,
            "ventas_efectivo": total_efectivo,
            "ventas_qr": total_qr,
            "ventas_tarjeta": total_tarjeta,
            "total_en_caja": monto_final_esperado
        }
    }), 200

@api_bp.route('/caja/ticket_cierre/<int:caja_id>', methods=['GET'])
def imprimir_ticket_cierre(caja_id):
    caja = Caja.query.get(caja_id)
    if not caja:
        return jsonify({"error": "Caja no encontrada"}), 404

    # Recalculamos los totales de esa caja específica
    ventas = Venta.query.filter_by(caja_id=caja.id).all()
    total_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'Efectivo')
    total_qr = sum(v.total for v in ventas if v.metodo_pago == 'QR')
    total_ventas = total_efectivo + total_qr
    monto_esperado = caja.monto_inicial + total_efectivo

    # Lienzo de 58mm para tu impresora Knup
    ancho = 58 * mm
    alto = 120 * mm 
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    # --- DISEÑO DEL TICKET DE CIERRE ---
    y = alto - 10 * mm  # <--- AQUÍ NACE LA VARIABLE 'y'
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(ancho/2, y, "CIERRE DE TURNO")

    y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(5 * mm, y, f"Apertura: {caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')}")
    y -= 4 * mm
    c.drawString(5 * mm, y, f"Cierre: {caja.fecha_cierre.strftime('%d/%m/%Y %H:%M')}")
    y -= 4 * mm
    c.drawString(5 * mm, y, "-" * 35)

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5 * mm, y, "DESGLOSE DE INGRESOS:")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(5 * mm, y, "Fondo Inicial:")
    c.drawRightString(ancho - 5 * mm, y, f"{caja.monto_inicial:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "Ventas en Efectivo:")
    c.drawRightString(ancho - 5 * mm, y, f"+ {total_efectivo:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "Ventas por QR:")
    c.drawRightString(ancho - 5 * mm, y, f"+ {total_qr:.2f}")

    y -= 5 * mm
    c.drawString(5 * mm, y, "-" * 35)

    # --- PARTE FINAL CORREGIDA ---
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5 * mm, y, "TOTAL VENTAS:")
    c.drawRightString(ancho - 5 * mm, y, f"{total_ventas:.2f} Bs.")

    y -= 6 * mm
    c.drawString(5 * mm, y, "=" * 35)
    
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(ancho/2, y, "EFECTIVO A ENTREGAR")
    
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 14) 
    c.drawCentredString(ancho/2, y, f"> {monto_esperado:.2f} Bs. <")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')