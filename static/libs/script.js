window.onresize = (ev) => {
    plat_app.camera.aspect=div_3D_plant.clientWidth / div_3D_plant.clientHeight;
    plat_app.camera.updateProjectionMatrix();
    plat_app.renderer.setSize( div_3D_plant.clientWidth, div_3D_plant.clientHeight);
};

window.addEventListener('keydown',function(event){
    if(event.code==='Escape'){

    }
})

const conten_set_info=document.getElementById('conten_set_info');

//plat_app.controls.enabled=true

Input_Value=[
    {
        Title: 'Temperatura de entrada',
        input_data: 20,
        unidad: '°C',
        color: 'red',
        incoText:'T',
        type:1
    },
    {
        Title: 'Presión del cátodo',
        input_data: 25,
        unidad: 'bar',
        color: 'black',
        incoText:'P',
        type:1
    },
    {
        Title: 'Presión del ánodo',
        input_data: 26,
        unidad: 'bar',
        color: 'black',
        incoText:'P',
        type:1
    },
    {
        Title: 'Corriente suministrada',
        input_data: 250,
        unidad: 'A',
        color: 'rgb(224, 66, 245)',
        incoText:'I',
        type:1
    },
    {
        Title: 'Flujo de alimentación',
        input_data: 120,
        unidad: 'L/min',
        color: '#03adfc',
        incoText:'F',
        type:1
    },
    {
        Title: 'Velociodad simulación',
        input_data: 1,
        unidad: 's',
        color: 'white',
        incoText:'<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" class="bi bi-play-fill" viewBox="0 0 16 16"><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393"/></svg>',
        type:2,
        fun:function(even){dinamic_play(even);}
    }
]

function crear_input_value(){
    Input_Value.forEach(item => {
        // Crear el elemento div principal con sus atributos
        let itemInfoDiv = document.createElement('div');
        itemInfoDiv.classList.add('item_info'); 
        itemInfoDiv.style.borderColor = item.color;

        // Crear el elemento h1 dentro del div

        let h1 = document.createElement('h1');
        h1.style.marginLeft = '15px'; 
        if (item.type==2){
            h1 = document.createElement('div');
            h1.classList.add('click_item_info');
            h1.innerHTML=item.incoText;
            h1.style.width='40px';
            h1.style.margin='0px';            
            h1.addEventListener('click', item.fun);
            h1.addEventListener('mouseenter', (event)=>{
                plat_app.controls.enabled=false;
            });
        }else{
            h1.textContent = item.incoText; 
        }
        h1.style.color = item.color; 

        // Crear el elemento div secundario dentro del div principal
        let subDiv = document.createElement('div');

        // Crear el elemento h4 dentro del div secundario
        let h4 = document.createElement('h4');
        h4.textContent = item.Title;
        // h4.style.userSelect='none';

        // Crear el elemento input dentro del div secundario
        let input = document.createElement('input');

        input.onfocus=(e)=>{
            plat_app.controls.enabled=false;
        }

        input.onchange=(e)=>{
            item.input_data=Number(input.value);
            estacionario_calcular();
        }

        input.type = 'number'; 
        input.value = item.input_data; 

        // Crear el segundo elemento h1 dentro del div secundario
        let h1Sub = document.createElement('h1');
        h1Sub.textContent = item.unidad;
        h1Sub.style.fontSize = '15px'; 

        // Agregar los elementos creados a la estructura HTML
        subDiv.appendChild(h4); 
        subDiv.appendChild(input); 
        subDiv.appendChild(h1Sub); 

        itemInfoDiv.appendChild(h1); 
        itemInfoDiv.appendChild(subDiv); 

        conten_set_info.appendChild(itemInfoDiv);

    });
}

socket.on("connect", () => {
    console.log("Conectado"); // true
    estacionario_calcular();
});
  
socket.on("disconnect", () => {
    console.log("Desconectado"); // false
});

socket.on("log_message", (data) => {
    info_activador(data);
});

var infoTimer;
var infoDiv_isHovered = false;
const infoDiv = document.getElementById("info");

// Detectar cuando el ratón entra en el elemento
infoDiv.addEventListener('mouseenter', function () {
    if (infoTimer) {
        clearTimeout(infoTimer);
    }
    if(infoDiv.classList.contains('info_des')){
        infoDiv.classList.remove('info_des');
    }
    infoDiv_isHovered = true;
});

// Detectar cuando el ratón sale del elemento
infoDiv.addEventListener('mouseleave', function () {
    infoDiv_isHovered = false;
    desactivar_info();
});

function print_terminal(msg){
    if(terminal){
        terminal.print(msg);
    }
}


function show_terminal(){
    if(terminal){
        if(terminal.html.parentElement.style.display==='none'){
            terminal.html.parentElement.style.display='block';
        }else{
            terminal.html.parentElement.style.display='none';
        }
    }
}

function info_activador(data, descativar=true) {
    let level;
    let styleClass;

    let logger_map = {
        10: { 'name': 'Debug', style: 'debug' },
        20: { 'name': 'Info', style: 'info' },
        30: { 'name': 'Warning', style: 'warning' },
        40: { 'name': 'Error', style: 'error' }, 
        50: { 'name': 'Critical', style: 'critical' },
        25: { 'name': 'Procesando', style: 'procesando' },
        26: { 'name': 'Cargando', style: 'debug' }
    };

    // Mapea el número de nivel de registro al nombre del nivel y su respectiva clase de estilo
    if (data.level in logger_map) {
        level = logger_map[data.level].name;
        styleClass = logger_map[data.level].style;
    } else {
        level = 'INFO';
        styleClass = 'info_conten';
    }

    if ("info_conten " + styleClass !== infoDiv.className) {
        infoDiv.className = "info_conten " + styleClass;
        // Modifica el contenido de los elementos h4 y h3 con el nivel y mensaje respectivamente
        let infoType = document.getElementById("info_type");
        infoType.innerText = level;
    }

    let infoMessage = document.getElementById("info_mensaje");
    infoMessage.innerText = data.message;
    console.log(data.msg_format);
    print_terminal(data.msg_format);

    // Reiniciar el temporizador si ya está en marcha
    if (infoTimer) {
        clearTimeout(infoTimer);
    }

    // Establecer un nuevo temporizador para desactivar el elemento después de un cierto tiempo (por ejemplo, 5 segundos)
    if(descativar && !infoDiv_isHovered){
        desactivar_info();
    }
}

