# 📊 DataScope v2.0 - Social Media Data Mining & Sentiment Analysis Platform

<div align="center">

![Version](https://img.shields.io/badge/Version-2.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Google Cloud NLP](https://img.shields.io/badge/Google_Cloud-NLP_API-green?style=flat-square&logo=google-cloud)
![Mastodon](https://img.shields.io/badge/Mastodon-API-purple?style=flat-square&logo=mastodon)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-GPLv3-red?style=flat-square)

**A modular data mining pipeline and interactive web dashboard that scrapes social media data from Mastodon, cleanses and normalizes text, performs sentiment analysis using Google Cloud NLP, and generates visual reports.**

[System Design Doc](docs/sistem_analizi_ve_tasarimi_v2.md) • [Data Format Guide](docs/VERI_FORMATI_KILAVUZU.md) • [Dependencies](requirements.txt)

*(Türkçe açıklama için aşağı kaydırın / Scroll down for Turkish)*

</div>

---

## 🌟 Key Features

- 🌐 **Mastodon Integration:** Fetches decentralized social media posts based on specified hashtags.
- 🧹 **Advanced Text Cleaning:** Strips HTML, URLs, mentions (@user), and redundant spaces to prepare text for analysis.
- 🧠 **Google NLP Sentiment Analysis:** Uses Google Cloud Natural Language API to assign sentiment scores (-1.0 to 1.0) and magnitudes; categorizes posts as positive, negative, or neutral.
- 🖥️ **Interactive Streamlit Web Dashboard:** A user-friendly bilingual interface to pull live data, upload local CSV/JSON files, inspect graphs, and download compiled PDF reports.
- 📈 **Rich Visualizations:**
  - **Sentiment Distribution (Pie Chart):** Percentage breakdowns of positive, negative, and neutral posts.
  - **Word Cloud:** Highlights frequently occurring words with Turkish stopword filtering.
  - **Time Series Trend:** Plots sentiment score variations over time.
- 📄 **PDF Reporting:** Automatic PDF reports compiled using ReportLab with full Turkish character support (DejaVu Sans font).
- 🐳 **Docker Support:** Containerized with Docker and Docker Compose for instant running with zero local installation.

---

## 🏗️ Project Architecture

```
DataScope/
├── src/
│   ├── scraper/         # Mastodon API scraping integration
│   ├── processor/       # Text cleaning and normalization
│   ├── analyzer/        # Sentiment analysis and statistics
│   ├── output/          # Matplotlib visualization and PDF report generation
│   └── utils/           # Configuration, logging, and custom exceptions
├── docs/                # System design and data guide documentation
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configurations
├── docker-compose.yml   # Docker Compose orchestration
├── run.sh               # Easy startup script (CLI)
├── app.py               # Streamlit Web Dashboard UI
└── main.py              # CLI Application Entry Point
```

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.11+
- Google Cloud Service Account Key (`key.json` file)

---

### Option A: Running the Streamlit Web Dashboard (Recommended 🖥️)

To launch the interactive web dashboard with bilingual support:

1. **Activate the virtual environment and run Streamlit:**
   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```
2. **Access via browser:**
   Open `http://localhost:8501` in your web browser.

---

### Option B: Running with Docker Compose 🐳

Run the containerized app with a single command:

1. **Place your Google Cloud credentials:**
   Save your key file under `credentials/key.json`.
   
2. **Launch with Docker Compose:**
   ```bash
   docker compose run --rm datascope --hashtag climate --limit 50
   ```

---

### Option C: Running the Local CLI

The `run.sh` script automatically verifies your Python version, installs missing dependencies, and sets up the virtual environment (`venv`):

1. **Set your environment credentials path:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-key.json"
   ```

2. **Execute the script:**
   ```bash
   ./run.sh --hashtag climate --limit 50
   ```

---

## ⚙️ CLI Arguments

```bash
python main.py [OPTIONS]
```

### Parameters:
- `--hashtag TEXT` : Hashtag to search for (Required)
- `--instance URL` : Mastodon instance address (Default: `https://mastodon.social`)
- `--limit INT` : Maximum number of posts to fetch (Default: `100`)
- `--output-dir PATH` : Output directory path (Default: `./outputs`)
- `--skip-analysis` : Skip Google NLP sentiment analysis
- `--skip-visualization` : Skip visualization generation
- `--skip-report` : Skip PDF report compilation
- `--test-mode` : Run with local mock/sample data without calling external APIs
- `--verbose` : Enable debug logging

### CLI Examples:

```bash
# Run a trial analysis using mock/test data
python main.py --test-mode --hashtag test

# Fetch and analyze posts from a Turkish Mastodon server
python main.py --hashtag İklimKanunu --instance https://mastodon.tr --limit 200

# Scrape only (without NLP analysis or reports)
python main.py --hashtag python --skip-analysis --skip-visualization --skip-report
```

---

## 📊 Outputs

All generated files are saved under the output directory (default: `outputs/`):
- 📁 `outputs/veri.csv` : Cleaned text data with sentiment score labels.
- 📈 `outputs/sentiment_distribution.png` : Pie chart of sentiment distributions.
- ☁️ `outputs/wordcloud.png` : Visual cloud of key terms.
- 📅 `outputs/time_series.png` : Sentiment trend graph over time.
- 📄 `outputs/rapor.pdf` : Formal PDF analysis report.
- 📝 `logs/ika-vms.log` : Application logs.

---
---

# 📊 DataScope v2.0 - Sosyal Medya Veri Madenciliği ve Duygu Analizi Platformu

**Mastodon (Fediverse) üzerinden sosyal medya verilerini çeken, temizleyen, duygu analizine tabi tutan ve görsel raporlar üreten modüler bir veri madenciliği boru hattı ve etkileşimli web paneli.**

## 🌟 Öne Çıkan Özellikler

- 🌐 **Mastodon Entegrasyonu:** Belirlenen hashtag'ler üzerinden merkeziyetsiz sosyal medya verisi çeker.
- 🧹 **Gelişmiş Veri Temizleme:** HTML etiketleri, URL'ler, mention'lar (@kullanıcı) ve gereksiz boşlukları ayıklayarak metni analize hazırlar.
- 🧠 **Google NLP ile Duygu Analizi:** Google Cloud Natural Language API entegrasyonu ile metinlere duygu skoru (-1.0 ile 1.0) ve yoğunluk (magnitude) atar; pozitif, negatif veya nötr olarak etiketler.
- 🖥️ **Streamlit Web Arayüzü (Dashboard):** Verileri canlı çekebileceğiniz, yerel CSV/JSON yükleyip analiz edebileceğiniz, grafiklerinizi interaktif görüntüleyip çift dilli (İngilizce/Türkçe) arayüzden PDF raporu tek tıkla indirebileceğiniz modern web paneli.
- 📈 **Zengin Görselleştirmeler:**
  - **Duygu Dağılımı (Pie Chart):** Pozitif, negatif ve nötr duygu oranlarını gösterir.
  - **Kelime Bulutu (Word Cloud):** Türkçe stopword filtrelemeli en sık geçen kelimeleri haritalandırır.
  - **Zaman Serisi Analizi:** Duygu durumunun zaman içindeki değişimini grafikleştirir.
- 📄 **PDF Raporlama:** ReportLab altyapısı ve Türkçe karakter (DejaVu Sans) desteği ile tüm istatistik ve grafikleri içeren otomatik analiz raporları üretir.
- 🐳 **Docker Hazır:** Docker ve Docker Compose entegrasyonu ile yerel kurulum gerektirmeden tek komutla çalıştırılabilir.

---

## 🚀 Kurulum ve Çalıştırma

### Yöntem A: Streamlit Web Dashboard ile Çalıştırma (Önerilen 🖥️)

1. **Sanal ortamı aktif edin ve Streamlit uygulamasını çalıştırın:**
   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```
2. **Tarayıcınızda açın:** `http://localhost:8501`

---

### Yöntem B: Docker ile Çalıştırma 🐳

1. **Google Cloud Credentials Dosyanızı yerleştirin:** `credentials/key.json`
2. **Docker Compose ile çalıştırın:**
   ```bash
   docker compose run --rm datascope --hashtag iklim --limit 50
   ```

---

### Yöntem C: Yerel Python ile CLI Üzerinden Çalıştırma

1. **Ortam değişkenini tanımlayın:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-key.json"
   ```
2. **Scripti çalıştırın:**
   ```bash
   ./run.sh --hashtag iklim --limit 50
   ```

---

## 📄 Lisans

Bu proje **GNU General Public License v3.0** (GPLv3) altında lisanslanmıştır. Detaylar için sistem dökümanlarına göz atabilirsiniz.
