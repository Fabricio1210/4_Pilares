from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import mean
from typing import Protocol, List
from statistics import mean, stdev

class Notificador(Protocol):
    def enviar(self, mensaje: str) -> None: ...

class NotificadorEmail:
    def __init__(self, destinatario: str) -> None:
        self._destinatario = destinatario # encapsulado
    def enviar(self, mensaje: str) -> None:
        print(f"[EMAIL a {self._destinatario}] {mensaje}")

class NotificadorWebhook:
    def __init__(self, url: str) -> None:
        self._url = url
    def enviar(self, mensaje: str) -> None:
        print(f"[WEBHOOK {self._url}] {mensaje}")

@dataclass
class Sensor(ABC):
    id: str
    ventana: int = 5
    _calibracion: float = field(default=0.0, repr=False) # encapsulado
    _buffer: list[float] = field(default_factory=list, repr=False)
    def leer(self, valor: float) -> None:
        """Agrega lectura aplicando calibración y mantiene ventana móvil."""
        v = valor + self._calibracion
        self._buffer.append(v)
        if len(self._buffer) > self.ventana:
            self._buffer.pop(0)

    @property
    def promedio(self) -> float:
        return mean(self._buffer) if self._buffer else 0.0

    @abstractmethod
    def en_alerta(self) -> bool: ...

    @abstractmethod
    def obtener_unidad(self) -> str: ...


@dataclass
class SensorTemperatura(Sensor):
    umbral: float = 80.0
    def en_alerta(self) -> bool:
        # Polimorfismo: cada sensor define su propia condición
        return self.promedio >= self.umbral
    def obtener_unidad(self) -> str:
        return "°C"

@dataclass
class SensorVibracion(Sensor):
    rms_umbral: float = 2.5
    def en_alerta(self) -> bool:
        # Ejemplo tonto de RMS  promedio absoluto
        return abs(self.promedio) >= self.rms_umbral
    def obtener_unidad(self) -> str:
        return "m/s²"    

@dataclass
class SensorMovimento(Sensor):
    mov_umbral: float = 1.0
    def en_alerta(self) -> bool:
        if len(self._buffer) < 2:
            return False
        desviacion_estandar = stdev(self._buffer)
        return desviacion_estandar >= self.mov_umbral
    def obtener_unidad(self) -> str:
        return "m/s"

class GestorAlertas:
    def __init__(self, sensores: List[Sensor], notificadores: List[Notificador]) -> None:
        self._sensores = sensores
        self._notificadores = notificadores

    def evaluar_y_notificar(self) -> None:
        for s in self._sensores:
            if s.en_alerta():
                msg = f"ALERTA Sensor {s.id} en umbral (avg={s.promedio:.2f})"
                for n in self._notificadores:
                    n.enviar(msg)

class ControladorLuces:
    def __init__(self, sensor_movimiento: SensorMovimento):
        self.sensor = sensor_movimiento
        self.luces_encendidas = False
    
    def verificar_movimiento(self):
        if self.sensor.en_alerta():
            self.encender_luces()
        else:
            self.apagar_luces()
            print("No hay suficiente movimiento detectado")
    
    def encender_luces(self):
        if not self.luces_encendidas:
            self.luces_encendidas = True
            print("LUCES ENCENDIDAS")
    
    def apagar_luces(self):
        if self.luces_encendidas:
            self.luces_encendidas = False
            print("LUCES APAGADAS")

if __name__ == "__main__":
    temp = SensorTemperatura(id="T1")
    vib = SensorVibracion(id="V1")
    mov = SensorMovimento(id="M1")

    email = NotificadorEmail("example@example.com")
    webhook = NotificadorWebhook("http://webhook.com")

    gestor = GestorAlertas([temp, vib, mov], [email, webhook])
    controlador = ControladorLuces(mov)

    print("\nAgregando lecturas de temperatura...")
    for val in [90, 104, 156]:
        temp.leer(val)
        print(f" Lectura T: {val}°C -> Promedio: {temp.promedio:.2f}°C")

    print("\nAgregando lecturas de vibración...")
    for val in [0.5, 1.0, 2.0]:
        vib.leer(val)
        print(f" Lectura V: {val} -> Promedio: {vib.promedio:.2f}")

    print("\nAgregando lecturas de movimiento...")
    for val in [0.0, 1.0, 0.2, 1.5]:
        mov.leer(val)
        print(f" Lectura M: {val} -> Promedio: {mov.promedio:.2f}")
    
    print("\nEvaluando alertas")
    gestor.evaluar_y_notificar()

    print("\nControlador de luces")
    controlador.verificar_movimiento()