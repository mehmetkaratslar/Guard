# guard_pc_app/utils/image_utils.py
import cv2
import numpy as np
import logging

def resize_image(image, width=None, height=None):
    """Görüntüyü yeniden boyutlandırır.
    
    Args:
        image (numpy.ndarray): Boyutlandırılacak görüntü
        width (int, optional): İstenen genişlik, None ise orantılı olarak hesaplanır
        height (int, optional): İstenen yükseklik, None ise orantılı olarak hesaplanır
        
    Returns:
        numpy.ndarray: Boyutlandırılmış görüntü
    """
    if image is None:
        return None
    
    if width is None and height is None:
        return image
    
    h, w = image.shape[:2]
    
    # Sadece genişlik verilmişse, yüksekliği orantılı olarak hesapla
    if width is not None and height is None:
        aspect = width / float(w)
        height = int(h * aspect)
    
    # Sadece yükseklik verilmişse, genişliği orantılı olarak hesapla
    elif height is not None and width is None:
        aspect = height / float(h)
        width = int(w * aspect)
    
    # Görüntüyü yeniden boyutlandır
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

def add_text_to_image(image, text, position, font_scale=1.0, color=(255, 255, 255), thickness=2):
    """Görüntüye metin ekler.
    
    Args:
        image (numpy.ndarray): Metin eklenecek görüntü
        text (str): Eklenecek metin
        position (tuple): Metnin konumu (x, y)
        font_scale (float, optional): Yazı tipi ölçeği
        color (tuple, optional): Yazı rengi (B, G, R)
        thickness (int, optional): Yazı kalınlığı
        
    Returns:
        numpy.ndarray: Metin eklenmiş görüntü
    """
    if image is None:
        return None
    
    # Görüntüyü kopyala
    result = image.copy()
    
    # Metni ekle
    cv2.putText(
        result,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA
    )
    
    return result

def draw_rect_on_image(image, rect, color=(0, 255, 0), thickness=2):
    """Görüntüye dikdörtgen çizer.
    
    Args:
        image (numpy.ndarray): Dikdörtgen çizilecek görüntü
        rect (tuple): Dikdörtgen koordinatları (x, y, w, h)
        color (tuple, optional): Çizgi rengi (B, G, R)
        thickness (int, optional): Çizgi kalınlığı
        
    Returns:
        numpy.ndarray: Dikdörtgen çizilmiş görüntü
    """
    if image is None:
        return None
    
    # Görüntüyü kopyala
    result = image.copy()
    
    # Dikdörtgen çiz
    x, y, w, h = rect
    cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
    
    return result

def draw_fall_detection_overlay(image, confidence, timestamp=None):
    """Düşme algılama yer paylaşımını görüntüye ekler.
    
    Args:
        image (numpy.ndarray): İşlenecek görüntü
        confidence (float): Düşme olasılığı (0-1 arası)
        timestamp (float, optional): Zaman damgası
        
    Returns:
        numpy.ndarray: Yer paylaşımı eklenmiş görüntü
    """
    if image is None:
        return None
    
    # Görüntüyü kopyala
    result = image.copy()
    
    # Görüntü boyutları
    h, w = result.shape[:2]
    
    # Alt bilgi çubuğu ekle
    bar_height = 60
    footer = np.zeros((bar_height, w, 3), dtype=np.uint8)
    footer[:] = (30, 30, 30)  # Koyu gri arka plan
    
    # Görüntü ile alt bilgi çubuğunu birleştir
    result = np.vstack((result, footer))
    
    # Düşme olasılığı metnini ekle
    conf_text = f"Düşme Olasılığı: %{confidence * 100:.2f}"
    font_scale = 0.7
    thickness = 2
    
    # Olasılığa göre renk belirle (düşük: yeşil, orta: sarı, yüksek: kırmızı)
    if confidence < 0.4:
        color = (0, 255, 0)  # Yeşil
    elif confidence < 0.7:
        color = (0, 255, 255)  # Sarı
    else:
        color = (0, 0, 255)  # Kırmızı
    
    result = add_text_to_image(
        result,
        conf_text,
        (10, h + 30),
        font_scale,
        color,
        thickness
    )
    
    # Zaman damgası varsa ekle
    if timestamp:
        import datetime
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")
        
        result = add_text_to_image(
            result,
            time_str,
            (w - 200, h + 30),
            font_scale,
            (255, 255, 255),
            thickness
        )
    
    return result

def image_to_bytes(image, format=".jpg", quality=90):
    """Görüntüyü bayt dizisine dönüştürür.
    
    Args:
        image (numpy.ndarray): Dönüştürülecek görüntü
        format (str, optional): Çıktı formatı ('.jpg', '.png', vb.)
        quality (int, optional): JPEG sıkıştırma kalitesi (0-100)
        
    Returns:
        bytes: Görüntü bayt dizisi
    """
    if image is None:
        return None
    
    try:
        # Formatı belirle
        if format.lower() in ['.jpg', '.jpeg']:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode(format, image, encode_param)
        else:
            _, buffer = cv2.imencode(format, image)
        
        return buffer.tobytes()
        
    except Exception as e:
        logging.error(f"Görüntü bayt dizisine dönüştürülürken hata: {str(e)}")
        return None

def bytes_to_image(byte_data):
    """Bayt dizisini görüntüye dönüştürür.
    
    Args:
        byte_data (bytes): Dönüştürülecek bayt dizisi
        
    Returns:
        numpy.ndarray: Oluşturulan görüntü
    """
    if byte_data is None:
        return None
    
    try:
        # Bayt dizisini numpy dizisine dönüştür
        buffer = np.frombuffer(byte_data, dtype=np.uint8)
        
        # Görüntüyü çöz
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        
        return image
        
    except Exception as e:
        logging.error(f"Bayt dizisi görüntüye dönüştürülürken hata: {str(e)}")
        return None

def apply_blur_to_regions(image, regions, kernel_size=(15, 15)):
    """Görüntüdeki belirli bölgelere bulanıklaştırma efekti uygular.
    
    Args:
        image (numpy.ndarray): İşlenecek görüntü
        regions (list): Bulanıklaştırılacak bölgelerin listesi [(x, y, w, h), ...]
        kernel_size (tuple, optional): Bulanıklaştırma çekirdeği boyutu
        
    Returns:
        numpy.ndarray: Bulanıklaştırılmış görüntü
    """
    if image is None or not regions:
        return image
    
    # Görüntüyü kopyala
    result = image.copy()
    
    # Her bölgeyi bulanıklaştır
    for region in regions:
        x, y, w, h = region
        
        # Geçerli bir bölge mi kontrol et
        if x >= 0 and y >= 0 and w > 0 and h > 0:
            # Bölgeyi kırp
            roi = result[y:y+h, x:x+w]
            
            # Bulanıklaştır
            blurred = cv2.GaussianBlur(roi, kernel_size, 0)
            
            # Bulanık bölgeyi orijinal görüntüye yerleştir
            result[y:y+h, x:x+w] = blurred
    
    return result