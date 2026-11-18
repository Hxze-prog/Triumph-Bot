param(
    [Parameter(Mandatory = $true)]
    [string]$DashboardUrl,

    [Parameter(Mandatory = $true)]
    [string]$BotHealthUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:Failures = 0

function Write-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:Failures++
}

function Test-DashboardPage {
    param(
        [string]$BaseUrl,
        [string]$Path
    )

    $url = "$BaseUrl$Path"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -MaximumRedirection 5 -TimeoutSec 30
        if ($response.StatusCode -eq 200) {
            Write-Pass "$url returned 200"
        } else {
            Write-Fail "$url returned $($response.StatusCode)"
        }
    } catch {
        Write-Fail "$url failed: $($_.Exception.Message)"
    }
}

$DashboardUrl = $DashboardUrl.TrimEnd("/")
$BotHealthUrl = $BotHealthUrl.Trim()

Write-Host "Triumph deployment verification"
Write-Host "Dashboard: $DashboardUrl"
Write-Host "Bot health: $BotHealthUrl"
Write-Host ""

foreach ($path in @("/", "/command", "/terms", "/privacy", "/login")) {
    Test-DashboardPage -BaseUrl $DashboardUrl -Path $path
}

try {
    $health = Invoke-RestMethod -Uri $BotHealthUrl -TimeoutSec 30
    if ($health.status -ne "ok") {
        Write-Fail "health status is '$($health.status)'"
    } else {
        Write-Pass "health status is ok"
    }
    if ($health.discord_configured -ne $true) {
        Write-Fail "discord_configured is not true"
    } else {
        Write-Pass "discord_configured is true"
    }
    if ($health.supabase_configured -ne $true) {
        Write-Fail "supabase_configured is not true"
    } else {
        Write-Pass "supabase_configured is true"
    }
    if ($health.bot_ready -ne $true) {
        Write-Fail "bot_ready is not true"
    } else {
        Write-Pass "bot_ready is true"
    }
    if ([int]$health.guilds -lt 1) {
        Write-Fail "guilds is $($health.guilds); expected at least 1"
    } else {
        Write-Pass "guilds is $($health.guilds)"
    }
} catch {
    Write-Fail "$BotHealthUrl failed: $($_.Exception.Message)"
}

Write-Host ""
if ($script:Failures -gt 0) {
    Write-Host "$($script:Failures) check(s) failed." -ForegroundColor Red
    exit 1
}

Write-Host "All deployment checks passed." -ForegroundColor Green
exit 0
