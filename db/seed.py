import mysql.connector
from werkzeug.security import generate_password_hash
import random
from datetime import date, timedelta

# === VERİTABANI AYARLARI ===
DB_CONFIG = {
    'user': 'root',
    'password': '1234',  # Kendi şifreniz
    'host': 'localhost',
    'raise_on_warnings': True
}
DB_NAME = 'arac_kiralama'

# === AYARLAR ===
N_ARAC = 150
N_MUSTERI = 50
N_KIRALAMA = 200

# === SABİT VERİ LİSTELERİ ===
SEHIRLER = [
    'İstanbul','Ankara','İzmir','Konya','Antalya','Bursa','Adana','Gaziantep',
    'Kayseri','Eskişehir','Mersin','Samsun','Trabzon','Denizli','Diyarbakır',
    'Şanlıurfa','Malatya','Aydın','Muğla','Tekirdağ'
]

KATEGORILER = ['Ekonomik', 'Orta Sınıf', 'SUV', 'Lüks', 'Minivan', 'Elektrikli', 'Ticari', 'Cabrio', 'Klasik', 'Off-Road']
SIGORTA_SIRKETLERI = ['Allianz', 'AXA', 'Anadolu', 'Mapfre', 'Sompo', 'Aksigorta', 'HDI', 'Zurich']

# Sigorta Paketleri (Veritabanındaki yapıya uygun)
SIGORTA_PAKETLERI = [
    ('Temel Sigorta', 'Zorunlu Trafik Sigortası', 0),
    ('Mini Hasar Paketi', 'Lastik, Cam, Far Güvencesi', 500),
    ('Tam Kapsamlı (Kasko)', '%100 Güvence, 0 Muafiyet', 1000),
]

# Resim isimleri static/img klasöründekilerle uyumlu
ARAC_HAVUZU = {
    'Fiat': [('Egea', 'egea.jpg'), ('Egea Cross', 'egeacross.jpg')],
    'Renault': [('Clio', 'clio.jpg'), ('Megane', 'megane.jpg')],
    'Toyota': [('Corolla', 'corolla.jpg')],
    'Volkswagen': [('Passat', 'passat.jpg')],
    'Ford': [('Focus', 'focus.jpg')],
    'Hyundai': [('i20', 'i20.jpg')],
    'Peugeot': [('3008', 'peugeot3008.jpg')],
    'BMW': [('5.20i', 'bmw520.jpg')],
    'Mercedes-Benz': [('Vito', 'vito.jpg')],
    'Audi': [('A3', 'a3.jpg')],
    'Honda': [('Civic', 'civic.jpg')],
    'Nissan': [('Qashqai', 'qashqai.jpg')],
    'Jeep': [('Renegade', 'renegade.jpg')],
    'Citroen': [('C3', 'c3.jpg')],
    'Dacia': [('Duster', 'duster.jpg')],
    'Opel': [('Corsa', 'corsa.jpg')]
}

ISIMLER = ['Ahmet', 'Mehmet', 'Ayse', 'Fatma', 'Ali', 'Zeynep', 'Can', 'Elif', 'Mert', 'Ece', 'Deniz', 'Emre', 'Seda', 'Burak', 'Cem', 'Naz', 'Hakan', 'Selin']
SOYISIMLER = ['Yilmaz', 'Kaya', 'Demir', 'Sahin', 'Celik', 'Yildiz', 'Aydin', 'Koc', 'Arslan', 'Dogan', 'Ozturk', 'Kara', 'Aslan', 'Polat']
CINSIYETLER = ['Kadın', 'Erkek', 'Belirtmek İstemiyorum']

YORUMLAR_LISTESI = [
    ('Hizmetten çok memnun kaldım, araç tertemizdi.', 5),
    ('Fiyat performans harika, tekrar kiralayacağım.', 5),
    ('Araç biraz kirliydi ama personel ilgiliydi.', 4),
    ('Her şey yolundaydı, teşekkürler.', 5),
    ('Teslimatta biraz bekledim ama sorun çözüldü.', 3),
    ('Harika bir deneyimdi, araç yeni gibiydi.', 5),
    ('Navigasyon çalışmıyordu ama sürüş keyifliydi.', 4),
    ('Yakıt tüketimi çok iyiydi.', 5)
]

BAKIM_NEDENLERI = [
    'Periyodik Yağ Değişimi', 'Fren Balata Kontrolü', 'Lastik Değişimi',
    'Motor Arıza Lambası', 'Kaporta Boya', 'Klima Gazı Dolumu'
]