function desactivar_info(time=5000){
    infoTimer = setTimeout(function () {
        infoDiv.classList.add('info_des');
        if(terminal){
            terminal.html.parentElement.style.display='none';
        }
    }, time); // 5000 milisegundos = 5 segundos
}


socket.on("estacionario_resultado", (data) => {
    let data_serializada=JSON.parse(data);
    if(!(data_serializada.error===undefined)){
        console.log(data_serializada.error);
        return;
    }
    Object.assign(plantadata,data_serializada);
    Object.keys(ventanas).forEach(tipo=>{
        Object.keys(ventanas[tipo]).forEach(key=>{
            show_data_ventana(key,ventanas[tipo][key].type,false);
        });
    });

    update_visual_color();

    update_value_control();
});

function estacionario_calcular(){
    if(!isdinamicactive){
        info_activador({
            'level': 25,
            'message': 'Calculando',
            'msg_format': 'Calculando'
        },false);
        socket.emit("estacionario_calcular", {
            T13:Number(Input_Value[0].input_data+273.15),
            Pan:Number(Input_Value[2].input_data*(1e5)),
            Pca:Number(Input_Value[1].input_data*(1e5)),
            I:Number(Input_Value[3].input_data),
            Q:Number(Input_Value[4].input_data)
        });
    }else{
        socket.emit("modificar_setpoint", {
            T13:Number(Input_Value[0].input_data+273.15),
            Pan:Number(Input_Value[2].input_data*(1e5)),
            Pca:Number(Input_Value[1].input_data*(1e5)),
            I:Number(Input_Value[3].input_data),
            Q:Number(Input_Value[4].input_data)
        });
    }
}

function crear_tabla_propiedades_equipos(data, dom_objeto) {
    // Crear tabla
    let tabla = document.createElement('table');
    tabla.className = 'table_propiedades';

    // Obtener número de flujos (suma de flujos de entrada y salida)
    let num_flujos = Object.keys(data.flujos['Entrada']).length + Object.keys(data.flujos['Salida']).length;

    let titulo = document.createElement('tr');
    let columporpiedades= document.createElement('td');
    columporpiedades.innerText='Propiedades';
    columporpiedades.className = 'head_tabla_p';
    columporpiedades.colSpan=num_flujos+1;
    titulo.appendChild(columporpiedades);

    tabla.appendChild(titulo);

    // Agregar filas para cada propiedad
    Object.keys(data).forEach(key => {
        if (propiedades[key]!==undefined) {
            let row = document.createElement('tr');

            // Nombre de la propiedad
            let colName = document.createElement('td');
            colName.innerText = propiedades[key].name;
            row.appendChild(colName);

            // Valor de la propiedad para cada flujo
            let colValue = document.createElement('td');
            colValue.colSpan = num_flujos;
            colValue.innerText = `${propiedades[key].to(data[key]).toFixed(2)} ${propiedades[key].unidad}`;
            row.appendChild(colValue);

            tabla.appendChild(row);
        }
    });

    // Encabezado para flujos
    let headerFlujos = document.createElement('tr');
    let headerFlujosName = document.createElement('td');
    headerFlujosName.innerText = 'Flujos';
    headerFlujosName.colSpan = num_flujos + 1;
    headerFlujosName.className = 'head_tabla_p';
    headerFlujos.appendChild(headerFlujosName);
    tabla.appendChild(headerFlujos);

    // Encabezados de propiedades y flujos
    let propiedadesRow = document.createElement('tr');
    let propiedadesHeader = document.createElement('td');
    propiedadesHeader.innerText = '';
    propiedadesRow.appendChild(propiedadesHeader);

    Object.keys(data.flujos).forEach(key => {
        Object.keys(data.flujos[key]).forEach(fluido => {
            let headerFluido = document.createElement('td');
            headerFluido.innerText = fluido;
            headerFluido.style.textAlign='center';
            headerFluido.style.borderBottom='var(--border_color)';
            propiedadesRow.appendChild(headerFluido);
        });
    });

    tabla.appendChild(propiedadesRow);

    // Filas de datos para cada propiedad y flujo
    rows={}
    Object.keys(data.flujos).forEach(key => {
        Object.keys(data.flujos[key]).forEach(fluido => {
            Object.keys(propiedades).forEach(prop => {
                if (data.flujos[key][fluido][prop]!==undefined) {
                    if(!rows[prop]){
                        let row = document.createElement('tr');
                        // Nombre de la propiedad
                        let propName = document.createElement('td');
                        propName.innerText = propiedades[prop].name;
                        row.appendChild(propName);
                        rows[prop]=row;
                        tabla.appendChild(rows[prop]);
                    }
                    // Valor de la propiedad para cada flujo
                    let propValue = document.createElement('td');
                    propValue.innerText = `${propiedades[prop].to(data.flujos[key][fluido][prop]).toFixed(2)} ${propiedades[prop].unidad}`;
                    rows[prop].appendChild(propValue);
                }
            });
        });
    });

    // Encabezado para composición
    let headerComposicion = document.createElement('tr');
    let headerComposicionName = document.createElement('td');
    headerComposicionName.innerText = 'Composición';
    headerComposicionName.colSpan = num_flujos + 1;
    headerComposicionName.className = 'head_tabla_p';
    headerComposicion.appendChild(headerComposicionName);
    tabla.appendChild(headerComposicion);

    // Filas de composición para cada elemento
    ['Agua', 'Hidrógeno', 'Oxígeno'].forEach((elemento,index) => {
        let row = document.createElement('tr');

        // Nombre del elemento
        let elementoName = document.createElement('td');
        elementoName.innerText = elemento;
        row.appendChild(elementoName);

        // Valores de composición para cada flujo
        Object.keys(data.flujos).forEach(key => {
            Object.keys(data.flujos[key]).forEach(fluido => {
                let composicionValue = document.createElement('td');
                composicionValue.innerText = `${data.flujos[key][fluido].z[index].toFixed(5)}`;
                row.appendChild(composicionValue);
            });
        });

        tabla.appendChild(row);
    });

    // Agregar la tabla al elemento del DOM especificado
    dom_objeto.appendChild(tabla);
}

