#include "status_client.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "config.h"
#include "secrets.h"

namespace {
String fitLine(const char* value) {
  String line = value == nullptr ? "" : String(value);
  line.trim();
  if (line.length() > deskdeck::config::LCD_COLUMNS) {
    line = line.substring(0, deskdeck::config::LCD_COLUMNS);
  }
  return line;
}
}  // namespace

namespace deskdeck {
bool StatusClient::fetch(DisplayState& state) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  HTTPClient http;
  http.setTimeout(config::HTTP_TIMEOUT_MS);

  if (!http.begin(STATUS_SERVER_URL)) {
    return false;
  }

  const int statusCode = http.GET();
  if (statusCode != HTTP_CODE_OK) {
    Serial.print("Status request failed. HTTP ");
    Serial.println(statusCode);
    http.end();
    return false;
  }

  const String body = http.getString();
  http.end();

  JsonDocument doc;
  const DeserializationError error = deserializeJson(doc, body);
  if (error) {
    Serial.print("Status JSON parse failed: ");
    Serial.println(error.c_str());
    return false;
  }

  state.line1 = fitLine(doc["line1"] | "");
  state.line2 = fitLine(doc["line2"] | "");
  state.backlight = colorFromName(String(doc["backlight"] | "white"));
  return state.line1.length() > 0 || state.line2.length() > 0;
}
}  // namespace deskdeck
