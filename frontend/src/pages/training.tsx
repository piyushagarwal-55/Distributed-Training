import React, { useEffect, useRef } from 'react';
import { useTrainingStore } from '@/lib/store';

export default function TrainingPage() {
  const { session, metrics, isTraining, startTraining, stopTraining, pauseTraining, resumeTraining, addMetric } = useTrainingStore();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const latestMetric = metrics[metrics.length - 1];
  const progress = session ? (session.currentEpoch / session.totalEpochs) * 100 : 0;

  // Simulate training progress
  useEffect(() => {
    if (isTraining && session) {
      intervalRef.current = setInterval(() => {
        const currentEpoch = session.currentEpoch + 1;
        if (currentEpoch <= session.totalEpochs) {
          addMetric({
            epoch: currentEpoch,
            step: currentEpoch * 100,
            loss: Math.max(0.1, 2.5 - (currentEpoch * 0.2) + (Math.random() * 0.1)),
            accuracy: Math.min(0.99, 0.5 + (currentEpoch * 0.04) + (Math.random() * 0.02)),
            learningRate: 0.001,
            timestamp: new Date().toISOString(),
          });
        } else {
          stopTraining();
        }
      }, 2000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isTraining, session?.currentEpoch]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Training</h1>
          <p className="text-sm text-gray-500 mt-1">Monitor and control training sessions</p>
        </div>
        <div className="flex gap-2">
          {!isTraining ? (
            <button onClick={() => startTraining()} className="btn btn-primary">
              Start Training
            </button>
          ) : (
            <>
              {session?.status === 'paused' ? (
                <button onClick={() => resumeTraining()} className="btn btn-primary">
                  Resume
                </button>
              ) : (
                <button onClick={() => pauseTraining()} className="btn btn-secondary">
                  Pause
                </button>
              )}
              <button onClick={() => stopTraining()} className="btn btn-danger">
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status Card */}
      <div className="card p-5">
        <div className="flex items-center gap-3 mb-4">
          <span className={`status-dot ${isTraining ? 'status-online animate-pulse-slow' : 'status-offline'}`} style={{ width: 10, height: 10 }} />
          <span className="font-medium text-gray-900">
            {isTraining ? (session?.status === 'paused' ? 'Paused' : 'Training in Progress') : 'Ready to Train'}
          </span>
        </div>
        
        {session && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Epoch {session.currentEpoch} of {session.totalEpochs}</span>
              <span className="font-medium">{progress.toFixed(0)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <p className="stat-label">Loss</p>
          <p className="stat-value">{latestMetric?.loss.toFixed(4) || '—'}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Accuracy</p>
          <p className="stat-value">{latestMetric ? `${(latestMetric.accuracy * 100).toFixed(1)}%` : '—'}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Learning Rate</p>
          <p className="stat-value">{latestMetric?.learningRate || '0.001'}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Steps</p>
          <p className="stat-value">{latestMetric?.step || 0}</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Loss</h3>
          <div className="h-40 flex items-end gap-1">
            {metrics.length > 0 ? (
              metrics.slice(-20).map((m, i) => (
                <div 
                  key={i}
                  className="flex-1 bg-gray-900 rounded-t transition-all duration-300"
                  style={{ height: `${Math.max(5, (1 - m.loss / 3) * 100)}%` }}
                  title={`Loss: ${m.loss.toFixed(4)}`}
                />
              ))
            ) : (
              <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
                Start training to see metrics
              </div>
            )}
          </div>
        </div>
        
        <div className="card p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Accuracy</h3>
          <div className="h-40 flex items-end gap-1">
            {metrics.length > 0 ? (
              metrics.slice(-20).map((m, i) => (
                <div 
                  key={i}
                  className="flex-1 bg-emerald-500 rounded-t transition-all duration-300"
                  style={{ height: `${m.accuracy * 100}%` }}
                  title={`Accuracy: ${(m.accuracy * 100).toFixed(1)}%`}
                />
              ))
            ) : (
              <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
                Start training to see metrics
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Session Details */}
      {session && (
        <div className="card p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Session Details</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Session ID</p>
              <p className="text-sm font-mono truncate">{session.id}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Model</p>
              <p className="text-sm font-medium">{session.modelName}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Dataset</p>
              <p className="text-sm font-medium">{session.dataset}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Started</p>
              <p className="text-sm font-medium">{new Date(session.startTime).toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
