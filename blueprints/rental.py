from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, make_response
from datetime import datetime
from fpdf import FPDF
import os
import db.vehicles as db_vehicles
import db.rentals as db_rentals
import db.customers as db_customers
from utils.email_utils import send_email

bp = Blueprint('rental', __name__)

@bp.route('/kiralama/<int:arac_id>', methods=['GET', 'POST'])
def kiralama(arac_id):
    """Kiralama işlemi"""
    if 'user_id' not in session:
        flash('kiralama yapmak için önce giriş yapmalısınız.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

    arac = db_vehicles.get_arac_by_id(arac_id)
    if not arac:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('index'))

    url_baslangic = request.args.get('baslangic')
    url_bitis = request.args.get('bitis')

    if request.method == 'POST':
        baslangic = request.form['baslangic_tarihi']
        bitis = request.form['bitis_tarihi']
        
        try:
            sigorta_paket_id = int(request.form.get('sigorta_paket_id', 0))
            sigorta_paket = db_rentals.get_sigorta_paketi_by_id(sigorta_paket_id)            
            sigorta_fiyati = float(sigorta_paket['gunluk_ucret']) if sigorta_paket else 0
            
        except (ValueError, TypeError):
            sigorta_fiyati = 0
            sigorta_paket_id = 0

        try:
            d1 = datetime.strptime(baslangic, "%Y-%m-%d")
            d2 = datetime.strptime(bitis, "%Y-%m-%d")
            gun_sayisi = (d2 - d1).days
        except ValueError:
            flash('Tarih formatı hatalı.', 'danger')
            return redirect(request.url)

        if gun_sayisi <= 0:
            flash('Bitiş tarihi başlangıç tarihinden sonra olmalıdır!', 'danger')
            return redirect(request.url) 
        
        arac_ucret = gun_sayisi * float(arac['gunluk_ucret'])
        toplam_sigorta_ucreti = gun_sayisi * sigorta_fiyati
        toplam_ucret = arac_ucret + toplam_sigorta_ucreti

        session['kiralama_bilgi'] = {
            'musteri_id': session['user_id'],
            'arac_id': arac_id,
            'baslangic_tarihi': baslangic,
            'bitis_tarihi': bitis,
            'alis_saati': request.form['alis_saati'],
            'teslim_saati': request.form['teslim_saati'],
            'gun_sayisi': gun_sayisi,
            'toplam_ucret': toplam_ucret,
            'sigorta_paket_id': sigorta_paket_id
        }

        return redirect(url_for('rental.odeme_yap'))

    return render_template('rental/kiralama.html', arac=arac, url_baslangic=url_baslangic, url_bitis=url_bitis)

@bp.route('/odeme', methods=['GET', 'POST'])
def odeme_yap():
    """Ödeme işlemi"""
    if 'kiralama_bilgi' not in session:
        return redirect(url_for('index'))

    arac = db_vehicles.get_arac_by_id(session['kiralama_bilgi']['arac_id'])

    if request.method == 'POST':
        
        odeme_bilgisi = {
            'sahip': request.form.get('kart_sahibi', '-'),
            'no': request.form.get('kart_no', '-'),
            'tur': request.form.get('odeme_turu')
        }
        
        # Veritabanına kaydet
        if db_rentals.add_kiralama(session['kiralama_bilgi'], odeme_bilgisi):
            # Müşteriye Onay Maili Gönder
            musteri = db_customers.get_musteri_by_id(session['user_id'])
            try:
                html_body = render_template('email/confirmation.html', 
                                            musteri=musteri, 
                                            arac=arac, 
                                            rez=session['kiralama_bilgi'])
                send_email(musteri['eposta'], "kiralama Onayı - Yolingo", html_body)
            except:
                pass 

            session.pop('kiralama_bilgi', None)
            flash(f'✅ Ödeme Başarılı! Keyifli sürüşler.', 'success')
            return redirect(url_for('rental.kiralamalarim'))
        else:
            flash('Bir hata oluştu.', 'danger')

    return render_template('rental/odeme.html', arac=arac)

@bp.route('/kiralamalarim')
def kiralamalarim():
    """Müşteri kiralamaları"""
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    kiralamalar = db_rentals.get_musteri_kiralamalari(session['user_id'])
    return render_template('customer/kiralamalarim.html', kiralamalar=kiralamalar)

