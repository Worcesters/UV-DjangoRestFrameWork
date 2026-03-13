import json
from typing import Any

from .models import ContainerConfig, PipelineRequest


class PipelineGenerationError(Exception):
    pass


def _parse_commands(commands_text: str) -> list[str]:
    commands: list[str] = []
    for raw_line in commands_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        commands.append(line)
    return commands


def _parse_env_variables(env_text: str) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_line in env_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise PipelineGenerationError(
                f"Variable invalide: '{line}'. Utilise le format KEY=VALUE."
            )
        key, value = line.split("=", 1)
        variables[key.strip()] = value.strip()
    return variables


def _parse_containers(containers_json: str) -> list[ContainerConfig]:
    if not containers_json:
        return []
    try:
        payload = json.loads(containers_json)
    except json.JSONDecodeError as exc:
        raise PipelineGenerationError("Configuration container invalide (JSON).") from exc

    if not isinstance(payload, list):
        raise PipelineGenerationError("Configuration container invalide: liste attendue.")

    containers: list[ContainerConfig] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        service_name = str(item.get("service_name", "")).strip()
        docker_image = str(item.get("docker_image", "")).strip()
        if not service_name or not docker_image:
            continue
        containers.append(
            ContainerConfig(
                service_name=service_name,
                docker_image=docker_image,
                dockerfile_path=str(item.get("dockerfile_path", "Dockerfile")).strip() or "Dockerfile",
                ports=str(item.get("ports", "")).strip(),
                environment=str(item.get("environment", "")).strip(),
            )
        )
    return containers


def _build_request(data: dict[str, Any]) -> PipelineRequest:
    use_containers = data.get("use_containers") == "yes"
    use_ssh = data.get("use_ssh") == "yes"
    containers = _parse_containers(str(data.get("containers_json", "")))
    if use_containers and not containers:
        raise PipelineGenerationError("Tu as choisi containers=oui, ajoute au moins un container.")
    command_shell = str(data.get("command_shell", "bash")).strip().lower()
    if command_shell not in {"bash", "powershell", "sh"}:
        raise PipelineGenerationError("Shell non supporte. Choisis bash, powershell ou sh.")

    ssh_host = str(data.get("ssh_host", "")).strip()
    ssh_user = str(data.get("ssh_user", "")).strip()
    ssh_port = str(data.get("ssh_port", "22")).strip() or "22"
    ssh_key_variable = str(data.get("ssh_key_variable", "SSH_PRIVATE_KEY")).strip() or "SSH_PRIVATE_KEY"
    if use_ssh and (not ssh_host or not ssh_user):
        raise PipelineGenerationError("SSH active: renseigne au minimum host et user.")

    pre_deploy_commands = _parse_commands(str(data.get("pre_deploy_commands", "")))
    deploy_commands = _parse_commands(str(data.get("deploy_commands", "")))
    post_deploy_commands = _parse_commands(str(data.get("post_deploy_commands", "")))

    return PipelineRequest(
        project_name=str(data.get("project_name", "")).strip(),
        deploy_target=str(data.get("deploy_target", "")).strip(),
        use_containers=use_containers,
        command_shell=command_shell,
        use_ssh=use_ssh,
        repo_url=str(data.get("repo_url", "")).strip(),
        deploy_branch=str(data.get("deploy_branch", "main")).strip() or "main",
        ssh_host=ssh_host,
        ssh_user=ssh_user,
        ssh_port=ssh_port,
        ssh_key_variable=ssh_key_variable,
        pre_deploy_commands=pre_deploy_commands,
        deploy_commands=deploy_commands,
        post_deploy_commands=post_deploy_commands,
        env_variables=_parse_env_variables(str(data.get("env_variables", ""))),
        containers=containers if use_containers else [],
    )


