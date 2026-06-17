# DataScope v2.0 - Sistem Analizi ve Tasarımı

## Doküman Bilgileri

| Alan | Değer |
|------|-------|
| Versiyon | 2.0 |
| Tarih | 2024-12-04 |
| Durum | Aktif |
| Hedef Platform | Mastodon (Fediverse) |

---

## 1. Giriş

### 1.1 Amaç

Bu doküman, Sosyal Medya Veri Madenciliği ve Duygu Analizi Platformu'nun (DataScope) v2.0 sürümünün teknik tasarımını tanımlar.

### 1.2 Kapsam

Sistem aşağıdaki işlevleri yerine getirir:

1. Mastodon platformundan hashtag bazlı veri çekme
2. Çekilen verileri temizleme ve normalize etme
3. Duygu analizi yapma (Google Cloud Natural Language API)
4. Sonuçları görselleştirme ve raporlama

### 1.3 Önceki Sistemden Çıkarılan Dersler

| Sorun | Çözüm |
|-------|-------|
| Birden fazla veri kaynağı arasında otomatik geçiş (fallback) yapılıyordu | Tek kaynak kullanılır, başarısız olursa hata verilir |
| API fonksiyonları yanlış parametrelerle çağrılıyordu | Her API çağrısı test edilmiş ve doğrulanmış parametrelerle yapılır |
| Hata mesajları yetersizdi | Her hata detaylı mesaj ve çözüm önerisi içerir |
| Modüller arası bağımlılıklar belirsizdi | Her modül bağımsız çalışır, açık arayüzler kullanılır |
| Kod tekrarı fazlaydı | Ortak işlevler utility modüllerinde toplanır |

---

## 2. Sistem Mimarisi

### 2.1 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                        KULLANICI ARAYÜZÜ                        │
│                      (CLI veya run.sh script)                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          ANA ORKESTRATÖR                        │
│                            (main.py)                            │
│  • Argüman ayrıştırma                                           │
│  • İş akışı yönetimi                                            │
│  • Hata yönetimi                                                │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VERİ ÇEKME   │       │  VERİ TEMİZ.  │       │   ANALİZ      │
│   MODÜLÜ      │       │    MODÜLÜ     │       │   MODÜLÜ      │
│               │       │               │       │               │
│ mastodon.py   │──────▶│ cleaning.py   │──────▶│ analysis.py   │
└───────────────┘       └───────────────┘       └───────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────┐
│                    ÇIKTI MODÜLLERI                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ GÖRSEL.     │  │ RAPORLAMA   │  │ VERİ KAYIT  │   │
│  │ visual.py   │  │ report.py   │  │ storage.py  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└───────────────────────────────────────────────────────┘
```

### 2.2 Dizin Yapısı

```
ika-vms-v2/
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── mastodon.py          # Mastodon API entegrasyonu
│   │   └── base.py              # Temel scraper sınıfı (genişleme için)
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── cleaning.py          # Veri temizleme
│   │   └── normalizer.py        # Veri normalizasyonu
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── sentiment.py         # Duygu analizi
│   │   └── statistics.py        # İstatistiksel analiz
│   ├── output/
│   │   ├── __init__.py
│   │   ├── visualization.py     # Grafik oluşturma
│   │   ├── report.py            # PDF rapor oluşturma
│   │   └── storage.py           # Veri kaydetme
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Yapılandırma yönetimi
│       ├── logger.py            # Loglama
│       └── exceptions.py        # Özel hata sınıfları
├── data/                        # Veri dosyaları
├── outputs/                     # Çıktı dosyaları
├── logs/                        # Log dosyaları
├── credentials/                 # API anahtarları
├── tests/                       # Test dosyaları
├── main.py                      # Ana giriş noktası
├── run.sh                       # Çalıştırma scripti
├── requirements.txt             # Python bağımlılıkları
├── Dockerfile                   # Docker yapılandırması
├── docker-compose.yml           # Docker Compose yapılandırması
└── README.md                    # Kullanım kılavuzu
```

---

## 3. Modül Spesifikasyonları

### 3.1 Mastodon Scraper Modülü

**Dosya:** `src/scraper/mastodon.py`

**Amaç:** Mastodon API'sinden hashtag bazlı veri çeker.

**Sınıf:** `MastodonScraper`

```python
class MastodonScraper:
    """
    Mastodon API'sinden veri çeken sınıf.
    
    Kullanım:
        scraper = MastodonScraper(instance_url="https://mastodon.social")
        posts = scraper.fetch_by_hashtag(hashtag="iklim", limit=100)
    """
    
    def __init__(self, instance_url: str) -> None:
        """
        Args:
            instance_url: Mastodon instance URL'i
                          Örnek: "https://mastodon.social"
                          
        Raises:
            ValueError: instance_url boş veya geçersiz ise
            ConnectionError: Instance'a bağlanılamıyorsa
        """
        pass
    
    def fetch_by_hashtag(self, hashtag: str, limit: int = 100) -> List[Dict]:
        """
        Belirtilen hashtag'e sahip postları çeker.
        
        Args:
            hashtag: Aranacak hashtag (# işareti olmadan)
                     Örnek: "iklim" veya "İklimKanunu"
            limit: Çekilecek maksimum post sayısı (varsayılan: 100)
            
        Returns:
            List[Dict]: Post listesi. Her post şu alanları içerir:
                - id: str - Post ID'si
                - text: str - Post metni (HTML temizlenmiş)
                - author: str - Yazar kullanıcı adı
                - created_at: str - Oluşturulma tarihi (ISO 8601)
                - reblogs_count: int - Reblog sayısı
                - favourites_count: int - Favori sayısı
                - replies_count: int - Yanıt sayısı
                
        Raises:
            HashtagNotFoundError: Hashtag bulunamazsa
            RateLimitError: Rate limit aşılırsa
            APIError: Diğer API hataları
        """
        pass
