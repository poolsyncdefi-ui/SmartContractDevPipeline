# ===============================
# CONFIGURATION GÉNÉRALE
# ===============================
$Script:ScriptName = "Partage de fichiers"
$Script:Version = "1.0.0"
$Script:CurrentUser = $env:USERNAME
$Script:ConfigFile = "..\project_config.json"
$Script:OutputDir = [Environment]::GetFolderPath("Desktop")

# ===============================
# FONCTIONS UTILITAIRES
# ===============================
function Show-Banner {
    Clear-Host
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "          $ScriptName v$Version" -ForegroundColor Yellow
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "Utilisateur : $Script:CurrentUser" -ForegroundColor Gray
    Write-Host "Date : $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
}

# ===============================
# CONFIGURATION DU SCRIPT
# ===============================
function Initialize-Configuration {
    if (-not (Test-Path $Script:ConfigFile)) {
        Write-Host "Configuration non trouvée : $Script:ConfigFile" -ForegroundColor Red
        Write-Host "Veuillez créer le fichier project_config.json avec la structure suivante :" -ForegroundColor Yellow
        Write-Host @"
{
    "PROJECT_NAME": "SmartContractPipeline",
    "PROJECT_PATH": "D:\\Web3Projects\\SmartContractPipeline",
    "GITHUB_USERNAME": "poolsyncdefi-ui",
    "GITHUB_TOKEN": "ghp_*********",
    "GITHUB_REPO_NAME": "SmartContractPipeline",
    "GITHUB_REPO_DESCRIPTION": "Pipeline de déploiement de Smart Contracts pour PoolSync DeFi",
    "GITHUB_REPO_PRIVATE": false
}
"@ -ForegroundColor Gray
        exit 1
    }
    
    try {
        $configContent = Get-Content $Script:ConfigFile -Raw
        $Script:Config = $configContent | ConvertFrom-Json
        Write-Host "Configuration chargée : $($Script:Config.PROJECT_NAME)" -ForegroundColor Green
        return $Script:Config
    } catch {
        Write-Host "Erreur de lecture de la configuration : $_" -ForegroundColor Red
        exit 1
    }
}

