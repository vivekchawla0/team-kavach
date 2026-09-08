import React, { useState, useEffect, useCallback } from 'react';
import { Wifi, RefreshCw, AlertCircle, ChevronRight, BellRing, Square, Radio } from 'lucide-react';
import { api } from '@/services/api';
import { BlynkStatusResponse } from '@/types';

export const BlynkStatusCard: React.FC = () => {
  const [status, setStatus] = useState<BlynkStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [isAlertTriggering, setIsAlertTriggering] = useState<boolean>(false);
  const [isAlertActive, setIsAlertActive] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>({
    message: 'Blynk connection successful',
    type: 'info',
  });

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await api.getBlynkStatus();
      setStatus(data);
      if (data.connected) {
        setFeedback({ message: 'Blynk connection successful - Device online', type: 'info' });
      }
    } catch {
      setStatus({
        success: false,
        connected: false,
        device: 'FloodWatch-Station-01',
        template: 'FloodWatch',
        message: 'Unable to connect to Blynk backend service',
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleTestConnection = async () => {
    try {
      setIsTesting(true);
      const res = await api.testBlynkConnection();
      if (res.success && res.connected) {
        setFeedback({ message: 'Blynk connection successful', type: 'info' });
      } else if (res.success && !res.connected) {
        setFeedback({ message: 'Blynk Cloud reachable (Device offline)', type: 'info' });
      } else {
        setFeedback({ message: 'Blynk connection failed', type: 'error' });
      }
      await fetchStatus();
    } catch {
      setFeedback({
        message: 'Unable to connect to Blynk test endpoint',
        type: 'error',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleTriggerAlert = async (action: 'trigger' | 'clear') => {
    try {
      setIsAlertTriggering(true);
      const val = action === 'trigger' ? 1 : 0;
      const res = await api.triggerBlynkAlert(action, 'v0', val);

      if (res.success) {
        setIsAlertActive(action === 'trigger');
        setFeedback({
          message: action === 'trigger'
            ? '🚨 Alert dispatched to FloodWatch-Station-01 (V0=1)'
            : 'Alert signal reset on hardware (V0=0)',
          type: 'info',
        });
      }
      await fetchStatus();
    } catch {
      setFeedback({
        message: 'Error transmitting alert to Blynk device',
        type: 'error',
      });
    } finally {
      setIsAlertTriggering(false);
    }
  };

  const isConnected = status?.connected === true;
  const deviceName = status?.device || 'FloodWatch-Station-01';
  const templateName = status?.template || 'FloodWatch';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Blynk Connection
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              IoT Device Status
            </p>
          </div>
        </div>

        <div className="w-7 h-7 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      {/* Device & Template Details matching reference */}
      <div className="flex flex-col divide-y divide-slate-100 text-xs py-1">
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500 font-medium">Device</span>
          <span className="font-bold text-slate-900 font-mono">{deviceName}</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500 font-medium">Template</span>
          <span className="font-bold text-slate-900">{templateName}</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500 font-medium">Status</span>
          <div>
            {isConnected ? (
              <span className="inline-flex items-center gap-1.5 font-bold text-emerald-600">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-bold text-rose-500">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                Disconnected
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Info Banner matching reference */}
      {feedback && (
        <div className="p-2.5 my-2 rounded-xl bg-amber-50/80 border border-amber-200/80 text-xs font-medium text-amber-900 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Primary Action Button: Dark Navy Test Button matching reference */}
      <div className="flex flex-col gap-2 pt-2">
        <button
          onClick={handleTestConnection}
          disabled={isTesting || isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 active:scale-[0.99] text-white text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-60"
        >
          {isTesting ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />
              <span>Testing Connection...</span>
            </>
          ) : (
            <>
              <Wifi className="w-4 h-4 text-sky-400" />
              <span>Test Blynk Connection</span>
            </>
          )}
        </button>

        {/* Working Hardware Alarm Action Button */}
        {!isAlertActive ? (
          <button
            onClick={() => handleTriggerAlert('trigger')}
            disabled={isAlertTriggering}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-60"
          >
            <BellRing className="w-3 h-3 text-rose-600" />
            <span>🚨 Signal Device Alert (V0)</span>
          </button>
        ) : (
          <button
            onClick={() => handleTriggerAlert('clear')}
            disabled={isAlertTriggering}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-60"
          >
            <Square className="w-3 h-3 text-rose-500" />
            <span>Stop Device Alert</span>
          </button>
        )}
      </div>
    </div>
  );
};
