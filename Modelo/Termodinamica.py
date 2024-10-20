import CoolProp.CoolProp as cp
import CoolProp
import numpy as np
import scipy.optimize as sop

PARAMETROS_BINARIOS_H2O_H2=[0.34136764, 1.40993009, 1.17115251, 0.        ]
#PARAMETROS_BINARIOS_H2O_H2=[0.19332646, 1.0, 0.65838246, 0.0]

#Constante de los gases
R=8.31446261815324 #J/(mol*K)

#Estado de referencia
Dmolar_H2O = cp.PropsSI("Dmolar", "T", 298.15, "P", 101325, "H2O")
Dmolar_H2 = cp.PropsSI("Dmolar", "T", 298.15, "P", 101325, "H2")
Dmolar_O2 = cp.PropsSI("Dmolar", "T", 298.15, "P", 101325, "O2")

G0molar=-237.18*1000
H0molar=-285.830*1000
S0molar=(H0molar-G0molar)/298.15
cp.set_reference_state('H2O', 298.15, Dmolar_H2O, H0molar, S0molar) # fluid, T, D (mol/m^3), h (J/mol), s (J/mol/K)
cp.set_reference_state('H2',  298.15, Dmolar_H2, 0, 0)
cp.set_reference_state('O2',  298.15, Dmolar_O2, 0, 0)

def Termo_Propiedades(Termo,T,P):
    return np.transpose([cp.PropsSI(Termo,'T',T,'P',P,es) for es in ["H2O","H2","O2"]])

class Termo_state:
    def __init__(self, Es, EOS='HEOS'):
        self.Es = np.array(Es)
        self.EOS = EOS
        
        self.state_liq = None
        self.state_gas = None
        self.q = None
    
    def set_parametros(self, state, z):
        es_list = list(self.Es[np.nonzero(z)])
        if 'H2' in es_list and 'H2O' in es_list:
            i = es_list.index('H2O')
            j = es_list.index('H2')
            state.set_binary_interaction_double(i, j, 'betaT', PARAMETROS_BINARIOS_H2O_H2[0])
            state.set_binary_interaction_double(i, j, 'betaV', PARAMETROS_BINARIOS_H2O_H2[1])
            state.set_binary_interaction_double(i, j, 'gammaT', PARAMETROS_BINARIOS_H2O_H2[2])
            state.set_binary_interaction_double(i, j, 'gammaV', PARAMETROS_BINARIOS_H2O_H2[3])
    
    def set_phase(self, flujo):
        self.q = flujo.q
        non_zero_z = self.Es[np.nonzero(flujo.z)]
        joined_es = '&'.join(non_zero_z)
        
        if self.q == 0:
            self.state_liq = CoolProp.AbstractState(self.EOS, joined_es)
            self.set_parametros(self.state_liq, flujo.z[np.nonzero(flujo.z)])
            self.state_liq.specify_phase(CoolProp.iphase_liquid)
            if len(non_zero_z) > 1:
                self.state_liq.set_mole_fractions(flujo.z[np.nonzero(flujo.z)])
        elif self.q == 1:
            self.state_gas = CoolProp.AbstractState(self.EOS, joined_es)
            self.set_parametros(self.state_gas, flujo.z[np.nonzero(flujo.z)])
            self.state_gas.specify_phase(CoolProp.iphase_gas)
            if len(non_zero_z) > 1:
                self.state_gas.set_mole_fractions(flujo.z[np.nonzero(flujo.z)])
        else:
            self.state_liq = CoolProp.AbstractState(self.EOS, joined_es)
            self.set_parametros(self.state_liq, flujo.z[np.nonzero(flujo.z)])
            self.state_liq.specify_phase(CoolProp.iphase_liquid)
            if len(non_zero_z) > 1:
                self.state_liq.set_mole_fractions(flujo.LiqPhase.x[np.nonzero(flujo.z)])

            self.state_gas = CoolProp.AbstractState(self.EOS, joined_es)
            self.set_parametros(self.state_gas, flujo.z[np.nonzero(flujo.z)])
            self.state_gas.specify_phase(CoolProp.iphase_gas)
            if len(non_zero_z) > 1:
                self.state_gas.set_mole_fractions(flujo.GasPhase.x[np.nonzero(flujo.z)])
    
    def update(self, T, P):
        liquid_result = {
            'D': 0,
            'h': 0,
            's': 0,
            'cp': 0,
            'v': 0,
            'L': 0,
            'PRANDTL': 0
        }
        gas_result = {
            'D': 0,
            'h': 0,
            's': 0,
            'cp': 0,
            'v': 0,
            'L': 0,
            'PRANDTL': 0
        }
        
        if self.state_liq is not None:
            self.state_liq.update(CoolProp.PT_INPUTS, P, T)
            liquid_result = {
                'D': self.state_liq.rhomass(),
                'h': self.state_liq.hmass(),
                's': self.state_liq.smass(),
                'cp': self.state_liq.cpmass(),
                'v': self.state_liq.viscosity(),
                'L': self.state_liq.conductivity(),
                'PRANDTL': self.state_liq.Prandtl()
            }
        
        if self.state_gas is not None:
            self.state_gas.update(CoolProp.PT_INPUTS, P, T)
            gas_result = {
                'D': self.state_gas.rhomass(),
                'h': self.state_gas.hmass(),
                's': self.state_gas.smass(),
                'cp': self.state_gas.cpmass(),
                'v': self.state_gas.viscosity(),
                'L': self.state_gas.conductivity(),
                'PRANDTL': self.state_gas.Prandtl()
            }
        
        # Calculate the weighted result
        result = {key: gas_result[key] * self.q + liquid_result[key] * (1 - self.q) for key in gas_result}
        
        return {
            'liquid': liquid_result,
            'gas': gas_result,
            'result': result
        }

