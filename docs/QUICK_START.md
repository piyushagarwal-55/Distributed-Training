# 🎯 QUICK START - Deploy in 5 Steps

## ⚡ Fast Track to Deployment

### Step 1: Get MON Tokens (5 minutes) 🪙
```
1. Join: https://discord.gg/monad
2. Go to: #faucet channel
3. Type: /faucet 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA
4. Wait: 1-5 minutes for tokens
5. Check MetaMask: Should see 1-10 MON
```

### Step 2: Check Balance (10 seconds) ✅
```bash
cd C:\Users\LENOVO\Desktop\lnmhacks1\smart-contracts
node scripts/check-balance.js
```
**Need:** >0.5 MON

### Step 3: Deploy Contracts (1 minute) 🚀
```bash
npx hardhat run scripts/deploy.js --network monad_testnet
```
**Wait for:** 3 contract deployments (~30-60 seconds)

### Step 4: Verify (30 seconds) ✅
```bash
node scripts/verify-deployment.js
```
**Check:** All 3 contracts accessible

### Step 5: Test (1 minute) 🧪
```bash
node scripts/test-deployment.js
```
**Verify:** All functions work

---

## 📋 What You Have

✅ **Contracts:** Compiled and ready  
✅ **Config:** Chain ID 10143, correct RPC  
✅ **Scripts:** deploy, test, verify  
✅ **Account:** 0x3eBA...D1cA  
⚠️ **Balance:** 0.165 MON (need 0.5+ MON)

---

## 🎯 Your Mission

1. **NOW:** Get MON tokens from Discord
2. **THEN:** Run 3 commands above
3. **DONE:** Contracts deployed!

---

## 📝 Contract Addresses (After Deployment)

Check file: `deployments/monad_testnet_deployment.json`

```json
{
  "TrainingRegistry": "0x...",
  "ContributionTracker": "0x...",
  "RewardDistributor": "0x..."
}
```

---

## 🔗 Important Links

- **Get Tokens:** https://discord.gg/monad
- **Explorer:** https://testnet.monadexplorer.com
- **Your Address:** https://testnet.monadexplorer.com/address/0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA
- **Monad Docs:** https://docs.monad.xyz

---

## ⚡ Commands Reference

```bash
# Check balance
node scripts/check-balance.js

# Deploy
npx hardhat run scripts/deploy.js --network monad_testnet

# Verify
node scripts/verify-deployment.js

# Test
node scripts/test-deployment.js
```

---

## 💰 Gas Costs

**Total Deployment:** ~0.25-0.4 MON  
- TrainingRegistry: ~0.05-0.1 MON
- ContributionTracker: ~0.1-0.15 MON
- RewardDistributor: ~0.1-0.15 MON

**Safe Amount:** Have 1 MON for testing

---

## 🐛 Quick Fixes

**"Insufficient funds"**  
→ Get more MON from faucet

**"Network error"**  
→ Check internet, wait 1 min, try again

**"Nonce too high"**  
→ MetaMask → Settings → Advanced → Reset account

---

## ✨ Success = 

- ✅ 3 contract addresses
- ✅ 3 transactions in MetaMask
- ✅ Contracts on block explorer
- ✅ Test script passes

---

**🔥 STEP 1: GET MON TOKENS NOW!**
**Discord: https://discord.gg/monad**
**Command: /faucet 0x3eBA27c0AF5b16498272AB7661E996bf2FF0D1cA**

Then deploy in under 2 minutes! ⚡
