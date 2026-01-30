from werkzeug.security import check_password_hash, generate_password_hash
from db.connection import get_db_connection

def check_user_login(eposta, sifre):
    """
    Kullanıcı girişi kontrolü (Admin veya Müşteri)
    
    Returns:
        dict: {'type': 'admin'/'musteri', 'data': user_data} veya None
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Önce Personel (Admin) Kontrolü
    cursor.execute("SELECT * FROM Personel WHERE eposta = %s", (eposta,))
    admin = cursor.fetchone()
    if admin and check_password_hash(admin['sifre'], sifre):
        conn.close()
        return {'type': 'admin', 'data': admin}
    
    # Sonra Müşteri Kontrolü
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s", (eposta,))
    musteri = cursor.fetchone()
    if musteri and check_password_hash(musteri['sifre'], sifre):
        conn.close()
        return {'type': 'musteri', 'data': musteri}
    
    conn.close()
    return None

def check_email_exists(eposta):
    """E-posta adresinin sistemde kayıtlı olup olmadığını kontrol eder"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s", (eposta,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_password_by_email(eposta, yeni_sifre):
    """E-posta ile şifre günceller"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(yeni_sifre)
        cursor.execute("UPDATE Musteri SET sifre = %s WHERE eposta = %s", (hashed, eposta))
        conn.commit()
        return True
    except: 
        return False
    finally: 
        conn.close()

def register_musteri(bilgiler):
    """Yeni müşteri kaydı oluşturur"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s OR tc_kimlik_no = %s", 
                   (bilgiler['eposta'], bilgiler['tc_no']))
    existing = cursor.fetchone()
    if existing: 
        conn.close()
        return False
    
    hashed = generate_password_hash(bilgiler['sifre'])
    
    sql = """INSERT INTO Musteri (ad, soyad, eposta, telefon, sifre, adres, ehliyet_no, tc_kimlik_no, cinsiyet, dogum_tarihi, ProfilResim) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'default_user.png')"""
    
    val = (
        bilgiler['ad'], 
        bilgiler['soyad'], 
        bilgiler['eposta'], 
        bilgiler['telefon'], 
        hashed, 
        bilgiler['adres'], 
        bilgiler['ehliyet'], 
        bilgiler['tc_no'], 
        bilgiler['cinsiyet'], 
        bilgiler['dogum']
    )
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return True
    except Exception as e:
        print(f"Kayıt Veritabanı Hatası: {e}")
        return False
    finally:
        conn.close()

def check_current_password(mid, sifre):
    """Mevcut şifrenin doğru olup olmadığını kontrol eder"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sifre FROM Musteri WHERE musteri_id = %s", (mid,))
    user = cursor.fetchone()
    conn.close()
    return check_password_hash(user['sifre'], sifre) if user else False

def update_musteri_sifre(mid, yeni_hash):
    """Müşteri şifresini günceller"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Musteri SET sifre = %s WHERE musteri_id = %s", (yeni_hash, mid))
        conn.commit()
        return True
    except: 
        return False
    finally: 
        conn.close()
