-- ==========================================================
-- VERİTABANI OLUŞTURMA VE BAŞLANGIÇ AYARLARI
-- ==========================================================

-- Daha önce aynı isimde veritabanı varsa silinir
DROP DATABASE IF EXISTS arac_kiralama;

-- UTF-8 Türkçe karakter desteğiyle yeni veritabanı oluşturulur
CREATE DATABASE arac_kiralama 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- Aktif veritabanı seçilir
USE arac_kiralama;

-- Karakter seti ve zaman dilimi ayarlanır (Türkiye için)
SET NAMES utf8mb4;
SET time_zone = '+03:00';

-- ==========================================================
-- 1) ANA TABLOLAR
-- ==========================================================

-- Şehir bilgilerini tutan tablo
CREATE TABLE Sehir (
    sehir_id INT AUTO_INCREMENT PRIMARY KEY,
    sehir_ad VARCHAR(50) NOT NULL,
    adres VARCHAR(255),
    telefon VARCHAR(20)
);

-- Araç sınıflarını tutan kategori tablosu
CREATE TABLE Kategori (
    kategori_id INT AUTO_INCREMENT PRIMARY KEY,
    kategori_ad VARCHAR(50) NOT NULL
);

-- Araçlara ait sigorta bilgilerini tutan tablo
CREATE TABLE Sigorta (
    sigorta_id INT AUTO_INCREMENT PRIMARY KEY,
    sigorta_sirketi VARCHAR(50) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    police_no VARCHAR(50) UNIQUE
);

-- Sistemi yöneten personeller
CREATE TABLE Personel (
    personel_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    gorev VARCHAR(50) NOT NULL,
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL
);

-- Müşteri (kullanıcı) bilgileri
CREATE TABLE Musteri (
    musteri_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    tc_kimlik_no CHAR(11) UNIQUE NOT NULL,
    cinsiyet ENUM('Kadın','Erkek','Belirtmek İstemiyorum') 
        NOT NULL DEFAULT 'Belirtmek İstemiyorum',
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL,
    telefon VARCHAR(15),
    ehliyet_no VARCHAR(20),
    adres TEXT,
    ProfilResim VARCHAR(255) DEFAULT 'default_user.png',
    dogum_tarihi DATE
);

-- Araç bilgileri
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

    -- İlişkisel alanlar
    kategori_id INT,
    sigorta_id INT,
    bulundugu_sehir_id INT,

    -- Foreign Key tanımları
    FOREIGN KEY (kategori_id) REFERENCES Kategori(kategori_id),
    FOREIGN KEY (sigorta_id) REFERENCES Sigorta(sigorta_id),
    FOREIGN KEY (bulundugu_sehir_id) REFERENCES Sehir(sehir_id)
);

-- Sigorta paketleri (opsiyonel hizmetler)
CREATE TABLE SigortaPaketi (
    sigorta_paket_id INT AUTO_INCREMENT PRIMARY KEY,
    paket_adi VARCHAR(50) NOT NULL,
    aciklama VARCHAR(255),
    gunluk_ucret DECIMAL(10,2) NOT NULL
);

-- Kiralama işlemleri
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
    durum ENUM(
        'Onaylandı','Bekliyor','İptal',
        'İptal Edildi','Tamamlandı',
        'Kirada','Devam Ediyor'
    ) DEFAULT 'Bekliyor',

    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id),
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id),
    FOREIGN KEY (sigorta_paket_id) REFERENCES SigortaPaketi(sigorta_paket_id)
);

-- Ödeme bilgileri (kartın tamamı tutulmaz, güvenlik için son 4 hane)
CREATE TABLE Odeme (
    odeme_id INT AUTO_INCREMENT PRIMARY KEY,
    kiralama_id INT NOT NULL,
    odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    odeme_tutari DECIMAL(10,2),
    kart_sahibi VARCHAR(100),
    kart_no_son4 VARCHAR(4),
    odeme_turu ENUM('Kredi Kartı','Havale') DEFAULT 'Kredi Kartı',
    FOREIGN KEY (kiralama_id) REFERENCES Kiralama(kiralama_id)
);

-- Kullanıcı yorumları (admin onaylı)
CREATE TABLE Yorum (
    yorum_id INT AUTO_INCREMENT PRIMARY KEY,
    musteri_id INT NOT NULL,
    yorum_metni TEXT NOT NULL,
    puan INT DEFAULT 5,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    durum ENUM('Bekliyor', 'Onaylandı', 'Reddedildi') DEFAULT 'Bekliyor',
    islem_yapan_personel_id INT,
    islem_tarihi DATETIME,

    -- Kullanıcı silinirse yorumlar da silinir
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
    FOREIGN KEY (islem_yapan_personel_id) REFERENCES Personel(personel_id)
);

-- Favori araçlar (çoktan-çoğa ilişki)
CREATE TABLE Favori (
    musteri_id INT NOT NULL,
    arac_id INT NOT NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (musteri_id, arac_id),
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id) ON DELETE CASCADE
);

-- Araç bakım kayıtları
CREATE TABLE Bakim (
    bakim_id INT AUTO_INCREMENT PRIMARY KEY,
    personel_id INT NOT NULL,
    arac_id INT NOT NULL,
    bakim_nedeni TEXT NOT NULL,
    maliyet DECIMAL(10,2),
    giris_tarihi DATE NOT NULL,
    cikis_tarihi DATE,
    durum ENUM('Devam Ediyor', 'Tamamlandı') DEFAULT 'Devam Ediyor',
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id)
);

-- ==========================================================
-- 2) TEMEL VERİLER (LOOKUP / REFERANS TABLOLAR)
-- ==========================================================
-- Bu bölümde sisteme ait sabit ve referans niteliğindeki veriler eklenmektedir. Bu tablolar, uygulamanın filtreleme, sınıflandırma
-- ve lokasyon bazlı işlemlerinde kullanılmaktadır.

