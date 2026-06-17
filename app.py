import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import os
import io
import matplotlib.pyplot as plt

# Proje dizinini yola ekle
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import load_config
from src.processor import process_dataframe, normalize_dataframe
from src.analyzer import SentimentAnalyzer, generate_full_report
from src.scraper import MastodonScraper
from src.output import (
    create_all_visualizations,
    create_pdf_report,
    save_analysis_results,
    create_sample_data,
)

# Localization Dictionary
LANGUAGES = {
    "EN": {
        "title": "DataScope v2.0",
        "subtitle": "Social Media Data Mining and Sentiment Analysis Platform",
        "source_label": "Select Data Source:",
        "source_mastodon": "Mastodon Scraper 🌐",
        "source_file": "Upload Local File 📁",
        "source_test": "Test Mode (Sample Data) 🧪",
        "hashtag_label": "Hashtag (without #):",
        "instance_label": "Mastodon Instance URL:",
        "limit_label": "Scrape Limit:",
        "run_button": "Scrape & Analyze 🚀",
        "file_label": "Upload CSV or JSON file:",
        "meta_hashtag": "Analysis Label (for report):",
        "analyze_file_button": "Analyze File 🚀",
        "sample_limit": "Number of Sample Posts:",
        "run_test_button": "Run with Sample Data 🚀",
        "connecting": "Connecting to {} and fetching #{}...",
        "no_posts": "No posts found. Please check the hashtag or instance URL.",
        "loaded_success": "✓ {} posts successfully loaded.",
        "cleaning": "Cleaning and normalizing text data...",
        "analyzing": "Performing sentiment analysis (Google Cloud NLP)...",
        "stats_calculated": "✓ Statistics calculated.",
        "success_msg": "✓ Process completed successfully. Outputs saved.",
        "error_msg": "An error occurred: {}",
        "tab_overview": "📈 Overview",
        "tab_charts": "📊 Charts & Analysis",
        "tab_data": "📋 Raw Data Table",
        "tab_report": "📄 Report & Export",
        "metric_total": "Total Posts",
        "metric_pos": "Positive Ratio",
        "metric_neg": "Negative Ratio",
        "metric_neu": "Neutral Ratio",
        "pie_caption": "Sentiment Distribution (Pie Chart)",
        "wordcloud_caption": "Frequently Occurring Words (Word Cloud)",
        "timeseries_caption": "Sentiment Trend Over Time",
        "author_caption": "Sentiment Distribution by Author",
        "engagement_caption": "Engagement Distribution",
        "no_time_series": "Time series chart requires a valid 'created_at' date column in data.",
        "pdf_header": "Generate PDF Analysis Report",
        "pdf_desc": "You can generate a formal PDF report containing all statistics, charts, and findings.",
        "pdf_button": "Compile Analysis Report to PDF 📄",
        "pdf_success": "✓ PDF Report successfully generated!",
        "pdf_download": "Download Report 📥",
        "csv_header": "Export Raw Data",
        "csv_download": "Download Analyzed Data as CSV 📥",
        "info_sidebar": "Please select a data source from the left sidebar and click 'Run'.",
        "sidebar_title": "🛠️ Control Panel",
        "lang_label": "Language / Dil"
    },
    "TR": {
        "title": "DataScope v2.0",
        "subtitle": "Sosyal Medya Veri Madenciliği ve Duygu Analizi Platformu",
        "source_label": "Veri Kaynağı Seçin:",
        "source_mastodon": "Mastodon Scraper 🌐",
        "source_file": "Yerel Dosya Yükle 📁",
        "source_test": "Test Modu (Örnek Veri) 🧪",
        "hashtag_label": "Hashtag (örn. iklim):",
        "instance_label": "Mastodon Sunucu URL'i:",
        "limit_label": "Çekilecek Gönderi Sınırı:",
        "run_button": "Verileri Çek ve Analiz Et 🚀",
        "file_label": "CSV veya JSON dosyası yükleyin:",
        "meta_hashtag": "Analiz Etiketi (Raporlama için):",
        "analyze_file_button": "Dosyayı Analiz Et 🚀",
        "sample_limit": "Üretilecek Örnek Gönderi Sayısı:",
        "run_test_button": "Örnek Verilerle Çalıştır 🚀",
        "connecting": "{} sunucusuna bağlanılıyor ve #{} çekiliyor...",
        "no_posts": "Hiçbir gönderi bulunamadı. Lütfen hashtag'i veya sunucuyu kontrol edin.",
        "loaded_success": "✓ {} adet gönderi başarıyla yüklendi.",
        "cleaning": "Metin verileri temizleniyor ve normalleştiriliyor...",
        "analyzing": "Duygu analizi yapılıyor (Google Cloud NLP)...",
        "stats_calculated": "✓ İstatistikler hesaplandı.",
        "success_msg": "✓ İşlem başarıyla tamamlandı. Çıktılar kaydedildi.",
        "error_msg": "Bir hata oluştu: {}",
        "tab_overview": "📈 Genel Görünüm",
        "tab_charts": "📊 Grafikler & Analiz",
        "tab_data": "📋 Ham Veri Tablosu",
        "tab_report": "📄 Rapor & İhracat",
        "metric_total": "Toplam Gönderi",
        "metric_pos": "Pozitif Oranı",
        "metric_neg": "Negatif Oranı",
        "metric_neu": "Nötr Oranı",
        "pie_caption": "Duygu Dağılımı (Pie Chart)",
        "wordcloud_caption": "Sık Geçen Kelimeler (Kelime Bulutu)",
        "timeseries_caption": "Zamana Bağlı Duygu Durumu Değişimi",
        "author_caption": "Yazarlara Göre Duygu Dağılımı",
        "engagement_caption": "Etkileşim Dağılımları",
        "no_time_series": "Zaman serisi grafiği oluşturulabilmesi için veride geçerli bir tarih ('created_at') bulunmalıdır.",
        "pdf_header": "PDF Analiz Raporu Oluştur",
        "pdf_desc": "Tüm istatistikleri, grafikleri ve bulguları içeren resmi bir PDF rapor dosyası oluşturabilirsiniz.",
        "pdf_button": "Analiz Raporunu PDF Olarak Derle 📄",
        "pdf_success": "✓ PDF Raporu başarıyla oluşturuldu!",
        "pdf_download": "Raporu Bilgisayarına İndir 📥",
        "csv_header": "Ham Verileri Dışa Aktar",
        "csv_download": "Analiz Edilmiş Verileri CSV Olarak İndir 📥",
        "info_sidebar": "Lütfen soldaki kontrol panelinden bir veri kaynağı seçip 'Çalıştır' butonuna basın.",
        "sidebar_title": "🛠️ Control Panel",
        "lang_label": "Dil / Language"
    }
}

