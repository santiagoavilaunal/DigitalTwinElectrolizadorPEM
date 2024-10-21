import sys
sys.path.append(r'../')
from Modelo.Equipos import ElectrolizadorPEM,FlashTanque, IntercambiadorCalor
from Modelo.Accesorios import Valvula,PIDController
from Modelo.Termodinamica import Termo_Propiedades,BinarieVLE
from Modelo.Flujos import Flujo
from Modelo.Socket_logger import SocketLogger,PlantaFormat
import numpy as np
import json
import time



class Planta:
    def __init__(self,T13,Q,I,Pca,Pan,sio=None,tol=1e-8):
        
        self.logger = SocketLogger('Planta',sio=sio,planta=self)
        self.logger.setFormatter('[%(levelname)s][%(name)s]: %(message)s',PlantaFormat)
        #self.logger.setLevel(logging.DEBUG)
        self.sio=sio

        self.dt=None
        self.dinamico_activo=True


        jo_an2,la=9.87785e-09, 0.55139
        area=290
        area=290
        dm=0.0178

        di = 19.05e-3  # Diámetro interno del tubo en metros (19.05 mm)
        Di = 205e-3    # Diámetro de la coraza en metros (205 mm)
        L = 1000e-3     # Longitud del tubo en metros (500 mm)
        nt = 30        # Número de tubos
        Es=['H2O','H2','O2']
        self.tol=tol
        
        self.flujos = {f'F{i}': Flujo(T13, Pca, 1, [1, 0, 0], Es, name=f'F{i}', tol=self.tol) for i in range(1, 15)}
        
        self.equipos = {
            'EK101': ElectrolizadorPEM(area, dm, jo_an2, la, 60, 1, [
                [self.flujos['F13']],
                [self.flujos['F5'], self.flujos['F6']]
            ], tol=self.tol, logger=self.get_logger('EK101'), name='EK101'),
            'V102': FlashTanque([
                [self.flujos['F6']],
                [self.flujos['F7'], self.flujos['F3']]
            ], logger=self.get_logger('V102'), name='V102',d=0.25,h=1,hL=0.3,tol=self.tol),
            'V101': FlashTanque([
                [self.flujos['F5'], self.flujos['F7'], self.flujos['F1']],
                [self.flujos['F4'], self.flujos['F2']]
            ], logger=self.get_logger('V101'),  name='V101',d=0.5,h=2.2,hL=0.5,tol=self.tol),
            'E101': IntercambiadorCalor([
                [self.flujos['F8'], self.flujos['F4']],
                [self.flujos['F9'], self.flujos['F10']]
            ], di, Di, L, nt, logger=self.get_logger('E101'), name='E101')
        }

        self.valvulas={
            'VC101':Valvula(20,80,'VC101',flujos=[self.flujos['F8']],dP=0.5e5),
            'VC102':Valvula(0.1,80,'VC102',flujos=[self.flujos['F1']],dP=0.5e5),
            'VC103':Valvula(0.5,80,'VC103',flujos=[self.flujos['F7']],dP=0.5e5),
            'VC104':Valvula(20,80,'VC104',flujos=[self.flujos['F13']],dP=0.5e5),
        }

        self.PIDControllers={
            'VC101':PIDController(-0.5/0.2,-0.5,0, 0, offset=0, min_Mv=0.01, max_Mv=95, activo=False),
            'VC102':PIDController(-500/0.2,-120,0, 0.3, offset=0.3, min_Mv=0.01, max_Mv=97, activo=False),
            'VC103':PIDController(-500/0.2,-120,0, 0.3, offset=0.3, min_Mv=0.01, max_Mv=97, activo=False),
            'VC105':PIDController(-1/14,-0.005,0, 0, offset=0, min_Mv=0.0, max_Mv=200, activo=False),
            'VC106':PIDController(-20/14,-0.1,0, 0, offset=0, min_Mv=0.0, max_Mv=200, activo=False)
        }
        
        self.T13=T13
        self.Q=Q
        self.Pca=Pca
        self.Pan=Pan
        self.I=I
        self.equipos['EK101'].corriente_costante=True
    
    def get_logger(self, equipo_name):
        equipo_logger = SocketLogger(f'Planta.{equipo_name}',sio=self.sio,planta=self)
        equipo_logger.propagate = False
        equipo_logger.setFormatter(f'[%(levelname)s][%(name)s][%(teamname)s]: %(message)s',PlantaFormat)
        #equipo_logger.setLevel(logging.DEBUG)
        # Añadir atributo `teamname` al registro de log
        equipo_logger.addFilter(lambda record: setattr(record, 'teamname', equipo_name) or True)
        return equipo_logger
    
    def error(self):
        self.dinamico_activo=False
    
    @property
    def T13(self):
        return self.flujos['F13'].T

    @T13.setter
    def T13(self, value):
        self.PIDControllers['VC101'].setpoint=value
        self.flujos['F13'].T = value
    
    @property
    def Q(self):
        return self._Q

    @Q.setter
    def Q(self, value):
        self._Q=value
        F=self._Q*Termo_Propiedades('Dmolar',self.T13,self.Pca)[0]/60000
        self.flujos['F13'].F = F
    
    @property
    def Pca(self):
        return self.flujos['F5'].P

    @Pca.setter
    def Pca(self, value):
        self.PIDControllers['VC105'].setpoint=value*1e-5
        self.flujos['F5'].P = value
    
    @property
    def Pan(self):
        return self.flujos['F6'].P

    @Pan.setter
    def Pan(self, value):
        self.PIDControllers['VC106'].setpoint=value*1e-5
        self.flujos['F6'].P = value
    
    @property
    def I(self):
        return self.equipos['EK101'].I

    @I.setter
    def I(self, value):
        self.equipos['EK101'].I = value
        
    
    def calcular(self):
        F40=self.Q*Termo_Propiedades('Dmolar',self.T13,self.Pca)[0]/60000
        T130=self.T13
        self.flujos['F1'].T=20+273.15
        self.flujos['F1'].F=1
        #self.flujos['F3'].update()
        self.flujos['F1'].update()

        self.flujos['F13'].F=F40
        self.flujos['F13'].P=self.Pca
        result_binarie=BinarieVLE(self.flujos['F13'].T,self.flujos['F13'].P,['H2O','O2'], tol=self.tol)
        self.flujos['F13'].z=[result_binarie['c'][0][0],0,result_binarie['c'][0][1]]
        self.flujos['F13'].update()

        self.flujos['F4'].F=F40
        self.flujos['F4'].P=self.Pca
        result_binarie=BinarieVLE(self.flujos['F13'].T,self.flujos['F13'].P,['H2O','O2'], tol=self.tol)
        self.flujos['F4'].z=[result_binarie['c'][0][0],0,result_binarie['c'][0][1]]
        self.flujos['F4'].update()

        error1=1
        z0=self.flujos['F13'].z
        la=0.5
        F10=1
        for i in range(30):
            self.equipos['EK101'].calcular_temperatura_salida()
            self.equipos['V102'].calcular_temperatura_salida()

            self.flujos['F1'].F=self.flujos['F2'].F_get(0)+self.flujos['F3'].F_get(0)+(self.flujos['F13'].F_get(0)-self.flujos['F5'].F_get(0)-self.flujos['F6'].F_get(0))
            self.flujos['F1'].update()


            self.equipos['V101'].calcular_temperatura_salida()
            
            error=np.abs(self.flujos['F1'].F-self.flujos['F2'].F-self.flujos['F3'].F-(self.flujos['F13'].F_get(2)-self.flujos['F5'].F_get(2)-self.flujos['F6'].F_get(2)))
            self.logger.procesando(f'Error: {error}')
            if error<1e-5:
                if(self.finis_calc()):
                    self.logger.info(f'El balance de materia ha convergido en la iteración {i+1}.')
                    return True
                else:
                    return False
            
            if np.abs(error1-error)<1e-9:
                self.logger.warning(f'No convergio despues de {i+1} iteraciones')
                return False
            
            self.flujos['F1'].P=self.equipos['V101'].P
            self.flujos['F1'].update()
            
            self.flujos['F13'].F=F40
            self.flujos['F13'].T=T130
            self.flujos['F13'].z=self.flujos['F4'].z
            self.flujos['F13'].update()
            error1=error
            
        
        self.logger.warning(f'No convergio despues de {i+1} iteraciones')
        return False
    
    def finis_calc(self):
        self.flujos['F10'].T=self.flujos['F13'].T
        self.flujos['F8'].F=self.flujos['F13'].F
        self.flujos['F8'].P=2*1e+5
        self.flujos['F8'].T=10+273.15
        self.flujos['F8'].update()
        result = self.equipos['E101'].calcular_flujo_CW()

        if result:
            self.valvulas['VC102'].Ap()
            self.valvulas['VC103'].Ap()
            self.valvulas['VC104'].Ap()

            self.PIDControllers['VC101'].setpoint=self.T13
            self.PIDControllers['VC101'].offset=self.valvulas['VC101'].Ap()

            self.PIDControllers['VC103'].offset=self.valvulas['VC103'].Ap()

            self.PIDControllers['VC105'].setpoint=self.Pca*1e-5
            self.PIDControllers['VC105'].offset=self.flujos['F2'].F

            self.PIDControllers['VC106'].setpoint=self.Pca*1e-5
            self.PIDControllers['VC106'].offset=self.flujos['F3'].F
        #self.equipos['E101'].calcular_temperatura_salida()
        return result
    
    def dinamico_step(self):
        if not self.dinamico_activo or self.dt is None or self.dt <= 0:
            return -1  # Retorna 0 si no se debe realizar el cálculo
        
        start_time = time.time()  # Registra el tiempo de inicio del cálculo

        segment_size = 10
        num_full_segments = int(self.dt // segment_size)
        remaining_segment = self.dt % segment_size
        
        # Iterar sobre los segmentos completos
        for i in range(num_full_segments):
            self.perform_dynamic_step(segment_size)

        # Manejar el segmento restante, si lo hay
        if remaining_segment > 0:
            self.perform_dynamic_step(remaining_segment)

        end_time = time.time()  # Registra el tiempo de finalización del cálculo
        return end_time - start_time  # Devuelve la diferencia de tiempo entre el inicio y el final del cálculo

    def perform_dynamic_step(self, dt):
        self.equipos['EK101'].dinamico_step(dt)
        self.equipos['V102'].dinamico_step(dt)
        self.equipos['V101'].dinamico_step(dt)
        #self.equipos['E101'].dinamico_step(dt)
        self.equipos['E101'].calcular_temperatura_salida()
        self.flujos['F13'].T = self.flujos['F10'].T
        self.flujos['F13'].F = self.flujos['F10'].F
        self.flujos['F13'].z = self.flujos['F10'].z
        self.flujos['F13'].update()

        if self.PIDControllers['VC101'].activo:
            self.valvulas['VC101'].Q(self.PIDControllers['VC101'].calculate(self.flujos['F13'].T,dt))
        
        if self.PIDControllers['VC103'].activo:
            self.valvulas['VC103'].Q(self.PIDControllers['VC103'].calculate(self.equipos['V102'].Liqlevel,dt))

        if self.PIDControllers['VC102'].activo:
            self.valvulas['VC102'].Q(self.PIDControllers['VC102'].calculate(self.equipos['V101'].Liqlevel,dt))
            
        if self.PIDControllers['VC105'].activo:
            self.flujos['F2'].F=self.PIDControllers['VC105'].calculate(self.equipos['V102'].P*1e-5,dt)
            self.flujos['F2'].update()
        
        if self.PIDControllers['VC106'].activo:
            self.flujos['F3'].F=self.PIDControllers['VC106'].calculate(self.equipos['V101'].P*1e-5,dt)
            self.flujos['F3'].update()



        for equipo in self.equipos:
            for key in self.equipos[equipo].dinamico:
                for traza in self.equipos[equipo].dinamico[key]['trazas']:
                    if len(traza['x'])>500:
                        traza['x'].pop(0)
                        traza['y'].pop(0)

    def reset_dinamics(self):
        for equipo in self.equipos:
            for key in self.equipos[equipo].dinamico:
                for traza in self.equipos[equipo].dinamico[key]['trazas']:
                    traza['x']=[]
                    traza['y']=[]
        
        for loop in self.PIDControllers.keys():
            self.PIDControllers[loop].activo=False


    def printData(self):
        return {
            'Equipos':{key: self.equipos[key].printData() for key in self.equipos},
            'Flujos':{key: self.flujos[key].printData() for key in self.flujos},
            'Valvulas': {key: {**self.valvulas[key].printData(), 'control': self.PIDControllers[key].printData() if key in self.PIDControllers else None} for key in self.valvulas},
            'T13':self.T13,
            'Q':self.Q,
            'Pca':self.Pca,
            'Pan':self.Pan,
            'I':self.I,
            'tol':self.tol
        }
    
    def to_json(self):
        return json.dumps(self.printData())
    
    def __str__(self):
        """
        Método para obtener una representación en cadena de caracteres del electrolizador.
        """
        return str(self.printData())

    def __repr__(self):
        """
        Método para obtener una representación del electrolizador.
        """
        return str(self.printData())