-- Şehirler
-- Şehir tablosuna Türkiye genelinde farklı lokasyonlar eklenmiştir.
-- Bu veriler, araçların şehir bazlı listelenmesi ve kiralama senaryolarının test edilmesi amacıyla kullanılmıştır.
INSERT INTO Sehir (sehir_ad, adres, telefon) VALUES
('İstanbul',     'Kadıköy Rıhtım Cad. No:12',             '0216 555 10 10'),
('Ankara',       'Çankaya Atatürk Bulvarı No:45',        '0312 555 20 20'),
('İzmir',        'Bornova Üniversite Cad. No:18',        '0232 555 30 30'),
('Antalya',      'Konyaaltı Sahil Yolu No:7',            '0242 555 40 40'),
('Bursa',        'Nilüfer FSM Bulvarı No:22',            '0224 555 50 50'),
('Adana',        'Seyhan Ziyapaşa Bulvarı No:14',        '0322 555 60 60'),
('Konya',        'Meram Yeni Yol Cad. No:9',             '0332 555 70 70'),
('Gaziantep',    'Şehitkamil İpek Yolu Cad. No:30',      '0342 555 80 80'),
('Şanlıurfa',    'Haliliye Atatürk Cad. No:11',          '0414 555 90 90'),
('Mersin',       'Yenişehir GMK Bulvarı No:55',          '0324 555 11 11'),
('Muğla',        'Menteşe Cumhuriyet Cad. No:6',         '0252 555 22 22'),
('Aydın',        'Efeler Girne Bulvarı No:19',           '0256 555 33 33'),
('Çanakkale',    'Merkez İnönü Cad. No:3',               '0286 555 44 44'),
('Balıkesir',    'Karesi Milli Kuvvetler Cad. No:21', '0266 555 55 55'),
('Yalova',       'Merkez Sahil Yolu No:8',               '0226 555 66 66'),
('Sakarya',      'Adapazarı Çark Cad. No:16',            '0264 555 77 77'),
('Kocaeli',      'İzmit Cumhuriyet Cad. No:28',         '0262 555 88 88'),
('Kayseri',      'Melikgazi Sivas Cad. No:10',           '0352 555 99 99'),
('Eskişehir',    'Odunpazarı Arifiye Cad. No:5',         '0222 555 12 12'),
('Diyarbakır',   'Kayapınar Diclekent Bulvarı No:40',    '0412 555 13 13'),
('Samsun',       'Atakum Atatürk Bulvarı No:60',         '0362 555 14 14'),
('Denizli',      'Pamukkale Üniversite Cad. No:17',     '0258 555 15 15'),
('Trabzon',      'Ortahisar Kahramanmaraş Cad. No:9', '0462 555 16 16'),
('Erzurum',      'Yakutiye Cumhuriyet Cad. No:23',      '0442 555 17 17'),
('Malatya',      'Battalgazi İnönü Cad. No:33',         '0422 555 18 18'),
('Hatay',        'Antakya Atatürk Cad. No:44',          '0326 555 19 19'),
('Manisa',       'Yunusemre 8 Eylül Cad. No:12',        '0236 555 21 21'),
('Tekirdağ',     'Süleymanpaşa Hükümet Cad. No:20',     '0282 555 22 23'),
('Van',           'İpekyolu Cumhuriyet Cad. No:25',     '0432 555 24 24'),
('Mardin',       'Artuklu 1. Cadde No:7',               '0482 555 25 25');

-- Araçların segment bazlı sınıflandırılabilmesi için kategori bilgileri eklenmiştir. Bu yapı sayesinde araçlar ekonomik,
-- SUV, lüks gibi sınıflara ayrılabilmektedir.
INSERT INTO Kategori (kategori_ad) VALUES 
('Ekonomik'), ('Orta Sınıf'), ('SUV'), ('Lüks'), ('Minivan'), 
('Elektrikli'), ('Üst Segment'), ('Ticari'), ('Cabrio'), ('Klasik'), ('Off-Road');

-- Sistemi yöneten ve işlemleri denetleyen personel kullanıcıları eklenmiştir. Şifreler güvenlik gereği hashlenmiş formatta
-- veritabanında saklanmaktadır.
INSERT INTO Personel (ad, soyad, gorev, eposta, sifre) VALUES 
('Fatih','Kaya','Yönetici','admin@yolingo.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f'),
('Banu', 'Demir', 'Müşteri Temsilcisi', 'mt@yolingo.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f'),
('Kamil', 'Çelik', 'Operasyon Sorumlusu', 'os@yolingo.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f');


-- Sigorta tablosu için örnek (normal) sigorta verileri oluşturulur.
-- Sigorta şirketi rastgele seçilir, başlangıç tarihi 2025 yılı içinden atanır, bitiş tarihi otomatik olarak 1 yıl sonrası olacak şekilde hesaplanır.
-- Her kayıt için benzersiz bir poliçe numarası üretilir.
INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no)
SELECT 
  ELT(1+FLOOR(RAND()*10), 'Allianz','AXA','Anadolu','Mapfre','Sompo','Aksigorta','HDI','Zurich','Generali','Doga'),
  DATE_ADD('2025-01-01', INTERVAL FLOOR(RAND()*365) DAY),
  DATE_ADD(DATE_ADD('2025-01-01', INTERVAL FLOOR(RAND()*365) DAY), INTERVAL 365 DAY),
  CONCAT('POL-', LPAD(ROW_NUMBER() OVER (), 4, '0')) 
FROM information_schema.columns t1, information_schema.columns t2 LIMIT 200;


