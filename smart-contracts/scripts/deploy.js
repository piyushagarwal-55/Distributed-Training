const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying Distributed ML Smart Contracts...\n");

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log("Account balance:", (await deployer.provider.getBalance(deployer.address)).toString());
  console.log();

  // Deploy TrainingRegistry
  console.log("📝 Deploying TrainingRegistry...");
  const TrainingRegistry = await hre.ethers.getContractFactory("TrainingRegistry");
  const trainingRegistry = await TrainingRegistry.deploy(deployer.address);
  await trainingRegistry.waitForDeployment();
  const registryAddress = await trainingRegistry.getAddress();
  console.log("✅ TrainingRegistry deployed to:", registryAddress);
  console.log();

  // Deploy ContributionTracker
  console.log("📝 Deploying ContributionTracker...");
  const ContributionTracker = await hre.ethers.getContractFactory("ContributionTracker");
  const contributionTracker = await ContributionTracker.deploy(deployer.address);
  await contributionTracker.waitForDeployment();
  const trackerAddress = await contributionTracker.getAddress();
  console.log("✅ ContributionTracker deployed to:", trackerAddress);
  console.log();

  // Deploy RewardDistributor
  console.log("📝 Deploying RewardDistributor...");
  const RewardDistributor = await hre.ethers.getContractFactory("RewardDistributor");
  // For testing, use native token (ETH/Monad)
  const useNativeToken = true;
  const tokenAddress = hre.ethers.ZeroAddress; // Not used when useNativeToken is true
  const rewardDistributor = await RewardDistributor.deploy(deployer.address, tokenAddress, useNativeToken);
  await rewardDistributor.waitForDeployment();
  const distributorAddress = await rewardDistributor.getAddress();
  console.log("✅ RewardDistributor deployed to:", distributorAddress);
  console.log();

  // Save deployment addresses
  const deploymentInfo = {
    network: hre.network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      TrainingRegistry: registryAddress,
      ContributionTracker: trackerAddress,
      RewardDistributor: distributorAddress
    }
  };

  console.log("📋 Deployment Summary:");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  console.log();

  // Save to file
  const fs = require("fs");
  const deploymentPath = `./deployments/${hre.network.name}_deployment.json`;
  
  // Create deployments directory if it doesn't exist
  if (!fs.existsSync("./deployments")) {
    fs.mkdirSync("./deployments");
  }
  
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log("💾 Deployment info saved to:", deploymentPath);
  console.log();

  console.log("✨ Deployment completed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
