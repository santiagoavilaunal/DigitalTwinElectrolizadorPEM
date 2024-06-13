from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
import socketio
from Modelo.Modelo import Planta
import json
import numpy as np
import os
from Modelo.Socket_logger import SocketLogger
import asyncio
import uvicorn
from uvicorn.loops.asyncio import asyncio_setup
import logging
import time
import threading


# Set some basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s]:\t%(message)s"
)


PLANTAS={}
# Inicializar FastAPI y Socket.IO
app = FastAPI()

loop=None
if os.environ.get('WEB_HOST',None) is None:
    sio = socketio.AsyncServer(async_mode="asgi")
else:
    sio = socketio.AsyncServer(async_mode="asgi",cors_allowed_origins="https://5050-"+os.environ.get('WEB_HOST',None))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://5050-"+os.environ.get('WEB_HOST',None)],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
socket_app = socketio.ASGIApp(sio, app)


logger=None

planta=None
calculando=False

# Definir la clase NumpyEncoder para la serialización personalizada
class NumpyEncoder(json.JSONEncoder):
    """Clase especial de codificador JSON para tipos de datos de numpy"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()  # Convertir el arreglo de numpy a lista
        elif isinstance(obj, np.int32):
            return int(obj) # Convertir el arreglo de numpy a lista
        return super(NumpyEncoder, self).default(obj)

# Ruta para servir archivos estáticos
@app.get("/{filename}")
async def get_static_files(filename: str):
    print(f'filename: {filename}')
    try:
        return FileResponse(f"static/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
@app.get("/libs/{filename}")
async def get_static_files(filename: str):
    print(f'filename: {filename}')
    try:
        return FileResponse(f"static/libs/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.get("/assets/{filename}")
async def get_static_files(filename: str):
    print(f'filename: {filename}')
    try:
        return FileResponse(f"static/assets/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def get_index():
    return "static/index.html"

# Evento de conexión de Socket.IO
@sio.on("connect")
async def connect(sid, environ):
    logger.info(f"Conectado: {sid}")

# Evento de desconexión de Socket.IO
@sio.on("disconnect")
async def disconnect(sid):
    logger.info(f"Desconectado: {sid}")

# Evento personalizado de Socket.IO

@sio.on("test")
async def test(sid, data):
    logger.info(f"mensaje")

@sio.on("lazo")
async def lazo(sid, data):
    global planta
    if planta.loops.get(data['loop'],None) is not None:
        planta.loops[data['loop']]=data['value']

@sio.on("valve")
async def valve(sid, data):
    global planta, calculando, logger
    Q=planta.valvulas[data['valvula']].Q(data['apertura'])

    await sio.emit('valve',data=json.dumps(planta.valvulas[data['valvula']].printData(), cls=NumpyEncoder), room=sid)

@sio.on('dinamico_activar')
async def dinamico_activar(sid, data):
    global planta, calculando, logger
    if calculando:
        return
    
    planta.dinamico_activo=True if data['activo']=='on' else False
    
    if planta.dinamico_activo:
        planta.dt=data['dt']
        thread = threading.Thread(target=Planta_dinamics, args=(sid,))
        thread.start()

    pass

@sio.on("modificar_setpoint")
async def modificar_setpoint(sid, data):
    global planta, calculando, logger
    if calculando:
        logger.info('Hay otro proceso')
        return
    
    try:
        if planta is None:
            planta = Planta(**data, sio=sio)
        else:
            # Update the planta values
            planta.I = data['I']
            planta.Q = data['Q']
            planta.T13 = data['T13']
            planta.Pca = data['Pca']
            planta.Pan = data['Pan']
    except:
        logger.warning('No se pudo actualizar los valores')
                

@sio.on("estacionario_calcular")
async def estacionario_calcular(sid, data):
    global planta, calculando, logger
    if calculando:
        logger.info('Hay otro proceso')
        return
    
    # Flag to check if values have changed
    valores_cambiaron = False
    
    try:
        if planta is None:
            planta = Planta(**data, sio=sio)
            valores_cambiaron = True
        else:
            planta.dinamico_activo=False
            planta.reset_dinamics()
            # Check if any value has changed
            if (planta.I != data['I'] or
                planta.Q != data['Q'] or
                planta.T13 != data['T13'] or
                planta.Pca != data['Pca'] or
                planta.Pan != data['Pan']):
                
                # Update the planta values
                planta.I = data['I']
                planta.Q = data['Q']
                planta.T13 = data['T13']
                planta.Pca = data['Pca']
                planta.Pan = data['Pan']
                valores_cambiaron = True
                
    except Exception as error:
        calculando = False
        logger.warning(f"Error: {error}")
        planta = None
        await sio.emit("estacionario_resultado", json.dumps({'error': str(error)}), room=sid)
        return
    
    # Only start the thread if values have changed
    if valores_cambiaron:
        calculando = True
        thread = threading.Thread(target=Planta_tasks, args=(sid,))
        thread.start()
    else:
        logger.info('No hay cambios en los valores')
        await sio.emit("estacionario_resultado", json.dumps(planta.printData(), cls=NumpyEncoder), room=sid)




async def background_task():
    while True:
        await asyncio.sleep(1)

def send_msg(event,msg,room):
    asyncio.set_event_loop(loop)
    asyncio.run_coroutine_threadsafe(
        sio.emit(event, msg, room=room),
        loop
    )

def Planta_dinamics(sid):
    global calculando, planta
    while planta.dinamico_activo:
        res_time=planta.dt
        try:
            res_time = planta.dinamico_step()
            if res_time>0:
                datos_resultado = planta.printData()
                send_msg("dinamics_resultado", json.dumps(datos_resultado, cls=NumpyEncoder), room=sid)
            else:
                logger.warning(f"Error:")
        except Exception as error:
            logger.warning(f"Error: {error}")
            planta.dinamico_activo=False
        finally:
            calculando = False
            if 1-res_time>=0:
                time.sleep(res_time)
            else:
                pass


def Planta_tasks(sid):
    global calculando, planta
    try:
        resultado = planta.calcular()
        if resultado:
            datos_resultado = planta.printData()
            send_msg("estacionario_resultado", json.dumps(datos_resultado, cls=NumpyEncoder), room=sid)
        else:
            send_msg("estacionario_resultado", json.dumps({'error': 'no_convergió'}), room=sid)
    except Exception as error:
        logger.warning(f"Error: {error}")
        planta = None
        send_msg("estacionario_resultado", json.dumps({'error': str(error)}), room=sid)
    finally:
        calculando = False



@app.on_event("startup")
async def startup_event():
    global loop, logger
    loop = asyncio.get_event_loop()
    logger=SocketLogger('Server',sio=sio,loop=loop)

@app.on_event("shutdown")
async def shutdown_event():
    global thread
    if thread:
        thread.join()

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=5050)