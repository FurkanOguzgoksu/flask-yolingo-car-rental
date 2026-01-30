from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import db.customers as db_customers
import db.favorites as db_favorites
import db.reviews as db_reviews
import db.auth as db_auth
from utils.file_utils import allowed_file

bp = Blueprint('customer', __name__)

@bp.route('/profil', methods=['GET', 'POST'])
def profil():
    """Müşteri profil sayfası"""
    if 'user_id' not in session or session.get('role') != 'musteri':
        return redirect(url_for('auth.login'))

    musteri_id = session['user_id']
    kullanici = db_customers.get_musteri_by_id(musteri_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'bilgi_guncelle':
            resim_yolu = None

            if 'profil_resim' in request.files:
                file = request.files['profil_resim']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"user_{musteri_id}_{file.filename}")
                    file.save(os.path.join(current_app.config['PROFILE_UPLOAD_FOLDER'], filename))
                    resim_yolu = filename

            if db_customers.update_musteri_profil(
                musteri_id=musteri_id,
                ad=request.form['ad'],
                soyad=request.form['soyad'],
                telefon=request.form['telefon'],
                adres=request.form['adres'],
                cinsiyet=request.form['cinsiyet'],     
                dogum=request.form['dogum_tarihi'],    
                resim=resim_yolu
            ):
                session['user_name'] = f"{request.form['ad']} {request.form['soyad']}"
                if resim_yolu:
                    session['user_img'] = resim_yolu

                flash("Profil bilgileri güncellendi.", "success")

            return redirect(url_for('customer.profil'))

        # ŞİFRE DEĞİŞTİR
        elif action == 'sifre_degistir':
            if not db_auth.check_current_password(musteri_id, request.form['eski_sifre']):
                flash("Mevcut şifre yanlış.", "danger")

            elif request.form['yeni_sifre'] != request.form['yeni_sifre_tekrar']:
                flash("Yeni şifreler uyuşmuyor.", "warning")

            else:
                yeni_hash = generate_password_hash(request.form['yeni_sifre'])
                if db_auth.update_musteri_sifre(musteri_id, yeni_hash):
                    flash("Şifre başarıyla değiştirildi.", "success")

            return redirect(url_for('customer.profil'))

    return render_template('customer/profil.html', user=kullanici)

@bp.route('/favorilerim')
def favorilerim():
    """Favori araçlar listesi"""
    if 'user_id' not in session:
        flash("Favorilerinizi görmek için giriş yapmalısınız.", "warning")
        return redirect(url_for('auth.login'))
    favori_araclar = db_favorites.get_user_favoriler_detayli(session['user_id'])
    return render_template('customer/favorilerim.html', araclar=favori_araclar)

@bp.route('/toggle-favori/<int:arac_id>', methods=['POST'])
def toggle_favori_api(arac_id):
    """Favori ekle/çıkar API"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapmalısınız'}), 401
    sonuc = db_favorites.toggle_favori(session['user_id'], arac_id)
    return jsonify(sonuc)

@bp.route('/favori-sil/<int:arac_id>')
def favori_sil(arac_id):
    """Favori sil"""
    if 'user_id' not in session:
        flash("Giriş yapmalısınız.", "warning")
        return redirect(url_for('auth.login'))
    
    db_favorites.delete_favori(session['user_id'], arac_id)
    
    flash("Araç favorilerden kaldırıldı.", "success")
    return redirect(url_for('customer.favorilerim'))

@bp.route('/yorum-yap', methods=['POST'])
def yorum_yap():
    """Yorum yapma"""
    if 'user_id' not in session or session.get('role') != 'musteri':
        flash("Yorum yapmak için müşteri girişi yapmalısınız.", "warning")
        return redirect(url_for('auth.login'))
    
    metin = request.form.get('yorum_metni')
    puan = request.form.get('puan')
    
    if db_reviews.add_yorum(session['user_id'], metin, puan):
        flash("Yorumunuz alındı! Yönetici onayından sonra yayınlanacaktır.", "success")
    else:
        flash("Bir hata oluştu.", "danger")
        
    return redirect(url_for('index'))
