# AbaySystems - Tumen Alüminyum Backend

**AbaySystems**, Tumen Alüminyum için geliştirilmiş; bayi yönetimi, proje tekliflendirme, sipariş takibi ve üretim süreçlerini dijitalleştiren kapsamlı bir backend projesidir. Modern web teknolojileri kullanılarak, yüksek performanslı ve ölçeklenebilir bir yapıda tasarlanmıştır.

## 🚀 Proje Hakkında

Bu sistem, alüminyum doğrama sektöründeki karmaşık hesaplama ve süreç yönetimini kolaylaştırmayı hedefler. Bayiler, sistem üzerinden kendi müşterileri için projeler oluşturabilir, kapı/pencere sistemlerini seçip ölçülerini girerek anlık maliyet ve teklif hesabı yapabilirler. Kesinleşen teklifler siparişe dönüştürülerek üretim bandına iletilir.

### Temel Özellikler

*   **🔐 Çoklu Rol Yönetimi:** Admin ve Bayi (Dealer) yetkilendirmesi.
*   **🏗️ Dinamik Ürün Yapılandırma:** Sistemler, varyantlar, profiller, camlar ve aksesuarlar dinamik olarak tanımlanabilir.
*   **📐 Proje & Teklif Motoru:**
    *   Gelişmiş metraj ve maliyet hesaplama algoritmaları.
    *   Profil kesim ölçüleri ve cam ebatlarının otomatik hesaplanması.
    *   Farklı para birimleri ve dinamik fiyatlandırma desteği.
*   **📄 PDF Raporlama:**
    *   Müşteri Teklif Formu
    *   İmalat/Kesim Listeleri
    *   Cam Sipariş Listeleri
    *   Malzeme İhtiyaç Listeleri
*   **🏭 Üretim Takibi:** Siparişlerin boya, cam ve montaj durumlarının takibi.
*   **🔄 Entegrasyon:** Frontend uygulamaları (React/Vue vb.) için RESTful API servisleri.

---

## 🛠️ Teknik Mimari

Proje, **Python** tabanlı olup, asenkron yapısı sayesinde yüksek eşzamanlılık (concurrency) gerektiren işlemleri başarıyla yönetir.

| Bileşen | Teknoloji | Açıklama |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | Yüksek performanslı, modern, asenkron API çatısı. |
| **Veritabanı** | **PostgreSQL** | Güçlü, açık kaynaklı ilişkisel veritabanı. |
| **ORM** | **SQLAlchemy** | Python nesneleri ile veritabanı etkileşimi. |
| **Migrasyon** | **Alembic** | Veritabanı şema değişikliklerinin versiyonlanması. |
| **Doğrulama** | **Pydantic** | Veri doğrulama ve serileştirme (Schema validation). |
| **Güvenlik** | **OAuth2 / JWT** | Güvenli kimlik doğrulama ve yetkilendirme. |

---

## 📂 Proje Yapısı

```
abaysystems/
├── app/
│   ├── api/            # API yapılandırmaları ve router tanımları
│   ├── core/           # Temel ayarlar (Config, Security, JWT)
│   ├── crud/           # Veritabanı işlemleri (Create, Read, Update, Delete)
│   ├── db/             # Veritabanı bağlantısı ve oturum yönetimi
│   ├── models/         # SQLAlchemy veritabanı modelleri (Tablo tanımları)
│   ├── routes/         # API uç noktaları (Endpoints)
│   ├── schemas/        # Pydantic veri şemaları (Request/Response modelleri)
│   ├── services/       # İş mantığı katmanı (Business Logic)
│   └── utils/          # Yardımcı fonksiyonlar
├── migrations/         # Alembic veritabanı migrasyon dosyaları
├── media/              # Yüklenen dosyalar (Resimler, PDF'ler)
├── .env                # Ortam değişkenleri (Gizli anahtarlar, DB URL)
├── main.py             # Uygulamanın giriş noktası
└── requirements.txt    # Proje bağımlılıkları
```

