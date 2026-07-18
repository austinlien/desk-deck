#include "display_state.h"

namespace deskdeck {
RgbColor colorFromName(const String& colorName) {
  if (colorName == "red") {
    return {255, 0, 0};
  }
  if (colorName == "yellow") {
    return {255, 180, 0};
  }
  if (colorName == "green") {
    return {0, 210, 12};
  }
  if (colorName == "blue") {
    return {0, 80, 255};
  }
  if (colorName == "purple") {
    return {180, 0, 255};
  }
  return {255, 255, 255};
}
}  // namespace deskdeck
