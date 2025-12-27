import React, { useState, useEffect } from 'react';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';
import { Progress } from '../atoms/Progress';
import { Button } from '../atoms/Button';
import { MetricCard } from '../molecules/MetricCard';
import { LineChart } from '../molecules/LineChart';
import { useTrainingStore } from '../../lib/store';
import { formatNumber } from '../../utils/dateFormat';

export const TrainingDashboard: React.FC = () => {
  const {
    session,
    metrics,
    isTraining,
    startTraining,
    stopTraining,
    pauseTraining,
    resumeTraining,
  } = useTrainingStore();

  console.log('[TrainingDashboard] Rendering:', { session, metricsCount: metrics.length, isTraining });

  // Calculate progress
  const progress = session
    ? ((session.currentEpoch / session.totalEpochs) * 100)
    : 0;

  // Get latest metrics
  const latestMetrics = metrics[metrics.length - 1];

  // Calculate estimated time remaining
  const estimateTimeRemaining = () => {
    if (!session || !latestMetrics || !session.startTime) return 'Calculating...';
    
    const elapsed = Date.now() - new Date(session.startTime).getTime();
    const progressRatio = session.currentEpoch / session.totalEpochs;
    
    if (progressRatio === 0) return 'Calculating...';
    
    const totalEstimated = elapsed / progressRatio;
    const remaining = totalEstimated - elapsed;
    
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
  };

  // Prepare chart data
  const lossData = metrics.map((m, i) => ({
    x: i,
    step: m.step,
    loss: m.loss,
    epoch: Math.floor(i / 10),
  }));

  const accuracyData = metrics.map((m, i) => ({
    x: i,
    step: m.step,
    accuracy: m.accuracy * 100,
    epoch: Math.floor(i / 10),
  }));

  // Find best metrics
  const bestAccuracy = metrics.length > 0
    ? Math.max(...metrics.map(m => m.accuracy)) * 100
    : 0;
    
  const lowestLoss = metrics.length > 0
    ? Math.min(...metrics.map(m => m.loss))
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Dashboard</h1>
          <p className="text-gray-600 mt-1">
            {session ? `Session: ${session.id}` : 'No active session'}
          </p>
        </div>
        <div className="flex gap-3">
          {!isTraining ? (
            <Button
              variant="primary"
              onClick={() => {
                console.log('[TrainingDashboard] Start training clicked');
                startTraining();
              }}
            >
              Start Training
            </Button>
          ) : (
            <>
              <Button
                variant="secondary"
                onClick={() => {
                  console.log('[TrainingDashboard] Pause clicked');
                  pauseTraining();
                }}
              >
                Pause
              </Button>
              <Button
                variant="danger"
                onClick={() => {
                  console.log('[TrainingDashboard] Stop clicked');
                  stopTraining();
                }}
              >
                Stop Training
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div>
        <Badge
          variant={
            isTraining ? 'success' :
            session ? 'warning' : 'neutral'
          }
        >
          {isTraining ? 'Training' : session ? 'Paused' : 'Idle'}
        </Badge>
      </div>

      {/* Progress Bar */}
      {session && (
        <Progress
          value={progress}
          size="lg"
          variant="primary"
          showLabel
          label={`Epoch ${session.currentEpoch} / ${session.totalEpochs}`}
        />
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Loss"
          value={latestMetrics?.loss.toFixed(4) || 'N/A'}
          icon="📉"
          variant="blue"
        />
        <MetricCard
          title="Current Accuracy"
          value={latestMetrics ? `${(latestMetrics.accuracy * 100).toFixed(2)}%` : 'N/A'}
          icon="🎯"
          variant="green"
        />
        <MetricCard
          title="Learning Rate"
          value={latestMetrics?.learningRate?.toFixed(4) || 'N/A'}
          icon="⚡"
          variant="purple"
        />
        <MetricCard
          title="Time Remaining"
          value={estimateTimeRemaining()}
          icon="⏱️"
          variant="yellow"
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="green">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Best Accuracy</h3>
          <p className="text-2xl font-bold text-success-600">
            {bestAccuracy.toFixed(2)}%
          </p>
        </Card>
        <Card variant="blue">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Lowest Loss</h3>
          <p className="text-2xl font-bold text-accent-600">
            {lowestLoss.toFixed(4)}
          </p>
        </Card>
        <Card variant="purple">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Samples</h3>
          <p className="text-2xl font-bold text-primary-600">
            {session ? formatNumber(session.currentEpoch * 50000) : '0'}
          </p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChart
          title="Training Loss"
          data={lossData}
          lines={[
            { dataKey: 'loss', name: 'Loss', color: '#3b82f6' },
          ]}
          xAxisKey="step"
          height={300}
        />
        <LineChart
          title="Training Accuracy"
          data={accuracyData}
          lines={[
            { dataKey: 'accuracy', name: 'Accuracy (%)', color: '#10b981' },
          ]}
          xAxisKey="step"
          height={300}
        />
      </div>

      {/* Detailed Metrics Table */}
      {session && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Configuration</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Model</p>
              <p className="font-semibold">{session.modelName || 'simple_cnn'}</p>
            </div>
            <div>
              <p className="text-gray-600">Dataset</p>
              <p className="font-semibold">{session.dataset || 'MNIST'}</p>
            </div>
            <div>
              <p className="text-gray-600">Total Epochs</p>
              <p className="font-semibold">{session.totalEpochs}</p>
            </div>
            <div>
              <p className="text-gray-600">Status</p>
              <p className="font-semibold capitalize">{session.status}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Export Actions */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Options</h3>
        <div className="flex gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => console.log('[TrainingDashboard] Export CSV clicked')}
          >
            📊 Export CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => console.log('[TrainingDashboard] Export Chart clicked')}
          >
            📈 Export Charts
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => console.log('[TrainingDashboard] Export PDF clicked')}
          >
            📄 Generate Report
          </Button>
        </div>
      </Card>
    </div>
  );
};
