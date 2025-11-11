#include "esp_camera.h"
#include <WiFi.h>
#include "esp_timer.h"
#include "esp_http_server.h" // Diperlukan untuk httpd_req_t
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ===================================
// 1. KREDENSIAL WIFI
// ===================================
const char *ssid = "Mama adelia"; // Ganti dengan SSID WiFi Anda
const char *password = "uu311009"; // Ganti dengan Password WiFi Anda

// ===================================
// 2. KONFIGURASI PIN (AI-THINKER OV2640)
// ===================================
#define CAMERA_MODEL_AI_THINKER 

#if defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

#define LED_GPIO_NUM 4
#endif

// ===================================
// 3. VARIABEL & DEKLARASI FUNGSI SERVER
// ===================================
httpd_handle_t camera_httpd = NULL; 

void startCameraServer();
void setupLedFlash();

// Deklarasi fungsi-fungsi server HTTP
static esp_err_t capture_handler(httpd_req_t *req);
static esp_err_t stream_handler(httpd_req_t *req);
static esp_err_t index_handler(httpd_req_t *req);

// **********************************
// KODE HTML UNTUK TAMPILAN WEB
// **********************************
const char* index_html = R"rawliteral(
<html>
<head>
    <title>ESP32-CAM Web Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; text-align: center; margin: 0; padding: 0; background-color: #f4f4f4; }
        .content { margin: auto; padding: 20px; background-color: white; border-radius: 8px; max-width: 600px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        img { max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ccc; display:block; margin: 10px auto; }
        .buttons a { text-decoration: none; padding: 10px 20px; margin: 5px; border-radius: 5px; background-color: #007bff; color: white; display: inline-block; transition: background-color 0.3s; }
        .buttons a:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="content">
        <h1>ESP32-CAM Stream</h1>
        <img id="cam-stream" src="/stream"> 
        <div class="buttons">
            <a href="/capture">Ambil Foto (Statis)</a>
        </div>
        <p>Akses ke /capture untuk foto statis, atau lihat streaming di atas.</p>
    </div>
</body>
</html>
)rawliteral";
// **********************************

// ===================================
// 4. SETUP
// ===================================
void setup() {
    // Matikan Brownout Detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 

    Serial.begin(115200);
    Serial.setDebugOutput(true);
    Serial.println();

    // 4.1 Inisialisasi Kamera
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA; // Resolusi Rendah (320x240) untuk Stabilitas
    config.jpeg_quality = 10;
    config.fb_count = 1;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x. Harap reset.\n", err);
        return;
    }

    sensor_t *s = esp_camera_sensor_get();
    if (s->id.PID == OV2640_PID) {
        s->set_vflip(s, 1); // Membalik gambar vertikal (sesuaikan jika perlu)
    }

    // 4.2 Koneksi Wi-Fi
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    Serial.print("Menghubungkan ke Wi-Fi.");
    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        timeout++;
        if (timeout > 40) { // 20 detik timeout
            Serial.println("\n\n!! Gagal terhubung ke Wi-Fi. Cek SSID/Password. !!");
            return;
        }
    }
    
    // Log Koneksi Berhasil
    Serial.println("\n\n✅ Terhubung ke Wi-Fi!");
    Serial.print("Alamat IP Lokal: ");
    Serial.println(WiFi.localIP());

    // 4.3 Mulai Web Server
    startCameraServer();

    // Log Alamat yang Bisa Diakses
    Serial.println("\n=============================================");
    Serial.print("SERVER KAMERA AKTIF! Akses melalui: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/");
    Serial.println("=============================================");
}

// ===================================
// 5. LOOP
// ===================================
void loop() {
    delay(10); 
}

// ===================================
// 6. IMPLEMENTASI FUNGSI SERVER HTTP
// ===================================

// Fungsi untuk menangkap satu gambar statis (/capture)
static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;

    fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera capture failed");
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    httpd_resp_send(req, (const char *)fb->buf, fb->len);

    esp_camera_fb_return(fb);
    return ESP_OK;
}

// Fungsi untuk menangani streaming video (Motion JPEG) (/stream)
static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t *_jpg_buf = NULL;
    char *part_buf[64];
    
    // Set Header Multi-Part
    res = httpd_resp_set_type(req, "multipart/x-mixed-replace;boundary=123456789000000000000987654321");

    // HEADER TAMBAHAN UNTUK NONAKTIFKAN CACHE DI BROWSER (Perbaikan)
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "Cache-Control", "no-cache, no-store, must-revalidate");
    httpd_resp_set_hdr(req, "Pragma", "no-cache");
    httpd_resp_set_hdr(req, "Expires", "-1");
    
    while (res == ESP_OK) { // Loop akan berjalan terus selama koneksi HTTP OK
        
        // Dapatkan frame dari kamera
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed (stream)");
            delay(100);
            continue; // Lanjutkan loop untuk mencoba lagi
        } 
        
        // Persiapan data frame
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
        
        // Bangun dan kirim header multi-part
        size_t hlen = snprintf((char *)part_buf, 64, 
                                 "--123456789000000000000987654321\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", 
                                 _jpg_buf_len);
        
        // Kirim header, data JPG, dan pemisah baris
        if (httpd_resp_send_chunk(req, (const char *)part_buf, hlen) != ESP_OK) {
            res = ESP_FAIL; break;
        }
        if (httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len) != ESP_OK) {
            res = ESP_FAIL; break;
        }
        if (httpd_resp_send_chunk(req, "\r\n", 2) != ESP_OK) {
            res = ESP_FAIL; break;
        }

        // Kembalikan buffer
        esp_camera_fb_return(fb);
        fb = NULL;
    }
    
    // Pastikan buffer dikembalikan jika loop berakhir secara tidak terduga
    if (fb) esp_camera_fb_return(fb); 
    return res;
}

// Fungsi untuk menangani halaman utama (HTML) (/)
static esp_err_t index_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, index_html, HTTPD_RESP_USE_STRLEN);
}


// Fungsi untuk memulai server HTTP
void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;

    httpd_uri_t index_uri = {
        .uri = "/",
        .method = HTTP_GET,
        .handler = index_handler,
        .user_ctx = NULL
    };

    httpd_uri_t capture_uri = {
        .uri = "/capture",
        .method = HTTP_GET,
        .handler = capture_handler,
        .user_ctx = NULL
    };

    httpd_uri_t stream_uri = {
        .uri = "/stream",
        .method = HTTP_GET,
        .handler = stream_handler,
        .user_ctx = NULL
    };

    Serial.printf("Starting web server on port: '%d'\n", config.server_port);
    
    // Mendaftarkan SEMUA handler di satu server HTTP (Port 80)
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &capture_uri);
        httpd_register_uri_handler(camera_httpd, &stream_uri);
    }
}

void setupLedFlash() {
    // Implementasi opsional untuk LED Flash
}