```

**Mastodon API Kullanımı:**

```python
# ✅ DOĞRU: Positional argument kullanımı
from mastodon import Mastodon

mastodon = Mastodon(api_base_url="https://mastodon.social")

# timeline_hashtag() MUTLAKA positional argument alır
timeline = mastodon.timeline_hashtag("iklim")  # ✅ DOĞRU
# timeline = mastodon.timeline_hashtag(hashtag="iklim")  # ❌ YANLIŞ

# search() kullanımı
results = mastodon.search("#iklim", result_type="hashtags")
```

**Hata Durumları:**

| Hata | Neden | Çözüm |
|------|-------|-------|
| `('Mastodon API returned error', 404, 'Not Found')` | Instance yanlış veya hashtag yok | Instance URL'ini kontrol et |
| `got an unexpected keyword argument` | Yanlış parametre kullanımı | Positional argument kullan |
| `MastodonNetworkError` | Ağ bağlantısı sorunu | İnternet bağlantısını kontrol et |

---

### 3.2 Veri Temizleme Modülü

**Dosya:** `src/processor/cleaning.py`

**Amaç:** Ham verileri temizler ve normalize eder.

**Fonksiyonlar:**

```python
def clean_html(text: str) -> str:
    """
    HTML etiketlerini kaldırır.
    
    Args:
        text: HTML içeren metin
        
    Returns:
        str: Temizlenmiş metin
        
    Örnek:
        >>> clean_html("<p>Merhaba <b>dünya</b></p>")
        "Merhaba dünya"
    """
    pass

