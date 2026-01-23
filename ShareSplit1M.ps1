<#
.SYNOPSIS
    Script de partage et publication SmartContractDevPipeline
.DESCRIPTION
    Partage les fichiers de pipeline de développement Smart Contract sur GitHub (Repository et Gists)
.NOTES
    Version: 1.0
    Auteur: SmartContractDevPipeline
#>

# Configuration par défaut
$defaultConfig = @{
    GITHUB_USERNAME = ""
    GITHUB_REPO_NAME = "SmartContractDevPipeline"
    GITHUB_TOKEN = ""
}

# Couleurs pour l'affichage
$colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
}

# ==================== FONCTIONS UTILITAIRES ====================

function Show-Menu {
    Clear-Host
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "SHARE SPLIT 1M - SmartContractDevPipeline" -ForegroundColor White
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=== MENU PRINCIPAL ===" -ForegroundColor Cyan
    Write-Host "1. Publier sur GitHub Repository" -ForegroundColor White
    Write-Host "2. Partager sur GitHub Gists" -ForegroundColor White
    Write-Host "3. Générer seulement les fichiers locaux" -ForegroundColor White
    Write-Host "4. Quitter" -ForegroundColor White
    Write-Host ""
}

function Read-ValidatedInput {
    param(
        [string]$Prompt,
        [string]$DefaultValue = "",
        [switch]$Required
    )
    
    while ($true) {
        if ($DefaultValue) {
            $inputText = Read-Host "$Prompt [$DefaultValue]"
            if ([string]::IsNullOrWhiteSpace($inputText)) {
                $inputText = $DefaultValue
            }
        } else {
            $inputText = Read-Host $Prompt
        }
        
        if (-not $Required -or (-not [string]::IsNullOrWhiteSpace($inputText))) {
            return $inputText
        } else {
            Write-Host "Ce champ est requis. Veuillez entrer une valeur." -ForegroundColor Red
        }
    }
}

