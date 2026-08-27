# 🎙️ VoxTurbo AI — Kullanıcı Kılavuzu (Türkçe)

**VoxTurbo AI**, bilgisayarınız için akıllı ve ultra hızlı bir sesli yazma (dikte) asistanıdır. Konuştuğunuz kelimeleri anında metne dönüştürür ve açık olan herhangi bir uygulamaya (WhatsApp, Telegram, tarayıcı, e-posta, Word, Excel, kod editörü veya terminal) otomatik olarak yazar.

Tüm ses işleme süreci **%100 yerel olarak bilgisayarınızda** gerçekleşir; sesiniz veya metniniz asla internete veya buluta gönderilmez.

---

## ⚡ 1. Dikte Etmenin İki Kolay Yolu

VoxTurbo AI'ı iki farklı şekilde kullanabilirsiniz: klavye kısayoluyla veya tamamen eller serbest (sesle).

### Yöntem A. Kısayol Tuşu ile Dikte (Klasik)
1. Farenizin imlecini yazı yazmak istediğiniz alana getirin (örneğin Telegram mesaj kutusu, Word belgesi veya arama çubuğu).
2. Klavyenizden **`Win + Boşluk`** (`Super + Space`) tuşlarına basın.
   - *Ekranda ses dalgası göstergesi belirir ve sağ alttaki simge kırmızıya döner.*
3. Mikrofonunuza doğal bir tempoda konuşun.
4. Kaydı durdurmak için tekrar **`Win + Boşluk`** tuşlarına basın.
5. Noktalama işaretleri ve büyük harfleri düzenlenmiş metin anında imlecin bulunduğu yere yazılır.

---

### Yöntem B. Eller Serbest Dikte (Sesli Aktivasyon / Wake Word)
*Elleriniz klavyede, kod yazarken veya kahve içerken mükemmeldir.*

1. Başlatma kelimesini söyleyin: **"Hey Jarvis"** (veya ayarladığınız diğer bir kelime, örn. *Alexa*).
   - *Kayıt göstergesi ekranda anında otomatik olarak açılır.*
2. Cümlenizi veya düşüncenizi normal hızda söyleyin.
3. Konuşmanız bittiğinde **yaklaşık 1 saniye sessiz kalın**.
4. Yapay zeka sustuğunuzu anlar, kaydı otomatik olarak tamamlar ve metni imlecin olduğu yere yapıştırır.

---

## 🌐 2. Desteklenen Diller ve Otomatik Algılama

VoxTurbo AI birden fazla dili tam olarak destekler:
* 🇹🇷 **Türkçe (tr)** — Türkçe karakterler (*ç, ğ, ı, ö, ş, ü*) ve dilbilgisi kurallarına tam uyum.
* 🇷🇺 **Rusça (ru)** — GigaAM v2 motoru ile konuşma hızından daha hızlı anlık çeviri.
* 🇬🇧 **İngilizce (en)** — Yüksek doğruluk ve zengin kelime haznesi.
* 🇰🇿 **Kazakça (kk / Қазақша)**
* ⚡ **Otomatik Algılama (Auto)** — Program hangi dilde konuştuğunuzu ilk 1-2 saniye içinde kendisi anlar ve en uygun yapay zeka modeline yönlendirir.

---

## ⚙️ 3. Sistem Tepsisi Simgesi (Saatin Yanı)

Ekranın sağ alt köşesindeki dairesel VoxTurbo simgesi durumunuzu gösterir:
* 🟢 **Yeşil:** Bellekte hazır — sesinizi veya kısayol tuşunu bekliyor.
* 🔴 **Kırmızı:** Şu anda sesiniz kaydediliyor.
* 🟡 **Sarı:** Yapay zeka sesi metne dönüştürüyor ve ekrana yazıyor.

