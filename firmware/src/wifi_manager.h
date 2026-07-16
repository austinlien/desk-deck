#pragma once

#include <Arduino.h>

namespace deskdeck {
class WifiManager {
 public:
  bool connect();
  bool isConnected() const;
  String localIp() const;
};
}  // namespace deskdeck
