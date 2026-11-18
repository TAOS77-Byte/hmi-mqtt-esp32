import paho.mqtt.client as mqtt
import tkinter as tk
import csv
import os
from datetime import datetime

BROKER = "localhost"
ARCHIVO = "registro_hmi.csv"

mensajes = []


def guardar(direccion, topico, mensaje):
    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), direccion, topico, mensaje])


def al_conectar(client, userdata, flags, rc, properties=None):
    client.subscribe("hmi/estado")
    client.subscribe("hmi/temperatura")
    client.subscribe("hmi/alarma")
    client.subscribe("hmi/umbral_ack")
    client.subscribe("hmi/log_dump")


def al_recibir(client, userdata, msg):
    mensaje = msg.payload.decode()
    guardar("RX", msg.topic, mensaje)
    mensajes.append((msg.topic, mensaje))


def enviar(topico, mensaje):
    client.publish(topico, mensaje)
    guardar("TX", topico, mensaje)
    registro.insert(tk.END, "Enviado: " + topico + " <- " + mensaje + "\n")
    registro.see(tk.END)


def actualizar():
    while len(mensajes) > 0:
        topico, mensaje = mensajes.pop(0)

        if topico == "hmi/estado":
            etiqueta_estado.config(text="Estado: " + mensaje)
            if mensaje == "ONLINE":
                etiqueta_estado.config(fg="green")
            else:
                etiqueta_estado.config(fg="red")

        elif topico == "hmi/temperatura":
            etiqueta_temp.config(text=mensaje + " °C")

        elif topico == "hmi/alarma":
            etiqueta_alarma.config(text="Alarma: " + mensaje)
            if mensaje == "ALTA":
                etiqueta_alarma.config(bg="red", fg="white")
            else:
                etiqueta_alarma.config(bg="green", fg="white")

        elif topico == "hmi/umbral_ack":
            etiqueta_umbral.config(text="Umbral confirmado: " + mensaje)

        if topico != "hmi/temperatura":
            registro.insert(tk.END, topico + " -> " + mensaje + "\n")
            registro.see(tk.END)

    ventana.after(200, actualizar)


def cerrar():
    client.loop_stop()
    client.disconnect()
    ventana.destroy()


if not os.path.exists(ARCHIVO):
    with open(ARCHIVO, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["fecha_hora", "direccion", "topico", "mensaje"])

ventana = tk.Tk()
ventana.title("HMI MQTT - ESP32")
ventana.geometry("440x580")

etiqueta_estado = tk.Label(ventana, text="Estado: --", font=("Arial", 14), fg="gray")
etiqueta_estado.pack(pady=5)

etiqueta_temp = tk.Label(ventana, text="-- °C", font=("Arial", 40))
etiqueta_temp.pack(pady=5)

etiqueta_alarma = tk.Label(ventana, text="Alarma: --", font=("Arial", 14), width=20, bg="lightgray")
etiqueta_alarma.pack(pady=5)

marco_led = tk.Frame(ventana)
marco_led.pack(pady=10)
tk.Label(marco_led, text="LED de la placa:").pack(side=tk.LEFT)
tk.Button(marco_led, text="Encender", width=10, command=lambda: enviar("hmi/led", "ON")).pack(side=tk.LEFT, padx=5)
tk.Button(marco_led, text="Apagar", width=10, command=lambda: enviar("hmi/led", "OFF")).pack(side=tk.LEFT, padx=5)

marco_umbral = tk.Frame(ventana)
marco_umbral.pack(pady=10)
tk.Label(marco_umbral, text="Umbral (°C):").pack(side=tk.LEFT)
entrada_umbral = tk.Entry(marco_umbral, width=8)
entrada_umbral.insert(0, "30.0")
entrada_umbral.pack(side=tk.LEFT, padx=5)
tk.Button(marco_umbral, text="Enviar", width=10, command=lambda: enviar("hmi/umbral", entrada_umbral.get())).pack(side=tk.LEFT)

etiqueta_umbral = tk.Label(ventana, text="Umbral confirmado: --")
etiqueta_umbral.pack()

marco_log = tk.Frame(ventana)
marco_log.pack(pady=10)
tk.Button(marco_log, text="Pedir DUMP", width=12, command=lambda: enviar("hmi/log_request", "DUMP")).pack(side=tk.LEFT, padx=5)
tk.Button(marco_log, text="Abrir CSV", width=12, command=lambda: os.startfile(ARCHIVO)).pack(side=tk.LEFT, padx=5)

registro = tk.Text(ventana, height=12, width=50)
registro.pack(padx=10, pady=5)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = al_conectar
client.on_message = al_recibir
client.connect(BROKER, 1883)
client.loop_start()

ventana.protocol("WM_DELETE_WINDOW", cerrar)
ventana.after(200, actualizar)
ventana.mainloop()