# === BAĞLANTI ===
def get_connection():
    config = DB_CONFIG.copy()
    config['database'] = DB_NAME
    return mysql.connector.connect(**config)

# === DATABASE OLUŞTUR ===
def create_database(cursor):
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(
        f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
    )
    print(f"✅ Veritabanı '{DB_NAME}' oluşturuldu.")

# === TABLOLAR ===
def create_tables(cursor):
    cursor.execute(f"USE {DB_NAME}")
    
    # 1. Lookups
    cursor.execute("""
    CREATE TABLE Sehir (
        sehir_id INT AUTO_INCREMENT PRIMARY KEY,
        sehir_ad VARCHAR(50) NOT NULL,
        adres VARCHAR(255),
        telefon VARCHAR(20)
    )""")

    cursor.execute("""
    CREATE TABLE Kategori (
        kategori_id INT AUTO_INCREMENT PRIMARY KEY,
        kategori_ad VARCHAR(50) NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE Sigorta (
        sigorta_id INT AUTO_INCREMENT PRIMARY KEY,
        sigorta_sirketi VARCHAR(50) NOT NULL,
        baslangic_tarihi DATE NOT NULL,
        bitis_tarihi DATE NOT NULL,
        police_no VARCHAR(50) UNIQUE
    )""")
    
    cursor.execute("""
    CREATE TABLE SigortaPaketi (
        sigorta_paket_id INT AUTO_INCREMENT PRIMARY KEY,
        paket_adi VARCHAR(50) NOT NULL,
        aciklama VARCHAR(255),
        gunluk_ucret DECIMAL(10,2) NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE Personel (
        personel_id INT AUTO_INCREMENT PRIMARY KEY,
        ad VARCHAR(50) NOT NULL,
        soyad VARCHAR(50) NOT NULL,
        gorev VARCHAR(50) NOT NULL,
        eposta VARCHAR(100) UNIQUE NOT NULL,
        sifre VARCHAR(255) NOT NULL
    )""")

    # 2. Müşteri
    cursor.execute("""
    CREATE TABLE Musteri (
        musteri_id INT AUTO_INCREMENT PRIMARY KEY,
        ad VARCHAR(50) NOT NULL,
        soyad VARCHAR(50) NOT NULL,
        tc_kimlik_no CHAR(11) UNIQUE NOT NULL,
        cinsiyet ENUM('Kadın','Erkek','Belirtmek İstemiyorum') NOT NULL DEFAULT 'Belirtmek İstemiyorum',
        eposta VARCHAR(100) UNIQUE NOT NULL,
        sifre VARCHAR(255) NOT NULL,
        telefon VARCHAR(15),
        ehliyet_no VARCHAR(20),
        adres TEXT,
        ProfilResim VARCHAR(255) DEFAULT 'default_user.png',
        dogum_tarihi DATE
    )""")

    # 3. Araç
    cursor.execute("""
    CREATE TABLE Arac (
        arac_id INT AUTO_INCREMENT PRIMARY KEY,
        plaka VARCHAR(15) UNIQUE NOT NULL,
        marka VARCHAR(30) NOT NULL,
        model VARCHAR(30) NOT NULL,
        yil INT,
        yakit_turu ENUM('Benzin', 'Dizel', 'Elektrik', 'Hibrit', 'LPG') NOT NULL,
        vites_turu ENUM('Manuel', 'Otomatik') NOT NULL,
        kilometre INT DEFAULT 0,
        gunluk_ucret DECIMAL(10,2),
        resim_url VARCHAR(255) DEFAULT 'default_car.jpg',
        durum ENUM('Müsait','Kirada','Bakımda') DEFAULT 'Müsait',
        kategori_id INT,
        sigorta_id INT,
        bulundugu_sehir_id INT,
        FOREIGN KEY (kategori_id) REFERENCES Kategori(kategori_id),
        FOREIGN KEY (sigorta_id) REFERENCES Sigorta(sigorta_id),
        FOREIGN KEY (bulundugu_sehir_id) REFERENCES Sehir(sehir_id)
    )""")

    # 4. Kiralama 
    cursor.execute("""
    CREATE TABLE Kiralama (
        kiralama_id INT AUTO_INCREMENT PRIMARY KEY,
        musteri_id INT NOT NULL,
        arac_id INT NOT NULL,
        sigorta_paket_id INT NOT NULL,
        baslangic_tarihi DATE NOT NULL,
        bitis_tarihi DATE NOT NULL,
        alis_saati VARCHAR(5),
        teslim_saati VARCHAR(5),
        toplam_ucret DECIMAL(10,2),
        sigorta_ucreti DECIMAL(10,2) DEFAULT 0,
        durum ENUM('Onaylandı','Bekliyor','İptal','İptal Edildi','Tamamlandı','Kirada','Devam Ediyor') DEFAULT 'Bekliyor',
        FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id),
        FOREIGN KEY (arac_id) REFERENCES Arac(arac_id),
        FOREIGN KEY (sigorta_paket_id) REFERENCES SigortaPaketi(sigorta_paket_id)
    )""")

    # 5. Ödeme
    cursor.execute("""
    CREATE TABLE Odeme (
        odeme_id INT AUTO_INCREMENT PRIMARY KEY,
        kiralama_id INT NOT NULL,
        odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
        odeme_tutari DECIMAL(10,2),
        kart_sahibi VARCHAR(100),
        kart_no_son4 VARCHAR(4),
        odeme_turu ENUM('Kredi Kartı','Havale') DEFAULT 'Kredi Kartı',
        FOREIGN KEY (kiralama_id) REFERENCES Kiralama(kiralama_id)
    )""")
    # 6. Yorum & Favori & Bakım
    cursor.execute("""
    CREATE TABLE Yorum (
        yorum_id INT AUTO_INCREMENT PRIMARY KEY,
        musteri_id INT NOT NULL,
        yorum_metni TEXT NOT NULL,
        puan INT DEFAULT 5,
        tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
        durum ENUM('Bekliyor', 'Onaylandı', 'Reddedildi') DEFAULT 'Bekliyor',
        islem_yapan_personel_id INT,
        islem_tarihi DATETIME,
        FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
        FOREIGN KEY (islem_yapan_personel_id) REFERENCES Personel(personel_id)
    )""")

    cursor.execute("""
    CREATE TABLE Favori (
        favori_id INT AUTO_INCREMENT PRIMARY KEY,
        musteri_id INT NOT NULL,
        arac_id INT NOT NULL,
        tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
        FOREIGN KEY (arac_id) REFERENCES Arac(arac_id) ON DELETE CASCADE,
        UNIQUE(musteri_id, arac_id)
    )""")

    cursor.execute("""
    CREATE TABLE Bakim (
        bakim_id INT AUTO_INCREMENT PRIMARY KEY,
        arac_id INT NOT NULL,
        personel_id INT,
        bakim_nedeni TEXT NOT NULL,
        maliyet DECIMAL(10,2),
        giris_tarihi DATE NOT NULL,
        cikis_tarihi DATE,
        durum ENUM('Devam Ediyor', 'Tamamlandı') DEFAULT 'Devam Ediyor',
        FOREIGN KEY (arac_id) REFERENCES Arac(arac_id),
        FOREIGN KEY (personel_id) REFERENCES Personel(personel_id)
    )""")

    print("✅ Tablolar başarıyla oluşturuldu.")

