import { AbstractService } from "../core/AbstractService.js";

export class AnimateService extends AbstractService {
    constructor(deps) {
        super("AnimateService");
        this.deps = deps;
    }

    start() {
        const state = this.deps.getState();
        if (state._animateLoopStarted) return;
        this.deps.setState({ _animateLoopStarted: true });

        const loop = () => {
            this.deps.runAnimateFrame();
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }
}
