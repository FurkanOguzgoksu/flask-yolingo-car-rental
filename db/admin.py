from db.connection import get_db_connection

def get_dashboard_stats():
    """Admin dashboard istatistikleri"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    stats = {}
    
    cursor.execute("SELECT COUNT(*) as sayi FROM Arac")
    stats['arac'] = cursor.fetchone()['sayi']
    cursor.execute("SELECT COUNT(*) as sayi FROM Musteri")
    stats['musteri'] = cursor.fetchone()['sayi']
    
    cursor.execute("SELECT SUM(toplam_ucret) as ciro FROM kiralama WHERE durum IN ('Onaylandı', 'Tamamlandı')")
    gelir = cursor.fetchone()['ciro'] or 0
    
    cursor.execute("SELECT SUM(maliyet) as gider FROM Bakim")
    gider = cursor.fetchone()['gider'] or 0
    
    stats['bakim_gideri'] = float(gider) 
    stats['ciro'] = float(gelir) - float(gider)

    cursor.execute("""
        SELECT a.marka, COUNT(r.kiralama_id) as sayi 
        FROM kiralama r 
        JOIN Arac a ON r.arac_id=a.arac_id 
        GROUP BY a.marka 
        ORDER BY sayi DESC
        LIMIT 5
    """)
    md = cursor.fetchall()
    stats['marka_isimleri'] = [i['marka'] for i in md]
    stats['marka_sayilari'] = [i['sayi'] for i in md]
    stats['aktif'] = sum(stats['marka_sayilari'])

    cursor.execute("SELECT DATE_FORMAT(baslangic_tarihi, '%Y-%m') as ay, SUM(toplam_ucret) as toplam FROM kiralama " \
    "WHERE durum IN ('Onaylandı', 'Tamamlandı') GROUP BY ay ORDER BY ay ASC LIMIT 6")
    kd = cursor.fetchall()
    stats['ay_isimleri'] = [i['ay'] for i in kd]
    stats['aylik_kazanclar'] = [float(i['toplam']) for i in kd]
    
    conn.close()
    return stats

def get_finansal_detaylar():
    """Finansal detayları getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT DATE_FORMAT(baslangic_tarihi, '%Y-%m') as ay, SUM(toplam_ucret) as tutar 
        FROM kiralama 
        WHERE durum IN ('Onaylandı', 'Tamamlandı') 
        GROUP BY ay ORDER BY ay ASC
    """)
    gelirler_db = {row['ay']: float(row['tutar']) for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT DATE_FORMAT(giris_tarihi, '%Y-%m') as ay, SUM(maliyet) as tutar 
        FROM Bakim 
        GROUP BY ay ORDER BY ay ASC
    """)
    giderler_db = {row['ay']: float(row['tutar']) for row in cursor.fetchall()}
    
    tum_aylar = sorted(list(set(gelirler_db.keys()) | set(giderler_db.keys())))
    
    finans_data = {
        'aylar': tum_aylar,
        'gelirler': [gelirler_db.get(ay, 0) for ay in tum_aylar],
        'giderler': [giderler_db.get(ay, 0) for ay in tum_aylar]
    }
    
    conn.close()
    return finans_data

def get_dashboard_tables():
    """Dashboard tablolarını getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        (SELECT 
            'REZ' as tip,
            r.kiralama_id as id,
            r.baslangic_tarihi as tarih,
            r.durum,
            COALESCE(r.toplam_ucret, 0) as tutar,
            a.plaka, a.marka, a.model,
            CONCAT(m.ad, ' ', m.soyad) as baslik, 
            'Müşteri' as alt_baslik
        FROM kiralama r
        JOIN Arac a ON r.arac_id = a.arac_id
        JOIN Musteri m ON r.musteri_id = m.musteri_id
        WHERE r.durum IN ('Onaylandı', 'Kirada', 'Tamamlandı'))

        UNION ALL

        (SELECT 
            'BAK' as tip,
            b.bakim_id as id,
            b.giris_tarihi as tarih,
            b.durum,
            COALESCE(b.maliyet, 0) as tutar,
            a.plaka, a.marka, a.model,
            'Servis Kaydı' as baslik,
            b.bakim_nedeni as alt_baslik
        FROM Bakim b
        JOIN Arac a ON b.arac_id = a.arac_id)

        ORDER BY tarih DESC
    """
    
    cursor.execute(sql)
    son_islemler = cursor.fetchall()
    
    # Müşteriler Listesi
    cursor.execute("SELECT * FROM Musteri ORDER BY musteri_id DESC LIMIT 5")
    mus = cursor.fetchall()
    
    # Sigorta Uyarıları
    cursor.execute("SELECT a.marka, a.model, a.plaka, DATEDIFF(s.bitis_tarihi, CURDATE()) as kalan_gun FROM Arac a " \
    "JOIN Sigorta s ON a.sigorta_id=s.sigorta_id WHERE DATEDIFF(s.bitis_tarihi, CURDATE()) <= 30")
    uyar = cursor.fetchall()
    
    conn.close()
    return son_islemler, mus, uyar

