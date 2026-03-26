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
