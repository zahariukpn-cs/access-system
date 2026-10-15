/*
  Input Pull-up Serial

  This example demonstrates the use of pinMode(INPUT_PULLUP). It reads a digital
  input on pin 2 and prints the results to the Serial Monitor.

  The circuit:
  - momentary switch attached from pin 2 to ground
  - built-in LED on pin 13

  Unlike pinMode(INPUT), there is no pull-down resistor necessary. An internal
  20K-ohm resistor is pulled to 5V. This configuration causes the input to read
  HIGH when the switch is open, and LOW when it is closed.

  created 14 Mar 2012
  by Scott Fitzgerald

  This example code is in the public domain.

  https://www.arduino.cc/en/Tutorial/BuiltInExamples/InputPullupSerial
*/
#define LOCK_RELE_ON  1
#define LOCK_RELE_OFF 0

#define LOCK_STATE_OPEN   0
#define LOCK_STATE_CLOSED 1

#define PIN_LOCK_RELE  2
#define PIN_LOCK_STATE 3

void setup() {
  //start serial connection
  Serial.begin(115200);
  //configure pin 2 as an input and enable the internal pull-up resistor
  pinMode(PIN_LOCK_STATE, INPUT_PULLUP);
  pinMode(PIN_LOCK_RELE, OUTPUT);
}

void loop() {
  
  if(digitalRead(PIN_LOCK_STATE) == LOCK_STATE_OPEN)
  {
     Serial.println("ERROR! Lock is opened!");
     delay(100);
     return;
  }

  digitalWrite(PIN_LOCK_RELE, LOCK_RELE_ON);
  delay(10);

  while(digitalRead(PIN_LOCK_STATE) == LOCK_STATE_CLOSED)
  {
    ;
  }

  Serial.println("Lock is opened");
  digitalWrite(PIN_LOCK_RELE, LOCK_RELE_OFF);
  
  delay(1000);
}
