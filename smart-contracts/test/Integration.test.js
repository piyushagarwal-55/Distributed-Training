const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("Full System Integration Tests", function () {
  async function deployFullSystemFixture() {
    const [owner, coordinator, node1, node2, node3] = await ethers.getSigners();

    // Deploy all contracts
    const TrainingRegistry = await ethers.getContractFactory("TrainingRegistry");
    const registry = await TrainingRegistry.deploy(owner.address);

    const ContributionTracker = await ethers.getContractFactory("ContributionTracker");
    const tracker = await ContributionTracker.deploy(owner.address);

    const RewardDistributor = await ethers.getContractFactory("RewardDistributor");
    const distributor = await RewardDistributor.deploy(owner.address, ethers.ZeroAddress, true);

    await Promise.all([
      registry.waitForDeployment(),
      tracker.waitForDeployment(),
      distributor.waitForDeployment()
    ]);

    return { registry, tracker, distributor, owner, coordinator, node1, node2, node3 };
  }

  describe("Complete Training Session Flow", function () {
    it("Should execute full training lifecycle", async function () {
      const { registry, tracker, distributor, node1, node2, node3 } = await loadFixture(deployFullSystemFixture);
      
      const sessionId = ethers.id("training_session_001");
      const modelHash = ethers.id("model_v1_hash");
      const poolAmount = ethers.parseEther("10.0");

      // 1. Create training session
      await registry.createSession(sessionId, modelHash);
      
      // 2. Register nodes
      await registry.registerNodesBatch(
        sessionId,
        [node1.address, node2.address, node3.address],
        ["gpu_node_1", "gpu_node_2", "gpu_node_3"]
      );

      // 3. Record contributions during training
      await tracker.recordContributionsBatch(
        sessionId,
        [node1.address, node2.address, node3.address],
        [2000, 3000, 5000],  // compute times
        [100, 150, 250],     // gradients accepted
        [20, 30, 50],        // successful rounds
        [8500, 9000, 9500]   // quality scores
      );

      // 4. Complete training session
      await registry.completeSession(sessionId);

      // 5. Create reward pool
      await distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });

      // 6. Calculate rewards based on contributions
      const contributions = [2000n, 3000n, 5000n];
      await distributor.calculateRewardsProportional(
        sessionId,
        [node1.address, node2.address, node3.address],
        contributions
      );

      // 7. Nodes claim rewards
      const balances = await Promise.all([
        ethers.provider.getBalance(node1.address),
        ethers.provider.getBalance(node2.address),
        ethers.provider.getBalance(node3.address)
      ]);

      await distributor.connect(node1).claimReward(sessionId);
      await distributor.connect(node2).claimReward(sessionId);
      await distributor.connect(node3).claimReward(sessionId);

      // Verify session completed
      const session = await registry.getSession(sessionId);
      expect(session.status).to.equal(1); // Completed

      // Verify contributions recorded
      const sessionTotal = await tracker.getSessionTotal(sessionId);
      expect(sessionTotal.participantCount).to.equal(3);
      expect(sessionTotal.totalComputeTime).to.equal(10000);

      // Verify rewards distributed
      const pool = await distributor.getRewardPool(sessionId);
      expect(pool.claimed).to.equal(poolAmount);
    });
  });
});