-- Müşteri tablosuna sisteme kayıtlı örnek kullanıcılar eklenmiştir.
-- Bu veriler kullanıcı girişi, profil yönetimi, kiralama ve yorum yapma senaryolarının test edilmesi amacıyla kullanılmıştır.
INSERT INTO Musteri (ad, soyad, tc_kimlik_no, cinsiyet, eposta, sifre, telefon, ehliyet_no, adres, dogum_tarihi, ProfilResim) VALUES
('Ayşe', 'Yılmaz', '12345678901', 'Kadın', 'ayse.yilmaz@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05321010101', 'B-10203', 'Kadıköy, İstanbul', '1993-04-12', 'default_user.png'),
('Burak', 'Çelik', '23456789012', 'Erkek', 'burak.celik@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05422020202', 'B-40506', 'Çankaya, Ankara', '1988-09-25', 'default_user.png'),
('Elif', 'Koç', '34567890123', 'Kadın', 'elif.koc@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05553030303', 'B-70809', 'Bornova, İzmir', '1999-01-15', 'default_user.png'),
('Emre', 'Arslan', '45678901234', 'Erkek', 'emre.arslan@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05064040404', 'E-12345', 'Nilüfer, Bursa', '1991-07-30', 'default_user.png'),
('Gamze', 'Polat', '56789012345', 'Kadın', 'gamze.polat@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05305050505', 'B-67890', 'Konyaaltı, Antalya', '1996-11-05', 'default_user.png'),
('Hakan', 'Doğan', '67890123456', 'Erkek', 'hakan.dogan@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05356060606', 'E-98765', 'Seyhan, Adana', '1985-03-22', 'default_user.png'),
('Ceren', 'Özkan', '78901234567', 'Kadın', 'ceren.ozkan@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05447070707', 'B-54321', 'Odunpazarı, Eskişehir', '2000-08-18', 'default_user.png'),
('Volkan', 'Şahin', '89012345678', 'Erkek', 'volkan.sahin@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05338080808', 'E-11223', 'Şehitkamil, Gaziantep', '1994-06-10', 'default_user.png'),
('Merve', 'Aksoy', '90123456789', 'Kadın', 'merve.aksoy@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05529090909', 'B-33445', 'Ortahisar, Trabzon', '1997-12-02', 'default_user.png'),
('Tolga', 'Tekin', '11223344556', 'Erkek', 'tolga.tekin@mail.com', 'scrypt:32768:8:1$BmB3FRGkLFQ0Aaqj$265307786c047bb43a8ec9e2b05217d0c0c56123708f33624386c244ec28720023c679d9ad82d8bd8ef349b580cfd1e90e15c778f006ef4197551288b58f610f', '05361000000', 'E-55667', 'Meram, Konya', '1992-02-28', 'default_user.png');


-- Araç tablosuna farklı marka, model, yakıt türü, vites tipi ve kilometre bilgilerine sahip araçlar eklenmiştir.
-- Araçların farklı şehirlerde bulunması sayesinde lokasyon bazlı müsaitlik senaryoları test edilmiştir.

