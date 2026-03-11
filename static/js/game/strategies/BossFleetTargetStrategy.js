import { TargetSelectionStrategy } from "../core/TargetSelectionStrategy.js";

export class BossFleetTargetStrategy extends TargetSelectionStrategy {
    supports(context) {
        return !!(context?.bossActive && context?.currentBoss && context?.currentBoss?.userData);
    }

    select(context, fromPos) {
        const type = context.currentBoss.userData.type;
        if (type === "wraith" || type === "kira" || type === "atlante") {
            return context.resolveNearestFleetShip(fromPos, type) || context.currentBoss;
        }
        return context.currentBoss;
    }
}
