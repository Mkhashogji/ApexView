# G0 Phase 0.3 — Golden snapshot capture (legacy pipeline contract freeze)
# Captures RAW response bytes for the qualifying telemetry endpoint, delta endpoint,
# track endpoint, and performance-insights endpoint, for the fixed fixture set:
#   Shanghai 2025 Q3: PIA (ref) vs RUS    [session 2025_2_Qualifying]
#   Monaco   2025 Q3: NOR (ref) vs LEC    [session 2025_8_Qualifying]
# Run from repo root with f1-api (:8000) and f1-analysis (:8501) healthy.
# Usage: powershell -File diagnostics/g0/capture_golden.ps1 [-OutDir diagnostics/g0/golden/legacy]
param(
  [string]$OutDir = "diagnostics/g0/golden/legacy"
)
$ErrorActionPreference = "Stop"
$API = "http://localhost:8000"
$ANALYSIS = "http://localhost:8501"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$fixtures = @(
  @{ name = "shanghai"; session = "2025_2_Qualifying"; round = 2;  ref = "PIA"; comp = "RUS" },
  @{ name = "monaco";   session = "2025_8_Qualifying"; round = 8;  ref = "NOR"; comp = "LEC" }
)

foreach ($f in $fixtures) {
  $n = $f.name
  Write-Output "=== fixture: $n ($($f.session)) $($f.ref) vs $($f.comp) ==="

  # 1. Track data (corners source — exactly what the frontend uses)
  $trackUrl = "$API/track/$($f.round)?season=2025"
  Invoke-WebRequest -Uri $trackUrl -OutFile "$OutDir/track_$n.json" -TimeoutSec 120 | Out-Null
  Write-Output "  track captured"

  # 2. Telemetry endpoint (warm-up doubles as capture; first call loads the FastF1 session)
  $telUrl = "$API/telemetry?session=$($f.session)&drivers=$($f.ref)&drivers=$($f.comp)&session_part=Q3"
  Invoke-WebRequest -Uri $telUrl -OutFile "$OutDir/telemetry_$n.json" -TimeoutSec 300 | Out-Null
  Write-Output "  telemetry captured"

  # 3. Delta endpoint (no frontend consumer — captured because it is in G0 rewire scope)
  $deltaUrl = "$API/telemetry/delta?session=$($f.session)&reference_driver=$($f.ref)&compare_drivers=$($f.comp)&session_part=Q3"
  Invoke-WebRequest -Uri $deltaUrl -OutFile "$OutDir/delta_$n.json" -TimeoutSec 300 | Out-Null
  Write-Output "  delta captured"

  # 4. Performance-insights — payload built EXACTLY as the frontend does
  #    (apps/web/lib/api.ts fetchPerformanceInsights: corners mapped from /track corners,
  #     include_telemetry: true, mode engineer, track_length from track.length)
  $track = Get-Content "$OutDir/track_$n.json" -Raw | ConvertFrom-Json
  $corners = @($track.corners | ForEach-Object {
    [ordered]@{
      corner_number = $_.cornerNumber
      name          = $_.name
      apex_distance = $_.distance
      corner_type   = $_.type
    }
  })
  $body = [ordered]@{
    session_id       = $f.session
    reference_driver = $f.ref
    compare_drivers  = @($f.comp)
    corners          = $corners
    mode             = "engineer"
    session_part     = "Q3"
    include_telemetry = $true
    track_length     = $track.length
  } | ConvertTo-Json -Depth 6
  Invoke-WebRequest -Uri "$ANALYSIS/analysis/performance-insights" -Method POST `
    -Body $body -ContentType "application/json" -OutFile "$OutDir/insights_$n.json" -TimeoutSec 300 | Out-Null
  # keep the exact request body for replay parity
  Set-Content -Path "$OutDir/insights_request_$n.json" -Value $body -Encoding utf8
  Write-Output "  performance-insights captured"
}
Write-Output "DONE -> $OutDir"
