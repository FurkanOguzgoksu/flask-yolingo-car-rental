import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Veritabanı Ayarları
# Veritabanı Ayarları
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'), 
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'arac_kiralama'),
    'raise_on_warnings': True
}

def get_db_connection():
    """
    MySQL veritabanı bağlantısı oluşturur
    
    Returns:
        mysql.connector.connection.MySQLConnection: Veritabanı bağlantısı
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        # ONLY_FULL_GROUP_BY modunu kapatarak esnek sorgulara izin ver
        cursor.execute("SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));")
        cursor.close()
        return conn
    except mysql.connector.Error as err:
        print(f"Veritabanı Bağlantı Hatası: {err}")
        return None
