from datetime import datetime, date
from db.connection import get_db_connection

def get_musteri_by_id(musteri_id):
    """Müşteri ID'sine göre bilgileri getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Musteri WHERE musteri_id = %s", (musteri_id,))
    res = cursor.fetchone()
    conn.close()
    
    # Tarih objesini HTML'in anlayacağı YYYY-MM-DD formatına çevir
    if res and res['dogum_tarihi']:
        if isinstance(res['dogum_tarihi'], (datetime, date)):
            res['dogum_tarihi'] = res['dogum_tarihi'].strftime('%Y-%m-%d')
            
    return res

def update_musteri_profil(musteri_id, ad, soyad, telefon, adres, cinsiyet, dogum, resim=None):
    """Müşteri profil bilgilerini günceller"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if resim:
            sql = """
                UPDATE Musteri 
                SET ad=%s, soyad=%s, telefon=%s, adres=%s, cinsiyet=%s, dogum_tarihi=%s, ProfilResim=%s 
                WHERE musteri_id=%s
            """
            cursor.execute(sql, (ad, soyad, telefon, adres, cinsiyet, dogum, resim, musteri_id))
        else:
            sql = """
                UPDATE Musteri 
                SET ad=%s, soyad=%s, telefon=%s, adres=%s, cinsiyet=%s, dogum_tarihi=%s 
                WHERE musteri_id=%s
            """
            cursor.execute(sql, (ad, soyad, telefon, adres, cinsiyet, dogum, musteri_id))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Güncelleme Hatası: {e}")
        return False
    finally:
        conn.close()
