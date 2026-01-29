# ShareSplit1M_Complete.ps1
# ============================================================================
# CONFIGURATION
# ============================================================================
# Lecture de la configuration
$configPath = ".\..\project_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $PROJECT_NAME = $config.PROJECT_NAME
    $PROJECT_PATH = $config.PROJECT_PATH
    $GITHUB_TOKEN = $config.GITHUB_TOKEN
    $GITHUB_USERNAME = $config.GITHUB_USERNAME
    $GITHUB_REPO_NAME = $config.GITHUB_REPO_NAME
    $GITHUB_REPO_PRIVATE = $config.GITHUB_REPO_PRIVATE
    $GITHUB_REPO_DESCRIPTION = $config.GITHUB_REPO_DESCRIPTION
} else {
    Write-Host "Fichier de configuration non trouvé." -ForegroundColor Red
    exit 1
}

# ============================================================================
# FONCTION POUR TROUVER LES FICHIERS SOURCES DU PROJET
# ============================================================================
function Get-SourceFiles {
    param(
        [string]$BasePath = "."
    )
    
    Write-Host "Recherche des fichiers sources du projet..." -NoNewline
    
    # Obtenir le chemin absolu du projet
    $projectRoot = Resolve-Path $BasePath
    
    # Définir les extensions de fichiers sources
    $sourceExtensions = @(
        '.ps1', '.psm1', '.psd1',         # PowerShell
        '.py',                            # Python
        '.js', '.jsx', '.ts', '.tsx',     # JavaScript/TypeScript
        '.vue', '.svelte',                # Frameworks JS
        '.html', '.htm', '.css', '.scss', '.sass', '.less', # Web
        '.json', '.xml', '.yaml', '.yml', '.toml', # Configurations
        '.md', '.txt', '.rst',            # Documentation
        '.cs', '.java', '.cpp', '.c', '.h', '.hpp', # Langages compilés
        '.go', '.rs', '.rb', '.php',      # Autres langages
        '.sql', '.psql',                  # Bases de données
        '.dockerfile',                    # Docker
        '.gitignore', '.gitattributes',   # Git
        '.env.example', '.env.sample',    # Environnement (exemples)
        '.config', '.ini', '.cfg',        # Configuration
        '.bat', '.cmd', '.sh', '.bash',   # Scripts shell
        '.csproj', '.sln', '.vcxproj'     # Projets Visual Studio
    )
    
    # Dossiers à exclure
    $excludeDirs = @(
        '.git',
        'node_modules',
        '.vscode',
        '.idea',
        '__pycache__',
        'bin',
        'obj',
        'Debug',
        'Release',
        'dist',
        'build',
        'out',
        'coverage',
        '.vs',
        '.cache',
        '.next',
        '.angular',
        '.nuget',
        '.sonarlint',
        '.svn',
        '.hg',
        'PROJECT_SHARE_*',
        'GISTS_INDEX_*',
        'GITHUB_PUBLISH_*'
    )
    
    # Fichiers à exclure
    $excludeFiles = @(
        'project_config.json',
        '.env',
        '.env.local',
        'desktop.ini',
        'Thumbs.db',
        '.DS_Store',
        '*.log',
        '*.tmp',
        '*.temp',
        '*.bak',
        '*.backup',
        '*.exe',
        '*.dll',
        '*.so',
        '*.dylib',
        'package-lock.json',
        'yarn.lock',
        'pnpm-lock.yaml'
    )
    
    # Rechercher tous les fichiers
    $allFiles = Get-ChildItem -Path $projectRoot -File -Recurse -ErrorAction SilentlyContinue
    
    # Filtrer les fichiers sources
    $sourceFiles = @()
    
    foreach ($file in $allFiles) {
        $filePath = $file.FullName
        $relativePath = $filePath.Substring($projectRoot.Path.Length + 1)
        $fileName = $file.Name
        $fileExt = [System.IO.Path]::GetExtension($fileName).ToLower()
        
        # Vérifier si le fichier est dans un dossier exclu
        $inExcludedDir = $false
        foreach ($excludeDir in $excludeDirs) {
            if ($relativePath -like "*\$excludeDir\*" -or $relativePath.StartsWith("$excludeDir\")) {
                $inExcludedDir = $true
                break
            }
        }
        
        if ($inExcludedDir) {
            continue
        }
        
        # Vérifier si le fichier est exclu par nom
        $isExcludedFile = $false
        foreach ($excludeFile in $excludeFiles) {
            if ($excludeFile.StartsWith('*.')) {
                if ($fileExt -eq $excludeFile.Substring(1)) {
                    $isExcludedFile = $true
                    break
                }
            } elseif ($fileName -eq $excludeFile) {
                $isExcludedFile = $true
                break
            }
        }
        
        if ($isExcludedFile) {
            continue
        }
        
        # Vérifier si c'est un fichier source (par extension)
        if ($sourceExtensions -contains $fileExt) {
            $sourceFiles += @{
                File = $file
                Path = $relativePath
                FullPath = $filePath
                Extension = $fileExt
            }
        }
    }
    
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "  Fichiers sources trouvés: $($sourceFiles.Count)" -ForegroundColor Green
    
    return $sourceFiles
}

# ============================================================================
# FONCTION POUR LIRE UN FICHIER AVEC NUMÉROS DE LIGNE (pour le fichier unique)
# ============================================================================
function Get-FileContentForSingleFile {
    param(
        [string]$FilePath,
        [string]$RelativePath
    )
    
    try {
        # Lire le contenu du fichier
        $content = Get-Content -Path $FilePath -Raw -Encoding UTF8 -ErrorAction Stop
        
        # Ajouter les numéros de ligne
        $lines = $content -split "`n"
        $numberedContent = ""
        
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $lineNum = $i + 1
            $numberedContent += "${lineNum}: $($lines[$i])`n"
        }
        
        return $numberedContent
        
    } catch {
        return "ERREUR: Impossible de lire le fichier $RelativePath`n$($_.Exception.Message)"
    }
}