function crear_tabla_propiedades_flujo(data, dom_objeto) {
    // Crear tabla
    let tabla = document.createElement('table');
    tabla.className = 'table_propiedades';

    // Obtener número de flujos (suma de flujos de entrada y salida)
    let num_flujos = 3;

    let titulo = document.createElement('tr');
    let columporpiedades= document.createElement('td');
    columporpiedades.innerText='Propiedades';
    columporpiedades.className = 'head_tabla_p';
    columporpiedades.colSpan=num_flujos+1;
    titulo.appendChild(columporpiedades);

    tabla.appendChild(titulo);

    // Agregar filas para cada propiedad
    Object.keys(data).forEach(key => {
        if (propiedades[key]!==undefined) {
            let row = document.createElement('tr');

            // Nombre de la propiedad
            let colName = document.createElement('td');
            colName.innerText = propiedades[key].name;
            row.appendChild(colName);

            // Valor de la propiedad para cada flujo
            let colValue = document.createElement('td');
            colValue.colSpan = num_flujos;
            colValue.innerText = `${propiedades[key].to(data[key]).toFixed(2)} ${propiedades[key].unidad}`;
            row.appendChild(colValue);

            tabla.appendChild(row);
        }
    });

    // Encabezado para flujos
    let headerFlujos = document.createElement('tr');
    let headerFlujosName = document.createElement('td');
    headerFlujosName.innerText = 'Composición';
    headerFlujosName.colSpan = num_flujos + 1;
    headerFlujosName.className = 'head_tabla_p';
    headerFlujos.appendChild(headerFlujosName);
    tabla.appendChild(headerFlujos);

    // Encabezados de propiedades y flujos
    let propiedadesRow = document.createElement('tr');
    let propiedadesHeader = document.createElement('td');
    propiedadesHeader.innerText = '';
    propiedadesRow.appendChild(propiedadesHeader);

    ['Total','Liquida','Gas'].forEach(fase=>{
        let headerFluido = document.createElement('td');
        headerFluido.innerText = fase;
        headerFluido.style.textAlign='center';
        headerFluido.style.borderBottom='var(--border_color)';
        propiedadesRow.appendChild(headerFluido);
    });


    tabla.appendChild(propiedadesRow);

    // Filas de composición para cada elemento
    ['Agua', 'Hidrógeno', 'Oxígeno'].forEach((elemento,index) => {
        let row = document.createElement('tr');

        // Nombre del elemento
        let elementoName = document.createElement('td');
        elementoName.innerText = elemento;
        row.appendChild(elementoName);

        // Valores de composición para cada flujo
        ['z','LiqPhase','GasPhase'].forEach(key => {
            let com =(key==='z')? data.z : data[key].x
            let composicionValue = document.createElement('td');
            if(com){
                composicionValue.innerText = `${com[index].toFixed(5)}`;
            }
            row.appendChild(composicionValue);
        });
        tabla.appendChild(row);
    });
    // Agregar la tabla al elemento del DOM especificado
    dom_objeto.appendChild(tabla);
}

function crear_ventana(elemento,type){

    let ventanaDiv =null;

    if(ventanas[type]===undefined){
        ventanas[type]={};
    }

    if(ventanas[type][elemento]===undefined){
        ventanas[type][elemento]={
            elemento:document.createElement('div'),
            x:20,
            y:20,
            mx0:0,
            my0:0,
            isDragging:false,
            type:type
        };
        ventanaDiv = ventanas[type][elemento].elemento;
        ventanaDiv.classList.add('ventana');
        ventanaDiv.addEventListener('mouseenter',(e)=>{
            plat_app.controls.enabled=false;
        });
        ventanaDiv.addEventListener('mouseleave',(e)=>{
            plat_app.controls.enabled=true;
        });
        ventanaDiv.addEventListener('mousedown', function(event) {
            plat_app.controls.enabled=false;
            Object.keys(ventanas).forEach(tipo=>{
                Object.keys(ventanas[tipo]).forEach(key=>{
                    ventanas[tipo][key].elemento.style.zIndex=1;
                })
            });
            ventanas[type][elemento].elemento.style.zIndex=1000;
            ventanas[type][elemento].mx0 = event.clientX - ventanas[type][elemento].x;
            ventanas[type][elemento].my0 = event.clientY - ventanas[type][elemento].y;
        });
        ventanaDiv.addEventListener('mousemove', function(event) {
            if(event.buttons!=1 && ventanas[type][elemento].isDragging){
                ventanas[type][elemento].isDragging=false;
                ventanas[type][elemento].elemento.style.cursor = 'default';
            }
        });
    }else{
        ventanaDiv = ventanas[type][elemento].elemento;
        ventanaDiv.innerHTML='';
        ventanas[type][elemento].type=type;
    }

    if(ventanas[type][elemento].x+ventanaDiv.getBoundingClientRect().width > window.innerWidth){
        ventanaDiv.style.left=window.innerWidth-ventanaDiv.getBoundingClientRect().width-20+'px';
        ventanas[type][elemento].x=window.innerWidth-ventanaDiv.getBoundingClientRect().width-20;
    }
    if(ventanas[type][elemento].y<0){
        ventanaDiv.style.top=20+'px';
        ventanas[type][elemento].y=20;
    }
    if(ventanas[type][elemento].x<0){
        ventanaDiv.style.left=20+'px';
        ventanas[type][elemento].x=20;
    }

    Object.keys(ventanas).forEach(tipo=>{
        Object.keys(ventanas[tipo]).forEach(key=>{
            ventanas[tipo][key].elemento.style.zIndex=1;
        })
    });

    ventanas[type][elemento].elemento.style.zIndex=1000;

    let ventanaTituloDiv = document.createElement('div');

    ventanaTituloDiv.addEventListener('mousedown', function(event) {
        plat_app.controls.enabled=false;
        ventanas[type][elemento].isDragging = true;
    });

    ventanaTituloDiv.addEventListener('mouseup', function(event) {
        ventanas[type][elemento].isDragging = false;
        ventanas[type][elemento].elemento.style.cursor = 'default';
    });

    ventanaTituloDiv.addEventListener('mousemove',function(event){
        if(ventanas[type][elemento].isDragging){
            ventanas[type][elemento].elemento.style.cursor = 'move';
        }
    });

    $(ventanaDiv).draggable({ handle: ventanaTituloDiv});

    ventanaDiv.style.position='absolute';

    ventanaTituloDiv.classList.add('ventana_titulo');

    let tituloH4 = document.createElement('h4');
    tituloH4.textContent = elemento;
    ventanaTituloDiv.appendChild(tituloH4);

    let closeDiv = document.createElement('div');
    closeDiv.classList.add('ventana_close');
    closeDiv.addEventListener('click',(e)=>{
        ventanas[type][elemento].isDragging=false;
        ventanas[type][elemento].elemento.style.cursor = 'default';
        plat_app.controls.enabled=true;
        ventanas[type][elemento].elemento.remove();
    });
    closeDiv.textContent = 'x';
    ventanaTituloDiv.appendChild(closeDiv);
    ventanaDiv.appendChild(ventanaTituloDiv);

    show_data_ventana(elemento,type);
}

