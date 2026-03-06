import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Truck, RefreshCw, MapPin, DollarSign, Package,
} from 'lucide-react';
import { scheduleDelivery, getDeliveryStatus, estimateDeliveryCost } from '@/lib/api';
import type { DeliveryRecord } from '@/types';

// Mock deliveries for demo
const MOCK_DELIVERIES: DeliveryRecord[] = [
  { id: 'D001', order_id: '1', farm_id: 'FARM_PNL_01', route_id: 'R001', pickup_time: new Date().toISOString(), delivery_distance_km: 15, estimated_cost: 950, actual_cost: null, delivery_status: 'scheduled', created_at: new Date().toISOString() },
  { id: 'D002', order_id: '2', farm_id: 'FARM_PNL_01', route_id: 'R001', pickup_time: new Date(Date.now() - 86400000).toISOString(), delivery_distance_km: 8, estimated_cost: 600, actual_cost: 580, delivery_status: 'delivered', created_at: new Date(Date.now() - 86400000).toISOString() },
];

export default function Delivery() {
  const [deliveries, setDeliveries] = useState<DeliveryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [costEstimate, setCostEstimate] = useState<{ distance: number; cost: number } | null>(null);

  // Schedule form state
  const [scheduleForm, setScheduleForm] = useState({ order_id: '', farm_id: 'FARM_PNL_01', delivery_date: '' });
  const [estimateForm, setEstimateForm] = useState({ distance: '', pickups: '1' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Try to load delivery status for known orders
      const results = await Promise.all(
        ['1', '2'].map(id => getDeliveryStatus(id).catch(() => null))
      );
      const validResults = results.filter(Boolean) as DeliveryRecord[];
      setDeliveries(validResults.length > 0 ? validResults : MOCK_DELIVERIES);
    } catch {
      setDeliveries(MOCK_DELIVERIES);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSchedule = async () => {
    try {
      const result = await scheduleDelivery({
        order_id: scheduleForm.order_id,
        farm_id: scheduleForm.farm_id,
        delivery_date: scheduleForm.delivery_date || undefined,
      });
      setDeliveries(prev => [result as DeliveryRecord, ...prev]);
      setShowScheduleForm(false);
      setScheduleForm({ order_id: '', farm_id: 'FARM_PNL_01', delivery_date: '' });
    } catch {
      // Demo mode
      const newDelivery: DeliveryRecord = {
        id: `D${String(deliveries.length + 1).padStart(3, '0')}`,
        order_id: scheduleForm.order_id || String(deliveries.length + 1),
        farm_id: scheduleForm.farm_id,
        route_id: null,
        pickup_time: scheduleForm.delivery_date || new Date().toISOString(),
        delivery_distance_km: 10 + Math.random() * 20,
        estimated_cost: 500 + Math.random() * 500,
        actual_cost: null,
        delivery_status: 'scheduled',
        created_at: new Date().toISOString(),
      };
      setDeliveries(prev => [newDelivery, ...prev]);
      setShowScheduleForm(false);
      setScheduleForm({ order_id: '', farm_id: 'FARM_PNL_01', delivery_date: '' });
    }
  };

  const handleEstimateCost = async () => {
    const dist = Number(estimateForm.distance);
    const pickups = Number(estimateForm.pickups);
    if (!dist || !pickups) return;

    try {
      const result = await estimateDeliveryCost(dist, pickups) as { distance_km: number; estimated_cost: number };
      setCostEstimate({ distance: result.distance_km, cost: result.estimated_cost });
    } catch {
      // Use engine formula: (distance * 50) + (pickups * 200)
      const cost = (dist * 50) + (pickups * 200);
      setCostEstimate({ distance: dist, cost });
    }
  };

  const statusVariant = (status: string): 'success' | 'warning' | 'info' | 'danger' => {
    const map: Record<string, 'success' | 'warning' | 'info' | 'danger'> = {
      delivered: 'success', in_transit: 'warning', scheduled: 'info', cancelled: 'danger',
    };
    return map[status] || 'info';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Delivery Management</h1>
          <p className="text-sm text-gray-500">AgroGo Rural Delivery System - Route optimization & tracking</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowScheduleForm(true)} size="sm">
            <Truck className="h-4 w-4 mr-2" />
            Schedule Delivery
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-50 p-2"><Package className="h-5 w-5 text-blue-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Total Deliveries</p>
                <p className="text-xl font-bold">{deliveries.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-50 p-2"><Truck className="h-5 w-5 text-green-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Delivered</p>
                <p className="text-xl font-bold">{deliveries.filter(d => d.delivery_status === 'delivered').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-50 p-2"><MapPin className="h-5 w-5 text-amber-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">In Transit</p>
                <p className="text-xl font-bold">{deliveries.filter(d => d.delivery_status === 'in_transit').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 p-2"><DollarSign className="h-5 w-5 text-purple-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Total Cost</p>
                <p className="text-xl font-bold">
                  {Math.round(deliveries.reduce((sum, d) => sum + (d.actual_cost || d.estimated_cost), 0))}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Deliveries List */}
        <div className="lg:col-span-2">
          {/* Schedule Form */}
          {showScheduleForm && (
            <Card className="border-green-200 shadow-lg mb-6">
              <CardHeader>
                <CardTitle className="text-sm">Schedule New Delivery</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div>
                    <label className="text-xs font-medium text-gray-700 mb-1 block">Order ID</label>
                    <Input placeholder="e.g. 1" value={scheduleForm.order_id}
                      onChange={e => setScheduleForm(p => ({ ...p, order_id: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700 mb-1 block">Farm ID</label>
                    <Input value={scheduleForm.farm_id}
                      onChange={e => setScheduleForm(p => ({ ...p, farm_id: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700 mb-1 block">Delivery Date</label>
                    <Input type="date" value={scheduleForm.delivery_date}
                      onChange={e => setScheduleForm(p => ({ ...p, delivery_date: e.target.value }))} />
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <Button size="sm" onClick={handleSchedule}>Schedule</Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowScheduleForm(false)}>Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-5 w-5 text-green-600" />
                Deliveries
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <div key={i} className="animate-pulse rounded-lg bg-gray-100 h-20" />)}
                </div>
              ) : deliveries.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No deliveries yet.</p>
              ) : (
                <div className="space-y-3">
                  {deliveries.map(delivery => (
                    <div key={delivery.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-900">Delivery #{delivery.id}</p>
                          <Badge variant={statusVariant(delivery.delivery_status)}>
                            {delivery.delivery_status}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium text-gray-900">
                          {Math.round(delivery.actual_cost || delivery.estimated_cost)}
                        </p>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm text-gray-600">
                        <div>
                          <span className="text-xs text-gray-400">Order</span>
                          <p>#{delivery.order_id}</p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-400">Distance</span>
                          <p>{Math.round(delivery.delivery_distance_km * 10) / 10} km</p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-400">Pickup</span>
                          <p>{delivery.pickup_time ? new Date(delivery.pickup_time).toLocaleDateString() : 'TBD'}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Cost Estimator */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4 text-green-600" />
                Cost Estimator
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-700 mb-1 block">Distance (km)</label>
                  <Input type="number" placeholder="15" value={estimateForm.distance}
                    onChange={e => setEstimateForm(p => ({ ...p, distance: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700 mb-1 block">Pickup Count</label>
                  <Input type="number" placeholder="1" value={estimateForm.pickups}
                    onChange={e => setEstimateForm(p => ({ ...p, pickups: e.target.value }))} />
                </div>
                <Button className="w-full" size="sm" onClick={handleEstimateCost}>
                  Estimate Cost
                </Button>

                {costEstimate && (
                  <div className="rounded-lg bg-green-50 border border-green-200 p-4 mt-3">
                    <p className="text-sm font-medium text-green-700">Estimated Cost</p>
                    <p className="text-3xl font-bold text-green-600 mt-1">{Math.round(costEstimate.cost)}</p>
                    <p className="text-xs text-green-600 mt-1">
                      For {costEstimate.distance} km ({Number(estimateForm.pickups)} pickups)
                    </p>
                    <div className="mt-2 text-xs text-gray-500">
                      <p>Base: 50/km | Pickup: 200/stop</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Route Info */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-blue-600" />
                Route Info
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">Farm Location</p>
                  <p className="font-medium">Poonamallee, Chennai</p>
                  <p className="text-xs text-gray-400">13.0475 N, 80.1112 E</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">Coverage</p>
                  <p className="font-medium">Max 50 km radius</p>
                  <p className="text-xs text-gray-400">Nearby threshold: 10 km</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">Algorithm</p>
                  <p className="font-medium">Nearest Neighbor</p>
                  <p className="text-xs text-gray-400">Auto-aggregation for nearby farms</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
