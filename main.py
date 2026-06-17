#!/usr/bin/env python3
"""
DataScope v2.0 - Sosyal Medya Veri Madenciliği ve Duygu Analizi Platformu

Bu komut dosyası, DataScope sisteminin ana giriş noktasıdır. Mastodon'dan
veri çeker, temizler, analiz eder ve görsel raporlar oluşturur.
"""

import sys
import os
from pathlib import Path
import click
import pandas as pd

# Proje kök dizinini import yoluna ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.utils.config import load_config
from src.scraper import MastodonScraper
from src.processor import process_dataframe, normalize_dataframe
from src.analyzer import SentimentAnalyzer, generate_full_report
from src.output import (
    create_all_visualizations,
    create_pdf_report,
    save_analysis_results,
    create_sample_data,
)

# CLI Yapılandırması
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--hashtag', '-t', required=True, help='Aranacak hashtag (# işareti olmadan)')
@click.option('--instance', '-i', default='https://mastodon.social', help='Mastodon sunucu adresi (Varsayılan: https://mastodon.social)')
@click.option('--limit', '-l', default=100, type=int, help='Çekilecek maksimum gönderi sayısı (Varsayılan: 100)')
@click.option('--output-dir', '-o', default='./outputs', type=click.Path(), help='Çıktıların kaydedileceği dizin (Varsayılan: ./outputs)')
@click.option('--skip-analysis', is_flag=True, help='Duygu analizini (Google NLP API) atla')
@click.option('--skip-visualization', is_flag=True, help='Grafik/görselleştirmeleri atla')
@click.option('--skip-report', is_flag=True, help='PDF rapor üretimini atla')
@click.option('--test-mode', is_flag=True, help='Mastodon yerine yerel örnek/test verileri kullan')
@click.option('--verbose', '-v', is_flag=True, help='Hata ayıklama loglarını aktif et')
def main(hashtag, instance, limit, output_dir, skip_analysis, skip_visualization, skip_report, test_mode, verbose):
    """
    DataScope v2.0 - Sosyal Medya Veri Madenciliği ve Duygu Analizi Platformu.
    
    Belirtilen hashtag ile veri toplar, temizler, duygu analizi yapar ve raporlar.
    """
    # Log seviyesini ayarla
    log_level = 'DEBUG' if verbose else 'INFO'
    logger = setup_logger('datascope', level=log_level)
    
    logger.info("DataScope v2.0 başlatılıyor...")
    
    try:
        # Config yükle
        config = load_config()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. VERİ ELDE ETME
        logger.info("=" * 60)
        logger.info("ADIM 1: Veri Toplama/Elde Etme")
        
        if test_mode:
            logger.info("✓ Test modu aktif. Örnek test verileri üretiliyor...")
            df = create_sample_data(num_posts=limit)
            logger.info(f"✓ {len(df)} adet örnek gönderi oluşturuldu.")
            source_info = "Yerel Test Modu"
        else:
            logger.info(f"✓ Mastodon Scraper başlatılıyor: {instance}")
            scraper = MastodonScraper(instance_url=instance)
            posts = scraper.fetch_by_hashtag(hashtag=hashtag, limit=limit)
            
            if not posts:
                logger.warning(f"⚠ Hashtag '#{hashtag}' için hiçbir gönderi bulunamadı.")
                sys.exit(0)
                
            df = pd.DataFrame(posts)
            logger.info(f"✓ {len(df)} gönderi başarıyla çekildi.")
            source_info = instance

        # 2. VERİ İŞLEME VE TEMİZLEME
        logger.info("=" * 60)
        logger.info("ADIM 2: Veri İşleme ve Temizleme")
        
        df = process_dataframe(df)
        df = normalize_dataframe(df)
        logger.info("✓ Metin verileri temizlendi ve normalleştirildi.")

        # 3. DUYGU ANALİZİ (SENTIMENT ANALYSIS)
        if not skip_analysis:
            logger.info("=" * 60)
            logger.info("ADIM 3: Duygu Analizi (Google Cloud NLP)")
            
            analyzer = SentimentAnalyzer()
            df = analyzer.analyze_dataframe(df)
            logger.info("✓ Duygu analizi başarıyla tamamlandı.")
        else:
            logger.info("✓ Duygu analizi atlandı.")

        # 4. İSTATİSTİKLERİN HESAPLANMASI
        logger.info("=" * 60)
        logger.info("ADIM 4: İstatistik Hesaplama")
        
        stats = generate_full_report(df)
        logger.info("✓ Tüm analiz metrikleri ve istatistikler hesaplandı.")

        # Özet konsol çıktısı
        print("\n" + "📊 ANALİZ ÖZETİ " + "=" * 40)
        print(f"  Toplam Gönderi : {len(df)}")
        if 'sentiment_label' in df.columns:
            sent_counts = df['sentiment_label'].value_counts()
            print("\n  Duygu Dağılımı:")
            for sent, count in sent_counts.items():
                print(f"    - {sent.capitalize()}: {count} (%{count/len(df)*100:.1f})")
        print("=" * 57 + "\n")

        # 5. GÖRSELLEŞTİRMELER
        graphs = {}
        if not skip_visualization:
            logger.info("=" * 60)
            logger.info("ADIM 5: Görselleştirmelerin Üretilmesi")
            
            graphs = create_all_visualizations(df, str(output_path))
            logger.info(f"✓ {len(graphs)} adet görselleştirme grafiği kaydedildi.")
        else:
            logger.info("✓ Görselleştirme atlandı.")

        # 6. PDF RAPOR OLUŞTURMA
        if not skip_report and not skip_visualization:
            logger.info("=" * 60)
            logger.info("ADIM 6: PDF Raporunun Hazırlanması")
            
            report_file_path = output_path / f"{hashtag}_analiz_raporu.pdf"
            create_pdf_report(
                df=df,
                stats=stats,
                graphs=graphs,
                output_path=str(report_file_path),
                hashtag=hashtag,
                instance=source_info
            )
            logger.info(f"✓ PDF Raporu oluşturuldu: {report_file_path}")
        elif skip_report:
            logger.info("✓ PDF Raporu atlandı.")
        else:
            logger.warning("⚠ PDF raporu grafiklere ihtiyaç duyduğu için görselleştirme atlandığında rapor da oluşturulamaz.")

        # 7. SONUÇLARIN DİSKE YAZILMASI
        logger.info("=" * 60)
        logger.info("ADIM 7: Sonuçların Kaydedilmesi")
        
        save_analysis_results(
            df=df,
            stats=stats,
            output_dir=str(output_path),
            prefix=hashtag
        )
        
        logger.info(f"🎉 Tüm işlemler tamamlandı! Çıktılar: '{output_path}' dizininde.")

    except Exception as e:
        logger.exception(f"❌ Kritik hata: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
