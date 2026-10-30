import { apiClient } from './client';
import type { SoilHealth, DegradationTrend } from './types';

export const soilyticsAPI = {
  async getSoilHealth(deviceId: string): Promise<SoilHealth> {
    return apiClient.get<SoilHealth>(`/api/soil/health?device_id=${deviceId}`);
  },

  async getDegradationTrends(
    deviceId: string,
    rangeDays: number = 30
  ): Promise<{ device_id: string; range_days: number; trends: DegradationTrend[] }> {
    return apiClient.get<{ device_id: string; range_days: number; trends: DegradationTrend[] }>(
      `/api/soil/degradation?device_id=${deviceId}&range=${rangeDays}`
    );
  },

  async getReadings(deviceId: string, limit: number = 100) {
    return apiClient.get(`/api/soil/readings?device_id=${deviceId}&limit=${limit}`);
  },

  async ingestSoilData(data: {
    device_id: string;
    timestamp?: string;
    location?: { lat: number; lng: number };
    soil: {
      moisture: number;
      ph: number;
      nitrogen: number;
      phosphorus: number;
      potassium: number;
    };
  }) {
    return apiClient.post('/api/soil/data', data);
  },

  async fetchFromThingSpeak(deviceId?: string, location?: string) {
    const params = new URLSearchParams();
    if (deviceId) params.append('device_id', deviceId);
    if (location) params.append('location', location);
    return apiClient.get(`/api/soil/fetch-thingspeak?${params.toString()}`);
  },
};