function show_data_ventana(elemento,type,add=true){
    let contenedorDiv =null;
    if(ventanas[type][elemento].elemento.getElementsByClassName('table_contenedor').length==0){
        contenedorDiv = document.createElement('div');
        contenedorDiv.classList.add('table_contenedor');
    
        ventanas[type][elemento].elemento.appendChild(contenedorDiv);
    }else{
        contenedorDiv = ventanas[type][elemento].elemento.getElementsByClassName('table_contenedor')[0];
        contenedorDiv.innerHTML='';
    }

    if(type==1){
        let contenedorPestañas=document.createElement('div');
        contenedorPestañas.classList.add('Pestaña_conten');

        if(Object.keys(plantadata.Equipos[elemento]).includes('graficas')){
            let graficasPestaña = document.createElement('div');
            graficasPestaña.classList.add('Pestaña');
            graficasPestaña.addEventListener('click',(e)=>{
                crear_ventana(elemento,3);
            });
            graficasPestaña.innerHTML=plantadata.Equipos[elemento].graficas.name;
            contenedorPestañas.appendChild(graficasPestaña);
        }
        contenedorDiv.appendChild(contenedorPestañas);
    }

    if(add){
        document.body.appendChild(ventanas[type][elemento].elemento);
    }

    if(type==1){
        crear_tabla_propiedades_equipos(plantadata.Equipos[elemento], contenedorDiv);
    }else if(type==2){
        crear_tabla_propiedades_flujo(plantadata.Flujos[elemento],contenedorDiv);
    }else if(type==3){
        crear_grafico_Ventana(plantadata.Equipos[elemento],contenedorDiv);
    }else if(type==4){
        valve_slider(contenedorDiv, plantadata.Valvulas[elemento]);
    }else if(type==5){
        crear_dinamico_Ventana(plantadata.Equipos[elemento],contenedorDiv);
    }else if(type==6){
        crear_PID_ventana(contenedorDiv);
    }

    if(ventanas[type][elemento].y+ventanas[type][elemento].elemento.getBoundingClientRect().height > window.innerHeight){
        ventanaDiv.style.top=window.innerHeight-ventanaDiv.getBoundingClientRect().height-20+'px';
        ventanas[type][elemento].y=window.innerHeight-ventanaDiv.getBoundingClientRect().height-20;
    }
}

function crear_grafico_Ventana(data, dom_objeto) {
    if(!ventanas[3][data.name].graficas){
        ventanas[3][data.name].graficas={}
    }
    data.graficas.graps.forEach((grafica, i) => {
        let grafica_contenedor = document.createElement('div');
        grafica_contenedor.classList.add('grafica_contenedor');
        dom_objeto.appendChild(grafica_contenedor);
        let grafica_div = document.createElement('div');
        grafica_div.id = data.name + '-grafica-normal-' + (i + 1);
        grafica_div.classList.add('graficas');
        grafica_contenedor.appendChild(grafica_div);
        crear_grafico(grafica_div.id, grafica, ventanas[3][data.name].graficas);
    });
}

function crear_grafico(elemento_name, config, listgrafic) {
    let data=[]
    config.trazas[0].x.forEach((xi,i)=>{
        point=[xi]
        config.trazas.forEach(traza=>{
            point.push(traza.y[i])
        })
        data.push(point)
    })

    let labels=['tiempo min']
    config.trazas.forEach(traza=>{
        labels.push(traza.name)
    })


    const dygraphOptions = {
        labels: labels,
        colors: config.trazas.map(traza => traza.color),
        strokeWidth: 1.5,
        title: config.title,
        titleHeight: 20,
        xlabel: config.xlabel,
        xLabelHeight:15,
        ylabel: config.ylabel1,
        axes: {
            x: {
                gridLineColor: 'rgba(255, 255, 255, 0.3)',
                //axisLabelColor: 'white',
                axisLineColor: 'rgba(255, 255, 255, 0.5)',
            },
            y: {
                gridLineColor: 'rgba(255, 255, 255, 0.3)',
                //axisLabelColor: 'white',
                axisLineColor: 'rgba(255, 255, 255, 0.5)',
            }
        },
        // labelsDivStyles: {
        //     color: 'white'
        // },
        legend: 'always',
        //showLabelsOnHighlight: true,
        highlightSeriesOpts: {
            strokeWidth: 2,
        },
        highlightSeriesBackgroundColor: 'rgb(0, 0, 0)',
        highlightSeriesBackgroundAlpha :1,
        resizable: "both",
    };

    if (config.ylabel2) {
        dygraphOptions.y2label = config.ylabel2;
        dygraphOptions.axes.y2 = {
            axisLabelColor: 'white',
            gridLineColor: 'rgba(255, 255, 255, 0.3)',
            axisLineColor: 'rgba(255, 255, 255, 0.5)',
        };
        dygraphOptions.series={};
        dygraphOptions.series[labels[labels.length-1]]={
            axis: 'y2'
        }
    }

    // Remove existing plot if any
    const graphContainer = document.getElementById(elemento_name);
    if (graphContainer) {
        graphContainer.innerHTML = '';
    }
    console.log(dygraphOptions);
    dygraph = new Dygraph(graphContainer, data, dygraphOptions);
    listgrafic[elemento_name]=dygraph;

}




