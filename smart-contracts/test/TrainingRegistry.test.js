const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("TrainingRegistry - Comprehensive Test Suite", function () {
  // Fixture for deploying contract
  async function deployTrainingRegistryFixture() {
    const [owner, coordinator, node1, node2, node3, unauthorized] = await ethers.getSigners();

    const TrainingRegistry = await ethers.getContractFactory("TrainingRegistry");
    const registry = await TrainingRegistry.deploy(owner.address);
    await registry.waitForDeployment();

    return { registry, owner, coordinator, node1, node2, node3, unauthorized };
  }

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      const { registry, owner } = await loadFixture(deployTrainingRegistryFixture);
      expect(await registry.owner()).to.equal(owner.address);
    });

    it("Should authorize deployer as coordinator", async function () {
      const { registry, owner } = await loadFixture(deployTrainingRegistryFixture);
      expect(await registry.authorizedCoordinators(owner.address)).to.be.true;
    });

    it("Should initialize with zero sessions", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      expect(await registry.getTotalSessions()).to.equal(0);
    });
  });

  describe("Coordinator Authorization", function () {
    it("Should allow owner to authorize coordinator", async function () {
      const { registry, coordinator } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(registry.setCoordinatorAuthorization(coordinator.address, true))
        .to.emit(registry, "CoordinatorAuthorized")
        .withArgs(coordinator.address, true);
      
      expect(await registry.authorizedCoordinators(coordinator.address)).to.be.true;
    });

    it("Should allow owner to revoke coordinator", async function () {
      const { registry, coordinator } = await loadFixture(deployTrainingRegistryFixture);
      
      await registry.setCoordinatorAuthorization(coordinator.address, true);
      await registry.setCoordinatorAuthorization(coordinator.address, false);
      
      expect(await registry.authorizedCoordinators(coordinator.address)).to.be.false;
    });

    it("Should reject zero address for coordinator", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(
        registry.setCoordinatorAuthorization(ethers.ZeroAddress, true)
      ).to.be.revertedWith("Invalid coordinator address");
    });

    it("Should reject unauthorized caller", async function () {
      const { registry, unauthorized, coordinator } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(
        registry.connect(unauthorized).setCoordinatorAuthorization(coordinator.address, true)
      ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount");
    });
  });

  describe("Session Creation", function () {
    it("Should create a new session", async function () {
      const { registry, owner } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId = ethers.id("session_001");
      const modelHash = ethers.id("model_v1");
      
      await expect(registry.createSession(sessionId, modelHash))
        .to.emit(registry, "SessionCreated");
      
      const session = await registry.getSession(sessionId);
      expect(session.sessionId).to.equal(sessionId);
      expect(session.modelHash).to.equal(modelHash);
      expect(session.status).to.equal(0); // Active
      expect(session.coordinator).to.equal(owner.address);
    });

    it("Should reject duplicate session ID", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId = ethers.id("session_001");
      const modelHash = ethers.id("model_v1");
      
      await registry.createSession(sessionId, modelHash);
      
      await expect(
        registry.createSession(sessionId, modelHash)
      ).to.be.revertedWith("Session already exists");
    });

    it("Should reject unauthorized coordinator", async function () {
      const { registry, unauthorized } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId = ethers.id("session_001");
      const modelHash = ethers.id("model_v1");
      
      await expect(
        registry.connect(unauthorized).createSession(sessionId, modelHash)
      ).to.be.revertedWith("Not authorized coordinator");
    });

    it("Should increment total sessions", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      expect(await registry.getTotalSessions()).to.equal(0);
      
      await registry.createSession(ethers.id("session_001"), ethers.id("model_v1"));
      expect(await registry.getTotalSessions()).to.equal(1);
      
      await registry.createSession(ethers.id("session_002"), ethers.id("model_v2"));
      expect(await registry.getTotalSessions()).to.equal(2);
    });

    it("Should reject when paused", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      await registry.pause();
      
      await expect(
        registry.createSession(ethers.id("session_001"), ethers.id("model_v1"))
      ).to.be.revertedWithCustomError(registry, "EnforcedPause");
    });
  });

  describe("Node Registration", function () {
    async function setupSession() {
      const fixture = await loadFixture(deployTrainingRegistryFixture);
      const sessionId = ethers.id("session_001");
      await fixture.registry.createSession(sessionId, ethers.id("model_v1"));
      return { ...fixture, sessionId };
    }

    it("Should register a node", async function () {
      const { registry, sessionId, node1 } = await setupSession();
      
      await expect(registry.registerNode(sessionId, node1.address, "node_1"))
        .to.emit(registry, "NodeRegistered");
      
      const nodeReg = await registry.getNodeRegistration(sessionId, node1.address);
      expect(nodeReg.nodeAddress).to.equal(node1.address);
      expect(nodeReg.nodeId).to.equal("node_1");
      expect(nodeReg.isActive).to.be.true;
    });

    it("Should increment node count", async function () {
      const { registry, sessionId, node1, node2 } = await setupSession();
      
      await registry.registerNode(sessionId, node1.address, "node_1");
      let session = await registry.getSession(sessionId);
      expect(session.nodeCount).to.equal(1);
      
      await registry.registerNode(sessionId, node2.address, "node_2");
      session = await registry.getSession(sessionId);
      expect(session.nodeCount).to.equal(2);
    });

    it("Should reject duplicate node registration", async function () {
      const { registry, sessionId, node1 } = await setupSession();
      
      await registry.registerNode(sessionId, node1.address, "node_1");
      
      await expect(
        registry.registerNode(sessionId, node1.address, "node_1")
      ).to.be.revertedWith("Node already registered");
    });

    it("Should reject zero address", async function () {
      const { registry, sessionId } = await setupSession();
      
      await expect(
        registry.registerNode(sessionId, ethers.ZeroAddress, "node_1")
      ).to.be.revertedWith("Invalid node address");
    });

    it("Should reject empty node ID", async function () {
      const { registry, sessionId, node1 } = await setupSession();
      
      await expect(
        registry.registerNode(sessionId, node1.address, "")
      ).to.be.revertedWith("Invalid node ID");
    });

    it("Should reject for non-existent session", async function () {
      const { registry, node1 } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(
        registry.registerNode(ethers.id("nonexistent"), node1.address, "node_1")
      ).to.be.revertedWith("Session does not exist");
    });

    it("Should reject for completed session", async function () {
      const { registry, sessionId, node1 } = await setupSession();
      
      await registry.completeSession(sessionId);
      
      await expect(
        registry.registerNode(sessionId, node1.address, "node_1")
      ).to.be.revertedWith("Session not active");
    });
  });

  describe("Batch Node Registration", function () {
    async function setupSession() {
      const fixture = await loadFixture(deployTrainingRegistryFixture);
      const sessionId = ethers.id("session_001");
      await fixture.registry.createSession(sessionId, ethers.id("model_v1"));
      return { ...fixture, sessionId };
    }

    it("Should register multiple nodes in batch", async function () {
      const { registry, sessionId, node1, node2, node3 } = await setupSession();
      
      const addresses = [node1.address, node2.address, node3.address];
      const nodeIds = ["node_1", "node_2", "node_3"];
      
      await registry.registerNodesBatch(sessionId, addresses, nodeIds);
      
      const session = await registry.getSession(sessionId);
      expect(session.nodeCount).to.equal(3);
      
      for (let i = 0; i < addresses.length; i++) {
        const nodeReg = await registry.getNodeRegistration(sessionId, addresses[i]);
        expect(nodeReg.isActive).to.be.true;
        expect(nodeReg.nodeId).to.equal(nodeIds[i]);
      }
    });

    it("Should reject mismatched array lengths", async function () {
      const { registry, sessionId, node1, node2 } = await setupSession();
      
      await expect(
        registry.registerNodesBatch(
          sessionId,
          [node1.address, node2.address],
          ["node_1"]
        )
      ).to.be.revertedWith("Array length mismatch");
    });

    it("Should reject empty arrays", async function () {
      const { registry, sessionId } = await setupSession();
      
      await expect(
        registry.registerNodesBatch(sessionId, [], [])
      ).to.be.revertedWith("Empty arrays");
    });

    it("Should skip already registered nodes", async function () {
      const { registry, sessionId, node1, node2 } = await setupSession();
      
      await registry.registerNode(sessionId, node1.address, "node_1");
      
      await registry.registerNodesBatch(
        sessionId,
        [node1.address, node2.address],
        ["node_1", "node_2"]
      );
      
      const session = await registry.getSession(sessionId);
      expect(session.nodeCount).to.equal(2); // Only node2 added
    });

    it("Should be gas efficient for large batches", async function () {
      const { registry, sessionId } = await setupSession();
      
      const signers = await ethers.getSigners();
      const addresses = signers.slice(0, 10).map(s => s.address);
      const nodeIds = addresses.map((_, i) => `node_${i}`);
      
      const tx = await registry.registerNodesBatch(sessionId, addresses, nodeIds);
      const receipt = await tx.wait();
      
      // Gas should be reasonable for 10 nodes
      expect(receipt.gasUsed).to.be.lessThan(1500000);
    });
  });

  describe("Session Completion", function () {
    async function setupSessionWithNodes() {
      const fixture = await loadFixture(deployTrainingRegistryFixture);
      const sessionId = ethers.id("session_001");
      await fixture.registry.createSession(sessionId, ethers.id("model_v1"));
      await fixture.registry.registerNode(sessionId, fixture.node1.address, "node_1");
      await fixture.registry.registerNode(sessionId, fixture.node2.address, "node_2");
      return { ...fixture, sessionId };
    }

    it("Should complete a session", async function () {
      const { registry, sessionId } = await setupSessionWithNodes();
      
      await expect(registry.completeSession(sessionId))
        .to.emit(registry, "SessionCompleted");
      
      const session = await registry.getSession(sessionId);
      expect(session.status).to.equal(1); // Completed
      expect(session.endTime).to.be.greaterThan(0);
    });

    it("Should reject completing non-existent session", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(
        registry.completeSession(ethers.id("nonexistent"))
      ).to.be.revertedWith("Session does not exist");
    });

    it("Should reject completing already completed session", async function () {
      const { registry, sessionId } = await setupSessionWithNodes();
      
      await registry.completeSession(sessionId);
      
      await expect(
        registry.completeSession(sessionId)
      ).to.be.revertedWith("Session not active");
    });
  });

  describe("Session Cancellation", function () {
    async function setupSession() {
      const fixture = await loadFixture(deployTrainingRegistryFixture);
      const sessionId = ethers.id("session_001");
      await fixture.registry.createSession(sessionId, ethers.id("model_v1"));
      return { ...fixture, sessionId };
    }

    it("Should cancel a session", async function () {
      const { registry, sessionId } = await setupSession();
      
      await expect(registry.cancelSession(sessionId))
        .to.emit(registry, "SessionCancelled");
      
      const session = await registry.getSession(sessionId);
      expect(session.status).to.equal(2); // Cancelled
    });

    it("Should reject cancelling completed session", async function () {
      const { registry, sessionId } = await setupSession();
      
      await registry.completeSession(sessionId);
      
      await expect(
        registry.cancelSession(sessionId)
      ).to.be.revertedWith("Session not active");
    });
  });

  describe("Node Deactivation", function () {
    async function setupSessionWithNode() {
      const fixture = await loadFixture(deployTrainingRegistryFixture);
      const sessionId = ethers.id("session_001");
      await fixture.registry.createSession(sessionId, ethers.id("model_v1"));
      await fixture.registry.registerNode(sessionId, fixture.node1.address, "node_1");
      return { ...fixture, sessionId };
    }

    it("Should deactivate a node", async function () {
      const { registry, sessionId, node1 } = await setupSessionWithNode();
      
      await expect(registry.deactivateNode(sessionId, node1.address))
        .to.emit(registry, "NodeDeactivated");
      
      const nodeReg = await registry.getNodeRegistration(sessionId, node1.address);
      expect(nodeReg.isActive).to.be.false;
    });

    it("Should reject deactivating non-active node", async function () {
      const { registry, sessionId, node1 } = await setupSessionWithNode();
      
      await registry.deactivateNode(sessionId, node1.address);
      
      await expect(
        registry.deactivateNode(sessionId, node1.address)
      ).to.be.revertedWith("Node not active");
    });
  });

  describe("Pause Functionality", function () {
    it("Should allow owner to pause", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      await registry.pause();
      expect(await registry.paused()).to.be.true;
    });

    it("Should allow owner to unpause", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      await registry.pause();
      await registry.unpause();
      expect(await registry.paused()).to.be.false;
    });

    it("Should reject non-owner pause", async function () {
      const { registry, unauthorized } = await loadFixture(deployTrainingRegistryFixture);
      
      await expect(
        registry.connect(unauthorized).pause()
      ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount");
    });
  });

  describe("Gas Optimization Tests", function () {
    it("Should use minimal gas for session creation", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      const tx = await registry.createSession(ethers.id("session_001"), ethers.id("model_v1"));
      const receipt = await tx.wait();
      
      // Should be under 200k gas
      expect(receipt.gasUsed).to.be.lessThan(200000);
    });

    it("Should use minimal gas for node registration", async function () {
      const { registry, node1 } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId = ethers.id("session_001");
      await registry.createSession(sessionId, ethers.id("model_v1"));
      
      const tx = await registry.registerNode(sessionId, node1.address, "node_1");
      const receipt = await tx.wait();
      
      // Should be under 200k gas
      expect(receipt.gasUsed).to.be.lessThan(200000);
    });
  });

  describe("Edge Cases and Security", function () {
    it("Should handle maximum node count", async function () {
      const { registry } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId = ethers.id("session_001");
      await registry.createSession(sessionId, ethers.id("model_v1"));
      
      const signers = await ethers.getSigners();
      const maxNodes = Math.min(signers.length, 20);
      
      for (let i = 0; i < maxNodes; i++) {
        await registry.registerNode(sessionId, signers[i].address, `node_${i}`);
      }
      
      const session = await registry.getSession(sessionId);
      expect(session.nodeCount).to.equal(maxNodes);
    });

    it("Should maintain data integrity across operations", async function () {
      const { registry, node1, node2 } = await loadFixture(deployTrainingRegistryFixture);
      
      const sessionId1 = ethers.id("session_001");
      const sessionId2 = ethers.id("session_002");
      
      await registry.createSession(sessionId1, ethers.id("model_v1"));
      await registry.createSession(sessionId2, ethers.id("model_v2"));
      
      await registry.registerNode(sessionId1, node1.address, "node_1");
      await registry.registerNode(sessionId2, node2.address, "node_2");
      
      const session1 = await registry.getSession(sessionId1);
      const session2 = await registry.getSession(sessionId2);
      
      expect(session1.nodeCount).to.equal(1);
      expect(session2.nodeCount).to.equal(1);
    });
  });
});
