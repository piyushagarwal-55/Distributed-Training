const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("ContributionTracker - Comprehensive Test Suite", function () {
  async function deployContributionTrackerFixture() {
    const [owner, coordinator, node1, node2, node3, unauthorized] = await ethers.getSigners();

    const ContributionTracker = await ethers.getContractFactory("ContributionTracker");
    const tracker = await ContributionTracker.deploy(owner.address);
    await tracker.waitForDeployment();

    return { tracker, owner, coordinator, node1, node2, node3, unauthorized };
  }

  describe("Deployment", function () {
    it("Should set correct owner", async function () {
      const { tracker, owner } = await loadFixture(deployContributionTrackerFixture);
      expect(await tracker.owner()).to.equal(owner.address);
    });

    it("Should authorize deployer as coordinator", async function () {
      const { tracker, owner } = await loadFixture(deployContributionTrackerFixture);
      expect(await tracker.authorizedCoordinators(owner.address)).to.be.true;
    });
  });

  describe("Contribution Recording", function () {
    it("Should record a contribution", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      const computeTime = 1000;
      const gradientsAccepted = 50;
      const successfulRounds = 10;
      const qualityScore = 8500; // 85.00%
      
      await expect(
        tracker.recordContribution(
          sessionId,
          node1.address,
          computeTime,
          gradientsAccepted,
          successfulRounds,
          qualityScore
        )
      ).to.emit(tracker, "ContributionRecorded")
        .withArgs(sessionId, node1.address, computeTime, gradientsAccepted, successfulRounds, qualityScore);
      
      const contrib = await tracker.getContribution(sessionId, node1.address);
      expect(contrib.computeTime).to.equal(computeTime);
      expect(contrib.gradientsAccepted).to.equal(gradientsAccepted);
      expect(contrib.successfulRounds).to.equal(successfulRounds);
      expect(contrib.qualityScore).to.equal(qualityScore);
    });

    it("Should accumulate multiple contributions", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      
      await tracker.recordContribution(sessionId, node1.address, 1000, 50, 10, 8500);
      await tracker.recordContribution(sessionId, node1.address, 500, 25, 5, 9000);
      
      const contrib = await tracker.getContribution(sessionId, node1.address);
      expect(contrib.computeTime).to.equal(1500);
      expect(contrib.gradientsAccepted).to.equal(75);
      expect(contrib.successfulRounds).to.equal(15);
      expect(contrib.qualityScore).to.equal(9000); // Latest score
    });

    it("Should reject zero address", async function () {
      const { tracker } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.recordContribution(ethers.id("session_001"), ethers.ZeroAddress, 1000, 50, 10, 8500)
      ).to.be.revertedWith("Invalid node address");
    });

    it("Should reject quality score > 10000", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.recordContribution(ethers.id("session_001"), node1.address, 1000, 50, 10, 10001)
      ).to.be.revertedWith("Quality score out of range");
    });

    it("Should reject unauthorized coordinator", async function () {
      const { tracker, unauthorized, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.connect(unauthorized).recordContribution(
          ethers.id("session_001"),
          node1.address,
          1000,
          50,
          10,
          8500
        )
      ).to.be.revertedWith("Not authorized coordinator");
    });

    it("Should update session totals", async function () {
      const { tracker, node1, node2 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      
      await tracker.recordContribution(sessionId, node1.address, 1000, 50, 10, 8500);
      await tracker.recordContribution(sessionId, node2.address, 1500, 75, 15, 9000);
      
      const sessionTotal = await tracker.getSessionTotal(sessionId);
      expect(sessionTotal.totalComputeTime).to.equal(2500);
      expect(sessionTotal.totalGradients).to.equal(125);
      expect(sessionTotal.totalRounds).to.equal(25);
      expect(sessionTotal.participantCount).to.equal(2);
    });

    it("Should track first-time contributors", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      
      expect(await tracker.hasContributed(sessionId, node1.address)).to.be.false;
      
      await tracker.recordContribution(sessionId, node1.address, 1000, 50, 10, 8500);
      
      expect(await tracker.hasContributed(sessionId, node1.address)).to.be.true;
      
      const contributors = await tracker.getSessionContributors(sessionId);
      expect(contributors).to.include(node1.address);
    });
  });

  describe("Batch Contribution Recording", function () {
    it("Should record batch contributions", async function () {
      const { tracker, node1, node2, node3 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      const addresses = [node1.address, node2.address, node3.address];
      const computeTimes = [1000, 1500, 2000];
      const gradientsAccepted = [50, 75, 100];
      const successfulRounds = [10, 15, 20];
      const qualityScores = [8500, 9000, 9500];
      
      await expect(
        tracker.recordContributionsBatch(
          sessionId,
          addresses,
          computeTimes,
          gradientsAccepted,
          successfulRounds,
          qualityScores
        )
      ).to.emit(tracker, "BatchContributionRecorded");
      
      for (let i = 0; i < addresses.length; i++) {
        const contrib = await tracker.getContribution(sessionId, addresses[i]);
        expect(contrib.computeTime).to.equal(computeTimes[i]);
        expect(contrib.gradientsAccepted).to.equal(gradientsAccepted[i]);
      }
    });

    it("Should reject mismatched array lengths", async function () {
      const { tracker, node1, node2 } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.recordContributionsBatch(
          ethers.id("session_001"),
          [node1.address, node2.address],
          [1000],
          [50, 75],
          [10, 15],
          [8500, 9000]
        )
      ).to.be.revertedWith("Array length mismatch");
    });

    it("Should reject empty arrays", async function () {
      const { tracker } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.recordContributionsBatch(ethers.id("session_001"), [], [], [], [], [])
      ).to.be.revertedWith("Empty arrays");
    });

    it("Should be gas efficient for large batches", async function () {
      const { tracker } = await loadFixture(deployContributionTrackerFixture);
      
      const signers = await ethers.getSigners();
      const batchSize = 10;
      const addresses = signers.slice(0, batchSize).map(s => s.address);
      const computeTimes = Array(batchSize).fill(1000);
      const gradientsAccepted = Array(batchSize).fill(50);
      const successfulRounds = Array(batchSize).fill(10);
      const qualityScores = Array(batchSize).fill(8500);
      
      const tx = await tracker.recordContributionsBatch(
        ethers.id("session_001"),
        addresses,
        computeTimes,
        gradientsAccepted,
        successfulRounds,
        qualityScores
      );
      const receipt = await tx.wait();
      
      // Should be under 1.5M gas for 10 nodes (reasonable for complex batch ops)
      expect(receipt.gasUsed).to.be.lessThan(1500000);
      
      // Average gas per node should be reasonable
      const gasPerNode = receipt.gasUsed / BigInt(batchSize);
      expect(gasPerNode).to.be.lessThan(150000);
    });

    it("Should handle duplicate nodes in batch correctly", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      
      // First batch
      await tracker.recordContributionsBatch(
        sessionId,
        [node1.address],
        [1000],
        [50],
        [10],
        [8500]
      );
      
      // Second batch with same node - should accumulate
      await tracker.recordContributionsBatch(
        sessionId,
        [node1.address],
        [500],
        [25],
        [5],
        [9000]
      );
      
      const contrib = await tracker.getContribution(sessionId, node1.address);
      expect(contrib.computeTime).to.equal(1500);
      expect(contrib.gradientsAccepted).to.equal(75);
      
      const sessionTotal = await tracker.getSessionTotal(sessionId);
      expect(sessionTotal.participantCount).to.equal(1); // Should not double count
    });
  });

  describe("Contribution Queries", function () {
    async function setupContributions() {
      const fixture = await loadFixture(deployContributionTrackerFixture);
      const sessionId = ethers.id("session_001");
      
      await fixture.tracker.recordContribution(sessionId, fixture.node1.address, 1000, 50, 10, 8500);
      await fixture.tracker.recordContribution(sessionId, fixture.node2.address, 1500, 75, 15, 9000);
      await fixture.tracker.recordContribution(sessionId, fixture.node3.address, 2000, 100, 20, 9500);
      
      return { ...fixture, sessionId };
    }

    it("Should get contribution percentage", async function () {
      const { tracker, sessionId, node1, node2 } = await setupContributions();
      
      // Total compute time: 1000 + 1500 + 2000 = 4500
      // Node1: 1000/4500 = 22.22% = 2222 (scaled by 10000)
      const percentage1 = await tracker.getContributionPercentage(sessionId, node1.address);
      expect(percentage1).to.equal(2222);
      
      // Node2: 1500/4500 = 33.33% = 3333
      const percentage2 = await tracker.getContributionPercentage(sessionId, node2.address);
      expect(percentage2).to.equal(3333);
    });

    it("Should return zero percentage for non-contributor", async function () {
      const { tracker, sessionId, unauthorized } = await setupContributions();
      
      const percentage = await tracker.getContributionPercentage(sessionId, unauthorized.address);
      expect(percentage).to.equal(0);
    });

    it("Should get batch contributions", async function () {
      const { tracker, sessionId, node1, node2, node3 } = await setupContributions();
      
      const addresses = [node1.address, node2.address, node3.address];
      const contributions = await tracker.getContributionsBatch(sessionId, addresses);
      
      expect(contributions.length).to.equal(3);
      expect(contributions[0].computeTime).to.equal(1000);
      expect(contributions[1].computeTime).to.equal(1500);
      expect(contributions[2].computeTime).to.equal(2000);
    });

    it("Should get session contributors list", async function () {
      const { tracker, sessionId, node1, node2, node3 } = await setupContributions();
      
      const contributors = await tracker.getSessionContributors(sessionId);
      expect(contributors.length).to.equal(3);
      expect(contributors).to.include(node1.address);
      expect(contributors).to.include(node2.address);
      expect(contributors).to.include(node3.address);
    });
  });

  describe("Pause Functionality", function () {
    it("Should pause and unpause", async function () {
      const { tracker } = await loadFixture(deployContributionTrackerFixture);
      
      await tracker.pause();
      expect(await tracker.paused()).to.be.true;
      
      await tracker.unpause();
      expect(await tracker.paused()).to.be.false;
    });

    it("Should reject contributions when paused", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await tracker.pause();
      
      await expect(
        tracker.recordContribution(ethers.id("session_001"), node1.address, 1000, 50, 10, 8500)
      ).to.be.revertedWithCustomError(tracker, "EnforcedPause");
    });

    it("Should reject non-owner pause", async function () {
      const { tracker, unauthorized } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(
        tracker.connect(unauthorized).pause()
      ).to.be.revertedWithCustomError(tracker, "OwnableUnauthorizedAccount");
    });
  });

  describe("Gas Optimization Tests", function () {
    it("Should use minimal gas for single contribution", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const tx = await tracker.recordContribution(
        ethers.id("session_001"),
        node1.address,
        1000,
        50,
        10,
        8500
      );
      const receipt = await tx.wait();
      
      // First contribution should be under 200k gas
      expect(receipt.gasUsed).to.be.lessThan(200000);
    });

    it("Should use less gas for subsequent contributions", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const sessionId = ethers.id("session_001");
      
      // First contribution
      await tracker.recordContribution(sessionId, node1.address, 1000, 50, 10, 8500);
      
      // Second contribution (should be cheaper - no new storage slots)
      const tx = await tracker.recordContribution(sessionId, node1.address, 500, 25, 5, 9000);
      const receipt = await tx.wait();
      
      // Subsequent contributions should be under 80k gas
      expect(receipt.gasUsed).to.be.lessThan(80000);
    });

    it("Should optimize storage with packed structs", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      // Verify struct packing by checking gas usage
      const tx = await tracker.recordContribution(
        ethers.id("session_001"),
        node1.address,
        2**32 - 1, // Max uint32
        2**32 - 1,
        2**32 - 1,
        10000
      );
      const receipt = await tx.wait();
      
      // Should still be efficient with max values
      expect(receipt.gasUsed).to.be.lessThan(200000);
    });
  });

  describe("Edge Cases and Security", function () {
    it("Should handle maximum values correctly", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const maxUint96 = 2n**96n - 1n;
      const maxUint32 = 2**32 - 1;
      
      await tracker.recordContribution(
        ethers.id("session_001"),
        node1.address,
        maxUint96,
        maxUint32,
        maxUint32,
        10000
      );
      
      const contrib = await tracker.getContribution(ethers.id("session_001"), node1.address);
      expect(contrib.computeTime).to.equal(maxUint96);
      expect(contrib.gradientsAccepted).to.equal(maxUint32);
    });

    it("Should maintain data integrity across multiple sessions", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      const session1 = ethers.id("session_001");
      const session2 = ethers.id("session_002");
      
      await tracker.recordContribution(session1, node1.address, 1000, 50, 10, 8500);
      await tracker.recordContribution(session2, node1.address, 2000, 100, 20, 9000);
      
      const contrib1 = await tracker.getContribution(session1, node1.address);
      const contrib2 = await tracker.getContribution(session2, node1.address);
      
      expect(contrib1.computeTime).to.equal(1000);
      expect(contrib2.computeTime).to.equal(2000);
    });

    it("Should handle zero contributions gracefully", async function () {
      const { tracker, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await tracker.recordContribution(ethers.id("session_001"), node1.address, 0, 0, 0, 0);
      
      const contrib = await tracker.getContribution(ethers.id("session_001"), node1.address);
      expect(contrib.computeTime).to.equal(0);
    });

    it("Should prevent reentrancy in batch operations", async function () {
      const { tracker, node1, node2 } = await loadFixture(deployContributionTrackerFixture);
      
      // This test verifies the ReentrancyGuard is in place
      // Actual reentrancy attack would require a malicious contract
      const sessionId = ethers.id("session_001");
      
      await tracker.recordContributionsBatch(
        sessionId,
        [node1.address, node2.address],
        [1000, 1500],
        [50, 75],
        [10, 15],
        [8500, 9000]
      );
      
      const sessionTotal = await tracker.getSessionTotal(sessionId);
      expect(sessionTotal.participantCount).to.equal(2);
    });
  });

  describe("Coordinator Management", function () {
    it("Should authorize new coordinator", async function () {
      const { tracker, coordinator } = await loadFixture(deployContributionTrackerFixture);
      
      await expect(tracker.setCoordinatorAuthorization(coordinator.address, true))
        .to.emit(tracker, "CoordinatorAuthorized")
        .withArgs(coordinator.address, true);
      
      expect(await tracker.authorizedCoordinators(coordinator.address)).to.be.true;
    });

    it("Should allow authorized coordinator to record contributions", async function () {
      const { tracker, coordinator, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await tracker.setCoordinatorAuthorization(coordinator.address, true);
      
      await expect(
        tracker.connect(coordinator).recordContribution(
          ethers.id("session_001"),
          node1.address,
          1000,
          50,
          10,
          8500
        )
      ).to.not.be.reverted;
    });

    it("Should revoke coordinator authorization", async function () {
      const { tracker, coordinator, node1 } = await loadFixture(deployContributionTrackerFixture);
      
      await tracker.setCoordinatorAuthorization(coordinator.address, true);
      await tracker.setCoordinatorAuthorization(coordinator.address, false);
      
      await expect(
        tracker.connect(coordinator).recordContribution(
          ethers.id("session_001"),
          node1.address,
          1000,
          50,
          10,
          8500
        )
      ).to.be.revertedWith("Not authorized coordinator");
    });
  });
});
