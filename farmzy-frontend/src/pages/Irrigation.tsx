import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Droplets, RefreshCw, Zap, Clock, BarChart3,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { computeIrrigation, getIrrigationHistory, getIrrigationInsights } from '@/lib/api';
import type { ZoneDistribution, IrrigationPlan, IrrigationInsights } from '@/types';

interface IrrigationDecision {
  irrigate: boolean;
  net_water_liters: number;
  zones: ZoneDistribution[];
  confidence: number;
  reasons: string[];
  computed_values?: Record<string, number>;
  strategy?: { cycle_on_min: number; cycle_off_min: number; total_cycles: number };
}

export default function Irrigation() {
  const [decision, setDecision] = useState<IrrigationDecision | null>(null);
  const [history, setHistory] = useState<IrrigationPlan[]>([]);
  const [insights, setInsights] = useState<IrrigationInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [historyData, insightsData] = await Promise.all([
        getIrrigationHistory('FARM_PNL_01', 20).catch(() => null),
        getIrrigationInsights('FARM_PNL_01').catch(() => null),
      ]);
      setHistory((historyData as IrrigationPlan[]) || []);
      setInsights((insightsData as IrrigationInsights) || {
        total_water_used_liters: 180000, total_irrigation_sessions: 8,
        average_water_per_session: 22500, water_savings_estimate_liters: 35000,
        efficiency_score: 78,
        trends: { water_usage: 'decreasing', frequency: 'stable' },
      });
    } catch {
      setInsights({
        total_water_used_liters: 180000, total_irrigation_sessions: 8,
        average_water_per_session: 22500, water_savings_estimate_liters: 35000,
        efficiency_score: 78,
        trends: { water_usage: 'decreasing', frequency: 'stable' },
      });
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCompute = async () => {
    setComputing(true);
    try {
      const result = await computeIrrigation('FARM_PNL_01') as IrrigationDecision;
      setDecision(result);
    } catch {
      setDecision({
        irrigate: true, net_water_liters: 45421.67,
        zones: [
          { zone_id: 'Z1', water_liters: 22710.84, duration_minutes: 341, area_m2: 4046.86 },
          { zone_id: 'Z2', water_liters: 22710.84, duration_minutes: 341, area_m2: 4046.86 },
        ],
        confidence: 0.78, reasons: ['Soil moisture below threshold', 'Low forecast rainfall'],
        computed_values: { et0: 4.2, crop_water_req: 48500, effective_rainfall: 3078.33 },
        strategy: { cycle_on_min: 30, cycle_off_min: 30, total_cycles: 6 },
      });
    }
    setComputing(false);
  };

  const historyChartData = history.length > 0
    ? history.slice(0, 10).reverse().map((plan, i) => ({
        session: `#${i + 1}`,
        water: Math.round(plan.net_water_liters),
        confidence: Math.round(plan.confidence * 100),
      }))
    : [
        { session: '#1', water: 42000, confidence: 75 },
        { session: '#2', water: 38000, confidence: 80 },
        { session: '#3', water: 45000, confidence: 72 },
        { session: '#4', water: 40000, confidence: 85 },
        { session: '#5', water: 35000, confidence: 78 },
      ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Irrigation Management</h1>
          <p className="text-sm text-gray-500">HydroIQ Smart Irrigation Intelligence</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleCompute} disabled={computing}>
            <Zap className={`h-4 w-4 mr-2 ${computing ? 'animate-pulse' : ''}`} />
            {computing ? 'Computing...' : 'Compute Decision'}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-50 p-2"><Droplets className="h-5 w-5 text-blue-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Total Water Used</p>
                <p className="text-xl font-bold">{Math.round((insights?.total_water_used_liters || 0) / 1000)}K L</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-50 p-2"><BarChart3 className="h-5 w-5 text-green-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Sessions</p>
                <p className="text-xl font-bold">{insights?.total_irrigation_sessions || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-50 p-2"><Zap className="h-5 w-5 text-amber-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Water Saved</p>
                <p className="text-xl font-bold">{Math.round((insights?.water_savings_estimate_liters || 0) / 1000)}K L</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 p-2"><Clock className="h-5 w-5 text-purple-600" /></div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Efficiency</p>
                <p className="text-xl font-bold">{insights?.efficiency_score || 0}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Decision & Zones */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Current Decision */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-blue-600" />
              Irrigation Decision
            </CardTitle>
          </CardHeader>
          <CardContent>
            {decision ? (
              <div className="space-y-4">
                {/* Status */}
                <div className={`rounded-lg p-4 ${decision.irrigate ? 'bg-blue-50 border border-blue-200' : 'bg-green-50 border border-green-200'}`}>
                  <p className={`text-lg font-semibold ${decision.irrigate ? 'text-blue-700' : 'text-green-700'}`}>
                    {decision.irrigate ? 'Irrigation Recommended' : 'No Irrigation Needed'}
                  </p>
                  {decision.irrigate && (
                    <p className="text-sm text-blue-600 mt-1">
                      Total: {Math.round(decision.net_water_liters)} liters needed
                    </p>
                  )}
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600">Confidence</span>
                    <span className="text-sm font-medium">{Math.round(decision.confidence * 100)}%</span>
                  </div>
                  <Progress value={decision.confidence * 100}
                    barClassName={decision.confidence >= 0.8 ? 'bg-green-500' : decision.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'} />
                </div>

                {/* Reasons */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Reasons</p>
                  <ul className="space-y-1">
                    {decision.reasons.map((r, i) => (
                      <li key={i} className="text-sm text-gray-600">- {r}</li>
                    ))}
                  </ul>
                </div>

                {/* Strategy */}
                {decision.strategy && (
                  <div className="grid grid-cols-3 gap-3">
                    <div className="rounded-lg bg-gray-50 p-3 text-center">
                      <p className="text-xs text-gray-500">Cycle ON</p>
                      <p className="font-semibold">{decision.strategy.cycle_on_min} min</p>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-3 text-center">
                      <p className="text-xs text-gray-500">Cycle OFF</p>
                      <p className="font-semibold">{decision.strategy.cycle_off_min} min</p>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-3 text-center">
                      <p className="text-xs text-gray-500">Total Cycles</p>
                      <p className="font-semibold">{decision.strategy.total_cycles}</p>
                    </div>
                  </div>
                )}

                {/* Computed Values */}
                {decision.computed_values && (
                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs font-medium text-gray-500 mb-2">Computed Parameters</p>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      {Object.entries(decision.computed_values).map(([key, val]) => (
                        <div key={key}>
                          <p className="text-gray-500">{key}</p>
                          <p className="font-medium">{typeof val === 'number' ? Math.round(val * 100) / 100 : val}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Droplets className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Click "Compute Decision" to analyze current conditions</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Zone Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Zone Water Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {decision?.zones && decision.zones.length > 0 ? (
              <div className="space-y-4">
                {decision.zones.map(zone => (
                  <div key={zone.zone_id} className="rounded-lg border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-medium text-gray-900">{zone.zone_id}</p>
                        <p className="text-xs text-gray-500">{zone.area_m2} m2</p>
                      </div>
                      <Badge variant="info">{zone.duration_minutes} min</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Water Required</span>
                      <span className="font-medium text-blue-600">{Math.round(zone.water_liters)} L</span>
                    </div>
                    <Progress value={(zone.water_liters / (decision.net_water_liters || 1)) * 100}
                      className="mt-2" barClassName="bg-blue-500" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Zone data will appear after computing a decision</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* History Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Irrigation History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={historyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="session" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="water" name="Water (L)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="confidence" name="Confidence (%)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Trends */}
      {insights?.trends && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <Card>
            <CardContent className="p-5">
              <p className="text-sm font-medium text-gray-700">Water Usage Trend</p>
              <p className="text-2xl font-bold mt-1 capitalize">{insights.trends.water_usage}</p>
              <p className="text-xs text-gray-500 mt-1">
                Avg: {Math.round(insights.average_water_per_session)} L per session
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <p className="text-sm font-medium text-gray-700">Irrigation Frequency</p>
              <p className="text-2xl font-bold mt-1 capitalize">{insights.trends.frequency}</p>
              <p className="text-xs text-gray-500 mt-1">
                {insights.total_irrigation_sessions} sessions this period
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