INSERT INTO Arac (plaka, marka, model, yil, yakit_turu, vites_turu, kilometre, gunluk_ucret, resim_url, durum, kategori_id, sigorta_id, bulundugu_sehir_id) VALUES
('34BMW520', 'BMW', '5.20i', 2023, 'Benzin', 'Otomatik', 15000, 5500.00, 'bmw520.jpg', 'Müsait', 4, 1, 1),
('06ANK060', 'BMW', '5.20i', 2022, 'Benzin', 'Otomatik', 28000, 5200.00, 'bmw520.jpg', 'Kirada', 4, 2, 2),
('35IZM520', 'BMW', '5.20i', 2023, 'Benzin', 'Otomatik', 12000, 5600.00, 'bmw520.jpg', 'Müsait', 4, 3, 3),
('07ANT007', 'BMW', '5.20i', 2021, 'Benzin', 'Otomatik', 45000, 4900.00, 'bmw520.jpg', 'Müsait', 4, 4, 5),
('34LUX001', 'BMW', '5.20i', 2024, 'Benzin', 'Otomatik', 5000, 6000.00, 'bmw520.jpg', 'Müsait', 4, 5, 1),
('16BUR520', 'BMW', '5.20i', 2022, 'Benzin', 'Otomatik', 32000, 5100.00, 'bmw520.jpg', 'Bakımda', 4, 6, 6),
('34AUD001', 'Audi', 'A3', 2023, 'Benzin', 'Otomatik', 18000, 3200.00, 'a3.jpg', 'Müsait', 4, 7, 1),
('06AUD006', 'Audi', 'A3', 2022, 'Dizel', 'Otomatik', 35000, 2900.00, 'a3.jpg', 'Kirada', 4, 8, 2),
('35AUD035', 'Audi', 'A3', 2023, 'Benzin', 'Otomatik', 10000, 3300.00, 'a3.jpg', 'Müsait', 4, 9, 3),
('42KON042', 'Audi', 'A3', 2021, 'Dizel', 'Otomatik', 52000, 2700.00, 'a3.jpg', 'Müsait', 4, 10, 4),
('07ANT034', 'Audi', 'A3', 2024, 'Hibrit', 'Otomatik', 6000, 3500.00, 'a3.jpg', 'Müsait', 4, 11, 5),
('34AUD022', 'Audi', 'A3', 2022, 'Benzin', 'Otomatik', 29000, 3000.00, 'a3.jpg', 'Bakımda', 4, 12, 1),
('34VW001', 'Volkswagen', 'Passat', 2022, 'Dizel', 'Otomatik', 42000, 2800.00, 'passat.jpg', 'Müsait', 2, 13, 1),
('06VW006', 'Volkswagen', 'Passat', 2021, 'Dizel', 'Otomatik', 65000, 2500.00, 'passat.jpg', 'Kirada', 2, 14, 2),
('35VW035', 'Volkswagen', 'Passat', 2023, 'Benzin', 'Otomatik', 15000, 3100.00, 'passat.jpg', 'Müsait', 2, 15, 3),
('34PASS01', 'Volkswagen', 'Passat', 2020, 'Dizel', 'Otomatik', 85000, 2200.00, 'passat.jpg', 'Müsait', 2, 16, 1),
('01ADN001', 'Volkswagen', 'Passat', 2022, 'Benzin', 'Otomatik', 33000, 2750.00, 'passat.jpg', 'Kirada', 2, 17, 7),
('27GAZ027', 'Volkswagen', 'Passat', 2023, 'Dizel', 'Otomatik', 12000, 3200.00, 'passat.jpg', 'Müsait', 2, 18, 8),
('16BUR016', 'Volkswagen', 'Passat', 2021, 'Benzin', 'Otomatik', 48000, 2600.00, 'passat.jpg', 'Bakımda', 2, 19, 6),
('34COR001', 'Toyota', 'Corolla', 2023, 'Hibrit', 'Otomatik', 22000, 1900.00, 'corolla.jpg', 'Müsait', 2, 20, 1),
('06COR006', 'Toyota', 'Corolla', 2022, 'Benzin', 'Otomatik', 38000, 1750.00, 'corolla.jpg', 'Kirada', 2, 21, 2),
('35COR035', 'Toyota', 'Corolla', 2021, 'Hibrit', 'Otomatik', 55000, 1650.00, 'corolla.jpg', 'Müsait', 2, 22, 3),
('42COR042', 'Toyota', 'Corolla', 2024, 'Hibrit', 'Otomatik', 8000, 2100.00, 'corolla.jpg', 'Müsait', 2, 23, 4),
('07COR007', 'Toyota', 'Corolla', 2022, 'Benzin', 'Manuel', 41000, 1600.00, 'corolla.jpg', 'Müsait', 2, 24, 5),
('34TOY001', 'Toyota', 'Corolla', 2023, 'Hibrit', 'Otomatik', 19000, 1950.00, 'corolla.jpg', 'Bakımda', 2, 25, 1),
('16TOY016', 'Toyota', 'Corolla', 2020, 'Dizel', 'Manuel', 90000, 1400.00, 'corolla.jpg', 'Müsait', 2, 26, 6),
('34MEG001', 'Renault', 'Megane', 2023, 'Dizel', 'Otomatik', 25000, 2000.00, 'megane.jpg', 'Müsait', 2, 27, 1),
('06MEG006', 'Renault', 'Megane', 2022, 'Benzin', 'Otomatik', 36000, 1850.00, 'megane.jpg', 'Müsait', 2, 28, 2),
('35MEG035', 'Renault', 'Megane', 2021, 'Dizel', 'Manuel', 58000, 1600.00, 'megane.jpg', 'Kirada', 2, 29, 3),
('34RNO001', 'Renault', 'Megane', 2024, 'Hibrit', 'Otomatik', 5000, 2300.00, 'megane.jpg', 'Müsait', 2, 30, 1),
('42KON043', 'Renault', 'Megane', 2022, 'Dizel', 'Otomatik', 40000, 1900.00, 'megane.jpg', 'Müsait', 2, 31, 4),
('07ANT008', 'Renault', 'Megane', 2020, 'Benzin', 'Manuel', 82000, 1500.00, 'megane.jpg', 'Bakımda', 2, 32, 5),
('63SAN063', 'Renault', 'Megane', 2023, 'Dizel', 'Otomatik', 18000, 2050.00, 'megane.jpg', 'Müsait', 2, 33, 9),
('34CIV001', 'Honda', 'Civic', 2023, 'Benzin', 'Otomatik', 16000, 2400.00, 'civic.jpg', 'Müsait', 2, 34, 1),
('06CIV006', 'Honda', 'Civic', 2022, 'Benzin', 'Otomatik', 32000, 2200.00, 'civic.jpg', 'Kirada', 2, 35, 2),
('35CIV035', 'Honda', 'Civic', 2021, 'LPG', 'Otomatik', 54000, 1900.00, 'civic.jpg', 'Müsait', 2, 36, 3),
('34HON001', 'Honda', 'Civic', 2024, 'Benzin', 'Otomatik', 3000, 2600.00, 'civic.jpg', 'Müsait', 2, 37, 1),
('16CIV016', 'Honda', 'Civic', 2022, 'Benzin', 'Otomatik', 28000, 2300.00, 'civic.jpg', 'Bakımda', 2, 38, 6),
('07CIV007', 'Honda', 'Civic', 2020, 'Benzin', 'Otomatik', 65000, 1800.00, 'civic.jpg', 'Müsait', 2, 39, 5),
('34FOC001', 'Ford', 'Focus', 2023, 'Benzin', 'Otomatik', 19000, 2100.00, 'focus.jpg', 'Müsait', 2, 40, 1),
('06FOC006', 'Ford', 'Focus', 2022, 'Dizel', 'Otomatik', 34000, 1950.00, 'focus.jpg', 'Kirada', 2, 41, 2),
('35FOC035', 'Ford', 'Focus', 2021, 'Benzin', 'Manuel', 51000, 1700.00, 'focus.jpg', 'Müsait', 2, 42, 3),
('34FRD001', 'Ford', 'Focus', 2024, 'Hibrit', 'Otomatik', 7000, 2400.00, 'focus.jpg', 'Müsait', 2, 43, 1),
('42FOC042', 'Ford', 'Focus', 2020, 'Dizel', 'Manuel', 75000, 1600.00, 'focus.jpg', 'Bakımda', 2, 44, 4),
('01FOC001', 'Ford', 'Focus', 2022, 'Benzin', 'Otomatik', 26000, 2000.00, 'focus.jpg', 'Müsait', 2, 45, 7),
('34EGE001', 'Fiat', 'Egea', 2023, 'Dizel', 'Manuel', 25000, 1300.00, 'egea.jpg', 'Müsait', 1, 46, 1),
('34EGE002', 'Fiat', 'Egea', 2024, 'Hibrit', 'Otomatik', 10000, 1600.00, 'egea.jpg', 'Müsait', 1, 47, 1),
('06EGE006', 'Fiat', 'Egea', 2022, 'Benzin', 'Manuel', 45000, 1100.00, 'egea.jpg', 'Kirada', 1, 48, 2),
('35EGE035', 'Fiat', 'Egea', 2021, 'Dizel', 'Manuel', 68000, 1000.00, 'egea.jpg', 'Müsait', 1, 49, 3),
('42EGE042', 'Fiat', 'Egea', 2023, 'Benzin', 'Otomatik', 20000, 1400.00, 'egea.jpg', 'Müsait', 1, 50, 4),
('07EGE007', 'Fiat', 'Egea', 2022, 'Dizel', 'Manuel', 39000, 1200.00, 'egea.jpg', 'Bakımda', 1, 51, 5),
('16EGE016', 'Fiat', 'Egea', 2020, 'Benzin', 'Manuel', 95000, 950.00, 'egea.jpg', 'Müsait', 1, 52, 6),
('27EGE027', 'Fiat', 'Egea', 2023, 'Hibrit', 'Otomatik', 15000, 1550.00, 'egea.jpg', 'Müsait', 1, 53, 8),
('63EGE063', 'Fiat', 'Egea', 2022, 'Dizel', 'Manuel', 42000, 1150.00, 'egea.jpg', 'Kirada', 1, 54, 9),
('34EGE003', 'Fiat', 'Egea', 2021, 'Benzin', 'Manuel', 60000, 1050.00, 'egea.jpg', 'Müsait', 1, 55, 1),
('34CRS001', 'Fiat', 'Egea Cross', 2023, 'Hibrit', 'Otomatik', 18000, 1700.00, 'egeacross.jpg', 'Müsait', 3, 56, 1),
('06CRS006', 'Fiat', 'Egea Cross', 2022, 'Benzin', 'Manuel', 35000, 1500.00, 'egeacross.jpg', 'Kirada', 3, 57, 2),
('35CRS035', 'Fiat', 'Egea Cross', 2024, 'Hibrit', 'Otomatik', 5000, 1900.00, 'egeacross.jpg', 'Müsait', 3, 58, 3),
('07CRS007', 'Fiat', 'Egea Cross', 2021, 'Dizel', 'Otomatik', 52000, 1600.00, 'egeacross.jpg', 'Müsait', 3, 59, 5),
('16CRS016', 'Fiat', 'Egea Cross', 2023, 'Benzin', 'Manuel', 22000, 1550.00, 'egeacross.jpg', 'Bakımda', 3, 60, 6),
('34FIA001', 'Fiat', 'Egea Cross', 2022, 'Dizel', 'Otomatik', 30000, 1650.00, 'egeacross.jpg', 'Müsait', 3, 61, 1),
('34CL001', 'Renault', 'Clio', 2023, 'Benzin', 'Otomatik', 16000, 1400.00, 'clio.jpg', 'Müsait', 1, 62, 1),
('34CL002', 'Renault', 'Clio', 2022, 'Dizel', 'Manuel', 38000, 1200.00, 'clio.jpg', 'Kirada', 1, 63, 1),
('06CL006', 'Renault', 'Clio', 2021, 'Benzin', 'Manuel', 65000, 1000.00, 'clio.jpg', 'Müsait', 1, 64, 2),
('35CL035', 'Renault', 'Clio', 2024, 'Hibrit', 'Otomatik', 8000, 1600.00, 'clio.jpg', 'Müsait', 1, 65, 3),
('42CL042', 'Renault', 'Clio', 2022, 'Benzin', 'Otomatik', 29000, 1350.00, 'clio.jpg', 'Müsait', 1, 66, 4),
('07CL007', 'Renault', 'Clio', 2020, 'Dizel', 'Manuel', 88000, 950.00, 'clio.jpg', 'Bakımda', 1, 67, 5),
('16CL016', 'Renault', 'Clio', 2023, 'Benzin', 'Otomatik', 12000, 1450.00, 'clio.jpg', 'Müsait', 1, 68, 6),
('34RNO002', 'Renault', 'Clio', 2021, 'LPG', 'Manuel', 55000, 1050.00, 'clio.jpg', 'Müsait', 1, 69, 1),
('27CL027', 'Renault', 'Clio', 2022, 'Dizel', 'Otomatik', 40000, 1300.00, 'clio.jpg', 'Kirada', 1, 70, 8),
('34HYU001', 'Hyundai', 'i20', 2023, 'Benzin', 'Otomatik', 14000, 1350.00, 'i20.jpg', 'Müsait', 1, 71, 1),
('06HYU006', 'Hyundai', 'i20', 2022, 'Benzin', 'Manuel', 32000, 1150.00, 'i20.jpg', 'Müsait', 1, 72, 2),
('35HYU035', 'Hyundai', 'i20', 2021, 'Dizel', 'Manuel', 58000, 1050.00, 'i20.jpg', 'Kirada', 1, 73, 3),
('42HYU042', 'Hyundai', 'i20', 2024, 'Benzin', 'Otomatik', 4000, 1550.00, 'i20.jpg', 'Müsait', 1, 74, 4),
('07HYU007', 'Hyundai', 'i20', 2022, 'Benzin', 'Otomatik', 27000, 1300.00, 'i20.jpg', 'Bakımda', 1, 75, 5),
('16HYU016', 'Hyundai', 'i20', 2020, 'LPG', 'Manuel', 75000, 900.00, 'i20.jpg', 'Müsait', 1, 76, 6),
('34I20001', 'Hyundai', 'i20', 2023, 'Benzin', 'Otomatik', 19000, 1400.00, 'i20.jpg', 'Müsait', 1, 77, 1),
('34OPL001', 'Opel', 'Corsa', 2023, 'Benzin', 'Otomatik', 13000, 1400.00, 'corsa.jpg', 'Müsait', 1, 78, 1),
('06OPL006', 'Opel', 'Corsa', 2022, 'Dizel', 'Manuel', 36000, 1200.00, 'corsa.jpg', 'Kirada', 1, 79, 2),
('35OPL035', 'Opel', 'Corsa', 2021, 'Benzin', 'Otomatik', 62000, 1150.00, 'corsa.jpg', 'Müsait', 1, 80, 3),
('07OPL007', 'Opel', 'Corsa', 2024, 'Elektrik', 'Otomatik', 6000, 1800.00, 'corsa.jpg', 'Müsait', 1, 81, 5),
('16OPL016', 'Opel', 'Corsa', 2022, 'Benzin', 'Manuel', 29000, 1250.00, 'corsa.jpg', 'Bakımda', 1, 82, 6),
('34CRS002', 'Opel', 'Corsa', 2020, 'Dizel', 'Manuel', 80000, 1000.00, 'corsa.jpg', 'Müsait', 1, 83, 1),
('34CTR001', 'Citroen', 'C3', 2023, 'Benzin', 'Otomatik', 17000, 1300.00, 'c3.jpg', 'Müsait', 1, 84, 1),
('06CTR006', 'Citroen', 'C3', 2022, 'Benzin', 'Manuel', 34000, 1100.00, 'c3.jpg', 'Kirada', 1, 85, 2),
('35CTR035', 'Citroen', 'C3', 2021, 'Dizel', 'Manuel', 59000, 1000.00, 'c3.jpg', 'Müsait', 1, 86, 3),
('07CTR007', 'Citroen', 'C3', 2024, 'Benzin', 'Otomatik', 5000, 1500.00, 'c3.jpg', 'Müsait', 1, 87, 5),
('42CTR042', 'Citroen', 'C3', 2022, 'Benzin', 'Otomatik', 26000, 1250.00, 'c3.jpg', 'Bakımda', 1, 88, 4),
('34DAC001', 'Dacia', 'Duster', 2023, 'Dizel', 'Manuel', 21000, 1600.00, 'duster.jpg', 'Müsait', 3, 89, 1),
('06DAC006', 'Dacia', 'Duster', 2022, 'LPG', 'Manuel', 42000, 1400.00, 'duster.jpg', 'Kirada', 3, 90, 2),
('35DAC035', 'Dacia', 'Duster', 2021, 'Dizel', 'Otomatik', 65000, 1500.00, 'duster.jpg', 'Müsait', 3, 91, 3),
('42DAC042', 'Dacia', 'Duster', 2024, 'Benzin', 'Otomatik', 9000, 1800.00, 'duster.jpg', 'Müsait', 3, 92, 4),
('07DAC007', 'Dacia', 'Duster', 2022, 'Dizel', 'Manuel', 38000, 1450.00, 'duster.jpg', 'Müsait', 3, 93, 5),
('16DAC016', 'Dacia', 'Duster', 2020, 'LPG', 'Manuel', 92000, 1200.00, 'duster.jpg', 'Bakımda', 3, 94, 6),
('34DST001', 'Dacia', 'Duster', 2023, 'Benzin', 'Otomatik', 15000, 1700.00, 'duster.jpg', 'Müsait', 3, 95, 1),
('34QSQ001', 'Nissan', 'Qashqai', 2023, 'Hibrit', 'Otomatik', 18000, 2400.00, 'qashqai.jpg', 'Müsait', 3, 96, 1),
('06QSQ006', 'Nissan', 'Qashqai', 2022, 'Dizel', 'Otomatik', 35000, 2200.00, 'qashqai.jpg', 'Kirada', 3, 97, 2),
('35QSQ035', 'Nissan', 'Qashqai', 2021, 'Benzin', 'Otomatik', 60000, 1900.00, 'qashqai.jpg', 'Müsait', 3, 98, 3),
('07QSQ007', 'Nissan', 'Qashqai', 2024, 'Hibrit', 'Otomatik', 6000, 2600.00, 'qashqai.jpg', 'Müsait', 3, 99, 5),
('34NIS001', 'Nissan', 'Qashqai', 2022, 'Benzin', 'Otomatik', 28000, 2100.00, 'qashqai.jpg', 'Bakımda', 3, 100, 1),
('16QSQ016', 'Nissan', 'Qashqai', 2020, 'Dizel', 'Manuel', 85000, 1750.00, 'qashqai.jpg', 'Müsait', 3, 101, 6),
('34PEU001', 'Peugeot', '3008', 2023, 'Dizel', 'Otomatik', 16000, 2500.00, 'peugeot3008.jpg', 'Müsait', 3, 102, 1),
('06PEU006', 'Peugeot', '3008', 2022, 'Benzin', 'Otomatik', 33000, 2300.00, 'peugeot3008.jpg', 'Kirada', 3, 103, 2),
('35PEU035', 'Peugeot', '3008', 2021, 'Dizel', 'Otomatik', 58000, 2000.00, 'peugeot3008.jpg', 'Müsait', 3, 104, 3),
('07PEU007', 'Peugeot', '3008', 2024, 'Hibrit', 'Otomatik', 5000, 2800.00, 'peugeot3008.jpg', 'Müsait', 3, 105, 5),
('34PGT001', 'Peugeot', '3008', 2022, 'Benzin', 'Otomatik', 25000, 2250.00, 'peugeot3008.jpg', 'Bakımda', 3, 106, 1),
('42PEU042', 'Peugeot', '3008', 2023, 'Dizel', 'Otomatik', 19000, 2450.00, 'peugeot3008.jpg', 'Müsait', 3, 107, 4),
('34JEEP01', 'Jeep', 'Renegade', 2023, 'Hibrit', 'Otomatik', 14000, 2600.00, 'renegade.jpg', 'Müsait', 3, 108, 1),
('06JEEP06', 'Jeep', 'Renegade', 2022, 'Benzin', 'Otomatik', 30000, 2300.00, 'renegade.jpg', 'Kirada', 3, 109, 2),
('35JEEP35', 'Jeep', 'Renegade', 2021, 'Benzin', 'Otomatik', 52000, 2000.00, 'renegade.jpg', 'Müsait', 3, 110, 3),
('07JEEP07', 'Jeep', 'Renegade', 2024, 'Hibrit', 'Otomatik', 4000, 2900.00, 'renegade.jpg', 'Müsait', 3, 111, 5),
('34REN001', 'Jeep', 'Renegade', 2022, 'Dizel', 'Otomatik', 28000, 2200.00, 'renegade.jpg', 'Bakımda', 3, 112, 1),
('34VIT001', 'Mercedes-Benz', 'Vito', 2023, 'Dizel', 'Otomatik', 15000, 3500.00, 'vito.jpg', 'Müsait', 5, 113, 1),
('06VIT006', 'Mercedes-Benz', 'Vito', 2022, 'Dizel', 'Otomatik', 35000, 3200.00, 'vito.jpg', 'Kirada', 5, 114, 2),
('35VIT035', 'Mercedes-Benz', 'Vito', 2021, 'Dizel', 'Otomatik', 60000, 2800.00, 'vito.jpg', 'Müsait', 5, 115, 3),
('07VIT007', 'Mercedes-Benz', 'Vito', 2024, 'Elektrik', 'Otomatik', 5000, 4000.00, 'vito.jpg', 'Müsait', 5, 116, 5),
('34VIP001', 'Mercedes-Benz', 'Vito', 2022, 'Dizel', 'Otomatik', 29000, 3100.00, 'vito.jpg', 'Bakımda', 5, 117, 1),
('16VIT016', 'Mercedes-Benz', 'Vito', 2020, 'Dizel', 'Manuel', 90000, 2500.00, 'vito.jpg', 'Müsait', 5, 118, 6),
('34SON001', 'Renault', 'Clio', 2024, 'Hibrit', 'Otomatik', 3000, 1650.00, 'clio.jpg', 'Müsait', 1, 119, 1),
('06SON002', 'Fiat', 'Egea', 2023, 'Dizel', 'Manuel', 21000, 1350.00, 'egea.jpg', 'Müsait', 1, 120, 2),
('35SON003', 'Toyota', 'Corolla', 2022, 'Hibrit', 'Otomatik', 39000, 1800.00, 'corolla.jpg', 'Kirada', 2, 121, 3),
('07SON004', 'Dacia', 'Duster', 2021, 'Dizel', 'Manuel', 56000, 1550.00, 'duster.jpg', 'Müsait', 3, 122, 5),
('34SON005', 'Honda', 'Civic', 2023, 'Benzin', 'Otomatik', 17000, 2450.00, 'civic.jpg', 'Müsait', 2, 123, 1),
('16SON006', 'Hyundai', 'i20', 2022, 'Benzin', 'Otomatik', 31000, 1400.00, 'i20.jpg', 'Müsait', 1, 124, 6),
('42SON007', 'Ford', 'Focus', 2020, 'Dizel', 'Manuel', 72000, 1650.00, 'focus.jpg', 'Bakımda', 2, 125, 4);