# ===============================
# OPTION 1 : ANALYSE ET SPLIT DES FICHIERS
# ===============================
function Analyze-And-Split-Files {
    Show-Banner
    
    Write-Host "📊 ANALYSE ET SPLIT DES FICHIERS (>1MB)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $directory = $Script:Config.PROJECT_PATH
    if (-not (Test-Path $directory)) {
        Write-Host "Le répertoire n'existe pas : $directory" -ForegroundColor Red
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Nettoyer les anciens fichiers
    Write-Host "🧹 Nettoyage des anciens fichiers..." -ForegroundColor Gray
    Get-ChildItem -Path $Script:OutputDir -Filter "PROJECT_SHARE_PART_*.txt" -File | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $Script:OutputDir -Filter "PROJECT_SHARE_INDEX.txt" -File | Remove-Item -Force -ErrorAction SilentlyContinue
    
    # Rechercher le plus gros fichier > 1MB
    Write-Host "🔍 Recherche des fichiers >1MB..." -ForegroundColor Gray
    
    $allFiles = Get-ChildItem -Path $directory -File -Recurse -ErrorAction SilentlyContinue
    
    if ($allFiles.Count -eq 0) {
        Write-Host "Aucun fichier trouvé dans le répertoire." -ForegroundColor Yellow
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Filtrer les fichiers > 1MB
    $largeFiles = $allFiles | Where-Object { $_.Length -gt 1MB }
    
    if ($largeFiles.Count -eq 0) {
        Write-Host "Aucun fichier de plus de 1MB trouvé." -ForegroundColor Yellow
        
        # Afficher les 5 plus gros fichiers quand même
        Write-Host "`n📁 Les 5 plus gros fichiers trouvés :" -ForegroundColor White
        $topFiles = $allFiles | Sort-Object Length -Descending | Select-Object -First 5
        $counter = 1
        foreach ($file in $topFiles) {
            $sizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Host "$counter. $($file.Name) ($sizeMB MB)" -ForegroundColor Gray
            $counter++
        }
        
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Prendre le plus gros fichier
    $largestFile = $largeFiles | Sort-Object Length -Descending | Select-Object -First 1
    
    Write-Host "`n✅ FICHIER TROUVÉ :" -ForegroundColor Green
    Write-Host "   Nom : $($largestFile.Name)" -ForegroundColor White
    Write-Host "   Taille : $([math]::Round($largestFile.Length / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "   Chemin : $($largestFile.FullName)" -ForegroundColor Gray
    
    Write-Host "`n🔪 Split du fichier en cours..." -ForegroundColor Cyan
    
    # Appeler la fonction de split
    $success = Split-File-Intelligently -FilePath $largestFile.FullName
    
    if ($success) {
        Write-Host "`n🎉 OPÉRATION RÉUSSIE !" -ForegroundColor Green
        
        # Vérifier et afficher les fichiers créés
        $createdFiles = Get-ChildItem -Path $Script:OutputDir -Filter "PROJECT_SHARE_*.txt" -File
        
        if ($createdFiles.Count -gt 0) {
            Write-Host "📁 Fichiers créés sur le Bureau :" -ForegroundColor White
            
            foreach ($file in $createdFiles) {
                $sizeKB = [math]::Round($file.Length / 1KB, 2)
                if ($file.Name -eq "PROJECT_SHARE_INDEX.txt") {
                    Write-Host "   📋 $($file.Name) ($sizeKB KB)" -ForegroundColor Cyan
                } else {
                    Write-Host "   📄 $($file.Name) ($sizeKB KB)" -ForegroundColor White
                }
            }
            
            Write-Host "`n📍 Emplacement : $Script:OutputDir" -ForegroundColor Gray
            
            # Demander si on veut voir les fichiers
            $showFiles = Read-Host "`nVoulez-vous ouvrir l'explorateur pour voir les fichiers ? (O/N)"
            if ($showFiles -eq "O" -or $showFiles -eq "o") {
                Start-Process "explorer.exe" -ArgumentList $Script:OutputDir
            }
        } else {
            Write-Host "❌ Aucun fichier n'a été créé sur le Bureau" -ForegroundColor Red
        }
    } else {
        Write-Host "`n❌ ÉCHEC DE L'OPÉRATION" -ForegroundColor Red
    }
    
    Read-Host "`nAppuyez sur Entrée pour continuer"
}

function Split-File-Intelligently {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    
    try {
        $fileInfo = Get-Item $FilePath
        $fileName = $fileInfo.Name
        $fileSize = $fileInfo.Length
        
        Write-Host "   📄 Fichier : $fileName" -ForegroundColor White
        Write-Host "   📊 Taille : $([math]::Round($fileSize / 1MB, 2)) MB" -ForegroundColor White
        
        # Limite de 1MB par partie
        $maxChunkSize = 1MB
        
        # Calculer le nombre de parties
        $numParts = [math]::Ceiling($fileSize / $maxChunkSize)
        Write-Host "   🔢 Parties nécessaires : $numParts" -ForegroundColor White
        
        # Lire le fichier en binaire
        Write-Host "   📖 Lecture du fichier..." -ForegroundColor Gray
        $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
        $totalBytes = $fileBytes.Length
        
        $createdFiles = @()
        
        Write-Host "   ✂️  Division en cours..." -ForegroundColor Gray
        
        for ($i = 1; $i -le $numParts; $i++) {
            $startIndex = ($i - 1) * $maxChunkSize
            $endIndex = [math]::Min($startIndex + $maxChunkSize, $totalBytes)
            $chunkSize = $endIndex - $startIndex
            
            if ($chunkSize -le 0) {
                continue
            }
            
            # Extraire le chunk
            $chunkBytes = New-Object byte[] $chunkSize
            [Array]::Copy($fileBytes, $startIndex, $chunkBytes, 0, $chunkSize)
            
            # Nom du fichier
            $outputFileName = "PROJECT_SHARE_PART_$i.txt"
            $outputPath = Join-Path $Script:OutputDir $outputFileName
            
            # Écrire le chunk
            [System.IO.File]::WriteAllBytes($outputPath, $chunkBytes)
            
            if (Test-Path $outputPath) {
                $fileSizeKB = [math]::Round((Get-Item $outputPath).Length / 1KB, 2)
                Write-Host "      ✅ Partie $i/$numParts : $outputFileName ($fileSizeKB KB)" -ForegroundColor Green
                $createdFiles += $outputPath
            }
            
            # Progression
            $percent = [math]::Round(($i / $numParts) * 100)
            Write-Progress -Activity "Division du fichier" -Status "$percent% complété" -PercentComplete $percent
        }
        
        Write-Progress -Activity "Division du fichier" -Completed
        
        # Créer le fichier d'index
        if ($createdFiles.Count -gt 0) {
            $indexFile = Create-Index-File -OriginalFile $fileInfo -NumParts $numParts -CreatedFiles $createdFiles
            if ($indexFile) {
                $createdFiles += $indexFile
                Write-Host "   📋 Fichier d'index créé" -ForegroundColor Cyan
            }
            
            Write-Host "   ✅ Division terminée" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ❌ Aucun fichier créé" -ForegroundColor Red
            return $false
        }
        
    } catch {
        Write-Host "   ❌ Erreur : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Create-Index-File {
    param(
        [System.IO.FileInfo]$OriginalFile,
        [int]$NumParts,
        [array]$CreatedFiles
    )
    
    try {
        $indexFileName = "PROJECT_SHARE_INDEX.txt"
        $indexPath = Join-Path $Script:OutputDir $indexFileName
        
        $indexContent = @"
PROJECT SHARE INDEX FILE
========================
Date : $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')
Projet : $($Script:Config.PROJECT_NAME)

Fichier original : $($OriginalFile.Name)
Taille originale : $([math]::Round($OriginalFile.Length / 1MB, 2)) MB
Nombre de parties : $NumParts

Liste des fichiers :
===================
"@
        
        # Ajouter la liste des fichiers
        for ($i = 1; $i -le $NumParts; $i++) {
            $partFile = Join-Path $Script:OutputDir "PROJECT_SHARE_PART_$i.txt"
            if (Test-Path $partFile) {
                $size = (Get-Item $partFile).Length
                $sizeKB = [math]::Round($size / 1KB, 2)
                $indexContent += "PROJECT_SHARE_PART_$i.txt ($sizeKB KB)`n"
            }
        }
        
        $indexContent += @"

Instructions :
=============
Ces fichiers ont été créés sur le Bureau.
Ils peuvent être partagés via GitHub Gist (Option 2).

Projet : $($Script:Config.PROJECT_NAME)
"@
        
        # Écrire le fichier d'index
        Set-Content -Path $indexPath -Value $indexContent -Encoding UTF8 -Force
        
        if (Test-Path $indexPath) {
            return Get-Item $indexPath
        }
        
        return $null
        
    } catch {
        Write-Host "   ❌ Erreur création index : $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ===============================
# OPTION 2 : PARTAGE GITHUB GIST
# ===============================
function Share-WithGitHubGist {
    Show-Banner
    
    Write-Host "📤 PARTAGE GITHUB GIST" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    
    # Vérifier le token GitHub
    if ([string]::IsNullOrEmpty($Script:Config.GITHUB_TOKEN) -or 
        $Script:Config.GITHUB_TOKEN -like "*\*\*\*") {
        Write-Host "❌ Token GitHub non configuré !" -ForegroundColor Red
        Write-Host "Veuillez configurer votre token dans project_config.json" -ForegroundColor Yellow
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Chercher les fichiers sur le Bureau
    $partFiles = Get-ChildItem -Path $Script:OutputDir -Filter "PROJECT_SHARE_PART_*.txt" -File | Sort-Object Name
    $indexFile = Get-ChildItem -Path $Script:OutputDir -Filter "PROJECT_SHARE_INDEX.txt" -File | Select-Object -First 1
    
    if ($partFiles.Count -eq 0) {
        Write-Host "❌ Aucun fichier PROJECT_SHARE_PART_*.txt trouvé sur le Bureau" -ForegroundColor Red
        Write-Host "   Exécutez d'abord l'Option 1 pour générer les fichiers" -ForegroundColor Yellow
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Préparer tous les fichiers
    $filesToShare = @($partFiles)
    if ($indexFile) {
        $filesToShare += $indexFile
    }
    
    Write-Host "📁 FICHIERS À PARTAGER : $($filesToShare.Count) fichiers" -ForegroundColor White
    
    $totalSize = 0
    foreach ($file in $filesToShare) {
        $sizeKB = [math]::Round($file.Length / 1KB, 2)
        $totalSize += $file.Length
        if ($file.Name -eq "PROJECT_SHARE_INDEX.txt") {
            Write-Host "   📋 $($file.Name) ($sizeKB KB)" -ForegroundColor Cyan
        } else {
            Write-Host "   📄 $($file.Name) ($sizeKB KB)" -ForegroundColor White
        }
    }
    
    $totalSizeMB = $totalSize / 1MB
    Write-Host "   📊 Taille totale : $($totalSizeMB.ToString('0.00')) MB" -ForegroundColor Gray
    
    if ($totalSizeMB > 10) {
        Write-Host "`n❌ Taille totale trop grande : $($totalSizeMB.ToString('0.00')) MB" -ForegroundColor Red
        Write-Host "   Limite GitHub Gist : 10 MB" -ForegroundColor Yellow
        Read-Host "`nAppuyez sur Entrée pour continuer"
        return
    }
    
    # Créer le Gist
    Write-Host "`n📤 Envoi vers GitHub Gist..." -ForegroundColor Cyan
    
    try {
        $filesObject = @{}
        
        foreach ($file in $filesToShare) {
            $fileName = $file.Name
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            $filesObject[$fileName] = @{ content = $content }
        }
        
        $body = @{
            description = "Fichiers partagés - $($Script:Config.PROJECT_NAME) - $(Get-Date -Format 'dd/MM/yyyy')"
            public = $false
            files = $filesObject
        } | ConvertTo-Json -Depth 5
        
        $headers = @{
            Authorization = "token $($Script:Config.GITHUB_TOKEN)"
            Accept = "application/vnd.github.v3+json"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.github.com/gists" `
                                      -Method POST `
                                      -Headers $headers `
                                      -Body $body `
                                      -ContentType "application/json"
        
        Write-Host "✅ GIST CRÉÉ AVEC SUCCÈS !" -ForegroundColor Green
        Write-Host "🔗 Lien : $($response.html_url)" -ForegroundColor White
        
        try {
            $response.html_url | Set-Clipboard -ErrorAction SilentlyContinue
            Write-Host "📋 Lien copié dans le presse-papiers" -ForegroundColor Green
        } catch {}
        
        $openLink = Read-Host "`nVoulez-vous ouvrir le Gist dans le navigateur ? (O/N)"
        if ($openLink -eq "O" -or $openLink -eq "o") {
            Start-Process $response.html_url
        }
        
    } catch {
        Write-Host "❌ Erreur : $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Read-Host "`nAppuyez sur Entrée pour continuer"
}

# ===============================
# OPTION 3 : GESTION GITHUB REPOSITORY
# ===============================
function Manage-GitHubRepo {
    Show-Banner
    
    Write-Host "🐙 GESTION GITHUB REPOSITORY" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    
    Write-Host "Repository : $($Script:Config.GITHUB_REPO_NAME)" -ForegroundColor White
    Write-Host "Description : $($Script:Config.GITHUB_REPO_DESCRIPTION)" -ForegroundColor Gray
    Write-Host "Private : $($Script:Config.GITHUB_REPO_PRIVATE)" -ForegroundColor Gray
    
    Write-Host "`n🔧 ACTIONS :" -ForegroundColor Cyan
    Write-Host "   1. Créer/Mettre à jour le repository" -ForegroundColor White
    Write-Host "   2. Synchroniser les fichiers" -ForegroundColor White
    Write-Host "   3. Voir les statistiques" -ForegroundColor White
    Write-Host "   4. Retour au menu" -ForegroundColor White
    
    $choice = Read-Host "`nVotre choix (1-4)"
    
    switch ($choice) {
        "1" {
            Write-Host "Création/Mise à jour du repository..." -ForegroundColor Yellow
        }
        "2" {
            Write-Host "Synchronisation des fichiers..." -ForegroundColor Yellow
        }
        "3" {
            Write-Host "Statistiques du repository..." -ForegroundColor Yellow
        }
        "4" {
            return
        }
        default {
            Write-Host "Choix invalide." -ForegroundColor Red
        }
    }
    
    Read-Host "`nAppuyez sur Entrée pour continuer"
}

# ===============================
# MENU PRINCIPAL
# ===============================
function Show-MainMenu {
    do {
        Show-Banner
        
        Write-Host "PROJET : $($Script:Config.PROJECT_NAME)" -ForegroundColor Green
        Write-Host "Chemin : $($Script:Config.PROJECT_PATH)" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "📋 MENU PRINCIPAL" -ForegroundColor Yellow
        Write-Host "   1. 📊 Analyse et split des fichiers (>1MB)" -ForegroundColor White
        Write-Host "   2. 📤 Partage GitHub Gist" -ForegroundColor White
        Write-Host "   3. 🐙 Gestion GitHub Repository" -ForegroundColor White
        Write-Host "   4. 🚪 Quitter" -ForegroundColor White
        
        $choice = Read-Host "`nVotre choix (1-4)"
        
        switch ($choice) {
            "1" { 
                Analyze-And-Split-Files 
            }
            "2" { 
                Share-WithGitHubGist 
            }
            "3" { 
                Manage-GitHubRepo 
            }
            "4" { 
                Write-Host "`nAu revoir !" -ForegroundColor Green
                Start-Sleep -Seconds 1
                break 
            }
            default { 
                Write-Host "Choix invalide." -ForegroundColor Red
                Start-Sleep -Seconds 2
            }
        }
    } while ($true)
}

# ===============================
# POINT D'ENTRÉE PRINCIPAL
# ===============================
function Main {
    # Initialisation
    Initialize-Configuration
    
    # Vérifier le token GitHub
    if ([string]::IsNullOrEmpty($Script:Config.GITHUB_TOKEN) -or 
        $Script:Config.GITHUB_TOKEN -like "*\*\*\*") {
        Write-Host "`n⚠️  ATTENTION : Token GitHub non configuré" -ForegroundColor Yellow
        Write-Host "Les fonctions GitHub ne seront pas disponibles." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    } else {
        Write-Host "GitHub Gist : Disponible ✓" -ForegroundColor Green
        Write-Host "GitHub Repository : Disponible ✓" -ForegroundColor Green
    }
    
    Start-Sleep -Seconds 1
    
    # Afficher le menu principal
    Show-MainMenu
}

# Point d'entrée
if ($MyInvocation.InvocationName -ne '.') {
    Main
}