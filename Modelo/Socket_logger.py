import logging
import socketio
import asyncio
from colorama import Fore, Style, init


# Define el nuevo nivel de registro "PROCESANDO"
PROCESANDO = 25
logging.addLevelName(PROCESANDO, "PROCESANDO")

loger_loops = asyncio.new_event_loop()

LEVEL_COLORS = {
    'DEBUG': Fore.BLUE,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.MAGENTA,
    'PROCESANDO': Fore.CYAN  # Color para el nuevo nivel "PROCESANDO"
}

# Inicializar colorama
init(autoreset=True)
class PlantaFormat(logging.Formatter):    
    # Agregar color naranja (una combinación de rojo y amarillo)
    ORANGE = '\033[38;5;214m'  # Código ANSI para un color cercano al naranja

    def format(self, record):
        record.name = Fore.BLUE + record.name.split('.')[0] + Style.RESET_ALL
        level_color = LEVEL_COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = level_color + record.levelname + Style.RESET_ALL
        if hasattr(record, 'teamname'):
            record.teamname = self.ORANGE + record.teamname + Style.RESET_ALL
        else:
            record.teamname = ''
        return super().format(record)

class LoggerFormat(logging.Formatter):
    
    def format(self, record):
        # Colorear el nombre del logger
        record.name = Fore.BLUE + record.name + Style.RESET_ALL
        # Colorear el nivel del log según el tipo
        level_color = LEVEL_COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = level_color + record.levelname + Style.RESET_ALL
        return super().format(record)



class SocketLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET, sio=None, loop=None,planta=None):
        super().__init__(name, level)
        self.sio = sio
        self.handler = logging.StreamHandler()
        formatter = LoggerFormat('[%(levelname)s][%(name)s]: %(message)s')
        self.socketio_handler=None
        self.handler.setFormatter(formatter)
        self.loop=loop
        self.planta=planta
        self.addHandler(self.handler)
    
    def procesando(self, msg, *args, **kwargs):
        # Método para registrar mensajes con el nivel personalizado "PROCESANDO"
        if self.isEnabledFor(PROCESANDO):
            self._log(PROCESANDO, msg, args, **kwargs)
    
    def setFormatter(self,formato,formar= None):
        formatter = formar(formato) if formar else LoggerFormat(formato)
        if self.sio is not None:
            self.socketio_handler.setFormatter(formatter)
        self.handler.setFormatter(formatter)
    
    def addHandler(self, handler):
        self.handler = handler  # Corrección aquí
        # Método para agregar un manejador al logger
        super().addHandler(handler)
        # Si se proporciona un socket.io, agregamos un SocketIOHandler al logger
        if self.sio is not None:
            self.socketio_handler = SocketIOHandler(self.sio,loop=self.loop,planta=self.planta)
            self.socketio_handler.setLevel(logging.DEBUG)
            self.socketio_handler.setFormatter(self.handler.formatter)
            super().addHandler(self.socketio_handler)


class SocketIOHandler(logging.Handler):
    def __init__(self, sio, event_name='log_message', loop=None,planta=None):
        super().__init__()
        self.sio = sio
        self.planta=planta
        self.event_name = event_name
        self.loop = loop or asyncio.get_event_loop()

    async def emit_log_message(self, level, message, msg_format):
        # Método para emitir un mensaje de registro a través de Socket.IO
        await self.sio.emit(self.event_name, {
            'level': level,
            'message': message,
            'msg_format': msg_format
        })

    def emit(self, record):
        if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL or record.levelno == logging.WARNING:
            if self.planta is not None:
                self.planta.error()
        # Método para enviar registros a través de Socket.IO
        log_entry = self.format(record)
        asyncio.run_coroutine_threadsafe(
            self.emit_log_message(record.levelno, record.msg, log_entry),
            self.loop
        )