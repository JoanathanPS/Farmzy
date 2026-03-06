import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  ShoppingCart, Plus, DollarSign, Users, Package, RefreshCw, X,
} from 'lucide-react';
import { getListings, createListing, getPricing, getBuyers, createOrder, getOrders } from '@/lib/api';
import { isSupabaseConfigured, subscribeToListings } from '@/lib/supabase';
import type { Listing, Order, Buyer } from '@/types';

// Mock data for demo
const MOCK_LISTINGS: Listing[] = [
  { id: '1', farm_id: 'FARM_PNL_01', crop: 'paddy', quantity: 500, quality_grade: 'B', suggested_price: 28, base_price: 28, soil_score: 70, status: 'active', created_at: new Date().toISOString() },
  { id: '2', farm_id: 'FARM_PNL_01', crop: 'tomato', quantity: 200, quality_grade: 'A', suggested_price: 46, base_price: 40, soil_score: 85, status: 'active', created_at: new Date().toISOString() },
  { id: '3', farm_id: 'FARM_CHN_02', crop: 'vegetables', quantity: 300, quality_grade: 'B', suggested_price: 35, base_price: 35, soil_score: 72, status: 'active', created_at: new Date().toISOString() },
];

const MOCK_BUYERS: Buyer[] = [
  { id: 'B001', name: 'Local Market', price: 26.6, location: 'Chennai', rating: 4.2 },
  { id: 'B002', name: 'Cooperative Society', price: 27.3, location: 'Poonamallee', rating: 4.5 },
  { id: 'B003', name: 'Direct Buyer', price: 28, location: 'Chennai', rating: 4.8 },
  { id: 'B004', name: 'Wholesale Dealer', price: 25.9, location: 'Chennai', rating: 4.0 },
];

