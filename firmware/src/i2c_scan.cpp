#include "i2c_scan.h"

#include <Arduino.h>
#include <Wire.h>

namespace deskdeck {
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
}  // namespace deskdeck
