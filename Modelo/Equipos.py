import sys
sys.path.append(r'../')
from Modelo.Termodinamica import BinarieVLE, Sistema,Termo_Propiedades,R,Termo_state
from Modelo.Flujos import Flujo
import numpy as np
import scipy.optimize as sop
import scipy.integrate as sint
import json
from Modelo.Socket_logger import SocketLogger

jo_an2=7.3849e-09
la=0.5514


#Submodelo electroquimico
class CeldaElectroquimica:
    CONSTANTE_FARADAY = 96485.3321233100184  # Constante de Faraday en C/mol
    
    def __init__(self, area, espesor_membrana, densidad_corriente_intercambio, exponente_presion):
        self.area = area 
        self.espesor_membrana = espesor_membrana
        self.densidad_corriente_intercambio = densidad_corriente_intercambio
        self.exponente_presion = exponente_presion

    def voltaje_estandar(self, T):
        return np.sum(Termo_Propiedades('Gmolar', T, 101325) * np.array([-1, 1, 0.5])) / (2 * self.CONSTANTE_FARADAY)

    def voltaje_reversible(self, T, f):
        return self.voltaje_estandar(T) + ((R * T) / (2 * self.CONSTANTE_FARADAY)) * np.log((f[1] * np.sqrt(f[2]) / (f[0])) * np.sqrt(1e-5))

    def densidad_corriente_anodica(self, T, P):
        return self.densidad_corriente_intercambio * ((P * 1E-5 / 25) ** self.exponente_presion) * np.exp(-52994 * (1 / T - 1 / 298.15) / R)  # A/cm^2

    def voltaje_activacion(self, I, T, P):
        j = I / self.area
        return (R * T) * np.arcsinh(j / (2 * self.densidad_corriente_anodica(T, P))) / (2 * 0.7353 * self.CONSTANTE_FARADAY)  # V

    def omm_sig(self, T):
        return 0.1031 * np.exp(-(10536 / R) * (1 / T - 1 / 298.15))

    def voltaje_ohmico(self, I, T):
        conductividad = 0.1031 * np.exp(-(10536 / R) * (1 / T - 1 / 298.15))
        return self.espesor_membrana * I / (self.area * conductividad)

    def voltaje(self, I, T, P_an, P_ca, y, phi):
        f = np.array([P_ca, P_an, P_ca]) * y * phi #coeficientes de fugaidad
        return self.voltaje_reversible(T, f) + self.voltaje_activacion(I, T, P_ca) + self.voltaje_ohmico(I, T)

    def corriente(self, V, T, P_an, P_ca, y, phi):
        def error_voltaje(corriente):
            voltaje_calculado = self.voltaje(corriente[0], T, P_an, P_ca,y,phi)
            return voltaje_calculado - V
        
        estimacion_inicial = np.array([1.0]) * self.area
        solucion = sop.fsolve(error_voltaje, x0=estimacion_inicial)
        return solucion[0]