export default function Marketplace() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [buyers, setBuyers] = useState<Buyer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [orderQuantity, setOrderQuantity] = useState('');
  const [pricingInfo, setPricingInfo] = useState<{ qualityGrade: string; suggestedPrice: number; basePrice: number } | null>(null);

  // Create listing form state
  const [newListing, setNewListing] = useState({ farm_id: 'FARM_PNL_01', crop: 'paddy', quantity: '', soil_score: '' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [listingsData, ordersData] = await Promise.all([
        getListings().catch(() => null),
        getOrders('FARM_PNL_01').catch(() => null),
      ]);
      setListings((listingsData as Listing[]) || MOCK_LISTINGS);
      setOrders((ordersData as Order[]) || []);
    } catch {
      setListings(MOCK_LISTINGS);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Supabase real-time subscription
  useEffect(() => {
    if (isSupabaseConfigured) {
      const sub = subscribeToListings(() => { loadData(); });
      return () => { sub?.unsubscribe(); };
    }
  }, [loadData]);

  const handleCreateListing = async () => {
    try {
      await createListing({
        farm_id: newListing.farm_id,
        crop: newListing.crop,
        quantity: Number(newListing.quantity),
        soil_score: newListing.soil_score ? Number(newListing.soil_score) : undefined,
      });
      setShowCreateForm(false);
      setNewListing({ farm_id: 'FARM_PNL_01', crop: 'paddy', quantity: '', soil_score: '' });
      loadData();
    } catch {
      // Add to local state for demo
      const mockId = String(listings.length + 1);
      const score = Number(newListing.soil_score) || 70;
      const grade = score >= 80 ? 'A' : score >= 60 ? 'B' : 'C';
      const basePrice = { paddy: 28, wheat: 24, maize: 22, vegetables: 35, tomato: 40, cotton: 180 }[newListing.crop] || 25;
      const multiplier = grade === 'A' ? 1.15 : grade === 'B' ? 1.0 : 0.9;
      setListings(prev => [{
        id: mockId, farm_id: newListing.farm_id, crop: newListing.crop,
        quantity: Number(newListing.quantity), quality_grade: grade,
        suggested_price: Math.round(basePrice * multiplier * 100) / 100,
        base_price: basePrice, soil_score: score, status: 'active',
        created_at: new Date().toISOString(),
      }, ...prev]);
      setShowCreateForm(false);
      setNewListing({ farm_id: 'FARM_PNL_01', crop: 'paddy', quantity: '', soil_score: '' });
    }
  };

  const handleSelectListing = async (listing: Listing) => {
    setSelectedListing(listing);
    setOrderQuantity('');
    try {
      const buyersData = await getBuyers(listing.id);
      setBuyers(buyersData as Buyer[]);
    } catch {
      setBuyers(MOCK_BUYERS.map(b => ({ ...b, price: Math.round(listing.suggested_price * (0.92 + Math.random() * 0.08) * 100) / 100 })));
    }
  };

  const handleOrder = async (buyerId: string) => {
    if (!selectedListing || !orderQuantity) return;
    try {
      await createOrder({
        listing_id: selectedListing.id,
        buyer_id: buyerId,
        quantity: Number(orderQuantity),
      });
      loadData();
      setSelectedListing(null);
    } catch {
      // Demo mode - add to local state
      setOrders(prev => [{
        id: String(prev.length + 1), listing_id: selectedListing.id,
        buyer_id: buyerId, farm_id: selectedListing.farm_id,
        quantity: Number(orderQuantity), price_per_kg: selectedListing.suggested_price,
        total_price: Number(orderQuantity) * selectedListing.suggested_price,
        status: 'pending', created_at: new Date().toISOString(),
      }, ...prev]);
      setSelectedListing(null);
    }
  };

  const handleCheckPricing = async () => {
    try {
      const result = await getPricing(newListing.crop, Number(newListing.soil_score) || 70) as { qualityGrade: string; suggestedPrice: number; basePrice: number };
      setPricingInfo(result);
    } catch {
      const score = Number(newListing.soil_score) || 70;
      const grade = score >= 80 ? 'A (Premium)' : score >= 60 ? 'B (Good)' : 'C (Standard)';
      const basePrice = { paddy: 28, wheat: 24, maize: 22, vegetables: 35, tomato: 40, cotton: 180 }[newListing.crop] || 25;
      const multiplier = score >= 80 ? 1.15 : score >= 60 ? 1.0 : 0.9;
      setPricingInfo({ qualityGrade: grade, suggestedPrice: Math.round(basePrice * multiplier * 100) / 100, basePrice });
    }
  };

  const gradeVariant = (grade: string): 'success' | 'warning' | 'default' => {
    if (grade === 'A') return 'success';
    if (grade === 'B') return 'warning';
    return 'default';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketplace</h1>
          <p className="text-sm text-gray-500">Buy and sell crops directly - quality-graded pricing</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateForm(true)} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Listing
          </Button>
        </div>
      </div>

      {isSupabaseConfigured && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-3">
          <p className="text-sm text-green-700">Supabase connected - Real-time updates enabled</p>
        </div>
      )}

      {/* Create Listing Modal */}
      {showCreateForm && (
        <Card className="border-green-200 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Create New Listing</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => { setShowCreateForm(false); setPricingInfo(null); }}>
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Farm ID</label>
                <Input value={newListing.farm_id} onChange={e => setNewListing(p => ({ ...p, farm_id: e.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Crop</label>
                <Select value={newListing.crop} onChange={e => setNewListing(p => ({ ...p, crop: e.target.value }))}>
                  <option value="paddy">Paddy</option>
                  <option value="wheat">Wheat</option>
                  <option value="maize">Maize</option>
                  <option value="vegetables">Vegetables</option>
                  <option value="tomato">Tomato</option>
                  <option value="cotton">Cotton</option>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Quantity (kg)</label>
                <Input type="number" placeholder="500" value={newListing.quantity} onChange={e => setNewListing(p => ({ ...p, quantity: e.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Soil Score (0-100)</label>
                <Input type="number" placeholder="70" value={newListing.soil_score} onChange={e => setNewListing(p => ({ ...p, soil_score: e.target.value }))} />
              </div>
            </div>

            {pricingInfo && (
              <div className="mt-4 rounded-lg bg-green-50 border border-green-200 p-3">
                <p className="text-sm font-medium text-green-700">Pricing Suggestion</p>
                <div className="mt-2 grid grid-cols-3 gap-3">
                  <div><p className="text-xs text-gray-500">Grade</p><p className="font-semibold">{pricingInfo.qualityGrade}</p></div>
                  <div><p className="text-xs text-gray-500">Suggested</p><p className="font-semibold text-green-600">{pricingInfo.suggestedPrice}/kg</p></div>
                  <div><p className="text-xs text-gray-500">Base</p><p className="font-semibold">{pricingInfo.basePrice}/kg</p></div>
                </div>
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <Button variant="outline" onClick={handleCheckPricing}>
                <DollarSign className="h-4 w-4 mr-1" />
                Check Pricing
              </Button>
              <Button onClick={handleCreateListing} disabled={!newListing.quantity}>
                <Plus className="h-4 w-4 mr-1" />
                Create Listing
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Listings Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Active Listings */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-green-600" />
                Active Listings ({listings.filter(l => l.status === 'active').length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse rounded-lg bg-gray-100 p-4 h-20" />
                  ))}
                </div>
              ) : listings.filter(l => l.status === 'active').length === 0 ? (
                <p className="text-center text-gray-500 py-8">No active listings. Create one to get started!</p>
              ) : (
                <div className="space-y-3">
                  {listings.filter(l => l.status === 'active').map(listing => (
                    <div key={listing.id} className={`rounded-lg border p-4 transition-colors cursor-pointer hover:border-green-300 hover:bg-green-50/30 ${selectedListing?.id === listing.id ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}
                      onClick={() => handleSelectListing(listing)}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-gray-900 capitalize">{listing.crop}</p>
                            <Badge variant={gradeVariant(listing.quality_grade)}>Grade {listing.quality_grade}</Badge>
                          </div>
                          <p className="text-sm text-gray-500 mt-1">
                            {listing.quantity} kg | Farm: {listing.farm_id}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-600">{listing.suggested_price}/kg</p>
                          <p className="text-xs text-gray-500">Soil: {listing.soil_score}/100</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Buyer Panel / Order Panel */}
        <div>
          {selectedListing ? (
            <Card className="border-green-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  Available Buyers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    Listing: <span className="font-medium capitalize">{selectedListing.crop}</span> ({selectedListing.quantity} kg)
                  </p>
                  <div className="mt-2">
                    <label className="text-sm font-medium text-gray-700 mb-1 block">Order Quantity (kg)</label>
                    <Input type="number" placeholder={String(selectedListing.quantity)}
                      value={orderQuantity} onChange={e => setOrderQuantity(e.target.value)}
                      max={selectedListing.quantity} />
                  </div>
                </div>
                <div className="space-y-2">
                  {buyers.map(buyer => (
                    <div key={buyer.id} className="rounded-lg border border-gray-200 p-3 hover:border-green-300 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-medium">{buyer.name}</p>
                          <p className="text-xs text-gray-500">{buyer.location}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-green-600">{buyer.price}/kg</p>
                          {buyer.rating && <p className="text-xs text-gray-500">Rating: {buyer.rating}</p>}
                        </div>
                      </div>
                      <Button size="sm" className="w-full" onClick={() => handleOrder(buyer.id)}
                        disabled={!orderQuantity || Number(orderQuantity) <= 0}>
                        <ShoppingCart className="h-3 w-3 mr-1" />
                        Sell to {buyer.name}
                      </Button>
                    </div>
                  ))}
                </div>
                <Button variant="ghost" className="w-full mt-3" onClick={() => setSelectedListing(null)}>
                  Cancel
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShoppingCart className="h-5 w-5 text-gray-400" />
                  Recent Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                {orders.length === 0 ? (
                  <p className="text-center text-gray-500 py-8 text-sm">No orders yet. Select a listing to start selling.</p>
                ) : (
                  <div className="space-y-3">
                    {orders.slice(0, 10).map(order => (
                      <div key={order.id} className="rounded-lg border border-gray-200 p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">Order #{order.id}</p>
                            <p className="text-xs text-gray-500">{order.quantity} kg @ {order.price_per_kg}/kg</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-bold">{order.total_price}</p>
                            <Badge variant={order.status === 'pending' ? 'warning' : order.status === 'confirmed' ? 'success' : 'info'}>
                              {order.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
