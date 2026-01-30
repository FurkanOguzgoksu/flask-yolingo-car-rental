from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import db.admin as db_admin
import db.vehicles as db_vehicles
import db.reviews as db_reviews
from utils.file_utils import allowed_file

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    
    istatistik = db_admin.get_dashboard_stats()
    son_islemler, musteriler, uyarilar = db_admin.get_dashboard_tables()
    
    finans = db_admin.get_finansal_detaylar()
    
    return render_template('admin/dashboard.html', 
                           istatistik=istatistik, 
                           son_islemler=son_islemler,  
                           musteriler=musteriler, 
                           uyarilar=uyarilar,
                           marka_isimleri=istatistik.get('marka_isimleri', []), 
                           marka_sayilari=istatistik.get('marka_sayilari', []),
                           finans_aylar=finans['aylar'],
                           finans_gelirler=finans['gelirler'],
                           finans_giderler=finans['giderler'])

@bp.route('/database', methods=['GET', 'POST'])
def database():
    """Veritabanı yönetimi"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    tables = db_admin.get_all_table_names()
    secilen_tablo = request.args.get('tablo')
    columns, rows = [], []
    if secilen_tablo:
        columns, rows = db_admin.get_table_data(secilen_tablo)
    return render_template('admin/database.html', tables=tables, secilen_tablo=secilen_tablo, columns=columns, rows=rows)

@bp.route('/run-sql', methods=['POST'])
def run_sql():
    """SQL sorgusu çalıştır"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return jsonify({'status': 'error', 'message': 'Yetkisiz işlem'})
    result = db_admin.run_custom_sql(request.form.get('query'))
    return jsonify(result)

@bp.route('/arac-ekle', methods=['GET', 'POST'])
def arac_ekle():
    """Araç ekleme"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    if request.method == 'GET': 
        return render_template('admin/arac_ekle.html', 
                               sehirler=db_vehicles.get_sehirler(), 
                               kategoriler=db_vehicles.get_kategoriler())
    if request.method == 'POST':
        resim_url = 'default_car.jpg'
        if 'resim' in request.files:
            file = request.files['resim']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                resim_url = filename
        arac_bilgi = {
            'plaka': request.form['plaka'], 
            'marka': request.form['marka'], 
            'model': request.form['model'], 
            'yil': request.form['yil'], 
            'yakit': request.form['yakit_turu'], 
            'vites': request.form['vites_turu'], 
            'ucret': request.form['gunluk_ucret'], 
            'sehir': request.form['sehir_id'], 
            'kategori': request.form['kategori_id'], 
            'resim': resim_url
        }
        sigorta_bilgi = {
            'sirket': request.form['sigorta_sirketi'], 
            'police': request.form['police_no'], 
            'baslangic': request.form['sigorta_baslangic'], 
            'bitis': request.form['sigorta_bitis']
        }
        if db_vehicles.add_arac_ve_sigorta(arac_bilgi, sigorta_bilgi): 
            flash("Araç eklendi!", 'success')
        else: 
            flash("Hata!", 'danger')
        return redirect(url_for('admin.dashboard'))

@bp.route('/teslim-al/<int:kiralama_id>')
def teslim_al(kiralama_id):
    """Araç teslim alma"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    if db_vehicles.teslim_al_arac(kiralama_id): 
        flash('Araç teslim alındı.', 'success')
    else: 
        flash('Hata!', 'danger')
    return redirect(url_for('admin.dashboard'))

@bp.route('/sigortalar')
def sigortalar():
    """Sigorta listesi"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    return render_template('admin/sigortalar.html', sigortalar=db_admin.get_all_sigortalar())

@bp.route('/sigorta-guncelle/<int:sigorta_id>', methods=['GET', 'POST'])
def sigorta_guncelle(sigorta_id):
    """Sigorta güncelleme"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        if db_admin.update_sigorta(sigorta_id, {
            'sirket': request.form['sigorta_sirketi'], 
            'baslangic': request.form['baslangic_tarihi'], 
            'bitis': request.form['bitis_tarihi'], 
            'police': request.form['police_no']
        }):
            flash('Güncellendi.', 'success')
            return redirect(url_for('admin.sigortalar'))
    return render_template('admin/sigorta_duzenle.html', sigorta=db_admin.get_sigorta_by_id(sigorta_id))

@bp.route('/bakim', methods=['GET', 'POST'])
def bakim():
    """Bakım yönetimi"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        personel_id = request.form.get('personel_id') 

        if db_admin.add_bakim(
            request.form.get('arac_id'), 
            personel_id,
            request.form.get('neden'), 
            request.form.get('maliyet'), 
            request.form.get('tarih')
        ):
            flash("Bakım kaydı başarıyla oluşturuldu.", "success")
        else: 
            flash("Kayıt sırasında bir hata oluştu.", "danger")
        
        return redirect(url_for('admin.bakim'))

    return render_template('admin/bakim.html', 
                           bakimlar=db_admin.get_bakim_listesi(), 
                           araclar=db_vehicles.get_tum_araclar(),
                           personeller=db_admin.get_personeller())

@bp.route('/bakim-bitir/<int:bakim_id>')
def bakim_bitir(bakim_id):
    """Bakım tamamlama"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    if db_admin.finish_bakim(bakim_id): 
        flash("Bakım tamamlandı.", "success")
    else: 
        flash("Hata.", "danger")
    return redirect(url_for('admin.bakim'))

@bp.route('/takvim')
def takvim():
    """Takvim görünümü"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    return render_template('admin/takvim.html')

@bp.route('/api/calendar-events')
def api_calendar_events():
    """Takvim eventleri API"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return jsonify([])
    
    events = db_admin.get_calendar_events()
    
    formatted = []
    for e in events:
        baslik = f"{e['ad']} {e['soyad']} | {e['marka']} {e['model']} ({e['plaka']})"
        
        formatted.append({
            'title': baslik, 
            'start': str(e['baslangic_tarihi']), 
            'end': str(e['bitis_tarihi']), 
            'color': '#ffc107' if e['durum']=='Onaylandı' else ('#198754' if e['durum']=='Kirada' else '#6c757d'),
            'extendedProps': {
                'musteri': f"{e['ad']} {e['soyad']}",
                'arac': f"{e['marka']} {e['model']}",
                'plaka': e['plaka'],
                'durum': e['durum']
            }
        })
        
    return jsonify(formatted)

@bp.route('/yorumlar')
def yorumlar():
    """Yorum yönetimi"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    return render_template('admin/yorumlar.html', yorumlar=db_reviews.get_tum_yorumlar_admin())

@bp.route('/yorum-islem/<int:yorum_id>/<islem>')
def yorum_islem(yorum_id, islem):
    """Yorum işlemi (onayla/reddet/sil)"""
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
    
    admin_id = session['user_id']
    
    if db_reviews.yorum_durum_degistir(yorum_id, islem, admin_id): 
        flash("İşlem başarıyla kaydedildi.", "success")
    else: 
        flash("Hata oluştu.", "danger")
        
    return redirect(url_for('admin.yorumlar'))
