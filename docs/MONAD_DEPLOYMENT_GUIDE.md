# 🚀 Monad Testnet Deployment & Setup Guide

## 📋 Table of Contents
1. [Monad Network Information](#monad-network-information)
2. [MetaMask Setup](#metamask-setup)
3. [Get Testnet Tokens](#get-testnet-tokens)
4. [Deploy Smart Contracts](#deploy-smart-contracts)
5. [Verify Deployment](#verify-deployment)
6. [Testing](#testing)

---

## 🌐 Monad Network Information

**Monad Testnet Details:**
- **Network Name:** Monad Testnet
- **RPC URL:** `https://testnet-rpc.monad.xyz`
- **Chain ID:** `10143` (0x279F in hex)
- **Currency Symbol:** MON
- **Block Explorer:** `https://testnet.monadexplorer.com/`

**Important:** Monad is currently in private testnet phase. Public testnet access may be limited.

---

## 🦊 MetaMask Setup Guide

### Step 1: Install MetaMask
1. Download MetaMask extension from [metamask.io](https://metamask.io)
2. Install and create/import your wallet
3. **IMPORTANT:** Keep your seed phrase secure!

### Step 2: Add Monad Testnet to MetaMask

**Option A: Manual Configuration**
1. Open MetaMask
2. Click on the network dropdown (top of MetaMask)
3. Click "Add Network" or "Add network manually"
4. Enter the following details:

```
Network Name: Monad Testnet
RPC URL: https://testnet-rpc.monad.xyz
Chain ID: 10143
Currency Symbol: MON
Block Explorer URL: https://testnet.monadexplorer.com/
```

5. Click "Save"
6. Switch to Monad Testnet network

**Option B: Quick Add (if available)**
1. Visit [chainlist.org](https://chainlist.org)
2. Search for "Monad"
3. Click "Add to MetaMask"
4. Approve the connection

### Step 3: Import Your Account
1. Click on account icon (top right)
2. Select "Import Account"
3. Paste your private key: `0x61dbad316e3f6503dfde8776427a2b9b51852d8944f2be986799b53a618f1e5d`
4. Click "Import"

**Your Address:** `0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA`

---

## 💰 Get Testnet Tokens (Faucet)

### Monad Testnet Faucets

**Official Sources:**
1. **Monad Discord Faucet**
   - Join: [discord.gg/monad](https://discord.gg/monad)
   - Go to #faucet channel
   - Use command: `/faucet 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA`
   - Receive: ~1-10 MON testnet tokens

2. **Monad Official Website**
   - Visit: [monad.xyz](https://monad.xyz) or [testnet.monad.xyz](https://testnet.monad.xyz)
   - Look for "Faucet" or "Get Test Tokens" button
   - Connect MetaMask
   - Request tokens

3. **Alternative Faucets** (if available):
   - Check [faucets.chain.link](https://faucets.chain.link)
   - Search for Monad testnet
   - Connect wallet and request tokens

**Note:** Monad testnet might be in private beta. If faucets are not publicly available:
- Join Monad Discord and request access
- Apply for testnet access on their website
- Contact Monad team for testnet tokens

---

## 🔧 Deploy Smart Contracts

### Prerequisites
1. ✅ Node.js installed
2. ✅ MetaMask configured with Monad Testnet
3. ✅ Testnet MON tokens in your wallet
4. ✅ Private key ready

### Deployment Steps

#### Step 1: Create .env file
```bash
cd smart-contracts
```

Create `.env` file with:
```
PRIVATE_KEY=0x61dbad316e3f6503dfde8776427a2b9b51852d8944f2be986799b53a618f1e5d
MONAD_TESTNET_RPC=https://testnet-rpc.monad.xyz/
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Compile Contracts
```bash
npm run compile
```

Expected output:
```
Compiled 3 Solidity files successfully
```

#### Step 4: Check Your Balance
Before deploying, verify you have testnet tokens:
- Open MetaMask
- Switch to Monad Testnet
- Check balance of `0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA`
- Should have at least **0.1 MON** for gas fees

#### Step 5: Deploy to Monad Testnet
```bash
npm run deploy:testnet
```

Expected output:
```
🚀 Deploying Distributed ML Smart Contracts...

Deploying with account: 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA
Account balance: 1000000000000000000

📝 Deploying TrainingRegistry...
✅ TrainingRegistry deployed to: 0x...

📝 Deploying ContributionTracker...
✅ ContributionTracker deployed to: 0x...

📝 Deploying RewardDistributor...
✅ RewardDistributor deployed to: 0x...

📋 Deployment Summary:
{
  "network": "monad_testnet",
  "deployer": "0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA",
  "contracts": {
    "TrainingRegistry": "0x...",
    "ContributionTracker": "0x...",
    "RewardDistributor": "0x..."
  }
}

💾 Deployment info saved to: ./deployments/monad_testnet_deployment.json
✨ Deployment completed successfully!
```

#### Step 6: Save Contract Addresses
The deployment script automatically saves addresses to:
`smart-contracts/deployments/monad_testnet_deployment.json`

---

## ✅ Verify Deployment

### Method 1: Block Explorer
1. Visit [https://testnet.monadexplorer.com/](https://testnet.monadexplorer.com/)
2. Search for each contract address
3. Verify:
   - Contract creation transaction successful
   - Contract code is present
   - No errors in transaction

### Method 2: Etherscan-style Verification (if supported)
```bash
npx hardhat verify --network monad_testnet <CONTRACT_ADDRESS>
```

### Method 3: Check via Script
Create `scripts/verify-deployment.js`:
```javascript
const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const deploymentFile = `./deployments/${hre.network.name}_deployment.json`;
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  console.log("🔍 Verifying deployment...\n");
  
  const [signer] = await hre.ethers.getSigners();
  
  // Check TrainingRegistry
  const registry = await hre.ethers.getContractAt(
    "TrainingRegistry",
    deployment.contracts.TrainingRegistry
  );
  console.log("✅ TrainingRegistry is accessible");
  
  // Check ContributionTracker
  const tracker = await hre.ethers.getContractAt(
    "ContributionTracker",
    deployment.contracts.ContributionTracker
  );
  console.log("✅ ContributionTracker is accessible");
  
  // Check RewardDistributor
  const distributor = await hre.ethers.getContractAt(
    "RewardDistributor",
    deployment.contracts.RewardDistributor
  );
  console.log("✅ RewardDistributor is accessible");
  
  console.log("\n✨ All contracts verified successfully!");
}

main().catch(console.error);
```

Run verification:
```bash
node scripts/verify-deployment.js
```

---

## 🧪 Testing Deployment

### Test 1: Basic Contract Interaction

Create `scripts/test-deployment.js`:
```javascript
const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🧪 Testing deployed contracts...\n");
  
  const deploymentFile = `./deployments/${hre.network.name}_deployment.json`;
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  const [signer] = await hre.ethers.getSigners();
  console.log("Testing with account:", signer.address);
  console.log("Balance:", await signer.provider.getBalance(signer.address), "wei\n");
  
  // Test TrainingRegistry
  console.log("📝 Testing TrainingRegistry...");
  const registry = await hre.ethers.getContractAt(
    "TrainingRegistry",
    deployment.contracts.TrainingRegistry
  );
  
  // Register a training session
  const tx1 = await registry.registerTraining("Test Model", "MNIST", 10);
  await tx1.wait();
  console.log("✅ Training session registered");
  
  // Get session count
  const sessionCount = await registry.getSessionCount();
  console.log("📊 Total sessions:", sessionCount.toString());
  
  // Test ContributionTracker
  console.log("\n📝 Testing ContributionTracker...");
  const tracker = await hre.ethers.getContractAt(
    "ContributionTracker",
    deployment.contracts.ContributionTracker
  );
  
  // Record a contribution
  const tx2 = await tracker.recordContribution(
    0, // sessionId
    signer.address,
    100, // computeTime
    95 // qualityScore
  );
  await tx2.wait();
  console.log("✅ Contribution recorded");
  
  // Get contribution
  const contribution = await tracker.getContribution(0, signer.address);
  console.log("📊 Contribution:", {
    computeTime: contribution[0].toString(),
    qualityScore: contribution[1].toString(),
    timestamp: new Date(Number(contribution[2]) * 1000).toISOString()
  });
  
  // Test RewardDistributor
  console.log("\n📝 Testing RewardDistributor...");
  const distributor = await hre.ethers.getContractAt(
    "RewardDistributor",
    deployment.contracts.RewardDistributor
  );
  
  // Fund the distributor (send some MON)
  const fundTx = await signer.sendTransaction({
    to: deployment.contracts.RewardDistributor,
    value: hre.ethers.parseEther("0.1")
  });
  await fundTx.wait();
  console.log("✅ RewardDistributor funded with 0.1 MON");
  
  // Get balance
  const balance = await distributor.getContractBalance();
  console.log("💰 Distributor balance:", hre.ethers.formatEther(balance), "MON");
  
  console.log("\n✨ All tests passed successfully!");
}

main().catch(console.error);
```

Run tests:
```bash
node scripts/test-deployment.js
```

### Test 2: Frontend Integration

Update `frontend/src/lib/blockchain.ts` with deployed addresses:
```typescript
export const CONTRACT_ADDRESSES = {
  TrainingRegistry: "0x...", // From deployment
  ContributionTracker: "0x...",
  RewardDistributor: "0x..."
};

export const MONAD_TESTNET = {
  chainId: "0x279F", // 10143 in hex
  chainName: "Monad Testnet",
  rpcUrls: ["https://testnet-rpc.monad.xyz"],
  nativeCurrency: {
    name: "Monad",
    symbol: "MON",
    decimals: 18
  },
  blockExplorerUrls: ["https://testnet.monadexplorer.com/"]
};
```

Test MetaMask connection in browser:
```javascript
// In browser console
const { ethereum } = window;
await ethereum.request({ method: 'eth_requestAccounts' });
const chainId = await ethereum.request({ method: 'eth_chainId' });
console.log('Connected to chain:', parseInt(chainId, 16));
```

---

## 📱 MetaMask Screenshot Reference

Your MetaMask should show:
- **Network:** Monad Testnet
- **Account:** Account 1 (0x3eBA...D1cA)
- **Balance:** X.XXX MON
- **Tokens Tab:** Should be empty initially
- **Activity Tab:** Should show deployment transactions

---

## 🐛 Troubleshooting

### Issue: "Insufficient funds for gas"
**Solution:** 
- Request more testnet tokens from faucet
- Check balance in MetaMask
- Reduce gas limit in deployment script

### Issue: "Network connection error"
**Solution:**
- Check RPC URL is correct
- Try alternative RPC: `https://rpc.monad.xyz`
- Check internet connection
- Verify Monad testnet is online

### Issue: "Private key error"
**Solution:**
- Ensure .env file exists in smart-contracts folder
- Verify private key format (starts with 0x)
- Check no extra spaces in .env file

### Issue: "Contract deployment failed"
**Solution:**
- Check account has sufficient balance (>0.1 MON)
- Verify contracts compile without errors
- Check network is set to monad_testnet
- Review transaction error in block explorer

---

## 📝 Post-Deployment Checklist

- [ ] All 3 contracts deployed successfully
- [ ] Deployment addresses saved to file
- [ ] Contracts verified on block explorer
- [ ] Test transactions executed successfully
- [ ] Frontend updated with contract addresses
- [ ] MetaMask connected and showing correct network
- [ ] Document addresses in project README

---

## 🔗 Useful Links

- **Monad Website:** [https://monad.xyz](https://monad.xyz)
- **Monad Docs:** [https://docs.monad.xyz](https://docs.monad.xyz)
- **Monad Discord:** [https://discord.gg/monad](https://discord.gg/monad)
- **Monad Twitter:** [@monad_xyz](https://twitter.com/monad_xyz)
- **Block Explorer:** [https://testnet.monadexplorer.com](https://testnet.monadexplorer.com)
- **MetaMask Support:** [https://support.metamask.io](https://support.metamask.io)

---

## ⚠️ Security Reminders

1. **NEVER share your private key publicly**
2. Keep your seed phrase secure and offline
3. Use testnet tokens only (no real value)
4. Verify all transactions before signing
5. Double-check contract addresses
6. Backup your .env file securely

---

## 🎉 Success Indicators

Your deployment is successful when:
1. ✅ All 3 contracts deployed without errors
2. ✅ Transaction hashes visible in block explorer
3. ✅ Contract addresses saved to JSON file
4. ✅ Test interactions complete successfully
5. ✅ MetaMask shows deployment transactions
6. ✅ Balance decreased by gas fees (small amount)

**Next Steps:** Integrate contract addresses into your frontend application and start testing the full ML training workflow!
