#include "lcd_display.h"

#include "DFRobot_RGBLCD1602.h"
#include "config.h"

namespace {
DFRobot_RGBLCD1602 lcd(
    deskdeck::config::LCD_RGB_ADDRESS,
    deskdeck::config::LCD_COLUMNS,
    deskdeck::config::LCD_ROWS);
}

namespace deskdeck {
void initializeDisplay() {
  lcd.init();
  delay(100);
}

void showMessage(const char* line1, const char* line2, uint8_t red, uint8_t green, uint8_t blue) {
  lcd.setRGB(red, green, blue);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}
}  // namespace deskdeck