def clean_text(text: str) -> str:
    """
    Metni temizler: URL, mention, özel karakterler kaldırılır.
    
    Args:
        text: Ham metin
        
    Returns:
        str: Temizlenmiş metin
        
    İşlemler:
        1. HTML etiketleri kaldırılır
        2. URL'ler kaldırılır
        3. Mention'lar (@kullanici) kaldırılır
        4. Fazla boşluklar temizlenir
        5. Başlangıç/bitiş boşlukları kaldırılır
    """
    pass

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame'deki tüm metinleri temizler.
    
    Args:
        df: Ham veri DataFrame'i
            Zorunlu kolonlar: ['id', 'text', 'author', 'created_at']
            
    Returns:
        pd.DataFrame: Temizlenmiş DataFrame
            Eklenen kolonlar: ['cleaned_text']
            
    Raises:
        ValueError: Zorunlu kolon eksikse
    """
    pass
```

---

### 3.3 Duygu Analizi Modülü

**Dosya:** `src/analyzer/sentiment.py`

**Amaç:** Google Cloud Natural Language API ile duygu analizi yapar.

**Sınıf:** `SentimentAnalyzer`

```python
class SentimentAnalyzer:
    """
    Google Cloud Natural Language API ile duygu analizi.
    
    Gereksinimler:
        - Google Cloud hesabı
        - Natural Language API etkinleştirilmiş
        - Service account key JSON dosyası
        - GOOGLE_APPLICATION_CREDENTIALS ortam değişkeni
        
    Kullanım:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Bu çok güzel bir haber!")
        print(result)  # {'score': 0.8, 'magnitude': 0.9, 'label': 'positive'}
    """
    
    def __init__(self) -> None:
        """
        Google Cloud client'ı başlatır.
        
        Raises:
            CredentialsError: API anahtarı bulunamazsa
            APINotEnabledError: API etkin değilse
        """
        pass
    
    def analyze(self, text: str) -> Dict:
        """
        Tek bir metin için duygu analizi yapar.
        
        Args:
            text: Analiz edilecek metin (min 1, max 5000 karakter)
            
        Returns:
            Dict:
                - score: float - Duygu skoru (-1.0 ile 1.0 arası)
                - magnitude: float - Duygu yoğunluğu (0.0 ile inf arası)
                - label: str - Etiket ("positive", "negative", "neutral")
                
        Raises:
            ValueError: Metin boş veya çok uzunsa
            QuotaExceededError: API kotası aşılmışsa
        """
        pass
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Birden fazla metin için duygu analizi yapar.
        
        Args:
            texts: Analiz edilecek metin listesi
            
        Returns:
            List[Dict]: Her metin için analiz sonucu
            
        Not:
            - Rate limiting otomatik uygulanır
            - Başarısız analizler None döner
        """
        pass
```

**Duygu Etiketleme Kuralları:**

| Skor Aralığı | Etiket |
|--------------|--------|
| score >= 0.25 | positive |
| score <= -0.25 | negative |
| -0.25 < score < 0.25 | neutral |

---

### 3.4 Görselleştirme Modülü

**Dosya:** `src/output/visualization.py`

**Amaç:** Analiz sonuçlarını görselleştirir.

**Fonksiyonlar:**

```python
def create_sentiment_distribution(df: pd.DataFrame, output_path: str) -> None:
    """
    Duygu dağılımı pasta grafiği oluşturur.
    
    Args:
        df: Analiz edilmiş DataFrame
            Zorunlu kolonlar: ['sentiment_label']
        output_path: Çıktı dosya yolu (PNG)
        
    Çıktı:
        - Pasta grafiği: Pozitif, Negatif, Nötr oranları
        - Türkçe etiketler
        - Yüzde değerleri
    """
    pass

def create_wordcloud(df: pd.DataFrame, output_path: str) -> None:
    """
    Kelime bulutu oluşturur.
    
    Args:
        df: Temizlenmiş DataFrame
            Zorunlu kolonlar: ['cleaned_text']
        output_path: Çıktı dosya yolu (PNG)
        
    Özellikler:
        - Türkçe karakter desteği
        - Stopword filtreleme
        - Maksimum 200 kelime
    """
    pass

def create_time_series(df: pd.DataFrame, output_path: str) -> None:
    """
    Zaman serisi grafiği oluşturur.
    
    Args:
        df: Tarih bilgisi içeren DataFrame
            Zorunlu kolonlar: ['created_at', 'sentiment_score']
        output_path: Çıktı dosya yolu (PNG)
    """
    pass
```

---

### 3.5 Raporlama Modülü

**Dosya:** `src/output/report.py`

**Amaç:** PDF formatında analiz raporu oluşturur.

**Fonksiyon:**

```python
def create_pdf_report(
    df: pd.DataFrame,
    stats: Dict,
    graphs: Dict[str, str],
    output_path: str
) -> None:
    """
    PDF rapor oluşturur.
    
    Args:
        df: Analiz edilmiş DataFrame
        stats: İstatistik sözlüğü
            - total_posts: int
            - positive_count: int
            - negative_count: int
            - neutral_count: int
            - avg_score: float
        graphs: Grafik dosya yolları
            - sentiment_dist: str
            - wordcloud: str
            - time_series: str
        output_path: Çıktı dosya yolu (PDF)
        
    Özellikler:
        - Türkçe karakter desteği (DejaVu Sans font)
        - A4 sayfa boyutu
        - Grafik yerleştirme
        - Tablo formatlaması
    """
    pass
