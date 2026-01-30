from flask_mail import Mail, Message

mail = Mail()

def send_email(to, subject, template):
    """
    E-posta gönderme fonksiyonu
    
    Args:
        to: Alıcı e-posta adresi
        subject: E-posta konusu
        template: HTML şablon içeriği
    
    Returns:
        bool: Başarılı ise True, değilse False
    """
    try:
        msg = Message(subject, recipients=[to], html=template)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Gönderme Hatası: {e}")
        return False
