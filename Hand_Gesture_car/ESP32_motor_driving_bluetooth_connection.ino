#include <WiFi.h>

const char* ssid = "ESP32_Car_AP";
const char* password = "12345678";

WiFiServer server(1234);

// Motor control pins
// Left Motor Pins
const int LEFT_IN1 = 25;
const int LEFT_IN2 = 26;
const int LEFT_PWM = 27;

// Right Motor Pins
const int RIGHT_IN1 = 12;
const int RIGHT_IN2 = 14;
const int RIGHT_PWM = 16;


WiFiClient client;  // Store the active client

// Move left motor forward/backward with given speed (0-255)
void moveLeftMotor(bool forward, int speed) {
  if (forward) {
    digitalWrite(LEFT_IN1, HIGH);
    digitalWrite(LEFT_IN2, LOW);
  } else {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, HIGH);
  }
analogWrite(LEFT_PWM, speed);
}

// Move right motor forward/backward with given speed (0-255)
void moveRightMotor(bool forward, int speed) {
  if (forward) {
    digitalWrite(RIGHT_IN1, HIGH);
    digitalWrite(RIGHT_IN2, LOW);
  } else {
    digitalWrite(RIGHT_IN1, LOW);
    digitalWrite(RIGHT_IN2, HIGH);
  }
  analogWrite(RIGHT_PWM, speed);
}

// Move both motors forward at speed
void moveForward(int speed) {
  moveLeftMotor(true, speed);
  moveRightMotor(true, speed);
}

// Stop both motors immediately
void stopMotors() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, LOW);
  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, LOW);
  analogWrite(LEFT_PWM, 0);
  analogWrite(RIGHT_PWM, 0);
}

// Reverse both motors at speed
void reverseMotor(int speed) {
  moveLeftMotor(false, speed);
  moveRightMotor(false, speed);
}

// Turn right: left motor forward, right motor backward at given speed
void turnRight(int speed) {
  moveLeftMotor(true, speed);
  moveRightMotor(false, speed);
}

// Turn left: left motor backward, right motor forward at given speed
void turnLeft(int speed) {
  moveLeftMotor(false, speed);
  moveRightMotor(true, speed);
}

void setup() {
  Serial.begin(115200);

  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);


  // Start WiFi as Access Point
  WiFi.softAP(ssid, password);
  Serial.print("ESP32 AP IP: "); Serial.println(WiFi.softAPIP());

  // Start TCP server
  server.begin();
  Serial.println("TCP Server started");

  stopMotors();
}

void loop() {
  // Check for new client if no active client or client disconnected
  if (!client || !client.connected()) {
    client = server.available();
  }

  if (client && client.connected()) {
    static String incomingCommand = "";

    // Read available data without blocking
    while (client.available()) {
      char c = client.read();

      if (c == '\n') {
        incomingCommand.trim();
        if (incomingCommand.length() > 0) {
          Serial.print("Received command: ");
          Serial.println(incomingCommand);

          // Process commands
          if (incomingCommand == "F") {
            moveForward(180);
          }
          else if (incomingCommand == "R") {
            turnRight(100);
          }
          else if (incomingCommand == "L") {
            turnLeft(100);
          }
          else if (incomingCommand == "I") {
            moveForward(200);
          }
          else if (incomingCommand == "D") {
            moveForward(130);
          }
          else if (incomingCommand == "S") {
            stopMotors();
          }
          else if (incomingCommand == "B") {
            reverseMotor(150);
          }
          else {
            Serial.println("Unknown command");
          }
        }
        incomingCommand = "";
      } else {
        incomingCommand += c;
      }
    }
  }//start
  else{
    stopMotors();
  }