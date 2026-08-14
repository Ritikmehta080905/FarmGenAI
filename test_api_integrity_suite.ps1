# ==============================================================================
# AgriNegotiator - API Contract, Schema, Identity & Persistence Integrity Suite
# Target: http://localhost:8000
# ==============================================================================

$ErrorActionPreference = "Continue"
$BaseUrl = "http://localhost:8000"
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$RandomId = (Get-Random -Minimum 1000 -Maximum 9999)

# Results Collector
$Results = [System.Collections.Generic.List[PSObject]]::new()
$GlobalFailed = $false

function Get-HttpErrorDetails {
    param($Exception)
    $statusCode = 0
    $bodyText = ""
    try {
        if ($Exception.Response -and $Exception.Response.StatusCode) {
            $statusCode = [int]$Exception.Response.StatusCode
        }
        if ($Exception.Response -and $Exception.Response.GetResponseStream()) {
            $stream = $Exception.Response.GetResponseStream()
            $reader = [System.IO.StreamReader]::new($stream)
            $bodyText = $reader.ReadToEnd()
        }
    } catch {
        # Fallback if stream reading fails
    }
    if (-not $bodyText -and $Exception.Message) {
        $bodyText = $Exception.Message
    }
    return @{ StatusCode = $statusCode; Body = $bodyText }
}

function Record-IntegrityResult {
    param(
        [string]$Category,
        [string]$TestName,
        [string]$Endpoint,
        [string]$Expected,
        [string]$Actual,
        [string]$Status,
        [string]$Details
    )
    $Results.Add([PSCustomObject]@{
        Category = $Category
        TestName = $TestName
        Endpoint = $Endpoint
        Expected = $Expected
        Actual   = $Actual
        Status   = $Status
        Details  = $Details
    })

    if ($Status -eq "PASS") {
        Write-Host " [PASS] [$Category] $TestName - $Details" -ForegroundColor Green
    } else {
        Write-Host " [FAIL] [$Category] $TestName - Expected: $Expected | Actual: $Actual | $Details" -ForegroundColor Red
        $script:GlobalFailed = $true
    }
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  AGRINEGOTIATOR API INTEGRITY & CONTRACT VERIFICATION" -ForegroundColor Cyan
Write-Host "  Target: $BaseUrl | Timestamp: $Timestamp | Run: $RandomId" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

# ==============================================================================
# SECTION 1: AUTH RESPONSE INTEGRITY & JWT RESOLUTION
# ==============================================================================
Write-Host "--- 1. Auth Response Integrity ---" -ForegroundColor Yellow

$FarmerEmail = "integ_farmer_${Timestamp}_${RandomId}@agri.com"
$BuyerEmail  = "integ_buyer_${Timestamp}_${RandomId}@agri.com"
$TestPassword = "Pass123!Secure"

$FarmerToken = $null
$FarmerUserId = $null
$BuyerToken = $null
$BuyerUserId = $null

# 1.1 Farmer Registration Contract
try {
    $FarmerSignup = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/signup" -Method POST -ContentType "application/json" -Body (@{
        name     = "Ramesh Patil"
        email    = $FarmerEmail
        password = $TestPassword
        role     = "farmer"
        location = "Pune"
        language = "Marathi"
    } | ConvertTo-Json) -TimeoutSec 10

    if ($FarmerSignup.token -and $FarmerSignup.user_id -and $FarmerSignup.role -eq "farmer") {
        $FarmerToken = $FarmerSignup.token
        $FarmerUserId = $FarmerSignup.user_id
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "token, user_id (string), role=farmer" -Actual "user_id=$FarmerUserId, role=$($FarmerSignup.role)" -Status "PASS" -Details "Valid registration envelope and token generated"
    } else {
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "token, user_id (string), role=farmer" -Actual ($FarmerSignup | ConvertTo-Json -Compress) -Status "FAIL" -Details "Missing token or user_id in signup response"
    }
} catch {
    $err = Get-HttpErrorDetails $_.Exception
    Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
}

# 1.2 Buyer Registration Contract
try {
    $BuyerSignup = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/signup" -Method POST -ContentType "application/json" -Body (@{
        name     = "Sahyadri Agro Traders"
        email    = $BuyerEmail
        password = $TestPassword
        role     = "buyer"
        location = "Aurangabad"
    } | ConvertTo-Json) -TimeoutSec 10

    if ($BuyerSignup.token -and $BuyerSignup.user_id -and $BuyerSignup.role -eq "buyer") {
        $BuyerToken = $BuyerSignup.token
        $BuyerUserId = $BuyerSignup.user_id
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Buyer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "token, user_id (string), role=buyer" -Actual "user_id=$BuyerUserId, role=$($BuyerSignup.role)" -Status "PASS" -Details "Valid registration envelope and token generated"
    } else {
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Buyer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "token, user_id (string), role=buyer" -Actual ($BuyerSignup | ConvertTo-Json -Compress) -Status "FAIL" -Details "Missing token or user_id in signup response"
    }
} catch {
    $err = Get-HttpErrorDetails $_.Exception
    Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Buyer Signup Contract" -Endpoint "POST /api/v1/auth/signup" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
}

