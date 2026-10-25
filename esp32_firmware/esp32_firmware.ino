/**
 * SiteGuard AI-Based Construction Safety Monitoring System
 * Firmware for AI-Thinker ESP32-CAM (OV2640)
 *
 * This sketch captures JPEG frames and streams them via HTTP POST to the
 * SiteGuard FastAPI backend running on your laptop.
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ============================================================================
// 1. NETWORK & SERVER CONFIGURATION
// ============================================================================

// Replace with your 2.4 GHz Wi-Fi credentials (or mobile hotspot)
const char* WIFI_SSID     = "Basweshvar Bhavan_A2";
const char* WIFI_PASSWORD = "Net@8055";

// Your laptop's LAN IP address running SiteGuard
// (Auto-detected IP: 192.168.0.101, port: 8000)
const char* SERVER_FRAME_URL     = "http://192.168.0.101:8000/api/camera/frame";
const char* SERVER_HEARTBEAT_URL = "http://192.168.0.101:8000/api/camera/heartbeat";

// Camera identification metadata
const char* CAMERA_ID       = "CAM-01";
const char* CAMERA_NAME     = "ESP32-CAM Node 1";
const char* CAMERA_LOCATION = "Zone A Entrance";

// Streaming pace: 200 ms = ~5 FPS (optimal for stability and YOLO inference)
const unsigned long FRAME_INTERVAL_MS     = 200;
const unsigned long HEARTBEAT_INTERVAL_MS = 10000; // Heartbeat every 10 seconds

// ----------------------------------------------------------------------------
// Camera Tuning Parameters (Adjust zoom / angle, orientation, and lighting)
// ----------------------------------------------------------------------------
// Resolution & Field of View (FOV):
// - FRAMESIZE_VGA  (640x480): Full wide angle FOV (eliminates 2x zoomed-in crop)
// - FRAMESIZE_HVGA (480x320): Medium FOV
// - FRAMESIZE_QVGA (320x240): Faster FPS, but crops center window (2x zoomed in)
#define CAMERA_TARGET_FRAMESIZE    FRAMESIZE_VGA

// Orientation adjustments:
#define CAMERA_VFLIP               0  // 0: Normal, 1: Flip vertically (if mounted upside down)
#define CAMERA_HMIRROR             0  // 0: Normal, 1: Horizontal mirror reflection

// Exposure and Color tuning:
#define CAMERA_BRIGHTNESS          1  // -2 to +2 (higher = brighter)
#define CAMERA_CONTRAST            0  // -2 to +2
#define CAMERA_SATURATION          0  // -2 to +2 (-2 = grayscale, +2 = rich color)
#define CAMERA_SPECIAL_EFFECT      0  // 0: None, 1: Negative, 2: Grayscale, 3: Red tint, etc.
#define CAMERA_AUTO_WHITE_BAL      1  // 1: Auto White Balance enabled, 0: Disabled
#define CAMERA_WHITE_BAL_MODE      0  // 0: Auto, 1: Sunny, 2: Cloudy, 3: Office, 4: Home
#define CAMERA_AUTO_EXPOSURE       1  // 1: Auto Exposure enabled, 0: Disabled
#define CAMERA_AE_LEVEL            0  // -2 to +2 (exposure compensation)
#define CAMERA_LENS_CORRECTION     1  // 1: Compensate for lens vignetting (brightens edges)

// ============================================================================
// 2. AI-THINKER ESP32-CAM PIN MAPPINGS
// ============================================================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Onboard flash LED (GPIO 4) - optional indicator
#define FLASH_LED_PIN      4

// ============================================================================
// 3. GLOBAL STATE
// ============================================================================
WiFiClient wifiClient;
HTTPClient httpClient;

bool cameraInitialized = false;
unsigned long lastHeartbeatTime = 0;
unsigned long frameCount = 0;
unsigned long fpsTimer = 0;
float measuredFps = 0.0;

// ============================================================================
// 4. CAMERA INITIALIZATION
// ============================================================================
bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    // Use target frame size if PSRAM is detected, QVGA otherwise
    if (psramFound()) {
        config.frame_size   = CAMERA_TARGET_FRAMESIZE;
        config.jpeg_quality = 12;             // 10-63 (lower = higher quality)
        config.fb_count     = 2;              // Double buffering
        config.fb_location  = CAMERA_FB_IN_PSRAM;
        Serial.println("[ESP32-CAM] PSRAM detected: Enabling double-buffered wide-angle capture.");
    } else {
        config.frame_size   = FRAMESIZE_QVGA; // 320x240
        config.jpeg_quality = 14;
        config.fb_count     = 1;
        config.fb_location  = CAMERA_FB_IN_DRAM;
        Serial.println("[ESP32-CAM] No PSRAM: Falling back to QVGA.");
    }

    config.grab_mode = CAMERA_GRAB_LATEST;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[ESP32-CAM] Native JPEG init failed with 0x%x. Retrying with RGB565 fallback...\n", err);
        esp_camera_deinit();
        delay(100);
        config.pixel_format = PIXFORMAT_RGB565;
        config.frame_size   = psramFound() ? CAMERA_TARGET_FRAMESIZE : FRAMESIZE_QVGA;
        config.fb_count     = 1;
        config.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
        err = esp_camera_init(&config);
        if (err != ESP_OK) {
            Serial.printf("[ESP32-CAM] Fallback init also failed with error 0x%x\n", err);
            return false;
        }
        Serial.println("[ESP32-CAM] Initialized in RGB565 mode with software JPEG compression!");
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s) {
        Serial.printf("[ESP32-CAM] Sensor PID: 0x%04X, MID: 0x%04X\n", s->id.PID, s->id.MIDH);
        if (s->set_vflip) s->set_vflip(s, CAMERA_VFLIP);
        if (s->set_hmirror) s->set_hmirror(s, CAMERA_HMIRROR);
        if (s->set_brightness) s->set_brightness(s, CAMERA_BRIGHTNESS);
        if (s->set_contrast) s->set_contrast(s, CAMERA_CONTRAST);
        if (s->set_saturation) s->set_saturation(s, CAMERA_SATURATION);
        if (s->set_special_effect) s->set_special_effect(s, CAMERA_SPECIAL_EFFECT);
        if (s->set_whitebal) s->set_whitebal(s, CAMERA_AUTO_WHITE_BAL);
        if (s->set_awb_gain) s->set_awb_gain(s, 1);
        if (s->set_wb_mode) s->set_wb_mode(s, CAMERA_WHITE_BAL_MODE);
        if (s->set_exposure_ctrl) s->set_exposure_ctrl(s, CAMERA_AUTO_EXPOSURE);
        if (s->set_ae_level) s->set_ae_level(s, CAMERA_AE_LEVEL);
        if (s->set_lenc) s->set_lenc(s, CAMERA_LENS_CORRECTION);
        if (s->set_dcw) s->set_dcw(s, 1); // Downsize enable: uses full active pixel array (widest FOV)
        Serial.println("[ESP32-CAM] Sensor orientation and image controls applied.");
    }

    Serial.println("[ESP32-CAM] Camera sensor ready!");
    return true;
}

// ============================================================================
// 5. WI-FI CONNECTION
// ============================================================================
void connectToWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.printf("[WiFi] Connecting to %s ", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - startAttempt) < 15000) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Connected successfully!");
        Serial.print("[WiFi] ESP32 IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("[WiFi] RSSI Signal: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
    } else {
        Serial.println("\n[WiFi] Connection timeout. Retrying in main loop...");
    }
}

// ============================================================================
// 6. FRAME UPLOAD TO SITEGUARD SERVER
// ============================================================================
void captureAndSendFrame() {
    if (WiFi.status() != WL_CONNECTED) return;

    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("[CAM] Frame capture failed!");
        return;
    }

    uint8_t* jpg_buf = NULL;
    size_t jpg_len = 0;
    bool needs_free = false;

    if (fb->format != PIXFORMAT_JPEG) {
        bool converted = frame2jpg(fb, 50, &jpg_buf, &jpg_len);
        if (!converted) {
            Serial.println("[CAM] Software JPEG conversion failed!");
            esp_camera_fb_return(fb);
            return;
        }
        needs_free = true;
    } else {
        jpg_buf = fb->buf;
        jpg_len = fb->len;
    }

    httpClient.begin(wifiClient, SERVER_FRAME_URL);
    httpClient.addHeader("Content-Type", "image/jpeg");
    httpClient.addHeader("X-Camera-ID", CAMERA_ID);
    httpClient.addHeader("X-Camera-Name", CAMERA_NAME);
    httpClient.addHeader("X-Camera-Location", CAMERA_LOCATION);
    httpClient.setConnectTimeout(3000);
    httpClient.setTimeout(4000);

    int httpCode = httpClient.POST(jpg_buf, jpg_len);

    if (httpCode == HTTP_CODE_OK || httpCode == 201) {
        frameCount++;
    } else if (httpCode > 0) {
        Serial.printf("[HTTP] Server returned status code: %d\n", httpCode);
    } else {
        Serial.printf("[HTTP] POST failed, error: %s\n", httpClient.errorToString(httpCode).c_str());
    }

    httpClient.end();
    if (needs_free && jpg_buf) {
        free(jpg_buf);
    }
    esp_camera_fb_return(fb);
}

// ============================================================================
// 7. TELEMETRY & HEARTBEAT
// ============================================================================
void sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) return;

    // Calculate approximate FPS over the window
    unsigned long now = millis();
    float seconds = (now - fpsTimer) / 1000.0;
    if (seconds > 0) {
        measuredFps = frameCount / seconds;
    }
    frameCount = 0;
    fpsTimer = now;

    // Prepare JSON payload
    char jsonBuffer[256];
    snprintf(jsonBuffer, sizeof(jsonBuffer),
        "{\"device_id\":\"%s\",\"rssi\":%d,\"free_heap\":%u,\"uptime\":%lu,\"fps\":%.1f,\"firmware_version\":\"1.0.0\"}",
        CAMERA_ID,
        WiFi.RSSI(),
        ESP.getFreeHeap(),
        now / 1000,
        measuredFps
    );

    httpClient.begin(wifiClient, SERVER_HEARTBEAT_URL);
    httpClient.addHeader("Content-Type", "application/json");
    httpClient.setConnectTimeout(2000);
    httpClient.setTimeout(3000);

    httpClient.POST((uint8_t*)jsonBuffer, strlen(jsonBuffer));
    httpClient.end();
}

// ============================================================================
// 8. SETUP & MAIN LOOP
// ============================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==================================================");
    Serial.println("  SiteGuard Construction Safety - ESP32-CAM Node  ");
    Serial.println("==================================================");

    // Flash LED off
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW);

    connectToWiFi();
    cameraInitialized = initCamera();

    httpClient.setReuse(true);
    fpsTimer = millis();
}

void loop() {
    // If Wi-Fi is lost, reconnect
    if (WiFi.status() != WL_CONNECTED) {
        connectToWiFi();
        delay(1000);
        return;
    }

    // Lazy retry camera init if hardware had delayed power-up
    if (!cameraInitialized) {
        Serial.println("[ESP32-CAM] Retrying camera init...");
        cameraInitialized = initCamera();
        if (!cameraInitialized) {
            delay(2000);
            return;
        }
    }

    // Capture & upload frame
    unsigned long startMs = millis();
    captureAndSendFrame();

    // Periodic heartbeat
    if (millis() - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
        sendHeartbeat();
        lastHeartbeatTime = millis();
    }

    // Rate pacing (~5 FPS)
    unsigned long elapsed = millis() - startMs;
    if (elapsed < FRAME_INTERVAL_MS) {
        delay(FRAME_INTERVAL_MS - elapsed);
    }
}
