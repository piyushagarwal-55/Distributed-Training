// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TrainingRegistry
 * @dev Manages training sessions and node registration for distributed ML training
 * @notice Stores session metadata and participating nodes
 */
contract TrainingRegistry is Ownable, Pausable, ReentrancyGuard {
    
    // Session status enum
    enum SessionStatus { Active, Completed, Cancelled }
    
    // Training session metadata
    struct TrainingSession {
        bytes32 sessionId;
        uint96 startTime;
        uint96 endTime;
        bytes32 modelHash;
        SessionStatus status;
        uint32 nodeCount;
        address coordinator;
    }
    
    // Node registration info
    struct NodeRegistration {
        address nodeAddress;
        string nodeId;
        uint96 registeredAt;
        bool isActive;
    }
    
    // State variables
    mapping(bytes32 => TrainingSession) public sessions;
    mapping(bytes32 => mapping(address => NodeRegistration)) public sessionNodes;
    mapping(bytes32 => address[]) public sessionNodeList;
    bytes32[] public allSessions;
    
    // Coordinator authorization
    mapping(address => bool) public authorizedCoordinators;
    
    // Events
    event SessionCreated(
        bytes32 indexed sessionId,
        address indexed coordinator,
        bytes32 modelHash,
        uint96 startTime
    );
    
    event SessionCompleted(
        bytes32 indexed sessionId,
        uint96 endTime,
        uint32 nodeCount
    );
    
    event SessionCancelled(
        bytes32 indexed sessionId,
        uint96 cancelledAt
    );
    
    event NodeRegistered(
        bytes32 indexed sessionId,
        address indexed nodeAddress,
        string nodeId,
        uint96 timestamp
    );
    
    event NodeDeactivated(
        bytes32 indexed sessionId,
        address indexed nodeAddress,
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
    
    modifier sessionExists(bytes32 _sessionId) {
        require(sessions[_sessionId].startTime != 0, "Session does not exist");
        _;
    }
    
    modifier sessionActive(bytes32 _sessionId) {
        require(sessions[_sessionId].status == SessionStatus.Active, "Session not active");
        _;
    }
    
    constructor(address initialOwner) Ownable(initialOwner) {
        authorizedCoordinators[msg.sender] = true;
    }
    
    /**
     * @dev Create a new training session
     * @param _sessionId Unique identifier for the session
     * @param _modelHash Hash of the model being trained
     */
    function createSession(
        bytes32 _sessionId,
        bytes32 _modelHash
    ) external onlyAuthorizedCoordinator whenNotPaused {
        require(sessions[_sessionId].startTime == 0, "Session already exists");
        
        sessions[_sessionId] = TrainingSession({
            sessionId: _sessionId,
            startTime: uint96(block.timestamp),
            endTime: 0,
            modelHash: _modelHash,
            status: SessionStatus.Active,
            nodeCount: 0,
            coordinator: msg.sender
        });
        
        allSessions.push(_sessionId);
        
        emit SessionCreated(_sessionId, msg.sender, _modelHash, uint96(block.timestamp));
    }
    
    /**
     * @dev Register a node for a training session
     * @param _sessionId Session to register for
     * @param _nodeAddress Ethereum address of the node
     * @param _nodeId String identifier for the node
     */
    function registerNode(
        bytes32 _sessionId,
        address _nodeAddress,
        string calldata _nodeId
    ) external onlyAuthorizedCoordinator sessionExists(_sessionId) sessionActive(_sessionId) whenNotPaused {
        require(_nodeAddress != address(0), "Invalid node address");
        require(bytes(_nodeId).length > 0, "Invalid node ID");
        require(!sessionNodes[_sessionId][_nodeAddress].isActive, "Node already registered");
        
        sessionNodes[_sessionId][_nodeAddress] = NodeRegistration({
            nodeAddress: _nodeAddress,
            nodeId: _nodeId,
            registeredAt: uint96(block.timestamp),
            isActive: true
        });
        
        sessionNodeList[_sessionId].push(_nodeAddress);
        sessions[_sessionId].nodeCount++;
        
        emit NodeRegistered(_sessionId, _nodeAddress, _nodeId, uint96(block.timestamp));
    }
    
    /**
     * @dev Register multiple nodes in a single transaction
     * @param _sessionId Session to register for
     * @param _nodeAddresses Array of node addresses
     * @param _nodeIds Array of node IDs
     */
    function registerNodesBatch(
        bytes32 _sessionId,
        address[] calldata _nodeAddresses,
        string[] calldata _nodeIds
    ) external onlyAuthorizedCoordinator sessionExists(_sessionId) sessionActive(_sessionId) whenNotPaused {
        require(_nodeAddresses.length == _nodeIds.length, "Array length mismatch");
        require(_nodeAddresses.length > 0, "Empty arrays");
        
        for (uint256 i = 0; i < _nodeAddresses.length; i++) {
            address nodeAddr = _nodeAddresses[i];
            string calldata nodeId = _nodeIds[i];
            
            require(nodeAddr != address(0), "Invalid node address");
            require(bytes(nodeId).length > 0, "Invalid node ID");
            
            if (!sessionNodes[_sessionId][nodeAddr].isActive) {
                sessionNodes[_sessionId][nodeAddr] = NodeRegistration({
                    nodeAddress: nodeAddr,
                    nodeId: nodeId,
                    registeredAt: uint96(block.timestamp),
                    isActive: true
                });
                
                sessionNodeList[_sessionId].push(nodeAddr);
                sessions[_sessionId].nodeCount++;
                
                emit NodeRegistered(_sessionId, nodeAddr, nodeId, uint96(block.timestamp));
            }
        }
    }
    
    /**
     * @dev Mark a session as completed
     * @param _sessionId Session to complete
     */
    function completeSession(bytes32 _sessionId) 
        external 
        onlyAuthorizedCoordinator 
        sessionExists(_sessionId) 
        sessionActive(_sessionId) 
    {
        sessions[_sessionId].status = SessionStatus.Completed;
        sessions[_sessionId].endTime = uint96(block.timestamp);
        
        emit SessionCompleted(_sessionId, uint96(block.timestamp), sessions[_sessionId].nodeCount);
    }
    
    /**
     * @dev Cancel a session
     * @param _sessionId Session to cancel
     */
    function cancelSession(bytes32 _sessionId) 
        external 
        onlyAuthorizedCoordinator 
        sessionExists(_sessionId) 
    {
        require(sessions[_sessionId].status == SessionStatus.Active, "Session not active");
        
        sessions[_sessionId].status = SessionStatus.Cancelled;
        sessions[_sessionId].endTime = uint96(block.timestamp);
        
        emit SessionCancelled(_sessionId, uint96(block.timestamp));
    }
    
    /**
     * @dev Deactivate a node in a session
     * @param _sessionId Session ID
     * @param _nodeAddress Node to deactivate
     */
    function deactivateNode(bytes32 _sessionId, address _nodeAddress) 
        external 
        onlyAuthorizedCoordinator 
        sessionExists(_sessionId) 
    {
        require(sessionNodes[_sessionId][_nodeAddress].isActive, "Node not active");
        
        sessionNodes[_sessionId][_nodeAddress].isActive = false;
        
        emit NodeDeactivated(_sessionId, _nodeAddress, uint96(block.timestamp));
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
     * @dev Get session information
     * @param _sessionId Session to query
     */
    function getSession(bytes32 _sessionId) 
        external 
        view 
        returns (TrainingSession memory) 
    {
        return sessions[_sessionId];
    }
    
    /**
     * @dev Get all nodes for a session
     * @param _sessionId Session to query
     */
    function getSessionNodes(bytes32 _sessionId) 
        external 
        view 
        returns (address[] memory) 
    {
        return sessionNodeList[_sessionId];
    }
    
    /**
     * @dev Get node registration details
     * @param _sessionId Session ID
     * @param _nodeAddress Node address
     */
    function getNodeRegistration(bytes32 _sessionId, address _nodeAddress) 
        external 
        view 
        returns (NodeRegistration memory) 
    {
        return sessionNodes[_sessionId][_nodeAddress];
    }
    
    /**
     * @dev Get total number of sessions
     */
    function getTotalSessions() external view returns (uint256) {
        return allSessions.length;
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
