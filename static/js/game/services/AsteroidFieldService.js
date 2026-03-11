import { AbstractService } from "../core/AbstractService.js";

export class AsteroidFieldService extends AbstractService {
    constructor(deps) {
        super("AsteroidFieldService");
        this.deps = deps;
    }

    spawnAsteroid() {
        const state = this.deps.getState();
        if (!state.asteroidModel || !state.ship) return null;
        const a = state.asteroidModel.clone();
        a.position.set(
            (Math.random() - 0.5) * 2000,
            (Math.random() - 0.5) * 1200,
            state.ship.position.z - Math.random() * 6000
        );
        a.scale.setScalar(Math.random() * 0.6 + 0.2);
        a.userData = {
            reboundVelocity: null,
            friendHp: 3,
            isAsteroid: true,
            inferredVelocity: new state.THREE.Vector3(),
            prevPos: a.position.clone()
        };
        state.scene.add(a);
        state.asteroids.push(a);
        return a;
    }

    resetField() {
        const state = this.deps.getState();
        for (let i = 0; i < state.asteroids.length; i++) {
            const a = state.asteroids[i];
            a.visible = true;
            a.position.x = (Math.random() - 0.5) * 1700;
            a.position.y = (Math.random() - 0.5) * 1000;
            a.position.z = state.ship.position.z - (800 + Math.random() * 5200);
            a.userData.velocity = null;
            a.userData.hitCooldown = 0;
            a.userData.friendHp = 3;
            if (!a.userData.inferredVelocity) a.userData.inferredVelocity = new state.THREE.Vector3();
            a.userData.inferredVelocity.set(0, 0, 0);
            if (!a.userData.prevPos) a.userData.prevPos = a.position.clone();
            a.userData.prevPos.copy(a.position);
        }
    }

    updateFrame(factor, delta) {
        const state = this.deps.getState();
        for (let i = 0; i < state.asteroids.length; i++) {
            const a = state.asteroids[i];
            if (state.currentPhase === "boss_fight" || state.currentPhase === "hyperspace") {
                a.visible = false;
                continue;
            }
            a.visible = true;

            if (a.userData.velocity) {
                a.position.addScaledVector(a.userData.velocity, factor);
                a.userData.velocity.multiplyScalar(0.92);
                if (a.userData.velocity.lengthSq() < 1) a.userData.velocity = null;
            }

            if (!a.userData.prevPos) a.userData.prevPos = a.position.clone();
            if (!a.userData.inferredVelocity) a.userData.inferredVelocity = new state.THREE.Vector3();
            a.userData.inferredVelocity.subVectors(a.position, a.userData.prevPos).multiplyScalar(1 / Math.max(delta, 0.001));
            a.userData.prevPos.copy(a.position);

            if (a.position.z > state.ship.position.z + 300) {
                a.position.z = state.ship.position.z - 6000 - (Math.random() * 2000);
                a.position.x = (Math.random() - 0.5) * 2000;
                a.userData.velocity = null;
                a.userData.hitCooldown = 0;
                a.userData.friendHp = 3;
                a.userData.inferredVelocity.set(0, 0, 0);
                a.userData.prevPos.copy(a.position);
            }

            if (a.userData.hitCooldown) a.userData.hitCooldown--;
            const dist = a.position.distanceTo(state.ship.position);
            if (dist < 80 && !a.userData.hitCooldown) {
                if (this.deps.onShieldHit) this.deps.onShieldHit(15, true);
                const pushDir = new state.THREE.Vector3().subVectors(a.position, state.ship.position).normalize();
                a.userData.velocity = pushDir.multiplyScalar(150);
                a.userData.hitCooldown = 45;
            }
        }
    }
}