# Electrolizador PEM
class ElectrolizadorPEM:
    CONSTANTE_FARADAY = 96485.3321233100184  # Constante de Faraday en C/mol
    UTH = 1.48  # Voltaje termoneutral en V

    def __init__(self, area_celda, espesor_membrana, densidad_corriente_intercambio, exponente_presion,num_celdas, eficiencia, flujos,name='',logger=None, tol=1e-9):
        
        """
        Constructor de la clase ElectrolizadorPEM.

        Parámetros:
        - area_celda: Área de la celda en m².
        - espesor_membrana: Espesor de la membrana en m.
        - densidad_corriente_intercambio: Densidad de corriente de intercambio en A/m².
        - exponente_presion: Exponente de la presión.
        - num_celdas: Número de celdas en el electrolizador.
        - eficiencia: Eficiencia del electrolizador.
        - flujos: Lista de flujos de entrada y salida.
        - tol: Tolerancia para cálculos numéricos (predeterminado a 1e-9).
        """
        
        self.flujos = flujos
        self.celda = CeldaElectroquimica(area_celda, espesor_membrana, densidad_corriente_intercambio, exponente_presion)
        self.num_celdas = num_celdas  # Número de celdas en el electrolizador
        self.eficiencia = eficiencia
        self.presion_anodo = flujos[1][1].P  # Presión en anódica
        self.presion_catodo = flujos[1][0].P  # Presión en catódica
        self.tol = tol
        self.T=None
        self.I=None
        self.V=None
        self.corriente_costante=True
        self.name=name
        self.logger = logger or SocketLogger('ElectrolizadorPEM')
        self.dinamico={
            'T': {'title' : 'Temperatura','xlabel': 'Tiempo (min)','ylabel1': 'Temperatura',
                    'trazas':[
                        {
                            'name': 'Temperatura',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#ff5757',
                        }
                    ],
                    'T0':self.T
                },
            'V': {'title' : 'Voltaje y Corriente en el stack','xlabel': 'Tiempo (min)','ylabel1': 'Voltaje','ylabel2': 'A',
                    'trazas':[
                        {
                            'name': 'Voltage',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#e8eb34',
                        },
                        {
                            'name': 'Corriente',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#cc34eb',
                        }
                    ],
                    'V0':self.T,
                    'I0':self.T
                }
        }

    def calcular_flujos(self):
        """
        Calcular los flujos de fase en el electrolizador.
        """
        nd = 0.0134 * self.T + 0.03  # Cálculo del coeficiente osmoeléctrico
        n = self.I * self.num_celdas * self.eficiencia / (2 * self.CONSTANTE_FARADAY)  # Moles reaccionadas por ley de Faraday
        Fnd = nd * np.array([1, 0, 0]) * 2 * n  # Flujo molar de agua transportado en la membrana PEM por el fenómeno osmoeléctrico

        F0 = self.flujos[0][0].F * self.flujos[0][0].z  # Flujo inicial
        Fout1 = F0 - Fnd + n * np.array([-1, 0, 0.5])  # Flujo de salida 1
        Fout2 = Fnd + n * np.array([0, 1, 0])  # Flujo de salida 2

        # Actualizar propiedades del flujo anódico (1)
        self.flujos[1][0].F = Fout1.sum()
        self.flujos[1][0].z = Fout1 / Fout1.sum()
        self.flujos[1][0].T = self.T
        self.flujos[1][0].update()

        # Actualizar propiedades del flujo catódico (2)
        self.flujos[1][1].F = Fout2.sum()
        self.flujos[1][1].z = Fout2 / Fout2.sum()
        self.flujos[1][1].T = self.T
        self.flujos[1][1].update()

    def balance_energia(self):
        """
        Calcular el balance de energía del electrolizador.
        """
        balance_energia = (self.V / self.num_celdas) * self.I * self.num_celdas + self.flujos[0][0].H - self.flujos[1][0].H - self.flujos[1][1].H
        return balance_energia
    
    def calcular_voltaje(self):
        """
        Calcular  tensión (V) a una corriende aplicada.
        """
        self.presion_anodo=self.flujos[1][1].P
        self.presion_catodo=self.flujos[1][0].P
        # Cálculos de equilibrio de solubilidad H2 y O2
        s_ca = BinarieVLE(self.T, self.presion_catodo, ['H2O', 'O2'])
        y1 = s_ca['c'][0]
        s_an = BinarieVLE(self.T, self.presion_anodo, ['H2O', 'H2'])
        y2 = s_an['c'][0]

        # Crear sistemas de flujo líquido con fracciones molares
        EOS_ca=Sistema(['H2O', 'O2'],phase='Liq')
        s_ca=EOS_ca.update(self.T, self.presion_catodo,z=y1)

        EOS_an=Sistema(['H2O', 'H2'],phase='Liq')
        s_an = EOS_an.update(self.T, self.presion_anodo,z=y2)

        # Calcular coeficiente de fugacidad
        phi = np.array([s_ca['phi'][0], s_an['phi'][1], s_ca['phi'][1]])
        y = np.array([y1[0], y2[1], y1[1]])
        self.V=self.celda.voltaje(self.I,self.T,self.presion_anodo,self.presion_catodo,y,phi)*self.num_celdas


    def calcular_corriente(self):
        """
        Calcular la corriente (I) necesaria para obtener la tensión (V) deseada.
        """
        self.presion_anodo=self.flujos[1][1].P
        self.presion_catodo=self.flujos[1][0].P
        # Cálculos de equilibrio de solubilidad H2 y O2
        s_ca = BinarieVLE(self.T, self.presion_catodo, ['H2O', 'O2'])
        y1 = s_ca['c'][0]
        s_an = BinarieVLE(self.T, self.presion_anodo, ['H2O', 'H2'])
        y2 = s_an['c'][0]

        # Crear sistemas de flujo líquido con fracciones molares
        EOS_ca=Sistema(['H2O', 'O2'],phase='Liq')
        s_ca=EOS_ca.update(self.T, self.presion_catodo,z=y1)

        EOS_an=Sistema(['H2O', 'H2'],phase='Liq')
        s_an = EOS_an.update(self.T, self.presion_anodo,z=y2)

        # Calcular coeficiente de fugacidad
        phi = np.array([s_ca['phi'][0], s_an['phi'][1], s_ca['phi'][1]])
        y = np.array([y1[0], y2[1], y1[1]])
        

        # Calcular la corriente (I) usando el método de la celda electroquímica
        self.I = self.celda.corriente(
            self.V / self.num_celdas,
            self.T,
            self.presion_anodo,
            self.presion_catodo,
            y, phi
        )

    def calcular_temperatura_salida(self):
        """
        Calcular la temperatura de salida (Tout) del electrolizador.
        """
        def resolver_ecuacion_temperatura(temperatura):
            self.T = temperatura[0]  # Establecer la temperatura actual
            if self.corriente_costante:
                self.calcular_voltaje()
            else:
                self.calcular_corriente()  # Calcular la corriente necesaria
            self.calcular_flujos()  # Calcular el flujo
            return self.balance_energia()  # Calcular el balance de energía

        # Resolver para encontrar la temperatura de salida usando el método de Newton
        sop.fsolve(resolver_ecuacion_temperatura, x0=self.flujos[0][0].T+1)
    
    def dif_dt(self):
        Cth=162116 #j/K^-1
        self.calcular_voltaje()
        self.calcular_flujos()
        dT_dt=np.round(self.balance_energia(),2)/Cth
        return dT_dt
    
    def dinamico_step(self,dt):
        if len(self.dinamico['T']['trazas'][0]['x'])==0:
            for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x'].append(dt/60)
            
            self.dinamico['T']['T0']=self.T
            self.dinamico['V']['V0']=self.V
            self.dinamico['V']['I0']=self.I
        else:
            for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x'].append(dt/60+traza['x'][-1])

        self.T=self.dif_dt()*dt+self.T
        self.dinamico['T']['trazas'][0]['y'].append(self.T-273.15)
        self.dinamico['V']['trazas'][0]['y'].append(self.V)
        self.dinamico['V']['trazas'][1]['y'].append(self.I)

        if self.V*self.I>45000:
            self.logger.error('El potencial eléctrico supera los 45 kW.')
        
        if self.presion_anodo>35*1e5:
             self.logger.error('El electrolizador está operando a una presión mayor de 35 bar en el ánodo.')
            
        if self.presion_catodo>35*1e5:
             self.logger.error('El electrolizador está operando a una presión mayor de 35 bar en el cátodo.')
    
    def reset_dinamics(self):
        self.T=self.dinamico['T']['T0']
        self.V=self.dinamico['V']['V0']
        self.I=self.dinamico['V']['I0']
    
    def dete_data_dinamic(self):
        for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x']=[]
                    traza['y']=[]
        self.reset_dinamics()

    def printData(self):
        """
        Método para obtener una representación en diccionario de los datos del electrolizador.
        """
        return {
            'name':self.name,
            'flujos': {
                'Entrada': {Fi.name: Fi.printData() for Fi in self.flujos[0]},
                'Salida' : {Fi.name: Fi.printData() for Fi in self.flujos[1]}
            },
            'num_celdas': self.num_celdas,
            'eficiencia': self.eficiencia,
            'presion_anodo': self.presion_anodo,
            'presion_catodo': self.presion_catodo,
            'T': self.T,
            'I': self.I,
            'V': self.V,
            'dinamico':self.dinamico
        }
    
    def to_json(self):
        """
        Método para convertir los datos del electrolizador en un diccionario JSON.
        """
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