def _generate_git_pipeline(request: PipelineRequest) -> str:
    shell_map = {
        "bash": "bash",
        "sh": "sh",
        "powershell": "pwsh",
    }
    shell_value = shell_map.get(request.command_shell, "bash")

    lines = [
        "name: CI-CD",
        "",
        "on:",
        "  push:",
        "    branches:",
        f"      - {request.deploy_branch}",
        "",
        "jobs:",
        "  build-and-deploy:",
        "    runs-on: ubuntu-latest",
    ]

    if request.env_variables:
        lines.extend(["    env:"])
        for key, value in request.env_variables.items():
            lines.append(f"      {key}: {value}")

    lines.extend(
        [
            "    steps:",
            "      - name: Checkout",
            "        uses: actions/checkout@v4",
            "",
            "      - name: Setup pipeline context",
            f"        run: echo \"Project: {request.project_name}\"",
            f"        shell: {shell_value}",
        ]
    )

    if request.repo_url:
        lines.extend(
            [
                "",
                "      - name: Repo target",
                f"        run: echo \"Repository: {request.repo_url}\"",
                f"        shell: {shell_value}",
            ]
        )

    if request.pre_deploy_commands:
        lines.extend(["", "      - name: Pre-deploy commands", "        run: |"])
        lines.extend([f"          {cmd}" for cmd in request.pre_deploy_commands])
        lines.append(f"        shell: {shell_value}")

    if request.use_containers:
        lines.extend(["", "      - name: Build and run containers", "        run: |"])
        for container in request.containers:
            lines.append(
                f"          docker build -t {container.docker_image} -f {container.dockerfile_path} ."
            )
            run_cmd = f"docker run -d --name {container.service_name}"
            if container.ports:
                run_cmd += f" -p {container.ports}"
            if container.environment:
                env_pairs = [e.strip() for e in container.environment.split(",") if e.strip()]
                for pair in env_pairs:
                    run_cmd += f" -e {pair}"
            run_cmd += f" {container.docker_image}"
            lines.append(f"          {run_cmd}")
        lines.append(f"        shell: {shell_value}")

    deploy_cmds = request.deploy_commands or ["echo \"Deploy step a personnaliser\""]

    if request.use_ssh:
        script_lines = "\n".join(deploy_cmds + request.post_deploy_commands)
        lines.extend(
            [
                "",
                "      - name: Deploy over SSH",
                "        uses: appleboy/ssh-action@v1.0.3",
                "        with:",
                f"          host: {request.ssh_host}",
                f"          username: {request.ssh_user}",
                f"          port: {request.ssh_port}",
                f"          key: ${{{{ secrets.{request.ssh_key_variable} }}}}",
                "          script: |",
            ]
        )
        for cmd in script_lines.splitlines():
            lines.append(f"            {cmd}")
    else:
        lines.extend(["", "      - name: Deploy", "        run: |"])
        lines.extend([f"          {cmd}" for cmd in deploy_cmds])
        lines.append(f"        shell: {shell_value}")
        if request.post_deploy_commands:
            lines.extend(["", "      - name: Post-deploy commands", "        run: |"])
            lines.extend([f"          {cmd}" for cmd in request.post_deploy_commands])
            lines.append(f"        shell: {shell_value}")

    return "\n".join(lines) + "\n"


def _generate_jenkins_pipeline(request: PipelineRequest) -> str:
    jenkins_exec = "powershell" if request.command_shell == "powershell" else "sh"

    lines = [
        "pipeline {",
        "  agent any",
        "",
        "  stages {",
        "    stage('Checkout') {",
        "      steps {",
        "        checkout scm",
        "      }",
        "    }",
        "",
        "    stage('Build') {",
        "      steps {",
        f"        echo 'Project: {request.project_name}'",
        "      }",
        "    }",
    ]

    if request.pre_deploy_commands:
        lines.extend(["", "    stage('PreDeploy') {", "      steps {"])
        lines.extend([f"        {jenkins_exec} '{cmd}'" for cmd in request.pre_deploy_commands])
        lines.extend(["      }", "    }"])

    if request.use_containers:
        lines.extend(
            [
                "",
                "    stage('Containers') {",
                "      steps {",
            ]
        )
        for container in request.containers:
            lines.append(
                f"        {jenkins_exec} 'docker build -t {container.docker_image} -f {container.dockerfile_path} .'"
            )
            run_cmd = f"docker run -d --name {container.service_name}"
            if container.ports:
                run_cmd += f" -p {container.ports}"
            if container.environment:
                env_pairs = [e.strip() for e in container.environment.split(",") if e.strip()]
                for pair in env_pairs:
                    run_cmd += f" -e {pair}"
            run_cmd += f" {container.docker_image}"
            lines.append(f"        {jenkins_exec} '{run_cmd}'")
        lines.extend(["      }", "    }"])

    deploy_cmds = request.deploy_commands or ["echo Deploy step a personnaliser"]

    if request.use_ssh:
        lines.extend(
            [
                "",
                "    stage('DeploySSH') {",
                "      steps {",
                "        sshagent(credentials: ['ssh-deploy-key']) {",
                (
                    f"          {jenkins_exec} "
                    f"'ssh -p {request.ssh_port} {request.ssh_user}@{request.ssh_host} "
                    f"\"{'; '.join(deploy_cmds + request.post_deploy_commands)}\"'"
                ),
                "        }",
                "      }",
                "    }",
            ]
        )
    else:
        lines.extend(["", "    stage('Deploy') {", "      steps {"])
        lines.extend([f"        {jenkins_exec} '{cmd}'" for cmd in deploy_cmds])
        lines.extend(["      }", "    }"])
        if request.post_deploy_commands:
            lines.extend(["", "    stage('PostDeploy') {", "      steps {"])
            lines.extend([f"        {jenkins_exec} '{cmd}'" for cmd in request.post_deploy_commands])
            lines.extend(["      }", "    }"])

    lines.extend(["", "  }"])

    if request.env_variables:
        lines.extend(["", "  environment {"])
        for key, value in request.env_variables.items():
            safe_value = value.replace("'", "\\'")
            lines.append(f"    {key} = '{safe_value}'")
        lines.append("  }")

    lines.extend(["}", ""])
    return "\n".join(lines)


def generate_pipeline_config(data: dict[str, Any]) -> str:
    request = _build_request(data)
    if not request.project_name:
        raise PipelineGenerationError("Le nom du projet est obligatoire.")

    if request.deploy_target == "git":
        return _generate_git_pipeline(request)
    if request.deploy_target == "jenkins":
        return _generate_jenkins_pipeline(request)

    raise PipelineGenerationError(f"Cible de deploiement non supportee: {request.deploy_target}")
