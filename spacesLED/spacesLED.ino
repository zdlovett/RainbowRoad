#include <Adafruit_NeoPixel.h>

#define FEED_TIME 1000

#define PIN 6
#define NUM_LEDS 353

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // put your setup code here, to run once:
  delay(50);
  
  Serial.begin(2000000);

  strip.begin();
  strip.show();

  startup();
}

char inbuf[NUM_LEDS*3];

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
  uint8_t red;
  while(Serial.available() == 0){
    for(uint16_t i=0; i<NUM_LEDS; i++){
      t = millis() / 2000.0;
      red = ( sin( t ) * sin(t) ) * 255; 
      strip.setPixelColor(i, strip.Color(red, 0, 255 - red));
    }
    strip.show();
  }
}

unsigned int index = 0; //track the color and led
void updateBuffer(){
  bool done = false; //loop until done == 1, which happens either on 0 or index = NUM_LEDS*3
  unsigned long feedTime = millis();
  
  while(!done){
    if(Serial.available() > 0){
      feedTime = millis(); //feed the watchdog
      unsigned char incoming = Serial.read();

      if(incoming != 0){
        inbuf[index] = incoming;
        index += 1;
      } else {
        index = 0;
      }
    }
    else{
      if(millis() - feedTime > FEED_TIME){

        //set the inbuf to 1s
        for(int i=0; i<NUM_LEDS*3; i++){
          inbuf[i] = 1;
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
  for(int i=0; i<NUM_LEDS; i++){
    strip.setPixelColor(i, strip.Color(inbuf[i*3]-1, inbuf[i*3+1]-1, inbuf[i*3+2]-1));
  }
  strip.show();
}
