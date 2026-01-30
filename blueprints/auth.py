from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from utils.email_utils import send_email
import db.auth as db_auth

bp = Blueprint('auth', __name__)

# Serializer için (şifre sıfırlama)
serializer = None

def init_serializer(secret_key):
    """Serializer'ı başlat"""
    global serializer
    serializer = URLSafeTimedSerializer(secret_key)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi"""
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        sonuc = db_auth.check_user_login(eposta, sifre)
        if sonuc:
            session.clear()
            user = sonuc['data']
            if sonuc['type'] == 'admin':
                session['user_id'] = user['personel_id']
                session['ad'] = user['ad']
                session['role'] = 'admin'
                session['gorev'] = user['gorev']
                flash(f"Hoşgeldin {user['ad']} (Yönetici)", "success")
                return redirect(url_for('admin.dashboard'))
            else:
                session['user_id'] = user['musteri_id']
                session['user_name'] = f"{user['ad']} {user['soyad']}"
                session['user_img'] = user.get('ProfilResim', 'default_user.png')
                session['role'] = 'musteri'
                flash(f"Hoşgeldin {user['ad']}", "success")
                return redirect(url_for('index'))
        else:
            flash("E-posta veya şifre hatalı!", "danger")
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kaydı"""
    if request.method == 'POST':
        sifre = request.form.get('sifre')
        if sifre != request.form.get('confirm_sifre'):
            flash("Şifreler uyuşmuyor!", "danger")
            return redirect(url_for('auth.register'))
            
        bilgiler = {
            'ad': request.form.get('ad'), 
            'soyad': request.form.get('soyad'),
            'eposta': request.form.get('eposta'), 
            'telefon': request.form.get('telefon'),
            'tc_no': request.form.get('tc_no'),       
            'cinsiyet': request.form.get('cinsiyet'),
            'dogum': request.form.get('dogum_tarihi'), 
            'ehliyet': request.form.get('ehliyet_no'),
            'adres': request.form.get('adres'), 
            'sifre': sifre
        }
        
        if db_auth.register_musteri(bilgiler):
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("E-posta zaten kayıtlı veya bir hata oluştu!", "warning")
            
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    """Çıkış"""
    session.clear()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Şifremi unuttum"""
    if request.method == 'POST':
        eposta = request.form['eposta']
        user = db_auth.check_email_exists(eposta)
        
        if user:
            token = serializer.dumps(eposta, salt='password-reset-salt')
            link = url_for('auth.reset_password', token=token, _external=True)
            
            html_body = f"""
            <h3>Şifre Sıfırlama İsteği</h3>
            <p>Merhaba {user['ad']}, şifrenizi sıfırlamak için aşağıdaki linke tıklayın:</p>
            <a href="{link}" style="background:#16a34a; padding:10px 20px; color:#fff; text-decoration:none; font-weight:bold; border-radius:5px;">Şifremi Sıfırla</a>
            <p>Bu işlemi siz yapmadıysanız lütfen dikkate almayın.</p>
            """
            
            if send_email(eposta, "Şifre Sıfırlama - Yolingo", html_body):
                flash("Sıfırlama linki e-posta adresinize gönderildi.", "info")
            else:
                flash("E-posta gönderilemedi (SMTP Ayarlarını kontrol edin).", "warning")
        else:
            flash("Bu e-posta adresiyle kayıtlı kullanıcı bulunamadı.", "warning")
            
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Şifre sıfırlama"""
    try:
        eposta = serializer.loads(token, salt='password-reset-salt', max_age=1800)
    except:
        flash("Sıfırlama linki geçersiz veya süresi dolmuş.", "danger")
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        yeni_sifre = request.form['yeni_sifre']
        if db_auth.update_password_by_email(eposta, yeni_sifre):
            flash("Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Hata oluştu.", "danger")
            
    return render_template('auth/reset_password.html', token=token)

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin girişi (aynı login sayfası)"""
    return login()