---

## 🗄️ Veritabanı Şeması

Veritabanı, ilişkisel bir yapıda tasarlanmış olup temel olarak şu modüllerden oluşur:

### 1. Kullanıcı Yönetimi (`app_user`)
*   Kullanıcılar `admin` veya `dealer` rolüne sahiptir.
*   Bayi bilgileri (Adres, Telefon, Firma Adı) bu tabloda tutulur.
*   Güvenlik için şifreler hashlenerek saklanır (`password_hash`).

### 2. Ürün Kataloğu
Sistemin kalbini oluşturan tanımlamalar:
*   **`System`**: Ana sistem ailesi (Örn: Sürme Seri, Menteşeli Seri).
*   **`SystemVariant`**: Sistemin alt varyasyonları.
*   **`Profile`**: Alüminyum profiller (Ağırlık, stok kodu, boyalı/boyasız durumu).
*   **`GlassType`**: Cam tipleri (Kalınlık, özellikler).
*   **`Color`**: Profil ve cam renk kartelası.
*   **`OtherMaterial`**: Fitil, tekerlek, kol gibi aksesuarlar.

### 3. Proje ve Sipariş (`project`, `sales_order`)
*   **`Project`**: Bir bayinin oluşturduğu iş dosyası. İçerisinde birden fazla "Sistem" barındırır.
*   **`ProjectSystem`**: Projeye eklenen her bir doğrama ünitesi. Ölçü (`width`, `height`) ve adet bilgisini tutar.
*   **`ProjectSystemProfile` / `Glass` / `Material`**: O ünite için hesaplanmış malzeme reçetesi.
*   **`SalesOrder`**: Onaylanan projenin siparişe dönüşmüş hali.

---

## 🔌 API Dokümantasyonu

API, RESTful prensiplerine uygun olarak tasarlanmıştır. Swagger UI üzerinden interaktif olarak test edilebilir.

### Önemli Endpoint'ler

#### 🔐 Kimlik Doğrulama (`/api/auth`)
*   `POST /token`: Giriş yap (Access Token & Refresh Cookie döner).
*   `POST /refresh`: Access Token yenile.
*   `POST /logout`: Güvenli çıkış.

#### 🏗️ Projeler (`/api/projects`)
*   `GET /`: Tüm projeleri listele (Filtreleme destekler).
*   `POST /`: Yeni proje oluştur.
*   `GET /{id}`: Proje detaylarını getir.
*   `PUT /{id}/requirements`: Projeye sistem/malzeme ekle.
*   `GET /{id}/requirements-detailed`: Projenin detaylı malzeme dökümünü al.

#### 📦 Siparişler (`/api/orders`)
*   `POST /`: Projeyi siparişe dönüştür.
*   `GET /`: Siparişleri listele.

---

## ⚙️ Kurulum ve Çalıştırma

Geliştirme ortamında projeyi ayağa kaldırmak için aşağıdaki adımları izleyin:

### 1. Gereksinimler
*   Python 3.10+
*   PostgreSQL

### 2. Kurulum

Projeyi klonlayın ve proje dizinine gidin:
```bash
git clone https://github.com/tumen-aluminyum/abaysystems.git
cd abaysystems
```

Sanal ortam (Virtual Environment) oluşturun ve aktif edin:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

### 3. Yapılandırma (.env)
Kök dizinde `.env` dosyası oluşturun ve gerekli ayarları girin:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/abaysystems_db
SECRET_KEY=guclu_bir_gizli_anahtar
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MEDIA_ROOT=media
```

### 4. Veritabanı Migrasyonları
Veritabanı tablolarını oluşturmak için Alembic kullanın:
```bash
alembic upgrade head
```

### 5. Uygulamayı Başlatma
Uygulamayı geliştirme modunda başlatın:
```bash
uvicorn main:app --reload
```
API artık `http://localhost:8000` adresinde çalışmaktadır.
Swagger dokümantasyonuna `http://localhost:8000/docs` adresinden erişebilirsiniz.