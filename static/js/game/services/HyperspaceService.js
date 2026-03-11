import { AbstractService } from "../core/AbstractService.js";

export class HyperspaceService extends AbstractService {
    constructor(deps) {
        super("HyperspaceService");
        this.deps = deps;
    }

    start(gate) {
        const state = this.deps.getState();
        if (state.gameOver) return;
        this.deps.setState({ currentPhase: "hyperspace" });
        state.bonusGates.forEach((g) => state.scene.remove(g));
        state.bonusGates.length = 0;
        state.hyperspaceTunnel.visible = true;

        setTimeout(() => {
            const live = this.deps.getState();
            live.hyperspaceTunnel.visible = false;
            this.deps.applySector(this.deps.pickNextSector());

            const wraithCountByScore = live.bossFleetCaps.wraith;
            const kiraCountByScore = live.bossFleetCaps.kira;
            const atlanteCountByScore = live.bossFleetCaps.atlante;
            const bossTypes = ["wraith", "atlante", "kira"];
            const bossType = bossTypes[Math.floor(Math.random() * bossTypes.length)];
            let currentBoss = (
                bossType === "atlante"
                    ? live.atlanteBossModel
                    : (bossType === "kira" ? live.kiraBossModel : live.wraithBossModel)
            ).clone();

            if (bossType === "atlante") {
                this.deps.applyAtlanteMetalMaterial(currentBoss);
                currentBoss.scale.set(6.5, 6.5, 6.5);
                currentBoss.position.set(0, -12, live.ship.position.z - 1540);
                currentBoss.rotation.x = -0.08;
                currentBoss.rotation.z = 0.07;
                currentBoss.rotation.y = -0.2;
                currentBoss.updateMatrixWorld(true);
                const bbox = new live.THREE.Box3().setFromObject(currentBoss);
                const worldCenter = bbox.getCenter(new live.THREE.Vector3());
                const localCenter = currentBoss.worldToLocal(worldCenter.clone());
                currentBoss.children.forEach((child) => {
                    if (child.isMesh || child.isGroup || child.type === "Object3D") child.position.sub(localCenter);
                });
                currentBoss.updateMatrixWorld(true);
                const bossShield = new live.THREE.Mesh(
                    new live.THREE.SphereGeometry(85, 32, 32),
                    new live.THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0, blending: live.THREE.AdditiveBlending, side: live.THREE.DoubleSide })
                );
                bossShield.position.set(0, 0, 0);
                currentBoss.add(bossShield);
                const atlanteOffsets = [-920, 920];
                const escorts = [];
                for (let i = 0; i < atlanteCountByScore - 1; i++) {
                    const escort = live.atlanteBossModel.clone();
                    this.deps.applyAtlanteMetalMaterial(escort);
                    escort.scale.set(6.2, 6.2, 6.2);
                    escort.position.set(currentBoss.position.x + atlanteOffsets[i], currentBoss.position.y + (i === 0 ? 26 : -26), currentBoss.position.z - 120);
                    escort.rotation.x = -0.08;
                    escort.rotation.z = 0.07;
                    escort.rotation.y = -0.2;
                    this.deps.centerModelOnVisualPivot(escort);
                    const escortShield = new live.THREE.Mesh(
                        new live.THREE.SphereGeometry(78, 24, 24),
                        new live.THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0, blending: live.THREE.AdditiveBlending, side: live.THREE.DoubleSide })
                    );
                    escort.add(escortShield);
                    escort.userData = {
                        offsetX: atlanteOffsets[i],
                        offsetY: (i === 0 ? 26 : -26),
                        offsetZ: -120,
                        lastSalvoAt: 0,
                        shieldMesh: escortShield,
                        shield: 170,
                        maxShield: 170,
                        hp: 130,
                        maxHp: 130
                    };
                    escorts.push(escort);
                    live.scene.add(escort);
                }
                this.deps.enforceShieldNoContact(currentBoss, escorts, 90);
                const fleet = [currentBoss].concat(escorts);
                currentBoss.userData = {
                    type: "atlante",
                    hp: 140, maxHp: 140, shield: 220, maxShield: 220, shieldMesh: bossShield,
                    gate, data: live.experiences[live.experienceIndex % live.experiences.length],
                    lastSalvoAt: 0, escorts, fleet
                };
                currentBoss.userData.fleet.forEach((shipRef) => {
                    if (!shipRef.userData) shipRef.userData = {};
                    shipRef.userData.hp = shipRef.userData.hp || 140;
                    shipRef.userData.maxHp = shipRef.userData.maxHp || 140;
                    shipRef.userData.shield = shipRef.userData.shield || 220;
                    shipRef.userData.maxShield = shipRef.userData.maxShield || 220;
                    shipRef.userData.lastSalvoAt = shipRef.userData.lastSalvoAt || 0;
                });
            } else if (bossType === "kira") {
                this.deps.applyKiraMetalMaterial(currentBoss);
                this.deps.centerModelOnVisualPivot(currentBoss);
                currentBoss.scale.set(40, 40, 40);
                currentBoss.position.set(0, 30, live.ship.position.z - 1780);
                currentBoss.rotation.y = -live.THREE.MathUtils.degToRad(50);
                currentBoss.rotation.x = -0.06;
                currentBoss.rotation.z = 0.05;
                const escorts = [];
                const shieldMain = new live.THREE.Mesh(
                    new live.THREE.SphereGeometry(19, 28, 28),
                    new live.THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0, blending: live.THREE.AdditiveBlending, side: live.THREE.DoubleSide })
                );
                currentBoss.add(shieldMain);
                currentBoss.userData.shieldMesh = shieldMain;
                currentBoss.userData.shield = 110;
                currentBoss.userData.maxShield = 110;
                const kiraSlots = [
                    { x: -560, y: 180, z: -120 }, { x: 560, y: -180, z: -120 },
                    { x: -520, y: -210, z: -180 }, { x: 520, y: 210, z: -180 }
                ];
                for (let i = 0; i < kiraCountByScore - 1; i++) {
                    const slot = kiraSlots[i % kiraSlots.length];
                    const escort = live.kiraBossModel.clone();
                    this.deps.applyKiraMetalMaterial(escort);
                    this.deps.centerModelOnVisualPivot(escort);
                    escort.scale.set(40, 40, 40);
                    escort.rotation.y = -live.THREE.MathUtils.degToRad(50);
                    escort.rotation.x = -0.06;
                    escort.rotation.z = 0.05;
                    escort.position.set(currentBoss.position.x + slot.x, currentBoss.position.y + slot.y, currentBoss.position.z + slot.z);
                    const escortShield = new live.THREE.Mesh(
                        new live.THREE.SphereGeometry(18, 24, 24),
                        new live.THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0, blending: live.THREE.AdditiveBlending, side: live.THREE.DoubleSide })
                    );
                    escort.add(escortShield);
                    escort.userData = { offsetX: slot.x, offsetY: slot.y, offsetZ: slot.z, lastSalvoAt: 0, shieldMesh: escortShield, shield: 95, maxShield: 95, hp: 120, maxHp: 120 };
                    escorts.push(escort);
                    live.scene.add(escort);
                }
                this.deps.enforceShieldNoContact(currentBoss, escorts, 90);
                const fleet = [currentBoss].concat(escorts);
                currentBoss.userData = {
                    type: "kira",
                    hp: 130, maxHp: 130, shield: 110, maxShield: 110, shieldMesh: shieldMain,
                    gate, data: live.experiences[live.experienceIndex % live.experiences.length],
                    lastSalvoAt: 0, escorts, fleet
                };
                currentBoss.userData.fleet.forEach((shipRef) => {
                    if (!shipRef.userData) shipRef.userData = {};
                    if (shipRef !== currentBoss && shipRef.userData.hp) return;
                    shipRef.userData.hp = shipRef.userData.hp || 130;
                    shipRef.userData.maxHp = shipRef.userData.maxHp || 130;
                    shipRef.userData.shield = shipRef.userData.shield || 110;
                    shipRef.userData.maxShield = shipRef.userData.maxShield || 110;
                });
            } else {
                currentBoss.scale.set(4, 4, 4);
                currentBoss.position.set(0, 0, live.ship.position.z - 1600);
                const escorts = [];
                const wraithSlots = [
                    { x: -560, y: 230, z: -170 }, { x: 560, y: -230, z: -170 }, { x: -620, y: -160, z: -240 },
                    { x: 620, y: 160, z: -240 }, { x: -360, y: 260, z: -300 }, { x: 360, y: -260, z: -300 },
                    { x: -700, y: 40, z: -340 }, { x: 700, y: -40, z: -340 }, { x: 0, y: 300, z: -380 }
                ];
                for (let i = 0; i < wraithCountByScore - 1; i++) {
                    const slot = wraithSlots[i % wraithSlots.length];
                    const escort = live.wraithBossModel.clone();
                    escort.scale.set(3.5, 3.5, 3.5);
                    escort.position.set(currentBoss.position.x + slot.x, currentBoss.position.y + slot.y, currentBoss.position.z + slot.z);
                    escort.userData = { offsetX: slot.x, offsetY: slot.y, offsetZ: slot.z, lastShotCenter: 0, lastShotWing: 0, wingSide: slot.x >= 0 ? 1 : -1 };
                    escorts.push(escort);
                    live.scene.add(escort);
                }
                const fleet = [currentBoss].concat(escorts);
                currentBoss.userData = {
                    type: "wraith", hp: 160, maxHp: 160, shield: 0, maxShield: 0,
                    gate, data: live.experiences[live.experienceIndex % live.experiences.length],
                    lastShotCenter: 0, lastShotWing: 0, wingSide: 1, escorts, fleet
                };
                currentBoss.userData.fleet.forEach((shipRef) => {
                    if (!shipRef.userData) shipRef.userData = {};
                    shipRef.userData.hp = 160;
                    shipRef.userData.maxHp = 160;
                });
            }

            live.scene.add(currentBoss);
            this.deps.setState({ currentBoss, bossActive: true, currentPhase: "boss_fight" });
            this.deps.setupBossHud(bossType, currentBoss);
            document.getElementById("boss-hud").classList.replace("opacity-0", "opacity-100");
        }, 2000);
    }
}
