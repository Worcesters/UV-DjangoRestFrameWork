import { AbstractService } from "../core/AbstractService.js";

export class BossCombatService extends AbstractService {
    constructor(deps) {
        super("BossCombatService");
        this.deps = deps;
    }

    estimateShieldWorldRadius(shipRef) {
        const state = this.deps.getState();
        if (!shipRef || !shipRef.userData || !shipRef.userData.shieldMesh) return 0;
        const shieldMesh = shipRef.userData.shieldMesh;
        const params = shieldMesh.geometry && shieldMesh.geometry.parameters ? shieldMesh.geometry.parameters : null;
        const localRadius = params && params.radius ? params.radius : 0;
        if (!localRadius) return 0;
        const worldScale = new state.THREE.Vector3();
        shieldMesh.getWorldScale(worldScale);
        return localRadius * Math.max(worldScale.x, worldScale.y, worldScale.z);
    }

    enforceShieldNoContact(leader, escorts, padding = 60) {
        const state = this.deps.getState();
        const fleet = [leader].concat(escorts || []);
        if (fleet.length < 2) return;
        for (let iter = 0; iter < 10; iter++) {
            let moved = false;
            for (let i = 0; i < fleet.length; i++) {
                for (let j = i + 1; j < fleet.length; j++) {
                    const a = fleet[i];
                    const b = fleet[j];
                    const ra = this.estimateShieldWorldRadius(a);
                    const rb = this.estimateShieldWorldRadius(b);
                    if (ra <= 0 || rb <= 0) continue;
                    const minDist = ra + rb + padding;
                    const delta = new state.THREE.Vector3().subVectors(b.position, a.position);
                    let dist = delta.length();
                    if (dist < 0.001) {
                        delta.set(1, 0, 0);
                        dist = 0.001;
                    }
                    if (dist < minDist) {
                        const push = minDist - dist;
                        const dir = delta.normalize();
                        if (i === 0) {
                            b.position.add(dir.clone().multiplyScalar(push));
                        } else {
                            a.position.add(dir.clone().multiplyScalar(-push * 0.5));
                            b.position.add(dir.clone().multiplyScalar(push * 0.5));
                        }
                        moved = true;
                    }
                }
            }
            if (!moved) break;
        }
        for (let i = 0; i < escorts.length; i++) {
            const e = escorts[i];
            e.userData = {
                ...(e.userData || {}),
                offsetX: e.position.x - leader.position.x,
                offsetY: e.position.y - leader.position.y,
                offsetZ: e.position.z - leader.position.z
            };
        }
    }

    spawnProgressiveBossHits(target, burstCount = 10, durationMs = 650, baseScale = 2.4) {
        const state = this.deps.getState();
        if (!target || !target.parent) return;
        const stepMs = Math.max(35, Math.floor(durationMs / Math.max(1, burstCount)));
        for (let i = 0; i < burstCount; i++) {
            setTimeout(() => {
                if (!target || !target.parent) return;
                const hitFx = state.hitEffectModel ? state.hitEffectModel.clone() : state.explosionModel.clone();
                const jitter = new state.THREE.Vector3(
                    (Math.random() - 0.5) * 170,
                    (Math.random() - 0.5) * 120,
                    (Math.random() - 0.5) * 160
                );
                hitFx.position.copy(target.position).add(jitter);
                const s = baseScale + (i / Math.max(1, burstCount - 1)) * (baseScale * 0.9);
                hitFx.scale.set(s, s, s);
                state.scene.add(hitFx);
                setTimeout(() => state.scene.remove(hitFx), 360 + i * 20);
            }, i * stepMs);
        }
    }

