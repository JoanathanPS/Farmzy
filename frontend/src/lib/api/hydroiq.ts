import { apiClient } from './client';
import type { IrrigationDecision } from './types';

export const hydroiqAPI = {
  async computeIrrigation(data: {
    farm_id: string;
    soil_data?: Record<string, unknown>;
    weather_data?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    plan_id?: number;
    decision: IrrigationDecision;
  }> {
    return apiClient.post('/api/irrigation/compute', data);
  },

  async executeIrrigation(planId: number, zones: unknown[]) {
    return apiClient.post('/api/irrigation/execute', {
      plan_id: planId,
      zones,
    });
  },

  async getHistory(
    farmId: string,
    startDate?: string,
    endDate?: string,
    limit: number = 50
  ) {
    const params = new URLSearchParams({ farm_id: farmId, limit: limit.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return apiClient.get(`/api/irrigation/history?${params.toString()}`);
  },

  async getInsights(farmId: string, period: string = 'month') {
    return apiClient.get(`/api/irrigation/insights?farm_id=${farmId}&period=${period}`);
  },
};

