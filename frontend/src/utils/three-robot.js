/**
 * Encapsulates the Three.js Robot Head animation logic.
 */
export class ThreeRobotHead {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.mainGroup = null;
        this.leftEye = null;
        this.rightEye = null;
        this.animationId = null;
        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        this.isInitialized = false;

        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleResize = this.handleResize.bind(this);
        this.animate = this.animate.bind(this);
    }

    async init() {
        if (this.isInitialized) return;

        // Ensure Three.js is loaded
        if (!window.THREE) {
            await this.loadThreeJS();
        }

        this.container = document.getElementById(this.containerId);
        if (!this.container) return;

        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || window.innerHeight;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.z = 5;

        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        this.container.appendChild(this.renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0x00aaff, 2, 10);
        pointLight.position.set(2, 2, 2);
        this.scene.add(pointLight);

        this.mainGroup = new THREE.Group();
        this.scene.add(this.mainGroup);

        // Head
        const headGeometry = new THREE.SphereGeometry(1.2, 64, 64);
        const headMaterial = new THREE.MeshPhongMaterial({
            color: 0x1a1a1a,
            shininess: 100,
            specular: 0x333333
        });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.scale.set(1, 1.1, 0.8);
        this.mainGroup.add(head);

        // Face Plate
        const facePlateGeo = new THREE.SphereGeometry(1.21, 64, 64, 0, Math.PI * 2, 0, Math.PI * 0.4);
        const facePlateMat = new THREE.MeshStandardMaterial({
            color: 0x050505,
            metalness: 0.9,
            roughness: 0.1,
            transparent: true,
            opacity: 0.95
        });
        const facePlate = new THREE.Mesh(facePlateGeo, facePlateMat);
        facePlate.rotation.x = Math.PI * 0.1;
        this.mainGroup.add(facePlate);

        // Eyes
        const eyeGroup = new THREE.Group();
        this.mainGroup.add(eyeGroup);

        const createEye = (x) => {
            const eyeGeo = new THREE.RingGeometry(0.15, 0.22, 64);
            const eyeMat = new THREE.MeshBasicMaterial({ 
                color: 0x00ccff, 
                transparent: true, 
                opacity: 0.8,
                side: THREE.DoubleSide
            });
            const eye = new THREE.Mesh(eyeGeo, eyeMat);
            eye.position.set(x, 0.2, 1.1);
            
            const pupilGeo = new THREE.CircleGeometry(0.08, 32);
            const pupilMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 });
            const pupil = new THREE.Mesh(pupilGeo, pupilMat);
            pupil.position.z = 0.01;
            eye.add(pupil);
            
            return eye;
        };

        this.leftEye = createEye(-0.4);
        this.rightEye = createEye(0.4);
        eyeGroup.add(this.leftEye, this.rightEye);

        // Events
        window.addEventListener('mousemove', this.handleMouseMove);
        window.addEventListener('resize', this.handleResize);

        this.isInitialized = true;
        this.animate();
    }

    handleMouseMove(e) {
        this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    }

    handleResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const w = this.container.clientWidth || window.innerWidth;
        const h = this.container.clientHeight || window.innerHeight;
        this.renderer.setSize(w, h);
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
    }

    animate() {
        this.animationId = requestAnimationFrame(this.animate);
        this.time += 0.01;

        if (this.mainGroup) {
            this.mainGroup.position.y = Math.sin(this.time * 0.5) * 0.1;
            this.mainGroup.rotation.y = Math.sin(this.time * 0.3) * 0.05;
            
            const targetRotX = this.mouse.y * 0.2;
            const targetRotY = this.mouse.x * 0.3;
            this.mainGroup.rotation.x += (targetRotX - this.mainGroup.rotation.x) * 0.05;
            this.mainGroup.rotation.y += (targetRotY - this.mainGroup.rotation.y) * 0.05;
        }

        if (this.leftEye && this.rightEye) {
            const eyePulse = 0.8 + Math.sin(this.time * 2) * 0.2;
            this.leftEye.material.opacity = eyePulse;
            this.rightEye.material.opacity = eyePulse;
            
            if (Math.random() > 0.995) {
                this.leftEye.scale.y = 0.1;
                this.rightEye.scale.y = 0.1;
            } else {
                this.leftEye.scale.y += (1 - this.leftEye.scale.y) * 0.2;
                this.rightEye.scale.y += (1 - this.rightEye.scale.y) * 0.2;
            }
        }

        this.renderer.render(this.scene, this.camera);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        window.removeEventListener('mousemove', this.handleMouseMove);
        window.removeEventListener('resize', this.handleResize);

        if (this.renderer && this.container) {
            this.container.removeChild(this.renderer.domElement);
            this.renderer.dispose();
        }
        this.isInitialized = false;
    }

    loadThreeJS() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://ajax.googleapis.com/ajax/libs/threejs/r125/three.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
}
