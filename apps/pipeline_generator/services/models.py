from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerConfig:
    service_name: str
    docker_image: str
    dockerfile_path: str = "Dockerfile"
    ports: str = ""
    environment: str = ""


@dataclass(slots=True)
class PipelineRequest:
    project_name: str
    deploy_target: str
    use_containers: bool
    command_shell: str
    use_ssh: bool
    repo_url: str
    deploy_branch: str
    ssh_host: str
    ssh_user: str
    ssh_port: str
    ssh_key_variable: str
    pre_deploy_commands: list[str] = field(default_factory=list)
    deploy_commands: list[str] = field(default_factory=list)
    post_deploy_commands: list[str] = field(default_factory=list)
    env_variables: dict[str, str] = field(default_factory=dict)
    containers: list[ContainerConfig] = field(default_factory=list)
