const hre = require("hardhat");

async function main() {
  console.log("🔍 Checking account balance on Monad Testnet...\n");
  
  const [signer] = await hre.ethers.getSigners();
  console.log("Account:", signer.address);
  
  try {
    const balance = await signer.provider.getBalance(signer.address);
    console.log("Balance:", hre.ethers.formatEther(balance), "MON");
    console.log("Balance (wei):", balance.toString());
    
    if (balance === 0n) {
      console.log("\n❌ No balance found!");
      console.log("\n💡 Get testnet tokens from:");
      console.log("   1. Discord: https://discord.gg/monad - Use /faucet command");
      console.log("   2. Website: https://testnet.monad.xyz/faucet");
      console.log("   3. Ask in Monad Discord #faucet channel");
      console.log("\n   Your address: " + signer.address);
    } else if (balance < hre.ethers.parseEther("0.1")) {
      console.log("\n⚠️  Low balance! Deployment may fail.");
      console.log("   Recommended: At least 0.1 MON for gas fees");
      console.log("   Get more tokens from faucet");
    } else {
      console.log("\n✅ Sufficient balance for deployment!");
    }
    
  } catch (error) {
    console.error("\n❌ Error checking balance:", error.message);
    if (error.code === 'NETWORK_ERROR') {
      console.log("\n💡 Network connection issue. Check:");
      console.log("   1. RPC URL is correct: https://testnet-rpc.monad.xyz");
      console.log("   2. Monad testnet is online");
      console.log("   3. Internet connection is stable");
    }
  }
}

main().catch(console.error);