function valve_slider(container, data) {

    container.parentElement.style.width='200px';
    container.parentElement.style.height='110px';

    let divcontenedor=document.createElement('div');
    divcontenedor.classList.add('valve-range-div');
    container.appendChild(divcontenedor);

    let rsRangeLine = document.createElement('input');
    rsRangeLine.classList.add('valve-range-input');
    rsRangeLine.setAttribute('type', 'range');
    rsRangeLine.setAttribute('value', '0');
    rsRangeLine.setAttribute('min', '0');
    rsRangeLine.setAttribute('max', '100');
    rsRangeLine.setAttribute('step', '0.00001');

    divcontenedor.appendChild(rsRangeLine);

    let divtextconten=document.createElement('div');
    divtextconten.className='valve-range-div-label-conten';

    let h4label=document.createElement('h4');
    h4label.textContent='Apertura:';
    divtextconten.appendChild(h4label);

    let h4label2=document.createElement('h4');
    h4label2.textContent='0%';
    divtextconten.appendChild(h4label2);

    divcontenedor.appendChild(divtextconten);

    rsRangeLine.addEventListener("input", showSliderValue, false);
    
    updatevaluevale(
        h4label2,
        rsRangeLine,
        data.apertura
    )

    ventanas[4][data.name]['slider']=rsRangeLine;
    ventanas[4][data.name]['label']=h4label2;
    ventanas[4][data.name]['activo']=data.control.activo;

    showSliderValue();

    // rsBullet.innerHTML=data.apertura.toFixed(0)
    // let bulletPosition = (data.apertura/rsRangeLine.max);
    // rsBullet.style.left = (bulletPosition * 578) + "px";

    function showSliderValue() {
        if(Number(rsRangeLine.value)>0){
            socket.emit("valve", {
                valvula:data.name,
                apertura:Number(rsRangeLine.value)
            });
        }
    }
}

function updatevaluevale(label,input,value){
    label.textContent=value.toFixed(2)+'%';
    input.value=value;
}

socket.on("valve", (data) => {
    let data_serializada=JSON.parse(data);
    updatevaluevale(
        ventanas[4][data_serializada.name]['label'],
        ventanas[4][data_serializada.name]['slider'],
        data_serializada.apertura
    )
    ventanas[4][data_serializada.name].value=data_serializada.apertura;
});


function crear_PID_ventana(contenedorDiv){

    if(pid===null){
        let PID_layout_diagram_element=document.createElement('div');
        PID_layout_diagram_element.classList.add('PID-layout-diagram');
        PID_layout_diagram_element.id='pid-ventana';

        contenedorDiv.appendChild(PID_layout_diagram_element);

        pid=new PIDDiagram('pid-ventana',true);
        pid.loadData('./assets/planta.json','./libs/PIDjs/symbols').then(()=>{
            pid.containerElement.addEventListener('mouseenter',(event)=>{
                plat_app.controls.enabled=false;
            });


            Object.keys(pid.equiments).forEach(equipo=>{
                pid.equiments[equipo].on('mouseover',(event)=>{
                    pid_selec(equipo);
                    plat_app.select(plat_app.Scene_objects[equipo].obj);
                });

                pid.equiments[equipo].on('mouseout',(event)=>{
                    pid_selec(equipo,false);
                });

                pid.equiments[equipo].on('tap',(event)=>{
                    plat_app.click();
                });
            });

            Object.keys(pid.controlelement).forEach(controlkey=>{
                pid.controlelement[controlkey].on('tap',(event)=>{
                    socket.emit("get_PID_control", {
                        id:controlkey.split('_')[2],
                        nodeid:controlkey
                    });
                });
            });
        });
        
    }else{
        contenedorDiv.appendChild(pid.containerElement);
    }

    update_value_control();

}

function pid_selec(equipo,on=true){
    if(pid.equiments[equipo]){
        pid.equiments[equipo].style('background-color', on? '#008a84' : 'white');
        pid.equiments[equipo].style('background-opacity', on? 0.3 : 0);
    }
}

