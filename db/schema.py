"""
Database Schema Setup and Reset Script
Creates all tables and stored procedures for the car rental system.
"""

import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash
import datetime

# === DATABASE CONFIGURATION ===
config = {
    'user': 'root',
    'password': '1234',  # Your MySQL password
    'host': 'localhost',
    'raise_on_warnings': True
}

DB_NAME = 'arac_kiralama'

# === TABLE DEFINITIONS ===
TABLES = {}

TABLES['Sehir'] = """
CREATE TABLE Sehir (
    sehir_id INT AUTO_INCREMENT PRIMARY KEY,
    sehir_ad VARCHAR(50) NOT NULL,
    adres VARCHAR(255),
    telefon VARCHAR(20)
) ENGINE=InnoDB;
"""

TABLES['Kategori'] = """
CREATE TABLE Kategori (
    kategori_id INT AUTO_INCREMENT PRIMARY KEY,
    kategori_ad VARCHAR(50) NOT NULL
) ENGINE=InnoDB;
"""

TABLES['Sigorta'] = """
CREATE TABLE Sigorta (
    sigorta_id INT AUTO_INCREMENT PRIMARY KEY,
    sigorta_sirketi VARCHAR(50) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    police_no VARCHAR(50) UNIQUE
) ENGINE=InnoDB;
"""

TABLES['SigortaPaketi'] = """
CREATE TABLE SigortaPaketi (
    sigorta_paket_id INT AUTO_INCREMENT PRIMARY KEY,
    paket_adi VARCHAR(50) NOT NULL,
    aciklama VARCHAR(255),
    gunluk_ucret DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;
"""

TABLES['Personel'] = """
CREATE TABLE Personel (
    personel_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    gorev VARCHAR(50) NOT NULL,
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL
) ENGINE=InnoDB;
"""

TABLES['Musteri'] = """
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
) ENGINE=InnoDB;
"""

TABLES['Arac'] = """
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
) ENGINE=InnoDB;
"""

TABLES['Kiralama'] = """
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
) ENGINE=InnoDB;
"""

TABLES['Odeme'] = """
CREATE TABLE Odeme (
    odeme_id INT AUTO_INCREMENT PRIMARY KEY,
    kiralama_id INT NOT NULL,
    odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    odeme_tutari DECIMAL(10,2),
    kart_sahibi VARCHAR(100),
    kart_no_son4 VARCHAR(4),
    odeme_turu ENUM('Kredi Kartı','Havale') DEFAULT 'Kredi Kartı',
    FOREIGN KEY (kiralama_id) REFERENCES Kiralama(kiralama_id)
) ENGINE=InnoDB;
"""

TABLES['Yorum'] = """
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
) ENGINE=InnoDB;
"""

TABLES['Favori'] = """
CREATE TABLE Favori (
    favori_id INT AUTO_INCREMENT PRIMARY KEY,
    musteri_id INT NOT NULL,
    arac_id INT NOT NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id) ON DELETE CASCADE,
    UNIQUE(musteri_id, arac_id)
) ENGINE=InnoDB;
"""

TABLES['Bakim'] = """
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
) ENGINE=InnoDB;
"""

# === DATABASE CREATION FUNCTION ===
def create_database(cursor):
    """Creates the database if it doesn't exist"""
    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        exit(1)

