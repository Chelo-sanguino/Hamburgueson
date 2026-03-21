from app import app
from models import db, Producto

menu_data = [
    # Hamburguesas Capi Bara
    {"nombre": "Capi Bara Simple", "precio": 18, "cat": "Hamburguesas"},
    {"nombre": "Capi Bara Doble", "precio": 25, "cat": "Hamburguesas"},
    # Clásicas
    {"nombre": "Clásica Junior", "precio": 22, "cat": "Hamburguesas"},
    {"nombre": "Clásica Mediana", "precio": 27, "cat": "Hamburguesas"},
    {"nombre": "Clásica Premium", "precio": 30, "cat": "Hamburguesas"},
    {"nombre": "Clásica Premium Doble", "precio": 42, "cat": "Hamburguesas"},
    # Especiales
    {"nombre": "Especial Junior", "precio": 25, "cat": "Hamburguesas"},
    {"nombre": "Especial Mediana", "precio": 30, "cat": "Hamburguesas"},
    {"nombre": "Especial Premium", "precio": 32, "cat": "Hamburguesas"},
    {"nombre": "Especial Junior Doble", "precio": 40, "cat": "Hamburguesas"},
    {"nombre": "Especial Premium Doble", "precio": 45, "cat": "Hamburguesas"},
    # Bacon & Cheese
    {"nombre": "Bacon & Cheese Mediana", "precio": 34, "cat": "Hamburguesas"},
    {"nombre": "Bacon & Cheese Premium", "precio": 39, "cat": "Hamburguesas"},
    {"nombre": "Bacon & Cheese Premium Doble", "precio": 49, "cat": "Hamburguesas"},
    # Yapada Supermacho
    {"nombre": "Supermacho Junior Doble", "precio": 39, "cat": "Hamburguesas"},
    {"nombre": "Supermacho Mediana Doble", "precio": 45, "cat": "Hamburguesas"},
    {"nombre": "Supermacho Premium Doble", "precio": 52, "cat": "Hamburguesas"},
    {"nombre": "Supermacho Super Doble 3XL", "precio": 125, "cat": "Hamburguesas"},
    # Sandwiches
    {"nombre": "Sándwich de Lomito", "precio": 40, "cat": "Sandwiches"},
    {"nombre": "Sándwich de Milanesa", "precio": 40, "cat": "Sandwiches"},
    {"nombre": "Philly Cheesesteak", "precio": 38, "cat": "Sandwiches"},
    # Papas y Sodas
    {"nombre": "Papas Cheddar", "precio": 18, "cat": "Papas"},
    {"nombre": "Porción de Papas", "precio": 10, "cat": "Papas"},
    {"nombre": "Sodas 750ml", "precio": 9, "cat": "Sodas"},
    {"nombre": "Sodas 1 lt", "precio": 12, "cat": "Sodas"},
    {"nombre": "Jugos Delis 1 lt", "precio": 12, "cat": "Jugos"}
]

with app.app_context():
    for item in menu_data:
        # Evitamos duplicados por nombre
        existente = Producto.query.filter_by(nombre=item['nombre']).first()
        if not existente:
            p = Producto(nombre=item['nombre'], precio_base=item['precio'], categoria=item['cat'])
            db.session.add(p)
    db.session.commit()
    print("¡Menú de Hamburguesón cargado con éxito!")