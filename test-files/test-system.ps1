# Complete System End-to-End Test Script
# Tests: Backend API, Frontend, Blockchain, WebSocket, Training Workflow

Write-Host "🧪 Starting Complete System End-to-End Tests" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

$ErrorActionPreference = "Continue"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    Write-Host "Testing: $Name" -NoNewline
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host " ✅ PASS" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host " ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    return $false
}

function Wait-ForService {
    param(
        [string]$Name,
        [string]$Url,
        [int]$MaxAttempts = 30
    )
    
    Write-Host "⏳ Waiting for $Name to be ready..." -NoNewline
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host " ✅ Ready!" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 1
        }
    }
    Write-Host " ❌ Timeout!" -ForegroundColor Red
    return $false
}

# ============================================================================
# 1. CHECK IF SERVICES ARE RUNNING
# ============================================================================
Write-Host "`n📡 PHASE 1: Service Availability Check" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

# Check Backend
if (Wait-ForService "Backend API" "http://localhost:8000/health") {
    $testsPassed++
} else {
    $testsFailed++
    Write-Host "❌ Backend not running. Start with: npm run dev:backend" -ForegroundColor Red
}

# Check Frontend
if (Wait-ForService "Frontend" "http://localhost:3000") {
    $testsPassed++
} else {
    $testsFailed++
    Write-Host "⚠️  Frontend not running. Start with: npm run dev:frontend" -ForegroundColor Yellow
}

# ============================================================================
# 2. BACKEND API TESTS
# ============================================================================
Write-Host "`n🔧 PHASE 2: Backend API Tests" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

$backendTests = @(
    @{ Name="Health Check"; Url="http://localhost:8000/health" }
    @{ Name="Root Endpoint"; Url="http://localhost:8000/" }
    @{ Name="API Status"; Url="http://localhost:8000/api/status" }
    @{ Name="Get Nodes"; Url="http://localhost:8000/api/nodes" }
    @{ Name="Get Metrics"; Url="http://localhost:8000/api/training/metrics" }
    @{ Name="API Docs"; Url="http://localhost:8000/docs" }
)

foreach ($test in $backendTests) {
    if (Test-Endpoint @test) {
        $testsPassed++
    } else {
        $testsFailed++
    }
}

# ============================================================================
# 3. WEBSOCKET TEST
# ============================================================================
Write-Host "`n🔌 PHASE 3: WebSocket Connection Test" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

