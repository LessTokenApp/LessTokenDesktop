# AI Clipboard Optimizer

Windows icin kullanimi kolay pano yardimcisi. Metin, gorsel ve dosya islemleri ayni pencerede toplanir.

## En kolay kullanim

1. `C:\Projects\LessToken` klasorunu acin.
2. `Start AI Clipboard Optimizer.bat` dosyasina cift tiklayin.
3. Pencerede su sekmeleri kullanin:
   - `Metin`: panodaki metni alir; duzeltme, kisaltma, resmi ton, ozet, maddeleme, ceviri ve e-posta taslagi islemleri sunar.
   - `Gorsel`: panodaki veya dosyadaki gorseli alir; genislik, kalite ve format secerek kucultur.
   - `Dosya`: metin, Markdown, kod, PDF ve Word dosyalarindan metin yuklemeyi dener.

## Gorsel kucultme

`Gorsel` sekmesinde once `Panodaki gorseli al` veya `Gorsel dosyasi ac` secin. Sonra `Maks. genislik`, `Kalite` ve `Format` ayarlarini belirleyip `Gorseli kucult ve kaydet` dugmesine basin. Ciktilar `C:\Projects\LessToken\outputs` klasorune kaydedilir.

## Istege bagli paketler

Temel metin/pano ve gorsel kucultme paketleri kurulu. OpenAI, PDF, Word ve OCR icin gerekirse `Install Optional Packages.bat` dosyasina cift tiklayin. Internet baglantisi gerekebilir.

## Gercek AI kullanimi

Uygulama varsayilan olarak yerel modda calisir. Gercek AI islemleri icin PowerShell'de sunlari ayarlayin:

```powershell
$env:AI_CLIPBOARD_OPTIMIZER_AI_PROVIDER="openai"
$env:OPENAI_API_KEY="anahtarinizi_buraya_yazin"
```

API anahtari yoksa uygulama yine acilir; ceviri gibi islemler AI gerektirdigini belirtir.

## Sorun olursa

`Start AI Clipboard Optimizer - Console.bat` dosyasini calistirin. Hata mesajini ekranda gosterir.
