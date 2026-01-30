from db.connection import get_db_connection

def add_kiralama(bilgi, odeme):
    """Yeni kiralama kaydı oluşturur"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sigorta_ucreti = bilgi.get('sigorta_paket_id', 0) 

        sql_rez = """
            INSERT INTO kiralama 
            (musteri_id, arac_id, baslangic_tarihi, bitis_tarihi, alis_saati, teslim_saati, toplam_ucret, sigorta_paket_id, durum)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Onaylandı')
        """
        
        val_rez = (
            bilgi['musteri_id'], 
            bilgi['arac_id'], 
            bilgi['baslangic_tarihi'], 
            bilgi['bitis_tarihi'], 
            bilgi['alis_saati'], 
            bilgi['teslim_saati'], 
            bilgi['toplam_ucret'], 
            sigorta_ucreti
        )
        
        cursor.execute(sql_rez, val_rez)
        rez_id = cursor.lastrowid
        
        # --- GÜVENLİ KART NUMARASI ALIMI ---
        kart_no = odeme.get('no', '')
        kart_son4 = kart_no[-4:] if len(str(kart_no)) >= 4 else 'XXXX'
        
        sql_odm = "INSERT INTO Odeme (kiralama_id, odeme_tutari, kart_sahibi, kart_no_son4, odeme_turu) VALUES (%s,%s,%s,%s,%s)"
        val_odm = (rez_id, bilgi['toplam_ucret'], odeme['sahip'], kart_son4, odeme['tur'])
        cursor.execute(sql_odm, val_odm)
        
        # Araç durumunu güncelle
        cursor.execute("UPDATE Arac SET durum='Kirada' WHERE arac_id=%s", (bilgi['arac_id'],))
        conn.commit()
        return True
    except Exception as e: 
        print(f"kiralama Hatası: {e}")
        conn.rollback()
        return False
    finally: 
        conn.close()

def get_musteri_kiralamalari(mid):
    """Müşterinin tüm kiralamalarını getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT r.*, a.marka, a.model, a.resim_url
        FROM kiralama r JOIN Arac a ON r.arac_id=a.arac_id
        WHERE r.musteri_id=%s ORDER BY r.kiralama_id DESC
    """
    cursor.execute(sql, (mid,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_sigorta_paketi_by_id(paket_id):
    """Sigorta paket bilgilerini getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM SigortaPaketi WHERE sigorta_paket_id = %s", (paket_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def get_kiralama_detay_pdf(rid):
    """PDF sözleşme için kiralama detaylarını getirir"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            r.kiralama_id,
            r.musteri_id,
            r.baslangic_tarihi,
            r.bitis_tarihi,
            r.alis_saati,
            r.teslim_saati,
            r.toplam_ucret,

            m.ad,
            m.soyad,
            m.ehliyet_no,
            m.tc_kimlik_no, 
            m.telefon,
            m.eposta,
            m.adres,

            a.plaka,
            a.marka,
            a.model,
            a.yil,
            a.yakit_turu,
            a.vites_turu,
            a.gunluk_ucret AS arac_gunluk_ucret,

            sp.paket_adi,
            sp.gunluk_ucret AS sigorta_gunluk_ucret,
            
            s.sehir_ad,
            s.adres AS ofis_adres,
            s.telefon AS ofis_telefon

        FROM kiralama r
        JOIN Musteri m ON r.musteri_id = m.musteri_id
        JOIN Arac a ON r.arac_id = a.arac_id
        LEFT JOIN SigortaPaketi sp ON r.sigorta_paket_id = sp.sigorta_paket_id
        JOIN Sehir s ON a.bulundugu_sehir_id = s.sehir_id
        
        WHERE r.kiralama_id = %s
    """

    cursor.execute(sql, (rid,))
    res = cursor.fetchone()
    conn.close()
    return res
