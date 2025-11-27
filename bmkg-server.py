import httpx
import xmltodict
import json
import csv
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Unofficial BMKG",
    instructions="""
    Server MCP untuk mengakses data dari BMKG (Badan Meteorologi, Klimatologi, dan Geofisika Indonesia).

    PENTING: Data yang disediakan bersumber dari BMKG. Wajib mencantumkan BMKG sebagai sumber data
    pada setiap penggunaan dan tampilan data.

    Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
    Website: https://www.bmkg.go.id
    Data API: https://data.bmkg.go.id
    """
)

BMKG_ATTRIBUTION = "Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) - https://www.bmkg.go.id"

@mcp.tool()
async def get_latest_earthquake() -> str:
    """
    Mengambil data gempa bumi terbaru yang dirasakan (M 5.0+ atau signifikan).
    Mengembalikan detail waktu, lokasi, magnitudo, dan potensi tsunami.

    Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
    """
    url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = xmltodict.parse(response.content)
            gempa = data['Infogempa']['gempa']
            
            result = {
                "waktu": f"{gempa['Tanggal']} - {gempa['Jam']}",
                "magnitudo": gempa['Magnitude'],
                "kedalaman": gempa['Kedalaman'],
                "koordinat": f"{gempa['Lintang']}, {gempa['Bujur']}",
                "lokasi": gempa['Wilayah'],
                "potensi": gempa['Potensi'],
                "dirasakan": gempa.get('Dirasakan', '-'),
                "shakemap_url": f"https://static.bmkg.go.id/{gempa['Shakemap']}",
                "sumber": BMKG_ATTRIBUTION
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Gagal mengambil data gempa: {str(e)}"

@mcp.tool()
async def get_significant_earthquakes() -> str:
    """
    Mengambil daftar 15 gempabumi terkini dengan magnitudo 5.0 atau lebih.
    Mengembalikan detail waktu, lokasi, magnitudo, kedalaman, dan potensi tsunami.

    Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
    """
    url = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = xmltodict.parse(response.content)

            gempa_list = data['Infogempa']['gempa']
            if isinstance(gempa_list, dict):
                gempa_list = [gempa_list]

            results = []
            for gempa in gempa_list:
                result = {
                    "waktu": f"{gempa['Tanggal']} - {gempa['Jam']}",
                    "datetime_utc": gempa.get('DateTime', '-'),
                    "magnitudo": gempa['Magnitude'],
                    "kedalaman": gempa['Kedalaman'],
                    "koordinat": f"{gempa['Lintang']}, {gempa['Bujur']}",
                    "lokasi": gempa['Wilayah'],
                    "potensi": gempa.get('Potensi', '-')
                }
                results.append(result)

            return json.dumps({
                "total": len(results),
                "data": results,
                "sumber": BMKG_ATTRIBUTION
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Gagal mengambil data gempa M 5.0+: {str(e)}"

@mcp.tool()
async def get_felt_earthquakes() -> str:
    """
    Mengambil daftar 15 gempabumi terkini yang dirasakan masyarakat.
    Mengembalikan detail waktu, lokasi, magnitudo, kedalaman, dan daerah yang merasakan.

    Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
    """
    url = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.xml"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = xmltodict.parse(response.content)

            gempa_list = data['Infogempa']['gempa']
            if isinstance(gempa_list, dict):
                gempa_list = [gempa_list]

            results = []
            for gempa in gempa_list:
                result = {
                    "waktu": f"{gempa['Tanggal']} - {gempa['Jam']}",
                    "datetime_utc": gempa.get('DateTime', '-'),
                    "magnitudo": gempa['Magnitude'],
                    "kedalaman": gempa['Kedalaman'],
                    "koordinat": f"{gempa['Lintang']}, {gempa['Bujur']}",
                    "lokasi": gempa['Wilayah'],
                    "dirasakan": gempa.get('Dirasakan', '-')
                }
                results.append(result)

            return json.dumps({
                "total": len(results),
                "data": results,
                "sumber": BMKG_ATTRIBUTION
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Gagal mengambil data gempa dirasakan: {str(e)}"

@mcp.tool()
async def search_location_code(location_name: str, admin_level: str = "all") -> str:
    """
    Mencari kode wilayah Indonesia berdasarkan nama lokasi menggunakan database lokal.
    Mendukung pencarian di semua level: provinsi, kabupaten/kota, kecamatan, kelurahan/desa.

    Args:
        location_name: Nama lokasi yang dicari (contoh: "Pandak", "Sumpiuh", "Banyumas")
        admin_level: Level administratif yang dicari:
                    - "province" atau "provinsi" untuk provinsi
                    - "regency" atau "kabkota" untuk kabupaten/kota
                    - "district" atau "kecamatan" untuk kecamatan
                    - "village" atau "desa" untuk kelurahan/desa
                    - "all" untuk mencari di semua level (default)

    Returns:
        Daftar kode wilayah yang cocok dengan pencarian, dengan hierarki lengkap.

    Note:
        Kode level desa (4 segmen) dapat langsung digunakan untuk get_weather_forecast()
    """
    try:
        csv_path = os.path.join(os.path.dirname(__file__), "base.csv")

        if not os.path.exists(csv_path):
            return json.dumps({
                "error": "File base.csv tidak ditemukan",
                "path": csv_path
            }, indent=2)

        results = []
        location_lower = location_name.lower().strip()

        def get_admin_level(code: str) -> tuple:
            parts = code.split('.')
            if len(parts) == 1 and len(code) == 2:
                return ("province", "Provinsi")
            elif len(parts) == 2:
                return ("regency", "Kabupaten/Kota")
            elif len(parts) == 3:
                return ("district", "Kecamatan")
            elif len(parts) == 4:
                return ("village", "Kelurahan/Desa")
            return ("unknown", "Unknown")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue

                code = row[0].strip()
                name = row[1].strip()
                level_code, level_name = get_admin_level(code)

                if admin_level != "all":
                    if admin_level in ["province", "provinsi"] and level_code != "province":
                        continue
                    elif admin_level in ["regency", "kabkota"] and level_code != "regency":
                        continue
                    elif admin_level in ["district", "kecamatan"] and level_code != "district":
                        continue
                    elif admin_level in ["village", "desa"] and level_code != "village":
                        continue

                if location_lower in name.lower():
                    hierarchy = get_hierarchy(code, csv_path)

                    results.append({
                        "code": code,
                        "name": name,
                        "level": level_name,
                        "hierarchy": hierarchy,
                        "ready_for_weather_api": level_code == "village"
                    })

        results = results[:50]

        if not results:
            return json.dumps({
                "message": f"Tidak ditemukan lokasi dengan nama '{location_name}'",
                "suggestion": "Coba gunakan nama yang lebih spesifik atau cek ejaan",
                "searched_in": "base.csv dengan 91,220 wilayah",
                "results": []
            }, indent=2)

        return json.dumps({
            "query": location_name,
            "admin_level_filter": admin_level,
            "total_found": len(results),
            "results": results,
            "note": "Gunakan kode level 'Kelurahan/Desa' (4 segmen) untuk get_weather_forecast()"
        }, indent=2)

    except Exception as e:
        return f"Gagal mencari kode wilayah: {str(e)}"

def get_hierarchy(code: str, csv_path: str) -> str:
    """Helper function untuk mendapatkan hierarki lengkap dari kode wilayah"""
    parts = code.split('.')
    hierarchy_parts = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        csv_data = {row[0].strip(): row[1].strip() for row in reader if len(row) >= 2}

    if len(parts) >= 1:
        prov_code = parts[0]
        hierarchy_parts.append(csv_data.get(prov_code, prov_code))

    if len(parts) >= 2:
        reg_code = f"{parts[0]}.{parts[1]}"
        hierarchy_parts.append(csv_data.get(reg_code, reg_code))

    if len(parts) >= 3:
        dist_code = f"{parts[0]}.{parts[1]}.{parts[2]}"
        hierarchy_parts.append(csv_data.get(dist_code, dist_code))

    if len(parts) >= 4:
        vill_code = code
        hierarchy_parts.append(csv_data.get(vill_code, vill_code))

    return " > ".join(hierarchy_parts)

@mcp.tool()
async def get_villages_in_district(district_code: str) -> str:
    """
    Mendapatkan daftar semua kelurahan/desa dalam kecamatan tertentu dari database lokal.

    Args:
        district_code: Kode kecamatan (contoh: "33.02.07" untuk Sumpiuh)

    Returns:
        Daftar kelurahan/desa dengan kode lengkap yang siap digunakan untuk prakiraan cuaca.
    """
    try:
        csv_path = os.path.join(os.path.dirname(__file__), "base.csv")

        if not os.path.exists(csv_path):
            return json.dumps({"error": "File base.csv tidak ditemukan"}, indent=2)

        villages = []
        district_name = None

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue

                code = row[0].strip()
                name = row[1].strip()

                if code == district_code:
                    district_name = name

                if code.startswith(district_code + ".") and len(code.split('.')) == 4:
                    villages.append({
                        "code": code,
                        "name": name,
                        "ready_for_weather_api": True
                    })

        if not district_name:
            return json.dumps({
                "error": f"Kode kecamatan '{district_code}' tidak ditemukan",
                "suggestion": "Gunakan search_location_code() untuk menemukan kode yang tepat"
            }, indent=2)

        return json.dumps({
            "district_code": district_code,
            "district_name": district_name,
            "total_villages": len(villages),
            "villages": villages,
            "note": "Gunakan 'code' untuk parameter kode_wilayah di get_weather_forecast()"
        }, indent=2)

    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_weather_forecast(kode_wilayah: str = "31.71.01.1001") -> str:
    """
    Mengambil prakiraan cuaca berdasarkan kode wilayah (adm4).

    Args:
        kode_wilayah: Kode wilayah Indonesia level desa/kelurahan (adm4).
                     Default: 31.71.01.1001 (Gambir, Jakarta Pusat).

    Returns:
        Prakiraan cuaca 3 hari dengan interval 3 jam (±24 forecast total).
        Termasuk: suhu, kelembaban, kondisi cuaca, angin, tutupan awan, jarak pandang.

    Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)

    Note:
        Untuk mencari kode wilayah, gunakan search_location_code() terlebih dahulu
        Format kode: [kode_provinsi].[kode_kabkota].[kode_kecamatan].[kode_desa]
        Contoh: 31.71.01.1001 = DKI Jakarta > Jakarta Pusat > Gambir > Gambir
    """
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return "Gagal mengambil data cuaca. Cek kode wilayah."

            data = response.json()

            lokasi = data['lokasi']
            info_lokasi = {
                "provinsi": lokasi['provinsi'],
                "kabkota": lokasi['kotkab'],
                "kecamatan": lokasi['kecamatan'],
                "desa": lokasi['desa'],
                "koordinat": f"{lokasi['lat']}, {lokasi['lon']}",
                "timezone": lokasi['timezone']
            }

            forecasts_by_day = []

            if 'data' in data and len(data['data']) > 0:
                for day_data in data['data']:
                    daily_forecasts = []

                    if 'cuaca' in day_data and len(day_data['cuaca']) > 0:
                        for forecast_group in day_data['cuaca']:
                            if isinstance(forecast_group, list):
                                for forecast in forecast_group:
                                    daily_forecasts.append({
                                        "waktu_lokal": forecast['local_datetime'],
                                        "waktu_utc": forecast['utc_datetime'],
                                        "suhu": f"{forecast['t']}°C",
                                        "kelembaban": f"{forecast['hu']}%",
                                        "cuaca": forecast['weather_desc'],
                                        "cuaca_en": forecast.get('weather_desc_en', '-'),
                                        "kecepatan_angin": f"{forecast['ws']} km/j",
                                        "arah_angin": forecast['wd'],
                                        "tutupan_awan": f"{forecast.get('tcc', 0)}%",
                                        "jarak_pandang": forecast.get('vs_text', '-'),
                                        "icon": forecast.get('image', '-')
                                    })

                    if daily_forecasts:
                        forecasts_by_day.append({
                            "tanggal": daily_forecasts[0]['waktu_lokal'].split()[0],
                            "jumlah_forecast": len(daily_forecasts),
                            "forecasts": daily_forecasts
                        })

            result = {
                "lokasi": info_lokasi,
                "total_hari": len(forecasts_by_day),
                "total_forecast": sum(day['jumlah_forecast'] for day in forecasts_by_day),
                "prakiraan": forecasts_by_day,
                "catatan": "Data prakiraan 3 hari dengan interval 3 jam (8 forecast per hari)",
                "sumber": BMKG_ATTRIBUTION
            }

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return f"Error: {str(e)}"

@mcp.tool()
async def get_weather_alerts(language: str = "id") -> str:
    """
    Mengambil peringatan dini cuaca ekstrem (hujan lebat/petir) yang sedang aktif di Indonesia.
    Data berbasis Common Alerting Protocol (CAP) hingga level kecamatan.

    Args:
        language: Bahasa output, "id" untuk Indonesia atau "en" untuk English (default: "id")

    Returns:
        Daftar peringatan dini cuaca aktif dengan informasi provinsi terdampak,
        waktu publikasi, deskripsi wilayah, dan tautan detail CAP.
    """
    if language not in ["id", "en"]:
        language = "id"

    url = f"https://www.bmkg.go.id/alerts/nowcast/{language}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = xmltodict.parse(response.content)

            alerts = []
            channel = data.get('rss', {}).get('channel', {})

            metadata = {
                "last_build_date": channel.get('lastBuildDate', '-'),
                "title": channel.get('title', 'BMKG Weather Alerts'),
                "language": language
            }

            items = channel.get('item', [])

            if isinstance(items, dict):
                items = [items]

            for item in items:
                alert = {
                    "title": item.get('title', '-'),
                    "link": item.get('link', '-'),  # Tautan detail CAP provinsi
                    "description": item.get('description', '-'),
                    "author": item.get('author', '-'),  # Pembuat rilis
                    "pub_date": item.get('pubDate', '-')  # Waktu publikasi lokal (RFC 1123)
                }
                alerts.append(alert)

            result = {
                "metadata": metadata,
                "total_alerts": len(alerts),
                "alerts": alerts
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Gagal mengambil peringatan dini: {str(e)}"

@mcp.tool()
async def get_weather_alert_detail(cap_code: str, language: str = "id") -> str:
    """
    Mengambil detail peringatan dini cuaca untuk provinsi tertentu berdasarkan CAP code.
    Mengembalikan informasi detail wilayah kecamatan terdampak.

    Args:
        cap_code: Kode detail CAP (contoh: "20231125120000_BMKG001")
        language: Bahasa output, "id" untuk Indonesia atau "en" untuk English (default: "id")

    Returns:
        Detail CAP meliputi: event, effective, expires, senderName, headline,
        description, web (infografik), dan area polygon wilayah terdampak.
    """
    if language not in ["id", "en"]:
        language = "id"

    url = f"https://www.bmkg.go.id/alerts/nowcast/{language}/{cap_code}_alert.xml"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = xmltodict.parse(response.content)

            alert = data.get('alert', {})
            info = alert.get('info', {})

            if isinstance(info, list):
                info = info[0]  # Ambil info pertama

            result = {
                "identifier": alert.get('identifier', '-'),
                "sender": alert.get('sender', '-'),
                "sent": alert.get('sent', '-'),
                "status": alert.get('status', '-'),
                "msg_type": alert.get('msgType', '-'),
                "event": info.get('event', '-'),
                "effective": info.get('effective', '-'),
                "expires": info.get('expires', '-'),
                "sender_name": info.get('senderName', '-'),
                "headline": info.get('headline', '-'),
                "description": info.get('description', '-'),
                "web": info.get('web', '-'),  # Tautan infografik
                "areas": []
            }

            areas = info.get('area', [])
            if isinstance(areas, dict):
                areas = [areas]

            for area in areas:
                area_info = {
                    "area_desc": area.get('areaDesc', '-'),
                    "polygon": area.get('polygon', '-')  # Polygon wilayah terdampak
                }
                result["areas"].append(area_info)

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Gagal mengambil detail CAP: {str(e)}"

@mcp.tool()
async def search_weather_alerts_by_kecamatan(kecamatan: str, language: str = "id") -> str:
    """
    Mencari peringatan dini cuaca yang aktif untuk kecamatan tertentu.
    Tool ini akan mencari di seluruh peringatan aktif dan mengembalikan yang relevan dengan kecamatan.

    Args:
        kecamatan: Nama kecamatan yang ingin dicari (contoh: "Kebayoran Baru", "Bogor Barat")
        language: Bahasa output, "id" untuk Indonesia atau "en" untuk English (default: "id")

    Returns:
        Daftar peringatan dini cuaca yang mempengaruhi kecamatan tersebut,
        termasuk detail waktu berlaku, jenis kejadian, dan wilayah terdampak.
    """
    if language not in ["id", "en"]:
        language = "id"

    url_rss = f"https://www.bmkg.go.id/alerts/nowcast/{language}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_rss)
            data = xmltodict.parse(response.content)

            channel = data.get('rss', {}).get('channel', {})
            items = channel.get('item', [])

            if isinstance(items, dict):
                items = [items]

            if not items:
                return json.dumps({"message": "Tidak ada peringatan aktif saat ini", "alerts": []}, indent=2)

            matching_alerts = []

            for item in items:
                link = item.get('link', '')

                if '_alert.xml' in link:
                    cap_code = link.split('/')[-1].replace('_alert.xml', '')

                    try:
                        cap_url = f"https://www.bmkg.go.id/alerts/nowcast/{language}/{cap_code}_alert.xml"
                        cap_response = await client.get(cap_url)
                        cap_data = xmltodict.parse(cap_response.content)

                        alert_detail = cap_data.get('alert', {})
                        info = alert_detail.get('info', {})

                        if isinstance(info, list):
                            info = info[0]

                        areas = info.get('area', [])
                        if isinstance(areas, dict):
                            areas = [areas]

                        affected_areas = []
                        kecamatan_found = False

                        for area in areas:
                            area_desc = area.get('areaDesc', '')

                            if kecamatan.lower() in area_desc.lower():
                                kecamatan_found = True
                                affected_areas.append({
                                    "area_desc": area_desc,
                                    "polygon": area.get('polygon', '-')
                                })

                        if kecamatan_found:
                            matching_alerts.append({
                                "headline": info.get('headline', '-'),
                                "event": info.get('event', '-'),
                                "effective": info.get('effective', '-'),
                                "expires": info.get('expires', '-'),
                                "severity": info.get('severity', '-'),
                                "certainty": info.get('certainty', '-'),
                                "urgency": info.get('urgency', '-'),
                                "description": info.get('description', '-'),
                                "web": info.get('web', '-'),
                                "affected_areas": affected_areas,
                                "cap_code": cap_code
                            })

                    except Exception:
                        continue

            result = {
                "kecamatan_searched": kecamatan,
                "total_matching_alerts": len(matching_alerts),
                "alerts": matching_alerts
            }

            if len(matching_alerts) == 0:
                result["message"] = f"Tidak ada peringatan aktif untuk kecamatan '{kecamatan}'"

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Gagal mencari peringatan untuk kecamatan: {str(e)}"

if __name__ == "__main__":
    mcp.run()