Write-Host "Testing: WebSocket Connection" -NoNewline
try {
    $ws = New-Object System.Net.WebSockets.ClientWebSocket
    $uri = [System.Uri]::new("ws://localhost:8000/ws")
    $cts = New-Object System.Threading.CancellationTokenSource
    $task = $ws.ConnectAsync($uri, $cts.Token)
    
    $timeout = [TimeSpan]::FromSeconds(5)
    if ($task.Wait($timeout)) {
        Write-Host " ✅ PASS" -ForegroundColor Green
        $testsPassed++
        $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Test complete", $cts.Token).Wait()
    } else {
        Write-Host " ❌ FAIL - Connection timeout" -ForegroundColor Red
        $testsFailed++
    }
    $ws.Dispose()
    $cts.Dispose()
} catch {
    Write-Host " ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================================================
# 4. BLOCKCHAIN INTEGRATION TEST
# ============================================================================
Write-Host "`n⛓️  PHASE 4: Blockchain Integration Test" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

# Check if blockchain is configured
try {
    $configPath = ".\python-ml-service\configs\default.json"
    $config = Get-Content $configPath | ConvertFrom-Json
    
    Write-Host "Checking: Blockchain Configuration" -NoNewline
    if ($config.blockchain.enabled -and $config.blockchain.training_registry_address) {
        Write-Host " ✅ PASS" -ForegroundColor Green
        $testsPassed++
        
        Write-Host "  📋 Contract Addresses:" -ForegroundColor Cyan
        Write-Host "    TrainingRegistry:      $($config.blockchain.training_registry_address)" -ForegroundColor Gray
        Write-Host "    ContributionTracker:   $($config.blockchain.contribution_tracker_address)" -ForegroundColor Gray
        Write-Host "    RewardDistributor:     $($config.blockchain.reward_distributor_address)" -ForegroundColor Gray
    } else {
        Write-Host " ⚠️  WARN - Blockchain disabled" -ForegroundColor Yellow
        $testsFailed++
    }
} catch {
    Write-Host " ❌ FAIL - Cannot read config" -ForegroundColor Red
    $testsFailed++
}

# ============================================================================
# 5. TRAINING WORKFLOW TEST
# ============================================================================
Write-Host "`n🎯 PHASE 5: Training Workflow Test" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

Write-Host "Test 1: Register Test Node" -NoNewline
try {
    $nodeBody = @{
        node_id = "test-node-e2e-$(Get-Random)"
        address = "192.168.1.100:8000"
        gpu_specs = @{
            model = "RTX 4090"
            memory_gb = 24
            compute_capability = "8.9"
        }
        status = "idle"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/nodes/register" -Method POST -Body ($nodeBody | ConvertTo-Json) -ContentType "application/json"
    Write-Host " ✅ PASS (Node ID: $($response.node_id))" -ForegroundColor Green
    $testNodeId = $response.node_id
    $testsPassed++
} catch {
    Write-Host " ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    $testNodeId = $null
}

Write-Host "Test 2: Start Training Session" -NoNewline
try {
    $trainingBody = @{
        model_name = "simple_cnn"
        dataset = "mnist"
        epochs = 2
        batch_size = 32
        learning_rate = 0.001
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/training/start" -Method POST -Body ($trainingBody | ConvertTo-Json) -ContentType "application/json"
    Write-Host " ✅ PASS (Session started)" -ForegroundColor Green
    $testsPassed++
    $trainingStarted = $true
} catch {
    Write-Host " ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    $trainingStarted = $false
}

# Wait a bit for training to start
if ($trainingStarted) {
    Start-Sleep -Seconds 3
    
    Write-Host "Test 3: Check Training Status" -NoNewline
    try {
        $status = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -Method GET
        if ($status.is_training) {
            Write-Host " ✅ PASS (Training active)" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host " ⚠️  WARN (Training not active)" -ForegroundColor Yellow
            $testsFailed++
        }
    } catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        $testsFailed++
    }
    
    Write-Host "Test 4: Get Training Metrics" -NoNewline
    try {
        $metrics = Invoke-RestMethod -Uri "http://localhost:8000/api/training/metrics" -Method GET
        Write-Host " ✅ PASS (Metrics retrieved)" -ForegroundColor Green
        $testsPassed++
    } catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        $testsFailed++
    }
    
    Write-Host "Test 5: Stop Training" -NoNewline
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/training/stop" -Method POST
        Write-Host " ✅ PASS (Training stopped)" -ForegroundColor Green
        $testsPassed++
    } catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        $testsFailed++
    }
}

# Cleanup: Unregister test node
if ($testNodeId) {
    Write-Host "Test 6: Cleanup Test Node" -NoNewline
    try {
        Invoke-RestMethod -Uri "http://localhost:8000/api/nodes/$testNodeId" -Method DELETE
        Write-Host " ✅ PASS (Node removed)" -ForegroundColor Green
        $testsPassed++
    } catch {
        Write-Host " ⚠️  WARN (Cleanup failed)" -ForegroundColor Yellow
    }
}

# ============================================================================
# 6. SYSTEM INFORMATION
# ============================================================================
Write-Host "`n📊 PHASE 6: System Information" -ForegroundColor Yellow
Write-Host "-" * 60 -ForegroundColor Gray

try {
    $systemStatus = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -Method GET
    Write-Host "System Status:" -ForegroundColor Cyan
    Write-Host "  Training Active:   $($systemStatus.is_training)" -ForegroundColor Gray
    Write-Host "  Current Epoch:     $($systemStatus.current_epoch)" -ForegroundColor Gray
    Write-Host "  Total Nodes:       $($systemStatus.num_nodes)" -ForegroundColor Gray
    Write-Host "  Active Nodes:      $($systemStatus.active_nodes)" -ForegroundColor Gray
    Write-Host "  Blockchain:        $($systemStatus.blockchain_connected)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Could not retrieve system status" -ForegroundColor Yellow
}

# ============================================================================
# FINAL RESULTS
# ============================================================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
Write-Host "📋 TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

$totalTests = $testsPassed + $testsFailed
$passRate = if ($totalTests -gt 0) { [math]::Round(($testsPassed / $totalTests) * 100, 1) } else { 0 }

Write-Host ""
Write-Host "  Total Tests:    $totalTests" -ForegroundColor White
Write-Host "  Tests Passed:   $testsPassed" -ForegroundColor Green
Write-Host "  Tests Failed:   $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host "  Pass Rate:      $passRate%" -ForegroundColor $(if ($passRate -ge 80) { "Green" } elseif ($passRate -ge 60) { "Yellow" } else { "Red" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! System is fully operational!" -ForegroundColor Green
    exit 0
} elseif ($passRate -ge 80) {
    Write-Host "Most tests passed. System is operational with minor issues." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "Multiple tests failed. Please check the system." -ForegroundColor Red
    exit 1
}
