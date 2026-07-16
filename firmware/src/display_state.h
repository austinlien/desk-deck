#pragma once

#include <Arduino.h>

namespace deskdeck {
struct RgbColor {
  uint8_t red;
  uint8_t green;
  uint8_t blue;
};

struct DisplayState {
  String line1;
  String line2;
  RgbColor backlight;
  bool flashBacklight;
  bool scrollText;
};

RgbColor colorFromName(const String& colorName);
}  // namespace deskdeck
