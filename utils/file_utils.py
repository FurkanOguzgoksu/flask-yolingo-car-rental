def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
    """
    Dosya uzantısının izin verilen listede olup olmadığını kontrol eder
    
    Args:
        filename: Kontrol edilecek dosya adı
        allowed_extensions: İzin verilen uzantılar seti
    
    Returns:
        bool: İzin veriliyorsa True, değilse False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
