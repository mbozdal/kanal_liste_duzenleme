# TCL Channel Editor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!WARNING]
> **Sorumluluk Reddi:** Bu uygulamanın kullanımı tamamen kullanıcının kendi sorumluluğundadır. İşlem yapmadan önce her zaman orijinal kanal listenizin yedeğini almayı unutmayın. Olası bir veri kaybı veya cihaz arızasından geliştirici sorumlu tutulamaz.

TCL marka televizyonlar için geliştirilmiş ancak birçok model için uyumlu olabilir, özellikle **Türksat kanal güncellemeleri sonrasında** bozulan veya karışan kanal sıralamasını bilgisayarınızdan kolayca düzenlemenizi sağlayan, Windows uyumlu bir masaüstü uygulamasıdır.

Televizyonunuzdan USB belleğe aktardığınız `tar` uzantılı kanal listesini bu program ile açıp düzenleyebilir ve tekrar televizyonunuza yükleyebilirsiniz.

## 🚀 Özellikler

- **Sürükle & Bırak Desteği:** Kanalları farenizle tutup sürükleyerek kolayca sıralayabilirsiniz.
- **Toplu Yeniden Numaralandırma:** Yaptığınız sıralamadan sonra tüm kanallara baştan sona (1'den N'e) otomatik numara verebilirsiniz.
- **CSV İçe/Dışa Aktarma:** Kanal listenizi Excel'de düzenlemek isterseniz CSV olarak dışa aktarabilir, düzenledikten sonra tekrar içe aktarabilirsiniz.
- **Hızlı Arama & Filtreleme:** Binlerce kanal arasında istediğiniz kanalı anında bulabilirsiniz.
- **Güvenli Düzenleme:** Program televizyonunuzun veritabanı (CRC) yapısını bozmaz. Orijinal dosyanın yedeğini korur ve sadece yeni bir TAR dosyası oluşturur.

## 🛠️ Kurulum ve Çalıştırma

Program Python ile yazılmıştır. Çalıştırmak için sisteminizde [Python 3.x](https://www.python.org/downloads/) yüklü olmalıdır.

1. Depoyu bilgisayarınıza indirin.
2. Komut satırını açın ve programın bulunduğu klasöre gidin.
3. Aşağıdaki komutu çalıştırın:
   ```bash
   python TCL_Channel_Editor_v3_CSV_Sort_DragDrop.py
   ```

*(Alternatif olarak, programı doğrudan bir `.exe` haline getirmek için `pyinstaller` kullanabilirsiniz.)*

## 📖 Kullanım Kılavuzu

Adım adım kullanım talimatları, televizyondan dosya alma ve televizyona yükleme adımları için detaylı [KULLANIM KILAVUZU (Türkçe)](KULLANIM_KILAVUZU.md) dosyasını inceleyin.

## ⚠️ Uyarılar

- Programı kullanmadan önce televizyonunuzdan aldığınız orijinal `.tar` dosyasının bir **yedeğini mutlaka saklayın**.
- Bu program açık kaynaklı bir topluluk projesidir. TCL veya Thomson firmaları ile resmi bir bağı yoktur. Kullanım sonucu oluşabilecek sorunlarda sorumluluk kullanıcıya aittir.

## 🤝 Katkıda Bulunma

Hata bildirimleri, yeni özellik önerileri ve "Pull Request"ler (PR) her zaman kabul edilmektedir. Katkılarınızla aracı daha da geliştirebiliriz!

## 📜 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.
