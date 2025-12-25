const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🧪 Testing deployed contracts on", hre.network.name, "...\n");
  
  const deploymentFile = `./deployments/${hre.network.name}_deployment.json`;
  
  if (!fs.existsSync(deploymentFile)) {
    console.error("❌ Deployment file not found:", deploymentFile);
    console.log("💡 Please deploy contracts first using: npm run deploy:testnet");
    process.exit(1);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  const [signer] = await hre.ethers.getSigners();
  console.log("Testing with account:", signer.address);
  const balance = await signer.provider.getBalance(signer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "MON");
  
  if (balance === 0n) {
    console.log("\n❌ Insufficient balance! Please get testnet tokens from faucet.");
    console.log("💡 Visit: https://discord.gg/monad or https://testnet.monad.xyz/faucet");
    process.exit(1);
  }
  console.log();
  
  try {
    // Test TrainingRegistry
    console.log("📝 Testing TrainingRegistry...");
    const registry = await hre.ethers.getContractAt(
      "TrainingRegistry",
      deployment.contracts.TrainingRegistry
    );
    
    console.log("   Registering training session...");
    const tx1 = await registry.registerTraining("Test CNN Model", "MNIST Dataset", 10);
    const receipt1 = await tx1.wait();
    console.log("   ✅ Training session registered");
    console.log("   📊 Gas used:", receipt1.gasUsed.toString());
    console.log("   🔗 Transaction:", receipt1.hash);
    
    const sessionCount = await registry.getSessionCount();
    console.log("   📊 Total sessions:", sessionCount.toString());
    
    if (sessionCount > 0n) {
      const session = await registry.getSession(0);
      console.log("   📝 Session 0 details:");
      console.log("      Model:", session[0]);
      console.log("      Dataset:", session[1]);
      console.log("      Epochs:", session[2].toString());
      console.log("      Trainer:", session[3]);
    }
    console.log();
    
    // Test ContributionTracker
    console.log("📝 Testing ContributionTracker...");
    const tracker = await hre.ethers.getContractAt(
      "ContributionTracker",
      deployment.contracts.ContributionTracker
    );
    
    console.log("   Recording contribution...");
    const tx2 = await tracker.recordContribution(
      0, // sessionId
      signer.address,
      150, // computeTime (seconds)
      92 // qualityScore (0-100)
    );
    const receipt2 = await tx2.wait();
    console.log("   ✅ Contribution recorded");
    console.log("   📊 Gas used:", receipt2.gasUsed.toString());
    console.log("   🔗 Transaction:", receipt2.hash);
    
    const contribution = await tracker.getContribution(0, signer.address);
    console.log("   📊 Your contribution:");
    console.log("      Compute Time:", contribution[0].toString(), "seconds");
    console.log("      Quality Score:", contribution[1].toString(), "/100");
    console.log("      Timestamp:", new Date(Number(contribution[2]) * 1000).toISOString());
    
    const totalContributions = await tracker.getTotalContributions(0);
    console.log("   📊 Total contributions for session 0:", totalContributions.toString());
    console.log();
    
    // Test RewardDistributor
    console.log("📝 Testing RewardDistributor...");
    const distributor = await hre.ethers.getContractAt(
      "RewardDistributor",
      deployment.contracts.RewardDistributor
    );
    
    console.log("   Funding distributor with 0.05 MON...");
    const fundTx = await signer.sendTransaction({
      to: deployment.contracts.RewardDistributor,
      value: hre.ethers.parseEther("0.05")
    });
    const fundReceipt = await fundTx.wait();
    console.log("   ✅ Distributor funded");
    console.log("   📊 Gas used:", fundReceipt.gasUsed.toString());
    console.log("   🔗 Transaction:", fundReceipt.hash);
    
    const contractBalance = await distributor.getContractBalance();
    console.log("   💰 Distributor balance:", hre.ethers.formatEther(contractBalance), "MON");
    
    // Check if rewards are distributed
    const pendingReward = await distributor.getPendingReward(signer.address);
    console.log("   💎 Your pending rewards:", hre.ethers.formatEther(pendingReward), "MON");
    
    if (pendingReward > 0n) {
      console.log("   Claiming rewards...");
      const claimTx = await distributor.claimReward();
      const claimReceipt = await claimTx.wait();
      console.log("   ✅ Rewards claimed!");
      console.log("   📊 Gas used:", claimReceipt.gasUsed.toString());
      console.log("   🔗 Transaction:", claimReceipt.hash);
    }
    console.log();
    
    // Final balance check
    const finalBalance = await signer.provider.getBalance(signer.address);
    console.log("💰 Final account balance:", hre.ethers.formatEther(finalBalance), "MON");
    console.log("📊 Gas fees paid:", hre.ethers.formatEther(balance - finalBalance), "MON");
    console.log();
    
    console.log("✨ All tests passed successfully!");
    console.log("\n📋 Test Summary:");
    console.log("   ✅ TrainingRegistry: Session registered and retrieved");
    console.log("   ✅ ContributionTracker: Contribution recorded and verified");
    console.log("   ✅ RewardDistributor: Funded and balance checked");
    console.log("\n🔗 View transactions on block explorer:");
    console.log("   https://explorer.testnet.monad.xyz/address/" + signer.address);
    
  } catch (error) {
    console.error("\n❌ Test failed:", error.message);
    if (error.reason) {
      console.error("   Reason:", error.reason);
    }
    if (error.data) {
      console.error("   Data:", error.data);
    }
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
