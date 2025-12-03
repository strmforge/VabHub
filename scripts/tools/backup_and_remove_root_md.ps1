# PowerShell script to backup and remove root-level Markdown files

# Define whitelist
$whitelist = @("README.md", "CHANGELOG.md")

# Get all Markdown files in root directory
$rootMdFiles = Get-ChildItem -Path . -Filter "*.md" | Select-Object -ExpandProperty Name

# Backup and remove non-whitelist files
foreach ($file in $rootMdFiles) {
    if (-not $whitelist.Contains($file)) {
        # Backup the file
        Copy-Item -Path $file -Destination "local-notes/root-md-backup/$file" -Force
        Write-Host "Backed up: $file"
        
        # Remove from Git
        git rm $file
        Write-Host "Removed from Git: $file"
    } else {
        Write-Host "Skipping whitelisted file: $file"
    }
}

Write-Host "\nBackup and removal complete!"
Write-Host "Backed up files are in: local-notes/root-md-backup/"
Write-Host "Remaining root-level Markdown files: $($whitelist -join ', ')"