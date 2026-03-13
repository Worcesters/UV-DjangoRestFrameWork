import subprocess


class GitBranchFetchError(Exception):
    pass


def fetch_remote_branches(repo_url: str) -> list[str]:
    url = (repo_url or "").strip()
    if not url:
        raise GitBranchFetchError("URL repository vide.")

    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", url],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except OSError as exc:
        raise GitBranchFetchError("Git n'est pas disponible sur la machine.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitBranchFetchError("Timeout pendant la recuperation des branches.") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise GitBranchFetchError(stderr or "Impossible de recuperer les branches distantes.")

    branches: list[str] = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        ref = parts[1]
        prefix = "refs/heads/"
        if ref.startswith(prefix):
            branches.append(ref[len(prefix):])

    branches = sorted(set(branches))
    if not branches:
        raise GitBranchFetchError("Aucune branche distante trouvee.")
    return branches
