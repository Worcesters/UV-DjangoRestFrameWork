import { AbstractService } from "../core/AbstractService.js";

export class HudCombatService extends AbstractService {
    constructor(deps) {
        super("HudCombatService");
        this.deps = deps;
    }

    addScore(points) {
        const state = this.deps.getState();
        if (state.gameOver || points <= 0) return;
        const nextScore = state.score + points;
        this.deps.setState({ score: nextScore });
        const scoreEl = document.getElementById("score-value");
        if (scoreEl) scoreEl.innerText = String(nextScore).padStart(6, "0");
    }

    triggerGameOver() {
        const state = this.deps.getState();
        if (state.gameOver) return;
        this.deps.setState({ gameOver: true, currentPhase: "game_over", bossActive: false });
        const statusEl = document.getElementById("status-text");
        if (statusEl) statusEl.innerText = "Shield Down";
        const bossHud = document.getElementById("boss-hud");
        if (bossHud) bossHud.classList.replace("opacity-100", "opacity-0");

        state.bossProjectiles.forEach((p) => state.scene.remove(p));
        state.bossProjectiles.length = 0;
        state.enemyDrones.forEach((d) => state.scene.remove(d));
        state.enemyDrones.length = 0;
        state.drones.forEach((d) => state.releasePlayerDroneVisual(d));
        state.drones.length = 0;
        state.friendBullets.forEach((b) => state.releaseFriendBullet(b));
        state.friendBullets.length = 0;
        state.friendShips.forEach((f) => state.scene.remove(f));
        state.friendShips.length = 0;
        state.bonusGates.forEach((g) => state.scene.remove(g));
        state.bonusGates.length = 0;
        if (state.currentBoss && state.currentBoss.userData && state.currentBoss.userData.escorts) {
            state.currentBoss.userData.escorts.forEach((e) => state.scene.remove(e));
            state.currentBoss.userData.escorts.length = 0;
        }

        const over = document.getElementById("game-over-screen");
        const scoreOver = document.getElementById("game-over-score");
        if (scoreOver) scoreOver.innerText = String(state.score).padStart(6, "0");
        if (over) {
            over.classList.remove("hidden");
            over.classList.add("flex");
        }
    }

    onShieldHit(intensity = 10, isBigLaser = false) {
        const state = this.deps.getState();
        if (state.shieldPower <= 0 || state.gameOver) return;
        let nextShield = state.shieldPower - (isBigLaser ? 15 : 5);
        nextShield = Math.max(0, nextShield);
        this.deps.setState({ shieldPower: nextShield, shakeIntensity: intensity });

        const shieldBar = document.getElementById("shield-bar");
        const shieldPct = document.getElementById("shield-percent");
        if (shieldBar) shieldBar.style.width = `${nextShield}%`;
        if (shieldPct) shieldPct.innerText = `${Math.round(nextShield)}%`;

        const shieldMesh = state.shieldMesh;
        if (shieldMesh && shieldMesh.material) {
            shieldMesh.material.opacity = 0.8;
            if (shieldMesh.userData && shieldMesh.userData.fadeTimeout) {
                clearTimeout(shieldMesh.userData.fadeTimeout);
            }
            if (!shieldMesh.userData) shieldMesh.userData = {};
            shieldMesh.userData.fadeTimeout = setTimeout(() => {
                if (shieldMesh.material) shieldMesh.material.opacity = 0;
            }, 1000);
        }
        if (nextShield <= 0) this.triggerGameOver();
    }

    setupBossHud(type, boss) {
        const card = document.getElementById("boss-hud-card");
        const name = document.getElementById("boss-name");
        const shieldWrap = document.getElementById("boss-shield-wrap");
        const fleetWrap = document.getElementById("boss-fleet-bars");
        const hullWrap = document.getElementById("boss-hull-wrap");
        if (!card || !name || !shieldWrap || !fleetWrap || !hullWrap) return;
        if (type === "atlante") {
            card.classList.remove("border-red-600");
            card.classList.add("border-cyan-500");
            name.classList.remove("text-red-500");
            name.classList.add("text-cyan-300");
            name.innerText = "Atlante Warship Detected";
            shieldWrap.classList.remove("hidden");
            hullWrap.classList.remove("hidden");
            fleetWrap.classList.add("hidden");
            fleetWrap.innerHTML = "";
        } else if (type === "kira") {
            card.classList.remove("border-red-600");
            card.classList.add("border-cyan-500");
            name.classList.remove("text-red-500");
            name.classList.add("text-cyan-300");
            name.innerText = "Kira-3 Target Locked";
            shieldWrap.classList.remove("hidden");
            hullWrap.classList.remove("hidden");
            fleetWrap.classList.add("hidden");
            fleetWrap.innerHTML = "";
        } else {
            card.classList.remove("border-cyan-500");
            card.classList.add("border-red-600");
            name.classList.remove("text-cyan-300");
            name.classList.add("text-red-500");
            name.innerText = "Wraith Hive Ship Detected";
            shieldWrap.classList.add("hidden");
            hullWrap.classList.remove("hidden");
            fleetWrap.classList.add("hidden");
            fleetWrap.innerHTML = "";
        }
        const hpPct = (boss.userData.hp / boss.userData.maxHp) * 100;
        const bossHpBar = document.getElementById("boss-hp-bar");
        if (bossHpBar) bossHpBar.style.width = `${hpPct}%`;
        const shieldPct = boss.userData.maxShield > 0 ? (boss.userData.shield / boss.userData.maxShield) * 100 : 0;
        const bossShieldBar = document.getElementById("boss-shield-bar");
        if (bossShieldBar) bossShieldBar.style.width = `${shieldPct}%`;
    }

    focusHudOnVictim(victim) {
        if (!victim || !victim.userData) return;
        const shieldWrap = document.getElementById("boss-shield-wrap");
        if (!shieldWrap) return;
        const hpPct = ((victim.userData.hp || 0) / Math.max(1, (victim.userData.maxHp || 1))) * 100;
        const shieldPct = ((victim.userData.shield || 0) / Math.max(1, (victim.userData.maxShield || 1))) * 100;
        const bossHpBar2 = document.getElementById("boss-hp-bar");
        if (bossHpBar2) bossHpBar2.style.width = `${Math.max(0, hpPct)}%`;
        const bossShieldBar2 = document.getElementById("boss-shield-bar");
        if ((victim.userData.maxShield || 0) > 0) {
            shieldWrap.classList.remove("hidden");
            if (bossShieldBar2) bossShieldBar2.style.width = `${Math.max(0, shieldPct)}%`;
        } else {
            shieldWrap.classList.add("hidden");
            if (bossShieldBar2) bossShieldBar2.style.width = "0%";
        }
    }

    getNearestFleetShip(fromPos, type) {
        const state = this.deps.getState();
        if (!state.currentBoss || state.currentBoss.userData.type !== type) return state.currentBoss;
        const fleet = (state.currentBoss.userData.fleet || []).filter((s) => s && s.userData && s.userData.hp > 0);
        if (!fleet.length) return null;
        let nearest = fleet[0];
        let best = nearest.position.distanceTo(fromPos);
        for (let i = 1; i < fleet.length; i++) {
            const d = fleet[i].position.distanceTo(fromPos);
            if (d < best) {
                best = d;
                nearest = fleet[i];
            }
        }
        return nearest;
    }
}
