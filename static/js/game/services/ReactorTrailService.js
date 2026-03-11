import { AbstractService } from "../core/AbstractService.js";

export class ReactorTrailService extends AbstractService {
    constructor(deps) {
        super("ReactorTrailService");
        this.deps = deps;
    }

    createLinearTrailMesh(nozzleX, nozzleY, nozzleZ) {
        return { x: nozzleX, y: nozzleY, z: nozzleZ };
    }

    getReactorNozzleWorld(nozzle, outVec) {
        const state = this.deps.getState();
        const shipRoll = state.ship.rotation.z || 0;
        const rz = -shipRoll;
        const c = Math.cos(rz);
        const s = Math.sin(rz);
        const pivotX = -10;
        const pivotY = -15;
        const lx = (nozzle ? nozzle.x : 0) - pivotX;
        const ly = (nozzle ? nozzle.y : 0) - pivotY;
        const rx = (lx * c) - (ly * s) + pivotX;
        const ry = (lx * s) + (ly * c) + pivotY;
        return outVec.set(
            state.ship.position.x + rx,
            state.ship.position.y + ry,
            state.ship.position.z + (nozzle ? nozzle.z : 0)
        );
    }

    initTrails() {
        const state = this.deps.getState();
        const leftReactorTrail = this.createLinearTrailMesh(-18.5, -0.4, 4.6);
        const rightReactorTrail = this.createLinearTrailMesh(-2.5, -0.4, 4.6);
        const reactorTrailGeo = new state.THREE.CylinderGeometry(0.42, 1.35, 8.4, 8);
        const reactorTrailMatA = new state.THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.78,
            blending: state.THREE.AdditiveBlending,
            depthWrite: false,
            depthTest: false
        });
        const reactorTrailMatB = new state.THREE.MeshBasicMaterial({
            color: 0x7c3aed,
            transparent: true,
            opacity: 0.74,
            blending: state.THREE.AdditiveBlending,
            depthWrite: false,
            depthTest: false
        });
        this.deps.setState({
            leftReactorTrail,
            rightReactorTrail,
            reactorTrailGeo,
            reactorTrailMatA,
            reactorTrailMatB
        });
    }

    updateTrails(active) {
        const state = this.deps.getState();
        if (!state.leftReactorTrail || !state.rightReactorTrail || !state.ship) return;
        if (!active) return;
        const now = state.clock.getElapsedTime();
        if ((now - state.lastReactorEmitAt) < 0.065) return;
        this.deps.setState({ lastReactorEmitAt: now });

        const nozzles = [state.leftReactorTrail, state.rightReactorTrail];
        for (let i = 0; i < nozzles.length; i++) {
            const n = nozzles[i];
            const nozzleWorld = this.getReactorNozzleWorld(n, state.tempVecA);
            const p = new state.THREE.Mesh(
                state.reactorTrailGeo,
                (Math.random() > 0.35 ? state.reactorTrailMatA : state.reactorTrailMatB).clone()
            );
            p.rotation.x = Math.PI / 2;
            p.position.set(
                nozzleWorld.x + (Math.random() - 0.5) * 0.35,
                nozzleWorld.y + (Math.random() - 0.5) * 0.3,
                nozzleWorld.z + Math.random() * 0.5
            );
            const s = 0.78 + Math.random() * 0.22;
            p.scale.set(s, s, 0.95 + Math.random() * 0.2);
            const baseOpacity = 0.68 + Math.random() * 0.16;
            p.material.opacity = baseOpacity;
            p.userData = {
                kind: "reactorThruster",
                nozzleX: n.x,
                nozzleY: n.y,
                nozzleZ: n.z,
                nozzleRef: n,
                driftZ: 2.6 + Math.random() * 1.1,
                life: 0.86,
                wobble: 0.22 + Math.random() * 0.16,
                grow: 1.006 + Math.random() * 0.004,
                bornAt: now,
                ttl: 0.72 + Math.random() * 0.18,
                baseOpacity,
                trailOffset: 0
            };
            state.scene.add(p);
            state.chargeParticles.push(p);
        }
    }
}