-- ==========================================================
-- 4) OPERASYONEL SÜREÇ VERİLERİ
-- ==========================================================
-- Bu bölümde kiralama, ödeme, bakım ve kullanıcı etkileşimi süreçlerini temsil eden örnek veriler eklenmiştir.

-- Araçların bakım süreçlerini test edebilmek amacıyla tamamlanmış ve devam eden bakım kayıtları eklenmiştir.
-- Bu veriler, araç durumunun otomatik güncellenmesi mekanizmasının doğrulanmasını sağlar.
INSERT INTO Bakim (arac_id, personel_id, bakim_nedeni, maliyet, giris_tarihi, cikis_tarihi, durum) VALUES
(4, 1, 'Fren balataları değişimi ve ağır bakım', 8500.00, '2025-10-10', NULL, 'Devam Ediyor'),
(5, 2, 'Yıllık periyodik yağ ve filtre değişimi', 4500.00, '2025-09-01', '2025-09-03', 'Tamamlandı'),
(1, 1, 'Dört adet kışlık lastik değişimi ve rot-balans', 14000.00, '2025-11-15', '2025-11-15', 'Tamamlandı'),
(8, 3, 'Klima kompresörü onarımı ve gaz dolumu', 6200.00, '2025-12-01', NULL, 'Devam Ediyor'),
(11, 2, 'Arazi sürüşü sonrası alt takım kontrolü', 3200.00, '2025-12-10', '2025-12-12', 'Tamamlandı'),
(14, 3, 'Detaylı iç ve dış boya koruma/seramik kaplama', 9500.00, '2025-12-15', NULL, 'Devam Ediyor'),
(22, 1, '10.000 km periyodik bakımı', 3800.00, '2025-11-20', '2025-11-21', 'Tamamlandı'),
(34, 3, 'Kaporta boya onarımı (Tampon çiziği)', 5500.00, '2025-12-18', NULL, 'Devam Ediyor'),
(19, 1, 'Akü değişimi ve şarj dinamosu kontrolü', 4200.00, '2025-10-25', '2025-10-25', 'Tamamlandı'),
(55, 2, 'Şanzıman yağı değişimi ve kontrol', 6000.00, '2025-12-05', '2025-12-06', 'Tamamlandı'),
(78, 2, 'Ön cam çatlak değişimi', 11000.00, '2025-12-19', NULL, 'Devam Ediyor'),
(92, 3, 'Egzoz emisyon ölçümü ve filtre temizliği', 2500.00, '2025-11-05', '2025-11-05', 'Tamamlandı'),
(41, 3, 'Silecek motoru değişimi', 1500.00, '2025-11-30', '2025-11-30', 'Tamamlandı'),
(66, 1, 'Motor arıza lambası tespiti ve oksijen sensörü değişimi', 5400.00, '2025-12-14', NULL, 'Devam Ediyor'),
(105, 1, 'AdBlue sistemi onarımı ve dolumu', 2800.00, '2025-11-12', '2025-11-13', 'Tamamlandı');


