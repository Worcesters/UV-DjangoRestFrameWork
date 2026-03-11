/**
 * @interface ITargetSelectionContext
 * @property {boolean} bossActive
 * @property {object | null} currentBoss
 */

export class TargetSelectionStrategy {
    supports(_context) {
        throw new Error("supports(context) must be implemented by subclasses.");
    }

    select(_context, _fromPos) {
        throw new Error("select(context, fromPos) must be implemented by subclasses.");
    }
}
