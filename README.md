# BMKG MCP Server (Unofficial)

Server MCP (Model Context Protocol) untuk mengakses data dari BMKG (Badan Meteorologi, Klimatologi, dan Geofisika Indonesia). Server ini menyediakan akses mudah ke data gempa bumi, prakiraan cuaca, dan peringatan dini cuaca untuk seluruh wilayah Indonesia.

## ✨ Fitur

### 🌍 Data Gempa Bumi
- **Gempa Terkini**: Info gempa bumi terbaru dengan shakemap
- **15 Gempa M 5.0+**: Daftar gempa berkekuatan 5.0 atau lebih
- **15 Gempa Dirasakan**: Daftar gempa yang dirasakan masyarakat

### ☁️ Prakiraan Cuaca
- **Prakiraan 3 Hari**: Data lengkap hingga level kelurahan/desa
- **Update Per 3 Jam**: 8 forecast per hari (total ±24 forecast)
- **Data Lengkap**: Suhu, kelembaban, angin, tutupan awan, jarak pandang

### ⚠️ Peringatan Dini Cuaca
- **Nowcast**: Peringatan cuaca ekstrem aktif di seluruh Indonesia
- **Berbasis CAP**: Mengikuti standar Common Alerting Protocol
- **Level Kecamatan**: Detail wilayah terdampak hingga kecamatan
- **Bilingual**: Tersedia dalam Bahasa Indonesia dan English

### 🗺️ Pencarian Kode Wilayah
- **Database Lokal**: 91,220+ wilayah dari provinsi hingga desa
- **Pencarian Fleksibel**: Cari berdasarkan nama di semua level
- **Hierarki Lengkap**: Tampilan struktur provinsi > kabupaten > kecamatan > desa

## 📦 Instalasi

### Prasyarat
- Python 3.8 atau lebih baru
- uv (package manager) atau pip

### Langkah Instalasi

1. **Clone repository**
```bash
git clone https://github.com/revomkg/bmkg-mcp.git
cd bmkg-mcp
```

2. **Install dependencies**

Menggunakan uv (disarankan):
```bash
uv sync
```

Atau menggunakan pip:
```bash
pip install httpx xmltodict mcp
```

3. **Pastikan file base.csv ada**

File `base.csv` berisi database kode wilayah Indonesia. Pastikan file ini ada di direktori yang sama dengan `bmkg-server.py`.

## 🚀 Penggunaan

### Konfigurasi di Claude Desktop

Tambahkan konfigurasi berikut ke file `claude_desktop_config.json`:

**Lokasi file konfigurasi:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Isi konfigurasi:**
```json
{
  "mcpServers": {
    "bmkg": {
      "command": "python",
      "args": ["/path/to/bmkg-mcp/bmkg-server.py"]
    }
  }
}
```

Atau dengan uv:
```json
{
  "mcpServers": {
    "bmkg": {
      "command": "uv",
      "args": ["run", "/path/to/bmkg-mcp/bmkg-server.py"]
    }
  }
}
```

## 🔧 Tools yang Tersedia

### 1. `get_latest_earthquake()`
Mendapatkan informasi gempa bumi terkini dengan shakemap.

**Return:**
- Waktu kejadian
- Magnitudo
- Kedalaman
- Lokasi
- Potensi tsunami
- URL shakemap

### 2. `get_significant_earthquakes()`
Daftar 15 gempa bumi terkini dengan magnitudo 5.0+.

**Return:**
- Array of earthquakes dengan detail lengkap
- Potensi tsunami untuk setiap gempa

### 3. `get_felt_earthquakes()`
Daftar 15 gempa bumi yang dirasakan masyarakat.

**Return:**
- Array of earthquakes
- Info daerah yang merasakan

### 4. `search_location_code(location_name, admin_level)`
Mencari kode wilayah berdasarkan nama lokasi.

**Parameters:**
- `location_name` (string): Nama lokasi yang dicari
- `admin_level` (string, optional): Filter level administratif
  - `"all"` - Semua level (default)
  - `"province"` / `"provinsi"` - Provinsi
  - `"regency"` / `"kabkota"` - Kabupaten/Kota
  - `"district"` / `"kecamatan"` - Kecamatan
  - `"village"` / `"desa"` - Kelurahan/Desa

**Contoh:**
```python
search_location_code("Pandak", "village")
# Returns: 33.02.07.2005 - Pandak di Jawa Tengah > Banyumas > Sumpiuh
```

### 5. `get_villages_in_district(district_code)`
Mendapatkan semua kelurahan/desa dalam kecamatan tertentu.

**Parameters:**
- `district_code` (string): Kode kecamatan (contoh: "33.02.07")

**Return:**
- Daftar lengkap kelurahan/desa dengan kode siap pakai