-- Kullanıcılar tarafından yapılan yorumlar eklenmiştir.
-- Hem onaylanmış hem de onay bekleyen yorumlar sayesinde yönetici onay mekanizması test edilmiştir.
INSERT INTO Yorum (musteri_id, yorum_metni, puan, tarih, durum, islem_yapan_personel_id, islem_tarihi) VALUES
(1, 'Mercedes kiraladım, araç gerçekten kusursuzdu.', 5, '2025-11-20', 'Onaylandı', 1, '2025-11-20 14:30:00'),
(2, 'Fiyatlar piyasaya göre yüksek ama kalite iyi.', 4, '2025-11-25', 'Onaylandı', 1, '2025-11-25 16:00:00'),
(3, 'Teslimat noktasında biraz bekledim ama personel nazikti.', 3, '2025-12-01', 'Onaylandı', 2, '2025-12-02 09:15:00'),
(4, 'Ekonomik sınıf araç yakıt cimrisi çıktı.', 5, '2025-12-05', 'Onaylandı', 3, '2025-12-05 11:45:00'),
(5, 'Hibrit araç sessizliği muazzam.', 5, '2025-12-10', 'Onaylandı', 1, '2025-12-10 13:20:00'),
(6, 'Navigasyon güncel değildi.', 3, '2025-12-12', 'Onaylandı', 2, '2025-12-12 15:00:00'),
(7, 'Duster tam bir arazi canavarı.', 4, '2025-12-14', 'Onaylandı', 3, '2025-12-15 08:30:00'),
(3, 'Personel güler yüzlüydü.', 5, '2025-12-08', 'Onaylandı', 1, '2025-12-08 10:00:00'),
(1, 'Müşteri hizmetleri çok ilgili.', 5, '2025-12-15', 'Bekliyor', NULL, NULL),
(2, 'Vito çok geniş ve rahattı.', 5, '2025-12-16', 'Bekliyor', NULL, NULL),
(8, 'Uygulama çok pratik.', 5, '2025-12-17', 'Bekliyor', NULL, NULL),
(9, 'BMW ile harika bir deneyimdi.', 5, '2025-12-18', 'Bekliyor', NULL, NULL);


