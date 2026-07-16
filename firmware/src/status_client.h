#pragma once

#include "display_state.h"

namespace deskdeck {
class StatusClient {
 public:
  bool fetch(DisplayState& state);
};
}  // namespace deskdeck
