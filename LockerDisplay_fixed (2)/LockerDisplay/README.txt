Arduino IDE: open LockerDisplay.ino.
Libraries: LVGL 8.3.11 (lv_conf.h: LV_COLOR_DEPTH 16, LV_COLOR_16_SWAP 0, LV_FONT_MONTSERRAT_24 1, LV_FONT_MONTSERRAT_30 1, LV_MEM_SIZE >= 128*1024 (the UI needs ~87 KB) or LV_MEM_CUSTOM 1), LovyanGFX (1.1.x-1.3.x).
Board settings (Elecrow/SmartView 5.0" ESP32-S3, N4R8):
  Board: ESP32S3 Dev Module | PSRAM: OPI PSRAM | Flash Mode: QIO 80MHz | Flash Size: 4MB (32Mb)
  Partition Scheme: Huge APP (3MB No OTA/1MB SPIFFS)   <- needed, the cat image alone is ~730 KB
Display: RGB 800x480, timings as in Elecrow's official LovyanGFX config (12 MHz, porches 8/4/43 and 8/4/12, pclk_active_neg=1).
Touch: GT911 on GPIO19/20 (I2C_NUM_1), address 0x14/0x5D is auto-detected. Backlight: GPIO2.
Home screen: tap the cat -> screen with currently opened boxes (ui_OpenedBoxes); the button there returns to Home.
