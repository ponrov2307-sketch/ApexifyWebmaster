param(
    [string[]]$Targets = @(
        "app.py",
        "web\router.py",
        "web\i18n.py",
        "web\components\*.py",
        "services\*.py"
    )
)

$ErrorActionPreference = "Stop"
$rules = @(
    @{
        Name = "double_question_in_string"
        Severity = "fail"
        Regex = "['""][^'""]*\?\?[^'""]*['""]"
        Message = "Found '??' inside a quoted string."
    },
    @{
        Name = "mojibake_bullet"
        Severity = "fail"
        Regex = "\u0E42\u20AC\u0E02|\u0E40\u0E19\u20AC\u0E40\u0E18"
        Message = "Found mojibake bullet token."
    },
    @{
        Name = "thai_mojibake_cluster"
        Severity = "warn"
        Regex = "(?:\u0E40\u0E18|\u0E40\u0E19){3,}|\u0E42\u20AC|\u0E22\u20AC|\u00C3|\u00C2|\uFFFD|[\u0400-\u04FF]{8,}"
        Message = "Found likely Thai mojibake cluster."
    }
)

$expandedTargets = @()
foreach ($target in $Targets) {
    $resolved = Resolve-Path $target -ErrorAction SilentlyContinue
    if ($resolved) {
        $expandedTargets += $resolved.Path
    }
}

if (-not $expandedTargets) {
    Write-Host "No matching files to scan." -ForegroundColor Yellow
    exit 0
}

$hasFailure = $false
$warnCount = 0

foreach ($file in $expandedTargets) {
    if (-not (Test-Path $file)) { continue }
    $lines = Get-Content $file -Encoding UTF8
    for ($idx = 0; $idx -lt $lines.Count; $idx++) {
        $line = $lines[$idx]
        if ($line.TrimStart().StartsWith("#")) { continue }

        foreach ($rule in $rules) {
            if (
                $rule.Name -eq "double_question_in_string" -and
                $file -like "*web\i18n.py" -and
                (
                    $line -match 'replace\("\?\?"' -or
                    $line -match '\("\?\?",\s*\d+\)' -or
                    $line -match 'if\s+\"\?\?\"\s+in\s+'
                )
            ) {
                continue
            }
            if ($line -match $rule.Regex) {
                $lineNo = $idx + 1
                if ($rule.Severity -eq "fail") {
                    $hasFailure = $true
                    Write-Host "[FAIL] $($rule.Name): ${file}:$lineNo" -ForegroundColor Red
                    Write-Host "       $($rule.Message)" -ForegroundColor DarkRed
                } else {
                    $warnCount++
                    Write-Host "[WARN] $($rule.Name): ${file}:$lineNo" -ForegroundColor Yellow
                    Write-Host "       $($rule.Message)" -ForegroundColor DarkYellow
                }
            }
        }
    }
}

if ($hasFailure) {
    Write-Host "Text integrity check failed." -ForegroundColor Red
    exit 1
}

if ($warnCount -gt 0) {
    Write-Host "Text integrity check passed with warnings ($warnCount)." -ForegroundColor Yellow
    exit 0
}

Write-Host "Text integrity check passed." -ForegroundColor Green
exit 0
