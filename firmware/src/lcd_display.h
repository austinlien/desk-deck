#pragma once

#include <Arduino.h>

namespace deskdeck {
void initializeDisplay();
void setBacklight(uint8_t red, uint8_t green, uint8_t blue);
void showMessage(const char* line1, const char* line2, uint8_t red, uint8_t green, uint8_t blue);
void showMessage(const String& line1, const String& line2, uint8_t red, uint8_t green, uint8_t blue);
}
