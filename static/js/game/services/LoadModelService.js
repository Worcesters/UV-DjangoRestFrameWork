import { AbstractService } from "../core/AbstractService.js";

export class LoadModelService extends AbstractService {
    constructor(deps) {
        super("LoadModelService");
        this.deps = deps;
    }

    async loadAll() {
        const state = this.deps.getState();
        const load = (path) => new Promise((resolve, reject) => {
            state.loader.load(
                state.modelsBase + path,
                (gltf) => resolve(gltf.scene),
                undefined,
                (err) => reject(err)
            );
        });
        try {
            const ship = await load("puddle_jumper.glb");
            ship.scale.set(3.5, 3.5, 3.5);
            ship.rotation.y = Math.PI;
            ship.traverse((child) => {
                if (child.isMesh) {
                    child.material = new state.THREE.MeshStandardMaterial({ color: 0x0a3d12, metalness: 0.9, roughness: 0.2 });
                }
            });
            state.scene.add(ship);

            const starGeo = new state.THREE.BufferGeometry();
            const starPositions = new Float32Array(state.STAR_COUNT * 6);
            for (let i = 0; i < state.STAR_COUNT * 6; i++) {
                starPositions[i] = (Math.random() - 0.5) * 4000;
            }
            starGeo.setAttribute("position", new state.THREE.BufferAttribute(starPositions, 3));
            const starMat = new state.THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 });
            const starField = new state.THREE.LineSegments(starGeo, starMat);
            state.scene.add(starField);

            const engineLight = new state.THREE.PointLight(0x00f2ff, 0, 50);
            engineLight.position.set(0, 0, 10);
            ship.add(engineLight);

            const shieldMesh = new state.THREE.Mesh(
                new state.THREE.SphereGeometry(12, 32, 32),
                new state.THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0, blending: state.THREE.AdditiveBlending, side: state.THREE.DoubleSide })
            );
            shieldMesh.position.set(3, 0, -2);
            ship.add(shieldMesh);

            const tunnelGeo = new state.THREE.CylinderGeometry(150, 40, 20000, 64, 100, true);
            const tunnelMat = new state.THREE.MeshStandardMaterial({ color: 0x0066ff, emissive: 0x0022ff, emissiveIntensity: 3, side: state.THREE.BackSide, transparent: true, opacity: 0.8 });
            const hyperspaceTunnel = new state.THREE.Mesh(tunnelGeo, tunnelMat);
            hyperspaceTunnel.rotation.x = Math.PI / 2;
            hyperspaceTunnel.visible = false;
            state.scene.add(hyperspaceTunnel);

            const wraithBossModel = await load("wraith_ship.glb");
            const atlanteBossModel = await load("atlante_boss.glb");
            const kiraBossModel = await load("kira_3.glb");
            const asteroidModel = await load("asteroid.glb");
            const explosionModel = await load("asteroid_explo.glb");
            const gateActiveModel = await load("stargate.glb");
            const hitEffectModel = await load("hit_ship.glb");
            let friendModel = null;
            let droneModel = null;
            try {
                friendModel = await load("friend.glb");
            } catch (_e) {
                friendModel = null;
            }
            try {
                droneModel = await load("drone.glb");
            } catch (_e) {
                droneModel = null;
            }

            this.deps.setState({
                ship,
                starField,
                engineLight,
                shieldMesh,
                hyperspaceTunnel,
                wraithBossModel,
                atlanteBossModel,
                kiraBossModel,
                asteroidModel,
                explosionModel,
                gateActiveModel,
                hitEffectModel,
                friendModel,
                droneModel
            });

            this.deps.initLinearReactorTrails();
            this.deps.initFriendBulletAssets();
            this.deps.warmPlayerDronePool(10);
            this.deps.applySector(this.deps.getState().currentSector);
            this.deps.initTutorialPreviews();
            for (let i = 0; i < 160; i++) this.deps.spawnAsteroid();
            this.deps.startAnimate();
        } catch (e) {
            console.error(e);
        }
    }
}