def get_all_table_names():
    """Tüm tablo isimlerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    t = [r[0] for r in cursor.fetchall()]
    conn.close()
    return t

def get_table_data(t_name):
    """Tablo verilerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if not t_name.isidentifier(): 
            return [], []
        cursor.execute(f"SELECT * FROM {t_name}")
        rows = cursor.fetchall()
        cols = [i[0] for i in cursor.description]
        return cols, rows
    except: 
        return [], []
    finally: 
        conn.close()

def run_custom_sql(q):
    """SQL sorgusu çalıştırır (DİKKAT: SQL Injection riski)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q)
        if q.strip().upper().startswith("SELECT") or q.strip().upper().startswith("SHOW"):
            rows = cursor.fetchall()
            cols = [i[0] for i in cursor.description] if cursor.description else []
            conn.close()
            return {'status':'success', 'columns':cols, 'rows':rows}
        else:
            conn.commit()
            aff = cursor.rowcount
            conn.close()
            return {'status':'success', 'message': f"Etkilenen: {aff}"}
    except Exception as e:
        conn.close()
        return {'status':'error', 'message': str(e)}

def get_personeller():
    """Tüm personelleri getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Personel")
        return cursor.fetchall()
    finally:
        conn.close()

def add_bakim(aid, personel_id, neden, maliyet, tarih):
    """Bakım kaydı ekler"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Bakim (arac_id, personel_id, bakim_nedeni, maliyet, giris_tarihi, durum) 
            VALUES (%s, %s, %s, %s, %s, 'Devam Ediyor')
        """, (aid, personel_id, neden, maliyet, tarih))
        
        cursor.execute("UPDATE Arac SET durum='Bakımda' WHERE arac_id=%s", (aid,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Bakim Ekleme Hatası: {e}")
        return False
    finally: 
        conn.close()

def finish_bakim(bid):
    """Bakımı tamamlar"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT arac_id FROM Bakim WHERE bakim_id=%s", (bid,))
        rec = cursor.fetchone()
        if rec:
            cursor.execute("UPDATE Bakim SET durum='Tamamlandı', cikis_tarihi=CURDATE() WHERE bakim_id=%s", (bid,))
            cursor.execute("UPDATE Arac SET durum='Müsait' WHERE arac_id=%s", (rec['arac_id'],))
            conn.commit()
            return True
        return False
    except: 
        return False
    finally: 
        conn.close()

def get_bakim_listesi():
    """Bakım listesini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT b.*, a.plaka, a.marka, a.model, p.ad, p.soyad 
        FROM Bakim b 
        JOIN Arac a ON b.arac_id = a.arac_id
        LEFT JOIN Personel p ON b.personel_id = p.personel_id
        ORDER BY FIELD(b.durum, 'Devam Ediyor', 'Tamamlandı'), b.giris_tarihi DESC
    """
    cursor.execute(sql)
    res = cursor.fetchall()
    conn.close()
    return res

def get_calendar_events():
    """Takvim eventlerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT 
            r.kiralama_id, 
            r.baslangic_tarihi, 
            r.bitis_tarihi, 
            r.durum,
            m.ad, 
            m.soyad,
            a.plaka, 
            a.marka, 
            a.model
        FROM kiralama r
        JOIN Musteri m ON r.musteri_id = m.musteri_id
        JOIN Arac a ON r.arac_id = a.arac_id
        WHERE r.durum IN ('Onaylandı', 'Kirada', 'Tamamlandı')
    """
    cursor.execute(sql)
    res = cursor.fetchall()
    conn.close()
    return res

def get_all_sigortalar():
    """Tüm sigorta kayıtlarını getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.*, a.plaka, a.marka, a.model, a.durum as arac_durumu, DATEDIFF(s.bitis_tarihi, CURDATE()) as kalan_gun FROM Sigorta s LEFT JOIN Arac a ON s.sigorta_id = a.sigorta_id ORDER BY s.bitis_tarihi ASC")
    res = cursor.fetchall()
    conn.close()
    return res

def update_sigorta(sid, data):
    """Sigorta bilgilerini günceller"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Sigorta SET sigorta_sirketi=%s, baslangic_tarihi=%s, bitis_tarihi=%s, police_no=%s WHERE sigorta_id=%s", 
                       (data['sirket'], data['baslangic'], data['bitis'], data['police'], sid))
        conn.commit()
        return True
    except: 
        return False
    finally: 
        conn.close()

def get_sigorta_by_id(sid):
    """Sigorta bilgisini ID'ye göre getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Sigorta WHERE sigorta_id=%s", (sid,))
    res = cursor.fetchone()
    conn.close()
    return res
