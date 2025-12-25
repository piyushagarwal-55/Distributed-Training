// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ContributionTracker
 * @dev Tracks node contributions for distributed ML training sessions
 * @notice Records compute time, gradients, and quality metrics per node
 */
contract ContributionTracker is Ownable, Pausable, ReentrancyGuard {
    
    // Contribution data structure - optimized for gas efficiency
    struct Contribution {
        uint96 computeTime;        // Total compute time in seconds
        uint32 gradientsAccepted;  // Number of accepted gradients
        uint32 successfulRounds;   // Successful training rounds
        uint32 qualityScore;       // Quality score (0-10000 for 2 decimals)
        uint96 lastUpdated;        // Last update timestamp
    }
    
    // Aggregated session contribution data
    struct SessionContribution {
        uint96 totalComputeTime;
        uint32 totalGradients;
        uint32 totalRounds;
        uint32 participantCount;
    }
    
    // State variables
    mapping(bytes32 => mapping(address => Contribution)) public contributions;
    mapping(bytes32 => SessionContribution) public sessionTotals;
    mapping(bytes32 => address[]) public sessionContributors;
    mapping(bytes32 => mapping(address => bool)) public hasContributed;
    
    // Coordinator authorization
    mapping(address => bool) public authorizedCoordinators;
    
    // Events
    event ContributionRecorded(
        bytes32 indexed sessionId,
        address indexed nodeAddress,
        uint96 computeTime,
        uint32 gradientsAccepted,
        uint32 successfulRounds,
        uint32 qualityScore
    );
    
    event BatchContributionRecorded(
        bytes32 indexed sessionId,
        uint256 nodeCount,
        uint96 timestamp
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
    
    constructor(address initialOwner) Ownable(initialOwner) {
        authorizedCoordinators[msg.sender] = true;
    }
    
    /**
     * @dev Record contribution for a single node
     * @param _sessionId Training session ID
     * @param _nodeAddress Node's Ethereum address
     * @param _computeTime Compute time in seconds
     * @param _gradientsAccepted Number of accepted gradients
     * @param _successfulRounds Number of successful rounds
     * @param _qualityScore Quality score (0-10000)
     */
    function recordContribution(
        bytes32 _sessionId,
        address _nodeAddress,
        uint96 _computeTime,
        uint32 _gradientsAccepted,
        uint32 _successfulRounds,
        uint32 _qualityScore
    ) external onlyAuthorizedCoordinator whenNotPaused {
        require(_nodeAddress != address(0), "Invalid node address");
        require(_qualityScore <= 10000, "Quality score out of range");
        
        // Track if this is first contribution
        bool isNewContributor = !hasContributed[_sessionId][_nodeAddress];
        
        // Update contribution record
        Contribution storage contrib = contributions[_sessionId][_nodeAddress];
        contrib.computeTime += _computeTime;
        contrib.gradientsAccepted += _gradientsAccepted;
        contrib.successfulRounds += _successfulRounds;
        contrib.qualityScore = _qualityScore; // Update to latest
        contrib.lastUpdated = uint96(block.timestamp);
        
        // Update session totals
        SessionContribution storage sessionTotal = sessionTotals[_sessionId];
        sessionTotal.totalComputeTime += _computeTime;
        sessionTotal.totalGradients += _gradientsAccepted;
        sessionTotal.totalRounds += _successfulRounds;
        
        // Track new contributor
        if (isNewContributor) {
            hasContributed[_sessionId][_nodeAddress] = true;
            sessionContributors[_sessionId].push(_nodeAddress);
            sessionTotal.participantCount++;
        }
        
        emit ContributionRecorded(
            _sessionId,
            _nodeAddress,
            _computeTime,
            _gradientsAccepted,
            _successfulRounds,
            _qualityScore
        );
    }
    
    /**
     * @dev Record contributions for multiple nodes in batch
     * @param _sessionId Training session ID
     * @param _nodeAddresses Array of node addresses
     * @param _computeTimes Array of compute times
     * @param _gradientsAccepted Array of gradients accepted
     * @param _successfulRounds Array of successful rounds
     * @param _qualityScores Array of quality scores
     */
    function recordContributionsBatch(
        bytes32 _sessionId,
        address[] calldata _nodeAddresses,
        uint96[] calldata _computeTimes,
        uint32[] calldata _gradientsAccepted,
        uint32[] calldata _successfulRounds,
        uint32[] calldata _qualityScores
    ) external onlyAuthorizedCoordinator whenNotPaused nonReentrant {
        uint256 length = _nodeAddresses.length;
        require(length > 0, "Empty arrays");
        require(
            length == _computeTimes.length &&
            length == _gradientsAccepted.length &&
            length == _successfulRounds.length &&
            length == _qualityScores.length,
            "Array length mismatch"
        );
        
        SessionContribution storage sessionTotal = sessionTotals[_sessionId];
        
        for (uint256 i = 0; i < length; i++) {
            address nodeAddr = _nodeAddresses[i];
            require(nodeAddr != address(0), "Invalid node address");
            require(_qualityScores[i] <= 10000, "Quality score out of range");
            
            // Track if this is first contribution
            bool isNewContributor = !hasContributed[_sessionId][nodeAddr];
            
            // Update contribution record
            Contribution storage contrib = contributions[_sessionId][nodeAddr];
            contrib.computeTime += _computeTimes[i];
            contrib.gradientsAccepted += _gradientsAccepted[i];
            contrib.successfulRounds += _successfulRounds[i];
            contrib.qualityScore = _qualityScores[i];
            contrib.lastUpdated = uint96(block.timestamp);
            
            // Update session totals
            sessionTotal.totalComputeTime += _computeTimes[i];
            sessionTotal.totalGradients += _gradientsAccepted[i];
            sessionTotal.totalRounds += _successfulRounds[i];
            
            // Track new contributor
            if (isNewContributor) {
                hasContributed[_sessionId][nodeAddr] = true;
                sessionContributors[_sessionId].push(nodeAddr);
                sessionTotal.participantCount++;
            }
            
            emit ContributionRecorded(
                _sessionId,
                nodeAddr,
                _computeTimes[i],
                _gradientsAccepted[i],
                _successfulRounds[i],
                _qualityScores[i]
            );
        }
        
        emit BatchContributionRecorded(_sessionId, length, uint96(block.timestamp));
    }
    
    /**
     * @dev Get contribution details for a node
     * @param _sessionId Session ID
     * @param _nodeAddress Node address
     */
    function getContribution(bytes32 _sessionId, address _nodeAddress)
        external
        view
        returns (Contribution memory)
    {
        return contributions[_sessionId][_nodeAddress];
    }
    
    /**
     * @dev Get session total contributions
     * @param _sessionId Session ID
     */
    function getSessionTotal(bytes32 _sessionId)
        external
        view
        returns (SessionContribution memory)
    {
        return sessionTotals[_sessionId];
    }
    
    /**
     * @dev Get all contributors for a session
     * @param _sessionId Session ID
     */
    function getSessionContributors(bytes32 _sessionId)
        external
        view
        returns (address[] memory)
    {
        return sessionContributors[_sessionId];
    }
    
    /**
     * @dev Get contributions for multiple nodes
     * @param _sessionId Session ID
     * @param _nodeAddresses Array of node addresses
     */
    function getContributionsBatch(bytes32 _sessionId, address[] calldata _nodeAddresses)
        external
        view
        returns (Contribution[] memory)
    {
        Contribution[] memory results = new Contribution[](_nodeAddresses.length);
        for (uint256 i = 0; i < _nodeAddresses.length; i++) {
            results[i] = contributions[_sessionId][_nodeAddresses[i]];
        }
        return results;
    }
    
    /**
     * @dev Calculate contribution percentage for a node
     * @param _sessionId Session ID
     * @param _nodeAddress Node address
     * @return Percentage scaled by 10000 (e.g., 2550 = 25.50%)
     */
    function getContributionPercentage(bytes32 _sessionId, address _nodeAddress)
        external
        view
        returns (uint256)
    {
        SessionContribution memory total = sessionTotals[_sessionId];
        if (total.totalComputeTime == 0) return 0;
        
        Contribution memory contrib = contributions[_sessionId][_nodeAddress];
        return (uint256(contrib.computeTime) * 10000) / uint256(total.totalComputeTime);
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
}
