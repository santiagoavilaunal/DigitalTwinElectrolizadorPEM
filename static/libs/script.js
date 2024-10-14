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
        unidad: 'min/s',
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
    console.log(data_serializada);
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
    var div = document.createElement('div');
    div.style.display = 'flex';
    div.style.justifyContent = 'center';

    // Crear el elemento label
    var label = document.createElement('label');
    label.style.color = 'white';
    label.textContent = 'Lazo abierto';

    // Crear el elemento input
    var input = document.createElement('input');
    input.setAttribute('type', 'checkbox');

    // Agregar el label y el input al div
    div.appendChild(label);
    div.appendChild(input);

    // Agregar el div al contenedor
    container.appendChild(div);
    ventanas[4][data.name]['loop']=false;

    // Agregar evento al checkbox
    input.addEventListener('change', function() {

        if (this.checked) {
            label.textContent='Lazo cerrado';
        } else {
            label.textContent='Lazo abierto';
        }
        ventanas[4][data.name]['loop']=this.checked;

        socket.emit("lazo", {
            loop:data.name.replace("VC", ""),
            value:this.checked
        });
    });
    let containerSlider = document.createElement('div');
    containerSlider.classList.add('container_slider');

    let rangeSlider = document.createElement('div');
    rangeSlider.classList.add('range-slider');

    let rsBullet = document.createElement('span');
    rsBullet.id = 'id_rs-bullet'; // Asignar el ID según el formato especificado
    rsBullet.classList.add('rs-label');
    rsBullet.textContent = '0';

    let rsRangeLine = document.createElement('input');
    rsRangeLine.id = 'id_rs-range-line'; // Asignar el ID según el formato especificado
    rsRangeLine.classList.add('rs-range');
    rsRangeLine.setAttribute('type', 'range');
    rsRangeLine.setAttribute('value', '0');
    rsRangeLine.setAttribute('min', '0');
    rsRangeLine.setAttribute('max', '100');
    rsRangeLine.setAttribute('step', '0.001');

    let boxMinMax = document.createElement('div');
    boxMinMax.classList.add('box-minmax');

    let span0 = document.createElement('span');
    span0.textContent = '0%';

    let spanApertura = document.createElement('span');
    spanApertura.textContent = 'Apertura';

    let span100 = document.createElement('span');
    span100.textContent = '100%';

    rsRangeLine.addEventListener("input", showSliderValue, false);
    rsRangeLine.value=data.apertura
    showSliderValue();

    ventanas[4][data.name]['slider']=rsRangeLine;
    ventanas[4][data.name]['bullet']=rsBullet;

    rsBullet.innerHTML=data.apertura.toFixed(0)
    let bulletPosition = (data.apertura/rsRangeLine.max);
    rsBullet.style.left = (bulletPosition * 578) + "px";

    function showSliderValue() {
        if(Number(rsRangeLine.value)>0 && !input.checked){
            socket.emit("valve", {
                valvula:data.name,
                apertura:Number(rsRangeLine.value)
            });
        }
    }


    // Agregar elementos al DOM
    rangeSlider.appendChild(rsBullet);
    rangeSlider.appendChild(rsRangeLine);

    boxMinMax.appendChild(span0);
    boxMinMax.appendChild(spanApertura);
    boxMinMax.appendChild(span100);

    containerSlider.appendChild(rangeSlider);
    containerSlider.appendChild(boxMinMax);

    // Agregar el contenedor al cuerpo del documento (puedes cambiar esto dependiendo de donde quieras agregarlo)
    container.appendChild(containerSlider);
}

socket.on("valve", (data) => {
    let data_serializada=JSON.parse(data);
    ventanas[4][data_serializada.name]['bullet'].innerHTML=data_serializada.apertura.toFixed(0)+'%';
    let rsRangeLine = ventanas[4][data_serializada.name]['slider'];
    let bulletPosition = (data_serializada.apertura /rsRangeLine.max);
    ventanas[4][data_serializada.name]['bullet'].style.left = (bulletPosition * 578) + "px";
});
