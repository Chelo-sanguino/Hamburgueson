from app import app
from models import db, Extra

salsas = [
    "Miel Mostaza", "Mayonesa Casera", "Salsa Barbacoa", 
    "Salsa Verdeo", "Mostaza Especiada", "Salsa Hamburgueson", 
    "Ketchup Casero", "Salsa Picante Dulce", "Salsa Mayo-Ranch"
]

with app.app_context():
    for s in salsas:
        # 50 ml - 4 Bs
        db.session.add(Extra(nombre=f"{s} (50ml)", precio=4))
        # 100 ml - 8 Bs
        db.session.add(Extra(nombre=f"{s} (100ml)", precio=8))
    db.session.commit()
    print("¡Salsas de Hamburguesón cargadas!")