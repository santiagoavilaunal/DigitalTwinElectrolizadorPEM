import sys
sys.path.append(r'../')
import Modelo.Termodinamica as Tm
import numpy as np
import json

#pesos moleculares
MW=np.array([18.01568,2.01568,31.998])

# Clase para manejar fracciones molares
class FraccionMolar(np.ndarray):
    def __new__(cls, z, tol=1E-9):
        obj = np.asarray(z)
        obj = np.round(obj*(100/tol))*tol/100

        if not np.isclose(np.sum(obj), 1, atol=1E-4):
            raise ValueError("La concentración no está normalizada correctamente a 1 ", obj)

        obj=obj/obj.sum()

        if np.any(obj < 0):
            raise ValueError("Las concentraciones no pueden ser negativas ", obj)

        obj = obj.view(cls)
        return obj

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # Manejar operaciones ufunc con otros arrays o escalares
        if method == '__array_wrap__':
            # Mantener la instancia como FraccionMolar después de la operación ufunc
            return self
        else:
            # Convertir el objeto a un numpy.ndarray antes de aplicar la ufunc
            inputs = [np.asarray(x) if isinstance(x, FraccionMolar) else x for x in inputs]
            result = getattr(ufunc, method)(*inputs, **kwargs)
            # Convertir el resultado a FraccionMolar si es una instancia de np.ndarray
            # if isinstance(result, np.ndarray):
            #     result = result.view(FraccionMolar)
            return result

# Clase constructora de la Fase
class FaseResult:
    def __init__(self, T, P, x, Z, D, h, Cp, phi, dh_dP, dD_dT, dD_dP, tol=1e-9):
        """
        Constructor de la clase FaseResult.

        Parámetros:
        - T: Temperatura en Kelvin (K).
        - P: Presión en Pascales (Pa).
        - x: Fracción molar en mol/mol.
        - Z: Factor de compresibilidad.
        - D: Densidad molar en mol/m³.
        - h: Entalpía en Julios por mol (J/mol).
        - Cp: Calor específico en Julios por mol por Kelvin (J/mol/K).
        - phi: Coeficientes de fugacidad.
        - dh_dP: Cambio de entalpía con respecto a la presión en Julios por mol por Pascal (J/mol/Pa).
        - dD_dT: Cambio de densidad con respecto a la temperatura en mol/m³/K.
        - dD_dP: Cambio de densidad con respecto a la presión en mol/m³/Pa.
        """
        self.tol=tol
        self.T = T
        self.P = P
        self.x = x
        self.Z = Z
        self.D = D
        self.h = h
        self.Cp = Cp
        self.phi = phi
        self.dh_dP = dh_dP
        self.dD_dT = dD_dT
        self.dD_dP = dD_dP
    
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = FraccionMolar(value, tol=self.tol)  # Convertir a FraccionMolar automáticamente
    
    def printData(self):
        """
        Método para imprimir los datos del objeto FaseResult de manera formateada.
        """
        return f"x: {self.x}\nZ: {self.Z}\nD: {self.D}\nh: {self.h}\nCp: {self.Cp}\nphi: {self.phi}\ndh_dP: {self.dh_dP}\ndD_dT: {self.dD_dT}\ndD_dP: {self.dD_dP}"
    
    def to_json(self):
        """
        Método para convertir los datos del objeto FaseResult en un diccionario JSON.
        """
        return {
            'T': self.T,
            'P': self.P,
            'x': self.x.tolist(),
            'Z': self.Z,
            'D': self.D,
            'h': self.h,
            'Cp': self.Cp,
            'phi': self.phi.tolist() if isinstance(self.phi, np.ndarray) else self.phi,
            'dh_dP': self.dh_dP,
            'dD_dT': self.dD_dT,
            'dD_dP': self.dD_dP
        }
    
    def __str__(self):
        """
        Método para obtener una representación en cadena de caracteres del objeto FaseResult.
        """
        return self.printData()

    def __repr__(self):
        """
        Método para obtener una representación del objeto FaseResult.
        """
        return self.printData()



