const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🔍 Verifying deployment on", hre.network.name, "...\n");
  
  const deploymentFile = `./deployments/${hre.network.name}_deployment.json`;
  
  if (!fs.existsSync(deploymentFile)) {
    console.error("❌ Deployment file not found:", deploymentFile);
    process.exit(1);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  const [signer] = await hre.ethers.getSigners();
  console.log("Verifying with account:", signer.address);
  console.log("Account balance:", hre.ethers.formatEther(await signer.provider.getBalance(signer.address)), "MON\n");
  
  // Check TrainingRegistry
  console.log("📝 Checking TrainingRegistry at", deployment.contracts.TrainingRegistry);
  try {
    const registry = await hre.ethers.getContractAt(
      "TrainingRegistry",
      deployment.contracts.TrainingRegistry
    );
    const code = await signer.provider.getCode(deployment.contracts.TrainingRegistry);
    if (code === "0x") {
      console.log("❌ No contract code found");
    } else {
      console.log("✅ Contract code verified (length:", code.length, "bytes)");
      // Try to call a view function
      try {
        const sessionCount = await registry.getSessionCount();
        console.log("✅ Function call successful - Session count:", sessionCount.toString());
      } catch (e) {
        console.log("⚠️  Contract deployed but function call failed:", e.message);
      }
    }
  } catch (error) {
    console.log("❌ Error:", error.message);
  }
  console.log();
  
  // Check ContributionTracker
  console.log("📝 Checking ContributionTracker at", deployment.contracts.ContributionTracker);
  try {
    const tracker = await hre.ethers.getContractAt(
      "ContributionTracker",
      deployment.contracts.ContributionTracker
    );
    const code = await signer.provider.getCode(deployment.contracts.ContributionTracker);
    if (code === "0x") {
      console.log("❌ No contract code found");
    } else {
      console.log("✅ Contract code verified (length:", code.length, "bytes)");
    }
  } catch (error) {
    console.log("❌ Error:", error.message);
  }
  console.log();
  
  // Check RewardDistributor
  console.log("📝 Checking RewardDistributor at", deployment.contracts.RewardDistributor);
  try {
    const distributor = await hre.ethers.getContractAt(
      "RewardDistributor",
      deployment.contracts.RewardDistributor
    );
    const code = await signer.provider.getCode(deployment.contracts.RewardDistributor);
    if (code === "0x") {
      console.log("❌ No contract code found");
    } else {
      console.log("✅ Contract code verified (length:", code.length, "bytes)");
      try {
        const balance = await distributor.getContractBalance();
        console.log("✅ Function call successful - Contract balance:", hre.ethers.formatEther(balance), "MON");
      } catch (e) {
        console.log("⚠️  Contract deployed but function call failed:", e.message);
      }
    }
  } catch (error) {
    console.log("❌ Error:", error.message);
  }
  console.log();
  
  console.log("✨ Verification completed!");
  console.log("\n📋 Deployment Summary:");
  console.log(JSON.stringify(deployment, null, 2));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