```

**Türkçe Karakter Desteği:**

```python
# PDF için font kaydı
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# DejaVu Sans fontu kaydedilir
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
```

---

## 4. Veri Yapıları

### 4.1 Post Veri Yapısı

```python
@dataclass
class Post:
    """Mastodon post veri yapısı."""
    
    id: str                  # Benzersiz post ID'si
    text: str                # Ham metin içeriği
    cleaned_text: str        # Temizlenmiş metin
    author: str              # Yazar kullanıcı adı
    created_at: datetime     # Oluşturulma tarihi
    reblogs_count: int       # Reblog sayısı
    favourites_count: int    # Favori sayısı
    replies_count: int       # Yanıt sayısı
    instance: str            # Kaynak instance URL'i
    sentiment_score: float   # Duygu skoru (-1.0 ile 1.0)
    sentiment_label: str     # Duygu etiketi
```

### 4.2 DataFrame Kolon Yapısı

| Kolon | Tip | Açıklama | Zorunlu |
|-------|-----|----------|---------|
| id | str | Post ID | Evet |
| text | str | Ham metin | Evet |
| cleaned_text | str | Temizlenmiş metin | Hayır (temizleme sonrası) |
| author | str | Yazar | Evet |
| created_at | str | Tarih (ISO 8601) | Evet |
| reblogs_count | int | Reblog sayısı | Hayır |
| favourites_count | int | Favori sayısı | Hayır |
| replies_count | int | Yanıt sayısı | Hayır |
| instance | str | Kaynak instance | Hayır |
| sentiment_score | float | Duygu skoru | Hayır (analiz sonrası) |
| sentiment_label | str | Duygu etiketi | Hayır (analiz sonrası) |

---

## 5. İş Akışı

### 5.1 Ana İş Akışı

```
1. BAŞLAT
   │
2. Argümanları ayrıştır
   │  ├── --hashtag: Aranacak hashtag
   │  ├── --instance: Mastodon instance URL'i
   │  ├── --limit: Maksimum post sayısı
   │  └── --output-dir: Çıktı dizini
   │
3. Mastodon'dan veri çek
   │  ├── Instance'a bağlan
   │  ├── timeline_hashtag() ile postları al
   │  └── Veriyi DataFrame'e dönüştür
   │
4. Veriyi temizle
   │  ├── HTML etiketlerini kaldır
   │  ├── URL'leri kaldır
   │  ├── Mention'ları kaldır
   │  └── cleaned_text kolonunu oluştur
   │
5. Duygu analizi yap
   │  ├── Google Cloud API'ye bağlan
   │  ├── Her post için analiz yap
   │  └── sentiment_score ve sentiment_label ekle
   │
6. İstatistikleri hesapla
   │  ├── Toplam post sayısı
   │  ├── Pozitif/Negatif/Nötr dağılımı
   │  └── Ortalama skor
   │
7. Görselleştirmeler oluştur
   │  ├── Duygu dağılımı grafiği
   │  ├── Kelime bulutu
   │  └── Zaman serisi (varsa)
   │
8. PDF rapor oluştur
   │
9. Veriyi kaydet (CSV)
   │
10. BİTİR
```

### 5.2 Hata Yönetimi Akışı

```
HER ADIMDA:
   │
   ├── Başarılı → Devam et
   │
   └── Hata oluştu
       │
       ├── Hata detayını logla
       │
       ├── Kullanıcıya bilgi ver
       │   ├── Hata türü
       │   ├── Olası neden
       │   └── Çözüm önerisi
       │
       └── Programı sonlandır (exit code 1)
```

---

## 6. Yapılandırma

### 6.1 Ortam Değişkenleri

| Değişken | Açıklama | Zorunlu | Varsayılan |
|----------|----------|---------|------------|
| GOOGLE_APPLICATION_CREDENTIALS | Service account key dosya yolu | Evet | - |
| MASTODON_INSTANCE | Mastodon instance URL'i | Hayır | https://mastodon.social |
| LOG_LEVEL | Log seviyesi | Hayır | INFO |
| OUTPUT_DIR | Çıktı dizini | Hayır | ./outputs |

### 6.2 CLI Argümanları

```bash
python main.py [ARGÜMANLAR]