# === MAIN EXECUTION ===
def main():
    try:
        print("⏳ Connecting to MySQL server...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 1. Drop and recreate database
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            print(f"🗑️  Old '{DB_NAME}' database dropped.")
        except mysql.connector.Error as err:
            print(f"Error (DROP DB): {err}")

        create_database(cursor)
        print(f"✅ New '{DB_NAME}' database created.")

        # Select the database
        conn.database = DB_NAME

        # 2. Create tables
        print("⏳ Creating tables...")
        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                print(f"  -> Creating {table_name}...", end='')
                cursor.execute(table_description)
                print("OK")
            except mysql.connector.Error as err:
                print(f"\n❌ ERROR ({table_name}): {err.msg}")
                exit(1)

        # 3. Insert fixed data (lookup tables)
        print("⏳ Inserting fixed data...")
        
        # CITIES
        cities = [
            ('İstanbul', 'Kadıköy Rıhtım Cad. No:12', '0216 555 10 10'),
            ('Ankara', 'Çankaya Atatürk Bulvarı No:45', '0312 555 20 20'),
            ('İzmir', 'Bornova Üniversite Cad. No:18', '0232 555 30 30'),
            ('Antalya', 'Konyaaltı Sahil Yolu No:7', '0242 555 40 40'),
            ('Bursa', 'Nilüfer FSM Bulvarı No:22', '0224 555 50 50'),
            ('Adana', 'Seyhan Ziyapaşa Bulvarı No:14', '0322 555 60 60'),
            ('Konya', 'Meram Yeni Yol Cad. No:9', '0332 555 70 70'),
            ('Gaziantep', 'Şehitkamil İpek Yolu Cad. No:30', '0342 555 80 80'),
            ('Trabzon', 'Ortahisar Kahramanmaraş Cad. No:9', '0462 555 16 16'),
            ('Eskişehir', 'Odunpazarı Arifiye Cad. No:5', '0222 555 12 12')
        ]
        cursor.executemany("INSERT INTO Sehir (sehir_ad, adres, telefon) VALUES (%s, %s, %s)", cities)

        #CATEGORIES
        categories = [('Ekonomik',), ('Orta Sınıf',), ('SUV',), ('Lüks',), ('Minivan',), 
                      ('Elektrikli',), ('Üst Segment',), ('Ticari',), ('Cabrio',), ('Klasik',), ('Off-Road',)]
        cursor.executemany("INSERT INTO Kategori (kategori_ad) VALUES (%s)", categories)

        # INSURANCE PACKAGES
        packages = [
            ('Temel Sigorta', 'Zorunlu Trafik Sigortası', 0),
            ('Mini Hasar Paketi', 'Lastik, Cam, Far Güvencesi', 500),
            ('Tam Kapsamlı (Kasko)', '%100 Güvence, 0 Muafiyet', 1000)
        ]
        cursor.executemany("INSERT INTO SigortaPaketi (paket_adi, aciklama, gunluk_ucret) VALUES (%s, %s, %s)", packages)

        # STAFF
        password = generate_password_hash("1234")
        staff = [
            ('Fatih', 'Kaya', 'Yönetici', 'admin@yolingo.com', password),
            ('Banu', 'Demir', 'Müşteri Temsilcisi', 'mt@yolingo.com', password),
            ('Kamil', 'Çelik', 'Operasyon Sorumlusu', 'os@yolingo.com', password)
        ]
        cursor.executemany("INSERT INTO Personel (ad, soyad, gorev, eposta, sifre) VALUES (%s, %s, %s, %s, %s)", staff)
        
        print("✅ Fixed data inserted.")

        # 4. Create stored procedure
        procedure_sql = """
        CREATE PROCEDURE sp_update_arac_durum()
        BEGIN
          UPDATE Arac a
          JOIN Bakim b ON b.arac_id = a.arac_id
          SET a.durum = 'Bakımda'
          WHERE b.durum = 'Devam Ediyor';

          UPDATE Arac a
          SET a.durum = 'Kirada'
          WHERE a.durum <> 'Bakımda'
            AND EXISTS (
            SELECT 1 FROM Kiralama k
            WHERE k.arac_id = a.arac_id
                AND k.durum IN ('Onaylandı','Bekliyor','Kirada')
                AND CURDATE() BETWEEN k.baslangic_tarihi AND k.bitis_tarihi
            );

          UPDATE Arac a
          SET a.durum = 'Müsait'
          WHERE a.durum <> 'Bakımda'
            AND NOT EXISTS (
              SELECT 1 FROM Kiralama k
              WHERE k.arac_id = a.arac_id
                AND k.durum IN ('Onaylandı','Bekliyor','Kirada')
                AND CURDATE() BETWEEN k.baslangic_tarihi AND k.bitis_tarihi
            );
        END
        """
        print("⏳ Creating stored procedure...")
        try:
            cursor.execute(procedure_sql)
            print("✅ Procedure created.")
        except mysql.connector.Error as err:
            print(f"⚠️ Warning: Could not create procedure (may already exist): {err}")

        conn.commit()
        print("\n🚀 DATABASE RESET COMPLETED SUCCESSFULLY!")
        print("Next step: Run 'python db/seed.py' to populate with test data.")

    except mysql.connector.Error as err:
        print(f"❌ CRITICAL ERROR: {err}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()
