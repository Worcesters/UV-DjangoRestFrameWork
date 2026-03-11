import { PlayerShipService } from "./services/PlayerShipService.js";
import { PlayerDroneTargetingService } from "./services/PlayerDroneTargetingService.js";
import { HudCombatService } from "./services/HudCombatService.js";
import { TargetingService } from "./services/TargetingService.js";
import { AsteroidFieldService } from "./services/AsteroidFieldService.js";
import { BossCombatService } from "./services/BossCombatService.js";
import { ReactorTrailService } from "./services/ReactorTrailService.js";
import { AnimateService } from "./services/AnimateService.js";
import { HyperspaceService } from "./services/HyperspaceService.js";
import { LoadModelService } from "./services/LoadModelService.js";
import { BossFleetTargetStrategy } from "./strategies/BossFleetTargetStrategy.js";
import { AsteroidTargetStrategy } from "./strategies/AsteroidTargetStrategy.js";

export class GameFacade {
    constructor(deps) {
        this.deps = deps;
        this.playerShip = new PlayerShipService(deps);
        this.hudCombat = new HudCombatService(deps);
        this.targeting = new TargetingService(deps);
        this.asteroidField = new AsteroidFieldService(deps);
        this.bossCombat = new BossCombatService(deps);
        this.reactorTrail = new ReactorTrailService(deps);
        this.animate = new AnimateService(deps);
        this.hyperspace = new HyperspaceService(deps);
        this.loadModel = new LoadModelService(deps);
        this.playerDroneTargeting = new PlayerDroneTargetingService([
            new BossFleetTargetStrategy(),
            new AsteroidTargetStrategy()
        ]);
    }

    getTargetingContext() {
        const state = this.deps.getState();
        return {
            bossActive: state.bossActive,
            currentBoss: state.currentBoss,
            resolveNearestFleetShip: this.deps.resolveNearestFleetShip,
            resolveBestAsteroidTarget: this.deps.resolveBestAsteroidTarget
        };
    }
}
