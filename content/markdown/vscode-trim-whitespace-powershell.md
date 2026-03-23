# VS Code : supprimer les espaces en fin de ligne (PowerShell)

Petit script **Windows PowerShell** qui modifie le fichier **`settings.json`** de Visual Studio Code pour activer ou désactiver la suppression des **espaces orphelins en fin de ligne** (`files.trimTrailingWhitespace`).

---

## Comportement

1. Lit `settings.json` dans le profil utilisateur Code.
2. Demande si vous souhaitez **activer** la suppression des espaces en fin de ligne (**Y** / **N**).
3. Enregistre la valeur dans `settings.json` (UTF-8).
4. Propose éventuellement de **revenir à la valeur par défaut** (`false`).

---

## Prérequis

- Windows  
- [Visual Studio Code](https://code.visualstudio.com/) installé  
- PowerShell (console ou **Terminal intégré** VS Code)

> **Cursor** : le chemin peut être `Cursor\User\settings.json` sous `%APPDATA%` au lieu de `Code\User\settings.json`. Adaptez `$settingsPath` si besoin.

---

## Script

Enregistrez le bloc suivant dans un fichier, par exemple `Set-VsCodeTrimTrailingWhitespace.ps1`, puis exécutez-le dans PowerShell :

```powershell
# Chemin vers votre fichier settings.json de VS Code
$settingsPath = "$env:APPDATA\Code\User\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Host "Fichier introuvable : $settingsPath" -ForegroundColor Red
    exit 1
}

$jsonContent = Get-Content $settingsPath -Raw -Encoding UTF8

# Tableau associatif pour gérer proprement la clé "files.trimTrailingWhitespace"
$hash = [ordered]@{}
if (-not [string]::IsNullOrWhiteSpace($jsonContent)) {
    ($jsonContent | ConvertFrom-Json).PSObject.Properties | ForEach-Object {
        $hash[$_.Name] = $_.Value
    }
}

$borderLine = "-" * 50
Write-Host "+$borderLine+"
Write-Host "| Souhaitez-vous activer la suppression des espaces en fin de ligne ? (Y/N) |"
Write-Host "+$borderLine+"

$response = Read-Host "Votre choix"
if ($response -eq 'Y' -or $response -eq 'y') {
    $hash['files.trimTrailingWhitespace'] = $true
    Write-Host "La suppression des espaces en fin de ligne a été activée." -ForegroundColor Green
} else {
    $hash['files.trimTrailingWhitespace'] = $false
    Write-Host "Valeur définie à false (espaces non supprimés automatiquement)." -ForegroundColor Yellow
}

[pscustomobject]$hash | ConvertTo-Json -Depth 100 | Set-Content $settingsPath -Force -Encoding UTF8
Write-Host "Le fichier settings.json a été mis à jour."

Write-Host ""
Write-Host "+$borderLine+"
Write-Host "| Souhaitez-vous forcer la valeur par défaut (false) ? (Y/N) |"
Write-Host "+$borderLine+"
$restoreDefault = Read-Host "Votre choix"

if ($restoreDefault -eq 'Y' -or $restoreDefault -eq 'y') {
    $hash['files.trimTrailingWhitespace'] = $false
    [pscustomobject]$hash | ConvertTo-Json -Depth 100 | Set-Content $settingsPath -Force -Encoding UTF8
    Write-Host "Valeur restaurée à false. settings.json mis à jour." -ForegroundColor Cyan
} else {
    Write-Host "Aucune restauration supplémentaire." -ForegroundColor Gray
}
```

---

## Exécution

Dans PowerShell (en tant qu’utilisateur, pas obligatoirement administrateur) :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # une fois si les scripts sont bloqués
.\Set-VsCodeTrimTrailingWhitespace.ps1
```

---

## Équivalent dans settings.json

Après activation (**Y**), vous devriez voir (ou fusionner avec vos autres clés) :

```json
{
  "files.trimTrailingWhitespace": true
}
```

Quand c’est à **`false`**, VS Code ne supprime pas automatiquement les espaces en fin de ligne à l’enregistrement.

---

## Notes

- **`ConvertTo-Json`** peut réordonner les clés ; le fichier reste valide pour VS Code.  
- Si votre `settings.json` contient des **commentaires** (`//`), `ConvertFrom-Json` **échoue** : dans ce cas, éditez la clé à la main ou utilisez un fichier sans commentaires pour ce script.  
- Pour **Cursor**, remplacez le chemin par par exemple :  
  `"$env:APPDATA\Cursor\User\settings.json"`.
