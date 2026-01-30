import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import config
from utils.email_utils import mail
import blueprints.auth as auth_bp
import blueprints.rental as rental_bp
import blueprints.customer as customer_bp
import blueprints.admin as admin_bp
import db.vehicles as db_vehicles
import db.favorites as db_favorites
import db.reviews as db_reviews

# Flask uygulamasını oluştur
env = os.getenv('FLASK_ENV', 'development')
config_class = config.get(env, config['default'])

app = Flask(__name__)
app.config.from_object(config_class)

# Mail'i başlat
mail.init_app(app)

# Upload klasörlerini oluştur
config_class.init_app(app)

# Serializer'ı başlat (şifre sıfırlama için)
auth_bp.init_serializer(app.secret_key)

# Blueprintleri kaydet
app.register_blueprint(auth_bp.bp)
app.register_blueprint(rental_bp.bp)
app.register_blueprint(customer_bp.bp)
app.register_blueprint(admin_bp.bp)

# ==========================================
#            ANA SAYFA ROTASI
# ==========================================

@app.route('/')
def index():
    """Ana sayfa"""
    sehir_id = request.args.get('sehir_id')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')
    vites = request.args.get('vites')
    yakit = request.args.get('yakit')

    if sehir_id == "": sehir_id = None
    if vites == "": vites = None
    if yakit == "": yakit = None
    
    try:
        min_fiyat = request.args.get('min_fiyat')
        min_fiyat = int(min_fiyat) if min_fiyat else 0
    except ValueError:
        min_fiyat = 0

    try:
        max_fiyat = request.args.get('max_fiyat')
        max_fiyat = int(max_fiyat) if max_fiyat else 100000
    except ValueError:
        max_fiyat = 100000
    
    sehirler = db_vehicles.get_sehirler()
    
    araclar = db_vehicles.get_tum_araclar(
        sehir_id=sehir_id, 
        baslangic=baslangic, 
        bitis=bitis,
        vites=vites,
        yakit=yakit,
        min_fiyat=min_fiyat,
        max_fiyat=max_fiyat
    )

    random.shuffle(araclar) # --- LİSTEYİ KARIŞTIR ---
    
    yorumlar = db_reviews.get_onayli_yorumlar()
    
    fav_ids = []
    if 'user_id' in session:
        fav_ids = db_favorites.get_user_favori_ids(session['user_id'])
    
    return render_template('index.html', araclar=araclar, sehirler=sehirler, secilen_sehir_id=sehir_id, yorumlar=yorumlar, fav_ids=fav_ids)

if __name__ == '__main__':
    app.run(debug=True)