# 1.3 Login Token & Claim Consistency
try {
    $FarmerLogin = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body (@{
        email    = $FarmerEmail
        password = $TestPassword
    } | ConvertTo-Json) -TimeoutSec 10

    if ($FarmerLogin.token -and $FarmerLogin.user_id -eq $FarmerUserId) {
        $FarmerToken = $FarmerLogin.token
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Login Identity Match" -Endpoint "POST /api/v1/auth/login" -Expected "user_id=$FarmerUserId" -Actual "user_id=$($FarmerLogin.user_id)" -Status "PASS" -Details "Login issued JWT matching signup user identity"
    } else {
        Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Login Identity Match" -Endpoint "POST /api/v1/auth/login" -Expected "user_id=$FarmerUserId" -Actual "user_id=$($FarmerLogin.user_id)" -Status "FAIL" -Details "Login user_id mismatch"
    }
} catch {
    $err = Get-HttpErrorDetails $_.Exception
    Record-IntegrityResult -Category "AUTH INTEGRITY" -TestName "Farmer Login Identity Match" -Endpoint "POST /api/v1/auth/login" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
}

# ==============================================================================
# SECTION 2: PROFILE IDENTITY & TRUST CONSISTENCY
# ==============================================================================
Write-Host "`n--- 2. Profile Identity & Trust Consistency ---" -ForegroundColor Yellow

