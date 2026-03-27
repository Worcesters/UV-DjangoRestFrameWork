import { AbstractService } from "../core/AbstractService.js";

export class AnimateService extends AbstractService {
    constructor(deps) {
        super("AnimateService");
        this.deps = deps;
        this._rafId = null;
        this._stopped = false;
    }

    start() {
        const state = this.deps.getState();
        if (state._animateLoopStarted) return;
        this._stopped = false;
        this.deps.setState({ _animateLoopStarted: true });

        const loop = () => {
            if (this._stopped) return;
            this.deps.runAnimateFrame();
            this._rafId = requestAnimationFrame(loop);
        };
        this._rafId = requestAnimationFrame(loop);
    }

    /** Arrête la boucle requestAnimationFrame (sortie onglet, navigation, nettoyage WebGL). */
    stop() {
        this._stopped = true;
        if (this._rafId != null) {
            cancelAnimationFrame(this._rafId);
            this._rafId = null;
        }
        this.deps.setState({ _animateLoopStarted: false });
    }
}