class Sistema:

    def __init__(self, components:np.ndarray | list | str, EOS="HEOS", phase=None):

        self.get_phase(phase)

        # Inicializar el estado del fluido o mezcla de fluidos
        if isinstance(components, str):
            # Si Es es un string (un solo componente), crear el estado para ese componente
            
            self.state = CoolProp.AbstractState(EOS, components)
        else:
            # Si Es es una lista de componentes (mezcla), crear el estado para la mezcla de componentes
            self.state = CoolProp.AbstractState(EOS, '&'.join(components))

            if 'H2' in components and 'H2O' in components:
                #modifico los parametros de interacción binaria
                i=list(components).index('H2O')
                j=list(components).index('H2')
                self.state.set_binary_interaction_double(i, j, 'betaT', PARAMETROS_BINARIOS_H2O_H2[0])
                self.state.set_binary_interaction_double(i, j, 'betaV', PARAMETROS_BINARIOS_H2O_H2[1])
                self.state.set_binary_interaction_double(i, j, 'gammaT', PARAMETROS_BINARIOS_H2O_H2[2])
                self.state.set_binary_interaction_double(i, j, 'gammaV', PARAMETROS_BINARIOS_H2O_H2[3])
        
        self.components=components
        
        # Especificar la fase del estado del fluido
        self.state.specify_phase(self.fase)
    
    def update(self, T: float, P: float, z:np.ndarray | list | None=None):
        
        if not(isinstance(self.components, str)):
            self.state.set_mole_fractions(z)
        
        # Actualizar el estado del fluido a las condiciones de temperatura y presión especificadas
        self.state.update(CoolProp.PT_INPUTS, P, T)
        
        # Calcular coeficientes de fugacidad para cada componente en la mezcla (si es una mezcla)
        # o para el componente único (si es un solo componente)
        if isinstance(self.components, str):
            phi =  self.state.fugacity_coefficient(0)
        else:
            phi = np.array([self.state.fugacity_coefficient(i) for i in range(len(self.components))])
        
        # Devolver un diccionario con propiedades termodinámicas calculadas
        return {
            'T':T,
            'P':P,
            'D': self.state.rhomolar(),  # Densidad molar
            'Z': self.state.compressibility_factor(),  # Factor de compresibilidad
            'h': self.state.hmolar(),  # Entalpía molar
            'Cp': self.state.cpmolar(),  # Capacidad calorífica molar a presión constante
            'phi': phi,  # Coeficientes de fugacidad
            'dh_dP': self.state.first_partial_deriv(CoolProp.iHmolar, CoolProp.iP, CoolProp.iT),  # Derivada parcial de entalpía molar respecto a presión a temperatura constante
            'dD_dT': self.state.first_partial_deriv(CoolProp.iDmolar, CoolProp.iT, CoolProp.iP),  # Derivada parcial de densidad molar respecto a temperatura a presión constante
            'dD_dP': self.state.first_partial_deriv(CoolProp.iDmolar, CoolProp.iP, CoolProp.iT)  # Derivada parcial de densidad molar respecto a presión a temperatura constante
        }
    
    def get_phase(self,phase=None):
        if phase == 'Liq':
            self.fase = CoolProp.iphase_liquid
        elif phase == 'Gas':
            self.fase = CoolProp.iphase_gas
        else:
            self.fase = CoolProp.iphase_not_imposed