### 6. `get_weather_forecast(kode_wilayah)`
Prakiraan cuaca 3 hari untuk wilayah tertentu.

**Parameters:**
- `kode_wilayah` (string): Kode wilayah level desa (4 segmen)

**Return:**
- Prakiraan 3 hari dengan 8 forecast per hari
- Suhu, kelembaban, cuaca, angin, tutupan awan, jarak pandang
- Total ±24 forecast points

**Contoh:**
```python
get_weather_forecast("33.02.07.2005")  # Pandak, Sumpiuh, Banyumas
```

### 7. `get_weather_alerts(language)`
Daftar peringatan dini cuaca aktif di Indonesia.

**Parameters:**
- `language` (string, optional): "id" atau "en" (default: "id")

**Return:**
- RSS feed peringatan cuaca aktif
- Link ke detail CAP tiap provinsi

### 8. `get_weather_alert_detail(cap_code, language)`
Detail peringatan dini cuaca untuk provinsi tertentu.

**Parameters:**
- `cap_code` (string): Kode CAP dari link di weather alerts
- `language` (string, optional): "id" atau "en" (default: "id")

**Return:**
- Detail lengkap CAP
- Wilayah kecamatan terdampak
- Waktu berlaku dan berakhir
- Tingkat bahaya (severity, urgency, certainty)

### 9. `search_weather_alerts_by_kecamatan(kecamatan, language)`
Mencari peringatan dini untuk kecamatan tertentu.

**Parameters:**
- `kecamatan` (string): Nama kecamatan
- `language` (string, optional): "id" atau "en" (default: "id")

**Return:**
- Peringatan yang mempengaruhi kecamatan tersebut
- Detail wilayah terdampak

## 💡 Contoh Penggunaan

### Mencari Cuaca untuk Lokasi Tertentu

**User:** "Bagaimana cuaca di Pandak, Sumpiuh?"

**Claude akan:**
1. Memanggil `search_location_code("Pandak", "village")`
2. Menemukan kode: `33.02.07.2005`
3. Memanggil `get_weather_forecast("33.02.07.2005")`
4. Menampilkan prakiraan 3 hari lengkap

### Cek Gempa Terkini

**User:** "Ada gempa apa hari ini?"

**Claude akan:**
1. Memanggil `get_latest_earthquake()`
2. Menampilkan info gempa terkini + shakemap
3. Bisa memanggil `get_significant_earthquakes()` untuk daftar lengkap

### Cek Peringatan Cuaca di Daerah Saya

**User:** "Ada peringatan cuaca untuk Jagakarsa?"

**Claude akan:**
1. Memanggil `search_weather_alerts_by_kecamatan("Jagakarsa")`
2. Menampilkan peringatan aktif (jika ada)
3. Detail tingkat bahaya dan waktu berlaku

## 📊 Sumber Data

Data yang digunakan server ini berasal dari:
- **BMKG (data.bmkg.go.id)**: Data gempa bumi dan cuaca resmi
- **BMKG API (api.bmkg.go.id)**: API prakiraan cuaca dan peringatan dini
- **Kode Wilayah**: Database lokal berdasarkan Keputusan Mendagri No. 100.1.1-6117 Tahun 2022

## 🔒 Batasan Akses

Sesuai dokumentasi BMKG:
- **Prakiraan Cuaca**: 60 permintaan per menit per IP
- **Peringatan Dini**: 60 permintaan per menit per IP

Gunakan dengan bijak untuk menghindari rate limiting.

## 🤝 Kontribusi

Kontribusi selalu diterima! Silakan:
1. Fork repository ini
2. Buat branch baru (`git checkout -b feature/fitur-baru`)
3. Commit perubahan (`git commit -am 'Tambah fitur baru'`)
4. Push ke branch (`git push origin feature/fitur-baru`)
5. Buat Pull Request

## 📝 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

Proyek ini adalah *unofficial* dan tidak berafiliasi dengan BMKG. Data yang digunakan berasal dari sumber publik BMKG.

## ⚠️ Disclaimer

Server ini dibuat untuk memudahkan akses data BMKG melalui Model Context Protocol. Pengguna bertanggung jawab untuk mematuhi syarat dan ketentuan penggunaan data dari BMKG.

## 🙏 Credits

- Data gempa dan cuaca dari [BMKG](https://www.bmkg.go.id)
- Database kode wilayah berdasarkan Keputusan Mendagri
- Menggunakan [FastMCP](https://github.com/jlowin/fastmcp) untuk MCP server

## 📧 Kontak

Untuk pertanyaan, saran, atau laporan bug, silakan buat issue di repository ini.

---

**⭐ Jika proyek ini bermanfaat, berikan bintang di GitHub!**
