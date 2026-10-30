import { apiClient } from './client';
import type { Delivery } from './types';

export const agrogoAPI = {
  async scheduleDelivery(data: {
    order_id: string;
    farm_id: string;
  }): Promise<Delivery> {
    return apiClient.post('/api/delivery/schedule', data);
  },

  async getRoutes(date: string): Promise<{
    routes: Array<{
      route_id: string;
      farms: Array<{ farm_id: string; location: { lat: number; lng: number } }>;
      total_distance: number;
      estimated_cost: number;
    }>;
  }> {
    return apiClient.get(`/api/delivery/routes?date=${date}`);
  },

  async aggregatePickups(data: {
    farm_ids: string[];
    date: string;
  }): Promise<{
    route_id: string;
    farms: Array<{ farm_id: string; location: { lat: number; lng: number } }>;
    total_distance: number;
    estimated_cost: number;
  }> {
    return apiClient.post('/api/delivery/aggregate', data);
  },

  async getDeliveryStatus(orderId: string): Promise<Delivery> {
    return apiClient.get(`/api/delivery/status?order_id=${orderId}`);
  },

  async estimateCost(data: {
    distance_km: number;
    pickup_count: number;
  }): Promise<{
    estimated_cost: number;
    breakdown: {
      base_cost: number;
      distance_cost: number;
      pickup_cost: number;
    };
  }> {
    return apiClient.post('/api/delivery/cost-estimate', data);
  },
};

