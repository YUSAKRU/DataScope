#!/bin/bash
#
# İKA-VMS v2.0 - Çalıştırma Scripti
#
# Kullanım:
#   ./run.sh --hashtag iklim --limit 50
#   ./run.sh --test-mode --hashtag test
#   ./run.sh --help
#

set -e

# Script dizinini al
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     DataScope v2.0                           ║"
echo "║       Genel Veri Algı Analizi ve Madenciliği Sistemi         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Python kontrolü
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        echo -e "${RED}Hata: Python bulunamadı!${NC}"
        echo "Lütfen Python 3.11+ yükleyin."
        exit 1
    fi
    
    # Versiyon kontrolü
    VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓ Python $VERSION bulundu${NC}"
}

# Sanal ortam kontrolü
check_venv() {
    if [ -d "venv" ]; then
        echo -e "${GREEN}✓ Sanal ortam mevcut${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}Sanal ortam bulunamadı. Oluşturuluyor...${NC}"
        $PYTHON -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        echo -e "${GREEN}✓ Sanal ortam oluşturuldu ve bağımlılıklar yüklendi${NC}"
    fi
}

# Bağımlılık kontrolü
check_dependencies() {
    echo "Bağımlılıklar kontrol ediliyor..."
    
    # requirements.txt kontrolü
    if [ -f "requirements.txt" ]; then
        # Eksik paketleri kontrol et
        MISSING=$($PYTHON -c "
import pkg_resources
import sys
with open('requirements.txt') as f:
    packages = [line.strip().split('>=')[0].split('==')[0] for line in f if line.strip() and not line.startswith('#')]
for pkg in packages:
    try:
        pkg_resources.require(pkg)
    except:
        print(pkg)
" 2>/dev/null || true)
        
        if [ -n "$MISSING" ]; then
            echo -e "${YELLOW}Eksik paketler yükleniyor...${NC}"
            pip install -r requirements.txt
        else
            echo -e "${GREEN}✓ Tüm bağımlılıklar mevcut${NC}"
        fi
    fi
}

# Google Cloud credentials kontrolü
check_credentials() {
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo -e "${YELLOW}⚠ GOOGLE_APPLICATION_CREDENTIALS ayarlanmamış${NC}"
        echo "  Duygu analizi mock modda çalışacak."
        echo "  Gerçek analiz için: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
    else
        if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
            echo -e "${GREEN}✓ Google Cloud credentials bulundu${NC}"
        else
            echo -e "${RED}✗ Credentials dosyası bulunamadı: $GOOGLE_APPLICATION_CREDENTIALS${NC}"
        fi
    fi
}

# Ana işlem
main() {
    echo ""
    
    # Kontroller
    check_python
    check_venv
    check_dependencies
    check_credentials
    
    echo ""
    echo -e "${BLUE}Uygulama başlatılıyor...${NC}"
    echo "─────────────────────────────────────────────────"
    echo ""
    
    # Uygulamayı çalıştır
    $PYTHON main.py "$@"
    
    EXIT_CODE=$?
    
    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ İşlem başarıyla tamamlandı${NC}"
    else
        echo -e "${RED}✗ İşlem hata ile sonlandı (kod: $EXIT_CODE)${NC}"
    fi
    
    exit $EXIT_CODE
}

# Yardım
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Kullanım: ./run.sh [ARGÜMANLAR]"
    echo ""
    echo "Argümanlar:"
    echo "  --hashtag, -t TEXT     Aranacak hashtag (zorunlu)"
    echo "  --instance, -i URL     Mastodon instance URL'i"
    echo "  --limit, -l INT        Maksimum gönderi sayısı"
    echo "  --output-dir, -o PATH  Çıktı dizini"
    echo "  --skip-analysis        Duygu analizini atla"
    echo "  --skip-visualization   Görselleştirmeyi atla"
    echo "  --skip-report          PDF rapor oluşturmayı atla"
    echo "  --test-mode            Test modu (örnek veri kullan)"
    echo "  --verbose, -v          Detaylı çıktı"
    echo "  --help, -h             Bu yardım mesajını göster"
    echo ""
    echo "Örnekler:"
    echo "  ./run.sh --hashtag iklim --limit 50"
    echo "  ./run.sh --hashtag iklim --instance https://mastodon.tr"
    echo "  ./run.sh --test-mode --hashtag test"
    echo ""
    exit 0
fi

# Çalıştır
main "$@"


