#include <Adafruit_NeoPixel.h>

#define FEED_TIME 1000

#define PIN 6
#define NUM_LEDS 390

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  strip.begin();
  strip.show();

  //startup();
}

//char inbuf[NUM_LEDS*3];

void loop() {
  updateBuffer();
  updateStrip();
}

void startup(){
  //start with a slow fill and then transistion to a breathe anaimation
  uint8_t b, r;
  for(uint16_t i=0; i<NUM_LEDS; i++){
    r = (127.0 * (NUM_LEDS - i) ) / NUM_LEDS;
    b = (127.0 * i) / NUM_LEDS;
    strip.setPixelColor(i, strip.Color(r, 0, b));
    strip.show();
    delay(50);
  }

  float t;
  uint8_t red, green;
  while(Serial.available() == 0){
    for(uint16_t i=0; i<NUM_LEDS; i++){
      t = millis() / 2000.0;
      red = ( sin( t ) * sin(t) ) * 255;
      green = ( cos( t ) * cos(t) ) * 255;
      strip.setPixelColor(i, strip.Color(red, green, 255 - red));
    }
    strip.show();
  }
}

unsigned int index = 0; //track the led
unsigned char r, g, b, s;

void updateBuffer(){
  bool done = false; //loop until done == 1, which happens either on 0 or index = NUM_LEDS*3
  unsigned long feedTime = millis();
  
  while(!done){
    if(Serial.available() > 0){
      feedTime = millis(); //feed the watchdog
      unsigned char incoming = Serial.read();

      if(incoming != 0){
        // load in new color values
        // note that they come in as r0 g0 b0 r1 g1 b1 etc...
        // so we must make sure that we are indexing them correctly
        /*
         * index :: 0 1 2 ! 3 4 5 !
         * s=i%3 :: 0 1 2 ! 0 1 2 !
         * 
         */

        s = index % 3;
        switch(s){
          case 0: 
            r = incoming - 1;
            break;
          case 1:
            g = incoming - 1;
            break;
          case 2:
            b = incoming - 1;
        }
        
        index += 1;
        if(s == 2){
          strip.setPixelColor( (index / 3), strip.Color(r, g, b));
        }
      } else {
        index = 0;
      }
    }
    else{
      if(millis() - feedTime > FEED_TIME){

        //set the inbuf to 1s
        for(int i=0; i<NUM_LEDS; i++){
          //turn off the leds since we are not getting anything over serial
          strip.setPixelColor(i, strip.Color(0, 0, 0) );
        }
        //and signal done
        done = true;

        //and reset the index
        index = 0;
      }
    }

    if(index == NUM_LEDS*3 - 1){
      done = true;
      index = 0;
    }
  }
}

void updateStrip(){
  strip.show();
}
