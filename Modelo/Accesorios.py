import numpy as np
import json


class Valvula:
    def __init__(self,cv0=None,apertura0=None,name='',flujos=None,dP=None):
        if cv0 is not None and apertura0 is not None:
            self.cv_m=(cv0)/apertura0 #suponer que se comporta lineal
        else:
            self.cv_m=None
        self._Q=None
        self._apertura=None
        self.name=name
        self.flujos=flujos
        self.dP=dP
    
    def calcular_cv(self,apertura,Q=None,dP=None,gs=None):

        dPi=self.flujos[0].P-self.flujos[1].P if dP is None and self.dP is None else self.dP if dP is None else dP
        gsi=(self.flujos[0].W/(self.flujos[0].Q*1000*1000)) if gs is None else gs
        Qi=self.flujos[0].Q*60000 if Q is None else Q

        gmp=Qi/(7.57683211E-5*60000)
        cv0=gmp/(np.sqrt((dPi)/(6895*gsi)))
        self.cv_m=(cv0)/apertura
        return cv0

    def Q(self,apertura,dP=None,gs=None):
        dPi=self.flujos[0].P-self.flujos[1].P if dP is None and self.dP is None else self.dP if dP is None else dP
        gsi=(self.flujos[0].W/(self.flujos[0].Q*1000*1000)) if gs is None else gs
            
        gmp=apertura*self.cv_m*np.sqrt((dPi)/(6895*gsi))
        self._Q=gmp*7.57683211E-5*60000 #Litros/min
        self._apertura=apertura
        if self.flujos is not None:
            self.flujos[0].F=self._Q*self.flujos[0].D/60000
            self.flujos[0].update()
        return self._Q

    def Ap(self,Q=None,dP=None,gs=None):

        Qi=self.flujos[0].Q*60000 if Q is None else Q
        dPi=self.flujos[0].P-self.flujos[1].P if dP is None and self.dP is None else self.dP if dP is None else dP
        gsi=(self.flujos[0].W/(self.flujos[0].Q*1000*1000)) if gs is None else gs

        gmp=Qi/(7.57683211E-5*60000)
        self._apertura=gmp/(self.cv_m*np.sqrt((dPi)/(6895*gsi)))
        return self._apertura
    
    def getQ(self):
        return self._Q
    
    def getAp(self):
        return self._apertura
    
    def printData(self):
        return {
            'name':self.name,
            'flujos':{Fi.name: Fi.printData() for Fi in self.flujos} if self.flujos is not None else {},
            'Q':self._Q,
            'apertura':self._apertura,
            'cv_ap':self.cv_m,
            'dP':self.dP
        }
    
    def to_json(self):
        return json.dumps(self.printData())

    def __str__(self):
        return str(self.printData())

    def __repr__(self):
        return str(self.printData())


class PIDController:
    def __init__(self, Kp:float, Ki:float, Kd:float, setpoint:float, offset:float=0, min_Mv=float('-inf'), max_Mv=float('inf'), activo=False):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.offset = offset
        self.min_Mv = min_Mv
        self.max_Mv = max_Mv
        self.integral = 0
        self.prev_error = 0
        self.activo=activo
        self.Mv=offset

    def calculate(self, measurement, dt):
        # Error calculation
        error = self.setpoint - measurement

        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += self.Ki * error * dt

        # Derivative term
        D = self.Kd * (error - self.prev_error) / dt

        # Control variable (Manipulated Variable, MV)
        MV1 = self.offset + P + self.integral + D
        self.Mv = max(self.min_Mv, min(MV1, self.max_Mv))

        # Update previous error
        self.prev_error = error

        return self.Mv
    
    def printData(self):
        return {
            "Kp":self.Kp,
            "Ki":self.Ki,
            "Kd":self.Kd,
            "setpoint":self.setpoint,
            "offset":self.offset,
            "min_Mv":self.min_Mv,
            "max_Mv":self.max_Mv,
            "integral":self.integral,
            "prev_error":self.prev_error,
            "activo":self.activo
        }
    
    def to_json(self):
        return json.dumps(self.printData())

    def __str__(self):
        return str(self.printData())

    def __repr__(self):
        return str(self.printData())