    spawnGuaranteedBossHitFx(targetShip, baseScale = 10) {
        const state = this.deps.getState();
        if (!targetShip || !targetShip.parent) return;
        const center = targetShip.position.clone().add(new state.THREE.Vector3(
            (Math.random() - 0.5) * 60,
            (Math.random() - 0.5) * 40,
            (Math.random() - 0.5) * 60
        ));
        const core = new state.THREE.Mesh(
            new state.THREE.SphereGeometry(1.6, 10, 10),
            new state.THREE.MeshBasicMaterial({
                color: 0xffe066,
                transparent: true,
                opacity: 0.95,
                blending: state.THREE.AdditiveBlending,
                depthTest: false,
                depthWrite: false
            })
        );
        core.position.copy(center);
        core.scale.set(baseScale, baseScale, baseScale);
        state.scene.add(core);
        const ring = new state.THREE.Mesh(
            new state.THREE.TorusGeometry(1.2, 0.22, 8, 22),
            new state.THREE.MeshBasicMaterial({
                color: 0xffb703,
                transparent: true,
                opacity: 0.88,
                blending: state.THREE.AdditiveBlending,
                depthTest: false,
                depthWrite: false
            })
        );
        ring.position.copy(center);
        ring.rotation.x = Math.random() * Math.PI;
        ring.rotation.y = Math.random() * Math.PI;
        ring.scale.set(baseScale * 0.75, baseScale * 0.75, baseScale * 0.75);
        state.scene.add(ring);
        setTimeout(() => state.scene.remove(core), 180);
        setTimeout(() => state.scene.remove(ring), 220);
    }

    playCinematicFleetDestruction(ships, onFinished) {
        const state = this.deps.getState();
        const aliveShips = (ships || []).filter((s) => s && s.parent);
        if (!aliveShips.length) {
            if (onFinished) onFinished();
            return;
        }
        const center = new state.THREE.Vector3(0, 0, 0);
        for (let i = 0; i < aliveShips.length; i++) center.add(aliveShips[i].position);
        center.multiplyScalar(1 / aliveShips.length);
        const stepMs = 620;
        for (let i = 0; i < aliveShips.length; i++) {
            const shipRef = aliveShips[i];
            setTimeout(() => {
                if (!shipRef || !shipRef.parent) return;
                this.spawnProgressiveBossHits(shipRef, 5, 420, 2.6);
                this.spawnGuaranteedBossHitFx(shipRef, 10.5);
                const localBoom = state.explosionModel.clone();
                localBoom.position.copy(shipRef.position);
                localBoom.scale.set(5.5, 5.5, 5.5);
                state.scene.add(localBoom);
                setTimeout(() => state.scene.remove(localBoom), 540);
            }, i * stepMs);
        }
        const finalDelay = aliveShips.length * stepMs + 500;
        setTimeout(() => {
            const finalExplo = state.explosionModel.clone();
            finalExplo.position.copy(center);
            finalExplo.scale.set(15, 15, 15);
            state.scene.add(finalExplo);
            for (let i = 0; i < 4; i++) {
                setTimeout(() => {
                    const pulse = new state.THREE.Mesh(
                        new state.THREE.SphereGeometry(2.2, 12, 12),
                        new state.THREE.MeshBasicMaterial({
                            color: 0xffb703,
                            transparent: true,
                            opacity: 0.85,
                            blending: state.THREE.AdditiveBlending,
                            depthTest: false,
                            depthWrite: false
                        })
                    );
                    pulse.position.copy(center).add(new state.THREE.Vector3(
                        (Math.random() - 0.5) * 120,
                        (Math.random() - 0.5) * 90,
                        (Math.random() - 0.5) * 120
                    ));
                    const s = 8 + i * 2.5;
                    pulse.scale.set(s, s, s);
                    state.scene.add(pulse);
                    setTimeout(() => state.scene.remove(pulse), 260);
                }, i * 90);
            }
            setTimeout(() => state.scene.remove(finalExplo), 980);
        }, finalDelay);
        setTimeout(() => {
            aliveShips.forEach((shipRef) => {
                if (shipRef && shipRef.parent) state.scene.remove(shipRef);
            });
            if (onFinished) onFinished();
        }, finalDelay + 760);
    }