#Tanques de separacion
class FlashTanque:
    def __init__(self, flujos,d=None,h=None,hL=None,name='',logger=None):
        self.flujos = flujos
        self.T=None
        self.name=name
        self.d=d
        self.h=h
        self.V=None
        self.Liqlevel=hL
        self.flujo_temporal=None
        self.logger = logger or SocketLogger('FlashTanque')
        self.dinamico={
            'T':{'title' : 'Temperatura','xlabel': 'Tiempo (min)','ylabel1': 'Temperatura',
                    'trazas':[
                        {
                            'name': 'Temperatura',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#00f7ff',
                        }
                    ],
                    'T0':self.T
                },
            'P':{'title' : 'Presión','xlabel': 'Tiempo (min)','ylabel1': 'bar',
                    'trazas':[
                        {
                            'name': 'Presión',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#ffffff',
                        }
                    ],
                    'P0':self.T
                },
            'L':{'title' : 'Nivel del liquido','xlabel': 'Tiempo (min)','ylabel1': 'm',
                    'trazas':[
                        {
                            'name': 'Nivel del liquido',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#03fcfc',
                        }
                    ],
                    'L0':None
                },
            'F':{'title' : 'Flujo gas','xlabel': 'Tiempo (min)','ylabel1': 'kg/h','ylabel2': 'mol/mol',
                    'trazas':[
                        {
                            'name': 'Flujo de gas',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#00ffdd',
                        },
                        {
                            'name': 'Concentracion H2',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#00ff88',
                        }
                    ],
                    'F0':self.T,
                    'n_gas':0,
                    'n_liq':0,
                    'x':np.array([1,0,0]),
                    'y':np.array([1,0,0]),
                },
        }

        if self.d is not None and self.h is not None:
            self.Vol()
    
    # Método para calcular el balance de energía del tanque
    def balance_energia(self):
        # Calcular la energía total de entrada (H_entrada)
        H_entrada = np.sum([Fi.H for Fi in self.flujos[0]])
        
        # Calcular la energía total de salida (H_salida)
        H_salida = self.flujos[1][1].H + self.flujos[1][0].H
        
        # Calcular el balance de energía
        return np.round(H_entrada - H_salida)
    
    # Método para calcular los flujos de salida del tanque
    def calcular_flujos(self):
        # Determinar la presión mínima de los flujos de entrada
        self.P = np.min([Fi.P for Fi in self.flujos[0]])
        
        # Calcular flujos totales y composiciones ponderadas
        F, z = self.calcular_flujo_total_y_composicion()
        FL, zL = self.calcular_flujo_total_y_composicion(q=0)
        
        # Crear un flujo temporal (F_tem) para determinar la fase de salida
        F_tem = self.crear_flujo_temporal(F, z)
        self.flujo_temporal=F_tem
        
        # Asignar temperatura y presión a los flujos de salida
        self.asignar_propiedades_flujos_salida()
        
        # Determinar el comportamiento de fase de los flujos de salida
        self.determinar_comportamiento_fase_salida(F_tem, F, FL, zL)
        
        # Actualizar propiedades de los flujos de salida
        self.actualizar_propiedades_flujos_salida()
    
    # Método para calcular flujos totales y composiciones ponderadas
    def calcular_flujo_total_y_composicion(self, q=None):
        F = np.sum([Fi.F for Fi in self.flujos[0] if Fi.q == q or (q is None and Fi.q != 0)])
        z = np.sum([Fi.F * Fi.z for Fi in self.flujos[0] if Fi.q == q or (q is None and Fi.q != 0)], axis=0)
        return F, z / F if F != 0 else np.array([0, 0, 0])
    
    # Método para crear un flujo temporal para determinar la fase de salida
    def crear_flujo_temporal(self, F, z):
        if F != 0:
            F_tem = Flujo(self.T, self.P, F, z, ['H2O', 'H2', 'O2'])
            F_tem.update()
        else:
            F_tem = Flujo(self.T, self.P, 0, self.flujos[0][0].z, ['H2O', 'H2', 'O2'])
            F_tem.update()
        return F_tem
    
    # Método para asignar temperatura y presión a los flujos de salida
    def asignar_propiedades_flujos_salida(self):
        for Fi in self.flujos[1]:
            Fi.T = self.T
            Fi.P = self.P
    
    # Método para determinar el comportamiento de fase de los flujos de salida
    def determinar_comportamiento_fase_salida(self, F_tem, F, FL, zL):
        if F_tem.q == 1:
            self.flujos[1][0].F = FL
            self.flujos[1][0].z = zL
            
            self.flujos[1][1].F = F
            self.flujos[1][1].z = F_tem.z
            self.flujos[1][1].GasPhase = F_tem.GasPhase
            self.flujos[1][1].LiqPhase = F_tem.LiqPhase
            self.flujos[1][1].q = 1
            
        elif F_tem.q == 0:
            self.flujos[1][1].F = 0
            self.flujos[1][1].z = F_tem.z
            self.flujos[1][1].GasPhase = F_tem.GasPhase
            self.flujos[1][1].LiqPhase = F_tem.LiqPhase
            self.flujos[1][1].q = 0
            
            self.flujos[1][0].F = F + FL
            self.flujos[1][0].z = (F_tem.z * F + zL * FL) / (F + FL)
            
        else:
            self.flujos[1][1].F = F * F_tem.q
            self.flujos[1][1].z = F_tem.GasPhase.x
            self.flujos[1][1].GasPhase = F_tem.GasPhase
            self.flujos[1][1].LiqPhase = None
            self.flujos[1][1].q = 1
            
            self.flujos[1][0].F = F * (1 - F_tem.q) + FL
            self.flujos[1][0].z = (F_tem.LiqPhase.x * F * (1 - F_tem.q) + zL * FL) / (F * (1 - F_tem.q) + FL)
    
    # Método para actualizar propiedades de los flujos de salida
    def actualizar_propiedades_flujos_salida(self):
        self.flujos[1][0].update()
        self.flujos[1][1].calcular_propiedades()
    
    # Método para calcular la temperatura de salida del tanque
    def calcular_temperatura_salida(self):
        # Calcular la temperatura de salida como la temperatura media ponderada de los flujos de entrada
        self.T = np.sum([Fi.T * Fi.F for Fi in self.flujos[0]]) / np.sum([Fi.F for Fi in self.flujos[0]])
        
        # Calcular los flujos de salida del tanque
        self.calcular_flujos()
        
        # Ajustar iterativamente la temperatura hasta alcanzar un balance de energía cercano a cero
        if np.abs(self.balance_energia()) < 1e-1:
            return self.balance_energia()
        
        # Definir una función para resolver la ecuación de temperatura y balance de energía
        def resolver_ecuacion_temperatura(temperatura):
            self.T = temperatura
            self.calcular_flujos()
            return self.balance_energia()

        # Resolver para encontrar la temperatura de salida usando el método de Newton
        s = sop.newton(resolver_ecuacion_temperatura, x0=self.T)
        self.T = np.round(s, 6)
        
        # Retornar el balance de energía final
        return self.balance_energia()
    
    def Vol(self):
        h2=0.1935*self.d
        r2=0.1*self.d
        r1=self.d

        r0=self.d/2

        def dV2(x):
            return (np.sqrt(r2**2-(x-h2)**2)+r0-r2)**2

        def fsol(x1):
            x=x1[0]
            y=x1[1]
            return [((r1-h2)*(2*x-h2-r1)-r2**2+r1**2)/(2*(r0-r2))+(r0-r2)/2-y,
                    (x-r1)**2+y**2-r1**2]

        a=sop.fsolve(fsol,x0=[h2,r1])[0]

        V1=lambda r,a,b:np.pi*((r**2)*(b-a)-((b-r)**3-(a-r)**3)/3)

        V=V1(r1,0,a)+np.pi*sint.quad(dV2,a,h2)[0] #m^3

        self.V=2*V+np.pi*self.h*(self.d**2)/4
    
    def dT_dt(self,dnL,dnG):
        nL=self.dinamico['F']['n_liq']
        nG=self.dinamico['F']['n_gas']
        hg=self.flujos[1][1].GasPhase.h
        hl=self.flujos[1][0].LiqPhase.h
        x=self.dinamico['F']['x']
        y=self.dinamico['F']['y']
        CpL=self.flujos[1][0].Cp
        CpG=self.flujos[1][1].Cp
        return np.round(self.balance_energia()-(dnG*hg+dnL*hl))/(nL*CpL+nG*CpG)

    def dz_dt(self):
        x=self.dinamico['F']['x']
        y=self.dinamico['F']['y']
        nL=self.dinamico['F']['n_liq']
        nG=self.dinamico['F']['n_gas']

        Fgi, zgi = self.calcular_flujo_total_y_composicion()
        FLi, zLi = self.calcular_flujo_total_y_composicion(q=0)
        F_tem = self.crear_flujo_temporal(Fgi, zgi)
        q=F_tem.q
        if F_tem.q == 1:
            ye=np.array([0,0,0])
            xe=F_tem.z
        elif F_tem.Q==0:
            xe=np.array([1,0,0])
            ye=F_tem.z
        else:
            ye=F_tem.GasPhase.x
            xe=F_tem.LiqPhase.x
        dnG=np.round(Fgi-Fgi*(1-q)-self.flujos[1][1].F,5)
        dnL=np.round(FLi+Fgi*(1-q)-self.flujos[1][0].F,5)
        return [[dnL,dnG],
            [
                (Fgi*zgi-Fgi*(1-q)*xe-self.flujos[1][1].F*y-dnG*y)/nG,
                (FLi*zLi+Fgi*(1-q)*xe-self.flujos[1][0].F*x-dnL*x)/nL
            ]
        ]
    
    def dP_dt(self,dnL,dnG,dT):
        z=self.flujos[1][1].GasPhase.Z
        nG=self.dinamico['F']['n_gas']
        nL=self.dinamico['F']['n_liq']
        V=self.V-nL/self.flujos[1][0].D
        dV=-dnL/self.flujos[1][0].D
        return np.round(dnG*z*R*self.T+dT*z*R*nG-dV*self.P)/V
    
    def dn_dt(self):
        Fi=np.sum([Fi.F for Fi in self.flujos[0]])
        Fs=np.sum([Fi.F for Fi in self.flujos[1]])
        return np.round(Fi-Fs,5)
    
    def dif_dt(self):
        dn=self.dn_dt()
        dz=self.dz_dt()
        dnL=dz[0][0]
        dnG=dz[0][1]
        dz=dz[1]
        nG=self.dinamico['F']['n_gas']
        nL=self.dinamico['F']['n_liq']
        dT=self.dT_dt(dnL,dnG)
        dP=self.dP_dt(dnL,dnG,dT)

        return [dn,dT,dP,dnL,dnG,dz]

    def dinamico_step(self,dt):
        if len(self.dinamico['T']['trazas'][0]['x'])==0:
            for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x'].append(dt/60)
            self.dinamico['F']['x']=self.flujos[1][0].z
            self.dinamico['F']['y']=self.flujos[1][1].z
            self.dinamico['F']['n_liq']=self.Liqlevel*np.pi*(self.d**2)*self.flujos[1][0].D/4
            Vg=self.V-0.5*np.pi*(self.d**2)/4
            self.dinamico['F']['n_gas']=(self.P*Vg)/(R*self.flujos[1][1].GasPhase.Z*self.T)
            self.dinamico['T']['T0']=self.T
            self.dinamico['P']['P0']=self.P
        else:
            for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x'].append(dt/60+traza['x'][-1])
        dt_dt=self.dif_dt()
        self.T=dt_dt[1]*dt+self.T
        self.P=dt_dt[2]*dt+self.P
        self.dinamico['T']['trazas'][0]['y'].append(self.T-273.15)
        self.dinamico['P']['trazas'][0]['y'].append(self.P*1e-5)
        self.dinamico['F']['trazas'][0]['y'].append(np.round(self.flujos[1][1].W*3600/1000,6))
        self.dinamico['F']['x']=np.round(dt_dt[-1][0],5)*dt+self.dinamico['F']['x']
        self.dinamico['F']['y']=np.round(dt_dt[-1][1],5)*dt+self.dinamico['F']['y']
        self.dinamico['F']['trazas'][1]['y'].append(self.dinamico['F']['y'][1])
        self.dinamico['F']['n_gas']=np.round(dt_dt[4],5)*dt+self.dinamico['F']['n_gas']
        self.dinamico['F']['n_liq']=np.round(dt_dt[3],5)*dt+self.dinamico['F']['n_liq']
        self.dinamico['L']['trazas'][0]['y'].append(np.round(self.dinamico['F']['n_liq']*4/(self.flujos[1][0].D*np.pi*(self.d**2)),4))
        self.Liqlevel=self.dinamico['L']['trazas'][0]['y'][-1]

        self.flujos[1][0].P=self.P
        self.flujos[1][0].T=self.T
        self.flujos[1][0].z=self.dinamico['F']['x']
        self.flujos[1][0].update()

        self.flujos[1][1].P=self.P
        self.flujos[1][1].T=self.T
        self.flujos[1][1].z=self.dinamico['F']['y']
        self.flujos[1][1].update()

        if self.Liqlevel / self.h > 0.9:
            self.logger.error('El nivel del tanque ha alcanzado un nivel alto, está al 90% de su capacidad total.')
        elif self.Liqlevel / self.h < 0.1:
            self.logger.error('El nivel del tanque ha alcanzado un nivel bajo, está al 10% de su capacidad total.')

    def reset_dinamics(self):
        self.T=self.dinamico['T']['T0']
        self.P=self.dinamico['P']['P0']
    
    def dete_data_dinamic(self):
        for key in self.dinamico:
                for traza in self.dinamico[key]['trazas']:
                    traza['x']=[]
                    traza['y']=[]
        self.reset_dinamics()


    def printData(self):
        return {
            'name':self.name,
            'flujos': {
                'Entrada': {Fi.name: Fi.printData() for Fi in self.flujos[0]},
                'Salida' : {Fi.name: Fi.printData() for Fi in self.flujos[1]}
            },
            'T': self.T,
            'P' : self.P,
            'dinamico':self.dinamico
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


class IntercambiadorCalor:
    def __init__(self, flujos, di, Di, L, nt, name='',logger=None):
        # Parámetros geométricos del intercambiador de calor
        self.di = di  # Diámetro interno del tubo en metros (19.05 mm)
        self.Di = Di  # Diámetro de la coraza en metros (205 mm)
        self.L = L    # Longitud del tubo en metros (500 mm)
        self.nt = nt  # Número de tubos
        self.At = nt * np.pi * (di / 2) ** 2
        self.des = (Di ** 2-(di**2)*nt) / ((nt * di))
        self.As = np.pi * ((Di) ** 2 - nt * (di ** 2)) / 4

        self.st1 = Termo_state(['H2O', 'H2', 'O2'])
        self.st2 = Termo_state(['H2O', 'H2', 'O2'])

        self.flujos = flujos
        self.tubos_temperatura_in = flujos[0][0].T
        self.tubos_temperatura_out = flujos[1][0].T
        self.coraza_temperatura_in = flujos[0][1].T
        self.coraza_temperatura_out = flujos[1][1].T
        self.duty = None
        self.Temperatura_data=None
        self.name=name
        self.logger = logger or SocketLogger('Intercambiador')

        self.dinamico={
            'T':{'title' : 'Temperatura','xlabel': 'Tiempo (min)','ylabel1': '°C',
                    'trazas':[
                        {
                            'name': 'Temperatura Tubos',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#00f7ff',
                        },
                        {
                            'name': 'Temperatura Coraza',
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'color': '#ff5757',
                        }
                    ],
                    'Tt0':self.flujos[1][0].T,
                    'Ts0':self.flujos[1][1].T
                },
        }
    
    # Función para calcular el coeficiente de transferencia de calor en la coraza
    def h_coraza(self, ks, Des, Re, Pr, mus):
        return 0.36 * (ks / Des) * (Re ** 0.55) * (Pr ** 0.33) * (mus ** 0.14)

    # Función para calcular el número de Reynolds
    def Re(self, rho, u, di, mu):
        return rho * u * di / mu

    # Función para calcular el coeficiente de transferencia de calor para Re < 2100
    def ht_Re_2100(self, ki, di, Re, Pr, Lt, mut):
        return 1.86 * (ki / di) * ((Re * Pr * (di / Lt)) ** 0.33) * (mut ** 0.14)

    # Función para calcular el coeficiente de transferencia de calor para 2100 <= Re < 10000
    def ht_Re_2100_10000(self, Cp, Gi, Re, Pr, di, Lt, mut):
        return 0.116 * Cp * Gi * ((Re ** 0.66 - 125) / Re) * (1 + ((di / Lt) ** 0.66)) * (Pr ** -0.66) * (mut ** 0.14)

    # Función para calcular el coeficiente de transferencia de calor para Re >= 10000
    def ht_Re_10000(self, ki, di, Re, Pr, mut):
        return (ki / di) * 0.023 * (Re ** 0.8) * (Pr ** 0.33) * (mut ** 0.14)

    # Función para seleccionar la fórmula correcta basada en el número de Reynolds
    def h_tubos(self, Re, ki, di, Pr, Lt, mut, Cp=None, Gi=None):
        if Re < 2100:
            return self.ht_Re_2100(ki, di, Re, Pr, Lt, mut)
        elif Re < 10000:
            return self.ht_Re_2100_10000(Cp, Gi, Re, Pr, di, Lt, mut)
        else:
            return self.ht_Re_10000(ki, di, Re, Pr, mut)

    # Función para corregir el coeficiente de transferencia de calor en tubos
    def h_tubos_correccion(self, Re, ki, di, de, Pr, Lt, mut, Cp=None, Gi=None):
        return self.h_tubos(Re, ki, di, Pr, Lt, mut, Cp, Gi) * di / de

    # Función para calcular el coeficiente global de transferencia de calor
    def U(self, ks, Des, Re_s, Pr_s, Re_t, kt, di, de, Prt, Lt, Cpt, Git, mut, mus, nt):
        hs = self.h_coraza(ks, Des, Re_s, Pr_s, mus)
        hw = self.h_tubos_correccion(Re_t, kt, di, de, Prt, Lt*nt, mut, Cpt, Git)
        return 1 / (de/ (di * hw) + (de * np.log(de / di) / (2 * 51.5)) + 1 / hs) #https://www.researchgate.net/figure/Thermal-conductivity-of-the-carbon-steel_tbl1_227144263

    def FT(self,T1, T2, t1, t2, Ns):
        """
        Calcula el factor de corrección de temperatura (FT) para un intercambiador de calor.

        Parámetros:
        T1 -- Temperatura de entrada del fluido caliente (°C)
        T2 -- Temperatura de salida del fluido caliente (°C)
        t1 -- Temperatura de entrada del fluido frío (°C)
        t2 -- Temperatura de salida del fluido frío (°C)
        Ns -- Número de pases

        Retorna:
        FT -- Factor de corrección de temperatura
        """
        R = (T1 - T2) / (t2 - t1)
        S = (t2 - t1) / (T1 - t1)

        # Verificación para evitar divisiones por cero o valores negativos en logaritmos
        if R == 1:
            raise ValueError("R no puede ser igual a 1.")
        if S == 1:
            raise ValueError("S no puede ser igual a 1.")

        # Cálculo del término Px
        Px = (1 - ((R * S - 1) / (S - 1)) ** (1 / Ns))
        # Verificación para evitar valores fuera del dominio de los logaritmos
        if not (0 < Px < 1):
            raise ValueError("Px debe estar en el rango (0, 1) para ser válido.")

        # Cálculo del factor de corrección de temperatura FT
        num = np.log((1 - Px) / (1 - R * Px))
        denom = np.log((2 / Px - 1 - R + np.sqrt(R ** 2 + 1)) / (2 / Px - 1 - R - np.sqrt(R ** 2 + 1)))

        FT = (np.sqrt(R ** 2 + 1) / (R - 1)) * (num / denom)

        return FT
    
    # Función para calcular el coeficiente de fricción en la coraza
    def f_coraza(self, Re):
        return np.exp(0.576 - 0.19 * np.log(Re))

    # Función para calcular el coeficiente de fricción en los tubos
    def f_tubos(self, Re):
        if Re < 2100:
            return 16 / Re
        else:
            return 0.014 + 0.125 * (Re ** -0.32)

    # Función para calcular la caída de presión en la coraza
    def dP_coraza(self, f, G, Nd, D, rho, Des, mus):
        return f * G * (Nd + 1) * D / (2 * rho * Des * (mus ** 0.14))

    # Función para calcular la caída de presión en los tubos
    def dP_tubos(self, f, Lc, n, di, rho, v):
        return (4 * f * Lc * n / di + 4 * n) * (rho * (v ** 2)) / 2
    
    def dTt(self, F, T, Tw, Cp_t, di, nt, U_diseno):
        return U_diseno * (Tw - T) * np.pi * di * nt / (F * Cp_t)

    def dTw(self, F, T, Tw, Cp_s, di, nt, U_diseno):
        return U_diseno * (T - Tw) * np.pi * di * nt / (F * Cp_s)
    
    def calcular_flujos(self):
        self.st1.set_phase(self.flujos[0][0])
        self.st2.set_phase(self.flujos[0][1])
    

    def dT_sistema(self, F, FCW, T, Tw, Pt, Ps, At, As, di, Di, nt, des, L, dx):

        resul1 = self.st1.update(T, Pt)
        resul2 = self.st2.update(Tw, Ps)

        # Densidad (kg/m^3)
        rhot = resul1['result']['D']
        rhos = resul2['result']['D']

        Qi = F / rhot
        QCW = FCW / rhos

        # Viscosidad dinámica (Pa·s)
        mu_t = resul1['result']['v']
        mu_s = resul2['result']['v']

        Tp = (1 / 2) * ((T + Tw))

        mu_t_Tp = self.st1.update(Tp, Pt)['result']['v']
        mu_s_Tp = self.st2.update(Tp, Ps)['result']['v']

        mut = mu_t / mu_t_Tp
        mus = mu_s / mu_s_Tp

        # Conductividad térmica (W/m·K)
        kt = resul1['result']['L']
        ks = resul2['result']['L']

        # Número de Prandtl
        Prs = resul1['result']['PRANDTL']
        Prt = resul2['result']['PRANDTL']

        # Capacidad calorífica (J/kg·K)
        Cp_t = resul1['result']['cp']
        Cp_s = resul2['result']['cp']

        ut = Qi / At    # Velocidad del agua caliente en los tubos
        us = QCW / As   # Velocidad del agua fría en la coraza

        # Número de Reynolds
        Re_t = self.Re(rhot, ut, di, mu_t)
        Re_s = self.Re(rhos, us, des, mu_s)

        U_diseno = self.U(ks, des, Re_s, Prs, Re_t, kt, di, di, Prt, dx, Cp_t, F/At, mut, mus, nt)

        dTt_i = self.dTt(F, T, Tw, Cp_t, di, nt, U_diseno)
        dTw_i = self.dTw(FCW, T, Tw, Cp_s, di, nt, U_diseno)


        fs = self.f_coraza(Re_s)
        ft = self.f_tubos(Re_t)

        dPs = -self.dP_coraza(fs, FCW / As, 0, Di, rhos, des, mus) / L
        dPt = -(rhot * ut / 2) * (4 * ft * nt / di)

        return [dTt_i, dTw_i, dPt, dPs]
    
    # Define la función que representa el sistema de ecuaciones diferenciales
    def sistema_diferencial1(self, t, Y, dx):
        T, Tw, Pt, Ps = Y
        dT, dTw, dPt, dPs = self.dT_sistema(
            self.flujos[0][0].W/1000, 
            self.flujos[0][1].W/1000, 
            T, 
            Tw,
            Pt,
            Ps,
            self.At,
            self.As,
            self.di,
            self.Di,
            self.nt,
            self.des,
            self.L,
            dx,
        )
        return [dT, -dTw, dPt, -dPs]

    def calcular_temperatura_salida(self,t_eval=None):
        t_eval_i = np.linspace(0, self.L, 20) if t_eval is None else t_eval
        self.calcular_flujos()
        
        def sistema_ecuaciones(t, Y):
            return self.sistema_diferencial1(t, Y, self.L)

        def Tsol(Y):
            sol = sint.solve_ivp(sistema_ecuaciones, [0, self.L], [self.flujos[0][0].T, Y[0], self.flujos[0][0].P, Y[1]], t_eval=[0, self.L])
            error=np.array([self.flujos[0][1].T - sol.y[1][-1], self.flujos[0][1].P - sol.y[-1][-1]])
            return [self.flujos[0][1].T - sol.y[1][-1], self.flujos[0][1].P - sol.y[-1][-1]]

        Y = sop.fsolve(Tsol, x0=[(self.flujos[0][0].T*self.flujos[0][0].F + self.flujos[0][1].T*self.flujos[0][1].F) / (self.flujos[0][1].F+self.flujos[0][0].F), self.flujos[0][1].P], xtol=1e-10)
        sol = sint.solve_ivp(sistema_ecuaciones, [0,self.L], [self.flujos[0][0].T, Y[0], self.flujos[0][0].P, Y[1]], t_eval=t_eval_i)
        self.Temperatura_data=[sol.y,sol.t]

        self.flujos[1][0].T = self.Temperatura_data[0][0][-1]
        self.flujos[1][0].F = self.flujos[0][0].F
        self.flujos[1][0].z = self.flujos[0][0].z
        self.flujos[1][0].P = self.Temperatura_data[0][2][-1]
        self.flujos[1][0].update()

        self.flujos[1][1].T = self.Temperatura_data[0][1][0]
        self.flujos[1][1].F = self.flujos[0][1].F
        self.flujos[1][1].z = self.flujos[0][1].z
        self.flujos[1][1].P = self.Temperatura_data[0][3][0]
        self.flujos[1][1].update()

        self.duty = self.flujos[1][0].H - self.flujos[0][0].H
        return sol
    
    def calcular_flujo_CW(self):
        self.logger.procesando('Calculando flujo de agua en la coraza')
        
        def Fsol(F, Tf):
            self.flujos[0][0].F = F
            self.flujos[0][0].update()
            sol = self.calcular_temperatura_salida(np.linspace(0, self.L, 20))
            error = sol.y[1][0] - Tf
            self.logger.procesando(f'Temperatura error {np.abs(error)}')
            return error
        
        Tf = self.flujos[1][1].T
        try:
            F_solution = sop.bisect(Fsol, a=0.01, b=500, args=(Tf,), xtol=1e-6, rtol=1e-6)
            self.logger.info(f'Solución encontrada: {F_solution}')
            return True
        except ValueError as e:
            self.logger.warning(f'Error en la bisección: {e}')
            return False
    
    def balance_energia(self):
        Ht=self.flujos[0][0].H-self.flujos[1][0].H+self.duty
        Hs=self.flujos[0][1].H-self.flujos[1][1].H-self.duty
        return np.round([Ht,Hs],2)
    
    def dif_dt(self):
        Tt0=self.flujos[1][0].T
        Pt0=self.flujos[1][0].P
        Ts0=self.flujos[1][1].T
        Ps0=self.flujos[1][1].P

        self.calcular_temperatura_salida()

        self.flujos[1][0].T=Tt0
        self.flujos[1][0].P=Pt0
        self.flujos[1][0].update()
        self.flujos[1][1].T=Ts0
        self.flujos[1][1].P=Ps0
        self.flujos[1][1].update()

        Vt=((self.di)**2)*np.pi*self.L*self.nt/4
        Vs=((self.Di)**2)*np.pi*self.L/4-Vt

        mol_t=Vt*self.flujos[0][0].D
        mol_s=Vt*self.flujos[0][1].D
        dE=self.balance_energia()
        dTt_dt=dE[0]/(mol_t*self.flujos[0][0].Cp)
        dTs_dt=dE[1]/(mol_s*self.flujos[0][1].Cp)

        return [dTt_dt,dTs_dt]
    
    def dinamico_step(self,dt):
        if len(self.dinamico['T']['trazas'][0]['x'])==0:
            self.dinamico['T']['trazas'][0]['x'].append(dt/60)
            self.dinamico['T']['Tt0']=self.flujos[1][0].T
            self.dinamico['T']['trazas'][1]['x'].append(dt/60)
            self.dinamico['T']['Ts0']=self.flujos[1][1].T

        else:
            self.dinamico['T']['trazas'][0]['x'].append(dt/60+self.dinamico['T']['trazas'][0]['x'][-1])
            self.dinamico['T']['trazas'][1]['x'].append(dt/60+self.dinamico['T']['trazas'][1]['x'][-1])
        
        dt_time=self.dif_dt()
        self.flujos[1][0].T=dt_time[0]*dt+self.flujos[1][0].T
        self.dinamico['T']['trazas'][0]['y'].append(self.flujos[1][0].T-273.15)

        self.flujos[1][1].T=dt_time[1]*dt+self.flujos[1][1].T
        self.dinamico['T']['trazas'][1]['y'].append(self.flujos[1][1].T-273.15)
    
    
    def dete_data_dinamic(self):
        self.dinamico['T']['trazas'][0]['x']=[]
        self.dinamico['T']['trazas'][1]['y']=[]
        self.dinamico['T']['trazas'][0]['x']=[]
        self.dinamico['T']['trazas'][1]['y']=[]

    
    def printData(self):
        return {
            'name':self.name,
            'flujos': {
                'Entrada': {Fi.name: Fi.printData() for Fi in self.flujos[0]},
                'Salida' : {Fi.name: Fi.printData() for Fi in self.flujos[1]}
            },
            'Tin'   : self.flujos[0][0].T,
            'TCwin' : self.flujos[1][0].T,
            'Tout'  : self.flujos[0][1].T,
            'TCwout': self.flujos[1][1].T,
            'duty'  : self.duty,
            'graficas' : {
                'name' : 'Perfiles de temperatura',
                'graps':[
                    {
                        'title' : 'Perfil de temperatura',
                        'xlabel': 'longitud (mm)',
                        'ylabel1': 'Temperatura',
                        'trazas':[
                            {
                                'name': 'Temperatura Tubos',
                                'x': self.Temperatura_data[1],
                                'y': self.Temperatura_data[0][0]-273.15,
                                'type': 'scatter',
                                'color': '#00f7ff',
                            },
                            {
                                'name': 'Temperatura coraza',
                                'x': self.Temperatura_data[1],
                                'y': self.Temperatura_data[0][1]-273.15,
                                'type': 'scatter',
                                'color': '#f678ff',
                            }
                        ]
                    }
                ]
            },
            'dinamico':self.dinamico
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
        
        
        
        
        
    
    