# ============================================================================
# FONCTION POUR GÉNÉRER UN SEUL FICHIER LOCAL AVEC TOUS LES SOURCES
# ============================================================================
function Generate-LocalSingleFile {
    param(
        [string]$Description = ""
    )
    
    Write-Host "`n=== GÉNÉRATION D'UN FICHIER UNIQUE AVEC TOUS LES SOURCES ===" -ForegroundColor Cyan
    
    # S'assurer d'être dans le bon répertoire
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host "ERREUR: Vous devez être dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Exécutez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais répertoire" }
    }
    
    # Obtenir les fichiers sources
    $sourceFiles = Get-SourceFiles -BasePath $currentDir
    
    if ($sourceFiles.Count -eq 0) {
        Write-Host "❌ Aucun fichier source trouvé" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier source" }
    }
    
    # Utiliser la description du projet si aucune fournie
    if (-not $Description) {
        $Description = $GITHUB_REPO_DESCRIPTION
    }
    
    # Créer un seul fichier de sortie
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = "PROJECT_SOURCES_$timestamp.txt"
    
    Write-Host "Création du fichier unique: $outputFile" -ForegroundColor Green
    Write-Host "Lecture de $($sourceFiles.Count) fichiers sources..." -NoNewline
    
    # Créer le contenu du fichier unique
    $fileContent = "=" * 100 + "`n"
    $fileContent += "PROJET: $PROJECT_NAME`n"
    $fileContent += "DESCRIPTION: $Description`n"
    $fileContent += "DATE: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    $fileContent += "FICHIERS SOURCES: $($sourceFiles.Count)`n"
    $fileContent += "=" * 100 + "`n`n"
    
    $processedFiles = 0
    $totalLines = 0
    
    # Parcourir tous les fichiers sources
    foreach ($sourceFile in $sourceFiles | Sort-Object { $_.Path }) {
        $relativePath = $sourceFile.Path
        $fileName = $sourceFile.File.Name
        
        # Ajouter l'en-tête du fichier
        $fileContent += "=" * 80 + "`n"
        $fileContent += "FICHIER: $fileName`n"
        $fileContent += "CHEMIN: $relativePath`n"
        $fileContent += "TAILLE: $([math]::Round($sourceFile.File.Length/1024, 2)) KB`n"
        $fileContent += "=" * 80 + "`n`n"
        
        # Lire le contenu du fichier avec numéros de ligne
        $fileLines = Get-FileContentForSingleFile -FilePath $sourceFile.FullPath -RelativePath $relativePath
        
        # Compter les lignes
        $lineCount = ($fileLines -split "`n").Count
        $totalLines += $lineCount
        
        # Ajouter le contenu au fichier unique
        $fileContent += $fileLines
        $fileContent += "`n"  # Espace entre les fichiers
        
        $processedFiles++
        
        # Afficher la progression
        if ($processedFiles % 10 -eq 0) {
            Write-Host " ($processedFiles/$($sourceFiles.Count))..." -NoNewline
        }
    }
    
    # Ajouter les statistiques à la fin
    $fileContent += "`n" + "=" * 100 + "`n"
    $fileContent += "STATISTIQUES FINALES`n"
    $fileContent += "=" * 100 + "`n"
    $fileContent += "Fichiers traités: $processedFiles`n"
    $fileContent += "Lignes totales: $totalLines`n"
    $fileContent += "Date de génération: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    
    # Statistiques par extension
    $extStats = $sourceFiles | Group-Object Extension | Sort-Object Count -Descending
    $fileContent += "`nRÉPARTITION PAR EXTENSION:`n"
    foreach ($stat in $extStats) {
        $extName = if ($stat.Name) { $stat.Name } else { "(sans extension)" }
        $fileContent += "  - $extName: $($stat.Count) fichiers`n"
    }
    
    $fileContent += "=" * 100 + "`n"
    
    # Écrire le fichier unique
    $fileContent | Out-File $outputFile -Encoding UTF8
    
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "`n✅ FICHIER UNIQUE CRÉÉ AVEC SUCCÈS !" -ForegroundColor Green
    
    # Afficher les informations du fichier
    $fileInfo = Get-Item $outputFile
    $fileSize = if ($fileInfo.Length -lt 1024) { "$($fileInfo.Length) B" }
                elseif ($fileInfo.Length -lt 1048576) { "$([math]::Round($fileInfo.Length/1KB, 2)) KB" }
                else { "$([math]::Round($fileInfo.Length/1MB, 2)) MB" }
    
    Write-Host "📄 Fichier créé: $outputFile" -ForegroundColor Cyan
    Write-Host "📊 Taille: $fileSize" -ForegroundColor Gray
    Write-Host "📁 Fichiers sources inclus: $processedFiles" -ForegroundColor Gray
    Write-Host "📈 Lignes totales: $totalLines" -ForegroundColor Gray
    
    # Aperçu du contenu (premières 10 lignes)
    Write-Host "`n📋 APERÇU DU CONTENU (premières 10 lignes):" -ForegroundColor Yellow
    Get-Content $outputFile -TotalCount 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    if ($totalLines > 10) {
        Write-Host "  ... ($($totalLines - 10) lignes supplémentaires)" -ForegroundColor Gray
    }
    
    return @{
        success = $true
        output_file = $outputFile
        file_size = $fileInfo.Length
        file_size_human = $fileSize
        source_files = $sourceFiles
        files_count = $processedFiles
        total_lines = $totalLines
    }
}

