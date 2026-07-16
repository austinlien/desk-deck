#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "i2c_scan.h"
#include "lcd_display.h"

namespace {
void showBringUpMessage() {
  deskdeck::initializeDisplay();
  deskdeck::showMessage(
      deskdeck::config::BRING_UP_LINE_1,
      deskdeck::config::BRING_UP_LINE_2,
      deskdeck::config::BRING_UP_BACKLIGHT_R,
      deskdeck::config::BRING_UP_BACKLIGHT_G,
      deskdeck::config::BRING_UP_BACKLIGHT_B);
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
}

void loop() {
  delay(deskdeck::config::LOOP_IDLE_DELAY_MS);
}
