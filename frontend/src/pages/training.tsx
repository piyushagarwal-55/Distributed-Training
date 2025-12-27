import React from 'react';
import { useTrainingStore } from '@/lib/store';

export default function TrainingPage() {
  const { session, metrics, isTraining, startTraining, stopTraining, pauseTraining } = useTrainingStore();
  
  const latestMetric = metrics[metrics.length - 1];
  const progress = session ? (session.currentEpoch / session.totalEpochs) * 100 : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Training</h1>
          <p className="text-gray-500 mt-1">Monitor and control training sessions</p>
        </div>
        <div className="flex gap-2">
          {!isTraining ? (
            <button onClick={() => startTraining()} className="btn btn-primary">
              Start Training
            </button>
          ) : (
            <>
              <button onClick={() => pauseTraining()} className="btn btn-secondary">
                Pause
              </button>
              <button onClick={() => stopTraining()} className="btn btn-secondary text-red-600 hover:text-red-700">
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className={`w-3 h-3 rounded-full ${isTraining ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
          <span className="font-medium">{isTraining ? 'Training in Progress' : 'Idle'}</span>
        </div>
        {session && (
          <>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
              <div 
                className="h-full bg-indigo-600 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500">
              Epoch {session.currentEpoch} of {session.totalEpochs} ({progress.toFixed(1)}%)
            </p>
          </>
        )}
      </div>

      {/* Metrics */}
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

      {/* Charts placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Loss Over Time</h3>
          <div className="h-48 bg-slate-50 rounded-lg flex items-center justify-center">
            {metrics.length > 0 ? (
              <div className="w-full h-full p-4">
                <div className="flex items-end justify-between h-full gap-1">
                  {metrics.slice(-20).map((m, i) => (
                    <div 
                      key={i}
                      className="bg-indigo-500 rounded-t w-full transition-all"
                      style={{ height: `${Math.max(10, (1 - m.loss) * 100)}%` }}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No data yet</p>
            )}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Accuracy Over Time</h3>
          <div className="h-48 bg-slate-50 rounded-lg flex items-center justify-center">
            {metrics.length > 0 ? (
              <div className="w-full h-full p-4">
                <div className="flex items-end justify-between h-full gap-1">
                  {metrics.slice(-20).map((m, i) => (
                    <div 
                      key={i}
                      className="bg-green-500 rounded-t w-full transition-all"
                      style={{ height: `${m.accuracy * 100}%` }}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No data yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Session Info */}
      {session && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Session Details</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Session ID</p>
              <p className="font-mono text-xs">{session.id}</p>
            </div>
            <div>
              <p className="text-gray-500">Model</p>
              <p className="font-medium">{session.modelName}</p>
            </div>
            <div>
              <p className="text-gray-500">Dataset</p>
              <p className="font-medium">{session.dataset}</p>
            </div>
            <div>
              <p className="text-gray-500">Started</p>
              <p className="font-medium">{new Date(session.startTime).toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