# ============================================================================
# FONCTION POUR LIRE UN FICHIER AVEC NUMÉROS DE LIGNE (pour Gists)
# ============================================================================
function Get-FileContentWithLineNumbers {
    param(
        [string]$FilePath,
        [string]$RelativePath
    )
    
    try {
        # Lire le contenu du fichier
        $content = Get-Content -Path $FilePath -Raw -Encoding UTF8 -ErrorAction Stop
        
        # Ajouter les numéros de ligne
        $lines = $content -split "`n"
        $numberedContent = ""
        
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $lineNum = $i + 1
            $numberedContent += "${lineNum}: $($lines[$i])`n"
        }
        
        # Ajouter l'en-tête avec le chemin du fichier
        $header = "=" * 80 + "`n"
        $header += "FICHIER: $RelativePath`n"
        $header += "=" * 80 + "`n`n"
        
        return $header + $numberedContent
        
    } catch {
        return "ERREUR: Impossible de lire le fichier $RelativePath`n$($_.Exception.Message)"
    }
}

# ============================================================================
# FONCTION POUR CRÉER DES GISTS AVEC CONTENU DES FICHIERS
# ============================================================================
function Create-SourceGists {
    param(
        [string]$Token,
        [string]$Username,
        [string]$Description,
        [array]$SourceFiles
    )
    
    Write-Host "`n=== CRÉATION DES GISTS ===" -ForegroundColor Cyan
    
    if ($SourceFiles.Count -eq 0) {
        Write-Host "❌ Aucun fichier source à publier" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier source" }
    }
    
    # Trier les fichiers par taille (du plus gros au plus petit)
    $sortedFiles = $SourceFiles | Sort-Object { $_.File.Length } -Descending
    
    # Limite de taille par Gist : 1 Go
    $maxGistSize = 1GB
    
    Write-Host "Organisation des fichiers dans les Gists..." -NoNewline
    
    # Algorithme de bin packing
    $gistBuckets = @()
    
    foreach ($sourceFile in $sortedFiles) {
        $fileSize = $sourceFile.File.Length
        
        # Ajouter une estimation pour les numéros de ligne (environ 10% supplémentaire)
        $estimatedSize = [math]::Round($fileSize * 1.1)
        
        # Trouver un Gist existant où ce fichier peut rentrer
        $placed = $false
        for ($i = 0; $i -lt $gistBuckets.Count; $i++) {
            $currentBucketSize = $gistBuckets[$i].size
            if (($currentBucketSize + $estimatedSize) -le $maxGistSize) {
                $gistBuckets[$i].files += $sourceFile
                $gistBuckets[$i].size += $estimatedSize
                $placed = $true
                break
            }
        }
        
        # Si le fichier n'a pas pu être placé, créer un nouveau Gist
        if (-not $placed) {
            $gistBuckets += @{
                files = @($sourceFile)
                size = $estimatedSize
            }
        }
    }
    
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "  Nombre de Gists nécessaires: $($gistBuckets.Count)" -ForegroundColor Gray
    
    # Créer les Gists
    $createdGists = @()
    for ($i = 0; $i -lt $gistBuckets.Count; $i++) {
        $bucket = $gistBuckets[$i]
        $gistNumber = $i + 1
        
        Write-Host "Création Gist $gistNumber/$($gistBuckets.Count)..." -NoNewline
        $gistResult = Create-GistFromSourceFiles -Token $Token -Username $Username `
            -Description $Description -SourceFiles $bucket.files -GistNumber $gistNumber
        
        if ($gistResult.success) {
            Write-Host " ✓" -ForegroundColor Green
            $createdGists += $gistResult
        } else {
            Write-Host " ✗" -ForegroundColor Red
            Write-Host "  Erreur: $($gistResult.error)" -ForegroundColor Red
        }
    }
    
    # Filtrer les Gists réussis
    $successfulGists = $createdGists | Where-Object { $_.success }
    
    # Afficher les résultats
    if ($successfulGists.Count -gt 0) {
        Write-Host "`n✅ GISTS CRÉÉS AVEC SUCCÈS !" -ForegroundColor Green
        
        $gistUrls = @()
        $totalFiles = 0
        
        foreach ($gist in $successfulGists) {
            Write-Host "🔗 Gist $($gist.gist_number): $($gist.gist_url)" -ForegroundColor Cyan
            Write-Host "   Fichiers: $($gist.files_published)" -ForegroundColor Gray
            $gistUrls += $gist.gist_url
            $totalFiles += $gist.files_published
        }
        
        # Créer un fichier d'index avec tous les liens
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $indexFile = "GISTS_INDEX_$timestamp.txt"
        
        $indexContent = "=" * 80 + "`n"
        $indexContent += "INDEX DES GISTS - $PROJECT_NAME`n"
        $indexContent += "=" * 80 + "`n"
        $indexContent += "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
        $indexContent += "Projet: $PROJECT_NAME`n"
        $indexContent += "Description: $Description`n"
        $indexContent += "Total Gists: $($successfulGists.Count)`n"
        $indexContent += "Total fichiers sources: $totalFiles`n"
        $indexContent += "`n" + "=" * 80 + "`n"
        $indexContent += "LIENS DES GISTS:`n"
        $indexContent += "=" * 80 + "`n`n"
        
        foreach ($gist in $successfulGists) {
            $indexContent += "GIST #$($gist.gist_number):`n"
            $indexContent += "URL: $($gist.gist_url)`n"
            $indexContent += "Fichiers inclus ($($gist.files_published)):`n"
            
            foreach ($fileInfo in $gist.file_list) {
                $indexContent += "  - $($fileInfo.path)`n"
            }
            
            $indexContent += "`n"
        }
        
        $indexContent += "=" * 80 + "`n"
        $indexContent += "STATISTIQUES:`n"
        $indexContent += "=" * 80 + "`n"
        $indexContent += "- Fichiers sources totaux: $($SourceFiles.Count)`n"
        $indexContent += "- Gists créés: $($successfulGists.Count)`n"
        $indexContent += "- Fichiers publiés: $totalFiles`n"
        
        # Statistiques par extension
        $extStats = $SourceFiles | Group-Object Extension | Sort-Object Count -Descending
        $indexContent += "`nRépartition par extension:`n"
        foreach ($stat in $extStats) {
            $indexContent += "  - $($stat.Name): $($stat.Count) fichiers`n"
        }
        
        $indexContent += "=" * 80 + "`n"
        
        $indexContent | Out-File $indexFile -Encoding UTF8
        Write-Host "`n📄 Fichier d'index créé: $indexFile" -ForegroundColor Green
        
        return @{
            success = $true
            gist_urls = $gistUrls
            total_gists = $successfulGists.Count
            index_file = $indexFile
            total_files = $totalFiles
            gist_details = $successfulGists
        }
        
    } else {
        Write-Host "❌ Aucun Gist créé" -ForegroundColor Red
        return @{ success = $false; error = "Aucun Gist créé" }
    }
}