Argümanlar:
  --hashtag TEXT        Aranacak hashtag (zorunlu)
  --instance URL        Mastodon instance URL'i
                        Varsayılan: https://mastodon.social
  --limit INT           Maksimum post sayısı
                        Varsayılan: 100
  --output-dir PATH     Çıktı dizini
                        Varsayılan: ./outputs
  --skip-analysis       Duygu analizini atla
  --skip-visualization  Görselleştirmeyi atla
  --skip-report         PDF rapor oluşturmayı atla
  --test-mode           Test modu (örnek veri kullan)
  --verbose             Detaylı çıktı
  --help                Yardım mesajını göster

Örnekler:
  python main.py --hashtag iklim --limit 50
  python main.py --hashtag İklimKanunu --instance https://mastodon.tr
  python main.py --test-mode --hashtag test
```

---

## 7. Hata Sınıfları

**Dosya:** `src/utils/exceptions.py`

```python
class IKAVMSError(Exception):
    """Temel hata sınıfı."""
    pass

class ScraperError(IKAVMSError):
    """Veri çekme hatası."""
    pass

class HashtagNotFoundError(ScraperError):
    """Hashtag bulunamadı."""
    
    def __init__(self, hashtag: str, instance: str):
        self.message = (
            f"'{hashtag}' hashtag'i '{instance}' instance'ında bulunamadı.\n"
            f"Çözüm önerileri:\n"
            f"  1. Hashtag'in doğru yazıldığından emin olun\n"
            f"  2. Farklı bir instance deneyin (örn: mastodon.social)\n"
            f"  3. Hashtag'in o instance'da kullanıldığından emin olun"
        )
        super().__init__(self.message)

class RateLimitError(ScraperError):
    """Rate limit aşıldı."""
    
    def __init__(self, retry_after: int = 60):
        self.message = (
            f"Mastodon API rate limit'i aşıldı.\n"
            f"Çözüm: {retry_after} saniye bekleyip tekrar deneyin."
        )
        super().__init__(self.message)

class AnalysisError(IKAVMSError):
    """Analiz hatası."""
    pass

class CredentialsError(AnalysisError):
    """API anahtarı hatası."""
    
    def __init__(self):
        self.message = (
            "Google Cloud API anahtarı bulunamadı.\n"
            "Çözüm:\n"
            "  1. Service account key dosyasını indirin\n"
            "  2. GOOGLE_APPLICATION_CREDENTIALS ortam değişkenini ayarlayın:\n"
            "     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
        )
        super().__init__(self.message)

class QuotaExceededError(AnalysisError):
    """API kotası aşıldı."""
    
    def __init__(self):
        self.message = (
            "Google Cloud API kotası aşıldı.\n"
            "Çözüm:\n"
            "  1. Google Cloud Console'dan kotanızı kontrol edin\n"
            "  2. Aylık ücretsiz kotayı bekleyin veya ödeme yapın"
        )
        super().__init__(self.message)
```

---

## 8. Test Stratejisi

### 8.1 Birim Testleri

```python
# tests/test_mastodon.py

def test_mastodon_scraper_init():
    """Instance URL doğrulaması."""
    scraper = MastodonScraper("https://mastodon.social")
    assert scraper.instance_url == "https://mastodon.social"

def test_mastodon_scraper_invalid_url():
    """Geçersiz URL hatası."""
    with pytest.raises(ValueError):
        MastodonScraper("invalid-url")

def test_fetch_by_hashtag():
    """Hashtag ile veri çekme."""
    scraper = MastodonScraper("https://mastodon.social")
    posts = scraper.fetch_by_hashtag("python", limit=5)
    assert len(posts) <= 5
    assert all("id" in post for post in posts)
```

### 8.2 Entegrasyon Testleri

```python
# tests/test_integration.py

def test_full_pipeline():
    """Tam iş akışı testi."""
    # 1. Veri çek
    scraper = MastodonScraper("https://mastodon.social")
    posts = scraper.fetch_by_hashtag("test", limit=3)
    
    # 2. Temizle
    df = pd.DataFrame(posts)
    df = process_dataframe(df)
    
    # 3. Analiz (mock)
    # ...
    
    # 4. Doğrula
    assert "cleaned_text" in df.columns
