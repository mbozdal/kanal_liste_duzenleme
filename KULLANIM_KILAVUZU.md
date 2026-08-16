# TCL Kanal Editörü Kullanım Kılavuzu

Bu kılavuz, özellikle **Türksat kanal güncellemeleri sonrasında** TCL ve Thomson marka televizyonlarınızın kanal listelerini düzenlemeniz için hazırlanmıştır.

## 1. Televizyondan Kanal Listesini Alma (USB Belleğe Aktarım)

1. FAT32 formatında biçimlendirilmiş boş bir USB belleği televizyonunuza takın.
2. Televizyonunuzun kumandasından **Ayarlar (Settings)** menüsüne girin.
3. **Kanal (Channel)** > **Kanal Düzenleme (Channel Organizer)** veya **Kanal Aktarımı (Channel Transfer)** seçeneklerini bulun. (Menü isimleri TV modelinize göre değişiklik gösterebilir).
4. **Kanalları USB'ye Aktar (Export to USB)** seçeneğini seçin.
5. İşlem tamamlandığında USB belleğinizde `ChannelList...` veya benzer isimli `.tar` uzantılı bir dosya oluşacaktır. Bu dosyayı bilgisayarınıza kopyalayın. **(Orijinal dosyanın bir yedeğini mutlaka farklı bir klasörde saklayın!)**

## 2. Programı Çalıştırma

- Bilgisayarınızda Python yüklü olduğundan emin olun.
- Program klasöründeki `kanal_duzenle.py` dosyasına çift tıklayarak veya komut satırından `python kanal_duzenle.py` yazarak uygulamayı başlatın.
- 
<img width="1231" height="767" alt="image" src="https://github.com/user-attachments/assets/26392e10-b955-4ab9-b4a2-53b06fcec300" />

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



## 3. Kanal Listesini Açma ve Düzenleme

1. **Dosya Açma:** Program açıldığında sol üst köşedeki **"TAR Aç"** butonuna tıklayın. USB belleğinizden bilgisayarınıza aldığınız `.tar` uzantılı dosyayı seçin.
2. **Kanal Arama:** Üst taraftaki **"Ara"** kutucuğuna kanal ismini yazarak (örneğin "TRT" veya "ATV") aradığınız kanalı hızlıca bulabilirsiniz.
3. **Sürükle - Bırak (Drag & Drop):** Bir kanalı taşımak için üzerine farenin sol tuşuyla tıklayıp basılı tutun ve taşımak istediğiniz sıraya götürüp bırakın.
4. **Butonla Taşıma:** Taşımak istediğiniz kanalı seçip yukarıdaki **"Yukarı (▲)"** veya **"Aşağı (▼)"** butonlarına tıklayarak da yerini değiştirebilirsiniz.
5. **Bilgileri Düzenleme:** Kanalın yeni sırasını (Yeni No) veya ismini (Kanal Adı) değiştirmek için o hücrenin üzerine **çift tıklayın**. Değişikliği yapıp `Enter` tuşuna basın.

## 4. Sıralamayı Tamamlama (ÖNEMLİ)

Kanalların yerlerini değiştirdikten sonra, numaraların 1, 2, 3, 4 şeklinde sıralı gitmesi gerekmektedir. 

* Sıralama işlemini bitirdiğinizde yukarıdaki menüden **"1..N Yeniden Numarala"** butonuna tıklayın. 
* Bu işlem, yukarıdan aşağıya doğru tüm kanallara sırasıyla yeni numara verecektir.
* **Uyarı:** Kanal numaralarının (Yeni No) benzersiz (tekrarsız) olması şarttır. Aksi takdirde program hata verecektir.

## 5. CSV ile Excel'de Düzenleme (İsteğe Bağlı)

Kanalları Excel üzerinden topluca düzenlemek isterseniz:
1. **"CSV Dışa Aktar"** butonuyla listeyi bilgisayarınıza kaydedin.
2. Excel'de açıp `New_No` ve `Channel_Name` sütunlarında değişikliklerinizi yapın.
3. Excel'den kaydettikten sonra programdaki **"CSV İçe Aktar"** butonuyla düzenlenmiş dosyayı geri yükleyin.

## 6. Kaydetme ve TV'ye Yükleme

1. Tüm düzenlemeleriniz bittikten sonra sol üstteki **"Kaydet / TAR Oluştur"** butonuna tıklayın.
2. Yeni dosyayı bilgisayarınızda bir konuma kaydedin (örneğin `Yeni_Kanal_Listesi.tar`).
3. Bu yeni dosyayı USB belleğinize kopyalayın (eski orijinal dosyanın ismini neyse o isimle yüklemeniz tavsiye edilir, genellikle TV orijinal ismi arar. Örn: `user_setting_backup.tar`).
4. USB belleği televizyonunuza takın.
5. TV'nizin menüsünden **Kanal Aktarımı** bölümüne girip, bu sefer **USB'den TV'ye Aktar (Import from USB)** seçeneğini seçin.
6. İşlem tamamlandıktan sonra televizyonunuz yeniden başlayabilir. Artık yeni kanal sıralamanız kullanıma hazırdır!

---
*Karşılaştığınız hatalar veya geri bildirimleriniz için GitHub üzerinden konu (Issue) açabilirsiniz.*
