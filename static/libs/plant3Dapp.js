import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GUI } from 'three/addons/libs/lil-gui.module.min.js';


var app={
    planta3D: function(){
        this.renderer = new THREE.WebGLRenderer( { antialias: true } );
        this.scene = new THREE.Scene();
        this.scene.background=new THREE.Color(0x8a8888);
        this.canvas_info = document.createElement('canvas');
        this.sprite_info=null;
        this.camera=null;
        this.controls=null;

        this.equipo_hover=null;
        
        const loader = new GLTFLoader();

        this.Scene_objects={};
        var gltf_scene=null;

        const mouse = new THREE.Vector2();
        var raycaster = new THREE.Raycaster();
        var INTERSECTED=null;
        var intersects=null;

        this.load= function(div,guiDOM){
            this.camera = new THREE.PerspectiveCamera( 50, div.clientWidth / div.clientHeight, 0.1, 2000.00);
            this.controls = new OrbitControls( this.camera, guiDOM);
            this.controls.minPolarAngle = 0; // Límite superior
            this.controls.maxPolarAngle = Math.PI / 2; // Límite inferior (90 grados)
            this.renderer.setSize( div.clientWidth, div.clientHeight);
            div.appendChild( this.renderer.domElement );
            document.addEventListener( 'mousemove', onDocumentMouseMove.bind(this) );

            guiDOM.addEventListener('click',scena_click.bind(this));

            let objec_this=this;
            info_activador({
                'level': 26,
                'message': 'Cargando...',
                'msg_format': 'Cargando...'
            },false);
            loader.load( './assets/scene.gltf', function ( gltf ) {
                info_activador({
                    'level': 20,
                    'message': 'Completado',
                    'msg_format': 'Completado'
                });
                gltf_scene=gltf.scene;
            
                gltf.scene.children[0].children.forEach(objecto=>{
                    objec_this.Scene_objects[objecto.name]={obj:objecto,punto:null};
                    gltf.scene.children.forEach(obj_parent =>{
                        if(obj_parent.name.includes('P_') && obj_parent.name.includes(objecto.name)){
                            objec_this.Scene_objects[objecto.name].punto=obj_parent;
                        }
                    })
                })
                objec_this.scene.add(gltf.scene);
                gltf.scene.children[gltf.scene.children.length-1].material.blending=2;
            
                objec_this.play();
                crear_input_value();
                socket.connect();
            
            }, function ( xhr ) {
                //console.log( ( xhr.loaded / xhr.total * 100 ) + '% loaded' );
            
            }, function ( error ) {
            
                console.error( error );
            
            });
            

            this.canvas_info.width=400;
            this.canvas_info.height=700;
            let texture = new THREE.Texture(this.canvas_info);
            texture.needsUpdate = true;
            let spriteMaterial = new THREE.SpriteMaterial({ map: texture });
            this.sprite_info = new THREE.Sprite(spriteMaterial);
            this.sprite_info.position.set(0, 0, 0);

            this.scene.add(this.sprite_info);


            this.controls.target.set(0.9787335427537514,4.89907657477432,-3.3036502097258675);

            this.camera.position.set(-19.031459770284346,16.423340748672004,11.112456080633438);

            this.controls.update();

        }

        var scena_click= (event)=>{

            if(!this.controls.enabled){
                this.controls.enabled=true;
            }
            event.preventDefault();

            this.click();
        }

        this.click=()=>{

            desactivar_info(100);

            if(INTERSECTED){
                if (plantadata.Equipos && plantadata.Equipos[INTERSECTED.name]){
                    if(!isdinamicactive){
                        crear_ventana(INTERSECTED.name,1);
                    }else{
                        crear_ventana(INTERSECTED.name,5);
                    }
                }

                if(plantadata.Flujos && plantadata.Flujos[INTERSECTED.name] && !isdinamicactive){
                    crear_ventana(INTERSECTED.name,2);
                }

                if(plantadata.Valvulas && plantadata.Valvulas[INTERSECTED.name]){
                    crear_ventana(INTERSECTED.name,4);
                }
            }

        }

        var onDocumentMouseMove = ( event )=> {
            if (this.controls.enabled){
                event.preventDefault();
            }else{
                return;
            }
        
            mouse.x = ( event.clientX / this.renderer.domElement.clientWidth ) * 2 - 1;
            mouse.y = - ( event.clientY / this.renderer.domElement.clientHeight ) * 2 + 1;
        }

        var objecto_emissive = (objec,emissive) =>{
            if(objec.name=='EK101'){
                objec.children.forEach(subo_bjetos => {
                    subo_bjetos.material.emissive.setHex(emissive);
                });
            }else{
                objec.material.emissive.setHex(emissive);
            }
        }
        
        var object_test_select = () => {
            let object_select=null;
            raycaster.setFromCamera( mouse, this.camera );
        
            if(!gltf_scene){
                return null;
            }
        
            intersects = raycaster.intersectObjects(gltf_scene.children[0].children, false);
        
            if(!(intersects.length>0)){
                intersects = raycaster.intersectObjects(gltf_scene.children[0].children[0].children, false);
                if(intersects.length>0){
                    object_select=gltf_scene.children[0].children[0];
                }
            }else{
                object_select=intersects[0].object;
            }

            this.select(object_select, true);
        
            return object_select;
        }

        this.select = (object_select, on_pid=false) =>{

            if(object_select){
                if(INTERSECTED != object_select){
                    if(INTERSECTED){
                        objecto_emissive(INTERSECTED,0x000000);
                    }
                    
                    if(pid && on_pid){
                        Object.keys(pid.equiments).forEach(equipo=>{pid_selec(equipo,false)});
                    }

                    INTERSECTED = object_select;
                    this.equipo_hover=this.Scene_objects[INTERSECTED.name];
                    objecto_emissive(INTERSECTED,0x008a84);

                    if(pid && on_pid){
                        pid_selec(INTERSECTED.name);
                    }
                }
            }else{
                if(INTERSECTED){
                    objecto_emissive(INTERSECTED,0x000000);
                    INTERSECTED=null;
                }
            }

            if(this.equipo_hover){
                if(this.equipo_hover.punto){
                    Infomación_Select(this.canvas_info,this.sprite_info,this.equipo_hover);
                }
            }
        }

        var animate = () => {
            requestAnimationFrame(animate);
            this.controls.update();
            
            if(this.controls.enabled){
                object_test_select();
            }
        
            this.renderer.render( this.scene, this.camera );
        }

        this.play = () => {
            animate();
        }

        var Infomación_Select = (canvas,Tex_sprinte,obj) =>{
            

            let scale = obj.punto.position.distanceTo(this.camera.position)*7/22
            Tex_sprinte.scale.set(scale, scale*700/400, scale); // Escalar el sprite según sea necesario
            let ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            //fondo cuadro
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
            ctx.fillRect(0, 0, canvas.width, 220);
        
            //Titulo
            ctx.font = 'Bold 24px Arial';
            ctx.fillStyle = 'white';
            ctx.fillText(obj.obj.name, 20, 40,100);
            
            let yi=40;
            if (plantadata.Equipos && plantadata.Equipos[obj.obj.name]){
                Object.keys(plantadata.Equipos[obj.obj.name]).forEach(key=>{
                    if(Object.keys(propiedades).includes(key)){
                        ctx.font = '22px Arial';
                        ctx.fillStyle = 'white';

                        let valor=plantadata.Equipos[obj.obj.name][key];
                        ctx.fillText(propiedades[key].name, 20, 40+yi,200);
                        valor=`${propiedades[key].to(valor).toFixed(2)} ${propiedades[key].unidad}`;

                        ctx.font = '22px Arial';
                        ctx.fillStyle = 'white';
                        ctx.fillText(valor, canvas.width/2+50, 40+yi,100);
                        yi+=30;   
                    }
                })
            }
        
            //linea
            ctx.lineWidth = 5; // Grosor de la línea en píxeles
            ctx.strokeStyle = '#005ca3';
            ctx.beginPath();
            ctx.moveTo(canvas.width/2, 220);
            ctx.lineTo(canvas.width/2, 350);
            ctx.stroke();
            ctx.closePath();

            // Dibujar el círculo
            ctx.beginPath();
            ctx.arc(canvas.width/2, 220, 10, 0, 2 * Math.PI);
            ctx.fillStyle = '#005ca3'; // Color de relleno del círculo
            ctx.fill();
            ctx.closePath();
            
        
            Tex_sprinte.material.map.needsUpdate = true;
            Tex_sprinte.position.set(obj.punto.position.x,obj.punto.position.y,obj.punto.position.z);
        }

    }
}


export{ app }