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
unsigned long lastSensorPostAt = 0;
deskdeck::DisplayState currentDisplayState;
bool hasCurrentDisplayState = false;
bool flashBacklightOn = true;
unsigned long lastFlashAt = 0;
int scrollFrame = 0;
unsigned long lastScrollAt = 0;

bool sameColor(deskdeck::RgbColor left, deskdeck::RgbColor right) {
  return left.red == right.red && left.green == right.green && left.blue == right.blue;
}

bool sameDisplayState(const deskdeck::DisplayState& left, const deskdeck::DisplayState& right) {
  return left.line1 == right.line1 &&
         left.line2 == right.line2 &&
         sameColor(left.backlight, right.backlight) &&
         left.flashBacklight == right.flashBacklight &&
         left.scrollText == right.scrollText;
}

String scrollWindow(const String& line, int frame) {
  const int lineLength = line.length();
  if (lineLength <= deskdeck::config::LCD_COLUMNS) {
    return line;
  }

  const int maxOffset = lineLength - deskdeck::config::LCD_COLUMNS;
  const int cycleFrames =
      deskdeck::config::SCROLL_PAUSE_FRAMES +
      maxOffset + 1 +
      deskdeck::config::SCROLL_PAUSE_FRAMES;
  int position = frame % cycleFrames;
  if (position < deskdeck::config::SCROLL_PAUSE_FRAMES) {
    return line.substring(0, deskdeck::config::LCD_COLUMNS);
  }

  position -= deskdeck::config::SCROLL_PAUSE_FRAMES;
  const int offset = position <= maxOffset ? position : maxOffset;
  return line.substring(offset, offset + deskdeck::config::LCD_COLUMNS);
}

void renderCurrentDisplayState() {
  String line1 = currentDisplayState.line1;
  String line2 = currentDisplayState.line2;
  if (currentDisplayState.scrollText) {
    line1 = scrollWindow(currentDisplayState.line1, scrollFrame);
    line2 = scrollWindow(currentDisplayState.line2, scrollFrame);
  }

  deskdeck::showMessage(
      line1,
      line2,
      currentDisplayState.backlight.red,
      currentDisplayState.backlight.green,
      currentDisplayState.backlight.blue);
}

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
  hasCurrentDisplayState = false;
}

void showStatus(const deskdeck::DisplayState& state) {
  if (hasCurrentDisplayState && sameDisplayState(currentDisplayState, state)) {
    return;
  }

  currentDisplayState = state;
  hasCurrentDisplayState = true;
  flashBacklightOn = true;
  lastFlashAt = millis();
  scrollFrame = 0;
  lastScrollAt = millis();
  renderCurrentDisplayState();
}

void updateFlashEffect() {
  if (!hasCurrentDisplayState || !currentDisplayState.flashBacklight) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastFlashAt < deskdeck::config::FLASH_INTERVAL_MS) {
    return;
  }

  lastFlashAt = now;
  flashBacklightOn = !flashBacklightOn;
  if (flashBacklightOn) {
    deskdeck::setBacklight(
        currentDisplayState.backlight.red,
        currentDisplayState.backlight.green,
        currentDisplayState.backlight.blue);
    return;
  }

  deskdeck::setBacklight(0, 0, 0);
}

void updateScrollEffect() {
  if (!hasCurrentDisplayState || !currentDisplayState.scrollText) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastScrollAt < deskdeck::config::SCROLL_INTERVAL_MS) {
    return;
  }

  lastScrollAt = now;
  scrollFrame++;
  renderCurrentDisplayState();
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

float readInsideTemperatureF() {
  const float temperatureC = temperatureRead();
  return (temperatureC * 9.0F / 5.0F) + 32.0F;
}

void postInsideTemperature() {
  const float temperatureF = readInsideTemperatureF();
  if (statusClient.postInsideTemperature(temperatureF)) {
    Serial.print("Inside temperature posted: ");
    Serial.print(temperatureF);
    Serial.println(" F");
    return;
  }

  Serial.println("Inside temperature post failed.");
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
  lastSensorPostAt = millis() - deskdeck::config::SENSOR_POST_INTERVAL_MS;
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

  if (now - lastSensorPostAt >= deskdeck::config::SENSOR_POST_INTERVAL_MS) {
    lastSensorPostAt = now;
    postInsideTemperature();
  }

  updateFlashEffect();
  updateScrollEffect();
  delay(deskdeck::config::LOOP_IDLE_DELAY_MS);
}
