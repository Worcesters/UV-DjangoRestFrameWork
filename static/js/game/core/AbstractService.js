export class AbstractService {
    constructor(name = "AbstractService") {
        if (new.target === AbstractService) {
            throw new Error(`${name} cannot be instantiated directly.`);
        }
        this.serviceName = name;
    }
}
