from db.connection import get_db_connection

def add_yorum(mid, metin, puan):
    """Yeni yorum ekler"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Yorum (musteri_id, yorum_metni, puan, durum) VALUES (%s,%s,%s,'Bekliyor')", 
                       (mid, metin, puan))
        conn.commit()
        return True
    except: 
        return False
    finally: 
        conn.close()

def get_onayli_yorumlar():
    """Onaylanmış yorumları getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT y.*, 
               MAX(m.ad) as ad, 
               MAX(LEFT(m.soyad, 1)) as soyad_bas_harf, 
               MAX(m.ProfilResim) as ProfilResim, 
               MAX(s.sehir_ad) as sehir_ad 
        FROM Yorum y 
        JOIN Musteri m ON y.musteri_id = m.musteri_id 
        LEFT JOIN kiralama r ON r.musteri_id = m.musteri_id 
        LEFT JOIN Arac a ON r.arac_id = a.arac_id
        LEFT JOIN Sehir s ON a.bulundugu_sehir_id = s.sehir_id
        WHERE y.durum = 'Onaylandı' 
        GROUP BY y.yorum_id 
        ORDER BY y.tarih DESC LIMIT 6
    """
    cursor.execute(sql)
    res = cursor.fetchall()
    conn.close()
    return res

def get_tum_yorumlar_admin():
    """Admin için tüm yorumları getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT y.*, 
               m.ad, m.soyad, 
               p.ad AS admin_ad, p.soyad AS admin_soyad
        FROM Yorum y 
        JOIN Musteri m ON y.musteri_id = m.musteri_id 
        LEFT JOIN Personel p ON y.islem_yapan_personel_id = p.personel_id
        ORDER BY COALESCE(y.islem_tarihi, y.tarih) DESC
    """
    
    cursor.execute(sql)
    res = cursor.fetchall()
    conn.close()
    return res

def yorum_durum_degistir(yid, islem, admin_id):
    """Yorum durumunu değiştirir (onayla/reddet/sil)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yeni_durum = None
        
        if islem == 'onayla':
            yeni_durum = 'Onaylandı'
        elif islem == 'reddet': 
            yeni_durum = 'Reddedildi'
        
        if yeni_durum:
            sql = """
                UPDATE Yorum 
                SET durum = %s, 
                    islem_yapan_personel_id = %s, 
                    islem_tarihi = NOW() 
                WHERE yorum_id = %s
            """
            cursor.execute(sql, (yeni_durum, admin_id, yid))
            
        elif islem == 'sil':
            cursor.execute("DELETE FROM Yorum WHERE yorum_id = %s", (yid,))

        conn.commit()
        return True
    except Exception as e: 
        print(f"Yorum İşlem Hatası: {e}")
        return False
    finally: 
        conn.close()
