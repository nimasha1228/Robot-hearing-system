#include <Servo.h>
Servo myservo; // create servo object to control a servo
int val; // variable to read the value from the analog pin
int new_angle = 0;

void setup() {
  Serial.begin(9600);
   myservo.attach(9); // attaches the servo on pin 9 to the servo object
}

void loop() {
   if(Serial.available()>0){
    new_angle = new_angle + Serial.parseInt();
    val = Serial.parseInt();
    //Serial.println(val);
  }


  if (new_angle>180){new_angle=180;}
  if(new_angle<0){new_angle=0;}
   myservo.write(new_angle); // sets the servo position according to the scaled value
   delay(15);
}
