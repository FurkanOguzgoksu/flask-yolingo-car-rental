from db.connection import get_db_connection

def toggle_favori(mid, aid):
    """Favori ekler veya çıkarır"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Favori WHERE musteri_id=%s AND arac_id=%s", (mid, aid))
        ex = cursor.fetchone()
        
        if ex:
            # Varsa sil (Composite Key ile)
            cursor.execute("DELETE FROM Favori WHERE musteri_id=%s AND arac_id=%s", (mid, aid))
            action = 'removed'
        else:
            # Yoksa ekle
            cursor.execute("INSERT INTO Favori (musteri_id, arac_id) VALUES (%s,%s)", (mid, aid))
            action = 'added'
            
        conn.commit()
        return {'status':'success', 'action':action}
    except Exception as e:
        print(f"Favori Hatası: {e}")
        return {'status':'error'}
    finally: 
        conn.close()

def get_user_favori_ids(mid):
    """Kullanıcının favori araç ID'lerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT arac_id FROM Favori WHERE musteri_id=%s", (mid,))
    res = [r[0] for r in cursor.fetchall()]
    conn.close()
    return res

def get_user_favoriler_detayli(mid):
    """Kullanıcının favori araçlarını detaylı getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT a.*, s.sehir_ad, f.tarih 
        FROM Favori f 
        JOIN Arac a ON f.arac_id=a.arac_id 
        JOIN Sehir s ON a.bulundugu_sehir_id=s.sehir_id 
        WHERE f.musteri_id=%s 
        ORDER BY f.tarih DESC
    """
    cursor.execute(sql, (mid,))
    res = cursor.fetchall()
    conn.close()
    return res

def delete_favori(musteri_id, arac_id):
    """Favori kaydını siler"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Favori WHERE musteri_id=%s AND arac_id=%s", (musteri_id, arac_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Favori Silme Hatası: {e}")
        return False
    finally:
        conn.close()