function crearNodeVentanaEdicion(config) {
    // Crear el contenedor principal
    let nodeWindows = document.createElement('div');
    nodeWindows.className = 'node-windows';

    // Crear la cabecera de la ventana
    let nodeWindowsHead = document.createElement('div');
    nodeWindowsHead.className = 'node-windows-head';

    nodeWindowsHead.addEventListener('mousedown',()=>{
        nodeWindowsHead.style.cursor='move';
    });

    nodeWindowsHead.addEventListener('mouseup',()=>{
        nodeWindowsHead.style.cursor='auto';
    });

    let headCircle1 = document.createElement('div');
    headCircle1.className = 'node-windows-head-cicle';

    let headTitle = document.createElement('h4');
    headTitle.textContent = config.title;

    let headCircleClose = document.createElement('div');
    headCircleClose.className = 'node-windows-head-cicle';

    headCircleClose.classList.add('close');

    // Agregar los elementos a la cabecera
    nodeWindowsHead.appendChild(headCircle1);
    nodeWindowsHead.appendChild(headTitle);
    nodeWindowsHead.appendChild(headCircleClose);
    nodeWindows.appendChild(nodeWindowsHead);

    let funs={
        start: function(event, ui) {
        },
        drag: function(event, ui) {
        },
        stop: function(event, ui) {
        },
        closed: (targe)=>{
        }
    }

    headCircleClose.addEventListener('click',()=>{
        nodeWindows.remove();
        funs.closed(nodeWindows);
    });

    $(nodeWindows).draggable({
        handle: nodeWindowsHead,
        start: (event, ui)=>{funs.start(event, ui)},
        drag: (event, ui)=>{funs.drag(event, ui)},
        stop: (event, ui)=>{funs.stop(event, ui)}
    });

    nodeWindows.style.position='absolute';

    // Crear las subconfiguraciones
    config.subconfigs.forEach(subconfig => {
        let subconfigTitle = document.createElement('h4');

        subconfigTitle.style.margin = '5px';
        subconfigTitle.style.fontSize = '10.5px';
        subconfigTitle.textContent = 'Editor de configuraciones';

        subconfigTitle.textContent = subconfig.title;

        nodeWindows.appendChild(subconfigTitle);

        // Crear los inputs para cada subconfiguración
        subconfig.inputs.forEach(inputConfig => {
            let inputDiv = document.createElement('div');
            inputDiv.className = 'node-windows-input';

            let inputLabel = document.createElement('h4');
            inputLabel.textContent = inputConfig.name;

            let inputElement = document.createElement('input');
            inputElement.type = inputConfig.type;
            if(inputConfig.type!=='checkbox'){
                inputElement.value = inputConfig.value;
            }else{
                inputElement.checked=inputConfig.value;
            }

            inputElement.addEventListener('change', (event) => {
                inputConfig.fun(event);
            });

            inputElement.addEventListener('wheel', function(event) {
                event.preventDefault();
                if(document.activeElement !== inputElement){
                    return;
                }
                inputElement.value=(parseFloat(inputElement.value)-event.deltaY/100).toFixed(5);
                inputConfig.fun(event);
            });

            inputConfig.element=inputElement;

            // Agregar los elementos a la sección de entrada de la constante
            if (inputConfig.type === 'number') {
                let inputArrowLeft = document.createElement('div');
                inputArrowLeft.className = 'node-windows-input-arrow left';

                inputArrowLeft.addEventListener('click',(event)=>{
                    inputElement.value=(parseFloat(inputElement.value)-0.1).toFixed(5);
                    inputConfig.fun(event);
                });

                inputDiv.appendChild(inputArrowLeft);
            }
            inputDiv.appendChild(inputLabel);

            inputDiv.appendChild(inputElement);

            if(inputConfig.type==='checkbox'){
                let checkdiv=document.createElement('div');
                checkdiv.className='checkbox-input-node';

                checkdiv.addEventListener('click',(event)=>{
                    inputElement.checked=!inputElement.checked;
                    let event2={...event};
                    event2.target=inputElement;
                    inputConfig.fun(event2);
                });

                let checkboxCircle=document.createElement('div');
                checkboxCircle.className='checkbox-input-node-cicle';
                checkdiv.appendChild(checkboxCircle);
                inputDiv.appendChild(checkdiv);
            }

            if (inputConfig.type === 'number') {

                let inputArrowRight = document.createElement('div');
                inputArrowRight.className = 'node-windows-input-arrow right';

                inputArrowRight.addEventListener('click',(event)=>{
                    inputElement.value=(parseFloat(inputElement.value)+0.1).toFixed(5);
                    inputConfig.fun(event);
                });

                inputDiv.appendChild(inputArrowRight);
            }

            nodeWindows.appendChild(inputDiv);
        });
    });

    return {element:nodeWindows,data:config, funs:funs};
}

socket.on("get_PID_control", (data) => {
    let dataPID=JSON.parse(data);

    create_type_node('PID');

    dataPID,nodeVentanas['PID'][dataPID.input.id]=create_config_node(
        'PID',
        dataPID,
        nodeVentanas['PID'][dataPID.input.id]
    );
    
    if(ventanas[4] && ventanas[4]['VC'+dataPID.input.id]){
        ventanas[4]['VC'+dataPID.input.id]['activo']=dataPID.data.activo;
    }

    nodeVentanas['PID'][dataPID.input.id].PIDcontroler=dataPID.data;
    nodeVentanas['PID'][dataPID.input.id].PIDcontroler.loop='VC'+dataPID.input.id;
});

function configplatilla(type, data){
    let platilla = platillastylenodeconfig(data);
    return platilla[type] || {};
}

function create_config_node(type,data,nodeV){
    let nodeVentana = nodeV;
    if(nodeVentana===undefined){
        nodeVentana=crearNodeVentanaEdicion(configplatilla(type, data));
        let nodes=creat_node_diagram(nodeVentana,data);
        nodeVentana.node=nodes.node;
        nodeVentana.line_nodes=nodes.edge;
    }

    if (!pid.containerElement.contains(nodeVentana.element)) {
        pid.containerElement.appendChild(nodeVentana.element);
        pid.cy.add(nodeVentana.node);
        pid.cy.add(nodeVentana.line_nodes);
    }

    let rectsize=nodeVentana.element.getBoundingClientRect();

    nodeVentana.node.style({
        'width':rectsize.width/pid.cy.zoom(),
        'height':rectsize.height/pid.cy.zoom(),
    });

    node_update_ventana(nodeVentana.node, nodeVentana.element);
    update_value_node_config(nodeVentana, data.data);

    return nodeVentana
}

function update_value_node_config(nodeVentana, data){
    nodeVentana.data.subconfigs.forEach(subconfig=>{
        subconfig.inputs.forEach(input=>{
            if(input.type!=='checkbox'){
                input.element.value=data[input.key];
            }else{
                input.element.checked=data[input.key];
            }
        });
    });
}

