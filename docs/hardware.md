# Hardware

## Board

- ESP32-C3-DevKit-RUST-1 v1.2A
- ESP32-C3, 3.3 V GPIO logic
- USB is used for flashing and Serial Monitor during bring-up

## Display

- DFRobot Gravity I2C 16x2 LCD with RGB backlight
- Operates at 3.3 V to 5.0 V according to DFRobot documentation
- Uses I2C for both display text and RGB backlight control

## Wiring

The lab-kit LCD displayed text reliably when powered from the ESP32 `5V` pin. It did not display text reliably from `3V3`.

```text
LCD VCC -> ESP32 5V
LCD GND -> ESP32 GND
LCD SDA -> GPIO10 / SDA
LCD SCL -> GPIO8 / SCL
```

## I2C Notes

The Rust-1 board uses different I2C pins than the Rust-2 board. This project is configured for Rust-1:

```text
SDA = GPIO10
SCL = GPIO8
```

Expected onboard I2C devices may include:

```text
0x68
0x70
```

The LCD should appear as additional address(es). Confirmed addresses from the working setup:

```text
0x2D = RGB backlight controller
0x3E = LCD text controller
0x68 = onboard board device
0x70 = onboard board device
```

The firmware currently assumes RGB address `0x2D`, which matches the DFRobot library table for LCD1602 RGB Module V2.0.

## Bring-Up Checklist

- Confirm LCD is powered from `5V`.
- Confirm common ground between ESP32 and LCD.
- Confirm SDA/SCL are not swapped.
- Upload firmware.
- Open Serial Monitor at `115200`.
- Record all I2C addresses in `status.md`.
- Confirm display text and backlight color.

## Caution

The ESP32-C3 GPIO pins are 3.3 V logic. The current lab-kit setup works with LCD VCC on `5V`, but long-term use should confirm the LCD module's I2C level shifting/pullup design. If the module does not provide safe 3.3 V I2C signaling when powered from `5V`, add an I2C level shifter.
