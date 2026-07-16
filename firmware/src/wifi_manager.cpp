#include "wifi_manager.h"

#include <WiFi.h>

#include "config.h"
#include "secrets.h"

namespace deskdeck {
bool WifiManager::connect() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  const unsigned long startedAt = millis();
  while (WiFi.status() != WL_CONNECTED &&
         millis() - startedAt < config::WIFI_CONNECT_TIMEOUT_MS) {
    delay(250);
    Serial.print('.');
  }
  Serial.println();

  return WiFi.status() == WL_CONNECTED;
}

bool WifiManager::isConnected() const {
  return WiFi.status() == WL_CONNECTED;
}

String WifiManager::localIp() const {
  if (WiFi.status() != WL_CONNECTED) {
    return "";
  }
  return WiFi.localIP().toString();
}
}  // namespace deskdeck
