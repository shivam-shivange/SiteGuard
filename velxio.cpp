// URl:  https://velxio.dev/amirandalo/avnzado3/
// RUN BELOW CODE ON ABOVE URL LINK

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// =====================================================
// WiFi
// =====================================================

const char* WIFI_SSID = "Velxio-GUEST";
const char* WIFI_PASSWORD = "";

// PC LAN address running the FastAPI backend. Use ipconfig to update this
// value if the router assigns the PC a different address in the future.
const char* SERVER_URL =
    "http://192.168.0.102:8000/api/camera/frame";

const char* CAMERA_ID = "CAM-01";
const char* CAMERA_NAME = "ESP32-CAM 01";
const char* CAMERA_LOCATION = "Unassigned";

bool cameraReady = false;
unsigned long nextCameraInitAttempt = 0;


// =====================================================
// AI-THINKER ESP32-CAM PIN CONFIGURATION
// =====================================================

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


// =====================================================
// CAMERA SETUP
// =====================================================

bool setupCamera()
{
    camera_config_t config = {};

    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;

    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;

    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;

    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;

    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;

    config.xclk_freq_hz = 20000000;

    // JPEG output
    config.pixel_format = PIXFORMAT_JPEG;

    // Start with QVGA
    config.frame_size = FRAMESIZE_QVGA;

    // JPEG quality
    config.jpeg_quality = 12;

    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    // The uploader intentionally runs slowly. Discard stale camera frames
    // rather than allowing the producer to overflow its single frame buffer.
    config.grab_mode = CAMERA_GRAB_LATEST;

    esp_err_t result = esp_camera_init(&config);

    if (result != ESP_OK)
    {
        Serial.print("Camera initialization failed: 0x");
        Serial.println(result, HEX);
        return false;
    }

    Serial.println("Camera initialized successfully.");

    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor)
    {
        Serial.printf(
            "Camera sensor PID=0x%02X VER=0x%02X\n",
            sensor->id.PID,
            sensor->id.VER
        );
    }

    return true;
}


// =====================================================
// WIFI
// =====================================================

void connectWiFi()
{
    Serial.println();
    Serial.println("Connecting to WiFi...");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startedAt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startedAt < 20000)
    {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("WiFi connection timed out; will retry in loop.");
        return;
    }
    Serial.println("WiFi connected.");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
}


// =====================================================
// SEND IMAGE TO PC
// =====================================================

void sendFrameToServer()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("WiFi disconnected; reconnecting...");
        WiFi.reconnect();
        return;
    }

    camera_fb_t* frame = esp_camera_fb_get();

    if (!frame)
    {
        Serial.println("Failed to capture frame.");
        return;
    }

    Serial.print("Captured frame: ");
    Serial.print(frame->len);
    Serial.println(" bytes");


    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;

        http.begin(SERVER_URL);

        http.addHeader("Content-Type", "image/jpeg");
        http.addHeader("X-Camera-ID", CAMERA_ID);
        http.addHeader("X-Camera-Name", CAMERA_NAME);
        http.addHeader("X-Camera-Location", CAMERA_LOCATION);
        http.setConnectTimeout(5000);
        http.setTimeout(8000);

        int responseCode =
            http.POST(frame->buf, frame->len);

        Serial.print("Server response: ");
        Serial.println(responseCode);

        http.end();
    }


    esp_camera_fb_return(frame);
}


// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("=================================");
    Serial.println(" Construction Safety ESP32-CAM");
    Serial.println("=================================");


    // WiFi
    connectWiFi();


    Serial.println();
    Serial.println("System ready. Waiting for camera.");
    Serial.println("Velxio: click the Camera button in the canvas header");
    Serial.println("before or after starting the simulation.");
}


// =====================================================
// LOOP
// =====================================================

void loop()
{
    // Velxio attaches its virtual OV2640 only after its Camera control is
    // enabled. Retrying also makes real hardware recover from a late sensor
    // power-up without rebooting the entire device.
    if (!cameraReady)
    {
        if ((long)(millis() - nextCameraInitAttempt) < 0)
        {
            delay(100);
            return;
        }

        Serial.println("Initializing camera...");
        cameraReady = setupCamera();
        if (!cameraReady)
        {
            Serial.println("Camera unavailable. Retrying in 2 seconds.");
            nextCameraInitAttempt = millis() + 2000;
            delay(100);
            return;
        }
    }

    sendFrameToServer();

    // Don't hammer the server.
    // Start with 1 frame every second.
    delay(1000);
}