# Sayfa Yapılandırması
st.set_page_config(
    page_title="DataScope AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar - Dil Seçimi (En üstte)
st.sidebar.title("🌐 Settings / Ayarlar")
lang_code = st.sidebar.selectbox("Language / Dil:", ("English", "Türkçe"))
lang = "EN" if lang_code == "English" else "TR"
t = LANGUAGES[lang]

# Stil düzenlemeleri
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1e3d59;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .subheader {
            font-size: 1.2rem;
            color: #17b978;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Başlık
st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subheader">{t["subtitle"]}</div>', unsafe_allow_html=True)

# Config yükle
config = load_config()

# Sidebar - Veri Kaynağı Seçimi
st.sidebar.markdown("---")
st.sidebar.title(t["sidebar_title"])
source_option = st.sidebar.radio(
    t["source_label"],
    (t["source_mastodon"], t["source_file"], t["source_test"])
)

# Değişkenlerin ilklendirilmesi
df = None
stats = None
graphs = {}
hashtag = "analysis"

if source_option == t["source_mastodon"]:
    hashtag = st.sidebar.text_input(t["hashtag_label"], value="climate").strip()
    instance = st.sidebar.text_input(t["instance_label"], value="https://mastodon.social").strip()
    limit = st.sidebar.slider(t["limit_label"], min_value=10, max_value=200, value=50, step=10)
    
    run_analysis = st.sidebar.button(t["run_button"], use_container_width=True)
    
elif source_option == t["source_file"]:
    uploaded_file = st.sidebar.file_uploader(t["file_label"], type=["csv", "json"])
    hashtag = st.sidebar.text_input(t["meta_hashtag"], value="local-file").strip()
    
    run_analysis = st.sidebar.button(t["analyze_file_button"], use_container_width=True) if uploaded_file else False
    
else:  # Test Modu
    hashtag = st.sidebar.text_input(t["hashtag_label"], value="test").strip()
    limit = st.sidebar.slider(t["sample_limit"], min_value=10, max_value=200, value=50, step=10)
    
    run_analysis = st.sidebar.button(t["run_test_button"], use_container_width=True)

# Analiz Süreci
if run_analysis:
    with st.spinner(t["cleaning"] if "df" in locals() and df is not None else "..."):
        try:
            # Step 1: Data Acquisition
            if source_option == t["source_mastodon"]:
                st.info(t["connecting"].format(instance, hashtag))
                scraper = MastodonScraper(instance_url=instance)
                posts = scraper.fetch_by_hashtag(hashtag=hashtag, limit=limit)
                
                if not posts:
                    st.error(t["no_posts"])
                else:
                    df = pd.DataFrame(posts)
                    source_name = instance
            
            elif source_option == t["source_file"]:
                file_path = Path(uploaded_file.name)
                if file_path.suffix.lower() == '.csv':
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_json(uploaded_file)
                
                # Normalize columns
                column_mapping = {
                    'username': 'author', 'user': 'author', 'content': 'text', 
                    'text': 'text', 'tweet_id': 'id', 'created_at': 'created_at'
                }
                df = df.rename(columns=column_mapping)
                if 'text' not in df.columns:
                    st.error("Error: CSV/JSON must contain a 'text' or 'content' column.")
                    df = None
                source_name = "Local File"
                
            else:  # Test Modu
                df = create_sample_data(num_posts=limit)
                source_name = "Local Test Mode"
            
            if df is not None:
                st.success(t["loaded_success"].format(len(df)))
                
                # Step 2: Cleaning
                df = process_dataframe(df)
                df = normalize_dataframe(df)
                
                # Step 3: Sentiment Analysis
                analyzer = SentimentAnalyzer()
                df = analyzer.analyze_dataframe(df)
                
                # Step 4: Statistics
                stats = generate_full_report(df)
                
                # State'e kaydet
                st.session_state['df'] = df
                st.session_state['stats'] = stats
                st.session_state['hashtag'] = hashtag
                st.session_state['source_name'] = source_name
                
        except Exception as e:
            st.error(t["error_msg"].format(str(e)))

# Sonuç Ekranı
if 'df' in st.session_state:
    df = st.session_state['df']
    stats = st.session_state['stats']
    hashtag = st.session_state['hashtag']
    source_name = st.session_state['source_name']
    
    # Görselleştirmeleri geçici klasörde oluştur
    tmp_out = Path("./outputs_streamlit")
    tmp_out.mkdir(parents=True, exist_ok=True)
    graphs = create_all_visualizations(df, str(tmp_out))
    
    # Sekmeler
    tab_overview, tab_charts, tab_data, tab_report = st.tabs([
        t["tab_overview"], 
        t["tab_charts"], 
        t["tab_data"], 
        t["tab_report"]
    ])
    
    with tab_overview:
        # Metrik Kartları
        m1, m2, m3, m4 = st.columns(4)
        
        # Duygu Oranları
        total_posts = stats['basic_stats']['total_posts']
        sent_stats = stats.get('sentiment_stats', {})
        pos_count = sent_stats.get('positive_count', 0)
        neg_count = sent_stats.get('negative_count', 0)
        neu_count = sent_stats.get('neutral_count', 0)
        
        m1.metric(t["metric_total"], total_posts)
        m2.metric(t["metric_pos"], f"%{pos_count/total_posts*100:.1f}" if total_posts else "%0")
        m3.metric(t["metric_neg"], f"%{neg_count/total_posts*100:.1f}" if total_posts else "%0")
        m4.metric(t["metric_neu"], f"%{neu_count/total_posts*100:.1f}" if total_posts else "%0")
        
        # Yan yana iki ana görselleştirme
        col1, col2 = st.columns(2)
        
        with col1:
            if 'sentiment_distribution' in graphs:
                st.image(graphs['sentiment_distribution'], caption=t["pie_caption"], use_container_width=True)
        
        with col2:
            if 'wordcloud' in graphs:
                st.image(graphs['wordcloud'], caption=t["wordcloud_caption"], use_container_width=True)

    with tab_charts:
        # Zaman Serisi ve Etkileşim
        col1, col2 = st.columns(2)
        
        with col1:
            if 'time_series' in graphs:
                st.image(graphs['time_series'], caption=t["timeseries_caption"], use_container_width=True)
            else:
                st.info(t["no_time_series"])
                
        with col2:
            if 'sentiment_by_author' in graphs:
                st.image(graphs['sentiment_by_author'], caption=t["author_caption"], use_container_width=True)
            elif 'engagement_distribution' in graphs:
                st.image(graphs['engagement_distribution'], caption=t["engagement_caption"], use_container_width=True)
                
    with tab_data:
        st.dataframe(df, use_container_width=True)
        
    with tab_report:
        st.subheader(t["pdf_header"])
        st.write(t["pdf_desc"])
        
        pdf_path = tmp_out / f"{hashtag}_analiz_raporu.pdf"
        
        if st.button(t["pdf_button"], use_container_width=True):
            try:
                create_pdf_report(
                    df=df,
                    stats=stats,
                    graphs=graphs,
                    output_path=str(pdf_path),
                    hashtag=hashtag,
                    instance=source_name
                )
                st.success(t["pdf_success"])
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label=t["pdf_download"],
                        data=f,
                        file_name=f"{hashtag}_analysis_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error compiling report: {e}")
                
        st.markdown("---")
        st.subheader(t["csv_header"])
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label=t["csv_download"],
            data=csv_buffer.getvalue(),
            file_name=f"{hashtag}_analyzed_data.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info(t["info_sidebar"])
