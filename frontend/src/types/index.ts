// ============================================================================
// CORE TYPE DEFINITIONS
// ============================================================================

// Training Session Types
export interface TrainingSession {
  id: string;
  status: 'idle' | 'initializing' | 'training' | 'paused' | 'completed' | 'failed';
  startTime: Date | null;
  endTime: Date | null;
  currentEpoch: number;
  totalEpochs: number;
  currentStep: number;
  totalSteps: number;
  config: TrainingConfig;
  metrics: TrainingMetrics;
  nodes: NodeInfo[];
}

export interface TrainingConfig {
  model: string;
  dataset: string;
  learningRate: number;
  batchSize: number;
  epochs: number;
  optimizer: 'sgd' | 'adam' | 'adamw' | 'rmsprop';
  numNodes: number;
  adaptiveTraining: boolean;
  networkSimulation: NetworkSimulation;
  blockchain: BlockchainConfig;
}

export interface NetworkSimulation {
  profile: 'good' | 'average' | 'poor' | 'custom';
  latencyMin: number;
  latencyMax: number;
  packetLoss: number;
  customNodeConfig?: Record<string, NodeNetworkConfig>;
}

export interface NodeNetworkConfig {
  latency: number;
  bandwidth: number;
  reliability: number;
}

export interface BlockchainConfig {
  enabled: boolean;
  rpcUrl: string;
  chainId: number;
  trainingRegistryAddress: string;
  contributionTrackerAddress: string;
  rewardDistributorAddress: string;
  rewardPool: string;
}

// Training Metrics
export interface TrainingMetrics {
  currentLoss: number;
  currentAccuracy: number;
  bestLoss: number;
  bestAccuracy: number;
  lossHistory: MetricPoint[];
  accuracyHistory: MetricPoint[];
  learningRate: number;
  samplesProcessed: number;
  trainingTime: number;
  estimatedTimeRemaining: number;
}

export interface MetricPoint {
  epoch: number;
  step: number;
  value: number;
  timestamp: Date;
}

// Node Types
export interface NodeInfo {
  id: string;
  address: string;
  status: NodeStatus;
  health: NodeHealth;
  metrics: NodeMetrics;
  network: NodeNetworkMetrics;
  contribution: NodeContribution;
  lastSeen: Date;
}

export type NodeStatus = 'online' | 'offline' | 'initializing' | 'training' | 'failed';
export type NodeHealth = 'healthy' | 'degraded' | 'critical';

export interface NodeMetrics {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage?: number;
  uptime: number;
  successRate: number;
  avgProcessingTime: number;
}

export interface NodeNetworkMetrics {
  latency: number;
  bandwidth: number;
  packetLoss: number;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
  lastLatencies: number[];
}

export interface NodeContribution {
  computeTime: number;
  gradientsAccepted: number;
  gradientsRejected: number;
  successfulRounds: number;
  failedRounds: number;
  qualityScore: number;
  reliabilityScore: number;
  finalScore: number;
}

// Blockchain Types
export interface BlockchainSession {
  sessionId: string;
  coordinator: string;
  status: 'active' | 'completed' | 'cancelled';
  startTime: number;
  endTime: number;
  totalNodes: number;
  contributions: ContributionRecord[];
  rewards: RewardRecord[];
}

export interface ContributionRecord {
  nodeAddress: string;
  computeTime: number;
  gradientsAccepted: number;
  successfulRounds: number;
  qualityScore: number;
  timestamp: number;
  txHash: string;
}

export interface RewardRecord {
  nodeAddress: string;
  amount: string;
  claimed: boolean;
  timestamp: number;
  txHash: string;
}

export interface Transaction {
  hash: string;
  type: 'registration' | 'contribution' | 'reward' | 'claim';
  from: string;
  to: string;
  value: string;
  status: 'pending' | 'confirmed' | 'failed';
  timestamp: Date;
  gasUsed?: string;
  blockNumber?: number;
}

// UI Component Types
export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success' | 'warning';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type BadgeVariant = 'primary' | 'success' | 'warning' | 'danger' | 'neutral' | 'accent';
export type BadgeSize = 'sm' | 'md' | 'lg';

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// WebSocket Message Types
export interface WSMessage {
  type: 'training_update' | 'node_update' | 'metrics_update' | 'alert' | 'system';
  payload: any;
  timestamp: Date;
}

export interface TrainingUpdateMessage {
  epoch: number;
  step: number;
  loss: number;
  accuracy: number;
  learningRate: number;
}

export interface NodeUpdateMessage {
  nodeId: string;
  status: NodeStatus;
  health: NodeHealth;
  metrics: Partial<NodeMetrics>;
}

export interface AlertMessage {
  severity: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  nodeId?: string;
  timestamp: Date;
}

// Chart Types
export interface ChartData {
  label: string;
  data: ChartPoint[];
  color?: string;
}

export interface ChartPoint {
  x: number | Date;
  y: number;
  label?: string;
}

// Configuration Preset Types
export interface ConfigPreset {
  id: string;
  name: string;
  description: string;
  config: Partial<TrainingConfig>;
  createdAt: Date;
  isDefault?: boolean;
}

// Session History Types
export interface SessionHistory {
  id: string;
  config: TrainingConfig;
  metrics: TrainingMetrics;
  startTime: Date;
  endTime: Date;
  status: 'completed' | 'failed' | 'cancelled';
  nodes: number;
  finalAccuracy: number;
  totalTime: number;
}

// Network Topology Types
export interface NetworkTopology {
  coordinator: NetworkNode;
  nodes: NetworkNode[];
  connections: NetworkConnection[];
}

export interface NetworkNode {
  id: string;
  type: 'coordinator' | 'worker';
  x: number;
  y: number;
  status: NodeStatus;
  health: NodeHealth;
}

export interface NetworkConnection {
  from: string;
  to: string;
  quality: 'excellent' | 'good' | 'fair' | 'poor';
  latency: number;
  active: boolean;
}

// Utility Types
export type SortDirection = 'asc' | 'desc';

export interface SortConfig<T> {
  key: keyof T;
  direction: SortDirection;
}

export interface FilterConfig {
  [key: string]: any;
}

// Console Logging Utilities (for debugging)
export const DEBUG = {
  log: (component: string, message: string, data?: any) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[${component}] ${message}`, data || '');
    }
  },
  error: (component: string, message: string, error?: any) => {
    console.error(`[${component}] ERROR: ${message}`, error || '');
  },
  warn: (component: string, message: string, data?: any) => {
    console.warn(`[${component}] WARNING: ${message}`, data || '');
  },
};
