#!/usr/bin/env python3
"""
DataScope v2.0 - Yerel Dosya Analiz Aracı

Bu komut dosyası, yerel bir CSV veya JSON dosyasını okuyarak 
DataScope analiz boru hattından geçirir.

Kullanım:
    python analyze_local_file.py input.csv --hashtag analiz
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
from src.processor import process_dataframe, normalize_dataframe
from src.analyzer import SentimentAnalyzer, generate_full_report
from src.output import (
    create_all_visualizations,
    create_pdf_report,
    save_analysis_results,
)

# CLI yapılandırması
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def validate_and_normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Veri setindeki sütunları doğrular ve standart isimlere dönüştürür.
    Username -> author, content -> cleaned_text (işleme öncesi)
    """
    # Standartlaştırma haritası (Mevcut -> Hedef)
    column_mapping = {
        'username': 'author',
        'user': 'author',
        'content': 'text', # process_dataframe expects 'text' column
        'text': 'text',
        'tweet_id': 'id',
        'created_at': 'created_at'
    }
    
    # Sütun isimlerini değiştir
    df = df.rename(columns=column_mapping)
    
    # Gerekli sütun kontrolü
    required = ['text'] 
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        raise ValueError(f"Eksik sütunlar: {', '.join(missing)}. Dosyanızda 'content', 'text' veya 'body' sütunlarından biri olmalı.")
        
    return df

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--hashtag', '-t', default='analysis', help='Analiz etiketi (Raporlarda görünür)')
@click.option('--output-dir', '-o', default='./outputs', type=click.Path(), help='Çıktı dizini')
@click.option('--skip-analysis', is_flag=True, help='Duygu analizini atla')
@click.option('--skip-visualization', is_flag=True, help='Görselleştirmeyi atla')
@click.option('--verbose', '-v', is_flag=True, help='Detaylı çıktı')
def main(input_file, hashtag, output_dir, skip_analysis, skip_visualization, verbose):
    """
    Yerel bir veri dosyasını analiz et.
    
    INPUT_FILE: Analiz edilecek CSV veya JSON dosyası.
    """
    # Loglama kurulumu
    log_level = 'DEBUG' if verbose else 'INFO'
    logger = setup_logger('ika-vms-local', level=log_level)
    
    logger.info(f"Dosya analizi başlatılıyor: {input_file}")
    
    try:
        # Load configuration
        config = load_config()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Veri Yükleme
        logger.info("=" * 50)
        logger.info("ADIM 1: Veri Yükleme")
        
        file_path = Path(input_file)
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() == '.json':
            df = pd.read_json(file_path)
        else:
            raise ValueError("Desteklenmeyen dosya formatı. Sadece CSV ve JSON desteklenir.")
            
        logger.info(f"✓ Dosya okundu: {len(df)} satır")
        
        # Sütun normalizasyonu
        df = validate_and_normalize_columns(df)
        logger.info("✓ Sütunlar doğrulandı ve normalleştirildi")
        
        # 2. Veri İşleme
        logger.info("=" * 50)
        logger.info("ADIM 2: Veri İşleme")
        
        # process_dataframe fonksiyonu 'content' sütununu alıp temizleyip 'cleaned_text' oluşturuyor olmalı
        # app.py'ye baktığımızda process_dataframe çağrılıyor.
        
        df = process_dataframe(df)
        df = normalize_dataframe(df)
        
        logger.info(f"✓ Veri işlendi. Son boyut: {len(df)} satır")
        
        # 3. Duygu Analizi
        if not skip_analysis:
            logger.info("=" * 50)
            logger.info("ADIM 3: Duygu Analizi")
            
            analyzer = SentimentAnalyzer()
            df = analyzer.analyze_dataframe(df)
            logger.info("✓ Duygu analizi tamamlandı")
        
        # 4. İstatistikler
        logger.info("=" * 50)
        logger.info("ADIM 4: İstatistik Hesaplama")
        
        stats = generate_full_report(df)
        logger.info("✓ İstatistikler hesaplandı")
        
        # Özet Yazdır
        print("\n" + "=" * 30)
        print("📊 ANALİZ ÖZETİ")
        print(f"Toplam Veri: {len(df)}")
        if 'sentiment' in df.columns:
            sent_counts = df['sentiment'].value_counts()
            print("\nDuygu Dağılımı:")
            for sent, count in sent_counts.items():
                print(f"  {sent}: {count} (%{count/len(df)*100:.1f})")
        print("=" * 30 + "\n")
        
        # 5. Görselleştirme
        graphs = {}
        if not skip_visualization:
            logger.info("=" * 50)
            logger.info("ADIM 5: Görselleştirme")
            
            graphs = create_all_visualizations(df, str(output_path))
            logger.info(f"✓ {len(graphs)} görselleştirme oluşturuldu")
            
        # 6. Raporlama
        if not skip_visualization: # PDF raporu görsellere ihtiyaç duyar
            logger.info("=" * 50)
            logger.info("ADIM 6: PDF Rapor")
            
            report_path = output_path / f'{hashtag}_rapor.pdf'
            create_pdf_report(
                df=df,
                stats=stats,
                graphs=graphs,
                output_path=str(report_path),
                hashtag=hashtag,
                instance="Yerel Dosya"
            )
            logger.info(f"✓ PDF rapor oluşturuldu: {report_path}")
            
        # 7. Kaydetme
        logger.info("=" * 50)
        logger.info("ADIM 7: Sonuçları Kaydetme")
        
        save_analysis_results(
            df=df,
            stats=stats,
            output_dir=str(output_path),
            prefix=hashtag
        )
        
        logger.info(f"✅ İşlem başarıyla tamamlandı. Çıktılar: {output_path}")

    except Exception as e:
        logger.exception(f"Hata oluştu: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
