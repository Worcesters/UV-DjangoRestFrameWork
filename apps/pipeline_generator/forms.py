from django import forms


INPUT_CLASS = (
    "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 "
    "text-sm font-semibold text-slate-800 shadow-sm "
    "focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-200"
)


class PipelineConfigForm(forms.Form):
    DEPLOY_CHOICES = (
        ("git", "Git (GitHub Actions)"),
        ("gitlab", "GitLab CI"),
        ("jenkins", "Jenkins"),
    )

    YES_NO_CHOICES = (
        ("yes", "Oui"),
        ("no", "Non"),
    )
    SHELL_CHOICES = (
        ("bash", "Bash"),
        ("powershell", "PowerShell"),
        ("sh", "sh"),
    )

    project_name = forms.CharField(
        required=True,
        label="Nom du projet",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "uv-django",
            }
        ),
    )

    deploy_target = forms.ChoiceField(
        required=True,
        initial="git",
        choices=DEPLOY_CHOICES,
        label="Deploiement souhaite",
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-cyan-600 border-slate-300 focus:ring-cyan-500",
            }
        ),
    )

    use_containers = forms.ChoiceField(
        required=True,
        initial="no",
        choices=YES_NO_CHOICES,
        label="Containers",
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-cyan-600 border-slate-300 focus:ring-cyan-500",
            }
        ),
    )

    command_shell = forms.ChoiceField(
        required=True,
        initial="bash",
        choices=SHELL_CHOICES,
        label="Shell des commandes",
        widget=forms.Select(
            attrs={
                "class": INPUT_CLASS,
            }
        ),
    )

    use_ssh = forms.ChoiceField(
        required=True,
        initial="no",
        choices=YES_NO_CHOICES,
        label="Execution distante SSH",
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-cyan-600 border-slate-300 focus:ring-cyan-500",
            }
        ),
    )

    repo_url = forms.CharField(
        required=False,
        label="URL repository",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "https://github.com/org/repo",
            }
        ),
    )

    deploy_branch = forms.CharField(
        required=False,
        initial="main",
        label="Branche cible",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "main",
                "list": "deploy-branch-options",
            }
        ),
    )

    env_variables = forms.CharField(
        required=False,
        label="Variables d'environnement (KEY=VALUE)",
        widget=forms.Textarea(
            attrs={
                "rows": 7,
                "class": (
                    "w-full rounded-xl border border-slate-300 p-3 font-mono text-sm "
                    "text-slate-800 bg-slate-50 focus:border-cyan-400 "
                    "focus:outline-none focus:ring-2 focus:ring-cyan-200"
                ),
                "placeholder": "DJANGO_SETTINGS_MODULE=config.settings\nDEBUG=False",
            }
        ),
    )

    ssh_host = forms.CharField(
        required=False,
        label="SSH host",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "srv.example.com",
            }
        ),
    )
    ssh_user = forms.CharField(
        required=False,
        label="SSH user",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "deploy",
            }
        ),
    )
    ssh_port = forms.CharField(
        required=False,
        initial="22",
        label="SSH port",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "22",
            }
        ),
    )
    ssh_key_variable = forms.CharField(
        required=False,
        label="Variable cle privee",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "SSH_PRIVATE_KEY",
            }
        ),
    )

    pre_deploy_commands = forms.CharField(
        required=False,
        label="Commandes pre-deploy",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": (
                    "w-full rounded-xl border border-slate-300 p-3 font-mono text-sm "
                    "text-slate-800 bg-slate-50 focus:border-cyan-400 "
                    "focus:outline-none focus:ring-2 focus:ring-cyan-200"
                ),
                "placeholder": "python -m pip install -r requirements.txt",
            }
        ),
    )
    deploy_commands = forms.CharField(
        required=False,
        label="Commandes deploy",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": (
                    "w-full rounded-xl border border-slate-300 p-3 font-mono text-sm "
                    "text-slate-800 bg-slate-50 focus:border-cyan-400 "
                    "focus:outline-none focus:ring-2 focus:ring-cyan-200"
                ),
                "placeholder": "docker compose up -d --build",
            }
        ),
    )
    post_deploy_commands = forms.CharField(
        required=False,
        label="Commandes post-deploy",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": (
                    "w-full rounded-xl border border-slate-300 p-3 font-mono text-sm "
                    "text-slate-800 bg-slate-50 focus:border-cyan-400 "
                    "focus:outline-none focus:ring-2 focus:ring-cyan-200"
                ),
                "placeholder": "python manage.py migrate",
            }
        ),
    )

    containers_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
