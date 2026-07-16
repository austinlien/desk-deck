#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "display_state.h"
#include "i2c_scan.h"
#include "lcd_display.h"
#include "status_client.h"
#include "wifi_manager.h"

namespace {
deskdeck::WifiManager wifi;
deskdeck::StatusClient statusClient;
unsigned long lastStatusPollAt = 0;

void showBringUpMessage() {
  deskdeck::initializeDisplay();
  deskdeck::showMessage(
      deskdeck::config::BRING_UP_LINE_1,
      deskdeck::config::BRING_UP_LINE_2,
      deskdeck::config::BRING_UP_BACKLIGHT_R,
      deskdeck::config::BRING_UP_BACKLIGHT_G,
      deskdeck::config::BRING_UP_BACKLIGHT_B);
}

void showStatus(const char* line1, const char* line2, deskdeck::RgbColor color) {
  deskdeck::showMessage(line1, line2, color.red, color.green, color.blue);
}

void showStatus(const deskdeck::DisplayState& state) {
  deskdeck::showMessage(
      state.line1,
      state.line2,
      state.backlight.red,
      state.backlight.green,
      state.backlight.blue);
}

void connectWifiWithDisplay() {
  showStatus("WIFI", "CONNECTING", deskdeck::colorFromName("yellow"));
  Serial.print("Connecting to Wi-Fi");

  if (wifi.connect()) {
    Serial.print("Wi-Fi connected. IP: ");
    Serial.println(wifi.localIp());
    showStatus("WIFI", "CONNECTED", deskdeck::colorFromName("green"));
    delay(1500);
    return;
  }

  Serial.println("Wi-Fi connection failed.");
  showStatus("WIFI FAILED", "RETRYING", deskdeck::colorFromName("red"));
}

void pollStatusServer() {
  deskdeck::DisplayState state;
  if (statusClient.fetch(state)) {
    Serial.println("Status updated from server.");
    showStatus(state);
    return;
  }

  Serial.println("Status server unavailable.");
  showStatus("SERVER", "OFFLINE", deskdeck::colorFromName("yellow"));
}
}  // namespace

void setup() {
  Serial.begin(deskdeck::config::SERIAL_BAUD);
  delay(deskdeck::config::LCD_POWER_SETTLE_MS);

  Serial.println();
  Serial.println("Desk Deck display bring-up");
  Serial.print("I2C SDA pin: GPIO");
  Serial.println(deskdeck::config::I2C_SDA_PIN);
  Serial.print("I2C SCL pin: GPIO");
  Serial.println(deskdeck::config::I2C_SCL_PIN);
  Serial.print("LCD RGB address: 0x");
  Serial.println(deskdeck::config::LCD_RGB_ADDRESS, HEX);

  Wire.setPins(deskdeck::config::I2C_SDA_PIN, deskdeck::config::I2C_SCL_PIN);
  Wire.begin();

  showBringUpMessage();
  delay(deskdeck::config::LCD_RETRY_DELAY_MS);
  showBringUpMessage();
  delay(deskdeck::config::LCD_RETRY_DELAY_MS);
  showBringUpMessage();
  deskdeck::scanI2cBus();

  Serial.println("LCD message written.");
  connectWifiWithDisplay();
  lastStatusPollAt = millis() - deskdeck::config::STATUS_POLL_INTERVAL_MS;
}

void loop() {
  if (!wifi.isConnected()) {
    connectWifiWithDisplay();
    delay(deskdeck::config::WIFI_RETRY_DELAY_MS);
    return;
  }

  const unsigned long now = millis();
  if (now - lastStatusPollAt >= deskdeck::config::STATUS_POLL_INTERVAL_MS) {
    lastStatusPollAt = now;
    pollStatusServer();
  }

  delay(deskdeck::config::LOOP_IDLE_DELAY_MS);
}