def BinarieVLE(T, P, Es, max_iter=100, tol=1E-6):
    # Función para calcular el equilibrio de fases binario (VLE)

    # Obtener propiedades críticas y acentricidades para las especies
    w = np.array([cp.PropsSI('acentric', es) for es in Es])
    Tc = np.array([cp.PropsSI('TCRIT', es) for es in Es])
    Pc = np.array([cp.PropsSI('PCRIT', es) for es in Es])

    # Calcular coeficientes de ajuste k
    k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))

    # Configurar las fracciones molares y especificar fase líquida
    EOS_TLiq=Sistema(components=Es, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_TGas=Sistema(components=Es, phase='Gas')

    # Iterar para encontrar las fracciones molares de líquido (x) y vapor (y)
    error=1
    for _ in range(max_iter):
        # Estimar fracción molar líquida inicial (x1) usando la relación de K-values
        x1 = (1 - k[1]) / (k[0] - k[1])
        x = np.array([x1, 1 - x1])
        y = x * k

        try:
            # Configurar las fracciones molares y especificar fase líquida
            TLiq=EOS_TLiq.update(T,P,x)

            # Configurar las fracciones molares y especificar fase vapor
            TGas=EOS_TGas.update(T,P,y)

            # Calcular el error como la diferencia de fugacidades
            error = np.sqrt(np.sum((x * TLiq['phi'] - y * TGas['phi'])**2))

        except:
            # Manejar errores específicos de CoolProp reiniciando las fracciones molares
            x = np.array([0.9990, 0.0001])
            k = y / x
            continue

        # Comprobar la convergencia usando un criterio de tolerancia
        if error < tol*10:
            del EOS_TGas,EOS_TLiq
            return {'c': [x, y], 'converg': True,'error':error}

        # Actualizar los K-values usando la corrección de la fugacidad
        k = k * (x * TLiq['phi']/ (y * TGas['phi'] ))

    # Si no se alcanza la convergencia después de las iteraciones, devolver resultados no convergentes
    del EOS_TGas,EOS_TLiq
    return {'c': [x, y], 'converg': False,'error':error}

def Solubilidad_Gas(T, P, z1, max_iter=100, tol=1E-6):
    # Función para calcular la solubilidad de un gas en una mezcla

    a = np.array(['H2O', 'H2', 'O2'])  # Especies en la mezcla

    z=np.round(z1*(100/(tol)))*tol/100

    yphase = np.array([0, 1, 1])       # Fracciones molares en fase vapor

    # Verificar si la mezcla es un único componente puro
    if len(z[z == 1]) == 1:
        q = yphase[z == 1][0]
        
        # Configurar el estado para el componente puro
        EOS_sis=Sistema(a[z == 1][0])
        sis=EOS_sis.update(T,P)
        
        del EOS_sis
        return {'c':[z,z],'q':q,'Liq':sis if q==0 else None,'Gas':sis if q==1 else None,'error':tol,'converg':True}

    # Verificar si no hay agua en la mezcla
    if z[0] == 0:
        x = z
        y = z
        q = 1

        # Configurar el estado para las especies restantes
        EOS_sis=Sistema(a[z > 0],phase='Gas')
        sis=EOS_sis.update(T,P,z=z[z > 0])

        del EOS_sis
        return {'c':[z,z],'q':q,'Liq':None,'Gas':sis,'error':tol,'converg':True}

    def rachford_rice(q, k, z):
        # Ecuación de Rachford & Rice modificada para resolver por fsolve
        return np.sum(z * (k - 1) / (1 + q * (k - 1)))

    # Verificar si hay dos especies en la mezcla
    if len(z[z > 0]) == 2:

        x = np.array([0.0, 0.0, 0.0])
        y = np.array([0.0, 0.0, 0.0])

        # Resolver el equilibrio de fases binario (VLE) usando BinarieVLE
        s = BinarieVLE(T, P, a[z > 0], max_iter=max_iter, tol=tol)
        x[z > 0] = s['c'][0]
        y[z > 0] = s['c'][1]

        if not s['converg']:
            return {'c':[z,z],'q':-1,'Liq':None,'Gas':None,'error':1,'converg':False}

        #identifica si esta todo disuelto
        if z[z > 0][1] < x[z > 0][1]:
            EOS_sis=Sistema(a[z > 0],phase='Liq')
            sis=EOS_sis.update(T,P,z=z[z > 0])
            del EOS_sis
            return {'c':[z,z],'q':0,'Liq':sis,'Gas':None,'error':tol,'converg':True}

        k = y[z > 0] / x[z > 0]
        bmin = 1 / (1 - max(k))
        bmax = 1 / (1 - min(k))

        # Resolver por fsolve la ecuación de Rachford & Rice para obtener q
        q = np.abs(sop.fsolve(lambda q: np.abs(rachford_rice(np.abs(q), k, z[z > 0])), x0=(bmin + bmax) / 2, xtol=1E-11))[0]
        
        # Calcular propiedades para la fase líquida
        EOS_sisL=Sistema(a[z > 0],phase='Liq')
        sisL=EOS_sisL.update(T,P,z=x[z > 0])
        del EOS_sisL

        # Calcular propiedades para la fase vapor
        EOS_sisV=Sistema(a[z > 0],phase='Gas')
        sisV=EOS_sisV.update(T,P,z=y[z > 0])
        del EOS_sisV
        
        return {'c':[x,y],'q':q,'Liq':sisL,'Gas':sisV,'error':np.sqrt(s['error']**2+rachford_rice(q, k, z[z>0])**2),'converg':True}

    # Resolver para mezclas con más de dos especies
    
    if z[0]<0.99:
        pr=PuntoRocio2(T,z,a,tol=tol)
        #print(np.round(pr*1e-5,3),np.round(P*1e-5,3))
        if np.round(pr*1e-5,3)>=np.round(P*1e-5,3):
            EOS_sisV=Sistema(a,phase='Gas')
            sisV=EOS_sisV.update(T,P,z=z)
            del EOS_sisV

            return {'c':[z,z],'q':1,'Liq':None,'Gas':sisV,'error':tol,'converg':True}
    else:
        pb=PuntoBurbuja2(T,z,a,tol=tol)
        #print(np.round(pb*1e-5,3),np.round(P*1e-5,3))
        if np.round(pb*1e-5,3)<=np.round(P*1e-5,3):
            EOS_sisL=Sistema(a,phase='Liq')
            sisL=EOS_sisL.update(T,P,z=z)
            del EOS_sisL

            return {'c':[z,z],'q':0,'Liq':sisL,'Gas':None,'error':tol,'converg':True}
    
    # Obtener propiedades críticas y acentricidades para las especies
    # w = np.array([cp.PropsSI('acentric', es) for es in a])
    # Tc = np.array([cp.PropsSI('TCRIT', es) for es in a])
    # Pc = np.array([cp.PropsSI('PCRIT', es) for es in a])
    #k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))
    k = np.array([1-0.5-0.4,0.5,0.4])/np.array([1-2*0.005,0.005,0.005])
    la=1
    gama=1

    # Configurar las fracciones molares y especificar fase líquida
    EOS_Liq=Sistema(components=a, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_Gas=Sistema(components=a, phase='Gas')


    for i in range(max_iter):

        # Whitson & Michelsen (1989)
        bmin = 1 / (1 - max(k))
        bmax = 1 / (1 - min(k))

        # Resolver por fsolve la ecuación de Rachford & Rice para obtener q
        q = sop.fsolve(lambda q: rachford_rice(q, k, z), x0=(bmin + bmax) / 2)[0]

        # Estimar fracciones molares líquidas (x) y vapor (y)
        if q>1:
            y=z
            x=np.array([1-2*0.005,0.005,0.005])
            k=y/x
        elif q<0:
            x=z
            y = x*k
        else:
            x = np.abs(z / (1 + q * (k - 1)))
            x=x/x.sum()
            y = k * x
            y=y/y.sum()
        
        # Configurar el estado para la fase líquida y calcular propiedades
        sisL=EOS_Liq.update(T=T,P=P,z=x)

        # Configurar el estado para la fase vapor y calcular propiedades
        sisV=EOS_Gas.update(T=T,P=P,z=y)

        # Calcular el error como la diferencia de fugacidades
        error = np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2))
        # Comprobar la convergencia usando un criterio de tolerancia
        if error < tol*10:
            # Verificar si la ecuación de Rachford & Rice es cercana a cero
            if np.abs(rachford_rice(q, k, z)) < tol:
                if abs(q)<=1 and q>=0:

                    del EOS_Liq,EOS_Gas         
                    return {'c':[x,y],'q':q,'Liq':sisL,'Gas':sisV,'error':np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2)+rachford_rice(q, k, z)**2),'converg':True}


        # Actualizar los K-values usando el modelo de Mehra et al. (1983)
        fr= (x * sisL['phi'] / (y * sisV['phi']))
        if i>0:
            if error>f_error:
                la= -1*la*0.93
        
        #print(f'iteracion: {i}, error : {error}, k: {k}')
        k = k * (fr**la)
        f_error=error

    # Si no se alcanza la convergencia después de las iteraciones, devolver resultados no convergentes
    del EOS_Liq,EOS_Gas 
    return {'c':[z,z],'q':-1,'Liq':None,'Gas':None,'error':np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2)+rachford_rice(q, k, z)**2),'converg':False}