@bp.route('/sozlesme-indir/<int:kiralama_id>')
def sozlesme_indir(kiralama_id):
    """PDF sözleşme indir"""
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    data = db_rentals.get_kiralama_detay_pdf(kiralama_id)
    
    if not data or (session.get('role') != 'admin' and data['musteri_id'] != session['user_id']):
        flash("Bu sözleşmeye erişim hakkınız yok.", "danger")
        return redirect(url_for('index'))

    # --- VERİ GÜVENLİĞİ VE YARDIMCI FONKSİYONLAR ---
    def safe_str(val):
        return str(val) if val is not None else ""

    # Karakter düzeltme (Font dosyası yoksa çökmemesi için)
    def tr_fix(text):
        if text is None: return ""
        text = str(text)
        mapping = {
            'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 
            'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C', '₺': 'TL'
        }
        for k, v in mapping.items(): 
            text = text.replace(k, v)
        return text

    # Renk Tanımları 
    COLOR_DARK_BLUE = (11, 18, 40)    # Lacivert Başlık
    COLOR_ORANGE = (249, 115, 22)     # Turuncu
    COLOR_GRAY_HEADER = (240, 240, 240) # Tablo Gri Başlık
    COLOR_BORDER = (0, 0, 0)          # Siyah Çerçeve

    pdf = FPDF()
    pdf.add_page()

    # --- FONT AYARLARI ---
    from flask import current_app
    font_path = os.path.join(current_app.root_path, 'static', 'fonts', 'DejaVuSans.ttf')
    font_yuklendi = False
    try:
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.add_font('DejaVu', 'B', font_path, uni=True) # Bold için de aynısını kullanıyoruz (Simüle)
        pdf.set_font('DejaVu', '', 10)
        font_yuklendi = True
    except:
        pdf.set_font("Helvetica", '', 10)
        font_yuklendi = False

    # Yazdırma sarmalayıcısı (Font yoksa tr_fix uygular)
    def yaz(text):
        return text if font_yuklendi else tr_fix(text)

    # 1. EN ÜST BANNER (LACİVERT ZEMİN)
    pdf.set_fill_color(*COLOR_DARK_BLUE)
    pdf.rect(0, 0, 210, 35, 'F') # Sayfa genişliği, 35mm yükseklik

    # Sol Üst: YOLINGO (Turuncu)
    pdf.set_xy(10, 8)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.set_font_size(22)
    pdf.set_font(family=pdf.font_family, style='B') # Bold
    pdf.cell(0, 10, text="YOLINGO", align='L')

    # Altındaki Beyaz Yazı
    pdf.set_xy(10, 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font_size(12)
    sehir_adi = safe_str(data.get('sehir_ad')).upper()
    pdf.cell(0, 8, text=yaz(f"ARAC KIRALAMA SOZLESMESI - {sehir_adi}"), align='L')

    # Sağ Üst: Sözleşme No ve Tarih (Beyaz)
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='') # Normal
    pdf.set_xy(120, 8)
    pdf.cell(80, 5, text=yaz(f"Sozlesme No: #RZ-{data['kiralama_id']}"), align='R', new_x="LMARGIN", new_y="NEXT")
    
    tarih_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    pdf.set_xy(120, 13)
    pdf.cell(80, 5, text=yaz(f"Duzenleme: {tarih_str}"), align='R')

    pdf.set_y(40) # Banner sonrası boşluk

    # 2. A ve B BÖLÜMLERİ (YAN YANA KUTULAR)
    y_start_ab = pdf.get_y()
    
    # --- SOL TARAF: A) KIRALAYAN ---
    pdf.set_fill_color(*COLOR_ORANGE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font_size(10)
    pdf.set_font(family=pdf.font_family, style='B')
    # Genişlik: 93mm (Sayfa 210mm - 20mm kenar / 2 yaklaşık)
    pdf.cell(93, 7, text=yaz(" A) KIRALAYAN (FIRMA)"), border=0, fill=True, align='L')
    
    # Firma Bilgileri (Altına)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='')
    pdf.ln(8)
    
    ofis_sehir = safe_str(data.get('sehir_ad')).upper()
    ofis_adres = safe_str(data.get('ofis_adres')).replace('\\n', ' ')
    ofis_tel = safe_str(data.get('ofis_telefon'))

    # Firma Adı (Bold gibi)
    pdf.set_font(family=pdf.font_family, style='B')
    pdf.cell(93, 5, text=yaz(f"YOLINGO {ofis_sehir} SUBESI"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(family=pdf.font_family, style='')
    
    # Adres (Multi-cell gerekebilir ama tek satır sığdıracağız görseldeki gibi)
    current_y = pdf.get_y()
    pdf.multi_cell(93, 5, text=yaz(ofis_adres))
    pdf.set_xy(10, pdf.get_y()) # Multi cell x'i bozar, düzelt
    
    pdf.cell(93, 5, text=yaz(ofis_sehir), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(93, 5, text=yaz(f"Tel: {ofis_tel}"), new_x="LMARGIN", new_y="NEXT")

    # --- SAĞ TARAF: B) KIRACI ---
    pdf.set_xy(107, y_start_ab) # 10mm sol margin + 93mm genişlik + 4mm boşluk
    
    pdf.set_fill_color(*COLOR_ORANGE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(family=pdf.font_family, style='B')
    pdf.set_font_size(10)
    pdf.cell(93, 7, text=yaz(" B) KIRACI (MUSTERI)"), border=0, fill=True, align='L')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='')
    pdf.set_xy(107, y_start_ab + 8)

    ad_soyad = f"{safe_str(data['ad']).upper()} {safe_str(data['soyad']).upper()}"
    kimlik = safe_str(data.get('tc_kimlik_no'))
    tel = safe_str(data['telefon'])
    email = safe_str(data['eposta'])

    pdf.set_font(family=pdf.font_family, style='B')
    pdf.cell(93, 5, text=yaz(ad_soyad), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(107)
    pdf.set_font(family=pdf.font_family, style='')
    pdf.cell(93, 5, text=yaz(f"TC/Pass: {kimlik}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(107)
    pdf.cell(93, 5, text=yaz(f"Tel: {tel}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(107)
    pdf.cell(93, 5, text=yaz(f"E-Posta: {email}"), new_x="LMARGIN", new_y="NEXT")

    # Boşluk bırak (En uzun kolon kadar aşağı in)
    pdf.set_y(y_start_ab + 35)

    # 3. C BÖLÜMÜ (ARAÇ BİLGİLERİ - TABLO GÖRÜNÜMÜ)
    pdf.set_fill_color(*COLOR_ORANGE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(family=pdf.font_family, style='B')
    pdf.set_font_size(10)
    pdf.cell(0, 7, text=yaz(" C) ARAC VE KIRALAMA BILGILERI"), border=0, fill=True, new_x="LMARGIN", new_y="NEXT")

    # Tablo Başlıkları (Gri Zemin)
    pdf.set_fill_color(*COLOR_GRAY_HEADER)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(8)
    
    # Sütun Genişlikleri: Marka(50), Plaka(40), Yakıt(50), Süre(50)
    pdf.cell(50, 7, text=yaz("MARKA / MODEL"), border=0, fill=True, align='C')
    pdf.cell(40, 7, text=yaz("PLAKA"), border=0, fill=True, align='C')
    pdf.cell(50, 7, text=yaz("YAKIT / VITES"), border=0, fill=True, align='C')
    pdf.cell(50, 7, text=yaz("SURE"), border=0, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")

    # Veri Hesaplama
    try:
        t1 = data['baslangic_tarihi']
        t2 = data['bitis_tarihi']
        if isinstance(t1, str): t1 = datetime.strptime(t1, "%Y-%m-%d")
        if isinstance(t2, str): t2 = datetime.strptime(t2, "%Y-%m-%d")
        gun_sayisi = (t2 - t1).days
        if gun_sayisi <= 0: gun_sayisi = 1
    except:
        gun_sayisi = 1

    # Tablo Verileri (Beyaz Zemin)
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='')
    # Alt çizgi eklemiyoruz, görselde temiz duruyor, sadece boşluk
    pdf.cell(50, 8, text=yaz(f"{safe_str(data['marka'])} {safe_str(data['model'])}"), align='C')
    pdf.cell(40, 8, text=yaz(safe_str(data['plaka'])), align='C')
    pdf.cell(50, 8, text=yaz(f"{safe_str(data['yakit_turu'])} / {safe_str(data.get('vites_turu', 'Otomatik'))}"), align='C')
    pdf.cell(50, 8, text=yaz(f"{gun_sayisi} GUN"), align='C', new_x="LMARGIN", new_y="NEXT")

    # Tarihler (Tablonun Altında)
    pdf.ln(2)
    pdf.set_font_size(8)
    pdf.cell(95, 5, text=yaz("ALIS TARIHI"), border=0)
    pdf.cell(95, 5, text=yaz("IADE TARIHI"), border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font_size(9)
    alis_saati = safe_str(data['alis_saati'])
    teslim_saati = safe_str(data['teslim_saati'])
    pdf.cell(95, 6, text=yaz(f"{safe_str(data['baslangic_tarihi'])} - {alis_saati}"), border=0)
    pdf.cell(95, 6, text=yaz(f"{safe_str(data['bitis_tarihi'])} - {teslim_saati}"), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # 4. D BÖLÜMÜ (HESAP DÖKÜMÜ)
    pdf.set_fill_color(*COLOR_ORANGE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(family=pdf.font_family, style='B')
    pdf.set_font_size(10)
    pdf.cell(0, 7, text=yaz(" D) HESAP DOKUMU VE ODEME DETAYLARI"), border=0, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(family=pdf.font_family, style='')
    pdf.set_font_size(9)
    pdf.ln(2)

    # Dökümler
    arac_gunluk = float(data['arac_gunluk_ucret'])
    arac_toplam = arac_gunluk * gun_sayisi

    sigorta_paket = safe_str(data.get('paket_adi', '-'))
    sigorta_gunluk = float(data.get('sigorta_gunluk_ucret') or 0)
    sigorta_toplam = sigorta_gunluk * gun_sayisi

    genel_toplam = float(data['toplam_ucret'])

    pdf.cell(130, 6, text=yaz(f"Arac Kiralama ({gun_sayisi} gun x {arac_gunluk:.2f} TL)"), border='B')
    pdf.cell(0, 6, text=yaz(f"{arac_toplam:.2f} TL"), border='B', align='R', new_x="LMARGIN", new_y="NEXT")

    if sigorta_toplam > 0:
        pdf.cell(130, 6, text=yaz(f"Sigorta Paketi: {sigorta_paket} ({gun_sayisi} gun x {sigorta_gunluk:.2f} TL)"), border='B')
        pdf.cell(0, 6, text=yaz(f"{sigorta_toplam:.2f} TL"), border='B', align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(family=pdf.font_family, style='B')
    pdf.set_font_size(11)
    pdf.cell(130, 8, text=yaz("GENEL TOPLAM"), border=0)
    pdf.cell(0, 8, text=yaz(f"{genel_toplam:.2f} TL"), border=0, align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # 5. E BÖLÜMÜ (KOŞULLAR - ÇERÇEVELİ)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='')
    pdf.cell(0, 6, text=yaz(" E) GENEL KIRALAMA KOSULLARI"), new_x="LMARGIN", new_y="NEXT")
    
    # Çerçeveli Metin
    pdf.set_font_size(7)
    kosullar = (
        "1. KULLANIM: Kiraci, araci karayollari trafik kanununa uygun kullanmayı kabul eder.\n"
        "2. KAZA: Herhangi bir kaza durumunda polis/jandarma raporu tutulmasi zorunludur.\n"
        "3. TESLIM GECIKMESI: 3 saati asan gecikmelerde 1 gunluk tam kira bedeli tahsil edilir.\n"
        "4. YAKIT: Arac teslim alindigi yakit seviyesinde iade edilmelidir.\n"
        "5. CEZALAR: Kiralama suresi icerisindeki tum trafik cezalari kiraciya aittir.\n"
        "6. SIGORTA: Alkol/uyusturucu etkisi altinda yapilan kazalar sigorta kapsami disindadir."
    )
    pdf.multi_cell(0, 4, text=yaz(kosullar), border=1, align='L')

    pdf.ln(15)

    # 6. İMZA ALANI
    pdf.set_font_size(9)
    pdf.set_font(family=pdf.font_family, style='B')
    pdf.cell(95, 5, text=yaz("TESLIM EDEN (YOLINGO)"), align='C')
    pdf.cell(95, 5, text=yaz("TESLIM ALAN (KIRACI)"), align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font(family=pdf.font_family, style='')
    pdf.set_font_size(8)
    pdf.cell(95, 4, text=yaz("Premium Yolingo Operasyon Birimi"), align='C')
    pdf.cell(95, 4, text=yaz("Beyan: Okudum, anladim, teslim aldim."), align='C', new_x="LMARGIN", new_y="NEXT")

    # PDF Çıktısını bytes olarak oluştur
    # FPDF2'de output() bytes döndürür ama bazen encode edilmesi gerekir
    try:
        # Önce direkt bytes olarak dene
        pdf_bytes = bytes(pdf.output())
    except:
        # Eğer çalışmazsa string olarak al ve encode et
        pdf_bytes = pdf.output().encode('latin-1')
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Sozlesme_{kiralama_id}.pdf'
    
    return response
