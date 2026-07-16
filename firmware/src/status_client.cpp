#include "status_client.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "config.h"
#include "secrets.h"

namespace {
String trimmedLine(const char* value) {
  String line = value == nullptr ? "" : String(value);
  line.trim();
  return line;
}

String fitLine(const char* value) {
  String line = trimmedLine(value);
  if (line.length() > deskdeck::config::LCD_COLUMNS) {
    line = line.substring(0, deskdeck::config::LCD_COLUMNS);
  }
  return line;
}

String sensorPostUrl() {
  String url = STATUS_SERVER_URL;
  const int statusPathIndex = url.indexOf("/api/status");
  if (statusPathIndex >= 0) {
    url = url.substring(0, statusPathIndex);
  }
  return url + "/api/sensors/inside";
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

  const String effect = String(doc["effect"] | "solid");
  state.scrollText = effect == "scroll" || effect == "scroll_once";
  state.scrollOnce = effect == "scroll_once";
  state.line1 = state.scrollText ? trimmedLine(doc["line1"] | "") : fitLine(doc["line1"] | "");
  state.line2 = state.scrollText ? trimmedLine(doc["line2"] | "") : fitLine(doc["line2"] | "");
  state.backlight = colorFromName(String(doc["backlight"] | "white"));
  state.flashBacklight = effect == "flash";
  return state.line1.length() > 0 || state.line2.length() > 0;
}

bool StatusClient::postInsideTemperature(float temperatureF) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  HTTPClient http;
  http.setTimeout(config::HTTP_TIMEOUT_MS);
  if (!http.begin(sensorPostUrl())) {
    return false;
  }

  JsonDocument doc;
  doc["temperature_f"] = temperatureF;
  String body;
  serializeJson(doc, body);

  http.addHeader("Content-Type", "application/json");
  const int statusCode = http.POST(body);
  http.end();

  if (statusCode < 200 || statusCode >= 300) {
    Serial.print("Inside sensor POST failed. HTTP ");
    Serial.println(statusCode);
    return false;
  }

  return true;
}
}  // namespace deskdeck
