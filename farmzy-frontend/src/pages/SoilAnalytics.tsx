import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import {
  Sprout, RefreshCw, Activity, AlertTriangle, Wifi,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { fetchThingSpeakData, getSoilHealth, getSoilReadings } from '@/lib/api';
import { fetchFeeds, parseFeed, generateMockSensorData } from '@/lib/thingspeak';
import type { ParsedSensorData } from '@/lib/thingspeak';

interface SoilHealthData {
  soil_score: number;
  moisture: { value: number; status: string };
  ph: { value: number; status: string };
  nitrogen: { value: number; status: string };
  phosphorus: { value: number; status: string };
  potassium: { value: number; status: string };
  degradation_index: number;
}

export default function SoilAnalytics() {
  const [sensorData, setSensorData] = useState<ParsedSensorData[]>([]);
  const [soilHealth, setSoilHealth] = useState<SoilHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [thingspeakConfigured, setThingspeakConfigured] = useState(false);
  const [channelId, setChannelId] = useState(import.meta.env.VITE_THINGSPEAK_CHANNEL_ID || '');
  const [apiKey, setApiKey] = useState(import.meta.env.VITE_THINGSPEAK_API_KEY || '');
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Try loading from ThingSpeak directly
    if (channelId && apiKey) {
      try {
        const response = await fetchFeeds(channelId, apiKey, 100);
        const parsed = response.feeds.map(parseFeed);
        setSensorData(parsed);
        setThingspeakConfigured(true);
      } catch (err) {
        setError('ThingSpeak direct fetch failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
        setSensorData(generateMockSensorData(48));
      }
    } else {
      // Try via backend
      try {
        await fetchThingSpeakData('ESP_FARM_01');
        const readings = await getSoilReadings('ESP_FARM_01', 100) as Array<{
          timestamp: string;
          soil: { moisture: number; ph: number; nitrogen: number; phosphorus: number; potassium: number };
        }>;
        setSensorData(readings.map(r => ({
          timestamp: r.timestamp,
          moisture: r.soil.moisture,
          ph: r.soil.ph,
          nitrogen: r.soil.nitrogen,
          phosphorus: r.soil.phosphorus,
          potassium: r.soil.potassium,
        })));
      } catch {
        setSensorData(generateMockSensorData(48));
      }
    }

    // Load soil health
    try {
      const health = await getSoilHealth('ESP_FARM_01', 'FARM_PNL_01') as SoilHealthData;
      setSoilHealth(health);
    } catch {
      setSoilHealth({
        soil_score: 70, degradation_index: 22,
        moisture: { value: 38, status: 'moderate' },
        ph: { value: 6.4, status: 'optimal' },
        nitrogen: { value: 42, status: 'medium' },
        phosphorus: { value: 18, status: 'low' },
        potassium: { value: 155, status: 'medium' },
      });
    }

    setLoading(false);
  }, [channelId, apiKey]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-refresh every 60 seconds if ThingSpeak is configured
  useEffect(() => {
    if (!thingspeakConfigured) return;
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [thingspeakConfigured, loadData]);

  const latest = sensorData.length > 0 ? sensorData[sensorData.length - 1] : null;

  const chartData = sensorData.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    Moisture: Math.round(d.moisture * 10) / 10,
    pH: Math.round(d.ph * 10) / 10,
    N: Math.round(d.nitrogen),
    P: Math.round(d.phosphorus),
    K: Math.round(d.potassium),
  }));

  function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'info' {
    const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
      high: 'success', medium: 'warning', low: 'danger', very_low: 'danger',
      excess: 'warning', optimal: 'success', acidic: 'danger', alkaline: 'warning',
      adequate: 'success', moderate: 'warning', critical: 'danger',
    };
    return map[status] || 'info';
  }

  function getScoreColor(score: number) {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Soil Analytics</h1>
          <p className="text-sm text-gray-500">Soilytics Intelligence - Real-time sensor data & health analysis</p>
        </div>
        <div className="flex items-center gap-2">
          {thingspeakConfigured && (
            <Badge variant="success" className="flex items-center gap-1">
              <Wifi className="h-3 w-3" /> ThingSpeak Live
            </Badge>
          )}
          <Button onClick={loadData} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-700">{error}</p>
          </div>
        </div>
      )}

      {/* ThingSpeak Config */}
      {!thingspeakConfigured && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Wifi className="h-4 w-4" />
              ThingSpeak Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1 block">Channel ID</label>
                <Input placeholder="e.g. 2468101" value={channelId} onChange={e => setChannelId(e.target.value)} />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1 block">Read API Key</label>
                <Input placeholder="e.g. ABCDEF123456" value={apiKey} onChange={e => setApiKey(e.target.value)} />
              </div>
              <div className="flex items-end">
                <Button onClick={loadData} size="sm">Connect</Button>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Fields: field1=Moisture, field2=pH, field3=Nitrogen, field4=Phosphorus, field5=Potassium
            </p>
          </CardContent>
        </Card>
      )}

      {/* Soil Health Score */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sprout className="h-5 w-5 text-green-600" />
              Soil Health Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center mb-6">
              <p className={`text-6xl font-bold ${getScoreColor(soilHealth?.soil_score || 0)}`}>
                {soilHealth?.soil_score || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">out of 100</p>
              <Progress value={soilHealth?.soil_score || 0} className="mt-3"
                barClassName={soilHealth && soilHealth.soil_score >= 80 ? 'bg-green-500' : soilHealth && soilHealth.soil_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'} />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Degradation Index</span>
                <span className="text-sm font-medium">{soilHealth?.degradation_index || 0}%</span>
              </div>
              <Progress value={soilHealth?.degradation_index || 0}
                barClassName={soilHealth && soilHealth.degradation_index > 40 ? 'bg-red-500' : 'bg-amber-500'} />
            </div>
          </CardContent>
        </Card>

        {/* Current Readings */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Current Sensor Readings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
              {[
                { label: 'Moisture', value: latest?.moisture, unit: '%', status: soilHealth?.moisture?.status, color: 'blue' },
                { label: 'pH', value: latest?.ph, unit: '', status: soilHealth?.ph?.status, color: 'purple' },
                { label: 'Nitrogen', value: latest?.nitrogen, unit: 'mg/kg', status: soilHealth?.nitrogen?.status, color: 'green' },
                { label: 'Phosphorus', value: latest?.phosphorus, unit: 'mg/kg', status: soilHealth?.phosphorus?.status, color: 'amber' },
                { label: 'Potassium', value: latest?.potassium, unit: 'mg/kg', status: soilHealth?.potassium?.status, color: 'red' },
              ].map(item => (
                <div key={item.label} className="rounded-lg bg-gray-50 p-4 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{item.label}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {item.value !== undefined ? Math.round(item.value * 10) / 10 : '-'}
                  </p>
                  <p className="text-xs text-gray-400">{item.unit}</p>
                  {item.status && (
                    <Badge variant={getStatusVariant(item.status)} className="mt-2">{item.status}</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Moisture & pH */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Moisture & pH Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData.slice(-24)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} domain={[0, 14]} />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="Moisture" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="pH" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* NPK Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Nutrient Trends (NPK)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData.slice(-24)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="N" stroke="#22c55e" strokeWidth={2} dot={false} name="Nitrogen" />
                  <Line type="monotone" dataKey="P" stroke="#f59e0b" strokeWidth={2} dot={false} name="Phosphorus" />
                  <Line type="monotone" dataKey="K" stroke="#ef4444" strokeWidth={2} dot={false} name="Potassium" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sprout className="h-5 w-5 text-green-600" />
            Soil Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {soilHealth && soilHealth.nitrogen.status === 'low' || soilHealth?.nitrogen.status === 'very_low' ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm font-medium text-red-700">Nitrogen Deficiency</p>
                <p className="text-xs text-red-600 mt-1">Apply urea or ammonium-based fertilizer. Recommended: 50-80 kg/acre</p>
                <Badge variant="danger" className="mt-2">High Priority</Badge>
              </div>
            ) : null}
            {soilHealth && soilHealth.phosphorus.status === 'low' || soilHealth?.phosphorus.status === 'very_low' ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-700">Phosphorus Supplement Needed</p>
                <p className="text-xs text-amber-600 mt-1">Apply DAP or SSP fertilizer. Recommended: 25-40 kg/acre</p>
                <Badge variant="warning" className="mt-2">Medium Priority</Badge>
              </div>
            ) : null}
            {soilHealth && (soilHealth.moisture as { value: number; status: string }).status === 'moderate' ? (
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="text-sm font-medium text-blue-700">Optimize Irrigation Schedule</p>
                <p className="text-xs text-blue-600 mt-1">Soil moisture is moderate. Consider drip irrigation optimization.</p>
                <Badge variant="info" className="mt-2">Advisory</Badge>
              </div>
            ) : null}
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="text-sm font-medium text-green-700">General Soil Health</p>
              <p className="text-xs text-green-600 mt-1">
                Score: {soilHealth?.soil_score}/100. {soilHealth && soilHealth.soil_score >= 80 ? 'Excellent condition.' :
                  soilHealth && soilHealth.soil_score >= 60 ? 'Good condition, minor improvements recommended.' :
                  'Needs attention. Review nutrient levels.'}
              </p>
              <Badge variant="success" className="mt-2">Status</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