def PuntoBurbuja(T,x,Es,tol=1E-6):
    w = np.array([cp.PropsSI('acentric', es) for es in Es])
    Tc = np.array([cp.PropsSI('TCRIT', es) for es in Es])
    Pc = np.array([cp.PropsSI('PCRIT', es) for es in Es])
    P = np.sum(x*Pc * np.exp(5.37 * (1 + w) * (1 - Tc / T)))
    #P=cp.PropsSI('P','T',T,'Q',1,'H2O')

    # Configurar las fracciones molares y especificar fase líquida
    EOS_Liq=Sistema(components=Es, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_Gas=Sistema(components=Es, phase='Gas')

    try: 
        def fsol(P):
            sisL=EOS_Liq.update(T,P[0],x)
            k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))
            #k = np.array([1-2*0.4,0.4,0.4])/x
            la=1
            for i in range(10):
                y = k * x
                y=y/y.sum()
                sisV=EOS_Gas.update(T,P[0],y)
                error = np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2))
                if error<10*tol:
                    break
                # Actualizar los K-values usando el modelo de Mehra et al. (1983)
                fr= (x * sisL['phi'] / (y * sisV['phi']))
                if i>0:
                    if error>f_error:
                        la= -1*la*0.93
                
                #print(f'iteracion: {i}, error : {error}, k: {k}')
                k = k * (fr**la)
                f_error=error
            return error
            
        return sop.fsolve(fsol,x0=P)[0]
    finally:
        del EOS_Liq,EOS_Gas