    damageBoss(amount, targetBoss = null) {
        const state = this.deps.getState();
        if (!state.currentBoss || !state.bossActive || state.gameOver) return;
        const victim = targetBoss || state.currentBoss;
        if (!victim || !victim.userData) return;
        if ((state.currentBoss.userData.type === "atlante" || state.currentBoss.userData.type === "kira") && victim.userData.shield > 0) {
            victim.userData.shield = Math.max(0, victim.userData.shield - amount);
            this.deps.addScore(6);
            this.deps.focusHudOnVictim(victim);
            if (victim.userData.shield <= 0) {
                if (victim.userData.shieldMesh) victim.userData.shieldMesh.material.opacity = 0;
            } else if (victim.userData.shieldMesh) {
                victim.userData.shieldMesh.material.opacity = 0.85;
                if (!victim.userData.shieldMesh.userData) victim.userData.shieldMesh.userData = {};
                if (victim.userData.shieldMesh.userData.fadeTimeout) clearTimeout(victim.userData.shieldMesh.userData.fadeTimeout);
                victim.userData.shieldMesh.userData.fadeTimeout = setTimeout(() => {
                    if (victim && victim.userData && victim.userData.shieldMesh) victim.userData.shieldMesh.material.opacity = 0;
                }, 2000);
            }
            return;
        }
        victim.userData.hp = Math.max(0, victim.userData.hp - amount);
        this.deps.addScore(12);
        if (state.currentBoss.userData.type === "atlante" && (victim.userData.shield || 0) <= 0) {
            this.spawnGuaranteedBossHitFx(victim, 13);
            const hullHit = state.hitEffectModel ? state.hitEffectModel.clone() : state.explosionModel.clone();
            hullHit.position.copy(victim.position);
            hullHit.scale.set(12, 12, 12);
            state.scene.add(hullHit);
            setTimeout(() => state.scene.remove(hullHit), 300);
        }
        this.deps.focusHudOnVictim(victim);
        if (state.currentBoss.userData.type === "wraith" || state.currentBoss.userData.type === "kira" || state.currentBoss.userData.type === "atlante") {
            if (victim.userData.hp <= 0) {
                const prevLeader = state.currentBoss;
                const survivorsAfterKill = (prevLeader.userData.fleet || []).filter((s) => s && s !== victim && s.userData && s.userData.hp > 0);
                const finalKill = survivorsAfterKill.length === 0;
                victim.userData.destroying = true;
                victim.userData.frozenPosition = victim.position.clone();
                if (!finalKill) {
                    const burstScale = state.currentBoss.userData.type === "kira" ? 3.4 : (state.currentBoss.userData.type === "atlante" ? 3.0 : 2.8);
                    this.spawnProgressiveBossHits(victim, 12, 760, burstScale);
                    const shipExplo = state.explosionModel.clone();
                    shipExplo.position.copy(victim.position);
                    if (state.currentBoss.userData.type === "kira") shipExplo.scale.set(10, 5.2, 5.2);
                    else if (state.currentBoss.userData.type === "atlante") shipExplo.scale.set(8, 4.4, 4.4);
                    else shipExplo.scale.set(10, 2.2, 2.2);
                    state.scene.add(shipExplo);
                    setTimeout(() => state.scene.remove(shipExplo), 450);
                }
                if (finalKill) {
                    if (victim !== state.currentBoss) {
                        if (state.currentBoss && state.currentBoss.parent) state.scene.remove(state.currentBoss);
                        this.deps.setState({ currentBoss: victim });
                    }
                    const refreshed = this.deps.getState().currentBoss;
                    refreshed.userData = {
                        ...(refreshed.userData || {}),
                        type: prevLeader.userData.type,
                        gate: prevLeader.userData.gate,
                        data: prevLeader.userData.data,
                        escorts: [],
                        fleet: [refreshed]
                    };
                    const fleetWrap = document.getElementById("boss-fleet-bars");
                    if (fleetWrap) {
                        fleetWrap.classList.add("hidden");
                        fleetWrap.innerHTML = "";
                    }
                }
                if (!finalKill && victim === prevLeader && survivorsAfterKill.length > 0) {
                    victim.visible = false;
                    victim.userData.hp = 0;
                    victim.userData.maxHp = victim.userData.maxHp || 1;
                    this.deps.getState().currentBoss.userData.fleet = survivorsAfterKill;
                    this.deps.getState().currentBoss.userData.escorts = survivorsAfterKill;
                    this.deps.setupBossHud(this.deps.getState().currentBoss.userData.type, this.deps.getState().currentBoss);
                } else if (!finalKill) {
                    setTimeout(() => {
                        if (victim) state.scene.remove(victim);
                    }, 680);
                    this.deps.getState().currentBoss.userData.fleet = survivorsAfterKill;
                    this.deps.getState().currentBoss.userData.escorts = survivorsAfterKill.filter((s) => s !== this.deps.getState().currentBoss);
                }
            }
            const survivors = (this.deps.getState().currentBoss.userData.fleet || []).filter((s) => s && s.userData && s.userData.hp > 0);
            if (survivors.length === 0) {
                this.deps.getState().currentBoss.userData.hp = 0;
                document.getElementById("boss-hp-bar").style.width = "0%";
                this.deps.victory();
            }
            return;
        }
        if (this.deps.getState().currentBoss.userData.hp <= 0) this.deps.victory();
    }

