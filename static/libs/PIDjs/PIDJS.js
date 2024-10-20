class PIDDiagram {
    constructor(containerId, isblackstyle=false) {
        this.containerId = containerId;
        this.containerElement = document.getElementById(containerId);
        this.cyElement=document.createElement('div');
        this.layaodelement = document.createElement('div');
        this.layerEquirmenElement=document.createElement('div');
        this.equiments_data = {};
        this.planta ={}
        this.isblackstyle = isblackstyle;
        this.cy = null;
        this.equiments={};
        this.controlelement={};

        this.cyElement.classList.add('cy-layer-diagram');
        this.cyElement.id='id-cy-layer-diagram';
        this.layaodelement.classList.add('grid-layer-diagram');
        this.layerEquirmenElement.classList.add('equipment-layer-diagram"');
        this.layerEquirmenElement.id='equipment-layer';

        this.containerElement.appendChild(this.layaodelement);
        this.containerElement.appendChild(this.layerEquirmenElement);
        this.containerElement.appendChild(this.cyElement);

        if(this.isblackstyle){this.layaodelement.classList.add('blackstyle')}

    }

    // Cargar datos de los archivos JSON
    loadData(plantajson,symbols_path) {
        return new Promise((resolve, reject) => {
                fetch(plantajson)
                .then(response => response.json())
                .then(plantaData => {
                    this.planta = plantaData;  // Guardar los datos de la planta
                    return fetch(symbols_path+'/symboldata.json');
                })
                .then(response => response.json())
                .then(symbolData => {
                    this.equiments_data = symbolData;  // Guardar los datos de los equipos

                    // Crear un array de promesas para cargar los SVG
                    const svgLoads = Object.values(this.equiments_data).flatMap(equiment => this.loadSvgSymbol(symbols_path+'/'+equiment.svg).then(svg=>equiment.svg=svg));

                    // Esperar que todas las promesas de carga de SVG se resuelvan
                    return Promise.all(svgLoads);
                })
                .then(() => {

                    // Crear el gráfico PID con los datos de la planta
                    this.createPID(this.planta);

                    // Inicializar la cuadrícula de fondo con el zoom y el pan inicial del gráfico
                    this.zoom_grid(this.cy.zoom());
                    this.move_grid(this.cy.pan());

                    let pidclass=this;

                    // Escuchar los eventos de pan (cuando el gráfico se mueve)
                    this.cy.on('pan', function() {
                        pidclass.move_grid(pidclass.cy.pan());
                    });

                    // Escuchar los eventos de zoom (cuando el gráfico hace zoom)
                    this.cy.on('zoom', function() {
                        pidclass.zoom_grid(pidclass.cy.zoom());
                    });
                    resolve(this);
                })
                .catch(error => {
                    console.error('Error al leer el archivo JSON o cargar los SVG:', error);
                    reject(error);
                });
            });
    }

    // Función para actualizar el tamaño de la cuadrícula según el zoom
    zoom_grid(zoom) {
        this.layaodelement.style.backgroundSize = `${10 * zoom}px ${10 * zoom}px`;
    }

    // Función para mover la cuadrícula según el pan
    move_grid(pan) {
        this.layaodelement.style.backgroundPosition = `${pan.x}px ${pan.y}px`;
    }

    // Crear un símbolo de equipo
    createEquipmentSymbol(plantequiment) {
        let dataEquipment = {
            id: plantequiment.id,
            nodes: [],
            nodeconection: [],
            style: []
        };

        if (plantequiment.type === 'linepoint') {
            return this.createLinePoint(dataEquipment, plantequiment.id+'-diagram', plantequiment.pos, plantequiment.color || 'black');
        }

        if (plantequiment.type === 'nodecontrol') {
            return this.createNodeControl(dataEquipment, plantequiment.id+'-diagram', plantequiment.pos);
        }

        if (this.equiments_data[plantequiment.type]) {
            return this.createStandardEquipment(dataEquipment, plantequiment);
        } else {
            console.error(`No se encontró el tipo de equipo: ${type}`);
            return null;
        }
    }

    // Crear un punto de línea
    createLinePoint(dataEquipment, id, position, color) {
        
        dataEquipment.nodes.push({
            data: { id: id },
            position: position
        });

        dataEquipment.nodeconection.push({ id: id, type: 'auto' });

        dataEquipment.style.push({
            selector: 'node#' + id,
            css: {
                'width': 1.5,
                'height': 1.5,
                'padding': 0,
                'background-color': (color!=='black')?color : this.isblackstyle? 'white' :'black'
            }
        });

        return dataEquipment;
    }

    // Crear un nodo de control
    createNodeControl(dataEquipment, id, position) {

        let idcontrol=id.split('-')[0].split('_')

        dataEquipment.nodes.push({
            data: {
                id: id,
                label: `${idcontrol[1]} ${idcontrol[2]}`
            },
            position: position
        });

        const controltype = {
            electrical: '#ff0000', // Color rojo para señales eléctricas
            pneumatic: '#00ff00', // Color verde para señales neumáticas
            control: 'blue', // Color azul para lazos de control
            process: this.isblackstyle? 'white' :'black', // Color negro para procesos
        };

        dataEquipment.nodeconection.push({ id: id, type: 'auto' });

        dataEquipment.style.push({
            selector: 'node#' + id,
            css: {
                'background-color': !this.isblackstyle? 'white' :'rgb(50,50,50)',
                'border-color': (idcontrol.length>3)? controltype[idcontrol[3]]: controltype.process,
                'border-width': 0.25,
                'label': `${idcontrol[1]}\n${idcontrol[2]}`,
                'text-valign': 'center',
                'text-halign': 'center',
                'text-wrap':'wrap',
                'font-size':4,
                'color': this.isblackstyle? 'white' :'black',
                'width': 12,
                'height': 12,
                'shape': 'ellipse',
                'line-height':1.25
            }
        });

        return dataEquipment;
    }

    // Crear un equipo estándar
    createStandardEquipment(dataEquipment, plantequiment) {
        let data = _.cloneDeep(this.equiments_data[plantequiment.type]); // Datos del equipo
        let id = plantequiment.id +'-diagram';

        dataEquipment.nodes.push(
            {
                data: { id: id },
                position: plantequiment.pos
            },
            {
                data: { id: id +'-simbolo', parent: id },
                position: plantequiment.pos
            }
        );

        dataEquipment.nodeconection = []; // Almacena los puntos de conexión

        let divelement_tem= document.createElement('div');

        data.svg=this.isblackstyle? data.svg.replace(/#000000/g, "#ffffff"): data.svg;

        divelement_tem.innerHTML=data.svg;

        let svg_tem_element=divelement_tem.getElementsByTagName('svg')[0];

        let svg=SVG().svg(svg_tem_element.innerHTML);

        svg.viewbox(svg_tem_element.getAttribute('viewBox').split(' '));

        //chequear direccion
        if(plantequiment.direction){

            if(plantequiment.direction=='bottom'){

                data.connectors.forEach(point=>{point.pos.y=-point.pos.y;});
                svg.css({'transform':'rotate(180deg)'});

            } else if (plantequiment.direction === 'left') {

                svg.css({'transform':'rotate(270deg)'});
                this.flipsizes(data);
                data.connectors.forEach(point=>{
                    let y = point.pos.x
                    
                    point.pos.x=point.pos.y;
                    point.pos.y=y;
                    point.type='vertical';

                });

            } else if (plantequiment.direction === 'right') {
                
                svg.css({'transform':'rotate(90deg)'});
                this.flipsizes(data);
                data.connectors.forEach(point=>{
                    let y = point.pos.x
                    
                    point.pos.x=-point.pos.y;
                    point.pos.y=y;
                    point.type='vertical';

                });
            }
        }

        dataEquipment.svg=svg;
        dataEquipment.direction=plantequiment.direction || 'top';

        dataEquipment.style.push(
            this.createSymbolStyle(id, data),
            this.createLabelStyle(id, plantequiment.texthalign, plantequiment.textvalign)
        );

        // Generar conectores
        this.createConnectors(dataEquipment, id, data, plantequiment.pos, plantequiment.connectors || []);

        return dataEquipment;
    }

    flipsizes(data){
        let width = data.height;
        data.height = data.width;
        data.width = width;
    }

    // Crear estilo para el símbolo
    createSymbolStyle(id, data) {
        return {
            selector: 'node#' + id + '-simbolo',
            style: {
                'width': data.width,
                'height': data.height,
                'shape': 'rectangle',
                'padding': 0,
                'background-color': !this.isblackstyle? 'white' :'black',
                'background-opacity': 0,
                //'background-image': 'data:image/svg+xml;base64,' + btoa(data.svg), // Imagen de fondo
                'background-fit': 'contain',
                'border-width': 0,
                'events': 'no'
            }
        };
    }

    // Crear estilo para la etiqueta
    createLabelStyle(id, texthalign, textvalign) {
        return {
            selector: 'node#' + id,
            style: {
                'shape': 'rectangle',
                'background-color': !this.isblackstyle? 'white' :'black',
                'background-opacity': 0,
                'border-width': 0,
                'text-halign': texthalign,
                'text-valign': textvalign,
                'font-size': 7,
                'color':this.isblackstyle? 'white':'black',
                'padding': 0,
                'content': id.split('-')[0]
            }
        };
    }

    // Crear conectores
    createConnectors(dataEquipment, id, data, position, listconnectors) {
        let connectors = [...data.connectors, ...listconnectors];

        connectors.forEach((point, i) => {
            let connectorId = id + '-' + i; // Identificación del conector
            dataEquipment.nodes.push(
                {
                    data: { id: connectorId, parent: id },
                    position: {
                        x: position.x + data.width * point.pos.x,
                        y: position.y + data.height * point.pos.y
                    }
                }
            );

            dataEquipment.nodeconection.push({ id: connectorId, type: point.type });

            dataEquipment.style.push({
                selector: 'node#' + connectorId,
                css: {
                    'width': 0.1,
                    'height': 0.1,
                    'padding': '0px',
                    'events': 'no', // Hacer que el conector no sea seleccionable
                }
            });
        });
    }

    // Crear una arista entre dos equipos
    createLine(id, eq1, eq2, connecs, arrowshape = 'triangle', type = 'process') {

        const lineStyles = {
            electrical: {
                'line-style': 'dashed',
                'line-color': '#ff0000', // Color rojo para señales eléctricas
                'width': 0.3
            },
            pneumatic: {
                'line-style': 'dotted', // Línea discontinua para señales neumáticas
                'line-color': '#00ff00', // Color verde para señales neumáticas
                'width': 0.3
            },
            control: {
                'line-style': 'solid', // Línea sólida para lazos de control
                'line-color': 'blue', // Color azul para lazos de control
                'width': 0.3
            },
            process: {
                'line-style': 'solid', // Línea sólida para procesos
                'line-color': this.isblackstyle? 'white' :'black', // Color negro para procesos
                'width': 0.3
            }
        };

        const style = lineStyles[type] || lineStyles.process; // Utiliza el tipo proporcionado o 'process' como valor por defecto.

        // Validar que los índices existan
        if (eq1.nodeconection[connecs[0]] && eq2.nodeconection[connecs[1]]) {
            let edge_line = {
                edges: {
                    data: {
                        id: id+'-diagram-line',
                        source: eq1.nodeconection[connecs[0]].id,
                        target: eq2.nodeconection[connecs[1]].id
                    }
                },
                style: {
                    selector: 'edge#' + id+'-diagram-line',
                    css: {
                        'target-arrow-shape': arrowshape,
                        'target-arrow-color': this.isblackstyle? 'white': 'black',
                        'taxi-direction': eq1.nodeconection[connecs[0]].type, // Tipo de dirección
                        'taxi-turn': (eq1.nodeconection[connecs[0]].type === 'vertical') ? 100 : 10, // Ajustar la curva
                        // Aplica el estilo correspondiente
                        ...style // Esparce el objeto de estilo
                    }
                }
            };

            return edge_line;
        } else {
            console.error(`Error: Conexión inválida en el equipo ${id}`);
            return null;
        }
    }

    loadSvgSymbol(url) {
        return new Promise((resolve, reject) => {
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        reject(new Error(`Error al cargar el archivo SVG: ${response.statusText}`));
                    }
                    return response.text();
                })
                .then(data => {
                    resolve(data); // Resolviendo la promesa con el contenido SVG
                })
                .catch(error => {
                    reject(error); // Rechazando la promesa si ocurre algún error
                });
        });
    }

    createPID(diagram) {
        let equiments = {};
    
        // Crear los nodos de equipos
        diagram.equiments.forEach(equiment => {
            equiments[equiment.id] = this.createEquipmentSymbol(equiment);
        });
    
        // Crear las líneas entre equipos
        let lines = diagram.lines.map(line_i => 
            this.createLine(
                line_i.id,
                equiments[line_i.equiments[0]],
                equiments[line_i.equiments[1]],
                line_i.connects,
                line_i.arrowshape || 'triangle',
                line_i.signalType || 'process'
            )
        );
    
        // Configuración del grafo Cytoscape
        this.cy= cytoscape({
            container: this.cyElement,
            boxSelectionEnabled: false,
            style: this.getGraphStyles(lines, equiments),
            elements: this.getGraphElements(equiments, lines),
            layout: {
                name: 'preset',  // Usar posiciones predeterminadas definidas
                padding: 5
            }
        });
    
        diagram.equiments.forEach(equiment => {
            if(equiment.type != 'linepoint' && equiment.type != 'nodecontrol'){
                this.createDivEquiments(equiments[equiment.id]);
                this.equiments[equiment.id]=this.cy.$('#'+equiment.id+'-diagram');
            }else if(equiment.type == 'nodecontrol'){
                this.controlelement[equiment.id]=this.cy.$('#'+equiment.id+'-diagram');
            }
        });
    
        return this.cy;
    
    }

    updatepost(equiment){
        let width = ((equiment.direction=='top' || equiment.direction=='bottom')? this.cy.$('#'+equiment.id+'-diagram-simbolo').width() : this.cy.$('#'+equiment.id+'-diagram-simbolo').height())*this.cy.zoom();
        let height = ((equiment.direction=='top' || equiment.direction=='bottom')? this.cy.$('#'+equiment.id+'-diagram-simbolo').height(): this.cy.$('#'+equiment.id+'-diagram-simbolo').width())*this.cy.zoom();

        let position = this.cy.$('#'+equiment.id+'-diagram').renderedPosition();

        equiment.svg.css({
            position: 'absolute',
            width: width+'px',
            height: height+'px',
            top: (position.y-height/2)+'px',
            left: (position.x-width/2)+'px'
        })
    }
    
    createDivEquiments(equiment){
    
        equiment.svg.addTo(this.layerEquirmenElement);
    
        this.updatepost(equiment);

        let pidclass=this;
    
        this.cy.$('#'+equiment.id+'-diagram').on('position', function(event) {
            pidclass.updatepost(equiment);
        });
    
        // Escuchar los eventos de pan (cuando el gráfico se mueve)
        this.cy.on('pan', function() {
            pidclass.updatepost(equiment);
        });
    
        // Escuchar los eventos de zoom (cuando el gráfico hace zoom)
        this.cy.on('zoom', function() {
            pidclass.updatepost(equiment);
        });
    }
    
    // Obtener estilos del grafo
    getGraphStyles(lines, equiments) {
        return [
            {
                selector: 'edge',
                css: {
                    'curve-style': 'taxi',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#000000',
                    'arrow-scale': 0.4,
                    'width': 0.3,
                    'line-color': '#000000'
                }
            },
            ...lines.map(line_i => line_i.style),  // Estilos de líneas
            ...Object.values(equiments).flatMap(eq => eq.style)  // Estilos de equipos
        ];
    }
    
    // Obtener elementos del grafo
    getGraphElements(equiments, lines) {
        return {
            nodes: Object.values(equiments).flatMap(eq => eq.nodes),  // Todos los nodos
            edges: lines.map(line_i => line_i.edges)  // Todas las líneas
        };
    }
    
    // Guardar posiciones de equipos y descargar JSON
    savePosition() {
        this.planta.equiments.forEach((equipo, i) => {
            this.planta.equiments[i].pos = this.cy.$('#' + equipo.id+'-diagram').position();
        });
        this.downloadJSON(this.planta, 'planta.json');  // Llama a la función de descarga
    }
    
    // Función para descargar el objeto como un archivo JSON
    downloadJSON(obj, filename) {
        const jsonStr = JSON.stringify(obj);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const link = document.createElement("a");
    
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
}