### Sağ Tık Menüsü:
Simgeye sağ tıklayarak şunları yapabilirsiniz:
1. **🌟 Engine & Model:** Yapay zeka motorunu seçin (GigaAM veya çok dilli Whisper).
2. **🌐 Language:** Dikte dilini değiştirin (Türkçe, Rusça, İngilizce, Kazakça veya Otomatik).
3. **🗣️ Wake Word:** Sesli başlatmayı (*Hey Jarvis, Alexa* vb.) açın veya kapatın.
4. **🔤 Smart Punctuation:** Otomatik nokta, virgül ve soru işareti koyma özelliğini açıp kapatın.
5. **✨ Floating Voice HUD:** Ekrandaki kayan ses dalgası animasyonunu açıp kapatın.
6. **⚙️ Ayarlar...:** Detaylı grafiksel ayarlar penceresini açın.

---

## 🎛️ 4. Ayarlar Penceresi (Sekmeler)

Ayarları açmak için tepsideki simgeye sağ tıklayıp **"⚙️ Настройки... / Ayarlar..."** seçeneğini seçin.

### 🎙️ Ses (Audio) Sekmesi
* **Giriş Cihazı:** Kullanmak istediğiniz mikrofonu (laptop mikrofonu, USB mikrofon veya kulaklık) seçin.
* **Mikrofon Testi:** *“▶ Test”* butonuna basıp konuşarak yeşil seviye çubuğundan sesinizi kontrol edin.

### ⚡ Motor (Engine) Sekmesi
* **Aktif Model:** Çok dilli kullanım (Türkçe dahil) için *Whisper Large-v3-Turbo* veya Rusça için *GigaAM v2*.
* **Dikte Dili:** Varsayılan dilinizi belirleyin.
* **CPU Çekirdekleri:** İşlemci çekirdek sayısı (önerilen: 4 veya 6).
* **Akıllı Noktalama:** Konuşmanızı noktalama işaretleriyle düzgün cümlelere dönüştürür.

### 🗣️ Wake Word (Sesli Aktivasyon) Sekmesi
* **Sesli Aktivasyonu Etkinleştir:** Sesle başlatma için işaretleyin.
* **Anahtar Kelime:** Başlatma kelimesini seçin (*Hey Jarvis, Alexa, Hey Mycroft, Weather, Timer*).
* **Hassasiyet (Eşik):** Modelin tetiklenme hassasiyetini ayarlar.
* **Otomatik Durma Süresi:** Konuşma bittikten sonra ne kadar süre sessizlik bekleneceği (varsayılan: 0.8 saniye).
* **Sesli Bildirim:** Kelime algılandığında kısa bir uyarı tonu çalar.
* **Özel Modeller:** Kendi eğittiğiniz `.onnx` modellerini `models/wakewords/` klasörüne ekleyebilirsiniz.

### ⌨️ Kısayollar (Hotkeys) Sekmesi
* Dikteyi başlatan klavye tuşunu seçin:
  - `Super + Space` (`Win + Boşluk`) — Standart varsayılan.
  - `Alt + Space`
  - `Ctrl + Shift + Space`
  - `F8` (Tek tuş)

---

## 💡 5. İpuçları ve En İyi Verim

1. **Doğal Konuşun:** Kelimeler arasında yapay duraklamalar yapmanıza gerek yoktur; yapay zeka akıcı insan konuşmasını en iyi şekilde anlar.
2. **Noktalama İşaretlerini Söyleme:** İsterseniz doğrudan *"virgül"*, *"nokta"*, *"soru işareti"*, *"yeni satır"* diyerek de işaret koydurabilirsiniz.
3. **Arka Plan Gürültüsü:** Entegre Silero VAD filtresi sayesinde oda ve fan gürültüsü konuşmanızdan otomatik olarak filtrelenir.

---

## ❓ Sıkça Sorulan Sorular (SSS)

**S: Dikte edilen metin nereye yazılır?**  
**C:** O anda imlecinizin yanıp söndüğü metin alanına doğrudan yazılır (`Ctrl + V` yapmışsınız gibi).

**S: Metin otomatik yapışmadıysa ne yapmalıyım?**  
**C:** Son dikte edilen metin her zaman panonuzda kayıtlıdır (`Ctrl + V` ile yapıştırabilirsiniz) ve sağ alttaki menüde `💬 Last: ...` kısmında görünür.

**S: Programdan tamamen nasıl çıkılır?**  
**C:** Sağ alttaki simgeye sağ tıklayıp **"❌ Quit VoxTurbo AI"** seçeneğine tıklayın.