# Clase Flujo para calcular propiedas del la linea
class Flujo:
    def __init__(self, T, P, F, z, Es, name='' ,tol=1E-9):
        """
        Constructor de la clase Flujo.

        Parámetros:
        - T: Temperatura del sistema.
        - P: Presión del sistema.
        - F: Flujo molar en mol/s.
        - z: Fracción molar de las sustancias en mol/mol.
        - Es: Sustancias involucradas en el sistema.
        - name: Nombre de la linea.
        - tol: Tolerancia para el cálculo de la fracción molar (predeterminado a 1E-9).
        """
        self.name=name
        self.T = T 
        self.P = P
        self.Es = Es
        self.F = F
        self.tol = tol
        self.z = z
        self.GasPhase = None
        self.LiqPhase = None
        self.q = None
        self.H = None 
        self.Q = None
        self.D = None
        self.W = None
        self.Cp= None
    
    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = FraccionMolar(value, tol=self.tol)  # Convertir a FraccionMolar automáticamente
    
    def F_get(self,i):
        return self.F*self.z[i]
        
    def calcular_propiedades(self):
        if self.q == 0:            
            self.H = self.LiqPhase.h * self.F  # Calcular la entalpía total
            self.Q = self.F / self.LiqPhase.D  # Calcular el caudal volumétrico
            self.D = self.LiqPhase.D  # Densidad del sistema
            self.W = np.sum(self.z * MW * self.F)  # Calcular la masa total
            self.Cp= self.LiqPhase.Cp # Calcular el calor Especifico
        
        elif self.q == 1:
            self.H = self.GasPhase.h * self.F  # Calcular la entalpía total
            self.Q = self.F / self.GasPhase.D  # Calcular el caudal volumétrico
            self.D = self.GasPhase.D  # Densidad del sistema
            self.W = np.sum(self.z * MW * self.F)  # Calcular la masa total
            self.Cp= self.GasPhase.Cp # Calcular el calor Especifico
            
        else:
            self.H = (self.GasPhase.h*self.q + self.LiqPhase.h*(1-self.q)) * self.F  # Calcular la entalpía total
            self.Q = (self.q / self.GasPhase.D + (1 - self.q) / self.LiqPhase.D) * self.F  # Calcular el caudal volumétrico
            self.D = self.F / self.Q  # Densidad del sistema
            self.W = np.sum(self.z * MW * self.F)  # Calcular la masa total
            self.Cp= self.q*self.GasPhase.Cp + (1-self.q)*self.LiqPhase.Cp # Calcular el calor Especifico
        
        
    
    def update(self,z0: list | None=None):
        """
        Método para actualizar las propiedades termodinámicas del flujo.
        """
        # Calcular la solubilidad del gas en el sistema
        resultado_solubilidad = Tm.Solubilidad_Gas(self.T, self.P, self.z,z0=z0,tol=self.tol)
        
        # Verificar si el cálculo de solubilidad converge
        if not resultado_solubilidad['converg']:
            raise ValueError(f"El equilibrio no converge con un error de {resultado_solubilidad['error']}")
        
        self.q = np.round(resultado_solubilidad['q']*(1/self.tol))*self.tol  # Fracción de fase gaseosa (q) obtenida del resultado de solubilidad
        
        # Caso: Sistema en fase líquida (q = 0)
        if self.q == 0:
            self.GasPhase = None
            self.LiqPhase = FaseResult(x=self.z, **resultado_solubilidad['Liq'])
            self.calcular_propiedades()
            return
        
        # Caso: Sistema en fase gaseosa (q = 1)
        if self.q == 1:
            self.LiqPhase = None
            self.GasPhase = FaseResult(x=self.z, **resultado_solubilidad['Gas'])
            self.calcular_propiedades()
            return
        
        # Caso: Sistema en equilibrio de fases mixtas (0 < q < 1)
        self.LiqPhase = FaseResult(x=FraccionMolar(resultado_solubilidad['c'][0], tol=self.tol), **resultado_solubilidad['Liq'])
        self.GasPhase = FaseResult(x=FraccionMolar(resultado_solubilidad['c'][1], tol=self.tol), **resultado_solubilidad['Gas'])
        self.calcular_propiedades()
        return
    
    def printData(self):
        """
        Método para obtener una representación en cadena de caracteres de los datos del flujo.
        """
        return {
            'Name': self.name,
            'T': self.T,
            'P': self.P,
            'F': self.F,
            'z': self.z.tolist(),
            'q': self.q,
            'H': self.H,
            'W': self.W,
            'Q': self.Q,
            'LiqPhase': self.LiqPhase.to_json() if self.LiqPhase is not None else {},
            'GasPhase': self.GasPhase.to_json() if self.GasPhase is not None else {}
        }
    
    def to_json(self):
        """
        Método para convertir los datos del flujo en un diccionario JSON.
        """
        return json.dumps(self.printData())
    
    def __str__(self):
        """
        Método para obtener una representación en cadena de caracteres del flujo.
        """
        return '\n'.join([f'{clave}: {str(valor)}' for clave, valor in self.printData().items()])

    def __repr__(self):
        """
        Método para obtener una representación del flujo.
        """
        return '\n'.join([f'{clave}: {str(valor)}' for clave, valor in self.printData().items()])