```

---

## 9. Docker Yapılandırması

### 9.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY src/ ./src/
COPY main.py .

# Dizinler
RUN mkdir -p /app/data /app/outputs /app/logs

# Ortam değişkenleri
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/key.json

ENTRYPOINT ["python", "main.py"]
```

### 9.2 docker-compose.yml

```yaml
services:
  ika-vms:
    build: .
    container_name: ika-vms
    volumes:
      - ./data:/app/data
      - ./outputs:/app/outputs
      - ./credentials:/app/credentials:ro
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/key.json
```

---

## 10. Kullanım Örnekleri

### 10.1 Temel Kullanım

```bash
# Docker ile
docker compose run --rm ika-vms --hashtag iklim --limit 50

# Python ile
python main.py --hashtag iklim --limit 50
```

### 10.2 Farklı Instance Kullanımı

```bash
# Türkçe instance
docker compose run --rm ika-vms \
    --hashtag iklim \
    --instance https://mastodon.tr \
    --limit 100
```

### 10.3 Test Modu

```bash
# Örnek veri ile test
docker compose run --rm ika-vms --test-mode --hashtag test
```

### 10.4 Sadece Veri Çekme

```bash
# Analiz ve rapor olmadan sadece veri çek
docker compose run --rm ika-vms \
    --hashtag iklim \
    --skip-analysis \
    --skip-visualization \
    --skip-report
```

---

## 11. Çıktı Dosyaları

| Dosya | Açıklama | Format |
|-------|----------|--------|
| `outputs/veri.csv` | Çekilen ve analiz edilmiş veri | CSV |
| `outputs/sentiment_distribution.png` | Duygu dağılımı grafiği | PNG |
| `outputs/wordcloud.png` | Kelime bulutu | PNG |
| `outputs/time_series.png` | Zaman serisi grafiği | PNG |
| `outputs/rapor.pdf` | Analiz raporu | PDF |
| `logs/ika-vms.log` | Uygulama logları | TXT |

---

## 12. Genişletilebilirlik

### 12.1 Yeni Veri Kaynağı Ekleme

Yeni bir veri kaynağı eklemek için:

1. `src/scraper/` altında yeni modül oluştur
2. `BaseScraper` sınıfından türet
3. `fetch_by_hashtag()` metodunu implement et

```python
# src/scraper/base.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Temel scraper sınıfı."""
    
    @abstractmethod
    def fetch_by_hashtag(self, hashtag: str, limit: int) -> List[Dict]:
        """Hashtag ile veri çeker."""
        pass

# src/scraper/new_platform.py
class NewPlatformScraper(BaseScraper):
    def fetch_by_hashtag(self, hashtag: str, limit: int) -> List[Dict]:
        # Platform-specific implementation
        pass
```

### 12.2 Yeni Analiz Yöntemi Ekleme

1. `src/analyzer/` altında yeni modül oluştur
2. Standart giriş/çıkış formatını kullan

```python
# src/analyzer/new_analysis.py
def analyze_new_metric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Yeni metrik analizi.
    
    Args:
        df: Veri DataFrame'i
        
    Returns:
        pd.DataFrame: Yeni kolonlar eklenmiş DataFrame
    """
    # Implementation
    return df
```

---

## 13. Sürüm Geçmişi

| Versiyon | Tarih | Değişiklikler |
|----------|-------|---------------|
| 2.0 | 2024-12-04 | Sistem yeniden tasarlandı, sadece Mastodon desteği |
| 1.0 | 2024-11-XX | İlk sürüm (Twitter/X + Reddit + Mastodon) |

---

## 14. Referanslar

- [Mastodon API Dokümantasyonu](https://docs.joinmastodon.org/api/)
- [Mastodon.py Kütüphanesi](https://mastodonpy.readthedocs.io/)
- [Google Cloud Natural Language API](https://cloud.google.com/natural-language/docs)
- [ReportLab PDF Kütüphanesi](https://www.reportlab.com/docs/reportlab-userguide.pdf)

---

**Doküman Sonu**

