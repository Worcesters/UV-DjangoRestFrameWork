import { AbstractService } from "../core/AbstractService.js";

export class TargetingService extends AbstractService {
    constructor(deps) {
        super("TargetingService");
        this.deps = deps;
    }

    getPredictedAsteroidPoint(fromPos, asteroid, projectileSpeedPerSec = 4800) {
        const state = this.deps.getState();
        if (!asteroid || !asteroid.visible) return null;
        const speed = Math.max(1200, projectileSpeedPerSec);
        const vel = asteroid.userData && asteroid.userData.inferredVelocity ? asteroid.userData.inferredVelocity : null;
        let eta = Math.min(1.5, Math.max(0.04, fromPos.distanceTo(asteroid.position) / speed));
        const out = state.tempVecD;
        out.copy(asteroid.position);
        if (vel && vel.lengthSq() > 0.01) {
            for (let i = 0; i < 2; i++) {
                out.copy(asteroid.position).addScaledVector(vel, eta);
                eta = fromPos.distanceTo(out) / speed;
            }
        }
        return out;
    }

    getBestAsteroidForFriend(ally) {
        const state = this.deps.getState();
        let best = null;
        let bestScore = Infinity;
        for (let i = 0; i < state.asteroids.length; i++) {
            const a = state.asteroids[i];
            if (!a.visible) continue;
            const predicted = this.getPredictedAsteroidPoint(ally.position, a, 80 * 60) || a.position;
            if (predicted.z >= ally.position.z) continue;
            const dz = Math.abs(predicted.z - ally.position.z);
            if (dz > 3800) continue;
            const dx = predicted.x - ally.position.x;
            const dy = predicted.y - ally.position.y;
            const scoreAxis = (Math.abs(dx) * 1.4) + (Math.abs(dy) * 1.1);
            const score = scoreAxis + (dz * 0.12) + ((a.userData.inferredVelocity ? a.userData.inferredVelocity.length() : 0) * 0.02);
            if (score < bestScore) {
                bestScore = score;
                best = a;
            }
        }
        return best;
    }

    getBestAsteroidForPlayerDrone(fromPos) {
        const state = this.deps.getState();
        const claimed = new Set();
        for (let i = 0; i < state.drones.length; i++) {
            const t = state.drones[i] && state.drones[i].userData ? state.drones[i].userData.target : null;
            if (t && t.userData && t.userData.isAsteroid && t.visible) claimed.add(t);
        }
        let best = null;
        let bestScore = Infinity;
        for (let i = 0; i < state.asteroids.length; i++) {
            const a = state.asteroids[i];
            if (!a || !a.visible || claimed.has(a)) continue;
            const predicted = this.getPredictedAsteroidPoint(fromPos, a, 80 * 60) || a.position;
            if (predicted.z >= fromPos.z) continue;
            const dz = Math.abs(predicted.z - fromPos.z);
            if (dz > 4200) continue;
            const dx = predicted.x - fromPos.x;
            const dy = predicted.y - fromPos.y;
            const score = (Math.abs(dx) * 1.35) + (Math.abs(dy) * 1.1) + (dz * 0.1);
            if (score < bestScore) {
                bestScore = score;
                best = a;
            }
        }
        return best || this.getBestAsteroidForFriend({ position: fromPos });
    }

    isAsteroidTargetStale(drone, asteroidTarget) {
        const state = this.deps.getState();
        if (!drone || !asteroidTarget || !asteroidTarget.visible) return true;
        const dist = drone.position.distanceTo(asteroidTarget.position);
        if (dist > 2600) return true;
        if (asteroidTarget.position.z > state.ship.position.z + 420) return true;
        if (asteroidTarget.position.z < state.ship.position.z - 7000) return true;
        return false;
    }
}
