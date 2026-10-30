import { apiClient } from './client';
import type { MarketplaceListing, Buyer, Order } from './types';

export const marketplaceAPI = {
  async createListing(data: {
    farm_id: string;
    crop: string;
    quantity: number;
    quality_grade?: string;
  }): Promise<MarketplaceListing> {
    return apiClient.post('/api/marketplace/list', data);
  },

  async getListings(farmId?: string): Promise<MarketplaceListing[]> {
    const params = farmId ? `?farm_id=${farmId}` : '';
    return apiClient.get(`/api/marketplace/listings${params}`);
  },

  async getPricing(crop: string, soilScore: number): Promise<{
    qualityGrade: string;
    suggestedPrice: number;
    basePrice: number;
    buyersAvailable: number;
  }> {
    return apiClient.get(`/api/marketplace/pricing?crop=${crop}&soil_score=${soilScore}`);
  },

  async getBuyers(listingId: string): Promise<Buyer[]> {
    return apiClient.get(`/api/marketplace/buyers?listing_id=${listingId}`);
  },

  async createOrder(data: {
    listing_id: string;
    buyer_id: string;
    quantity: number;
  }): Promise<Order> {
    return apiClient.post('/api/marketplace/order', data);
  },

  async getOrders(farmId: string): Promise<Order[]> {
    return apiClient.get(`/api/marketplace/orders?farm_id=${farmId}`);
  },
};

