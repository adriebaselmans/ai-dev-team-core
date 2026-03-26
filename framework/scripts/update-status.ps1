param(
    [Parameter(Mandatory = $true)]
    [string]$Phase,

    [Parameter(Mandatory = $true)]
    [string]$Owner,

    [Parameter(Mandatory = $true)]
    [string]$State,

    [Parameter(Mandatory = $true)]
    [string]$NextAction
)

$content = @"
# Current Status

- Phase: $Phase
- Owner: $Owner
- State: $State
- Next action: $NextAction
"@

Set-Content -Path "framework/flows/current-status.md" -Value $content

$statePath = "framework/runtime/state.json"
$existingState = @{}

if (Test-Path $statePath) {
    try {
        $existingState = Get-Content $statePath -Raw | ConvertFrom-Json -AsHashtable
    }
    catch {
        $existingState = @{}
    }
}

$stateJson = @{
    version = if ($existingState.ContainsKey("version")) { $existingState.version } else { 1 }
    runtime = if ($existingState.ContainsKey("runtime")) { $existingState.runtime } else { "codex-first" }
    phase = $Phase
    owner = $Owner
    state = $State
    next_action = $NextAction
    active_feature = if ($existingState.ContainsKey("active_feature")) { $existingState.active_feature } else { $null }
    active_subagents = if ($existingState.ContainsKey("active_subagents")) { $existingState.active_subagents } else { @() }
    last_transition = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6

Set-Content -Path $statePath -Value $stateJson
