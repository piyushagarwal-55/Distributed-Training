# 🚀 Monad Deployment - Quick Start

## Your Configuration (From MetaMask Screenshot)

✅ **Network:** Monad Testnet  
✅ **RPC URL:** https://testnet-rpc.monad.xyz  
✅ **Chain ID:** 10143  
✅ **Symbol:** MON  
✅ **Explorer:** https://testnet.monadexplorer.com  
✅ **Your Address:** 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA  
✅ **Your Balance:** 0.501 MON (seen in screenshot)

## ✅ What We've Done

1. **Contracts Compiled Successfully** ✅
   - TrainingRegistry.sol
   - ContributionTracker.sol
   - RewardDistributor.sol
   - All OpenZeppelin v5 compatibility fixes applied

2. **Configuration Set** ✅
   - hardhat.config.js updated with Chain ID 10143
   - .env file created with your private key
   - RPC URL configured: https://testnet-rpc.monad.xyz

3. **Ready to Deploy** ✅
   - You have 0.501 MON (sufficient for deployment)
   - All scripts created (deploy, test, verify)

## 🚀 Deploy NOW

### Step 1: Deploy Contracts
```bash
cd C:\Users\LENOVO\Desktop\lnmhacks1\smart-contracts
npx hardhat run scripts/deploy.js --network monad_testnet
```

**Expected Output:**
```
🚀 Deploying Distributed ML Smart Contracts...

Deploying with account: 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA
Account balance: 501000000000000000

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
  "timestamp": "2025-12-24T...",
  "contracts": {
    "TrainingRegistry": "0x...",
    "ContributionTracker": "0x...",
    "RewardDistributor": "0x..."
  }
}

💾 Deployment info saved to: ./deployments/monad_testnet_deployment.json
✨ Deployment completed successfully!
```

### Step 2: Verify Deployment
```bash
node scripts/verify-deployment.js
```

### Step 3: Test Contracts
```bash
node scripts/test-deployment.js
```

This will:
- Register a training session
- Record a contribution  
- Fund the reward distributor
- Check balances and verify all functions work

## 📱 Check in MetaMask

After deployment, check MetaMask Activity tab:
- You should see 3 contract creation transactions
- Each will have a "Contract Deployment" label
- Total gas fees: ~0.01-0.05 MON

## 🔗 View on Block Explorer

Visit: https://testnet.monadexplorer.com/address/0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA

You'll see:
- Your 3 contract deployment transactions
- Contract addresses created
- Gas fees paid
- Transaction history

## 📝 Contract Addresses (After Deployment)

The addresses will be saved in:
`smart-contracts/deployments/monad_testnet_deployment.json`

Format:
```json
{
  "network": "monad_testnet",
  "deployer": "0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA",
  "timestamp": "2025-12-24T...",
  "contracts": {
    "TrainingRegistry": "0x...",
    "ContributionTracker": "0x...",
    "RewardDistributor": "0x..."
  }
}
```

## 🔄 Update Frontend

After deployment, update `frontend/src/lib/store.ts`:

```typescript
// Add at top of file
export const CONTRACT_ADDRESSES = {
  TrainingRegistry: "0x...", // Copy from deployment.json
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

## ❌ If Faucet Needed

If you don't have MON tokens:

1. **Join Monad Discord:** https://discord.gg/monad
2. **Go to #faucet channel**
3. **Use command:**
   ```
   /faucet 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA
   ```
4. **Wait 1-2 minutes** for tokens to arrive
5. **Check balance** in MetaMask

## 🐛 Troubleshooting

### "Insufficient funds"
- Get more MON from faucet
- Need at least 0.05 MON for deployment

### "Network connection error"
- Check RPC URL: https://testnet-rpc.monad.xyz
- Try without /faucet path at end
- Verify Monad testnet is online

### "Nonce too high"
- Reset MetaMask account:
  - Settings → Advanced → Clear activity tab data
  - Settings → Advanced → Reset account

### "Transaction underpriced"
- Increase gas price in hardhat.config.js:
  ```javascript
  monad_testnet: {
    url: "https://testnet-rpc.monad.xyz",
    accounts: [process.env.PRIVATE_KEY],
    chainId: 10143,
    gasPrice: 20000000000 // 20 gwei
  }
  ```

## ✅ Success Checklist

- [ ] Contracts compiled (3 contracts)
- [ ] Account has MON balance (>0.05 MON)
- [ ] Deployment completed (3 contract addresses)
- [ ] Transactions visible in MetaMask
- [ ] Deployment JSON file created
- [ ] Contracts verified on explorer
- [ ] Test script passed
- [ ] Frontend updated with addresses

## 🎯 Next Steps After Deployment

1. **Save contract addresses** - Copy from deployment JSON
2. **Update frontend** - Add addresses to store.ts
3. **Test MetaMask connection** - Connect frontend to Monad
4. **Test contract calls** - Try registering session from frontend
5. **Integrate backend** - Connect Python service to contracts
6. **Full system test** - Run complete ML training workflow

## 📞 Support

- **Monad Discord:** https://discord.gg/monad
- **Monad Docs:** https://docs.monad.xyz
- **Monad Twitter:** @monad_xyz
- **Block Explorer:** https://testnet.monadexplorer.com

---

**Ready to deploy? Run the command above!** 🚀
