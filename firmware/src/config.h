#pragma once

#include <Arduino.h>

namespace deskdeck::config {
constexpr uint8_t I2C_SDA_PIN = 10;
constexpr uint8_t I2C_SCL_PIN = 8;

constexpr uint8_t LCD_COLUMNS = 16;
constexpr uint8_t LCD_ROWS = 2;
constexpr uint8_t LCD_RGB_ADDRESS = 0x2D;

constexpr unsigned long SERIAL_BAUD = 115200;
constexpr unsigned long LCD_POWER_SETTLE_MS = 1500;
constexpr unsigned long LCD_RETRY_DELAY_MS = 250;
constexpr unsigned long LOOP_IDLE_DELAY_MS = 1000;
constexpr unsigned long WIFI_CONNECT_TIMEOUT_MS = 15000;
constexpr unsigned long WIFI_RETRY_DELAY_MS = 5000;
constexpr unsigned long STATUS_POLL_INTERVAL_MS = 5000;
constexpr unsigned long HTTP_TIMEOUT_MS = 3000;

constexpr const char* BRING_UP_LINE_1 = "DESK DECK";
constexpr const char* BRING_UP_LINE_2 = "HARDWARE OK";

constexpr uint8_t BRING_UP_BACKLIGHT_R = 255;
constexpr uint8_t BRING_UP_BACKLIGHT_G = 255;
constexpr uint8_t BRING_UP_BACKLIGHT_B = 255;
}  // namespace deskdeck::config