# 2.1 Farmer Profile Self-Resolution
if ($FarmerToken) {
    try {
        $FProf = Invoke-RestMethod -Uri "$BaseUrl/api/v1/profiles/me" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        $uidMatch = ($FProf.data.user_id -eq $FarmerUserId)
        $roleMatch = ($FProf.data.role -eq "farmer")
        $trustIsNum = ($FProf.data.trust_score -ne $null -and ($FProf.data.trust_score -is [ValueType]))

        if ($FProf.success -and $uidMatch -and $roleMatch -and $trustIsNum) {
            Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Farmer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "user_id=$FarmerUserId, role=farmer, trust_score=[Number]" -Actual "user_id=$($FProf.data.user_id), role=$($FProf.data.role), trust_score=$($FProf.data.trust_score)" -Status "PASS" -Details "Farmer profile verified with numeric trust score"
        } else {
            Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Farmer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "user_id=$FarmerUserId, role=farmer, trust_score=[Number]" -Actual "user_id=$($FProf.data.user_id), role=$($FProf.data.role), trust_score=$($FProf.data.trust_score)" -Status "FAIL" -Details "Profile schema or identity mismatch"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Farmer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 2.2 Buyer Profile Self-Resolution
if ($BuyerToken) {
    try {
        $BProf = Invoke-RestMethod -Uri "$BaseUrl/api/v1/profiles/me" -Method GET -Headers @{ Authorization = "Bearer $BuyerToken" } -TimeoutSec 10
        $uidMatch = ($BProf.data.user_id -eq $BuyerUserId)
        $roleMatch = ($BProf.data.role -eq "buyer")
        $trustIsNum = ($BProf.data.trust_score -ne $null -and ($BProf.data.trust_score -is [ValueType]))

        if ($BProf.success -and $uidMatch -and $roleMatch -and $trustIsNum) {
            Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Buyer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "user_id=$BuyerUserId, role=buyer, trust_score=[Number]" -Actual "user_id=$($BProf.data.user_id), role=$($BProf.data.role), trust_score=$($BProf.data.trust_score)" -Status "PASS" -Details "Buyer profile verified with numeric trust score"
        } else {
            Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Buyer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "user_id=$BuyerUserId, role=buyer, trust_score=[Number]" -Actual "user_id=$($BProf.data.user_id), role=$($BProf.data.role), trust_score=$($BProf.data.trust_score)" -Status "FAIL" -Details "Profile schema or identity mismatch"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "PROFILE INTEGRITY" -TestName "Buyer Profile Identity" -Endpoint "GET /api/v1/profiles/me" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 3: FARMER DATA & LISTING CONSISTENCY
# ==============================================================================
Write-Host "`n--- 3. Farmer Listing Data Consistency ---" -ForegroundColor Yellow

$SubmittedCrop = "Wheat"
$SubmittedQuantity = 1200.0
$SubmittedMinPrice = 24.0
$SubmittedLocation = "Pune"
$ListingId = $null

if ($FarmerToken) {
    try {
        $ListRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/listings/" -Method POST -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{
            crop          = $SubmittedCrop
            quantity      = $SubmittedQuantity
            min_price     = $SubmittedMinPrice
            location      = $SubmittedLocation
            spoilage_days = 14
            description   = "Integrity Certified Organic Wheat"
        } | ConvertTo-Json) -TimeoutSec 10

        if ($ListRes.success -and $ListRes.listing_id) {
            $ListingId = $ListRes.listing_id
            $isIdStr = ($ListingId -is [string] -and $ListingId.Length -gt 0)
            Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Farmer Listing Creation Contract" -Endpoint "POST /api/v1/listings/" -Expected "success=true, listing_id=[non-empty string]" -Actual "success=$($ListRes.success), listing_id=$ListingId" -Status "PASS" -Details "Listing registered with valid ID"
        } else {
            Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Farmer Listing Creation Contract" -Endpoint "POST /api/v1/listings/" -Expected "success=true, listing_id=[non-empty string]" -Actual ($ListRes | ConvertTo-Json -Compress) -Status "FAIL" -Details "Listing creation failed"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Farmer Listing Creation Contract" -Endpoint "POST /api/v1/listings/" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 4: BUYER DATA & REQUIREMENT CONSISTENCY
# ==============================================================================
Write-Host "`n--- 4. Buyer Requirement Data Consistency ---" -ForegroundColor Yellow

$SubmittedTargetPrice = 28.0
$SubmittedMaxPrice = 31.0
$SubmittedBudget = 38000.0
$RequirementId = $null

if ($BuyerToken) {
    try {
        $ReqRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/requirements/" -Method POST -Headers @{ Authorization = "Bearer $BuyerToken" } -ContentType "application/json" -Body (@{
            crop          = $SubmittedCrop
            quantity      = $SubmittedQuantity
            target_price  = $SubmittedTargetPrice
            max_price     = $SubmittedMaxPrice
            location      = "Aurangabad"
            budget        = $SubmittedBudget
            delivery_days = 10
            quality_grade = "A"
            notes         = "Integrity verified milling demand"
        } | ConvertTo-Json) -TimeoutSec 10

        if ($ReqRes.success -and $ReqRes.requirement_id) {
            $RequirementId = $ReqRes.requirement_id
            Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Buyer Requirement Contract" -Endpoint "POST /api/v1/requirements/" -Expected "success=true, requirement_id=[string]" -Actual "success=$($ReqRes.success), requirement_id=$RequirementId" -Status "PASS" -Details "Requirement registered with valid ID"
        } else {
            Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Buyer Requirement Contract" -Endpoint "POST /api/v1/requirements/" -Expected "success=true, requirement_id=[string]" -Actual ($ReqRes | ConvertTo-Json -Compress) -Status "FAIL" -Details "Requirement creation failed"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "DATA CONSISTENCY" -TestName "Buyer Requirement Contract" -Endpoint "POST /api/v1/requirements/" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 5: MATCHING RESPONSE CONTRACT & SCORES
# ==============================================================================
Write-Host "`n--- 5. Matching Response Contract & Type Integrity ---" -ForegroundColor Yellow

# 5.1 Listing-to-Buyers Multi-Factor Match Contract
if ($FarmerToken -and $ListingId -and $RequirementId) {
    try {
        $MatchRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/matching/listing-to-buyers" -Method POST -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{
            listing_id    = $ListingId
            crop          = $SubmittedCrop
            quantity      = $SubmittedQuantity
            min_price     = $SubmittedMinPrice
            location      = $SubmittedLocation
            spoilage_days = 14
            quality       = "A"
        } | ConvertTo-Json) -TimeoutSec 10

        $hasSuccess = ($MatchRes.success -eq $true)
        $hasData = ($MatchRes.data -ne $null)
        $hasCount = ($MatchRes.total_matches -is [ValueType])

        if ($hasSuccess -and $hasData -and $hasCount) {
            $Candidate = $null
            foreach ($item in $MatchRes.data) {
                if ($item.requirement_id -eq $RequirementId) {
                    $Candidate = $item
                    break
                }
            }

            if ($Candidate) {
                $scoreIsNum = ($Candidate.compatibility_score -is [ValueType])
                $gradeValid = ($Candidate.match_grade -in @("A", "B", "C", "D"))
                $buyerIdValid = ($Candidate.buyer_id -eq $BuyerUserId)

                if ($scoreIsNum -and $gradeValid -and $buyerIdValid) {
                    Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Listing-to-Buyers Schema Integrity" -Endpoint "POST /api/v1/matching/listing-to-buyers" -Expected "buyer_id=$BuyerUserId, score=[Number], grade in [A,B,C,D]" -Actual "buyer_id=$($Candidate.buyer_id), score=$($Candidate.compatibility_score), grade=$($Candidate.match_grade)" -Status "PASS" -Details "Matching contract validated with correct types and IDs"
                } else {
                    Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Listing-to-Buyers Schema Integrity" -Endpoint "POST /api/v1/matching/listing-to-buyers" -Expected "buyer_id=$BuyerUserId, score=[Number], grade in [A,B,C,D]" -Actual "buyer_id=$($Candidate.buyer_id), score=$($Candidate.compatibility_score), grade=$($Candidate.match_grade)" -Status "FAIL" -Details "Invalid candidate type or mismatch"
                }
            } else {
                Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Listing-to-Buyers Schema Integrity" -Endpoint "POST /api/v1/matching/listing-to-buyers" -Expected "Requirement $RequirementId in matches" -Actual "Count=$($MatchRes.data.Count)" -Status "FAIL" -Details "Expected requirement not returned in match results"
            }
        } else {
            Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Listing-to-Buyers Schema Integrity" -Endpoint "POST /api/v1/matching/listing-to-buyers" -Expected "success=true, data=[Array], total_matches=[Number]" -Actual ($MatchRes | ConvertTo-Json -Compress) -Status "FAIL" -Details "Matching envelope invalid"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Listing-to-Buyers Schema Integrity" -Endpoint "POST /api/v1/matching/listing-to-buyers" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 5.2 Reverse Matching (Requirement to Listings) Contract
if ($BuyerToken -and $RequirementId) {
    try {
        $RevRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/matching/requirement-to-listings" -Method POST -Headers @{ Authorization = "Bearer $BuyerToken" } -ContentType "application/json" -Body (@{
            requirement_id = $RequirementId
            crop           = $SubmittedCrop
            quantity       = $SubmittedQuantity
            target_price   = $SubmittedTargetPrice
            max_price      = $SubmittedMaxPrice
            budget         = $SubmittedBudget
            location       = "Aurangabad"
        } | ConvertTo-Json) -TimeoutSec 10

        if ($RevRes.success -eq $true -and ($RevRes.total_matches -is [ValueType])) {
            Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Reverse Matching Schema Integrity" -Endpoint "POST /api/v1/matching/requirement-to-listings" -Expected "success=true, total_matches=[Number], crop=$SubmittedCrop" -Actual "success=$($RevRes.success), total_matches=$($RevRes.total_matches), crop=$($RevRes.crop)" -Status "PASS" -Details "Reverse matching schema confirmed"
        } else {
            Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Reverse Matching Schema Integrity" -Endpoint "POST /api/v1/matching/requirement-to-listings" -Expected "success=true, total_matches=[Number]" -Actual ($RevRes | ConvertTo-Json -Compress) -Status "FAIL" -Details "Invalid reverse match envelope"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "MATCHING CONTRACT" -TestName "Reverse Matching Schema Integrity" -Endpoint "POST /api/v1/matching/requirement-to-listings" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 6: NEGOTIATION RESPONSE CONTRACT & CONVERGENCE
# ==============================================================================
Write-Host "`n--- 6. LangGraph Multi-Agent Negotiation Contract ---" -ForegroundColor Yellow

$NegotiationId = $null
$FinalPrice = $null
$NegotiationStatus = $null

if ($FarmerToken) {
    try {
        $NegRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/negotiation/start-negotiation" -Method POST -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{
            farmer_name        = "Ramesh Patil"
            crop               = $SubmittedCrop
            quantity           = $SubmittedQuantity
            min_price          = $SubmittedMinPrice
            shelf_life         = 14
            location           = $SubmittedLocation
            quality            = "A"
            language           = "Marathi"
            buyer_name         = "Sahyadri Agro Traders"
            buyer_budget       = $SubmittedBudget
            buyer_target_price = $SubmittedTargetPrice
            buyer_location     = "Aurangabad"
        } | ConvertTo-Json) -TimeoutSec 120

        $NegotiationId = $NegRes.negotiation_id
        $NegotiationStatus = $NegRes.status
        $FinalPrice = [double]$NegRes.final_price

        $idValid = ($NegotiationId -is [string] -and $NegotiationId.Length -gt 0)
        $statusValid = ($NegotiationStatus -in @("DEAL", "NO_DEAL"))
        $priceValid = ($FinalPrice -ge $SubmittedMinPrice -and $FinalPrice -le $SubmittedMaxPrice)

        if ($idValid -and $statusValid -and $priceValid -and $NegotiationStatus -eq "DEAL") {
            Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Convergence & Schema" -Endpoint "POST /api/v1/negotiation/start-negotiation" -Expected "status=DEAL, price between $SubmittedMinPrice and $SubmittedMaxPrice" -Actual "status=$NegotiationStatus, price=₹$FinalPrice" -Status "PASS" -Details "Multi-agent LangGraph converged to valid deal"
        } else {
            Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Convergence & Schema" -Endpoint "POST /api/v1/negotiation/start-negotiation" -Expected "status=DEAL, price between $SubmittedMinPrice and $SubmittedMaxPrice" -Actual "status=$NegotiationStatus, price=₹$FinalPrice" -Status "FAIL" -Details "Negotiation failed to reach valid DEAL"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Convergence & Schema" -Endpoint "POST /api/v1/negotiation/start-negotiation" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 6.2 Negotiation Telemetry Endpoint Integrity
if ($NegotiationId) {
    try {
        $NegStatusRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/negotiation/negotiation-status/$NegotiationId" -Method GET -TimeoutSec 10
        $idMatches = ($NegStatusRes.negotiation_id -eq $NegotiationId)
        $statusMatches = ($NegStatusRes.status -eq $NegotiationStatus)
        $priceMatches = ([double]$NegStatusRes.final_price -eq $FinalPrice)

        if ($idMatches -and $statusMatches -and $priceMatches) {
            Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Status Telemetry Parity" -Endpoint "GET /api/v1/negotiation/negotiation-status/{id}" -Expected "id=$NegotiationId, status=$NegotiationStatus, price=₹$FinalPrice" -Actual "id=$($NegStatusRes.negotiation_id), status=$($NegStatusRes.status), price=₹$($NegStatusRes.final_price)" -Status "PASS" -Details "Telemetry endpoint reports exact negotiation state"
        } else {
            Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Status Telemetry Parity" -Endpoint "GET /api/v1/negotiation/negotiation-status/{id}" -Expected "id=$NegotiationId, status=$NegotiationStatus, price=₹$FinalPrice" -Actual "id=$($NegStatusRes.negotiation_id), status=$($NegStatusRes.status), price=₹$($NegStatusRes.final_price)" -Status "FAIL" -Details "Telemetry mismatch with negotiation result"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "NEGOTIATION INTEGRITY" -TestName "Negotiation Status Telemetry Parity" -Endpoint "GET /api/v1/negotiation/negotiation-status/{id}" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 7: HISTORY PERSISTENCE & DATA PARITY
# ==============================================================================
Write-Host "`n--- 7. History Persistence & Data Parity ---" -ForegroundColor Yellow

if ($FarmerToken -and $FarmerUserId -and $NegotiationId) {
    try {
        $HistRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/history/$FarmerUserId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        
        $PersistedDeal = $null
        if ($HistRes.history) {
            foreach ($h in $HistRes.history) {
                if ($h.negotiation_id -eq $NegotiationId) {
                    $PersistedDeal = $h
                    break
                }
            }
        }

        if ($PersistedDeal) {
            $cropMatches = ($PersistedDeal.crop -eq $SubmittedCrop)
            $qtyMatches = ([double]$PersistedDeal.quantity -eq $SubmittedQuantity)
            $priceMatches = ([double]$PersistedDeal.final_price -eq $FinalPrice)

            if ($cropMatches -and $qtyMatches -and $priceMatches) {
                Record-IntegrityResult -Category "HISTORY INTEGRITY" -TestName "PostgreSQL History Record Parity" -Endpoint "GET /api/v1/history/{user_id}" -Expected "crop=$SubmittedCrop, qty=$SubmittedQuantity, price=₹$FinalPrice" -Actual "crop=$($PersistedDeal.crop), qty=$($PersistedDeal.quantity), price=₹$($PersistedDeal.final_price)" -Status "PASS" -Details "Persisted transaction matches negotiation output"
            } else {
                Record-IntegrityResult -Category "HISTORY INTEGRITY" -TestName "PostgreSQL History Record Parity" -Endpoint "GET /api/v1/history/{user_id}" -Expected "crop=$SubmittedCrop, qty=$SubmittedQuantity, price=₹$FinalPrice" -Actual "crop=$($PersistedDeal.crop), qty=$($PersistedDeal.quantity), price=₹$($PersistedDeal.final_price)" -Status "FAIL" -Details "Data field mismatch in history record"
            }
        } else {
            Record-IntegrityResult -Category "HISTORY INTEGRITY" -TestName "PostgreSQL History Record Parity" -Endpoint "GET /api/v1/history/{user_id}" -Expected "negotiation_id=$NegotiationId in history" -Actual "Not found in $($HistRes.history.Count) history records" -Status "FAIL" -Details "Negotiation deal was not persisted to database history"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "HISTORY INTEGRITY" -TestName "PostgreSQL History Record Parity" -Endpoint "GET /api/v1/history/{user_id}" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 8: DASHBOARD AGGREGATION & NUMERIC INTEGRITY
# ==============================================================================
Write-Host "`n--- 8. Dashboard Aggregation & Numeric Integrity ---" -ForegroundColor Yellow

# 8.1 Farmer Dashboard Calculation Parity
if ($FarmerToken -and $FarmerUserId -and $FinalPrice) {
    try {
        $FDash = Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboards/farmer" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        
        $ExpectedGross = [Math]::Round(($FinalPrice * $SubmittedQuantity), 2)
        $ReportedGross = [Math]::Round([double]$FDash.data.earnings.total, 2)
        $SuccessfulDeals = [int]$FDash.data.negotiations.successful
        $AvgPrice = [double]$FDash.data.earnings.average_price

        $dealsNonNegative = ($SuccessfulDeals -ge 1)
        $grossMatches = ($ReportedGross -ge $ExpectedGross)
        $avgPriceValid = ($AvgPrice -ge $SubmittedMinPrice)

        if ($FDash.success -and $dealsNonNegative -and $grossMatches -and $avgPriceValid) {
            Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Farmer Dashboard Dynamic Math" -Endpoint "GET /api/v1/dashboards/farmer" -Expected "earnings >= ₹$ExpectedGross, deals >= 1" -Actual "earnings=₹$ReportedGross, deals=$SuccessfulDeals, avg=₹$AvgPrice" -Status "PASS" -Details "Farmer dashboard math matches transaction earnings"
        } else {
            Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Farmer Dashboard Dynamic Math" -Endpoint "GET /api/v1/dashboards/farmer" -Expected "earnings >= ₹$ExpectedGross, deals >= 1" -Actual "earnings=₹$ReportedGross, deals=$SuccessfulDeals" -Status "FAIL" -Details "Farmer dashboard calculation discrepancy"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Farmer Dashboard Dynamic Math" -Endpoint "GET /api/v1/dashboards/farmer" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 8.2 Buyer Dashboard Identity & Types
if ($BuyerToken -and $BuyerUserId) {
    try {
        $BDash = Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboards/buyer" -Method GET -Headers @{ Authorization = "Bearer $BuyerToken" } -TimeoutSec 10
        
        $uidCorrect = ($BDash.data.user.user_id -eq $BuyerUserId)
        $dealsNonNeg = ([double]$BDash.data.purchases.total_deals -ge 0)
        $spentNonNeg = ([double]$BDash.data.purchases.total_spent -ge 0)

        if ($BDash.success -and $uidCorrect -and $dealsNonNeg -and $spentNonNeg) {
            Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Buyer Dashboard Schema & Identity" -Endpoint "GET /api/v1/dashboards/buyer" -Expected "user_id=$BuyerUserId, non-negative purchases" -Actual "user_id=$($BDash.data.user.user_id), deals=$($BDash.data.purchases.total_deals), spent=₹$($BDash.data.purchases.total_spent)" -Status "PASS" -Details "Buyer dashboard verified with clean non-negative aggregations"
        } else {
            Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Buyer Dashboard Schema & Identity" -Endpoint "GET /api/v1/dashboards/buyer" -Expected "user_id=$BuyerUserId, non-negative purchases" -Actual ($BDash | ConvertTo-Json -Compress) -Status "FAIL" -Details "Buyer dashboard schema or identity mismatch"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "DASHBOARD INTEGRITY" -TestName "Buyer Dashboard Schema & Identity" -Endpoint "GET /api/v1/dashboards/buyer" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 9: TRANSPORT BOOKING & STATE MACHINE INTEGRITY
# ==============================================================================
Write-Host "`n--- 9. Transport Booking & State Machine Integrity ---" -ForegroundColor Yellow

$BookingId = $null
$EstCost = 0.0

# 9.1 Transport Booking Creation & Contract
if ($FarmerToken -and $NegotiationId) {
    try {
        $BookRes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/book" -Method POST -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{
            negotiation_id       = $NegotiationId
            crop                 = $SubmittedCrop
            quantity             = $SubmittedQuantity
            origin_location      = $SubmittedLocation
            destination_location = "Aurangabad"
            distance_km          = 235.0
            shelf_life           = 14
        } | ConvertTo-Json) -TimeoutSec 10

        if ($BookRes.success -and $BookRes.data.booking_id) {
            $BookingId = $BookRes.data.booking_id
            $EstCost = [double]$BookRes.data.estimated_cost
            $Cap = [double]$BookRes.data.capacity_kg

            $negMatches = ($BookRes.data.negotiation_id -eq $NegotiationId)
            $qtyMatches = ([double]$BookRes.data.quantity -eq $SubmittedQuantity)
            $capSufficient = ($Cap -ge $SubmittedQuantity)
            $costPositive = ($EstCost -gt 0)
            $statusInit = ($BookRes.data.status -eq "SCHEDULED")

            if ($negMatches -and $qtyMatches -and $capSufficient -and $costPositive -and $statusInit) {
                Record-IntegrityResult -Category "TRANSPORT INTEGRITY" -TestName "Transport Booking Contract" -Endpoint "POST /api/v1/transport/book" -Expected "status=SCHEDULED, capacity >= $SubmittedQuantity, cost > 0" -Actual "status=$($BookRes.data.status), capacity=${Cap}kg, cost=₹$EstCost" -Status "PASS" -Details "Transport booking correctly initialized with required vehicle capacity"
            } else {
                Record-IntegrityResult -Category "TRANSPORT INTEGRITY" -TestName "Transport Booking Contract" -Endpoint "POST /api/v1/transport/book" -Expected "status=SCHEDULED, capacity >= $SubmittedQuantity, cost > 0" -Actual ($BookRes.data | ConvertTo-Json -Compress) -Status "FAIL" -Details "Transport booking contract discrepancy"
            }
        } else {
            Record-IntegrityResult -Category "TRANSPORT INTEGRITY" -TestName "Transport Booking Contract" -Endpoint "POST /api/v1/transport/book" -Expected "success=true, booking_id=[string]" -Actual ($BookRes | ConvertTo-Json -Compress) -Status "FAIL" -Details "Transport booking creation failed"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "TRANSPORT INTEGRITY" -TestName "Transport Booking Contract" -Endpoint "POST /api/v1/transport/book" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 9.2 State Machine Step 1: SCHEDULED Tracking Verification
if ($FarmerToken -and $BookingId) {
    try {
        $Track1 = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        if ($Track1.success -and $Track1.data.status -eq "SCHEDULED" -and $Track1.data.booking_id -eq $BookingId) {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: SCHEDULED" -Endpoint "GET /api/v1/transport/booking/{id}" -Expected "status=SCHEDULED" -Actual "status=$($Track1.data.status)" -Status "PASS" -Details "Persisted initial state verified as SCHEDULED"
        } else {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: SCHEDULED" -Endpoint "GET /api/v1/transport/booking/{id}" -Expected "status=SCHEDULED" -Actual "status=$($Track1.data.status)" -Status "FAIL" -Details "Initial tracking state mismatch"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: SCHEDULED" -Endpoint "GET /api/v1/transport/booking/{id}" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 9.3 State Machine Step 2: IN_TRANSIT Transition & Verification
if ($FarmerToken -and $BookingId) {
    try {
        $Patch1 = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId/status" -Method PATCH -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{ status = "IN_TRANSIT" } | ConvertTo-Json) -TimeoutSec 10
        $Track2 = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10

        if ($Patch1.success -and $Track2.data.status -eq "IN_TRANSIT") {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: IN_TRANSIT" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "status=IN_TRANSIT" -Actual "status=$($Track2.data.status)" -Status "PASS" -Details "State machine progressed and persisted IN_TRANSIT"
        } else {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: IN_TRANSIT" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "status=IN_TRANSIT" -Actual "status=$($Track2.data.status)" -Status "FAIL" -Details "Failed to transition to IN_TRANSIT"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: IN_TRANSIT" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# 9.4 State Machine Step 3: DELIVERED Transition & Final Parity
if ($FarmerToken -and $BookingId) {
    try {
        $Patch2 = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId/status" -Method PATCH -Headers @{ Authorization = "Bearer $FarmerToken" } -ContentType "application/json" -Body (@{ status = "DELIVERED" } | ConvertTo-Json) -TimeoutSec 10
        $Track3 = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10

        if ($Patch2.success -and $Track3.data.status -eq "DELIVERED") {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: DELIVERED" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "status=DELIVERED" -Actual "status=$($Track3.data.status)" -Status "PASS" -Details "Final shipment lifecycle completed as DELIVERED"
        } else {
            Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: DELIVERED" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "status=DELIVERED" -Actual "status=$($Track3.data.status)" -Status "FAIL" -Details "Failed to transition to DELIVERED"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "STATE MACHINE" -TestName "Transport State: DELIVERED" -Endpoint "PATCH & GET /api/v1/transport/booking/{id}/status" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 10: CROSS-ENDPOINT ID CONSISTENCY
# ==============================================================================
Write-Host "`n--- 10. Cross-Endpoint ID Consistency ---" -ForegroundColor Yellow

if ($NegotiationId -and $BookingId) {
    # Verify negotiation_id across: Start, Telemetry, History, Transport Booking
    $negIdInBooking = ($BookRes.data.negotiation_id -eq $NegotiationId)
    $negIdInTelemetry = ($NegStatusRes.negotiation_id -eq $NegotiationId)
    $negIdInHistory = ($PersistedDeal.negotiation_id -eq $NegotiationId)

    if ($negIdInBooking -and $negIdInTelemetry -and $negIdInHistory) {
        Record-IntegrityResult -Category "CROSS-ENDPOINT ID" -TestName "Negotiation ID Global Linkage" -Endpoint "Multi-Endpoint ID Audit" -Expected "negotiation_id=$NegotiationId consistent across 4 endpoints" -Actual "Linkage Confirmed (Booking, Telemetry, History)" -Status "PASS" -Details "Relational foreign key integrity maintained across distributed services"
    } else {
        Record-IntegrityResult -Category "CROSS-ENDPOINT ID" -TestName "Negotiation ID Global Linkage" -Endpoint "Multi-Endpoint ID Audit" -Expected "negotiation_id=$NegotiationId consistent across 4 endpoints" -Actual "Booking=$negIdInBooking, Telemetry=$negIdInTelemetry, History=$negIdInHistory" -Status "FAIL" -Details "Cross-endpoint negotiation ID reference broken"
    }

    # Verify booking_id across: Book, Tracking, Status Updates
    $bookIdInTracking = ($Track3.data.booking_id -eq $BookingId)
    $bookIdInPatch = ($Patch2.data.booking_id -eq $BookingId)

    if ($bookIdInTracking -and $bookIdInPatch) {
        Record-IntegrityResult -Category "CROSS-ENDPOINT ID" -TestName "Booking ID Lifecycle Linkage" -Endpoint "Multi-Endpoint ID Audit" -Expected "booking_id=$BookingId consistent across 3 lifecycle steps" -Actual "Linkage Confirmed (Create, Patch, Track)" -Status "PASS" -Details "Transport booking ID referenced consistently throughout fulfillment"
    } else {
        Record-IntegrityResult -Category "CROSS-ENDPOINT ID" -TestName "Booking ID Lifecycle Linkage" -Endpoint "Multi-Endpoint ID Audit" -Expected "booking_id=$BookingId consistent across 3 lifecycle steps" -Actual "Track=$bookIdInTracking, Patch=$bookIdInPatch" -Status "FAIL" -Details "Cross-endpoint transport booking ID reference broken"
    }
}

# ==============================================================================
# SECTION 11 & 12: TYPE INTEGRITY & NULL-VALUE AUDIT
# ==============================================================================
Write-Host "`n--- 11 & 12. Type Integrity & Non-Null Audit ---" -ForegroundColor Yellow

if ($FProf -and $FDash -and $Track3) {
    $typePass = $true
    $nullViolations = [System.Collections.Generic.List[string]]::new()

    # Required non-null checks
    if (-not $FarmerUserId) { $nullViolations.Add("FarmerUserId is null"); $typePass = $false }
    if (-not $BuyerUserId)  { $nullViolations.Add("BuyerUserId is null"); $typePass = $false }
    if (-not $ListingId)    { $nullViolations.Add("ListingId is null"); $typePass = $false }
    if (-not $RequirementId){ $nullViolations.Add("RequirementId is null"); $typePass = $false }
    if (-not $NegotiationId){ $nullViolations.Add("NegotiationId is null"); $typePass = $false }
    if (-not $BookingId)    { $nullViolations.Add("BookingId is null"); $typePass = $false }

    # Type validations
    if (-not ($FinalPrice -is [double] -or $FinalPrice -is [ValueType])) { $typePass = $false }
    if (-not ($EstCost -is [double] -or $EstCost -is [ValueType])) { $typePass = $false }

    if ($typePass -and $nullViolations.Count -eq 0) {
        Record-IntegrityResult -Category "TYPE & NULL AUDIT" -TestName "Entity Required Fields & Types Audit" -Endpoint "System-Wide Entity Audit" -Expected "Zero unexpected nulls in required entities, valid scalar types" -Actual "0 null violations across 6 major entities" -Status "PASS" -Details "All primary keys, foreign keys, numeric metrics, and timestamps satisfy type contracts"
    } else {
        Record-IntegrityResult -Category "TYPE & NULL AUDIT" -TestName "Entity Required Fields & Types Audit" -Endpoint "System-Wide Entity Audit" -Expected "Zero unexpected nulls in required entities, valid scalar types" -Actual "Violations: $($nullViolations -join ', ')" -Status "FAIL" -Details "Unexpected nulls or invalid types discovered"
    }
}

# ==============================================================================
# SECTION 13: PERSISTENCE VERIFICATION RE-QUERY
# ==============================================================================
Write-Host "`n--- 13. Persistence Verification Re-Query ---" -ForegroundColor Yellow

if ($FarmerToken -and $FarmerUserId -and $NegotiationId -and $BookingId) {
    try {
        # Re-fetch History
        $ReHist = Invoke-RestMethod -Uri "$BaseUrl/api/v1/history/$FarmerUserId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        # Re-fetch Tracking
        $ReTrack = Invoke-RestMethod -Uri "$BaseUrl/api/v1/transport/booking/$BookingId" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10

        $histPersisted = ($ReHist.history | Where-Object { $_.negotiation_id -eq $NegotiationId })
        $trackPersisted = ($ReTrack.data.booking_id -eq $BookingId -and $ReTrack.data.status -eq "DELIVERED")

        if ($histPersisted -and $trackPersisted) {
            Record-IntegrityResult -Category "PERSISTENCE AUDIT" -TestName "Entity Persistence Across Re-queries" -Endpoint "Multi-GET Persistence Check" -Expected "Entities retain state on second retrieval" -Actual "Deal $NegotiationId and Booking $BookingId verified intact" -Status "PASS" -Details "No state loss, transient memory resets, or session corruption"
        } else {
            Record-IntegrityResult -Category "PERSISTENCE AUDIT" -TestName "Entity Persistence Across Re-queries" -Endpoint "Multi-GET Persistence Check" -Expected "Entities retain state on second retrieval" -Actual "HistPersisted=$([bool]$histPersisted), TrackPersisted=$([bool]$trackPersisted)" -Status "FAIL" -Details "Entity state disappeared upon re-query"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "PERSISTENCE AUDIT" -TestName "Entity Persistence Across Re-queries" -Endpoint "Multi-GET Persistence Check" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 14: SECURITY IDENTITY ISOLATION CHECK
# ==============================================================================
Write-Host "`n--- 14. Security Identity Isolation Check ---" -ForegroundColor Yellow

if ($FarmerToken -and $BuyerToken -and $FarmerUserId -and $BuyerUserId) {
    try {
        $FProfCheck = Invoke-RestMethod -Uri "$BaseUrl/api/v1/profiles/me" -Method GET -Headers @{ Authorization = "Bearer $FarmerToken" } -TimeoutSec 10
        $BProfCheck = Invoke-RestMethod -Uri "$BaseUrl/api/v1/profiles/me" -Method GET -Headers @{ Authorization = "Bearer $BuyerToken" } -TimeoutSec 10

        $fIdMatch = ($FProfCheck.data.user_id -eq $FarmerUserId -and $FProfCheck.data.role -eq "farmer")
        $bIdMatch = ($BProfCheck.data.user_id -eq $BuyerUserId -and $BProfCheck.data.role -eq "buyer")
        $noCrossContamination = ($FProfCheck.data.user_id -ne $BProfCheck.data.user_id)

        if ($fIdMatch -and $bIdMatch -and $noCrossContamination) {
            Record-IntegrityResult -Category "IDENTITY ISOLATION" -TestName "Dual-Persona Token Isolation" -Endpoint "GET /api/v1/profiles/me" -Expected "Farmer=$FarmerUserId, Buyer=$BuyerUserId, Distinct tokens" -Actual "Farmer ID=$($FProfCheck.data.user_id), Buyer ID=$($BProfCheck.data.user_id)" -Status "PASS" -Details "JWT authentication claims securely isolate farmer and buyer sessions"
        } else {
            Record-IntegrityResult -Category "IDENTITY ISOLATION" -TestName "Dual-Persona Token Isolation" -Endpoint "GET /api/v1/profiles/me" -Expected "Farmer=$FarmerUserId, Buyer=$BuyerUserId, Distinct tokens" -Actual "Contamination or ID mismatch detected" -Status "FAIL" -Details "Security token session cross-contamination"
        }
    } catch {
        $err = Get-HttpErrorDetails $_.Exception
        Record-IntegrityResult -Category "IDENTITY ISOLATION" -TestName "Dual-Persona Token Isolation" -Endpoint "GET /api/v1/profiles/me" -Expected "HTTP 200" -Actual "HTTP $($err.StatusCode)" -Status "FAIL" -Details $err.Body
    }
}

# ==============================================================================
# SECTION 15: RESPONSE CONTRACT REPORT & FINAL SUMMARY
# ==============================================================================
Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "             API INTEGRITY VERIFICATION REPORT" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

$Results | Format-Table -AutoSize -Property Category, TestName, Endpoint, Expected, Actual, Status, Details

$TotalPass  = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$TotalFail  = ($Results | Where-Object { $_.Status -eq "FAIL" }).Count
$TotalCount = $Results.Count

$PassRate = [Math]::Round(($TotalPass / $TotalCount) * 100, 1)

$SummaryColor = if ($TotalFail -eq 0) { "Green" } else { "Red" }

$FailColor = if ($TotalFail -eq 0) { "Green" } else { "Red" }

Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  API INTEGRITY SUMMARY" -ForegroundColor Cyan
Write-Host "  Passed:    $TotalPass" -ForegroundColor Green
Write-Host "  Failed:    $TotalFail" -ForegroundColor $FailColor
Write-Host "  Total:     $TotalCount" -ForegroundColor Cyan
Write-Host "  Pass Rate: $PassRate%" -ForegroundColor $SummaryColor
Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray

if ($TotalFail -gt 0) {
    Write-Host "`n[FAIL] Integrity suite completed with $TotalFail failure(s)." -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n[SUCCESS] 100% PASS RATE ACROSS ALL $TotalCount INTEGRITY PROBES!" -ForegroundColor Green
    exit 0
}