function Test-GitHubToken {
    param([string]$Token, [string]$Username)
    
    Write-Host "Vérification du token GitHub..." -NoNewline
    
    try {
        $headers = @{
            "Authorization" = "token $Token"
            "Accept" = "application/vnd.github.v3+json"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method Get
        
        if ($response.login -eq $Username) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "   Connecté en tant que: $($response.login)" -ForegroundColor Green
            Write-Host "   Nom: $($response.name)" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ✗" -ForegroundColor Red
            Write-Host "   Le token ne correspond pas à l'utilisateur $Username" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "   Erreur: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Get-FilesToShare {
    $files = @()
    
    # Fichiers principaux
    $mainFiles = @(
        "ShareSplit1M.ps1",
        "smart-contract-dev-pipeline.sh",
        "automated-deployment.ps1",
        "security-audit-checklist.md",
        "gas-optimization-guide.md",
        "README.md"
    )
    
    foreach ($file in $mainFiles) {
        if (Test-Path $file) {
            $files += $file
        }
    }
    
    # Dossiers supplémentaires
    $folders = @("scripts", "templates", "configs")
    foreach ($folder in $folders) {
        if (Test-Path $folder -PathType Container) {
            $folderFiles = Get-ChildItem -Path $folder -File -Recurse | Where-Object { $_.Extension -in ".ps1", ".sh", ".md", ".yml", ".yaml", ".json", ".sol", ".js", ".ts" }
            foreach ($file in $folderFiles) {
                $files += $file.FullName
            }
        }
    }
    
    return $files
}

function Create-ZipArchive {
    param([array]$Files, [string]$OutputPath)
    
    Write-Host "Création de l'archive ZIP..." -NoNewline
    
    try {
        Compress-Archive -Path $Files -DestinationPath $OutputPath -Force
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "   Archive créée: $OutputPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "   Erreur: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ==================== FONCTIONS GITHUB ====================

function Publish-Repository {
    param([hashtable]$config)
    
    Write-Host "`n=== PUBLICATION SUR GITHUB REPOSITORY ===" -ForegroundColor Cyan
    Write-Host "Vérification du répertoire..." -NoNewline
    
    # Vérifier le répertoire courant
    if (-not (Test-Path -Path ".git")) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Erreur: Ce répertoire n'est pas un dépôt Git." -ForegroundColor Red
        Write-Host "   Exécutez ce script depuis le répertoire de votre projet Git." -ForegroundColor Yellow
        return $false
    }
    Write-Host " ✓" -ForegroundColor Green
    
    Write-Host "Nettoyage Git..." -NoNewline
    git clean -fd 2>&1 | Out-Null
    git reset --hard 2>&1 | Out-Null
    Write-Host " ✓" -ForegroundColor Green
    
    Write-Host "Configuration Git..." -NoNewline
    git config user.name $config.GITHUB_USERNAME 2>&1 | Out-Null
    git config user.email "$($config.GITHUB_USERNAME)@users.noreply.github.com" 2>&1 | Out-Null
    Write-Host " ✓" -ForegroundColor Green
    
    Write-Host "Remote: https://github.com/$($config.GITHUB_USERNAME)/$($config.GITHUB_REPO_NAME)" -ForegroundColor Cyan
    $remoteUrl = "https://x-access-token:${newToken}@github.com/$($config.GITHUB_USERNAME)/$($config.GITHUB_REPO_NAME).git"
    git remote remove origin 2>&1 | Out-Null
    git remote add origin $remoteUrl 2>&1 | Out-Null
    
    Write-Host "Ajout fichiers..." -NoNewline
    git add . 2>&1 | Out-Null
    Write-Host " ✓" -ForegroundColor Green
    
    Write-Host "Commit..." -NoNewline
    $commitResult = git commit -m "SmartContractDevPipeline - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        # Si pas de changements, créer un commit vide
        if ($commitResult -match "nothing to commit") {
            git commit --allow-empty -m "SmartContractDevPipeline - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
            Write-Host " (commit vide) ✓" -ForegroundColor Yellow
        } else {
            Write-Host " ✗" -ForegroundColor Red
            Write-Host "❌ Erreur: $commitResult" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "Branche..." -NoNewline
    git branch -M main 2>&1 | Out-Null
    Write-Host " ✓" -ForegroundColor Green
    
    # CORRECTION UNIQUE : Section push modifiée
    # Push vers GitHub
    Write-Host "Push vers GitHub..." -NoNewline
    
    # CORRECTION : Approche en deux étapes au lieu de --allow-unrelated-histories --force
    $pushResult = git push -u origin main 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        if ($pushResult -match "failed to push some refs" -or $pushResult -match "unrelated histories" -or $pushResult -match "non-fast-forward") {
            Write-Host " (tentative avec --force)..." -NoNewline -ForegroundColor Yellow
            $pushResult = git push -u origin main --force 2>&1
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Erreur: $pushResult" -ForegroundColor Red
        return $false
    }
    
    Write-Host "`n✅ Publication réussie sur GitHub !" -ForegroundColor Green
    Write-Host "📂 Repository: https://github.com/$($config.GITHUB_USERNAME)/$($config.GITHUB_REPO_NAME)" -ForegroundColor Cyan
    return $true
}

function Share-Gists {
    param([hashtable]$config)
    
    Write-Host "`n=== PARTAGE SUR GITHUB GISTS ===" -ForegroundColor Cyan
    
    $files = Get-FilesToShare
    
    if ($files.Count -eq 0) {
        Write-Host "❌ Aucun fichier à partager trouvé." -ForegroundColor Red
        return $false
    }
    
    Write-Host "Fichiers à partager ($($files.Count) trouvés):" -ForegroundColor White
    foreach ($file in $files) {
        Write-Host "  • $file" -ForegroundColor Gray
    }
    
    Write-Host "`nCréation des Gists..." -ForegroundColor Cyan
    
    $successCount = 0
    $failedCount = 0
    $gistLinks = @()
    
    foreach ($file in $files) {
        Write-Host "  $file..." -NoNewline
        
        try {
            $content = Get-Content -Path $file -Raw -Encoding UTF8
            $fileName = Split-Path $file -Leaf
            
            $body = @{
                description = "SmartContractDevPipeline - $fileName"
                public = $true
                files = @{
                    $fileName = @{ content = $content }
                }
            } | ConvertTo-Json
            
            $headers = @{
                "Authorization" = "token $($config.GITHUB_TOKEN)"
                "Accept" = "application/vnd.github.v3+json"
            }
            
            $response = Invoke-RestMethod `
                -Uri "https://api.github.com/gists" `
                -Headers $headers `
                -Method Post `
                -Body $body `
                -ContentType "application/json"
            
            $successCount++
            $gistLinks += "$fileName : $($response.html_url)"
            Write-Host " ✓" -ForegroundColor Green
        } catch {
            $failedCount++
            Write-Host " ✗" -ForegroundColor Red
            Write-Host "    Erreur: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n=== RÉSUMÉ GISTS ===" -ForegroundColor Cyan
    Write-Host "Gists créés avec succès: $successCount" -ForegroundColor Green
    Write-Host "Gists échoués: $failedCount" -ForegroundColor $(if ($failedCount -gt 0) { "Red" } else { "Green" })
    
    if ($gistLinks.Count -gt 0) {
        Write-Host "`n📋 Liens des Gists:" -ForegroundColor Cyan
        foreach ($link in $gistLinks) {
            Write-Host "  • $link" -ForegroundColor White
        }
    }
    
    return $true
}

function Generate-LocalFiles {
    param([hashtable]$config)
    
    Write-Host "`n=== GÉNÉRATION DE FICHIERS LOCAUX ===" -ForegroundColor Cyan
    
    $files = Get-FilesToShare
    
    if ($files.Count -eq 0) {
        Write-Host "❌ Aucun fichier trouvé à partager." -ForegroundColor Red
        return $false
    }
    
    Write-Host "Fichiers trouvés ($($files.Count)):" -ForegroundColor White
    foreach ($file in $files) {
        Write-Host "  • $file" -ForegroundColor Gray
    }
    
    # Créer un dossier pour les fichiers partagés
    $shareDir = "SmartContractDevPipeline_Share_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $shareDir -Force | Out-Null
    
    Write-Host "`nCopie des fichiers dans: $shareDir" -NoNewline
    
    foreach ($file in $files) {
        $destFile = Join-Path $shareDir (Split-Path $file -Leaf)
        Copy-Item -Path $file -Destination $destFile -Force
    }
    
    Write-Host " ✓" -ForegroundColor Green
    
    # Créer une archive ZIP
    $zipPath = "$shareDir.zip"
    if (Create-ZipArchive -Files (Get-ChildItem -Path $shareDir -File).FullName -OutputPath $zipPath) {
        Write-Host "`n✅ Fichiers générés avec succès !" -ForegroundColor Green
        Write-Host "📁 Dossier: $shareDir" -ForegroundColor Cyan
        Write-Host "📦 Archive: $zipPath" -ForegroundColor Cyan
    }
    
    return $true
}

function Test-GitPush {
    param([hashtable]$config, [string]$newToken)
    
    Write-Host "Test Git push..." -NoNewline
    $testDir = "test_push_$(Get-Date -Format 'HHmmss')"
    New-Item -ItemType Directory -Path $testDir -Force | Out-Null
    Set-Location $testDir
    
    git init
    git config user.name "$($config.GITHUB_USERNAME)"
    git config user.email "$($config.GITHUB_USERNAME)@users.noreply.github.com"
    
    # Créer un fichier test
    "Test file" | Out-File -FilePath "test.txt" -Encoding UTF8
    
    git add .
    git commit -m "Test" --quiet
    
    # IMPORTANT: Créer la branche main avant de pousser
    git branch -M main
    
    # Essayer avec x-access-token
    $remoteUrl = "https://x-access-token:${newToken}@github.com/$($config.GITHUB_USERNAME)/$($config.GITHUB_REPO_NAME).git"
    git remote add origin $remoteUrl
    
    # CORRECTION : Approche en deux étapes
    Write-Host "  Tentative de push..." -NoNewline
    $pushOutput = git push -u origin main 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        if ($pushOutput -match "failed to push some refs" -or $pushOutput -match "unrelated histories") {
            Write-Host " échoué, tentative avec --force..." -NoNewline -ForegroundColor Yellow
            $pushOutput = git push -u origin main --force 2>&1
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Git push OK!" -ForegroundColor Green
    } else {
        Write-Host " ✗ Git push échoué" -ForegroundColor Red
        # Afficher l'erreur pour diagnostiquer
        Write-Host "Erreur: $pushOutput" -ForegroundColor Red

        # Vérifier si c'est un problème de branche
        if ($pushOutput -match "src refspec main does not match any") {
            Write-Host "ASTUCE: La branche 'main' n'existe pas localement" -ForegroundColor Yellow
        }
    }
    
    # Nettoyer
    Set-Location ..
    Remove-Item $testDir -Recurse -Force -ErrorAction SilentlyContinue
}

# ==================== PROGRAMME PRINCIPAL ====================

# Point d'entrée
Clear-Host
Write-Host "SHARE SPLIT 1M - SmartContractDevPipeline" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration
$config = $defaultConfig.Clone()

Write-Host "`n=== CONFIGURATION GITHUB ===" -ForegroundColor Cyan

$config.GITHUB_USERNAME = Read-ValidatedInput -Prompt "Nom d'utilisateur GitHub" -Required
$config.GITHUB_REPO_NAME = Read-ValidatedInput -Prompt "Nom du repository GitHub" -DefaultValue "SmartContractDevPipeline"
$config.GITHUB_TOKEN = Read-ValidatedInput -Prompt "Token GitHub (classic, avec permissions repo et gist)" -Required -MaskInput

Write-Host "`nConfiguration enregistrée:" -ForegroundColor Cyan
Write-Host "  Utilisateur: $($config.GITHUB_USERNAME)" -ForegroundColor White
Write-Host "  Repository: $($config.GITHUB_REPO_NAME)" -ForegroundColor White
Write-Host "  Token: ******" -ForegroundColor White

# Test du token
if (-not (Test-GitHubToken -Token $config.GITHUB_TOKEN -Username $config.GITHUB_USERNAME)) {
    Write-Host "`n❌ Le token GitHub est invalide." -ForegroundColor Red
    Write-Host "Veuillez vérifier votre token et réessayer." -ForegroundColor Yellow
    Read-Host "`nAppuyez sur Entrée pour quitter"
    exit 1
}

# Initialiser la variable newToken (utilisée dans Publish-Repository)
$newToken = $config.GITHUB_TOKEN

# Test Git push
Test-GitPush -config $config -newToken $newToken

# Menu principal
do {
    Show-Menu
    $choice = Read-Host "Votre choix [1-4]"
    
    switch ($choice) {
        "1" {
            # Publication sur GitHub Repository
            Publish-Repository -config $config
            Read-Host "`nAppuyez sur Entrée pour continuer..."
        }
        "2" {
            # Partage sur GitHub Gists
            Share-Gists -config $config
            Read-Host "`nAppuyez sur Entrée pour continuer..."
        }
        "3" {
            # Génération de fichiers locaux
            Generate-LocalFiles -config $config
            Read-Host "`nAppuyez sur Entrée pour continuer..."
        }
        "4" {
            Write-Host "`nAu revoir !" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "Choix invalide. Veuillez sélectionner une option entre 1 et 4." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
} while ($true)