from flask import Flask, render_template
from models import db
from routes import api_bp

app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hamburgueson_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# IMPORTANTE: Añadimos /api para que no choque con las rutas de las páginas
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return render_template('index.html')

# --- NUEVA RUTA PARA EL DUEÑO ---
@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)