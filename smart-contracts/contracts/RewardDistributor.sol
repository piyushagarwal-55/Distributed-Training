// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title RewardDistributor
 * @dev Manages reward calculation and distribution for ML training contributors
 * @notice Supports multiple reward strategies and pull payment pattern
 */
contract RewardDistributor is Ownable, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;
    
    // Reward distribution strategy
    enum RewardStrategy { Proportional, Tiered, PerformanceBased, Hybrid }
    
    // Reward calculation result for a node
    struct NodeReward {
        address nodeAddress;
        uint256 rewardAmount;
        uint96 calculatedAt;
        bool claimed;
    }
    
    // Session reward pool
    struct RewardPool {
        bytes32 sessionId;
        uint256 totalPool;
        uint256 distributed;
        uint256 claimed;
        RewardStrategy strategy;
        uint96 calculatedAt;
        bool finalized;
    }
    
    // State variables
    mapping(bytes32 => RewardPool) public rewardPools;
    mapping(bytes32 => mapping(address => NodeReward)) public nodeRewards;
    mapping(bytes32 => address[]) public sessionRewardees;
    mapping(address => uint256) public pendingWithdrawals;
    
    // Token for rewards (if using ERC20)
    IERC20 public rewardToken;
    bool public useNativeToken;
    
    // Coordinator authorization
    mapping(address => bool) public authorizedCoordinators;
    
    // Tier thresholds for tiered strategy (in basis points)
    uint256 public constant TIER1_THRESHOLD = 5000;  // Top 50%
    uint256 public constant TIER2_THRESHOLD = 8000;  // Top 80%
    uint256 public constant TIER1_BONUS = 1500;      // 15% bonus
    uint256 public constant TIER2_BONUS = 500;       // 5% bonus
    
    // Minimum guarantee (in basis points of average)
    uint256 public constant MIN_GUARANTEE_BPS = 5000; // 50% of average
    
    // Events
    event RewardPoolCreated(
        bytes32 indexed sessionId,
        uint256 totalPool,
        RewardStrategy strategy,
        uint96 timestamp
    );
    
    event RewardsCalculated(
        bytes32 indexed sessionId,
        uint256 nodeCount,
        uint256 totalDistributed
    );
    
    event RewardClaimed(
        bytes32 indexed sessionId,
        address indexed nodeAddress,
        uint256 amount,
        uint96 timestamp
    );
    
    event RewardPoolFinalized(
        bytes32 indexed sessionId,
        uint256 totalDistributed,
        uint256 totalClaimed
    );
    
    event CoordinatorAuthorized(address indexed coordinator, bool status);
    
    // Modifiers
    modifier onlyAuthorizedCoordinator() {
        require(
            authorizedCoordinators[msg.sender] || msg.sender == owner(),
            "Not authorized coordinator"
        );
        _;
    }
    
    constructor(address initialOwner, address _rewardToken, bool _useNativeToken) Ownable(initialOwner) {
        if (!_useNativeToken) {
            require(_rewardToken != address(0), "Invalid token address");
            rewardToken = IERC20(_rewardToken);
        }
        useNativeToken = _useNativeToken;
        authorizedCoordinators[msg.sender] = true;
    }
    
    /**
     * @dev Create a reward pool for a training session
     * @param _sessionId Session identifier
     * @param _totalPool Total reward amount
     * @param _strategy Distribution strategy
     */
    function createRewardPool(
        bytes32 _sessionId,
        uint256 _totalPool,
        RewardStrategy _strategy
    ) external payable onlyAuthorizedCoordinator whenNotPaused {
        require(rewardPools[_sessionId].totalPool == 0, "Pool already exists");
        require(_totalPool > 0, "Invalid pool amount");
        
        if (useNativeToken) {
            require(msg.value == _totalPool, "Incorrect ETH amount");
        } else {
            rewardToken.safeTransferFrom(msg.sender, address(this), _totalPool);
        }
        
        rewardPools[_sessionId] = RewardPool({
            sessionId: _sessionId,
            totalPool: _totalPool,
            distributed: 0,
            claimed: 0,
            strategy: _strategy,
            calculatedAt: 0,
            finalized: false
        });
        
        emit RewardPoolCreated(_sessionId, _totalPool, _strategy, uint96(block.timestamp));
    }
    
    /**
     * @dev Calculate and set rewards for nodes (proportional strategy)
     * @param _sessionId Session ID
     * @param _nodeAddresses Array of node addresses
     * @param _contributions Array of contribution amounts (compute time or score)
     */
    function calculateRewardsProportional(
        bytes32 _sessionId,
        address[] calldata _nodeAddresses,
        uint256[] calldata _contributions
    ) external onlyAuthorizedCoordinator whenNotPaused {
        RewardPool storage pool = rewardPools[_sessionId];
        require(pool.totalPool > 0, "Pool does not exist");
        require(!pool.finalized, "Pool already finalized");
        require(_nodeAddresses.length == _contributions.length, "Array length mismatch");
        
        // Calculate total contributions
        uint256 totalContribution = 0;
        for (uint256 i = 0; i < _contributions.length; i++) {
            totalContribution += _contributions[i];
        }
        require(totalContribution > 0, "No contributions");
        
        // Calculate proportional rewards
        uint256 totalDistributed = 0;
        for (uint256 i = 0; i < _nodeAddresses.length; i++) {
            uint256 reward = (pool.totalPool * _contributions[i]) / totalContribution;
            
            nodeRewards[_sessionId][_nodeAddresses[i]] = NodeReward({
                nodeAddress: _nodeAddresses[i],
                rewardAmount: reward,
                calculatedAt: uint96(block.timestamp),
                claimed: false
            });
            
            sessionRewardees[_sessionId].push(_nodeAddresses[i]);
            pendingWithdrawals[_nodeAddresses[i]] += reward;
            totalDistributed += reward;
        }
        
        pool.distributed = totalDistributed;
        pool.calculatedAt = uint96(block.timestamp);
        
        emit RewardsCalculated(_sessionId, _nodeAddresses.length, totalDistributed);
    }
    
    /**
     * @dev Calculate rewards with tiered bonuses
     * @param _sessionId Session ID
     * @param _nodeAddresses Array of node addresses (must be sorted by contribution DESC)
     * @param _contributions Array of contribution amounts (sorted DESC)
     */
    function calculateRewardsTiered(
        bytes32 _sessionId,
        address[] calldata _nodeAddresses,
        uint256[] calldata _contributions
    ) external onlyAuthorizedCoordinator whenNotPaused {
        RewardPool storage pool = rewardPools[_sessionId];
        require(pool.totalPool > 0, "Pool does not exist");
        require(!pool.finalized, "Pool already finalized");
        require(_nodeAddresses.length == _contributions.length, "Array length mismatch");
        
        uint256 nodeCount = _nodeAddresses.length;
        uint256 totalContribution = 0;
        
        // Calculate total contributions
        for (uint256 i = 0; i < nodeCount; i++) {
            totalContribution += _contributions[i];
        }
        require(totalContribution > 0, "No contributions");
        
        // Calculate tier cutoffs
        uint256 tier1Cutoff = (nodeCount * TIER1_THRESHOLD) / 10000;
        uint256 tier2Cutoff = (nodeCount * TIER2_THRESHOLD) / 10000;
        
        // Calculate base rewards with tier bonuses
        uint256 totalDistributed = 0;
        uint256 basePool = (pool.totalPool * 8500) / 10000; // 85% for base distribution
        uint256 bonusPool = pool.totalPool - basePool;       // 15% for bonuses
        
        for (uint256 i = 0; i < nodeCount; i++) {
            // Base proportional reward
            uint256 baseReward = (basePool * _contributions[i]) / totalContribution;
            
            // Add tier bonus
            uint256 bonus = 0;
            if (i < tier1Cutoff) {
                // Top tier gets larger bonus
                bonus = (bonusPool * TIER1_BONUS * _contributions[i]) / (totalContribution * 10000);
            } else if (i < tier2Cutoff) {
                // Second tier gets smaller bonus
                bonus = (bonusPool * TIER2_BONUS * _contributions[i]) / (totalContribution * 10000);
            }
            
            uint256 totalReward = baseReward + bonus;
            
            nodeRewards[_sessionId][_nodeAddresses[i]] = NodeReward({
                nodeAddress: _nodeAddresses[i],
                rewardAmount: totalReward,
                calculatedAt: uint96(block.timestamp),
                claimed: false
            });
            
            sessionRewardees[_sessionId].push(_nodeAddresses[i]);
            pendingWithdrawals[_nodeAddresses[i]] += totalReward;
            totalDistributed += totalReward;
        }
        
        pool.distributed = totalDistributed;
        pool.calculatedAt = uint96(block.timestamp);
        
        emit RewardsCalculated(_sessionId, nodeCount, totalDistributed);
    }
    
    /**
     * @dev Calculate rewards with minimum guarantee
     * @param _sessionId Session ID
     * @param _nodeAddresses Array of node addresses
     * @param _contributions Array of contribution amounts
     */
    function calculateRewardsWithMinimum(
        bytes32 _sessionId,
        address[] calldata _nodeAddresses,
        uint256[] calldata _contributions
    ) external onlyAuthorizedCoordinator whenNotPaused {
        RewardPool storage pool = rewardPools[_sessionId];
        require(pool.totalPool > 0, "Pool does not exist");
        require(!pool.finalized, "Pool already finalized");
        require(_nodeAddresses.length == _contributions.length, "Array length mismatch");
        
        uint256 nodeCount = _nodeAddresses.length;
        uint256 totalContribution = 0;
        
        for (uint256 i = 0; i < nodeCount; i++) {
            totalContribution += _contributions[i];
        }
        require(totalContribution > 0, "No contributions");
        
        // Calculate average reward and minimum
        uint256 avgReward = pool.totalPool / nodeCount;
        uint256 minReward = (avgReward * MIN_GUARANTEE_BPS) / 10000;
        
        // First pass: calculate proportional rewards
        uint256[] memory proportionalRewards = new uint256[](nodeCount);
        uint256 belowMinCount = 0;
        uint256 belowMinTotal = 0;
        
        for (uint256 i = 0; i < nodeCount; i++) {
            uint256 reward = (pool.totalPool * _contributions[i]) / totalContribution;
            proportionalRewards[i] = reward;
            
            if (reward < minReward) {
                belowMinCount++;
                belowMinTotal += (minReward - reward);
            }
        }
        
        // Second pass: adjust rewards
        uint256 totalDistributed = 0;
        
        if (belowMinCount > 0) {
            // Redistribute from above-minimum to below-minimum
            uint256 aboveMinCount = nodeCount - belowMinCount;
            uint256 reductionPerNode = aboveMinCount > 0 ? belowMinTotal / aboveMinCount : 0;
            
            for (uint256 i = 0; i < nodeCount; i++) {
                uint256 finalReward;
                
                if (proportionalRewards[i] < minReward) {
                    finalReward = minReward;
                } else {
                    finalReward = proportionalRewards[i] - reductionPerNode;
                }
                
                nodeRewards[_sessionId][_nodeAddresses[i]] = NodeReward({
                    nodeAddress: _nodeAddresses[i],
                    rewardAmount: finalReward,
                    calculatedAt: uint96(block.timestamp),
                    claimed: false
                });
                
                sessionRewardees[_sessionId].push(_nodeAddresses[i]);
                pendingWithdrawals[_nodeAddresses[i]] += finalReward;
                totalDistributed += finalReward;
            }
        } else {
            // All rewards above minimum, use proportional
            for (uint256 i = 0; i < nodeCount; i++) {
                nodeRewards[_sessionId][_nodeAddresses[i]] = NodeReward({
                    nodeAddress: _nodeAddresses[i],
                    rewardAmount: proportionalRewards[i],
                    calculatedAt: uint96(block.timestamp),
                    claimed: false
                });
                
                sessionRewardees[_sessionId].push(_nodeAddresses[i]);
                pendingWithdrawals[_nodeAddresses[i]] += proportionalRewards[i];
                totalDistributed += proportionalRewards[i];
            }
        }
        
        pool.distributed = totalDistributed;
        pool.calculatedAt = uint96(block.timestamp);
        
        emit RewardsCalculated(_sessionId, nodeCount, totalDistributed);
    }
    
    /**
     * @dev Claim rewards (pull payment pattern)
     */
    function claimReward(bytes32 _sessionId) external nonReentrant whenNotPaused {
        NodeReward storage reward = nodeRewards[_sessionId][msg.sender];
        require(reward.rewardAmount > 0, "No reward to claim");
        require(!reward.claimed, "Already claimed");
        require(pendingWithdrawals[msg.sender] >= reward.rewardAmount, "Insufficient balance");
        
        uint256 amount = reward.rewardAmount;
        reward.claimed = true;
        pendingWithdrawals[msg.sender] -= amount;
        rewardPools[_sessionId].claimed += amount;
        
        // Transfer reward
        if (useNativeToken) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "ETH transfer failed");
        } else {
            rewardToken.safeTransfer(msg.sender, amount);
        }
        
        emit RewardClaimed(_sessionId, msg.sender, amount, uint96(block.timestamp));
    }
    
    /**
     * @dev Claim rewards from multiple sessions
     * @param _sessionIds Array of session IDs
     */
    function claimRewardsBatch(bytes32[] calldata _sessionIds) external nonReentrant whenNotPaused {
        uint256 totalAmount = 0;
        
        for (uint256 i = 0; i < _sessionIds.length; i++) {
            bytes32 sessionId = _sessionIds[i];
            NodeReward storage reward = nodeRewards[sessionId][msg.sender];
            
            if (reward.rewardAmount > 0 && !reward.claimed) {
                uint256 amount = reward.rewardAmount;
                reward.claimed = true;
                pendingWithdrawals[msg.sender] -= amount;
                rewardPools[sessionId].claimed += amount;
                totalAmount += amount;
                
                emit RewardClaimed(sessionId, msg.sender, amount, uint96(block.timestamp));
            }
        }
        
        require(totalAmount > 0, "No rewards to claim");
        
        // Transfer total reward
        if (useNativeToken) {
            (bool success, ) = msg.sender.call{value: totalAmount}("");
            require(success, "ETH transfer failed");
        } else {
            rewardToken.safeTransfer(msg.sender, totalAmount);
        }
    }
    
    /**
     * @dev Finalize reward pool
     * @param _sessionId Session ID
     */
    function finalizeRewardPool(bytes32 _sessionId) external onlyAuthorizedCoordinator {
        RewardPool storage pool = rewardPools[_sessionId];
        require(pool.totalPool > 0, "Pool does not exist");
        require(!pool.finalized, "Already finalized");
        
        pool.finalized = true;
        
        emit RewardPoolFinalized(_sessionId, pool.distributed, pool.claimed);
    }
    
    /**
     * @dev Get pending reward for a node
     * @param _sessionId Session ID
     * @param _nodeAddress Node address
     */
    function getPendingReward(bytes32 _sessionId, address _nodeAddress)
        external
        view
        returns (uint256)
    {
        NodeReward memory reward = nodeRewards[_sessionId][_nodeAddress];
        if (reward.claimed) return 0;
        return reward.rewardAmount;
    }
    
    /**
     * @dev Get reward pool info
     * @param _sessionId Session ID
     */
    function getRewardPool(bytes32 _sessionId)
        external
        view
        returns (RewardPool memory)
    {
        return rewardPools[_sessionId];
    }
    
    /**
     * @dev Get all rewardees for a session
     * @param _sessionId Session ID
     */
    function getSessionRewardees(bytes32 _sessionId)
        external
        view
        returns (address[] memory)
    {
        return sessionRewardees[_sessionId];
    }
    
    /**
     * @dev Authorize or revoke coordinator
     * @param _coordinator Address to authorize/revoke
     * @param _status Authorization status
     */
    function setCoordinatorAuthorization(address _coordinator, bool _status)
        external
        onlyOwner
    {
        require(_coordinator != address(0), "Invalid coordinator address");
        authorizedCoordinators[_coordinator] = _status;
        emit CoordinatorAuthorized(_coordinator, _status);
    }
    
    /**
     * @dev Emergency withdraw unclaimed rewards (owner only, after finalization)
     * @param _sessionId Session ID
     */
    function emergencyWithdraw(bytes32 _sessionId) external onlyOwner {
        RewardPool storage pool = rewardPools[_sessionId];
        require(pool.finalized, "Pool not finalized");
        
        uint256 unclaimed = pool.distributed - pool.claimed;
        require(unclaimed > 0, "No unclaimed rewards");
        
        pool.claimed = pool.distributed;
        
        if (useNativeToken) {
            (bool success, ) = owner().call{value: unclaimed}("");
            require(success, "ETH transfer failed");
        } else {
            rewardToken.safeTransfer(owner(), unclaimed);
        }
    }
    
    /**
     * @dev Emergency pause
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Receive function to accept ETH
     */
    receive() external payable {}
}
