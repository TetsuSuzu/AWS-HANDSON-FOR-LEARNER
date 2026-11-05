# Session3: curl.exe で会員登録 API (POST /) と CORS をテストする
#
# 使い方（PowerShell）:
#   cd <このリポジトリ>\Session3
#   .\curl-test.ps1 -Api "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev" -Origin "https://dev.xxxxxxxxxxxxxx.amplifyapp.com"
#
# -Api    : 3-5 で控えた API の URL（ステージ名 /dev まで。末尾に / は付けない）
# -Origin : 3-7 で CORS に登録したオリジン（Amplify の URL。パスや末尾の / は付けない）
#
# 注意: テスト 3 で、DynamoDB に会員を 1 件登録します（ID は curl-<日時>）。
#       不要になったら、Session4 の管理画面か DynamoDB の画面で削除してください。

param(
    [Parameter(Mandatory = $true)][string]$Api,
    [Parameter(Mandatory = $true)][string]$Origin
)

$ErrorActionPreference = "Stop"
$Api = $Api.TrimEnd("/")

# curl.exe で送る JSON は、BOM なしの UTF-8 のファイルにして渡す（引用符の問題を避けるため）
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) "curl-test-body.json"
function Write-Body([string]$json) {
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding($false)))
}

# curl.exe を実行して、ステータス・CORS ヘッダー・本文を返す
function Invoke-Curl([string[]]$CurlArgs) {
    $raw = (& curl.exe -s -i @CurlArgs) -join "`n"
    $status = if ($raw -match '(?m)^HTTP/\S+\s+(\d{3})') { [int]$Matches[1] } else { 0 }
    $allow = if ($raw -match '(?im)^access-control-allow-origin:\s*(.+?)\s*$') { $Matches[1] } else { "" }
    $methods = if ($raw -match '(?im)^access-control-allow-methods:\s*(.+?)\s*$') { $Matches[1] } else { "" }
    $headers = if ($raw -match '(?im)^access-control-allow-headers:\s*(.+?)\s*$') { $Matches[1] } else { "" }
    $body = ($raw -split "`n`n", 2)[-1].Trim()
    [pscustomobject]@{ Status = $status; Allow = $allow; Methods = $methods; Headers = $headers; Body = $body }
}

$script:fail = 0
function Check([string]$name, [bool]$ok, [string]$detail) {
    if ($ok) { Write-Host ("[OK]   " + $name) -ForegroundColor Green }
    else { Write-Host ("[NG]   " + $name + "  -> " + $detail) -ForegroundColor Red; $script:fail++ }
}

Write-Host "API    : $Api"
Write-Host "Origin : $Origin"
Write-Host ""

# --- 1. プリフライト（許可したオリジン）---
$r = Invoke-Curl @("-X", "OPTIONS", $Api, "-H", "Origin: $Origin",
    "-H", "Access-Control-Request-Method: POST", "-H", "Access-Control-Request-Headers: content-type")
Check "1. プリフライト: 204 または 200 が返る" ($r.Status -in 200, 204) "status=$($r.Status)"
Check "1. プリフライト: access-control-allow-origin が Origin と同じ" ($r.Allow -eq $Origin) "値='$($r.Allow)'"
Check "1. プリフライト: allow-methods に POST が含まれる" ($r.Methods -match "POST") "値='$($r.Methods)'"
Check "1. プリフライト: allow-headers に content-type が含まれる" ($r.Headers -match "content-type") "値='$($r.Headers)'"

# --- 2. プリフライト（許可していないオリジン）---
$r = Invoke-Curl @("-X", "OPTIONS", $Api, "-H", "Origin: http://example.com",
    "-H", "Access-Control-Request-Method: POST", "-H", "Access-Control-Request-Headers: content-type")
Check "2. 許可していないオリジン: 応答があり、access-control-allow-origin が出ない" ($r.Status -ne 0 -and $r.Allow -eq "") "status=$($r.Status) 値='$($r.Allow)'"

# --- 3. 会員登録（正常）---
$id = "curl-" + (Get-Date -Format "yyyyMMddHHmmss")
Write-Body ('{"id":"' + $id + '","name":"Curl Test","email":"curl@example.com","age":30,"address":"Tokyo","tel":"09012345678"}')
$r = Invoke-Curl @("-X", "POST", $Api, "-H", "Origin: $Origin", "-H", "Content-Type: application/json", "--data-binary", "@$tmp")
Check "3. 会員登録: 201 が返る" ($r.Status -eq 201) "status=$($r.Status) body=$($r.Body)"
Check "3. 会員登録: 実際の応答にも access-control-allow-origin が付く" ($r.Allow -eq $Origin) "値='$($r.Allow)'"

# --- 4. 同じ ID をもう一度登録（重複）---
$r = Invoke-Curl @("-X", "POST", $Api, "-H", "Origin: $Origin", "-H", "Content-Type: application/json", "--data-binary", "@$tmp")
Check "4. 同じ ID の再登録: 409 が返る" ($r.Status -eq 409) "status=$($r.Status) body=$($r.Body)"

# --- 5. 必須項目が足りない ---
Write-Body '{"id":"curl-missing","name":"Curl Test"}'
$r = Invoke-Curl @("-X", "POST", $Api, "-H", "Content-Type: application/json", "--data-binary", "@$tmp")
Check "5. 必須項目の不足: 400 が返る" ($r.Status -eq 400) "status=$($r.Status) body=$($r.Body)"

# --- 6. JSON の形式が壊れている ---
Write-Body '{this is not json'
$r = Invoke-Curl @("-X", "POST", $Api, "-H", "Content-Type: application/json", "--data-binary", "@$tmp")
Check "6. JSON の形式エラー: 400 が返る" ($r.Status -eq 400) "status=$($r.Status) body=$($r.Body)"

Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host ""
if ($script:fail -eq 0) { Write-Host "すべて成功しました。" -ForegroundColor Green }
else { Write-Host "$($script:fail) 件が失敗しました。README の「うまくいかないとき」を確認してください。" -ForegroundColor Red; exit 1 }
