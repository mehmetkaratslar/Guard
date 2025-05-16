# File: guard_pc_app/ml/train_fall_detection.py
# Açıklama: Düşme algılama için derin öğrenme modelini eğiten modül
# Kullanım: python train_fall_detection.py --data_dir images/ --output_model resources/models/fall_model.pt

import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import numpy as np
import cv2
from PIL import Image
import random
from sklearn.model_selection import train_test_split
import time
import matplotlib.pyplot as plt

# Veri kümesi sınıfı - Resimleri ve etiketleri yükler
class FallDetectionDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        """
        Düşme algılama veri kümesini başlatır
        
        Args:
            image_paths (list): Görüntü dosyalarının yolları
            labels (list): 0: normal, 1: düşme etiketleri
            transform (callable, optional): Görüntülere uygulanacak dönüşüm
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        
    def __len__(self):
        """Veri kümesinin boyutunu döndürür"""
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        """Belirli bir indeksteki görüntüyü ve etiketi döndürür"""
        # Görüntüyü yükle ve RGB'ye dönüştür
        image = cv2.imread(self.image_paths[idx])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if self.transform:
            image = self.transform(image)
        
        # Etiketi tensor'a dönüştür
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return image, label

# Model tanımı - Düşme algılama için CNN mimarisi
class FallDetectionModel(nn.Module):
    def __init__(self):
        """Düşme algılama modelini başlatır"""
        super(FallDetectionModel, self).__init__()
        
        # Özellik çıkarma katmanları - Konvolüsyonel bloklar
        self.features = nn.Sequential(
            # İlk konvolüsyon bloğu: 3 kanallı girdi -> 32 kanallı çıktı
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),  # Batch normalizasyon ekledik
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 640x480 -> 320x240
            
            # İkinci konvolüsyon bloğu: 
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 320x240 -> 160x120
            
            # Üçüncü konvolüsyon bloğu: 
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 160x120 -> 80x60
            
            # Dördüncü konvolüsyon bloğu: 
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)  # 80x60 -> 40x30
        )
        
        # Düzleştirme ve tam bağlantılı katmanlar
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),  # Aşırı uyumu önlemek için dropout
            nn.Linear(256 * 40 * 30, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 2)  # 2 sınıf: [normal, düşme]
        )
    
    def forward(self, x):
        """İleri yayılım"""
        x = self.features(x)
        x = torch.flatten(x, 1)  # Düzleştirme
        x = self.classifier(x)
        return x  # CrossEntropyLoss için logits döndür

def train_fall_detection_model(data_dir, output_model_path, batch_size=8, num_epochs=30, learning_rate=0.001):
    """
    Düşme algılama modelini eğitir
    
    Args:
        data_dir (str): Görüntülerin bulunduğu dizin
        output_model_path (str): Modelin kaydedileceği dosya yolu
        batch_size (int): Mini-batch boyutu
        num_epochs (int): Eğitim döngü sayısı
        learning_rate (float): Öğrenme oranı
    """
    print(f"Düşme algılama modeli eğitiliyor...")
    print(f"Veri dizini: {data_dir}")
    print(f"Model çıktısı: {output_model_path}")
    
    # Veri yollarını ve etiketlerini hazırlama
    normal_images = []
    fall_images = []
    
    # Normal durumları topla
    normal_dir = os.path.join(data_dir, 'normal')
    if os.path.exists(normal_dir):
        for filename in os.listdir(normal_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                normal_images.append(os.path.join(normal_dir, filename))
    
    # Düşme durumlarını topla
    fall_dir = os.path.join(data_dir, 'fall')
    if os.path.exists(fall_dir):
        for filename in os.listdir(fall_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                fall_images.append(os.path.join(fall_dir, filename))
    
    print(f"Normal görüntü sayısı: {len(normal_images)}")
    print(f"Düşme görüntü sayısı: {len(fall_images)}")
    
    if len(normal_images) == 0 or len(fall_images) == 0:
        raise ValueError("Her iki sınıf için de görüntü bulunamadı. Lütfen veri dizinini kontrol edin.")
    
    # Tüm görüntüler ve etiketler
    all_images = normal_images + fall_images
    all_labels = [0] * len(normal_images) + [1] * len(fall_images)  # 0: normal, 1: düşme
    
    # Eğitim ve test kümelerini böl
    train_images, test_images, train_labels, test_labels = train_test_split(
        all_images, all_labels, test_size=0.2, random_state=42, stratify=all_labels
    )
    
    print(f"Eğitim seti boyutu: {len(train_images)}")
    print(f"Test seti boyutu: {len(test_images)}")
    
    # Veri dönüşümleri tanımla - Veri artırma ekleniyor
    train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((480, 640)),
        transforms.RandomHorizontalFlip(),  # Rastgele yatay çevirme
        transforms.RandomRotation(10),      # Rastgele döndürme
        transforms.ColorJitter(brightness=0.2, contrast=0.2),  # Parlaklık ve kontrast ayarı
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # ImageNet normalizasyonu
    ])
    
    test_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((480, 640)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Veri kümelerini oluştur
    train_dataset = FallDetectionDataset(train_images, train_labels, train_transform)
    test_dataset = FallDetectionDataset(test_images, test_labels, test_transform)
    
    # Veri yükleyicileri oluştur
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    
    # Cihazı seç (GPU varsa kullan)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Eğitim cihazı: {device}")
    
    # Modeli başlat
    model = FallDetectionModel().to(device)
    
    # Kayıp fonksiyonu ve optimize edici tanımla
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Öğrenme oranı zamanlayıcısı
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3
    )
        
    # Metrikler için listeler
    train_losses = []
    test_losses = []
    test_accuracies = []
    best_acc = 0.0
    
    # Eğitim başlangıç zamanı
    start_time = time.time()
    
    # Eğitim döngüsü
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            # Gradyanları sıfırla
            optimizer.zero_grad()
            
            # İleri yayılım
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Geri yayılım ve ağırlık güncelleme
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)
        
        # Epoch eğitim kaybı
        epoch_train_loss = running_loss / len(train_dataset)
        train_losses.append(epoch_train_loss)
        
        # Test aşaması
        model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item() * images.size(0)
                
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        # Epoch test kaybı ve doğruluğu
        epoch_test_loss = running_loss / len(test_dataset)
        epoch_test_acc = correct / total
        
        test_losses.append(epoch_test_loss)
        test_accuracies.append(epoch_test_acc)
        
        # Öğrenme oranını güncelle
        scheduler.step(epoch_test_loss)
        
        # İlerlemeyi yazdır
        print(f"Epoch {epoch+1}/{num_epochs}, "
              f"Train Loss: {epoch_train_loss:.4f}, "
              f"Test Loss: {epoch_test_loss:.4f}, "
              f"Test Acc: {epoch_test_acc:.4f}, "
              f"LR: {optimizer.param_groups[0]['lr']:.6f}")
        
        # En iyi modeli kaydet
        if epoch_test_acc > best_acc:
            best_acc = epoch_test_acc
            print(f"En iyi model kaydediliyor (Doğruluk: {best_acc:.4f})...")
            
            # Çıktı dizini yoksa oluştur
            os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
            
            # Modeli kaydet
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'accuracy': best_acc,
            }, output_model_path)
    
    # Toplam eğitim süresini hesapla
    total_time = time.time() - start_time
    print(f"Eğitim tamamlandı! Toplam süre: {total_time/60:.2f} dakika")
    print(f"En iyi test doğruluğu: {best_acc:.4f}")
    
    # Eğitim istatistiklerini görselleştir
    plt.figure(figsize=(12, 5))
    
    # Kayıp grafiği
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train')
    plt.plot(test_losses, label='Test')
    plt.title('Loss vs. Epoch')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Doğruluk grafiği
    plt.subplot(1, 2, 2)
    plt.plot(test_accuracies, label='Test Accuracy')
    plt.title('Accuracy vs. Epoch')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.tight_layout()
    
    # Grafik dosyasını kaydet
    graph_path = os.path.join(os.path.dirname(output_model_path), 'training_stats.png')
    plt.savefig(graph_path)
    print(f"Eğitim istatistikleri grafiği kaydedildi: {graph_path}")
    
    plt.show()
    
    return model

if __name__ == '__main__':
    # Komut satırı argümanlarını ayarla
    parser = argparse.ArgumentParser(description='Düşme Algılama Modeli Eğitimi')
    parser.add_argument('--data_dir', type=str, default='data/fall_detection',
                        help='Görüntülerin bulunduğu dizin (normal/ ve fall/ alt dizinleri içermelidir)')
    parser.add_argument('--output_model', type=str, default='resources/models/fall_model.pt',
                        help='Eğitilen modelin kaydedileceği dosya yolu')
    parser.add_argument('--batch_size', type=int, default=8, help='Mini-batch boyutu')
    parser.add_argument('--epochs', type=int, default=30, help='Eğitim döngü sayısı')
    parser.add_argument('--lr', type=float, default=0.001, help='Öğrenme oranı')
    
    args = parser.parse_args()
    
    # Model eğitimi fonksiyonunu çağır
    model = train_fall_detection_model(
        args.data_dir, 
        args.output_model,
        args.batch_size,
        args.epochs,
        args.lr
    )