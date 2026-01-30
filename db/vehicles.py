from db.connection import get_db_connection

def get_sehirler():
    """Tüm şehirleri getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Sehir")
    result = cursor.fetchall()
    conn.close()
    return result

def get_kategoriler():
    """Tüm kategorileri getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Kategori")
    result = cursor.fetchall()
    conn.close()
    return result

def get_tum_araclar(sehir_id=None, baslangic=None, bitis=None, vites=None, yakit=None, min_fiyat=0, max_fiyat=100000):
    """Filtrelere göre müsait araçları listeler"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT a.*, s.sehir_ad 
        FROM Arac a
        JOIN Sehir s ON a.bulundugu_sehir_id = s.sehir_id
        WHERE a.durum != 'Bakımda'
        AND a.gunluk_ucret BETWEEN %s AND %s
    """
    params = [min_fiyat, max_fiyat]

    if sehir_id and sehir_id != "":
        query += " AND a.bulundugu_sehir_id = %s"
        params.append(sehir_id)
    
    if vites and vites != "":
        query += " AND a.vites_turu = %s"
        params.append(vites)

    if yakit and yakit != "":
        query += " AND a.yakit_turu = %s"
        params.append(yakit)
    
    # Tarih çakışması kontrolü
    if baslangic and bitis:
        query += """ 
            AND a.arac_id NOT IN (
                SELECT arac_id FROM kiralama 
                WHERE durum IN ('Onaylandı', 'Bekliyor', 'Kirada')
                AND (baslangic_tarihi <= %s AND bitis_tarihi >= %s)
            )
        """
        params.append(bitis)
        params.append(baslangic)

    cursor.execute(query, tuple(params))
    araclar = cursor.fetchall()
    conn.close()
    return araclar

def get_arac_by_id(arac_id):
    """Araç ID'sine göre araç bilgilerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Arac WHERE arac_id = %s", (arac_id,))
    arac = cursor.fetchone()
    conn.close()
    return arac

def add_arac_ve_sigorta(arac_bilgi, sigorta_bilgi):
    """Yeni araç ve sigorta kaydı oluşturur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_sigorta = "INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_sigorta, (sigorta_bilgi['sirket'], sigorta_bilgi['baslangic'], sigorta_bilgi['bitis'], sigorta_bilgi['police']))
        sigorta_id = cursor.lastrowid

        sql_arac = """INSERT INTO Arac (plaka, marka, model, yil, yakit_turu, vites_turu, gunluk_ucret, resim_url, kategori_id, bulundugu_sehir_id, sigorta_id, durum) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Müsait')"""
        val_arac = (arac_bilgi['plaka'], arac_bilgi['marka'], arac_bilgi['model'], arac_bilgi['yil'], 
                    arac_bilgi['yakit'], arac_bilgi['vites'], arac_bilgi['ucret'], arac_bilgi['resim'], 
                    arac_bilgi['kategori'], arac_bilgi['sehir'], sigorta_id)
        cursor.execute(sql_arac, val_arac)
        conn.commit()
        return True
    except: 
        return False
    finally: 
        conn.close()

def teslim_al_arac(kiralama_id):
    """Kiralanan aracı teslim alır ve durumunu günceller"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT arac_id FROM kiralama WHERE kiralama_id = %s", (kiralama_id,))
        rez = cursor.fetchone()
        if rez:
            cursor.execute("UPDATE Arac SET durum = 'Müsait' WHERE arac_id = %s", (rez['arac_id'],))
            cursor.execute("UPDATE kiralama SET durum = 'Tamamlandı' WHERE kiralama_id = %s", (kiralama_id,))
            conn.commit()
            return True
        return False
    finally: 
        conn.close()
