import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Sprout, Droplets, TrendingUp, Zap, RefreshCw, AlertTriangle, CheckCircle, Cloud,
} from 'lucide-react';
import { getDashboard } from '@/lib/api';
import type { DashboardData } from '@/types';

function KpiCard({ title, value, unit, subtitle, icon: Icon, color }: {
  title: string; value: string; unit: string; subtitle: string;
  icon: React.ElementType; color: string;
}) {
  const colors: Record<string, string> = {
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</p>
          <div className={`rounded-lg p-2 ${colors[color] || colors.green}`}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-bold text-gray-900">{value}</span>
          <span className="text-sm text-gray-500">{unit}</span>
        </div>
        <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboard() as DashboardData;
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      // Use mock data for demo
      setData({
        farm: {
          farm_id: 'FARM_PNL_01', location: { name: 'Poonamallee, Chennai', lat: 13.0475, lng: 80.1112 },
          area_acres: 2, area_m2: 8093.72, soil_type: 'loamy', crop: 'paddy',
          irrigation_type: 'drip', flow_rate_lph: 2000, zones: [
            { zone_id: 'Z1', area_acres: 1, area_m2: 4046.86 },
            { zone_id: 'Z2', area_acres: 1, area_m2: 4046.86 },
          ],
        },
        soil: {
          soil_score: 70, moisture: 38, ph: 6.4,
          nitrogen: { value: 42, status: 'medium' },
          phosphorus: { value: 18, status: 'low' },
          potassium: { value: 155, status: 'medium' },
          degradation_index: 22,
        },
        irrigation: {
          irrigate: true, net_water_liters: 45421.67,
          zones: [
            { zone_id: 'Z1', water_liters: 22710.84, duration_minutes: 341, area_m2: 4046.86 },
            { zone_id: 'Z2', water_liters: 22710.84, duration_minutes: 341, area_m2: 4046.86 },
          ],
          confidence: 0.78, reasons: ['Soil moisture below threshold', 'Low forecast rainfall'],
        },
        marketplace: {
          pricing: {
            quality_grade: 'B', soil_score: 70, suggested_price: 28, base_price: 28,
            price_multiplier: 1.0, buyers_available: 6,
          },
          listings: [],
        },
        delivery: { pending_deliveries: [] },
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><h1 className="text-2xl font-bold text-gray-900">Dashboard</h1></div>
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="p-6"><div className="animate-pulse"><div className="h-4 bg-gray-200 rounded w-3/4 mb-4" /><div className="h-8 bg-gray-200 rounded w-1/2" /></div></CardContent></Card>
          ))}
        </div>
      </div>
    );
  }

  const soil = data?.soil;
  const irrigation = data?.irrigation;
  const pricing = data?.marketplace?.pricing;

  function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'info' {
    const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
      high: 'success', medium: 'warning', low: 'danger', very_low: 'danger',
      excess: 'warning', optimal: 'success', acidic: 'danger', alkaline: 'warning',
      adequate: 'success', moderate: 'warning', critical: 'danger',
    };
    return map[status] || 'info';
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Farm Intelligence Dashboard</h1>
          <p className="text-sm text-gray-500">
            {data?.farm.location.name} - {data?.farm.crop} ({data?.farm.area_acres} acres)
          </p>
        </div>
        <Button onClick={loadDashboard} variant="outline" size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-700">Using demo data - backend not connected. {error}</p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Soil Health" value={String(soil?.soil_score || 0)} unit="/ 100"
          subtitle={`Degradation: ${soil?.degradation_index || 0}%`} icon={Sprout} color="green" />
        <KpiCard title="Water Need" value={String(Math.round(irrigation?.net_water_liters || 0))} unit="L"
          subtitle={irrigation?.irrigate ? 'Irrigation needed' : 'No irrigation needed'} icon={Droplets} color="blue" />
        <KpiCard title="Market Price" value={`${pricing?.suggested_price || 0}`} unit="/kg"
          subtitle={`Grade ${pricing?.quality_grade || '-'} | ${pricing?.buyers_available || 0} buyers`} icon={TrendingUp} color="amber" />
        <KpiCard title="Confidence" value={String(Math.round((irrigation?.confidence || 0) * 100))} unit="%"
          subtitle="Decision confidence" icon={Zap} color="purple" />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Soil Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sprout className="h-5 w-5 text-green-600" />
              Soil Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Moisture</span>
                  <span className="text-sm font-medium">{soil?.moisture || 0}%</span>
                </div>
                <Progress value={soil?.moisture || 0} barClassName="bg-blue-500" />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">pH Level</span>
                  <span className="text-sm font-medium">{soil?.ph || 0}</span>
                </div>
                <Progress value={((soil?.ph || 7) / 14) * 100} barClassName="bg-purple-500" />
              </div>
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { label: 'Nitrogen', data: soil?.nitrogen },
                  { label: 'Phosphorus', data: soil?.phosphorus },
                  { label: 'Potassium', data: soil?.potassium },
                ].map(({ label, data }) => (
                  <div key={label} className="rounded-lg bg-gray-50 p-3 text-center">
                    <p className="text-xs text-gray-500 mb-1">{label}</p>
                    <p className="text-lg font-semibold text-gray-900">{data?.value || 0}</p>
                    <Badge variant={getStatusVariant(data?.status || '')} className="mt-1">
                      {data?.status || 'unknown'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Irrigation Decision */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-blue-600" />
              Irrigation Decision
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Decision Alert */}
              <div className={`rounded-lg p-4 ${irrigation?.irrigate ? 'bg-blue-50 border border-blue-200' : 'bg-green-50 border border-green-200'}`}>
                <div className="flex items-center gap-2">
                  {irrigation?.irrigate ? (
                    <Droplets className="h-5 w-5 text-blue-600" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  )}
                  <p className={`font-medium ${irrigation?.irrigate ? 'text-blue-700' : 'text-green-700'}`}>
                    {irrigation?.irrigate ? 'Irrigation Recommended' : 'No Irrigation Needed'}
                  </p>
                </div>
              </div>

              {/* Reasons */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Reasons</p>
                <ul className="space-y-1">
                  {irrigation?.reasons.map((reason, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-gray-400 mt-1">-</span>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Zone Distribution */}
              {irrigation?.zones && irrigation.zones.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Zone Distribution</p>
                  <div className="grid grid-cols-2 gap-3">
                    {irrigation.zones.map(zone => (
                      <div key={zone.zone_id} className="rounded-lg bg-gray-50 p-3">
                        <p className="text-xs text-gray-500">{zone.zone_id}</p>
                        <p className="text-sm font-semibold">{Math.round(zone.water_liters)} L</p>
                        <p className="text-xs text-gray-500">{zone.duration_minutes} min</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Marketplace Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-amber-600" />
              Market Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-gray-50 p-4">
                  <p className="text-xs text-gray-500 mb-1">Quality Grade</p>
                  <p className="text-2xl font-bold text-gray-900">Grade {pricing?.quality_grade || '-'}</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-4">
                  <p className="text-xs text-gray-500 mb-1">Suggested Price</p>
                  <p className="text-2xl font-bold text-green-600">{pricing?.suggested_price || 0}/kg</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs text-gray-500 mb-1">Base Price</p>
                  <p className="text-sm font-semibold">{pricing?.base_price || 0}/kg</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs text-gray-500 mb-1">Buyers Available</p>
                  <p className="text-sm font-semibold">{pricing?.buyers_available || 0}</p>
                </div>
              </div>
              {data?.marketplace.listings.length ? (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Active Listings</p>
                  {data.marketplace.listings.map(listing => (
                    <div key={listing.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <p className="text-sm font-medium">{listing.crop}</p>
                        <p className="text-xs text-gray-500">{listing.quantity} kg</p>
                      </div>
                      <Badge variant={listing.quality_grade === 'A' ? 'success' : listing.quality_grade === 'B' ? 'warning' : 'default'}>
                        Grade {listing.quality_grade}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">No active listings</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Weather & Delivery */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-blue-500" />
              Weather & Delivery
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Weather */}
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Cloud className="h-4 w-4 text-blue-600" />
                  <p className="text-sm font-medium text-blue-700">Weather Advisory</p>
                </div>
                <p className="text-sm text-blue-600">
                  Typical conditions for {data?.farm.location.name || 'Chennai'}.
                  {irrigation?.irrigate ? ' Low rainfall expected - irrigation recommended.' : ' Conditions favorable.'}
                </p>
              </div>

              {/* Pending Deliveries */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Pending Deliveries</p>
                {data?.delivery.pending_deliveries.length ? (
                  data.delivery.pending_deliveries.map(d => (
                    <div key={d.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <p className="text-sm font-medium">Order #{d.order_id}</p>
                        <p className="text-xs text-gray-500">{d.pickup_time ? new Date(d.pickup_time).toLocaleDateString() : 'TBD'}</p>
                      </div>
                      <Badge variant={d.delivery_status === 'scheduled' ? 'info' : d.delivery_status === 'in_transit' ? 'warning' : 'success'}>
                        {d.delivery_status}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">No pending deliveries</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
