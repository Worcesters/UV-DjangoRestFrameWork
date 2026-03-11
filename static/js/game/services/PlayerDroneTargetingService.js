import { AbstractService } from "../core/AbstractService.js";

export class PlayerDroneTargetingService extends AbstractService {
    constructor(strategies) {
        super("PlayerDroneTargetingService");
        this.strategies = strategies || [];
    }

    pickTarget(context, fromPos) {
        for (let i = 0; i < this.strategies.length; i++) {
            const strategy = this.strategies[i];
            if (!strategy.supports(context)) continue;
            const target = strategy.select(context, fromPos);
            if (target) return target;
        }
        return null;
    }
}
