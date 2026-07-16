#include <Arduino.h>
#include <Wire.h>
#include "DFRobot_RGBLCD1602.h"

namespace {
constexpr uint8_t I2C_SDA_PIN = 10;
constexpr uint8_t I2C_SCL_PIN = 8;
constexpr uint8_t LCD_COLUMNS = 16;
constexpr uint8_t LCD_ROWS = 2;
constexpr uint8_t LCD_RGB_ADDRESS = 0x2D;
constexpr unsigned long LCD_POWER_SETTLE_MS = 1500;

DFRobot_RGBLCD1602 lcd(LCD_RGB_ADDRESS, LCD_COLUMNS, LCD_ROWS);

void scanI2cBus() {
  Serial.println("Scanning I2C bus...");

  uint8_t foundCount = 0;
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    const uint8_t error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("  Found I2C device at 0x");
      if (address < 16) {
        Serial.print('0');
      }
      Serial.println(address, HEX);
      foundCount++;
    } else if (error == 4) {
      Serial.print("  Unknown I2C error at 0x");
      if (address < 16) {
        Serial.print('0');
      }
      Serial.println(address, HEX);
    }
  }

  Serial.print("I2C scan complete. Devices found: ");
  Serial.println(foundCount);
}

void showBringUpMessage() {
  lcd.init();
  delay(100);
  lcd.setRGB(255, 255, 255);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("DESK DECK");
  lcd.setCursor(0, 1);
  lcd.print("HARDWARE OK");
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(LCD_POWER_SETTLE_MS);

  Serial.println();
  Serial.println("Desk Deck display bring-up");
  Serial.print("I2C SDA pin: GPIO");
  Serial.println(I2C_SDA_PIN);
  Serial.print("I2C SCL pin: GPIO");
  Serial.println(I2C_SCL_PIN);
  Serial.print("LCD RGB address: 0x");
  Serial.println(LCD_RGB_ADDRESS, HEX);

  Wire.setPins(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.begin();

  showBringUpMessage();
  delay(250);
  showBringUpMessage();
  delay(250);
  showBringUpMessage();
  scanI2cBus();

  Serial.println("LCD message written.");
}

void loop() {
  delay(1000);
}