def PuntoRocio(T,y,Es,tol=1E-6):
    # w = np.array([cp.PropsSI('acentric', es) for es in Es])
    # Tc = np.array([cp.PropsSI('TCRIT', es) for es in Es])
    # Pc = np.array([cp.PropsSI('PCRIT', es) for es in Es])
    #P = np.sum(y*Pc * np.exp(5.37 * (1 + w) * (1 - Tc / T)))

    # Configurar las fracciones molares y especificar fase líquida
    EOS_Liq=Sistema(components=Es, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_Gas=Sistema(components=Es, phase='Gas')

    P=cp.PropsSI('P','T',T,'Q',1,'H2O')/(y[0])

    def fsol(s1):
        s=np.abs(s1)
        sisV=EOS_Gas.update(T,s[0],y)
        #k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))
        #k = y/np.array([1-2*0.005,0.005,0.005])
        #la=1
        #for i in range(10):
        #x = y/k
        x=np.array([1-s[1]-s[2],s[1],s[2]])
        sisL=EOS_Liq.update(T,s[0],x)
        #error = np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2))
        # if error<10*tol:
        #     break
        # Actualizar los K-values usando el modelo de Mehra et al. (1983)
        fr= (x * sisL['phi'] / (y * sisV['phi']))
        # if i>0:
        #     if error>f_error:
        #         la= -1*la*0.93
        # #print(f'iteracion: {i}, error : {error}, k: {k}')
        # k = k * (fr**la)
        # f_error=error
        
        
        return fr-1
    P=np.abs(sop.fsolve(fsol,x0=[P,0.005,0.005]))

    del EOS_Gas,EOS_Liq
    return P[0]

def PuntoBurbuja2(T,x,Es,tol=1E-6):
    w = np.array([cp.PropsSI('acentric', es) for es in Es])
    Tc = np.array([cp.PropsSI('TCRIT', es) for es in Es])
    Pc = np.array([cp.PropsSI('PCRIT', es) for es in Es])
    P = np.sum(x*Pc * np.exp(5.37 * (1 + w) * (1 - Tc / T)))

    # Configurar las fracciones molares y especificar fase líquida
    EOS_Liq=Sistema(components=Es, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_Gas=Sistema(components=Es, phase='Gas')

    def fsol(P):
        k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))
        s=np.array([P,*k])
        la=1
        for i in range(100):
            k=s[1:]
            y=k*x
            y=y/y.sum()

            sisL=EOS_Liq.update(T,s[0],x)
            sisV=EOS_Gas.update(T,s[0],y)
            error = np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2))
            if error<10*tol:
                break
            # Actualizar los K-values usando el modelo de Mehra et al. (1983)
            fr= (x * sisL['phi'] / (y * sisV['phi']))
            if i>0:
                if error>f_error:
                    la= -1*la*0.93
            #print(f'iteracion: {i}, error : {error}, k: {k}')
            k = k * (fr**la)
            f_error=error
            s[1:]=s[1:]*(fr**la)
            s[0]=s[0]*np.sqrt(np.sum(fr[1]**2))**la
        
        return s
    #P=np.abs(sop.fsolve(fsol,x0=[P,0.6,0.35]))
    P=fsol(P)
    
    del EOS_Gas,EOS_Liq
    return P[0]

