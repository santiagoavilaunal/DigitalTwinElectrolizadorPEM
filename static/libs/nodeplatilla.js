var platillastylenodeconfig=(data)=>{
    return {
        'PID':{
            title: 'Control PID '+data.input.id,
            subconfigs: [
                {
                    title:'Estado de control',
                    inputs:[
                        {
                            name: data.data.activo? 'Lazo cerrado': 'Lazo abierto', 
                            type: 'checkbox', value: data.data.activo, key:'activo',
                            fun: (event)=>active_PID_Controller(event,data.input.id)
                        },
                        {
                            name: 'Setpoint', type: 'number', value: data.data.setpoint, key:'setpoint', 
                            fun: (event)=>send_PID_controller(event,'setpoint',data.input.id)
                        }
                    ]
                },
                {
                    title: 'Constantes',
                    inputs: [
                        {
                            name: 'Proporcional', type: 'number', value: data.data.Kp, key:'Kp',
                            fun: (event)=>send_PID_controller(event,'Kp',data.input.id)
                        },
                        { 
                            name: 'Integral', type: 'number', value: data.data.Ki, key:'Ki',
                            fun: (event)=>send_PID_controller(event,'Ki',data.input.id)
                        },
                        { 
                            name: 'Derivativo', type: 'number', value: data.data.Kd, key:'Kd',
                            fun: (event)=>send_PID_controller(event,'Kd',data.input.id)
                        }
                    ]
                }
            ]
        }
    }
}