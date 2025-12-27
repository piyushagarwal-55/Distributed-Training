const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("RewardDistributor - Comprehensive Test Suite", function () {
  async function deployRewardDistributorFixture() {
    const [owner, coordinator, node1, node2, node3, unauthorized] = await ethers.getSigners();

    const RewardDistributor = await ethers.getContractFactory("RewardDistributor");
    // Deploy with native token (ETH) for rewards
    const distributor = await RewardDistributor.deploy(owner.address, ethers.ZeroAddress, true);
    await distributor.waitForDeployment();

    return { distributor, owner, coordinator, node1, node2, node3, unauthorized };
  }

  describe("Deployment", function () {
    it("Should set correct owner", async function () {
      const { distributor, owner } = await loadFixture(deployRewardDistributorFixture);
      expect(await distributor.owner()).to.equal(owner.address);
    });

    it("Should use native token", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      expect(await distributor.useNativeToken()).to.be.true;
    });

    it("Should authorize deployer as coordinator", async function () {
      const { distributor, owner } = await loadFixture(deployRewardDistributorFixture);
      expect(await distributor.authorizedCoordinators(owner.address)).to.be.true;
    });
  });

  describe("Reward Pool Creation", function () {
    it("Should create reward pool with ETH", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("1.0");
      
      await expect(
        distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount })
      ).to.emit(distributor, "RewardPoolCreated");
      
      const pool = await distributor.getRewardPool(sessionId);
      expect(pool.totalPool).to.equal(poolAmount);
      expect(pool.strategy).to.equal(0); // Proportional
      expect(pool.finalized).to.be.false;
    });

    it("Should reject incorrect ETH amount", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("1.0");
      
      await expect(
        distributor.createRewardPool(sessionId, poolAmount, 0, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("Incorrect ETH amount");
    });

    it("Should reject duplicate pool", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("1.0");
      
      await distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      
      await expect(
        distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount })
      ).to.be.revertedWith("Pool already exists");
    });

    it("Should reject zero pool amount", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      await expect(
        distributor.createRewardPool(ethers.id("session_001"), 0, 0)
      ).to.be.revertedWith("Invalid pool amount");
    });
  });

  describe("Proportional Rewards Calculation", function () {
    async function setupRewardPool() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      
      return { ...fixture, sessionId, poolAmount };
    }

    it("Should calculate proportional rewards", async function () {
      const { distributor, sessionId, node1, node2, node3 } = await setupRewardPool();
      
      const addresses = [node1.address, node2.address, node3.address];
      const contributions = [1000n, 2000n, 2000n]; // 20%, 40%, 40%
      
      await distributor.calculateRewardsProportional(sessionId, addresses, contributions);
      
      // Check rewards
      const reward1 = await distributor.getPendingReward(sessionId, node1.address);
      const reward2 = await distributor.getPendingReward(sessionId, node2.address);
      const reward3 = await distributor.getPendingReward(sessionId, node3.address);
      
      // 10 ETH total: 2 ETH, 4 ETH, 4 ETH
      expect(reward1).to.equal(ethers.parseEther("2.0"));
      expect(reward2).to.equal(ethers.parseEther("4.0"));
      expect(reward3).to.equal(ethers.parseEther("4.0"));
    });

    it("Should emit RewardsCalculated event", async function () {
      const { distributor, sessionId, node1, node2 } = await setupRewardPool();
      
      await expect(
        distributor.calculateRewardsProportional(
          sessionId,
          [node1.address, node2.address],
          [1000n, 1000n]
        )
      ).to.emit(distributor, "RewardsCalculated");
    });

    it("Should reject for non-existent pool", async function () {
      const { distributor, node1 } = await loadFixture(deployRewardDistributorFixture);
      
      await expect(
        distributor.calculateRewardsProportional(
          ethers.id("nonexistent"),
          [node1.address],
          [1000n]
        )
      ).to.be.revertedWith("Pool does not exist");
    });

    it("Should reject zero total contributions", async function () {
      const { distributor, sessionId, node1 } = await setupRewardPool();
      
      await expect(
        distributor.calculateRewardsProportional(sessionId, [node1.address], [0n])
      ).to.be.revertedWith("No contributions");
    });
  });

  describe("Tiered Rewards Calculation", function () {
    async function setupRewardPool() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 1, { value: poolAmount });
      
      return { ...fixture, sessionId, poolAmount };
    }

    it("Should calculate tiered rewards with bonuses", async function () {
      const { distributor, sessionId, node1, node2, node3 } = await setupRewardPool();
      
      // Sorted by contribution DESC
      const addresses = [node1.address, node2.address, node3.address];
      const contributions = [3000n, 2000n, 1000n];
      
      await distributor.calculateRewardsTiered(sessionId, addresses, contributions);
      
      const reward1 = await distributor.getPendingReward(sessionId, node1.address);
      const reward2 = await distributor.getPendingReward(sessionId, node2.address);
      const reward3 = await distributor.getPendingReward(sessionId, node3.address);
      
      // Top tier should get bonus
      expect(reward1).to.be.greaterThan(reward2);
      expect(reward2).to.be.greaterThan(reward3);
    });
  });

  describe("Rewards with Minimum Guarantee", function () {
    async function setupRewardPool() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 3, { value: poolAmount });
      
      return { ...fixture, sessionId, poolAmount };
    }

    it("Should ensure minimum reward guarantee", async function () {
      const { distributor, sessionId, node1, node2, node3 } = await setupRewardPool();
      
      // Very unequal contributions
      const addresses = [node1.address, node2.address, node3.address];
      const contributions = [9000n, 500n, 500n];
      
      await distributor.calculateRewardsWithMinimum(sessionId, addresses, contributions);
      
      const reward1 = await distributor.getPendingReward(sessionId, node1.address);
      const reward2 = await distributor.getPendingReward(sessionId, node2.address);
      const reward3 = await distributor.getPendingReward(sessionId, node3.address);
      
      // Average is ~3.33 ETH, minimum is 50% = ~1.67 ETH
      const minReward = ethers.parseEther("10.0") / 3n / 2n;
      
      expect(reward2).to.be.greaterThanOrEqual(minReward);
      expect(reward3).to.be.greaterThanOrEqual(minReward);
    });
  });

  describe("Reward Claiming", function () {
    async function setupWithRewards() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      await fixture.distributor.calculateRewardsProportional(
        sessionId,
        [fixture.node1.address, fixture.node2.address],
        [1000n, 1000n]
      );
      
      return { ...fixture, sessionId, poolAmount };
    }

    it("Should allow claiming rewards", async function () {
      const { distributor, sessionId, node1 } = await setupWithRewards();
      
      const balanceBefore = await ethers.provider.getBalance(node1.address);
      
      const tx = await distributor.connect(node1).claimReward(sessionId);
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      
      const balanceAfter = await ethers.provider.getBalance(node1.address);
      
      expect(balanceAfter - balanceBefore + gasUsed).to.equal(ethers.parseEther("5.0"));
    });

    it("Should emit RewardClaimed event", async function () {
      const { distributor, sessionId, node1 } = await setupWithRewards();
      
      await expect(distributor.connect(node1).claimReward(sessionId))
        .to.emit(distributor, "RewardClaimed");
    });

    it("Should reject double claiming", async function () {
      const { distributor, sessionId, node1 } = await setupWithRewards();
      
      await distributor.connect(node1).claimReward(sessionId);
      
      await expect(
        distributor.connect(node1).claimReward(sessionId)
      ).to.be.revertedWith("Already claimed");
    });

    it("Should reject claiming with no reward", async function () {
      const { distributor, sessionId, unauthorized } = await setupWithRewards();
      
      await expect(
        distributor.connect(unauthorized).claimReward(sessionId)
      ).to.be.revertedWith("No reward to claim");
    });

    it("Should update pool claimed amount", async function () {
      const { distributor, sessionId, node1 } = await setupWithRewards();
      
      await distributor.connect(node1).claimReward(sessionId);
      
      const pool = await distributor.getRewardPool(sessionId);
      expect(pool.claimed).to.equal(ethers.parseEther("5.0"));
    });
  });

  describe("Batch Claiming", function () {
    async function setupMultipleSessions() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      
      const session1 = ethers.id("session_001");
      const session2 = ethers.id("session_002");
      const poolAmount = ethers.parseEther("5.0");
      
      await fixture.distributor.createRewardPool(session1, poolAmount, 0, { value: poolAmount });
      await fixture.distributor.createRewardPool(session2, poolAmount, 0, { value: poolAmount });
      
      await fixture.distributor.calculateRewardsProportional(session1, [fixture.node1.address], [1000n]);
      await fixture.distributor.calculateRewardsProportional(session2, [fixture.node1.address], [1000n]);
      
      return { ...fixture, session1, session2 };
    }

    it("Should claim from multiple sessions", async function () {
      const { distributor, session1, session2, node1 } = await setupMultipleSessions();
      
      const balanceBefore = await ethers.provider.getBalance(node1.address);
      
      const tx = await distributor.connect(node1).claimRewardsBatch([session1, session2]);
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      
      const balanceAfter = await ethers.provider.getBalance(node1.address);
      
      expect(balanceAfter - balanceBefore + gasUsed).to.equal(ethers.parseEther("10.0"));
    });

    it("Should skip already claimed sessions", async function () {
      const { distributor, session1, session2, node1 } = await setupMultipleSessions();
      
      await distributor.connect(node1).claimReward(session1);
      
      // Should only claim from session2
      await expect(
        distributor.connect(node1).claimRewardsBatch([session1, session2])
      ).to.not.be.reverted;
    });
  });

  describe("Pool Finalization", function () {
    async function setupWithRewards() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      await fixture.distributor.calculateRewardsProportional(
        sessionId,
        [fixture.node1.address],
        [1000n]
      );
      
      return { ...fixture, sessionId };
    }

    it("Should finalize pool", async function () {
      const { distributor, sessionId } = await setupWithRewards();
      
      await expect(distributor.finalizeRewardPool(sessionId))
        .to.emit(distributor, "RewardPoolFinalized");
      
      const pool = await distributor.getRewardPool(sessionId);
      expect(pool.finalized).to.be.true;
    });

    it("Should reject double finalization", async function () {
      const { distributor, sessionId } = await setupWithRewards();
      
      await distributor.finalizeRewardPool(sessionId);
      
      await expect(
        distributor.finalizeRewardPool(sessionId)
      ).to.be.revertedWith("Already finalized");
    });
  });

  describe("Emergency Withdraw", function () {
    async function setupFinalizedPool() {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      await fixture.distributor.calculateRewardsProportional(
        sessionId,
        [fixture.node1.address, fixture.node2.address],
        [1000n, 1000n]
      );
      
      // Only node1 claims
      await fixture.distributor.connect(fixture.node1).claimReward(sessionId);
      await fixture.distributor.finalizeRewardPool(sessionId);
      
      return { ...fixture, sessionId };
    }

    it("Should allow emergency withdraw of unclaimed rewards", async function () {
      const { distributor, sessionId, owner } = await setupFinalizedPool();
      
      const balanceBefore = await ethers.provider.getBalance(owner.address);
      
      const tx = await distributor.emergencyWithdraw(sessionId);
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      
      const balanceAfter = await ethers.provider.getBalance(owner.address);
      
      // Should receive 5 ETH (node2's unclaimed reward)
      expect(balanceAfter - balanceBefore + gasUsed).to.equal(ethers.parseEther("5.0"));
    });

    it("Should reject if pool not finalized", async function () {
      const fixture = await loadFixture(deployRewardDistributorFixture);
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await fixture.distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      
      await expect(
        fixture.distributor.emergencyWithdraw(sessionId)
      ).to.be.revertedWith("Pool not finalized");
    });
  });

  describe("Gas Optimization Tests", function () {
    it("Should use minimal gas for reward calculation", async function () {
      const { distributor, node1, node2, node3 } = await loadFixture(deployRewardDistributorFixture);
      
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      
      const tx = await distributor.calculateRewardsProportional(
        sessionId,
        [node1.address, node2.address, node3.address],
        [1000n, 2000n, 3000n]
      );
      const receipt = await tx.wait();
      
      expect(receipt.gasUsed).to.be.lessThan(500000);
    });

    it("Should use minimal gas for claiming", async function () {
      const { distributor, node1 } = await loadFixture(deployRewardDistributorFixture);
      
      const sessionId = ethers.id("session_001");
      const poolAmount = ethers.parseEther("10.0");
      
      await distributor.createRewardPool(sessionId, poolAmount, 0, { value: poolAmount });
      await distributor.calculateRewardsProportional(sessionId, [node1.address], [1000n]);
      
      const tx = await distributor.connect(node1).claimReward(sessionId);
      const receipt = await tx.wait();
      
      expect(receipt.gasUsed).to.be.lessThan(80000);
    });
  });

  describe("Pause Functionality", function () {
    it("Should pause and unpause", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      await distributor.pause();
      expect(await distributor.paused()).to.be.true;
      
      await distributor.unpause();
      expect(await distributor.paused()).to.be.false;
    });

    it("Should reject operations when paused", async function () {
      const { distributor } = await loadFixture(deployRewardDistributorFixture);
      
      await distributor.pause();
      
      await expect(
        distributor.createRewardPool(ethers.id("session_001"), ethers.parseEther("1.0"), 0, { value: ethers.parseEther("1.0") })
      ).to.be.revertedWithCustomError(distributor, "EnforcedPause");
    });
  });
});