def PuntoRocio2(T,y,Es,tol=1E-6):
    w = np.array([cp.PropsSI('acentric', es) for es in Es])
    Tc = np.array([cp.PropsSI('TCRIT', es) for es in Es])
    Pc = np.array([cp.PropsSI('PCRIT', es) for es in Es])
    #P = np.sum(y*Pc * np.exp(5.37 * (1 + w) * (1 - Tc / T)))
    P=cp.PropsSI('P','T',T,'Q',1,'H2O')/(y[0])

    # Configurar las fracciones molares y especificar fase líquida
    EOS_Liq=Sistema(components=Es, phase='Liq')

    # Configurar las fracciones molares y especificar fase vapor
    EOS_Gas=Sistema(components=Es, phase='Gas')

    def fsol(P):
        k = (Pc / P) * np.exp(5.37 * (1 + w) * (1 - Tc / T))
        k = y/np.array([1-2*0.005,0.005,0.005])
        s=np.array([P,*k])
        #k = y/np.array([1-2*0.005,0.005,0.005])
        la=1
        #for i in range(10):
        #x = y/k
        for i in range(100):
            k=s[1:]
            x = y/k
            x=x/x.sum()
            sisL=EOS_Liq.update(T,s[0],x)
            sisV=EOS_Gas.update(T,s[0],y)
            error = np.sqrt(np.sum((x * sisL['phi'] - (y * sisV['phi']))**2))
            if error<10*tol:
                break
            # Actualizar los K-values usando el modelo de Mehra et al. (1983)
            fr= (x * sisL['phi'] / (y * sisV['phi']))
            if i>0:
                if error>f_error:
                    la= -1*la*0.93
            #print(f'iteracion: {i}, error : {error}, k: {k}')
            k = k * (fr**la)
            f_error=error
            s[1:]=s[1:]*(fr**la)
            s[0]=s[0]*np.sqrt(np.sum(fr[0]**2))**la
        return s
    P=fsol(P)
    del EOS_Gas,EOS_Liq
    return P[0]
        