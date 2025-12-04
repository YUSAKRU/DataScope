"""
Custom exception classes for DataScope.

This module defines all custom exceptions used throughout the application.
Each exception includes a descriptive message with solution suggestions.
"""


class IKAVMSError(Exception):
    """Base exception class for all DataScope errors."""
    
    def __init__(self, message: str = "An error occurred in DataScope"):
        self.message = message
        super().__init__(self.message)


# ============================================================================
# Scraper Exceptions
# ============================================================================

class ScraperError(IKAVMSError):
    """Base exception for scraper-related errors."""
    pass


class HashtagNotFoundError(ScraperError):
    """Raised when the specified hashtag is not found on the instance."""
    
    def __init__(self, hashtag: str, instance: str):
        self.hashtag = hashtag
        self.instance = instance
        self.message = (
            f"'{hashtag}' hashtag'i '{instance}' instance'ında bulunamadı.\n"
            f"Çözüm önerileri:\n"
            f"  1. Hashtag'in doğru yazıldığından emin olun\n"
            f"  2. Farklı bir instance deneyin (örn: mastodon.social)\n"
            f"  3. Hashtag'in o instance'da kullanıldığından emin olun"
        )
        super().__init__(self.message)


class RateLimitError(ScraperError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        self.message = (
            f"Mastodon API rate limit'i aşıldı.\n"
            f"Çözüm: {retry_after} saniye bekleyip tekrar deneyin."
        )
        super().__init__(self.message)


class InvalidInstanceError(ScraperError):
    """Raised when the Mastodon instance URL is invalid."""
    
    def __init__(self, instance: str):
        self.instance = instance
        self.message = (
            f"Geçersiz Mastodon instance URL'i: '{instance}'\n"
            f"Çözüm önerileri:\n"
            f"  1. URL'in 'https://' ile başladığından emin olun\n"
            f"  2. Instance'ın erişilebilir olduğunu kontrol edin\n"
            f"  3. Örnek: https://mastodon.social"
        )
        super().__init__(self.message)


class ConnectionError(ScraperError):
    """Raised when connection to the instance fails."""
    
    def __init__(self, instance: str, original_error: str = ""):
        self.instance = instance
        self.original_error = original_error
        self.message = (
            f"'{instance}' adresine bağlanılamadı.\n"
            f"Hata: {original_error}\n"
            f"Çözüm önerileri:\n"
            f"  1. İnternet bağlantınızı kontrol edin\n"
            f"  2. Instance'ın çalışır durumda olduğunu doğrulayın\n"
            f"  3. Firewall ayarlarını kontrol edin"
        )
        super().__init__(self.message)


# ============================================================================
# Analysis Exceptions
# ============================================================================

class AnalysisError(IKAVMSError):
    """Base exception for analysis-related errors."""
    pass


class CredentialsError(AnalysisError):
    """Raised when Google Cloud API credentials are missing or invalid."""
    
    def __init__(self, details: str = ""):
        self.details = details
        self.message = (
            "Google Cloud API anahtarı bulunamadı veya geçersiz.\n"
            f"{details}\n" if details else ""
            "Çözüm:\n"
            "  1. Service account key dosyasını indirin\n"
            "  2. GOOGLE_APPLICATION_CREDENTIALS ortam değişkenini ayarlayın:\n"
            "     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
        )
        super().__init__(self.message)


class QuotaExceededError(AnalysisError):
    """Raised when Google Cloud API quota is exceeded."""
    
    def __init__(self):
        self.message = (
            "Google Cloud API kotası aşıldı.\n"
            "Çözüm:\n"
            "  1. Google Cloud Console'dan kotanızı kontrol edin\n"
            "  2. Aylık ücretsiz kotayı bekleyin veya ödeme yapın"
        )
        super().__init__(self.message)


class TextTooLongError(AnalysisError):
    """Raised when text exceeds the maximum allowed length for analysis."""
    
    def __init__(self, text_length: int, max_length: int = 5000):
        self.text_length = text_length
        self.max_length = max_length
        self.message = (
            f"Metin çok uzun: {text_length} karakter (maksimum: {max_length}).\n"
            "Çözüm: Metni kısaltın veya bölün."
        )
        super().__init__(self.message)


class EmptyTextError(AnalysisError):
    """Raised when text is empty or contains only whitespace."""
    
    def __init__(self):
        self.message = (
            "Metin boş veya sadece boşluk karakteri içeriyor.\n"
            "Analiz yapılabilmesi için geçerli metin gereklidir."
        )
        super().__init__(self.message)


# ============================================================================
# Data Processing Exceptions
# ============================================================================

class ProcessingError(IKAVMSError):
    """Base exception for data processing errors."""
    pass


class MissingColumnError(ProcessingError):
    """Raised when a required DataFrame column is missing."""
    
    def __init__(self, column_name: str, required_columns: list):
        self.column_name = column_name
        self.required_columns = required_columns
        self.message = (
            f"Zorunlu kolon eksik: '{column_name}'\n"
            f"Zorunlu kolonlar: {', '.join(required_columns)}"
        )
        super().__init__(self.message)


class InvalidDataFormatError(ProcessingError):
    """Raised when data format is invalid."""
    
    def __init__(self, expected_format: str, received_format: str = ""):
        self.expected_format = expected_format
        self.received_format = received_format
        self.message = (
            f"Geçersiz veri formatı.\n"
            f"Beklenen: {expected_format}\n"
            f"Alınan: {received_format}" if received_format else ""
        )
        super().__init__(self.message)


# ============================================================================
# Output Exceptions
# ============================================================================

class OutputError(IKAVMSError):
    """Base exception for output-related errors."""
    pass


class FileWriteError(OutputError):
    """Raised when writing to a file fails."""
    
    def __init__(self, file_path: str, reason: str = ""):
        self.file_path = file_path
        self.reason = reason
        self.message = (
            f"Dosya yazılamadı: '{file_path}'\n"
            f"Neden: {reason}\n" if reason else ""
            "Çözüm önerileri:\n"
            "  1. Dizinin yazma iznine sahip olduğunuzu kontrol edin\n"
            "  2. Disk alanının yeterli olduğundan emin olun"
        )
        super().__init__(self.message)


class FontNotFoundError(OutputError):
    """Raised when required font is not found for PDF generation."""
    
    def __init__(self, font_name: str):
        self.font_name = font_name
        self.message = (
            f"Font bulunamadı: '{font_name}'\n"
            "Çözüm:\n"
            "  1. DejaVu Sans fontunu yükleyin:\n"
            "     sudo apt-get install fonts-dejavu\n"
            "  2. Veya Docker container kullanın"
        )
        super().__init__(self.message)


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(IKAVMSError):
    """Base exception for configuration errors."""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when a required configuration is missing."""
    
    def __init__(self, config_name: str):
        self.config_name = config_name
        self.message = (
            f"Zorunlu yapılandırma eksik: '{config_name}'\n"
            "Çözüm: .env dosyasını veya ortam değişkenlerini kontrol edin."
        )
        super().__init__(self.message)


