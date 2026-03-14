#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#include <WiFi.h>
IPAddress apIP(192, 168, 4, 1);
IPAddress netMsk(255, 255, 255, 0);
WiFiServer tcpServer(8080);
WiFiClient client;

Adafruit_MPU6050 mpu;

const String FIRMWARE_VERSION = "1.2";

byte pinA = 4;
byte pinB = 5;
byte pinC = 3;
byte pinD = 6;

byte mode = 0;

// radians now
const float MAX_ANGLE = 0.8f;   // ~46 deg
const byte TURNING_THRUST_LIMIT = 120;

float yaw = 0;

// keep targets in radians
float targetGyroX = 0;
float targetGyroY = 0;

float gyroOffsetX = 0;
float gyroOffsetY = 0;
float accOffsetX = 0;
float accOffsetY = 0;
float accOffsetZ = 0;

// these are actually integrated angles
float gyroX = 0;
float gyroY = 0;
float lastGyroX = 0;
float lastGyroY = 0;

int thrustA = 0;
int thrustB = 0;
int thrustC = 0;
int thrustD = 0;

bool propLock = false;

unsigned long lastTime = 0;

class PIDController {
  public:
    float kp, ki, kd;
    float max_output, max_i;
    float prev_error = 0.0f;
    float prev_error2 = 0.0f;
    float integral = 0.0f;
    float deriv_tau = 0.0f;
    float _d_state = 0.0f;
    float d_clip = -1.0f;

    float last_p = 0.0f;
    float last_i = 0.0f;
    float last_d = 0.0f;

    PIDController(float kp_, float ki_, float kd_,
                  float max_output_ = 3.0f, float max_i_ = 1.0f,
                  float deriv_tau_ = 0.0f, float d_clip_ = -1.0f) {
      kp = kp_;
      ki = ki_;
      kd = kd_;
      max_output = max_output_;
      max_i = max_i_;
      deriv_tau = deriv_tau_;
      d_clip = d_clip_;
    }

    float compute(float error, float dt, float d_meas = NAN) {
      if (dt <= 0.0f) return 0.0f;

      // I
      integral += error * dt;
      if (integral > max_i) integral = max_i;
      if (integral < -max_i) integral = -max_i;

      last_i = ki * integral;
      last_p = kp * error;

      // D
      float raw_d;
      if (!isnan(d_meas)) {
        raw_d = d_meas;
      } else {
        raw_d = (3.0f * error - 4.0f * prev_error + prev_error2) / (2.0f * dt);
      }

      float a = deriv_tau / (deriv_tau + dt);
      _d_state = a * _d_state + (1.0f - a) * raw_d;

      float dterm = kd * _d_state;
      if (d_clip >= 0.0f) {
        if (dterm > d_clip) dterm = d_clip;
        if (dterm < -d_clip) dterm = -d_clip;
      }
      last_d = dterm;

      float u = last_p + last_i + dterm;

      prev_error2 = prev_error;
      prev_error = error;

      if (u > max_output) u = max_output;
      if (u < -max_output) u = -max_output;
      return u;
    }

    void reset() {
      prev_error = 0.0f;
      prev_error2 = 0.0f;
      integral = 0.0f;
      _d_state = 0.0f;
      last_p = 0.0f;
      last_i = 0.0f;
      last_d = 0.0f;
    }
};

PIDController pidX(80.0f, 8.0f, 8.0f, TURNING_THRUST_LIMIT, 0.3f, 0.08f, TURNING_THRUST_LIMIT);
PIDController pidY(80.0f, 8.0f, 8.0f, TURNING_THRUST_LIMIT, 0.3f, 0.08f, TURNING_THRUST_LIMIT);

void resetControllers() {
  pidX.reset();
  pidY.reset();
}

void recalibrate() {
  sensors_event_t a, g, temp;
  unsigned int numCalibReadings = 3000;
  digitalWrite(7, HIGH);
  digitalWrite(8, LOW);
  digitalWrite(9, LOW);

  gyroOffsetX = 0;
  gyroOffsetY = 0;
  accOffsetX = 0;
  accOffsetY = 0;
  accOffsetZ = 0;

  Serial.println("Callibrating, please wait");

  for (unsigned int i = 0; i < numCalibReadings; i++) {
    mpu.getEvent(&a, &g, &temp);
    gyroOffsetX += g.gyro.x;
    gyroOffsetY += g.gyro.y;
    accOffsetX += a.acceleration.x;
    accOffsetY += a.acceleration.y;
    accOffsetZ += a.acceleration.z;
    delay(2);
  }

  gyroOffsetX /= numCalibReadings;
  gyroOffsetY /= numCalibReadings;
  accOffsetX /= numCalibReadings;
  accOffsetY /= numCalibReadings;
  accOffsetZ /= numCalibReadings;

  gyroX = 0.0f;
  gyroY = 0.0f;
  resetControllers();

  digitalWrite(7, LOW);
  digitalWrite(8, LOW);
  digitalWrite(9, HIGH);
}

