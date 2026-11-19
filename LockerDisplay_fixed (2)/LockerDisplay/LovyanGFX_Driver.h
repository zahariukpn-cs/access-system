#pragma once
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <lgfx/v1/platforms/esp32s3/Panel_RGB.hpp>
#include <lgfx/v1/platforms/esp32s3/Bus_RGB.hpp>
#include <driver/i2c.h>
class LGFX : public lgfx::LGFX_Device {
public:
 lgfx::Bus_RGB _bus_instance;
 lgfx::Panel_RGB _panel_instance;
 lgfx::Touch_GT911 _touch_instance;
 LGFX() {
  {auto c=_panel_instance.config();c.memory_width=800;c.memory_height=480;c.panel_width=800;c.panel_height=480;c.offset_x=0;c.offset_y=0;_panel_instance.config(c);}
  {auto c=_panel_instance.config_detail();c.use_psram=1;_panel_instance.config_detail(c);}
  {auto c=_bus_instance.config();c.panel=&_panel_instance;
   c.pin_d0=GPIO_NUM_8;c.pin_d1=GPIO_NUM_3;c.pin_d2=GPIO_NUM_46;c.pin_d3=GPIO_NUM_9;c.pin_d4=GPIO_NUM_1;
   c.pin_d5=GPIO_NUM_5;c.pin_d6=GPIO_NUM_6;c.pin_d7=GPIO_NUM_7;c.pin_d8=GPIO_NUM_15;c.pin_d9=GPIO_NUM_16;c.pin_d10=GPIO_NUM_4;
   c.pin_d11=GPIO_NUM_45;c.pin_d12=GPIO_NUM_48;c.pin_d13=GPIO_NUM_47;c.pin_d14=GPIO_NUM_21;c.pin_d15=GPIO_NUM_14;
   c.pin_henable=GPIO_NUM_40;c.pin_vsync=GPIO_NUM_41;c.pin_hsync=GPIO_NUM_39;c.pin_pclk=GPIO_NUM_0;
   c.freq_write=12000000;c.hsync_polarity=0;c.hsync_front_porch=8;c.hsync_pulse_width=4;c.hsync_back_porch=43;
   c.vsync_polarity=0;c.vsync_front_porch=8;c.vsync_pulse_width=4;c.vsync_back_porch=12;c.pclk_active_neg=1;c.de_idle_high=0;c.pclk_idle_high=0;
   _bus_instance.config(c);}
  _panel_instance.setBus(&_bus_instance);
  {auto c=_touch_instance.config();c.x_min=0;c.x_max=799;c.y_min=0;c.y_max=479;c.pin_int=-1;c.bus_shared=false;c.offset_rotation=0;
   c.i2c_port=I2C_NUM_1;c.pin_sda=GPIO_NUM_19;c.pin_scl=GPIO_NUM_20;c.pin_rst=-1;c.freq=400000;c.i2c_addr=0x14;
   _touch_instance.config(c);_panel_instance.setTouch(&_touch_instance);}
  setPanel(&_panel_instance);
 }
};
