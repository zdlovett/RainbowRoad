#include <Adafruit_NeoPixel.h>

#define PIN 6
#define NUM_LEDS 251

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(2500000);

  strip.begin();
  strip.show();
}

char inbuf[NUM_LEDS*3];

void loop() {
  updateBuffer();
  updateStrip();
}

unsigned int index = 0; //track the color and led
void updateBuffer(){
  unsigned char done = 0; //loop until done == 1, which happens either on 0 or index = NUM_LEDS*3
  while(!done){
    if(Serial.available() > 0){
      unsigned char incoming = Serial.read();
      //Serial.write(incoming);

      if(incoming != 0){
        inbuf[index] = incoming;
        index += 1;
      } else {
        index = 0;
      }
    }

    if(index == NUM_LEDS*3 - 1){
      done = 1;
      index = 0;
    }
  }
}

void updateStrip(){
  for(int i=0; i<NUM_LEDS; i++){
    strip.setPixelColor(i, strip.Color(inbuf[i*3], inbuf[i*3+1], inbuf[i*3+2]));
  }
  strip.show();
}