# ============================================================================
# FONCTION POUR CRÉER UN GIST À PARTIR DE FICHIERS SOURCES
# ============================================================================
function Create-GistFromSourceFiles {
    param(
        [string]$Token,
        [string]$Username,
        [string]$Description,
        [array]$SourceFiles,
        [int]$GistNumber
    )
    
    # Préparer les fichiers pour l'API GitHub
    $filesObject = @{}
    $fileList = @()
    
    foreach ($sourceFile in $SourceFiles) {
        $fileName = $sourceFile.File.Name
        $relativePath = $sourceFile.Path
        
        # Lire le contenu avec numéros de ligne
        $contentWithLines = Get-FileContentWithLineNumbers -FilePath $sourceFile.FullPath -RelativePath $relativePath
        
        # Créer un nom de fichier pour le Gist (incluant le chemin)
        $gistFileName = $relativePath -replace '[\\/]', '_'
        $gistFileName = $gistFileName -replace '[^\w\.\-]', '_'
        
        $filesObject[$gistFileName] = @{ content = $contentWithLines }
        $fileList += @{ name = $fileName; path = $relativePath; gist_name = $gistFileName }
    }
    
    if ($filesObject.Count -eq 0) {
        return @{ success = $false; error = "Aucun fichier à publier" }
    }
    
    # Description du Gist
    $gistDescription = "$Description - $PROJECT_NAME - Part $GistNumber ($($SourceFiles.Count) fichiers)"
    
    # Préparer le corps de la requête
    $body = @{
        description = $gistDescription
        public = $false
        files = $filesObject
    } | ConvertTo-Json -Depth 10
    
    try {
        $headers = @{
            "Authorization" = "token $Token"
            "Accept" = "application/vnd.github.v3+json"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.github.com/gists" `
            -Method Post `
            -Headers $headers `
            -Body $body `
            -TimeoutSec 30
        
        # Créer un fichier d'index local pour ce Gist
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $gistIndexFile = "GIST_${GistNumber}_${timestamp}.txt"
        
        $gistIndexContent = "=" * 80 + "`n"
        $gistIndexContent += "GIST #$GistNumber - $PROJECT_NAME`n"
        $gistIndexContent += "=" * 80 + "`n"
        $gistIndexContent += "URL: $($response.html_url)`n"
        $gistIndexContent += "ID: $($response.id)`n"
        $gistIndexContent += "Description: $gistDescription`n"
        $gistIndexContent += "Fichiers: $($SourceFiles.Count)`n"
        $gistIndexContent += "`n" + "=" * 80 + "`n"
        $gistIndexContent += "LISTE DES FICHIERS:`n"
        $gistIndexContent += "=" * 80 + "`n`n"
        
        foreach ($fileInfo in $fileList) {
            $gistIndexContent += "Fichier: $($fileInfo.path)`n"
            $gistIndexContent += "Nom dans Gist: $($fileInfo.gist_name)`n"
            $gistIndexContent += "-" * 40 + "`n"
        }
        
        $gistIndexContent | Out-File $gistIndexFile -Encoding UTF8
        
        return @{
            success = $true
            gist_url = $response.html_url
            gist_id = $response.id
            files_published = $SourceFiles.Count
            gist_number = $GistNumber
            file_list = $fileList
            index_file = $gistIndexFile
        }
        
    } catch {
        $errorMsg = "Erreur API GitHub"
        if ($_.Exception.Response) {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            
            try {
                $errorDetails = $responseBody | ConvertFrom-Json
                $errorMsg = "GitHub: $($errorDetails.message)"
            } catch {
                $errorMsg = "Erreur HTTP: $($_.Exception.Message)"
            }
        }
        
        return @{
            success = $false
            error = $errorMsg
            gist_number = $GistNumber
        }
    }
}

# ============================================================================
# FONCTION POUR PUBLIER SUR GITHUB REPOSITORY
# ============================================================================
function Publish-ToGitHubRepo {
    param(
        [string]$Token,
        [string]$Username,
        [string]$RepoName,
        [string]$Description,
        [bool]$IsPrivate
    )
    
    Write-Host "`n=== PUBLICATION SUR GITHUB REPOSITORY ===" -ForegroundColor Cyan
    
    # Vérifier que nous sommes dans le bon répertoire
    Write-Host "Vérification du répertoire..." -NoNewline
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "ERREUR: Vous devez être dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Actuel: $currentDir" -ForegroundColor Yellow
        Write-Host "Projet: $projectDir" -ForegroundColor Yellow
        Write-Host "Exécutez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais répertoire" }
    }
    Write-Host " ✓" -ForegroundColor Green
    
    # Vérifier le token
    if ([string]::IsNullOrWhiteSpace($Token) -or $Token -notmatch "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "❌ Token invalide ou manquant" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub invalide" }
    }
    
    # Vérifier que Git est installé
    try {
        git --version | Out-Null
    } catch {
        Write-Host "❌ Git non installé" -ForegroundColor Red
        return @{ success = $false; error = "Git non installé" }
    }
    
    # Obtenir les fichiers sources
    $sourceFiles = Get-SourceFiles -BasePath $currentDir
    if ($sourceFiles.Count -eq 0) {
        Write-Host "❌ Aucun fichier source trouvé" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier source" }
    }
    
    Write-Host "Fichiers à publier: $($sourceFiles.Count)" -ForegroundColor Gray
    
    # Nettoyer la configuration Git
    Write-Host "Nettoyage Git..." -NoNewline
    git config --global --unset credential.helper 2>$null
    git config --global credential.helper "" 2>$null
    Write-Host " ✓" -ForegroundColor Green
    
    try {
        # Initialiser Git si nécessaire
        if (-not (Test-Path ".git")) {
            Write-Host "Initialisation Git..." -NoNewline
            git init
            Write-Host " ✓" -ForegroundColor Green
        } else {
            Write-Host "✓ Git déjà initialisé" -ForegroundColor Gray
        }
        
        # Configurer Git
        Write-Host "Configuration Git..." -NoNewline
        git config user.name "$Username"
        git config user.email "$Username@users.noreply.github.com"
        Write-Host " ✓" -ForegroundColor Green
        
        # Créer .gitignore si nécessaire
        if (-not (Test-Path ".gitignore")) {
            $gitignoreContent = @"
# Fichiers générés
PROJECT_SHARE_*
GISTS_INDEX_*
GITHUB_PUBLISH_*

# Fichiers sensibles
project_config.json
.env
.env.local

# Dossiers système
node_modules/
.vscode/
.idea/
__pycache__/
bin/
obj/
dist/
build/
out/
coverage/
"@
            $gitignoreContent | Out-File ".gitignore" -Encoding UTF8
        }
        
        # Préparer l'URL avec le token
        $remoteUrl = "https://x-access-token:${Token}@github.com/${Username}/${RepoName}.git"
        Write-Host "Remote: https://github.com/${Username}/${RepoName}" -ForegroundColor Gray
        
        # Gérer le remote
        git remote remove origin 2>$null
        git remote add origin $remoteUrl
        
        # Ajouter tous les fichiers
        Write-Host "Ajout fichiers..." -NoNewline
        git add .
        Write-Host " ✓" -ForegroundColor Green
        
        # Commit
        Write-Host "Commit..." -NoNewline
        $commitMsg = "$Description - $PROJECT_NAME - Publication: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMsg --quiet
        Write-Host " ✓" -ForegroundColor Green
        
        # Créer la branche main
        Write-Host "Branche..." -NoNewline
        git branch -M main
        Write-Host " ✓" -ForegroundColor Green
        
        # Push vers GitHub
        Write-Host "Push vers GitHub..." -NoNewline
        $env:GIT_TERMINAL_PROMPT = "0"
        
        $pushOutput = git push -u origin main 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            if ($pushOutput -match "failed to push some refs" -or $pushOutput -match "unrelated histories" -or $pushOutput -match "non-fast-forward") {
                Write-Host " (tentative avec --force)..." -NoNewline -ForegroundColor Yellow
                $pushOutput = git push -u origin main --force 2>&1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "✅ PUBLICATION RÉUSSIE !" -ForegroundColor Green
            Write-Host "🔗 https://github.com/$Username/$RepoName" -ForegroundColor Cyan
            
            # Créer un fichier d'index local
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $indexFile = "GITHUB_PUBLISH_$timestamp.txt"
            
            $indexContent = @"
==========================================
GITHUB REPOSITORY PUBLICATION
==========================================
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Projet: $PROJECT_NAME
Repository: https://github.com/$Username/$RepoName
Description: $Description
Fichiers publiés: $($sourceFiles.Count)

DÉTAILS:
- Description: $Description - $PROJECT_NAME
- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Nombre de fichiers: $($sourceFiles.Count)
==========================================
"@
            
            $indexContent | Out-File $indexFile -Encoding UTF8
            Write-Host "📄 Fichier créé: $indexFile" -ForegroundColor Green
            
            return @{
                success = $true
                repo_url = "https://github.com/$Username/$RepoName"
                index_file = $indexFile
                message = "Publication réussie"
                files_count = $sourceFiles.Count
            }
        } else {
            Write-Host " ✗" -ForegroundColor Red
            $errorMsg = "Erreur Git"
            if ($pushOutput -match "Authentication failed") {
                $errorMsg = "Token invalide - Regénérez-le sur GitHub"
            } elseif ($pushOutput -match "Repository not found") {
                $errorMsg = "Repository non trouvé - Créez-le d'abord sur GitHub"
            } elseif ($pushOutput -match "GH013" -or $pushOutput -match "secret") {
                $errorMsg = "GitHub a bloqué le push (secret détecté) - Autorisez-le sur GitHub"
            } else {
                $errorMsg = "Erreur: $($pushOutput | Select-Object -First 2)"
            }
            Write-Host "❌ $errorMsg" -ForegroundColor Red
            return @{
                success = $false
                error = $errorMsg
                git_output = $pushOutput
            }
        }
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Erreur inattendue: $_" -ForegroundColor Red
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
}

