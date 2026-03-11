import { AbstractService } from "../core/AbstractService.js";

export class PlayerShipService extends AbstractService {
    constructor(deps) {
        super("PlayerShipService");
        this.deps = deps;
    }

    requestDodge(now) {
        const { ship, currentPhase, dodgeState, keys } = this.deps.getState();
        if (!ship) return;
        const canDodge = currentPhase !== "hyperspace" && currentPhase !== "charging" && !dodgeState.active && now >= dodgeState.cooldownUntil;
        if (!canDodge) return;
        let dir = 0;
        if (keys["q"] || keys["arrowleft"]) dir = -1;
        else if (keys["d"] || keys["arrowright"]) dir = 1;
        else dir = dodgeState.dir * -1;
        dodgeState.active = true;
        dodgeState.dir = dir;
        dodgeState.remaining = dodgeState.duration;
        dodgeState.cooldownUntil = now + 0.55;
        dodgeState.startRoll = ship.rotation.z;
        dodgeState.startX = ship.position.x;
        dodgeState.targetX = Math.max(-550, Math.min(550, ship.position.x + (dir * 210)));
    }

    updateMovement(delta, factor) {
        const { ship, currentPhase, currentSector, keys, dodgeState, THREE } = this.deps.getState();
        if (!ship || currentPhase === "hyperspace" || currentPhase === "charging") return;
        const limX = 550;
        const limY = 450;
        const controlMul = currentSector && currentSector.modifiers ? currentSector.modifiers.controlMul : 1;
        if ((keys["q"] || keys["arrowleft"]) && ship.position.x > -limX) ship.position.x -= 4.2 * factor * controlMul;
        if ((keys["d"] || keys["arrowright"]) && ship.position.x < limX) ship.position.x += 4.2 * factor * controlMul;
        if (keys["z"] && ship.position.y < limY) ship.position.y += 4.2 * factor * controlMul;
        if (keys["s"] && ship.position.y > -limY) ship.position.y -= 4.2 * factor * controlMul;
        if (dodgeState.active) {
            const progress = 1 - Math.max(0, dodgeState.remaining) / dodgeState.duration;
            const eased = 1 - Math.pow(1 - Math.min(1, progress), 3);
            ship.position.x = THREE.MathUtils.lerp(dodgeState.startX, dodgeState.targetX, eased);
            dodgeState.remaining -= delta;
            if (dodgeState.remaining <= 0) dodgeState.active = false;
        }
    }

    updateRotation() {
        const { ship, keys, dodgeState, THREE } = this.deps.getState();
        if (!ship) return;
        const baseRoll = ((keys["q"] || keys["arrowleft"]) ? -0.22 : 0) + ((keys["d"] || keys["arrowright"]) ? 0.22 : 0);
        const targetPitch = (keys["z"] ? 0.12 : 0) + (keys["s"] ? -0.12 : 0);
        if (dodgeState.active) {
            const progress = 1 - Math.max(0, dodgeState.remaining) / dodgeState.duration;
            ship.rotation.z = dodgeState.startRoll + (dodgeState.dir * Math.PI * 2 * progress);
        } else {
            ship.rotation.z = baseRoll;
        }
        ship.rotation.x = THREE.MathUtils.lerp(ship.rotation.x, targetPitch, 0.12);
    }
}
