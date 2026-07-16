#pragma once

#include "display_state.h"

namespace deskdeck {
class StatusClient {
 public:
  bool fetch(DisplayState& state);
  bool postInsideTemperature(float temperatureF);
};
}  // namespace deskdeck
