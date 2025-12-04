import re
import subprocess
import sys

def check_history():
    print("🔍 Git Geçmişi Güvenlik Taraması Başlatılıyor...")
    
    # Hassas veri desenleri
    patterns = {
        "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "Generic Secret": r"(?i)(api_key|apikey|secret|password|token|auth)\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{8,}['\"]?",
        "Bearer Token": r"Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*",
        "Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----"
    }
    
    try:
        # Tüm git geçmişini al (patch formatında)
        # binary dosyaları atla (--no-binary)
        cmd = ["git", "log", "-p", "--all", "--no-binary"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        
        current_commit = "Unknown"
        suspicious_findings = []
        
        for line in process.stdout:
            if line.startswith("commit "):
                current_commit = line.strip().split(" ")[1]
            
            # Sadece eklenen satırları kontrol et (+)
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                for name, pattern in patterns.items():
                    if re.search(pattern, content):
                        # Config ve örnek dosyaları hariç tut
                        if "config.py" in content or "example" in content.lower():
                            continue
                            
                        suspicious_findings.append({
                            "commit": current_commit,
                            "type": name,
                            "content": content.strip()[:100] # İlk 100 karakter
                        })

        if suspicious_findings:
            print(f"\n⚠️  {len(suspicious_findings)} Şüpheli Durum Tespit Edildi!")
            print("Lütfen bu commitleri kontrol edin:")
            for find in suspicious_findings:
                print(f"- Commit: {find['commit']}")
                print(f"  Tip: {find['type']}")
                print(f"  İçerik: {find['content']}...")
                print("-" * 30)
            print("\nEğer bu veriler hassassa, git history'den tamamen temizlemeniz gerekir (BFG Repo-Cleaner veya git-filter-repo kullanarak).")
        else:
            print("\n✅ Git geçmişinde belirgin bir hassas veri bulunamadı.")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")
        print("Not: Bu scriptin çalışması için git kurulu olmalı ve bir git reposu içinde çalıştırılmalıdır.")

if __name__ == "__main__":
    check_history()