-- Kullanıcıların favori olarak işaretlediği araçlar eklenmiştir.
-- Bu yapı, müşteri ile araç arasındaki çoktan-çoğa ilişkiyi temsil etmektedir.
INSERT INTO Favori (musteri_id, arac_id) VALUES
(1, 20),(1, 30),(1, 7),(2, 1),(2, 102),(2, 113),(3, 62),(3, 46),(4, 13),(4, 56),(5, 108),(5, 89);


-- Kiralama sırasında seçilebilen sigorta paketleri eklenmiştir.
-- Bu paketler, dinamik fiyatlandırma yapısının test edilmesi amacıyla kullanılmıştır.
INSERT INTO SigortaPaketi (paket_adi, aciklama, gunluk_ucret) VALUES
('Temel Sigorta', 'Zorunlu Trafik Sigortası', 0),
('Mini Hasar Paketi', 'Lastik, Cam, Far Güvencesi', 500),
('Tam Kapsamlı (Kasko)', '%100 Güvence, 0 Muafiyet', 1000);


-- Kullanıcıların araç kiralama işlemlerini temsil eden geçmiş, aktif ve onay bekleyen kiralama kayıtları eklenmiştir.
-- Bu veriler tarih bazlı müsaitlik ve fiyat hesaplama senaryolarının test edilmesi için kullanılmıştır.
INSERT INTO Kiralama (musteri_id, arac_id, sigorta_paket_id, baslangic_tarihi, bitis_tarihi, alis_saati, teslim_saati, toplam_ucret, durum) 
VALUES
(1, 1, 3, '2025-11-10', '2025-11-13', '09:00', '15:00', 16500.00, 'Tamamlandı'),
(2, 113, 2, '2025-12-05', '2025-12-08', '12:00', '15:00', 10500.00, 'Tamamlandı'),
(4, 46, 2, '2025-11-01', '2025-11-03', '15:00', '15:00', 2600.00, 'Tamamlandı'),
(7, 20, 2, '2025-11-25', '2025-11-26', '12:00', '12:00', 1900.00, 'Tamamlandı'),
(3, 56, 2, '2025-11-15', '2025-11-20', '12:00', '15:00', 8500.00, 'Tamamlandı'),
(10, 75, 1, '2025-12-10', '2025-12-12', '09:00', '12:00', 2800.00, 'Tamamlandı'),
(5, 89, 2, '2025-12-15', '2025-12-19', '09:00', '15:00', 6400.00, 'Tamamlandı'),
(6, 62, 3, '2025-12-18', '2025-12-25', '09:00', '09:00', 9800.00, 'Kirada'),
(8, 13, 3, '2025-12-19', '2025-12-21', '09:00', '15:00', 5600.00, 'Kirada'),
(3, 15, 1, '2025-12-20', '2025-12-23', '12:00', '09:00', 9300.00, 'Onaylandı'),
(9, 34, 2, '2025-12-22', '2025-12-24', '15:00', '15:00', 4800.00, 'Onaylandı'),
(1, 7, 2, '2025-12-28', '2025-12-30', '09:00', '15:00', 6400.00, 'Onaylandı'),
(2, 5, 3, '2025-12-30', '2026-01-02', '12:00', '09:00', 18000.00, 'Onaylandı'),
(4, 102, 1, '2026-01-01', '2026-01-05', '15:00', '12:00', 20000.00, 'Onaylandı');