# ============================================================================
# MENU PRINCIPAL
# ============================================================================
function Show-MainMenu {
    Clear-Host
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "SHARE SPLIT 1M - $PROJECT_NAME" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=== MENU PRINCIPAL ===" -ForegroundColor Yellow
    Write-Host "1. Publier sur GitHub Repository" -ForegroundColor Green
    Write-Host "2. Créer des Gists avec fichiers sources (lignes numérotées)" -ForegroundColor Yellow
    Write-Host "3. Générer un fichier unique avec tous les sources (lignes numérotées)" -ForegroundColor Cyan
    Write-Host "4. Quitter" -ForegroundColor Red
    Write-Host ""
    $choice = Read-Host "Votre choix [1-4]"
    
    switch ($choice) {
        '1' {
            Write-Host "`n=== PUBLICATION GITHUB REPOSITORY ===" -ForegroundColor Cyan
            
            # Vérifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            # Vérifier les autres informations
            $githubUsername = $GITHUB_USERNAME
            if (-not $githubUsername) {
                $githubUsername = Read-Host "Nom d'utilisateur GitHub"
            }
            
            $repoName = Read-Host "Nom du repository"
            
            # S'assurer d'être dans le bon répertoire
            Write-Host "`nVérification du répertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez être dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Exécutez d'abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            # Exécuter la publication
            $result = Publish-ToGitHubRepo -Token $GITHUB_TOKEN `
                -Username $githubUsername `
                -RepoName $repoName `
                -Description $GITHUB_REPO_DESCRIPTION `
                -IsPrivate $false
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Publication réussie sur GitHub!" -ForegroundColor Green
                Write-Host "Repository: $($result.repo_url)" -ForegroundColor Cyan
                Write-Host "Fichiers traités: $($result.files_count)" -ForegroundColor Gray
                Write-Host "Fichier créé: $($result.index_file)" -ForegroundColor Gray
            } else {
                Write-Host ""
                Write-Host "❌ Échec de la publication" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '2' {
            Write-Host "`n=== CRÉATION DE GISTS AVEC FICHIERS SOURCES ===" -ForegroundColor Cyan
            
            # Vérifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            $githubUsername = $GITHUB_USERNAME
            if (-not $githubUsername) {
                $githubUsername = Read-Host "Nom d'utilisateur GitHub"
            }
            
            # Vérifier le répertoire
            Write-Host "`nVérification du répertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez être dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Exécutez d'abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            # Obtenir les fichiers sources
            Write-Host "`nRecherche des fichiers sources..." -ForegroundColor Yellow
            $sourceFiles = Get-SourceFiles -BasePath (Get-Location)
            
            if ($sourceFiles.Count -eq 0) {
                Write-Host "❌ Aucun fichier source trouvé" -ForegroundColor Red
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            Write-Host "`nFichiers sources trouvés: $($sourceFiles.Count)" -ForegroundColor Green
            
            # Afficher un aperçu des fichiers
            Write-Host "`nAperçu des fichiers (premiers 10):" -ForegroundColor Yellow
            $sourceFiles | Select-Object -First 10 | ForEach-Object {
                Write-Host "  - $($_.Path) ($([math]::Round($_.File.Length/1024, 2)) KB)" -ForegroundColor Gray
            }
            
            if ($sourceFiles.Count -gt 10) {
                Write-Host "  ... et $($sourceFiles.Count - 10) autres fichiers" -ForegroundColor Gray
            }
            
            # Demander confirmation
            Write-Host "`nConfirmez-vous la création des Gists avec ces $($sourceFiles.Count) fichiers ?" -ForegroundColor Yellow
            $confirm = Read-Host "[O]ui ou [N]on"
            
            if ($confirm -notmatch '^[OoYy]') {
                Write-Host "Opération annulée." -ForegroundColor Yellow
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            # Créer les Gists
            $result = Create-SourceGists -Token $GITHUB_TOKEN `
                -Username $githubUsername `
                -Description $GITHUB_REPO_DESCRIPTION `
                -SourceFiles $sourceFiles
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Gists créés avec succès!" -ForegroundColor Green
                Write-Host "Nombre de Gists: $($result.total_gists)" -ForegroundColor Cyan
                Write-Host "Total fichiers: $($result.total_files)" -ForegroundColor Gray
                Write-Host "Fichier d'index: $($result.index_file)" -ForegroundColor Gray
                
                Write-Host "`n🔗 Liens des Gists:" -ForegroundColor Yellow
                foreach ($url in $result.gist_urls) {
                    Write-Host "  $url" -ForegroundColor Cyan
                }
            } else {
                Write-Host ""
                Write-Host "❌ Échec de la création des Gists" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '3' {
            Write-Host "`n=== GÉNÉRATION FICHIER UNIQUE AVEC TOUS LES SOURCES ===" -ForegroundColor Cyan
            
            # Vérifier le répertoire
            Write-Host "Vérification du répertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez être dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Exécutez d'abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            # Utiliser directement la description du projet
            $result = Generate-LocalSingleFile -Description $GITHUB_REPO_DESCRIPTION
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Fichier unique créé avec succès!" -ForegroundColor Green
                Write-Host "📄 Fichier: $($result.output_file)" -ForegroundColor Cyan
                Write-Host "📊 Taille: $($result.file_size_human)" -ForegroundColor Gray
                Write-Host "📁 Fichiers sources inclus: $($result.files_count)" -ForegroundColor Gray
                Write-Host "📈 Lignes totales: $($result.total_lines)" -ForegroundColor Gray
            } else {
                Write-Host ""
                Write-Host "❌ Échec de la génération" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '4' {
            Write-Host "Au revoir!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "Choix invalide!" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================
# Boucle principale
do {
    try {
        Show-MainMenu
    } catch {
        Write-Host "❌ Erreur: $_" -ForegroundColor Red
        Write-Host "Redémarrage dans 3 secondes..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($true)