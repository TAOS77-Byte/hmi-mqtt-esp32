import paho.mqtt.client as mqtt
import csv
import os
from datetime import datetime

BROKER = "localhost"
ARCHIVO = "registro_hmi.csv"


def guardar(direccion, topico, mensaje):
    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), direccion, topico, mensaje])


def al_conectar(client, userdata, flags, rc, properties=None):
    print("Conectado al broker")
    client.subscribe("hmi/estado")
    client.subscribe("hmi/temperatura")
    client.subscribe("hmi/alarma")
    client.subscribe("hmi/umbral_ack")
    client.subscribe("hmi/log_dump")


def al_recibir(client, userdata, msg):
    mensaje = msg.payload.decode()
    print(msg.topic, "->", mensaje)
    guardar("RX", msg.topic, mensaje)


def enviar(topico, mensaje):
    client.publish(topico, mensaje)
    guardar("TX", topico, mensaje)
    print("Enviado:", topico, "<-", mensaje)


if not os.path.exists(ARCHIVO):
    with open(ARCHIVO, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["fecha_hora", "direccion", "topico", "mensaje"])

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = al_conectar
client.on_message = al_recibir
client.connect(BROKER, 1883)
client.loop_start()

while True:
    print("")
    print("1. Encender LED")
    print("2. Apagar LED")
    print("3. Cambiar umbral")
    print("4. Pedir DUMP")
    print("5. Abrir archivo CSV")
    print("0. Salir")
    opcion = input("Opcion: ")

    if opcion == "1":
        enviar("hmi/led", "ON")
    elif opcion == "2":
        enviar("hmi/led", "OFF")
    elif opcion == "3":
        valor = input("Nuevo umbral: ")
        enviar("hmi/umbral", valor)
    elif opcion == "4":
        enviar("hmi/log_request", "DUMP")
    elif opcion == "5":
        os.startfile(ARCHIVO)
    elif opcion == "0":
        break

client.loop_stop()
client.disconnect()