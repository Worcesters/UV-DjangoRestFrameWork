import { TargetSelectionStrategy } from "../core/TargetSelectionStrategy.js";

export class AsteroidTargetStrategy extends TargetSelectionStrategy {
    supports(context) {
        return !context?.bossActive;
    }

    select(context, fromPos) {
        return context.resolveBestAsteroidTarget(fromPos);
    }
}
