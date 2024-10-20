var isdinamicactive=false;


function dinamic_play(even){
    if(isdinamicactive){
        info_activador({
            'level': 25,
            'message': 'Simulación dinámica detenida',
            'msg_format': 'Simulación dinámica detenida'
        }, false);
        dinamic_stop();
        isdinamicactive=false;
        return;
    }
    isdinamicactive=true;
    info_activador({
        'level': 25,
        'message': 'Simulación dinámica en progreso',
        'msg_format': 'Simulación dinámica en progreso'
    }, false);
    Object.keys(ventanas).forEach(tipo=>{
        Object.keys(ventanas[tipo]).forEach(key=>{
            ventanas[tipo][key].elemento.remove();
        })
    });
    ventanas={};

    socket.emit("dinamico_activar", {'activo':'on','dt':Number(Input_Value[5].input_data*60)});
}

function dinamic_stop() {
    socket.emit("dinamico_activar", {'activo':'off'});
}



function dinamico_calcular() {
    info_activador({
        'level': 25,
        'message': 'Simulación dinámica en progreso',
        'msg_format': 'Simulación dinámica en progreso'
    }, false);
    ventanas={};
}

function crear_dinamico_Ventana(data, dom_objeto) {
    if(!ventanas[5][data.name].graficas){
        ventanas[5][data.name].graficas={}
    }
    Object.keys(data.dinamico).forEach(key => {
        let grafica_contenedor = document.createElement('div');
        grafica_contenedor.classList.add('grafica_contenedor');
        dom_objeto.appendChild(grafica_contenedor);
        let grafica_div = document.createElement('div');
        grafica_div.id = data.name + '-grafica-dinamica-' + key;
        grafica_div.classList.add('graficas');
        grafica_contenedor.appendChild(grafica_div);
        crear_grafico(grafica_div.id, data.dinamico[key], ventanas[5][data.name].graficas);
    });
}

function actualizar_grafico(elemento_name, config, name) {
    let data=[]
    config.trazas[0].x.forEach((xi,i)=>{
        point=[xi]
        config.trazas.forEach(traza=>{
            point.push(traza.y[i])
        })
        data.push(point)
    })
    ventanas[5][name].graficas[elemento_name].updateOptions( { 'file': data } );
}

socket.on("dinamics_resultado", (data) => {
    console.log('actualizar');
    let data_serializada=JSON.parse(data);
    if(!(data_serializada.error===undefined)){
        console.log(data_serializada.error);
        return;
    }
    Object.assign(plantadata,data_serializada);

    Object.keys(ventanas).forEach(tipo=>{
        Object.keys(ventanas[tipo]).forEach(key=>{
            if (tipo==5){
                Object.keys(plantadata.Equipos[key].dinamico).forEach(grafico => {
                    let elemento_name=key + '-grafica-dinamica-' + grafico;
                    actualizar_grafico(elemento_name, plantadata.Equipos[key].dinamico[grafico],plantadata.Equipos[key].name)
                })
            }else if(tipo==4 && ventanas[4][key]['activo']){

                updatevaluevale(
                    ventanas[4][key]['label'],
                    ventanas[4][key]['slider'],
                    plantadata.Valvulas[key].apertura
                )
            }
        })
    });

});