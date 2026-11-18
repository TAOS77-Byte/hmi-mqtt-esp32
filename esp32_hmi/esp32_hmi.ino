#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* ssid = "Meso";
const char* password = "Un1f1M3so";
const char* broker = "172.17.161.205";

int ledEmbebido = 2;
int ledExterno = 4;
int pinDS18B20 = 13;

WiFiClient espClient;
PubSubClient client(espClient);
OneWire oneWire(pinDS18B20);
DallasTemperature sensor(&oneWire);

float umbral = 30.0;
float temperatura = 0;
bool alarma = false;
bool pedirDump = false;
unsigned long tiempoAnterior = 0;

String registro[20];
int indice = 0;
int total = 0;

void guardarRegistro(String texto) {
  registro[indice] = String(millis() / 1000) + "s;" + texto;
  indice = (indice + 1) % 20;
  if (total < 20) {
    total++;
  }
}

void enviarDump() {
  int inicio = (indice - total + 20) % 20;
  for (int i = 0; i < total; i++) {
    client.publish("hmi/log_dump", registro[(inicio + i) % 20].c_str());
  }
  client.publish("hmi/log_dump", "FIN");
}

void revisarAlarma() {
  if (temperatura > umbral && alarma == false) {
    alarma = true;
    digitalWrite(ledExterno, HIGH);
    client.publish("hmi/alarma", "ALTA");
    guardarRegistro("ALARMA;ALTA");
  }
  if (temperatura <= umbral && alarma == true) {
    alarma = false;
    digitalWrite(ledExterno, LOW);
    client.publish("hmi/alarma", "NORMAL");
    guardarRegistro("ALARMA;NORMAL");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String mensaje = "";
  for (unsigned int i = 0; i < length; i++) {
    mensaje += (char)payload[i];
  }
  mensaje.trim();
  String tema = String(topic);

  if (tema == "hmi/led") {
    if (mensaje == "ON") {
      digitalWrite(ledEmbebido, HIGH);
      guardarRegistro("LED;ON");
    }
    if (mensaje == "OFF") {
      digitalWrite(ledEmbebido, LOW);
      guardarRegistro("LED;OFF");
    }
  }

  if (tema == "hmi/umbral") {
    float valor = mensaje.toFloat();
    if (valor > 0) {
      umbral = valor;
      client.publish("hmi/umbral_ack", ("OK " + String(umbral, 1)).c_str());
      guardarRegistro("UMBRAL;" + String(umbral, 1));
      revisarAlarma();
    } else {
      client.publish("hmi/umbral_ack", "ERROR");
    }
  }

  if (tema == "hmi/log_request" && mensaje == "DUMP") {
    pedirDump = true;
  }
}

void reconectar() {
  while (!client.connected()) {
    Serial.println("Conectando a MQTT...");
    String id = "ESP32-" + String(random(0xffff), HEX);
    if (client.connect(id.c_str(), "hmi/estado", 1, true, "OFFLINE")) {
      Serial.println("Conectado");
      client.publish("hmi/estado", "ONLINE", true);
      client.subscribe("hmi/led");
      client.subscribe("hmi/umbral");
      client.subscribe("hmi/log_request");
      guardarRegistro("ESTADO;ONLINE");
    } else {
      Serial.print("Fallo, estado: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(ledEmbebido, OUTPUT);
  pinMode(ledExterno, OUTPUT);
  sensor.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi conectado");

  client.setServer(broker, 1883);
  client.setCallback(callback);
  client.setKeepAlive(10);
}

void loop() {
  if (!client.connected()) {
    reconectar();
  }
  client.loop();

  if (millis() - tiempoAnterior >= 2000) {
    tiempoAnterior = millis();

    sensor.requestTemperatures();
    temperatura = sensor.getTempCByIndex(0);

    String texto = String(temperatura, 1);
    client.publish("hmi/temperatura", texto.c_str());
    guardarRegistro("TEMP;" + texto);
    Serial.println("Temperatura: " + texto);

    revisarAlarma();
  }

  if (pedirDump) {
    pedirDump = false;
    enviarDump();
  }
}