void setup() {
  Serial.begin(115200);

  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);

  pinMode(pinA, OUTPUT);
  pinMode(pinB, OUTPUT);
  pinMode(pinC, OUTPUT);
  pinMode(pinD, OUTPUT);

  digitalWrite(7, HIGH);
  digitalWrite(8, LOW);
  digitalWrite(9, LOW);

  delay(3000);

  Wire.begin(11, 10);
  if (!mpu.begin(0x68)) {
    Serial.println("Failed to find MPU6050 chip");
    digitalWrite(7, LOW);
    digitalWrite(8, HIGH);
    while (1) { delay(10); }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  recalibrate();

  WiFi.softAPConfig(apIP, apIP, netMsk);
  WiFi.softAP("AeroHacks Drone 4", "skibidi123");
  tcpServer.begin();

  Serial.println("ready");

  lastTime = millis();
}

void loop() {
  unsigned long newTime = millis();
  float dt = (newTime - lastTime) * 0.001f;   // seconds
  lastTime = newTime;

  if (dt <= 0.0f) dt = 0.001f;

  lastGyroX = gyroX;
  lastGyroY = gyroY;

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float gyroVX = g.gyro.x - gyroOffsetX;   // rad/s
  float gyroVY = g.gyro.y - gyroOffsetY;   // rad/s

  // integrate angles in radians
  gyroX -= gyroVX * dt;
  gyroY -= gyroVY * dt;

  if (gyroX > MAX_ANGLE || gyroX < -MAX_ANGLE || gyroY > MAX_ANGLE || gyroY < -MAX_ANGLE) {
    mode = 0;
    resetControllers();
    digitalWrite(8, HIGH);
  }

  if (!client) {
    client = tcpServer.available();
  } else if (!client.connected()) {
    client.stop();
    mode = 0;
    resetControllers();
  }

  if (client.available()) {
    String instruct = client.readStringUntil('\n');

    if (instruct == "ping") {
      client.print("ping");
    } else if (instruct == "angX") {
      client.print(String(gyroX));
    } else if (instruct == "angY") {
      client.print(String(gyroY));
    } else if (instruct == "gyroX") {
      client.print(String(gyroVX));
    } else if (instruct == "gyroY") {
      client.print(String(gyroVY));
    } else if (instruct == "gMode") {
      client.print(String(mode));
    } else if (instruct == "vers") {
      client.print(FIRMWARE_VERSION);
    } else if (instruct == "lb1") {
      digitalWrite(7, HIGH);
    } else if (instruct == "lb0") {
      digitalWrite(7, LOW);
    } else if (instruct == "lr1") {
      digitalWrite(8, HIGH);
    } else if (instruct == "lr0") {
      digitalWrite(8, LOW);
    } else if (instruct == "lg1") {
      digitalWrite(9, HIGH);
    } else if (instruct == "lg0") {
      digitalWrite(9, LOW);
    } else if (instruct == "rst") {
      recalibrate();
    } else if (instruct == "lck") {
      propLock = true;
      mode = 0;
      resetControllers();
    } else if (instruct == "ulk") {
      propLock = false;
    } else if (instruct.startsWith("mode")) {
      instruct.remove(0, 4);
      mode = instruct.toInt();
      if (mode < 0 || mode > 2) mode = 0;
      if (mode == 0) resetControllers();
      Serial.print("New Mode: ");
      Serial.print(mode);
    } else if (instruct.startsWith("gx")) {
      instruct.remove(0, 2);
      targetGyroX = instruct.toFloat();   // radians
    } else if (instruct.startsWith("gy")) {
      instruct.remove(0, 2);
      targetGyroY = instruct.toFloat();   // radians
    } else if (instruct.startsWith("gainP")) {
      instruct.remove(0, 5);
      float v = instruct.toFloat();
      pidX.kp = v;
      pidY.kp = v;
    } else if (instruct.startsWith("gainI")) {
      instruct.remove(0, 5);
      float v = instruct.toFloat();
      pidX.ki = v;
      pidY.ki = v;
    } else if (instruct.startsWith("gainD")) {
      instruct.remove(0, 5);
      float v = instruct.toFloat();
      pidX.kd = v;
      pidY.kd = v;
    } else if (instruct.startsWith("yaw")) {
      instruct.remove(0, 3);
      yaw = instruct.toFloat();
    } else if (instruct == "irst") {
      resetControllers();
    } else if (instruct == "geti") {
      client.print(pidX.integral);
      client.print(',');
      client.print(pidY.integral);
    } else if (instruct == "manT") {
      thrustA = client.readStringUntil(',').toInt();
      thrustB = client.readStringUntil(',').toInt();
      thrustC = client.readStringUntil(',').toInt();
      thrustD = client.readStringUntil('\n').toInt();
    } else if (instruct == "incT") {
      thrustA += client.readStringUntil(',').toInt();
      thrustB += client.readStringUntil(',').toInt();
      thrustC += client.readStringUntil(',').toInt();
      thrustD += client.readStringUntil('\n').toInt();
    }

    client.print("\n");
  }

  float thrustOffA = 0;
  float thrustOffB = 0;
  float thrustOffC = 0;
  float thrustOffD = 0;

  if (mode == 2) {
    float errX = targetGyroX - gyroX;  // rad
    float errY = targetGyroY - gyroY;  // rad

    // d_meas = derivative of error = -gyro rate for constant target
    float outX = pidX.compute(errX, dt, -gyroVX);
    float outY = pidY.compute(errY, dt, -gyroVY);

    thrustOffA -= outX;
    thrustOffB -= outX;
    thrustOffC += outX;
    thrustOffD += outX;

    thrustOffA -= outY;
    thrustOffB += outY;
    thrustOffC -= outY;
    thrustOffD += outY;
  }

  if (thrustA < 0) thrustA = 0;
  if (thrustB < 0) thrustB = 0;
  if (thrustC < 0) thrustC = 0;
  if (thrustD < 0) thrustD = 0;

  if (thrustA > 200) thrustA = 200;
  if (thrustB > 200) thrustB = 200;
  if (thrustC > 200) thrustC = 200;
  if (thrustD > 200) thrustD = 200;

  if (mode == 0) {
    yaw = 0;
    thrustA = 0;
    thrustB = 0;
    thrustC = 0;
    thrustD = 0;
  }

  if (mode <= 1) {
    thrustOffA = 0;
    thrustOffB = 0;
    thrustOffC = 0;
    thrustOffD = 0;
  }

  if (thrustOffA < -TURNING_THRUST_LIMIT) thrustOffA = -TURNING_THRUST_LIMIT;
  if (thrustOffB < -TURNING_THRUST_LIMIT) thrustOffB = -TURNING_THRUST_LIMIT;
  if (thrustOffC < -TURNING_THRUST_LIMIT) thrustOffC = -TURNING_THRUST_LIMIT;
  if (thrustOffD < -TURNING_THRUST_LIMIT) thrustOffD = -TURNING_THRUST_LIMIT;

  if (thrustOffA > TURNING_THRUST_LIMIT) thrustOffA = TURNING_THRUST_LIMIT;
  if (thrustOffB > TURNING_THRUST_LIMIT) thrustOffB = TURNING_THRUST_LIMIT;
  if (thrustOffC > TURNING_THRUST_LIMIT) thrustOffC = TURNING_THRUST_LIMIT;
  if (thrustOffD > TURNING_THRUST_LIMIT) thrustOffD = TURNING_THRUST_LIMIT;

  int newThrustA = thrustA + thrustOffA - yaw;
  int newThrustB = thrustB + thrustOffB + yaw;
  int newThrustC = thrustC + thrustOffC + yaw;
  int newThrustD = thrustD + thrustOffD - yaw;

  if (newThrustA < 0) newThrustA = 0;
  if (newThrustB < 0) newThrustB = 0;
  if (newThrustC < 0) newThrustC = 0;
  if (newThrustD < 0) newThrustD = 0;

  if (newThrustA > 250) newThrustA = 250;
  if (newThrustB > 250) newThrustB = 250;
  if (newThrustC > 250) newThrustC = 250;
  if (newThrustD > 250) newThrustD = 250;

  if (propLock) {
    newThrustA = 0;
    newThrustB = 0;
    newThrustC = 0;
    newThrustD = 0;
  }

  analogWrite(pinA, newThrustA);
  analogWrite(pinB, newThrustB);
  analogWrite(pinC, newThrustC);
  analogWrite(pinD, newThrustD);
}