function update_value_control(){
    if(!nodeVentanas['PID']){
        return;
    }

    Object.keys(plantadata.Valvulas).forEach(valvula=>{
        if(nodeVentanas['PID'][valvula.replace('VC','')]){
            update_value_node_config(nodeVentanas['PID'][valvula.replace('VC','')],plantadata.Valvulas[valvula].control);
            nodeVentanas['PID'][valvula.replace('VC','')].PIDcontroler=plantadata.Valvulas[valvula].control;
        }
    })
}

function send_PID_controller(event, parameter, id) {
    const value = parseFloat(event.target.value);
    const pidController = nodeVentanas['PID'][id].PIDcontroler;

    if (!isNaN(value)) {
        pidController[parameter] = value;
        socket.emit("lazo", pidController);
    } else {
        console.error("Invalid value for parameter:", parameter);
    }
}

function active_PID_Controller(event,id){
    event.target.parentElement.childNodes[0].textContent = event.target.checked? 'Lazo cerrado': 'Lazo abierto';
    nodeVentanas['PID'][id].PIDcontroler.activo=event.target.checked;
    if(ventanas[4] && ventanas[4]['VC'+id]){
        ventanas[4]['VC'+id]['activo']=event.target.checked;
    }
    socket.emit("lazo", nodeVentanas['PID'][id].PIDcontroler);
}

function creat_node_diagram(nodeVentana,data){
    let node_diagram_pos=pid.cy.$('#'+data.input.nodeid+'-diagram').position();

    let node=pid.cy.add({
        group: 'nodes',
        data: { id: 'n3-windows-control-'+data.input.id},
    });

    nodeVentana.element.style.transformOrigin = "0 0";

    node.style({
        'width':1,
        'height':1,
        'shape': 'rectangle',
        'background-opacity':0
    });

    node.position(
        {
            x:node_diagram_pos.x+pid.cy.$('#'+data.input.nodeid+'-diagram').with()/2,
            y:node_diagram_pos.y+pid.cy.$('#'+data.input.nodeid+'-diagram').height()/2
        }
    );

    let line_nodes=pid.cy.add([
        {
            group: 'edges',
            data: {
                id: 'edge-line-control-'+data.input.id,
                source: data.input.nodeid+'-diagram',
                target: 'n3-windows-control-'+data.input.id
            }
        }
    ]);

    line_nodes.style({
        'width': 0.5,
        'line-color': pid.isblackstyle? 'white' :'black',
        'target-arrow-color': pid.isblackstyle? 'white' :'black',
        'target-arrow-shape': 'none',
        'line-color': pid.isblackstyle? 'white' :'black',
        "curve-style": "round-taxi",
        "taxi-radius": 50
    });

    node_windows_updatepost(node, nodeVentana.element);

    nodeVentana.funs.drag=function(event, ui){
        node_update_ventana(node, nodeVentana.element);
    }

    nodeVentana.funs.closed=(ventana)=>{
        line_nodes.remove();
        node.remove();
    }

    pid.cy.on('pan', function() {
        node_windows_updatepost(node, nodeVentana.element);
    });


    pid.cy.on('zoom', function() {
        node_windows_updatepost(node, nodeVentana.element);
    })

    return {node:node, edge:line_nodes}
}


function node_update_ventana(node, nodeWindowelement){
    let rect=nodeWindowelement.getBoundingClientRect();

    node.renderedPosition({
        x:Number(nodeWindowelement.style.left.split('px')[0])+rect.width/2,
        y:Number(nodeWindowelement.style.top.split('px')[0])+rect.height/2
    });
}

function create_type_node(type){
    if (nodeVentanas[type]===undefined){
        nodeVentanas[type]={}
    }
}

function node_windows_updatepost(node, nodeWindowelement){

    let position = node.renderedPosition();

    nodeWindowelement.style.transform= `scale(${pid.cy.zoom()*0.5})`;

    nodeWindowelement.style.top=position.y-node.height()*pid.cy.zoom()/2+'px';
    nodeWindowelement.style.left=position.x-node.width()*pid.cy.zoom()/2+'px';

}

function clarcolorbar(){
    const colorBarCanvas = document.getElementById('colorbar');
    const context = colorBarCanvas.getContext('2d');
    context.clearRect(0, 0, colorBarCanvas.width, colorBarCanvas.height);
}

function createColorBar(min, max, steps, unidad, tinks = 10, palette='jet') {
    const colorBarCanvas = document.getElementById('colorbar');
    const context = colorBarCanvas.getContext('2d');

    // Limpiar el canvas antes de dibujar
    context.clearRect(0, 0, colorBarCanvas.width, colorBarCanvas.height);

    for (let i = 0; i < steps; i++) {
        // Calcular el valor para el color
        const value = max - (max - min) * (i / (steps - 1));
        const rgb_color=getColorForValue(value, min, max, palette);
        const color = `rgb(${rgb_color.r},${rgb_color.g},${rgb_color.b})`;
        context.fillStyle = color;

        // Dibuja el rectángulo correspondiente en la barra de colores
        context.fillRect(0, (colorBarCanvas.height * i) / (steps - 1), 27, colorBarCanvas.height / (steps - 1) + 1);
    }

    // Dibujar la línea central
    context.beginPath();
    context.moveTo(31, 0);
    context.lineTo(31, colorBarCanvas.height);
    context.lineWidth = 1; // Cambiar el grosor de la línea si es necesario
    context.strokeStyle = 'rgb(10,10,10)'; // Establecer el color de la línea
    context.stroke();

    context.strokeStyle = 'rgb(10,10,10)'; 
    for (let i = 0; i < tinks; i++) {
        const value = max - (max - min) * (i / (tinks - 1));
        context.beginPath();
        context.moveTo(31, (colorBarCanvas.height * i) / (tinks - 1));
        context.lineTo(45, (colorBarCanvas.height * i) / (tinks - 1));
        context.lineWidth = 1; // Grosor de las líneas de tinks
        context.stroke();

        context.font = "10px Arial";
        context.fillStyle = 'black';
        context.fillText(value.toFixed(1)+" "+unidad,35,(colorBarCanvas.height * i) / (tinks - 1)-3);
    }
}