-- Kiralama işlemlerine ait ödeme kayıtları eklenmiştir.
-- Güvenlik gereği kart numaralarının yalnızca son 4 hanesi veritabanında tutulmuştur.
INSERT INTO Odeme (kiralama_id, odeme_tutari, kart_sahibi, kart_no_son4, odeme_turu) VALUES
(1, 16500.00, 'Ayşe Yılmaz', '1020', 'Kredi Kartı'),
(2, 10500.00, 'Burak Çelik', '3040', 'Kredi Kartı'),
(3, 2600.00, 'Emre Arslan', '5060', 'Havale'),
(4, 1900.00, 'Ceren Özkan', '7080', 'Kredi Kartı'),
(5, 8500.00, 'Elif Koç', '9010', 'Kredi Kartı'),
(6, 2800.00, 'Tolga Tekin', '1122', 'Kredi Kartı'),
(7, 6400.00, 'Gamze Polat', '3344', 'Havale'),
(8, 9800.00, 'Hakan Doğan', '5566', 'Kredi Kartı'),
(9, 5600.00, 'Volkan Şahin', '7788', 'Kredi Kartı'),
(10, 9300.00, 'Elif Koç', '9900', 'Kredi Kartı'),
(11, 4800.00, 'Merve Aksoy', '2233', 'Havale'),
(12, 6400.00, 'Ayşe Yılmaz', '4455', 'Kredi Kartı');


-- ==========================================================
-- ARAÇ DURUMUNU OTOMATİK GÜNCELLEYEN PROSEDÜR
-- ==========================================================

DELIMITER $$

CREATE PROCEDURE sp_update_arac_durum()
BEGIN
  -- Bakımı devam eden araçlar "Bakımda" olarak işaretlenir
  UPDATE Arac a
  JOIN Bakim b ON b.arac_id = a.arac_id
  SET a.durum = 'Bakımda'
  WHERE b.durum = 'Devam Ediyor';

  -- Aktif kiralaması olan araçlar "Kirada" yapılır
  UPDATE Arac a
  SET a.durum = 'Kirada'
  WHERE a.durum <> 'Bakımda'
    AND EXISTS (
      SELECT 1 FROM Kiralama k
      WHERE k.arac_id = a.arac_id
        AND k.durum IN ('Onaylandı','Bekliyor','Kirada')
        AND CURDATE() BETWEEN k.baslangic_tarihi AND k.bitis_tarihi
    );

  -- Diğer tüm araçlar "Müsait" yapılır
  UPDATE Arac a
  SET a.durum = 'Müsait'
  WHERE a.durum <> 'Bakımda'
    AND NOT EXISTS (
      SELECT 1 FROM Kiralama k
      WHERE k.arac_id = a.arac_id
        AND k.durum IN ('Onaylandı','Bekliyor','Kirada')
        AND CURDATE() BETWEEN k.baslangic_tarihi AND k.bitis_tarihi
    );
END$$

DELIMITER ;
