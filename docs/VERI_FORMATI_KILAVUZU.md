# 📁 DataScope v2.0 - Veri Dosyası Formatı Kılavuzu

Bu belge, DataScope sistemine yüklenecek veri dosyalarının nasıl hazırlanması gerektiğini açıklar.

---

## 📋 Genel Bilgiler

| Özellik | Değer |
|---------|-------|
| **Desteklenen Formatlar** | CSV, JSON |
| **Maksimum Dosya Boyutu** | 200 MB |
| **Karakter Kodlaması** | UTF-8 (önerilir) |

---

## 🔑 Zorunlu Sütunlar

Sisteme yüklenen dosyalarda aşağıdaki sütunlardan en az biri bulunmalıdır:

| Sütun Adı | Alternatif İsim | Açıklama | Örnek |
|-----------|-----------------|----------|-------|
| `text` | `content` | Gönderinin metin içeriği | "İklim değişikliği hepimizi etkiliyor!" |
| `author` | `username` | Gönderen kullanıcı adı | "@kullanici123" |
| `created_at` | - | Gönderinin tarihi | "2024-01-15T14:30:00Z" |
| `id` | `tweet_id` | Gönderinin benzersiz kimliği | "123456789" |

---

## 📄 CSV Formatı

### Örnek CSV Dosyası

```csv
id,text,author,created_at
1,"İklim kanunu hakkında konuşmalıyız!","kullanici1","2024-01-15T10:00:00Z"
2,"Sürdürülebilir enerji şart.","kullanici2","2024-01-15T11:30:00Z"
3,"Karbon salınımı azaltılmalı.","kullanici3","2024-01-15T12:45:00Z"
```

### CSV Kuralları

1. **Başlık Satırı**: İlk satır mutlaka sütun isimlerini içermelidir
2. **Ayraç**: Virgül (`,`) kullanılmalıdır
3. **Metin Alanları**: Virgül veya özel karakter içeren metinler çift tırnak (`"`) içinde olmalıdır
4. **Kodlama**: UTF-8 kodlaması kullanın (Türkçe karakterler için önemli)

---

## 📦 JSON Formatı

### Örnek JSON Dosyası (Dizi Formatı)

```json
[
  {
    "id": "1",
    "text": "İklim kanunu hakkında konuşmalıyız!",
    "author": "kullanici1",
    "created_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": "2",
    "text": "Sürdürülebilir enerji şart.",
    "author": "kullanici2",
    "created_at": "2024-01-15T11:30:00Z"
  },
  {
    "id": "3",
    "text": "Karbon salınımı azaltılmalı.",
    "author": "kullanici3",
    "created_at": "2024-01-15T12:45:00Z"
  }
]
```

### Örnek JSON Dosyası (JSONL/Satır Formatı)

```jsonl
{"id": "1", "text": "İklim kanunu hakkında konuşmalıyız!", "author": "kullanici1", "created_at": "2024-01-15T10:00:00Z"}
{"id": "2", "text": "Sürdürülebilir enerji şart.", "author": "kullanici2", "created_at": "2024-01-15T11:30:00Z"}
{"id": "3", "text": "Karbon salınımı azaltılmalı.", "author": "kullanici3", "created_at": "2024-01-15T12:45:00Z"}
```

---

## 📅 Tarih Formatları

`created_at` sütunu için desteklenen tarih formatları:

| Format | Örnek |
|--------|-------|
| ISO 8601 | `2024-01-15T14:30:00Z` |
| ISO 8601 (timezone) | `2024-01-15T14:30:00+03:00` |
| Standart tarih-saat | `2024-01-15 14:30:00` |
| Sadece tarih | `2024-01-15` |

> **💡 Öneri**: ISO 8601 formatı (`YYYY-MM-DDTHH:MM:SSZ`) kullanmanız önerilir.

---

## ✅ Dosya Doğrulama Kontrol Listesi

Dosyanızı yüklemeden önce aşağıdaki kontrolleri yapın:

- [ ] Dosya formatı CSV veya JSON mu?
- [ ] Dosya boyutu 200 MB'dan küçük mü?
- [ ] `text` veya `content` sütunu mevcut mu?
- [ ] `author` veya `username` sütunu mevcut mu?
- [ ] `created_at` sütunu mevcut mu?
- [ ] `id` veya `tweet_id` sütunu mevcut mu?
- [ ] Dosya UTF-8 kodlamasında mı?
- [ ] Türkçe karakterler düzgün görünüyor mu?

---

## ⚠️ Sık Yapılan Hatalar

### 1. Yanlış Sütun İsimleri
```csv
# ❌ YANLIŞ
mesaj,yazar,tarih
"Merhaba",kullanici1,2024-01-15

# ✅ DOĞRU
text,author,created_at
"Merhaba",kullanici1,2024-01-15
```

### 2. Eksik Tırnak İşaretleri
```csv
# ❌ YANLIŞ (virgül içeren metin)
1,İklim, çevre ve sürdürülebilirlik,kullanici1

# ✅ DOĞRU
1,"İklim, çevre ve sürdürülebilirlik",kullanici1
```

### 3. Yanlış Karakter Kodlaması
- Excel'den kaydederken **"CSV UTF-8"** formatını seçin
- Notepad++ veya VS Code kullanıyorsanız **"Encoding > UTF-8"** seçin

---

## 🔄 Diğer Kaynaklardan Veri Dönüştürme

### Twitter/X Arşivinden
Twitter arşiv verilerini dönüştürürken:
- `tweet.full_text` → `text`
- `tweet.user.screen_name` → `author`
- `tweet.created_at` → `created_at`
- `tweet.id_str` → `id`

### Mastodon Verisinden
Mastodon API çıktısını dönüştürürken:
- `content` → `text` (HTML etiketleri temizlenmiş)
- `account.username` → `author`
- `created_at` → `created_at`
- `id` → `id`

---

## 📝 Örnek Dosya Şablonları

### Minimal CSV Şablonu
```csv
id,text,author,created_at
```

### Genişletilmiş CSV Şablonu (Ekstra Alanlarla)
```csv
id,text,author,created_at,source,language,retweet_count,like_count
```

---

## 💾 Dosya Kaydetme İpuçları

### Microsoft Excel
1. "Dosya > Farklı Kaydet" seçin
2. Format olarak **"CSV UTF-8 (Virgülle ayrılmış) (*.csv)"** seçin
3. Kaydedin

### Google Sheets
1. "Dosya > İndir" seçin
2. **"Virgülle ayrılmış değerler (.csv)"** seçin

### Python ile Oluşturma
```python
import pandas as pd

df = pd.DataFrame({
    'id': [1, 2, 3],
    'text': ['Metin 1', 'Metin 2', 'Metin 3'],
    'author': ['user1', 'user2', 'user3'],
    'created_at': ['2024-01-15', '2024-01-16', '2024-01-17']
})

df.to_csv('veri.csv', index=False, encoding='utf-8')
```

---

## 📞 Destek

Dosya yükleme ile ilgili sorun yaşarsanız:
1. Yukarıdaki kontrol listesini gözden geçirin
2. Dosyanızı küçük bir örnek ile test edin
3. Hata mesajlarını not alın

---

*Bu belge DataScope v2.0 için hazırlanmıştır.*
