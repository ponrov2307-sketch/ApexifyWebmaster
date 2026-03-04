param(
    [string[]]$Targets = @(
        "app.py",
        "web\router.py",
        "web\components\table.py",
        "web\components\charts.py"
    )
)

$ErrorActionPreference = "Stop"
$banned = @(
    @{
        Name = "double_question_in_string"
        Regex = "['""][^'""]*\?\?[^'""]*['""]"
        Message = "Found '??' inside a quoted UI string."
    },
    @{
        Name = "mojibake_bullet"
        Regex = "โ€ข|เนโฌเธ"
        Message = "Found mojibake bullet token."
    },
    @{
        Name = "thai_mojibake_cluster"
        Regex = "เธ.*เธ|เน.*เธ|โ€|ย€"
        Message = "Found likely Thai mojibake cluster in a UI string."
    }
)

$hasIssue = $false

foreach ($file in $Targets) {
    if (-not (Test-Path $file)) { continue }
    $lines = Get-Content $file -Encoding UTF8
    for ($idx = 0; $idx -lt $lines.Count; $idx++) {
        $line = $lines[$idx]
        if ($line.TrimStart().StartsWith("#")) { continue }
        if ($line -notmatch "ui\.") { continue }

        foreach ($rule in $banned) {
            if ($line -match $rule.Regex) {
                $hasIssue = $true
                $lineNo = $idx + 1
                Write-Host "[FAIL] $($rule.Name): ${file}:$lineNo" -ForegroundColor Red
                Write-Host "       $($rule.Message)" -ForegroundColor DarkRed
            }
        }
    }
}

if ($hasIssue) {
    Write-Host "Text integrity check failed." -ForegroundColor Red
    exit 1
}

Write-Host "Text integrity check passed." -ForegroundColor Green
exit 0
