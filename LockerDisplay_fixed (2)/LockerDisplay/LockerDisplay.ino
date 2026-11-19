#include <Arduino.h>
#include <Wire.h>
#include <lvgl.h>
#include "LovyanGFX_Driver.h"
#include "ui.h"

LGFX gfx;
static lv_disp_draw_buf_t draw_buf;
static lv_color_t *draw_pixels = nullptr;
static uint32_t last_tick = 0;

static void display_flush(lv_disp_drv_t *disp,
                          const lv_area_t *area,
                          lv_color_t *pixels) {
  static int flush_count = 0;

  if (flush_count < 20) {
    Serial.printf(
      "FLUSH %d: x1=%d y1=%d x2=%d y2=%d\n",
      flush_count,
      area->x1,
      area->y1,
      area->x2,
      area->y2
    );
    flush_count++;
  }

  int32_t w = area->x2 - area->x1 + 1;
  int32_t h = area->y2 - area->y1 + 1;

  gfx.startWrite();
  gfx.pushImage(
    area->x1,
    area->y1,
    w,
    h,
    (const lgfx::rgb565_t *)pixels
  );
  gfx.endWrite();

  lv_disp_flush_ready(disp);
}
static void touch_read(lv_indev_drv_t *indev, lv_indev_data_t *data) {
  uint16_t x=0, y=0;
  if (gfx.getTouch(&x, &y)) {
    data->state = LV_INDEV_STATE_PR;
    data->point.x = x;
    data->point.y = y;
  } else {
    data->state = LV_INDEV_STATE_REL;
  }
}

// Serial Monitor (115200, line ending "Newline"): type a screen number or name + Enter to switch page.
struct ScreenEntry { const char *name; lv_obj_t **scr; void (*init)(void); };
#define SCR(n) { #n, &ui_##n, ui_##n##_screen_init }
static const ScreenEntry screens[] = {
  SCR(HomeScreen), SCR(AccessDenied), SCR(GroupBoxCreate), SCR(AccessGranted),
  SCR(AddToGroup), SCR(Opened), SCR(OpenedBoxes), SCR(Error),
  SCR(TakeFreeBox), SCR(LimitError), SCR(LeaveBox), SCR(GroupBoxEdit),
  SCR(GroupBox), SCR(Taken), SCR(GroupBoxEdit1), SCR(BoxNotClosed)
};
static const int SCREEN_COUNT = sizeof(screens) / sizeof(screens[0]);

static void serial_help() {
  Serial.println("Type screen number or name + Enter:");
  for (int i = 0; i < SCREEN_COUNT; i++) Serial.printf("  %d  %s\n", i, screens[i].name);
}

static void serial_screens() {
  static char buf[32];
  static uint8_t n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c != '\n' && c != '\r') {
      if (n < sizeof(buf) - 1) buf[n++] = c;
      continue;
    }
    if (!n) continue;
    buf[n] = 0;
    n = 0;
    int idx = -1;
    if (buf[0] >= '0' && buf[0] <= '9') {
      idx = atoi(buf);
    } else {
      for (int i = 0; i < SCREEN_COUNT; i++) if (strcasecmp(buf, screens[i].name) == 0) idx = i;
    }
    if (idx < 0 || idx >= SCREEN_COUNT) {
      serial_help();
      continue;
    }
    Serial.printf("-> %s\n", screens[idx].name);
    _ui_screen_change(screens[idx].scr, LV_SCR_LOAD_ANIM_NONE, 0, 0, screens[idx].init);
  }
}

void setup() {
  Serial.begin(115200);
  delay(300);
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH); // Confirmed backlight pin on this display
  // I2C for the GT911 touch is initialised by LovyanGFX itself (I2C_NUM_1, GPIO19/20).
  // Do not call Wire.begin(19, 20) here: it would grab the same pins.

  Serial.println("Initializing RGB display...");
  if (!gfx.init()) {
    Serial.println("ERROR: gfx.init failed");
    return;
  }
  gfx.fillScreen(TFT_BLACK);
  lv_init();

  // 800 x 40 pixels, RGB565; much smaller than a full-screen buffer.
  const size_t count = 800 * 40;
  // Internal RAM first: the RGB panel continuously reads the frame buffer from PSRAM,
  // so keeping LVGL's draw buffer out of PSRAM avoids bandwidth contention (garbled/half image).
  draw_pixels = (lv_color_t *)heap_caps_malloc(count * sizeof(lv_color_t), MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  if (!draw_pixels) {
    draw_pixels = (lv_color_t *)heap_caps_malloc(count * sizeof(lv_color_t), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  }
  if (!draw_pixels) {
    Serial.println("ERROR: LVGL draw buffer allocation failed");
    return;
  }
  lv_disp_draw_buf_init(&draw_buf, draw_pixels, nullptr, count);
  static lv_disp_drv_t disp_drv;
  lv_disp_drv_init(&disp_drv);
  disp_drv.hor_res = 800;
  disp_drv.ver_res = 480;
  disp_drv.flush_cb = display_flush;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);

  static lv_indev_drv_t indev_drv;
  lv_indev_drv_init(&indev_drv);
  indev_drv.type = LV_INDEV_TYPE_POINTER;
  indev_drv.read_cb = touch_read;
  lv_indev_drv_register(&indev_drv);

  gfx.fillScreen(TFT_BLACK);
  ui_init();
  last_tick = millis();
  serial_help();
}

void loop() {
  uint32_t now = millis();
  lv_tick_inc(now - last_tick);
  last_tick = now;
  serial_screens();
  lv_timer_handler();
  delay(5);
}
