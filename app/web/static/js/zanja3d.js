/**
 * HAZEN-WILLIAMS EXPRESS - MOTOR 3D TÉCNICO INTERACTIVO (Three.js)
 *
 * Características:
 * - Geometría limpia: CERO tierra ni arena dentro de la cañería.
 *   La cama de arena se ubica estrictamente debajo del caño y los estratos de suelo
 *   quedan confinados a los taludes laterales exteriores sin intersecar la tubería.
 * - Alineación coaxial y rigurosamente paralela entre cañería, masa de agua y vectores de flujo.
 * - Cañería con espesor de pared real y corte longitudinal técnico a escala.
 * - Simulación de flujo a sección llena con agua translúcida PBR (IOR 1.333) y flechas hidrodinámicas 3D.
 * - Zanja geotécnica con estratos de suelo, cama de arena compactada y rasante superior.
 * - Texturas procedurales HD (PEAD con franjas coextruidas, Galvanizado con zinc spangles, PVC técnico, etc.)
 * - Modos de vista técnicos: Isométrica, Sección transversal frontal y Perfil lateral longitudinal.
 * - Anotaciones CAD flotantes con cotas y líneas directrices.
 */

class Zanja3DViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.arrowsGroup = null;
    this.modelGroup = null;
    this.waterMesh = null;
    this.clock = new THREE.Clock();

    this.texturasCache = {};
    this.flechasList = [];
    this.yCentroTubo = 0;

    this.currentData = {
      materialId: 'pvc',
      materialNombre: 'PVC (Policloruro de Vinilo)',
      diametroMm: 110,
      diametroTexto: '110 mm',
      tipoSuelo: 'Arcilloso / tierra común',
      velocidadMs: 1.25
    };

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 600;
    const height = this.container.clientHeight || 390;

    // Escena con fondo neutro de estudio técnico
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf8fafc);
    this.scene.fog = new THREE.FogExp2(0xf8fafc, 0.035);

    // Cámara de perspectiva
    this.camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 100);
    this.camera.position.set(4.6, 3.2, 4.6);

    // Renderizador con antialiasing y renderizado físico
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2.0));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.08;

    this.container.innerHTML = "";
    this.container.appendChild(this.renderer.domElement);

    // Controles orbitales con amortiguación suave
    if (THREE.OrbitControls) {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.maxPolarAngle = Math.PI / 2.05;
      this.controls.minDistance = 2.0;
      this.controls.maxDistance = 12.0;
      this.controls.target.set(0, -0.15, 0);
    }

    // Iluminación
    this.configurarIluminacion();

    // Grupos principales
    this.modelGroup = new THREE.Group();
    this.scene.add(this.modelGroup);

    this.arrowsGroup = new THREE.Group();
    this.modelGroup.add(this.arrowsGroup);

    // Redimensionamiento responsivo
    window.addEventListener('resize', () => this.onWindowResize());

    // Construir geometría y escena inicial
    this.construirEscena();

    // Loop de animación
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  configurarIluminacion() {
    // 1. Luz de cielo y suelo
    const hemiLight = new THREE.HemisphereLight(0xf0f9ff, 0x78350f, 0.7);
    hemiLight.position.set(0, 20, 0);
    this.scene.add(hemiLight);

    // 2. Sol técnico con sombras nítidas
    const sunLight = new THREE.DirectionalLight(0xffffff, 1.15);
    sunLight.position.set(6, 10, 5);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 30;
    const d = 5.0;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0003;
    this.scene.add(sunLight);

    // 3. Luz difusa de relleno para claroscuros
    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.35);
    fillLight.position.set(-6, 4, -4);
    this.scene.add(fillLight);

    // 4. Luz de realce perimetral (rim)
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.3);
    rimLight.position.set(0, -4, -6);
    this.scene.add(rimLight);
  }

  onWindowResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  // ──────────────────────────────────────────────────────────────────
  // VISTAS DE CÁMARA TÉCNICAS
  // ──────────────────────────────────────────────────────────────────
  setVistaIsometica() {
    if (!this.camera || !this.controls) return;
    this.camera.position.set(4.6, 3.2, 4.6);
    this.controls.target.set(0, this.yCentroTubo || -0.15, 0);
    this.controls.update();
  }

  setVistaFrontal() {
    // Vista en corte transversal: mira de frente hacia el caño abierto
    if (!this.camera || !this.controls) return;
    this.camera.position.set(0, (this.yCentroTubo || -0.15) + 0.1, 5.2);
    this.controls.target.set(0, this.yCentroTubo || -0.15, 0);
    this.controls.update();
  }

  setVistaLateral() {
    // Vista en perfil longitudinal: mira el caño en toda su longitud horizontal
    if (!this.camera || !this.controls) return;
    this.camera.position.set(5.5, (this.yCentroTubo || -0.15) + 0.3, 0);
    this.controls.target.set(0, this.yCentroTubo || -0.15, 0);
    this.controls.update();
  }

  resetCamara() {
    this.setVistaIsometica();
  }

  // ──────────────────────────────────────────────────────────────────
  // GENERADORES DE TEXTURAS PROCEDURALES EN ALTA RESOLUCIÓN
  // ──────────────────────────────────────────────────────────────────
  crearTexturaSueloEstratificado(tipo) {
    const key = `suelo_${tipo}`;
    if (this.texturasCache[key]) return this.texturasCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    const t = (tipo || '').toLowerCase();
    let c1 = '#8c4830', c2 = '#6a311f', c3 = '#a75217', capaTop = '#365314';

    if (t.includes('arenoso')) {
      c1 = '#d4b483'; c2 = '#c29d66'; c3 = '#e2cda3'; capaTop = '#854d0e';
    } else if (t.includes('rocoso') || t.includes('grava')) {
      c1 = '#78716c'; c2 = '#57534e'; c3 = '#8d8580'; capaTop = '#3f3f46';
    } else if (t.includes('limoso') || t.includes('humedo') || t.includes('húmedo')) {
      c1 = '#52382c'; c2 = '#3a261c'; c3 = '#664536'; capaTop = '#18181b';
    }

    // Fondo estratificado con degradé geológico
    const grad = ctx.createLinearGradient(0, 0, 0, 1024);
    grad.addColorStop(0.00, capaTop);
    grad.addColorStop(0.06, c1);
    grad.addColorStop(0.35, c2);
    grad.addColorStop(0.65, c1);
    grad.addColorStop(1.00, c3);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 1024, 1024);

    // Estratos de sedimentación horizontales
    ctx.lineWidth = 3;
    for (let y = 60; y < 1024; y += 75) {
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.16)';
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(256, y + (Math.random() * 16 - 8), 768, y + (Math.random() * 16 - 8), 1024, y);
      ctx.stroke();
    }

    // Partículas y gravilla
    for (let i = 0; i < 6000; i++) {
      const px = Math.random() * 1024;
      const py = Math.random() * 1024;
      const alpha = Math.random() * 0.16;
      ctx.fillStyle = Math.random() > 0.5 ? `rgba(255,255,255,${alpha})` : `rgba(0,0,0,${alpha})`;
      ctx.fillRect(px, py, 2, 2);
    }

    // Clastos rocosos
    for (let i = 0; i < 110; i++) {
      const px = Math.random() * 1024;
      const py = Math.random() * 1024;
      const r = 3 + Math.random() * 6;
      ctx.fillStyle = 'rgba(50, 40, 30, 0.4)';
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    this.texturasCache[key] = texture;
    return texture;
  }

  crearTexturaArena() {
    const key = 'cama_arena';
    if (this.texturasCache[key]) return this.texturasCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    // Base de arena silícea dorada
    ctx.fillStyle = '#eab308';
    ctx.fillRect(0, 0, 512, 512);

    for (let i = 0; i < 7000; i++) {
      const px = Math.random() * 512;
      const py = Math.random() * 512;
      ctx.fillStyle = Math.random() > 0.5 ? 'rgba(254, 240, 138, 0.5)' : 'rgba(161, 98, 7, 0.35)';
      ctx.fillRect(px, py, 2, 2);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    this.texturasCache[key] = texture;
    return texture;
  }

  crearTexturaPEADFranjas() {
    const key = 'pead_franjas';
    if (this.texturasCache[key]) return this.texturasCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    // Base negro carbono PEAD
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, 1024, 1024);

    // 4 franjas azules longitudinales coextruidas según norma de agua potable
    ctx.fillStyle = '#0284c7';
    ctx.fillRect(100, 0, 48, 1024);
    ctx.fillRect(356, 0, 48, 1024);
    ctx.fillRect(612, 0, 48, 1024);
    ctx.fillRect(868, 0, 48, 1024);

    // Marcado técnico en relieve
    ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
    ctx.font = 'bold 24px monospace';
    ctx.fillText('PEAD PE100 PN16 SDR11 IRAM 13485 - AGUA POTABLE', 180, 500);

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    this.texturasCache[key] = texture;
    return texture;
  }

  crearTexturaMetalGalvanizado() {
    const key = 'acero_galv';
    if (this.texturasCache[key]) return this.texturasCache[key];

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#94a3b8';
    ctx.fillRect(0, 0, 1024, 1024);

    // Spangles de zinc ("flores de galvanizado")
    for (let i = 0; i < 900; i++) {
      const px = Math.random() * 1024;
      const py = Math.random() * 1024;
      const size = 10 + Math.random() * 26;
      ctx.fillStyle = Math.random() > 0.5 ? 'rgba(241, 245, 249, 0.4)' : 'rgba(51, 65, 85, 0.35)';
      ctx.beginPath();
      ctx.ellipse(px, py, size, size * 0.7, Math.random() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    this.texturasCache[key] = texture;
    return texture;
  }

  crearBadgeTexto(texto, icono = '📍', bgColor = '#0284c7') {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 110;
    const ctx = canvas.getContext('2d');

    // Sombra suave
    ctx.shadowColor = 'rgba(15, 23, 42, 0.35)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 5;

    // Fondo redondeado con gradiente premium
    const grad = ctx.createLinearGradient(0, 0, 512, 110);
    grad.addColorStop(0, bgColor);
    grad.addColorStop(1, '#0f172a');
    ctx.fillStyle = grad;

    const r = 20;
    ctx.beginPath();
    ctx.moveTo(r, 6);
    ctx.lineTo(512 - r, 6);
    ctx.quadraticCurveTo(512, 6, 512, 6 + r);
    ctx.lineTo(512, 104 - r);
    ctx.quadraticCurveTo(512, 104, 512 - r, 104);
    ctx.lineTo(r, 104);
    ctx.quadraticCurveTo(0, 104, 0, 104 - r);
    ctx.lineTo(0, 6 + r);
    ctx.quadraticCurveTo(0, 6, r, 6);
    ctx.closePath();
    ctx.fill();

    // Borde blanco sutil
    ctx.shadowColor = 'transparent';
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.stroke();

    // Texto de alta definición
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 32px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${icono}  ${texto}`, 256, 55);

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false
    });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(1.45, 0.32, 1);
    return sprite;
  }

  obtenerPBRMaterial(matId) {
    switch (matId) {
      case 'pvc':
        return new THREE.MeshStandardMaterial({
          color: 0xf1f5f9,
          roughness: 0.16,
          metalness: 0.05,
          side: THREE.DoubleSide
        });
      case 'polietileno':
        return new THREE.MeshStandardMaterial({
          map: this.crearTexturaPEADFranjas(),
          roughness: 0.38,
          metalness: 0.08,
          side: THREE.DoubleSide
        });
      case 'acero':
        return new THREE.MeshStandardMaterial({
          map: this.crearTexturaMetalGalvanizado(),
          color: 0xe2e8f0,
          roughness: 0.22,
          metalness: 0.92,
          side: THREE.DoubleSide
        });
      case 'hierro_fundido':
        return new THREE.MeshStandardMaterial({
          color: 0x1e293b,
          roughness: 0.88,
          metalness: 0.4,
          side: THREE.DoubleSide
        });
      case 'hormigon':
        return new THREE.MeshStandardMaterial({
          color: 0xd4d4d8,
          roughness: 0.96,
          metalness: 0.02,
          side: THREE.DoubleSide
        });
      default:
        return new THREE.MeshStandardMaterial({
          color: 0xe2e8f0,
          roughness: 0.35,
          metalness: 0.15,
          side: THREE.DoubleSide
        });
    }
  }

  // ──────────────────────────────────────────────────────────────────
  // CONSTRUCCIÓN EXACTA Y LIMPIA DE LA ESCENA (SIN TIERRA EN EL CAÑO)
  // ──────────────────────────────────────────────────────────────────
  construirEscena() {
    // Limpieza de objetos anteriores
    while (this.modelGroup.children.length > 0) {
      const obj = this.modelGroup.children[0];
      this.modelGroup.remove(obj);
    }

    this.arrowsGroup = new THREE.Group();

    // 1. DIMENSIONES A ESCALA
    const dMm = Math.max(25, Math.min(1000, Number(this.currentData.diametroMm) || 110));
    const radioTubo = 0.14 + Math.sqrt(dMm / 1000.0) * 0.42;
    const espesorTubo = Math.max(0.028, radioTubo * 0.10);
    const radioAgua = radioTubo - espesorTubo;
    const longitudTubo = 4.0;

    const anchoZanja = Math.max(1.5, radioTubo * 4.6);
    const profZanja = 1.5;

    // Espesor de la cama de arena debajo de la cañería
    const espesorArena = 0.22;

    // Centro del caño: el fondo del caño (yCentroTubo - radioTubo) descansa
    // EXACTAMENTE sobre la cara superior de la cama de arena (-profZanja/2 + espesorArena).
    // De esta forma, NADA de arena penetra dentro del caño.
    const yTopArena = -profZanja / 2 + espesorArena;
    const yCentroTubo = yTopArena + radioTubo;
    this.yCentroTubo = yCentroTubo;

    const texturaSuelo = this.crearTexturaSueloEstratificado(this.currentData.tipoSuelo);
    const texturaArena = this.crearTexturaArena();

    const matSuelo = new THREE.MeshStandardMaterial({
      map: texturaSuelo,
      roughness: 0.92,
      metalness: 0.02
    });

    // 2. BLOQUES EXTERIORES DE LA ZANJA (FUERA DE LA TUBERÍA)
    // Pared Lateral Izquierda (x <= -anchoZanja / 2)
    const bloqueLatGeo = new THREE.BoxGeometry(1.3, profZanja + 0.8, longitudTubo);
    const bloqueIzq = new THREE.Mesh(bloqueLatGeo, matSuelo);
    bloqueIzq.position.set(-(anchoZanja / 2 + 0.65), 0.1, 0);
    bloqueIzq.receiveShadow = true;
    bloqueIzq.castShadow = true;
    this.modelGroup.add(bloqueIzq);

    // Pared Trasera de la excavación (z <= -longitudTubo / 2)
    const bloqueTraseroGeo = new THREE.BoxGeometry(anchoZanja + 2.6, profZanja + 0.8, 0.9);
    const bloqueTrasero = new THREE.Mesh(bloqueTraseroGeo, matSuelo);
    bloqueTrasero.position.set(0, 0.1, -(longitudTubo / 2 + 0.45));
    bloqueTrasero.receiveShadow = true;
    this.modelGroup.add(bloqueTrasero);

    // Rasante de césped superior sobre el talud izquierdo
    const cespedGeo = new THREE.BoxGeometry(1.32, 0.08, longitudTubo * 1.01);
    const cespedMat = new THREE.MeshStandardMaterial({ color: 0x4d7c0f, roughness: 0.9 });
    const cesped = new THREE.Mesh(cespedGeo, cespedMat);
    cesped.position.set(-(anchoZanja / 2 + 0.65), (profZanja + 0.8) / 2 + 0.1, 0);
    this.modelGroup.add(cesped);

    // 3. CAMA DE ARENA COMPACTADA (ESTRICTAMENTE DEBAJO DEL CAÑO)
    // La cota superior de este prisma es yTopArena = yCentroTubo - radioTubo.
    // No existe invasión ni intersección geométrica con el caño.
    const camaArenaGeo = new THREE.BoxGeometry(anchoZanja * 0.99, espesorArena, longitudTubo);
    const camaArenaMat = new THREE.MeshStandardMaterial({
      map: texturaArena,
      roughness: 0.95,
      metalness: 0.0
    });
    const camaArena = new THREE.Mesh(camaArenaGeo, camaArenaMat);
    camaArena.position.set(0, -profZanja / 2 + espesorArena / 2, 0);
    camaArena.receiveShadow = true;
    this.modelGroup.add(camaArena);

    // 4. CAPAS DE RELLENO LATERAL COMPACTADO (SOLO EN EL TALUD IZQUIERDO, FUERA DEL CAÑO)
    // Se colocan exclusivamente en el espacio libre entre el talud izquierdo (x = -anchoZanja/2)
    // y el exterior izquierdo del caño (x = -radioTubo - 0.10 m de margen de seguridad).
    // Jamás pasan por x = 0 ni invaden el espacio interior de la tubería.
    const xMargenCaño = -radioTubo - 0.10;
    const xBordeZanja = -anchoZanja / 2;
    const anchoRellenoLat = Math.max(0.12, xMargenCaño - xBordeZanja);
    const xCentroRelleno = xBordeZanja + anchoRellenoLat / 2;
    const altoTotalRelleno = profZanja - espesorArena;
    const capas = 3;
    const altoCapa = altoTotalRelleno / capas;

    for (let i = 0; i < capas; i++) {
      const capaGeo = new THREE.BoxGeometry(anchoRellenoLat, altoCapa * 0.96, longitudTubo * 0.85);
      const capaColor = (i % 2 === 0) ? 0x854d0e : 0xa16207;
      const capaMat = new THREE.MeshStandardMaterial({
        color: capaColor,
        roughness: 0.88
      });
      const capaMesh = new THREE.Mesh(capaGeo, capaMat);
      capaMesh.position.set(xCentroRelleno, yTopArena + altoCapa * (i + 0.5), -longitudTubo * 0.05);
      capaMesh.receiveShadow = true;
      this.modelGroup.add(capaMesh);
    }

    // ──────────────────────────────────────────────────────────────────
    // 5. CAÑERÍA CON ESPESOR REAL (TOTALMENTE LIMPIA POR DENTRO)
    // ──────────────────────────────────────────────────────────────────
    //
    // Eje longitudinal horizontal a lo largo de Z:
    // Posición: (0, yCentroTubo, 0).
    // Corte longitudinal horizontal (semicírculo inferior de cuna):
    // thetaStart = -Math.PI * 0.5 (lado izquierdo horizontal, y = yCentroTubo)
    // thetaLength = Math.PI (lado derecho horizontal, y = yCentroTubo)
    // Ambos bordes de corte son exactamente horizontales y paralelos.
    const thetaStart = -Math.PI * 0.5;
    const thetaLength = Math.PI;
    const matTubo = this.obtenerPBRMaterial(this.currentData.materialId);

    // 5.1 Pared exterior del caño
    const geomTuboExt = new THREE.CylinderGeometry(
      radioTubo,
      radioTubo,
      longitudTubo,
      64,
      1,
      true,
      thetaStart,
      thetaLength
    );
    const meshTuboExt = new THREE.Mesh(geomTuboExt, matTubo);
    meshTuboExt.rotation.set(Math.PI / 2, 0, 0);
    meshTuboExt.position.set(0, yCentroTubo, 0);
    meshTuboExt.castShadow = true;
    meshTuboExt.receiveShadow = true;
    this.modelGroup.add(meshTuboExt);

    // 5.2 Pared interior del caño (muestra el espesor de pared y acabado interior)
    const geomTuboInt = new THREE.CylinderGeometry(
      radioAgua,
      radioAgua,
      longitudTubo,
      64,
      1,
      true,
      thetaStart,
      thetaLength
    );
    const meshTuboInt = new THREE.Mesh(geomTuboInt, matTubo);
    meshTuboInt.rotation.set(Math.PI / 2, 0, 0);
    meshTuboInt.position.set(0, yCentroTubo, 0);
    meshTuboInt.receiveShadow = true;
    this.modelGroup.add(meshTuboInt);

    // 5.3 Labios horizontales de corte longitudinal (espesor de pared en y = yCentroTubo)
    // Labio izquierdo (x entre -radioTubo y -radioAgua, y = yCentroTubo)
    const geoLabioIzq = new THREE.PlaneGeometry(espesorTubo, longitudTubo);
    const meshLabioIzq = new THREE.Mesh(geoLabioIzq, matTubo);
    meshLabioIzq.position.set(-(radioTubo + radioAgua) / 2, yCentroTubo, 0);
    meshLabioIzq.rotation.set(Math.PI / 2, 0, 0);
    this.modelGroup.add(meshLabioIzq);

    // Labio derecho (x entre +radioAgua y +radioTubo, y = yCentroTubo)
    const geoLabioDer = new THREE.PlaneGeometry(espesorTubo, longitudTubo);
    const meshLabioDer = new THREE.Mesh(geoLabioDer, matTubo);
    meshLabioDer.position.set((radioTubo + radioAgua) / 2, yCentroTubo, 0);
    meshLabioDer.rotation.set(Math.PI / 2, 0, 0);
    this.modelGroup.add(meshLabioDer);

    // 5.4 Tapas de espesor anular en los extremos frontal y posterior
    const geoAnilloFrontal = new THREE.RingGeometry(radioAgua, radioTubo, 48, 1, 0, Math.PI);
    const meshAnilloFrontal = new THREE.Mesh(geoAnilloFrontal, matTubo);
    meshAnilloFrontal.position.set(0, yCentroTubo, longitudTubo / 2);
    meshAnilloFrontal.rotation.set(0, 0, Math.PI); // Orientado hacia el semicírculo inferior
    this.modelGroup.add(meshAnilloFrontal);

    // Si es acero, agregar anillo de brida / cupla metálica en el tramo
    if (this.currentData.materialId === 'acero') {
      const bridaGeo = new THREE.TorusGeometry(radioTubo * 1.05, radioTubo * 0.10, 16, 48, Math.PI);
      const bridaMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.95, roughness: 0.2 });
      const bridaMesh = new THREE.Mesh(bridaGeo, bridaMat);
      bridaMesh.rotation.set(0, 0, Math.PI);
      bridaMesh.position.set(0, yCentroTubo, 0.4);
      this.modelGroup.add(bridaMesh);
    }

    // ──────────────────────────────────────────────────────────────────
    // 6. VOLUMEN DE AGUA A SECCIÓN LLENA (TRANSLÚCIDO Y PARALELO)
    // ──────────────────────────────────────────────────────────────────
    //
    // Cilindro coaxial de radio interior (radioAgua) totalmente limpio de tierra.
    // Material PBR con IOR 1.333 y transmisión para ver el agua y los vectores.
    const geomAgua = new THREE.CylinderGeometry(
      radioAgua * 0.996,
      radioAgua * 0.996,
      longitudTubo * 0.996,
      48,
      1,
      false
    );
    const matAgua = new THREE.MeshPhysicalMaterial({
      color: 0x0284c7,
      emissive: 0x0369a1,
      emissiveIntensity: 0.26,
      roughness: 0.04,
      metalness: 0.05,
      transmission: 0.85,
      ior: 1.333,
      transparent: true,
      opacity: 0.88,
      depthWrite: false
    });
    this.waterMesh = new THREE.Mesh(geomAgua, matAgua);
    this.waterMesh.rotation.set(Math.PI / 2, 0, 0);
    this.waterMesh.position.set(0, yCentroTubo, 0);
    this.modelGroup.add(this.waterMesh);

    // ──────────────────────────────────────────────────────────────────
    // 7. FLECHAS 3D DE FLUJO DE AGUA (CENTRADAS EN EL EJE Z)
    // ──────────────────────────────────────────────────────────────────
    const numFlechas = 8;
    this.flechasList = [];
    const colorFlecha = 0x38bdf8;

    for (let i = 0; i < numFlechas; i++) {
      const flechaGrp = new THREE.Group();

      // Vástago de la flecha
      const vastagoGeo = new THREE.CylinderGeometry(radioTubo * 0.042, radioTubo * 0.042, 0.28, 16);
      const flechaMat = new THREE.MeshBasicMaterial({ color: colorFlecha });
      const vastagoMesh = new THREE.Mesh(vastagoGeo, flechaMat);
      vastagoMesh.rotation.set(Math.PI / 2, 0, 0);
      flechaGrp.add(vastagoMesh);

      // Cono director de punta
      const conoGeo = new THREE.ConeGeometry(radioTubo * 0.12, 0.18, 20);
      const conoMesh = new THREE.Mesh(conoGeo, flechaMat);
      conoMesh.rotation.set(Math.PI / 2, 0, 0);
      conoMesh.position.set(0, 0, 0.18);
      flechaGrp.add(conoMesh);

      const zInicial = -longitudTubo / 2 + (i / numFlechas) * longitudTubo;
      flechaGrp.position.set(0, yCentroTubo, zInicial);

      this.arrowsGroup.add(flechaGrp);
      this.flechasList.push({ obj: flechaGrp, zOffset: (i / numFlechas) * longitudTubo });
    }
    this.longitudTubo = longitudTubo;
    this.modelGroup.add(this.arrowsGroup);

    // ──────────────────────────────────────────────────────────────────
    // 8. ETIQUETAS TÉCNICAS CAD FLOTANTES
    // ──────────────────────────────────────────────────────────────────
    // Badge 1: Material del caño
    const badgeMaterial = this.crearBadgeTexto(this.currentData.materialNombre, '🔘', '#0284c7');
    badgeMaterial.position.set(0, yCentroTubo + radioTubo + 0.52, 0.5);
    this.modelGroup.add(badgeMaterial);

    // Badge 2: Cota de Diámetro
    const badgeDiametro = this.crearBadgeTexto(`Ø ${this.currentData.diametroTexto}`, '📏', '#0369a1');
    badgeDiametro.position.set(0.72 + radioTubo, yCentroTubo + 0.1, 0.8);
    this.modelGroup.add(badgeDiametro);

    // Badge 3: Suelo / Terreno
    const badgeSuelo = this.crearBadgeTexto(`Suelo: ${this.currentData.tipoSuelo}`, '🌱', '#92400e');
    badgeSuelo.position.set(-(anchoZanja / 2 + 0.65), 0.75, 0);
    this.modelGroup.add(badgeSuelo);

    // Badge 4: Cama de arena compactada
    const badgeArena = this.crearBadgeTexto('Cama de arena compactada (10 cm)', '🏖️', '#ca8a04');
    badgeArena.position.set(-(anchoZanja / 2 + 0.5), -profZanja / 2 + espesorArena / 2, 0.9);
    this.modelGroup.add(badgeArena);

    // Líneas conectoras CAD nítidas
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x64748b,
      transparent: true,
      opacity: 0.85,
      linewidth: 2
    });

    // Cota hacia cañería
    const ptsTubo = [
      new THREE.Vector3(0, yCentroTubo + radioTubo, 0.5),
      new THREE.Vector3(0, yCentroTubo + radioTubo + 0.38, 0.5)
    ];
    this.modelGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsTubo), lineMat));

    // Cota hacia diámetro
    const ptsDiam = [
      new THREE.Vector3(radioTubo, yCentroTubo, 0.8),
      new THREE.Vector3(0.60 + radioTubo, yCentroTubo + 0.1, 0.8)
    ];
    this.modelGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsDiam), lineMat));
  }

  actualizar(datos) {
    if (datos.materialId) this.currentData.materialId = datos.materialId;
    if (datos.materialNombre) this.currentData.materialNombre = datos.materialNombre;
    if (datos.diametroMm) this.currentData.diametroMm = datos.diametroMm;
    if (datos.diametroTexto) this.currentData.diametroTexto = datos.diametroTexto;
    if (datos.tipoSuelo) this.currentData.tipoSuelo = datos.tipoSuelo;
    if (datos.velocidadMs) this.currentData.velocidadMs = datos.velocidadMs;

    this.construirEscena();
  }

  animate() {
    requestAnimationFrame(this.animate);

    // Animación fluida de avance del agua estrictamente paralela al eje Z
    if (this.flechasList && this.longitudTubo) {
      const v = Math.max(0.4, Math.min(3.5, Number(this.currentData.velocidadMs) || 1.25));
      const step = 0.012 * v;
      const minZ = -this.longitudTubo / 2;
      const maxZ = this.longitudTubo / 2;

      this.flechasList.forEach(item => {
        item.obj.position.z += step;
        if (item.obj.position.z > maxZ) {
          item.obj.position.z = minZ;
        }
      });
    }

    if (this.controls) {
      this.controls.update();
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
}

window.Zanja3DViewer = Zanja3DViewer;