    spawnAtlanteDroneSalvo(shooter) {
        const state = this.deps.getState();
        const source = shooter || state.currentBoss;
        for (let i = 0; i < 40; i++) {
            const angle = (i / 40) * Math.PI * 2;
            const offset = new state.THREE.Vector3(Math.cos(angle) * 70, Math.sin(angle) * 35, -20);
            const spawn = source.position.clone().add(offset);
            let drone;
            if (state.droneModel) {
                drone = state.droneModel.clone();
                drone.scale.set(6.2, 6.2, 6.2);
            } else {
                drone = new state.THREE.Mesh(
                    new state.THREE.SphereGeometry(6.5, 10, 10),
                    new state.THREE.MeshBasicMaterial({ color: 0xffd000, emissive: 0xffcc00, emissiveIntensity: 2.8 })
                );
            }
            drone.position.copy(spawn);
            this.deps.attachDroneYellowLight(drone, 1.2, 26);
            drone.userData = {
                velocity: new state.THREE.Vector3(0, 0, 0),
                bornAt: state.clock.getElapsedTime(),
                ttl: 6.2,
                lockAt: 1.25 + Math.random() * 0.25,
                locked: false,
                lockSpeed: 19,
                lockTarget: null,
                spiralCenter: spawn.clone(),
                spiralRadius: 60 + Math.random() * 24,
                spiralAngle: Math.random() * Math.PI * 2,
                spiralSpeed: 0.16 + Math.random() * 0.22,
                ascendSpeed: 10 + Math.random() * 8,
                driftZ: 6 + Math.random() * 5,
                spread: 0.22
            };
            state.scene.add(drone);
            state.enemyDrones.push(drone);
        }
    }

    spawnKiraDroneSalvo(shooter) {
        const state = this.deps.getState();
        const base = shooter.position.clone();
        for (let i = 0; i < 20; i++) {
            const angle = (i / 20) * Math.PI * 2;
            const ring = 120 + (i % 5) * 18;
            const spawn = base.clone().add(new state.THREE.Vector3(
                Math.cos(angle) * ring * 0.8,
                Math.sin(angle) * ring * 0.45,
                -40 + (i % 4) * 12
            ));
            const radial = new state.THREE.Vector3(Math.cos(angle), Math.sin(angle) * 0.6, -0.2).normalize();
            let drone;
            if (state.droneModel) {
                drone = state.droneModel.clone();
                drone.scale.set(5.6, 5.6, 5.6);
            } else {
                drone = new state.THREE.Mesh(
                    new state.THREE.SphereGeometry(5.2, 9, 9),
                    new state.THREE.MeshBasicMaterial({ color: 0xffd000, emissive: 0xffcc00, emissiveIntensity: 3.2 })
                );
            }
            drone.position.copy(spawn);
            this.deps.attachDroneYellowLight(drone, 2.0, 46);
            drone.userData = {
                velocity: radial.clone().multiplyScalar(5),
                bornAt: state.clock.getElapsedTime(),
                ttl: 7.2,
                lockAt: 1.45 + Math.random() * 0.35,
                locked: false,
                lockSpeed: 17,
                lockTarget: null,
                spiralCenter: spawn.clone(),
                spiralRadius: 90 + Math.random() * 30,
                spiralAngle: angle,
                spiralSpeed: 0.2 + Math.random() * 0.26,
                ascendSpeed: 9 + Math.random() * 7,
                driftZ: 5 + Math.random() * 4,
                spread: 0.28
            };
            state.scene.add(drone);
            state.enemyDrones.push(drone);
        }
    }

    pickDroneLockTarget() {
        const state = this.deps.getState();
        const shipPos = state.ship.position.clone();
        if (!state.friendShips.length) return shipPos;
        if (Math.random() < 0.7) return shipPos;
        const friend = state.friendShips[Math.floor(Math.random() * state.friendShips.length)];
        return friend ? friend.position.clone() : shipPos;
    }
}