function getColorForValue(value, min, max, style = 'jet') {
    const normalizedValue = Math.min(Math.max((value - min) / (max - min), 0), 1);

    const palettes = {
        jet: [
            [0, 0, 128],   // Azul oscuro
            [0, 0, 255],   // Azul
            [0, 255, 255], // Cian
            [0, 255, 0],   // Verde
            [255, 255, 0], // Amarillo
            [255, 0, 0],   // Rojo
            [128, 0, 0]    // Rojo oscuro
        ],
        grayscale: [
            [0, 0, 0],     // Negro
            [255, 255, 255] // Blanco
        ],
        rainbow: [
            [148, 0, 211], // Violeta
            [75, 0, 130],  // Índigo
            [0, 0, 255],   // Azul
            [0, 255, 0],   // Verde
            [255, 255, 0], // Amarillo
            [255, 127, 0], // Naranja
            [255, 0, 0]    // Rojo
        ],
        inferno: [
            [0, 0, 0],     // Negro
            [31, 12, 72],  // Azul oscuro
            [85, 15, 109], // Morado oscuro
            [187, 55, 84], // Rojo púrpura
            [249, 142, 0], // Naranja
            [252, 255, 164] // Amarillo claro
        ],
        viridis: [
            [68, 1, 84],   // Azul oscuro
            [72, 40, 120], // Púrpura
            [54, 92, 141], // Azul
            [39, 140, 142],// Verde azulado
            [31, 186, 114],// Verde
            [74, 220, 65], // Verde claro
            [253, 231, 37] // Amarillo
        ]
    };

    const colors = palettes[style] || palettes['jet'];

    const steps = colors.length - 1;

    const scaledValue = normalizedValue * steps;
    const index = Math.floor(scaledValue);
    const ratio = scaledValue - index;

    const colorStart = colors[index];
    const colorEnd = colors[Math.min(index + 1, steps)];

    const r = Math.round(colorStart[0] + (colorEnd[0] - colorStart[0]) * ratio);
    const g = Math.round(colorStart[1] + (colorEnd[1] - colorStart[1]) * ratio);
    const b = Math.round(colorStart[2] + (colorEnd[2] - colorStart[2]) * ratio);

    return {r: r, g: g, b: b};
}

function get_min_max(variable) {
    if (!plantadata.Flujos || Object.keys(plantadata.Flujos).length === 0) {
        return { min: null, max: null }; 
    }

    let { min, max } = Object.keys(plantadata.Flujos).reduce((acc, flujo) => {
        let value = plantadata.Flujos[flujo][variable];
        if (value > acc.max) {
            acc.max = value;
        }
        if (value < acc.min) {
            acc.min = value;
        }
        return acc;
    }, { min: Infinity, max: -Infinity });
    return { min: propiedades[variable].to(min), max: propiedades[variable].to(max) };
}

function visual_color_map(variable, palette='jet'){

    if(!propiedades[variable]){
        Object.keys(plantadata.Equipos).forEach(equipo=>{
            plat_app.Scene_objects[equipo].color=null;
            plat_app.objecto_emissive(plat_app.Scene_objects[equipo].obj,0x000000);
        });
    
        Object.keys(plantadata.Flujos).forEach(flujo=>{
            plat_app.Scene_objects[flujo].color=null;
            plat_app.objecto_emissive(plat_app.Scene_objects[flujo].obj,0x000000);
        });

        clarcolorbar();
        return;
    }

    let { min, max }=get_min_max(variable);
    createColorBar(min, max, 100, propiedades[variable].unidad, 10 ,palette);
    Object.keys(plantadata.Equipos).forEach(equipo=>{
        let value=get_equipo_max_varible(variable,plantadata.Equipos[equipo]);
        let {r,g,b}=getColorForValue(value, min, max, palette);
        plat_app.Scene_objects[equipo].color=new plat_app.THREE.Color(r/255,g/255,b/255);
        plat_app.objecto_emissive(plat_app.Scene_objects[equipo].obj,0x000000);
    });

    Object.keys(plantadata.Flujos).forEach(flujo=>{
        let {r,g,b}=getColorForValue(propiedades[variable].to(plantadata.Flujos[flujo][variable]), min, max, palette);
        plat_app.Scene_objects[flujo].color=new plat_app.THREE.Color(r/255,g/255,b/255);
        plat_app.objecto_emissive(plat_app.Scene_objects[flujo].obj,0x000000);
    });
}

function get_equipo_max_varible(variable,equipo){
    let max=-Infinity;
    if(!equipo[variable]){
        Object.keys(equipo.flujos).forEach(flujotype=>{
            Object.keys(equipo.flujos[flujotype]).forEach(flujo=>{
                if (equipo.flujos[flujotype][flujo][variable]>max){
                    max=equipo.flujos[flujotype][flujo][variable];
                }
            });
        });
    }else{
        max=equipo[variable];
    }
    return propiedades[variable].to(max);
}

function change_view_variable(infoElement) {
    let visualizaciones = {
        "Básica": { siguiente: 'T', nombre: 'Temperatura', palette:'jet'},
        "Temperatura": { siguiente: 'P', nombre: 'Presión', palette:'viridis'},
        "Presión": { siguiente: 'F', nombre: 'Flujos', palette:'rainbow'},
        "Flujos": { siguiente: null, nombre: 'Básica', palette:'jet'},
    };

    let currentView = infoElement.querySelector('.info_type-view-name').textContent;

    plantadata.vis = {
        variable:visualizaciones[currentView].siguiente,
        palette:visualizaciones[currentView].palette
    };

    visual_color_map(plantadata.vis.variable,plantadata.vis.palette);

    infoElement.querySelector('.info_type-view-name').textContent = visualizaciones[currentView].nombre;
}

function update_visual_color(){
    if(plantadata.vis && plantadata.vis.variable){
        visual_color_map(plantadata.vis.variable,plantadata.vis.palette);
    }
}
