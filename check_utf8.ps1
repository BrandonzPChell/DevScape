# check_utf8.ps1
param($files)

$err = $false
foreach ($f in $files) {
  try {
    Get-Content -Path $f -Encoding UTF8 | Out-Null
  } catch {
    Write-Error "Encoding error: $f is not valid UTF-8"; $err = $true
  }
}
if ($err) { exit 1 }
exit 0