# === SEED FONKSİYONU ===
def seed_data(cursor, conn):
    print("⏳ Veriler yükleniyor...")
    pw_hash = generate_password_hash("1234")

    # 1) ŞEHİRLER & KATEGORİLER
    for s in SEHIRLER:
        cursor.execute("INSERT INTO Sehir (sehir_ad, adres, telefon) VALUES (%s, 'Merkez Ofis', '05550001122')", (s,))
    for k in KATEGORILER:
        cursor.execute("INSERT INTO Kategori (kategori_ad) VALUES (%s)", (k,))

    # 2) PERSONEL EKLEME
    personel_listesi = [
        ("Fatih", "Kaya", "Yönetici", "admin@yolingo.com", pw_hash),
        ("Banu", "Demir", "Müşteri Temsilcisi", "mt@yolingo.com", pw_hash),
        ("Kamil", "Çelik", "Operasyon Sorumlusu", "os@yolingo.com", pw_hash)
    ]
    cursor.executemany(
        "INSERT INTO Personel (ad, soyad, gorev, eposta, sifre) VALUES (%s, %s, %s, %s, %s)",
        personel_listesi
    )
    
    # Personel ID'lerini al (Bakım kayıtlarında kullanacağız)
    cursor.execute("SELECT personel_id FROM Personel")
    personel_ids = [row['personel_id'] for row in cursor.fetchall()]

    # 3) SİGORTA PAKETLERİ (Önemli!)
    for paket_adi, aciklama, gunluk_ucret in SIGORTA_PAKETLERI:
        cursor.execute(
            "INSERT INTO SigortaPaketi (paket_adi, aciklama, gunluk_ucret) VALUES (%s,%s,%s)",
            (paket_adi, aciklama, gunluk_ucret)
        )
    
    # Paketleri hafızaya al (Fiyat hesaplamak için lazım)
    cursor.execute("SELECT sigorta_paket_id, gunluk_ucret FROM SigortaPaketi")
    sigorta_paketleri_db = cursor.fetchall()

    # 4) SİGORTA POLİÇELERİ (Araçlar için)
    sigorta_ids = []
    for i in range(N_ARAC + 50):
        sirket = random.choice(SIGORTA_SIRKETLERI)
        bas = date.today() - timedelta(days=random.randint(0, 300))
        bit = bas + timedelta(days=365)
        police = f"POL-{random.randint(100000, 999999)}"
        try:
            cursor.execute(
                "INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no) VALUES (%s,%s,%s,%s)",
                (sirket, bas, bit, police)
            )
            sigorta_ids.append(cursor.lastrowid)
        except:
            pass

    # 5) MÜŞTERİLER
    musteri_ids = []
    used_tc = set()
    for i in range(N_MUSTERI):
        ad = random.choice(ISIMLER)
        soyad = random.choice(SOYISIMLER)
        
        while True:
            tc = str(random.randint(10000000000, 99999999999))
            if tc not in used_tc:
                used_tc.add(tc)
                break
        
        cursor.execute(
            """INSERT INTO Musteri 
               (ad,soyad,tc_kimlik_no,cinsiyet,eposta,sifre,telefon,ehliyet_no,adres,dogum_tarihi) 
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                ad, soyad, tc,
                random.choice(CINSIYETLER),
                f"{ad.lower()}.{soyad.lower()}{i}@mail.com",
                pw_hash,
                f"05{random.randint(300,599)}{random.randint(1000000,9999999)}",
                f"E-{random.randint(10000,99999)}",
                f"{random.choice(SEHIRLER)} / Merkez",
                date(1990,1,1) + timedelta(days=random.randint(0, 5000))
            )
        )
        musteri_ids.append(cursor.lastrowid)

    # ID'leri çek
    cursor.execute("SELECT kategori_id FROM Kategori")
    cat_ids = [row['kategori_id'] for row in cursor.fetchall()]
    cursor.execute("SELECT sehir_id FROM Sehir")
    city_ids = [row['sehir_id'] for row in cursor.fetchall()]

    # 6) ARAÇLAR
    arac_ids = []
    used_plaka = set()
    
    for i in range(N_ARAC):
        marka = random.choice(list(ARAC_HAVUZU.keys()))
        model_ad, resim_ad = random.choice(ARAC_HAVUZU[marka])
        
        while True:
            kod = random.choice(['34','06','35','07','16','42','55','61'])
            harf = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
            sayi = random.randint(10, 999)
            plaka = f"{kod}{harf}{sayi}"
            if plaka not in used_plaka:
                used_plaka.add(plaka)
                break
        
        yakit = random.choice(['Benzin', 'Dizel', 'Elektrik', 'Hibrit'])
        vites = random.choice(['Manuel', 'Otomatik'])
        
        base_price = 1000
        if marka in ['BMW', 'Mercedes-Benz', 'Audi']: base_price += 2000
        if vites == 'Otomatik': base_price += 300
        ucret = base_price + random.randint(-200, 500)
        
        cursor.execute(
            """INSERT INTO Arac 
            (plaka, marka, model, yil, yakit_turu, vites_turu, kilometre, gunluk_ucret, resim_url, durum, 
             kategori_id, sigorta_id, bulundugu_sehir_id) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                plaka, marka, model_ad,
                random.randint(2020, 2024),
                yakit, vites,
                random.randint(0, 150000),
                ucret,
                resim_ad,
                'Müsait',
                random.choice(cat_ids),
                sigorta_ids[i] if i < len(sigorta_ids) else random.choice(sigorta_ids),
                random.choice(city_ids)
            )
        )
        arac_ids.append(cursor.lastrowid)

    # 7) BAKIM KAYITLARI
    bakimdaki_araclar = set()
    
    for _ in range(30):
        a_id = random.choice(arac_ids)
        if a_id in bakimdaki_araclar: continue

        neden = random.choice(BAKIM_NEDENLERI)
        durum = random.choice(['Devam Ediyor', 'Tamamlandı'])
        
        giris = date.today() - timedelta(days=random.randint(0, 20))
        cikis = None if durum == 'Devam Ediyor' else giris + timedelta(days=random.randint(1, 7))
        maliyet = random.randint(1000, 10000)

        personel = random.choice(personel_ids)
        cursor.execute(
            "INSERT INTO Bakim (arac_id, personel_id, bakim_nedeni, maliyet, giris_tarihi, cikis_tarihi, durum) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (a_id, personel, neden, maliyet, giris, cikis, durum)
        )
        
        if durum == 'Devam Ediyor':
            bakimdaki_araclar.add(a_id)
            cursor.execute("UPDATE Arac SET durum='Bakımda' WHERE arac_id=%s", (a_id,))

    # 8) KİRALAMALAR
    for _ in range(N_KIRALAMA):
        m_id = random.choice(musteri_ids)
        a_id = random.choice(arac_ids)
        
        # Bakımdaki aracı kiralama
        if a_id in bakimdaki_araclar: continue

        r_type = random.choice(['past', 'future', 'current'])
        
        if r_type == 'past':
            start = date.today() - timedelta(days=random.randint(10, 60))
            durum = 'Tamamlandı'
        elif r_type == 'future':
            start = date.today() + timedelta(days=random.randint(1, 30))
            durum = 'Onaylandı'
        else: # current
            start = date.today() - timedelta(days=random.randint(0, 2))
            durum = 'Kirada'

        gun = random.randint(1, 14)
        end = start + timedelta(days=gun)

        # Fiyat Hesaplama
        cursor.execute("SELECT gunluk_ucret FROM Arac WHERE arac_id=%s", (a_id,))
        daily_price = float(cursor.fetchone()['gunluk_ucret'])
        arac_ucret = daily_price * gun
        
        # Sigorta Paketi Seçimi
        paket = random.choice(sigorta_paketleri_db)
        paket_id = paket['sigorta_paket_id']
        paket_fiyat = float(paket['gunluk_ucret'])
        sigorta_ucreti = paket_fiyat * gun
        
        toplam = arac_ucret + sigorta_ucreti

        cursor.execute(
            """INSERT INTO Kiralama 
            (musteri_id, arac_id, sigorta_paket_id, baslangic_tarihi, bitis_tarihi, alis_saati, teslim_saati, 
             toplam_ucret, sigorta_ucreti, durum) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (m_id, a_id, paket_id, start, end, '10:00', '10:00', toplam, sigorta_ucreti, durum)
        )
        rez_id = cursor.lastrowid
        
        # Ödeme Ekle
        cursor.execute(
            "INSERT INTO Odeme (kiralama_id, odeme_tutari, kart_sahibi, kart_no_son4) VALUES (%s,%s,%s,%s)",
            (rez_id, toplam, "Test User", str(random.randint(1000,9999)))
        )

        # Araç Durum Güncelle
        if durum == 'Kirada':
            cursor.execute("UPDATE Arac SET durum='Kirada' WHERE arac_id=%s", (a_id,))

    # 9) YORUMLAR & FAVORİLER
    for _ in range(30):
        cursor.execute(
            "INSERT INTO Yorum (musteri_id, yorum_metni, puan, durum) VALUES (%s,%s,%s,%s)",
            (random.choice(musteri_ids), random.choice(YORUMLAR_LISTESI)[0], random.randint(3,5), 'Onaylandı')
        )

    for _ in range(30):
        try:
            cursor.execute(
                "INSERT INTO Favori (musteri_id, arac_id) VALUES (%s,%s)",
                (random.choice(musteri_ids), random.choice(arac_ids))
            )
        except: pass

    conn.commit()
    print("🚀 Seed işlemi başarıyla tamamlandı!")
    print(f"📊 {len(musteri_ids)} Müşteri, {len(arac_ids)} Araç, {N_KIRALAMA} kiralama eklendi.")

# === MAIN ===
def main():
    # 1) Veritabanını oluştur
    conn_raw = mysql.connector.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    create_database(conn_raw.cursor())
    conn_raw.close()

    # 2) Tabloları kur ve verileri bas
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        create_tables(cursor)
        seed_data(cursor, conn)
    except mysql.connector.Error as err:
        print(f"❌ HATA: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()