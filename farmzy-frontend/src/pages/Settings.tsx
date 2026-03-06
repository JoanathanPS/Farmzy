import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Settings as SettingsIcon, Wifi, Database, User, LogIn, LogOut, KeyRound,
} from 'lucide-react';
import { isSupabaseConfigured, signIn, signUp, signOut, getSession } from '@/lib/supabase';

export default function Settings() {
  const [supabaseUrl, setSupabaseUrl] = useState(import.meta.env.VITE_SUPABASE_URL || '');
  const [supabaseKey, setSupabaseKey] = useState(import.meta.env.VITE_SUPABASE_ANON_KEY || '');
  const [thingspeakChannel, setThingspeakChannel] = useState(import.meta.env.VITE_THINGSPEAK_CHANNEL_ID || '');
  const [thingspeakKey, setThingspeakKey] = useState(import.meta.env.VITE_THINGSPEAK_API_KEY || '');
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://localhost:8000');

  // Auth state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Check session on mount
  useState(() => {
    getSession().then(session => {
      if (session) {
        setIsLoggedIn(true);
        setUserEmail(session.user?.email || null);
      }
    });
  });

  const handleSignUp = async () => {
    if (!email || !password) return;
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      await signUp(email, password);
      setAuthMessage({ type: 'success', text: 'Account created! Check your email for verification.' });
    } catch (err) {
      setAuthMessage({ type: 'error', text: err instanceof Error ? err.message : 'Sign up failed' });
    }
    setAuthLoading(false);
  };

  const handleSignIn = async () => {
    if (!email || !password) return;
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const data = await signIn(email, password);
      setIsLoggedIn(true);
      setUserEmail(data.user?.email || email);
      setAuthMessage({ type: 'success', text: 'Signed in successfully!' });
    } catch (err) {
      setAuthMessage({ type: 'error', text: err instanceof Error ? err.message : 'Sign in failed' });
    }
    setAuthLoading(false);
  };

  const handleSignOut = async () => {
    setAuthLoading(true);
    try {
      await signOut();
      setIsLoggedIn(false);
      setUserEmail(null);
      setAuthMessage({ type: 'success', text: 'Signed out.' });
    } catch (err) {
      setAuthMessage({ type: 'error', text: err instanceof Error ? err.message : 'Sign out failed' });
    }
    setAuthLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">Configure integrations and manage your account</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Supabase Auth */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-green-600" />
              Authentication
              {isSupabaseConfigured ? (
                <Badge variant="success">Supabase Connected</Badge>
              ) : (
                <Badge variant="warning">Not Configured</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!isSupabaseConfigured ? (
              <p className="text-sm text-gray-500 py-4">
                Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables to enable authentication.
              </p>
            ) : isLoggedIn ? (
              <div className="space-y-4">
                <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-green-600" />
                    <p className="text-sm font-medium text-green-700">Signed in as {userEmail}</p>
                  </div>
                </div>
                <Button variant="outline" onClick={handleSignOut} disabled={authLoading}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
                  <Input type="email" placeholder="your@email.com" value={email}
                    onChange={e => setEmail(e.target.value)} />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Password</label>
                  <Input type="password" placeholder="Password" value={password}
                    onChange={e => setPassword(e.target.value)} />
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleSignIn} disabled={authLoading}>
                    <LogIn className="h-4 w-4 mr-2" />
                    Sign In
                  </Button>
                  <Button variant="outline" onClick={handleSignUp} disabled={authLoading}>
                    Sign Up
                  </Button>
                </div>
              </div>
            )}
            {authMessage && (
              <div className={`mt-3 rounded-lg p-3 text-sm ${authMessage.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {authMessage.text}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Supabase Config */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              Supabase Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Supabase URL</label>
                <Input placeholder="https://xxx.supabase.co" value={supabaseUrl}
                  onChange={e => setSupabaseUrl(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Anon Key</label>
                <Input placeholder="eyJhbGciOiJIUz..." value={supabaseKey}
                  onChange={e => setSupabaseKey(e.target.value)} type="password" />
              </div>
              <p className="text-xs text-gray-500">
                These values should be set as environment variables (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
                in a .env file at the project root. Restart the dev server after changes.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ThingSpeak Config */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-5 w-5 text-amber-600" />
              ThingSpeak Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Channel ID</label>
                <Input placeholder="e.g. 2468101" value={thingspeakChannel}
                  onChange={e => setThingspeakChannel(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Read API Key</label>
                <Input placeholder="e.g. ABCDEF123456" value={thingspeakKey}
                  onChange={e => setThingspeakKey(e.target.value)} type="password" />
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <p className="text-xs font-medium text-gray-500 mb-2">Field Mapping (ESP32)</p>
                <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                  <span>field1: Moisture (%)</span>
                  <span>field2: pH</span>
                  <span>field3: Nitrogen (mg/kg)</span>
                  <span>field4: Phosphorus (mg/kg)</span>
                  <span>field5: Potassium (mg/kg)</span>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Set VITE_THINGSPEAK_CHANNEL_ID and VITE_THINGSPEAK_API_KEY in .env file.
                Or configure directly on the Soil Analytics page.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Backend API Config */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-purple-600" />
              Backend API
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">API Base URL</label>
                <Input placeholder="http://localhost:8000" value={apiUrl}
                  onChange={e => setApiUrl(e.target.value)} />
              </div>
              <p className="text-xs text-gray-500">
                Set VITE_API_URL in .env file. Defaults to http://localhost:8000.
              </p>

              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">API Endpoints</p>
                <div className="rounded-lg bg-gray-50 p-3 space-y-1 text-xs text-gray-600 font-mono">
                  <p>/api/unified/dashboard - Dashboard data</p>
                  <p>/api/soil/* - Soil analytics</p>
                  <p>/api/irrigation/* - Irrigation management</p>
                  <p>/api/marketplace/* - Marketplace operations</p>
                  <p>/api/delivery/* - Delivery management</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Environment Setup Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5 text-gray-600" />
            Environment Setup
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-gray-900 p-4 text-sm font-mono text-green-400">
            <p className="text-gray-500"># Create .env file in farmzy-frontend/</p>
            <p className="mt-1">VITE_API_URL=http://localhost:8000</p>
            <p>VITE_SUPABASE_URL=https://your-project.supabase.co</p>
            <p>VITE_SUPABASE_ANON_KEY=your-anon-key</p>
            <p>VITE_THINGSPEAK_CHANNEL_ID=your-channel-id</p>
            <p>VITE_THINGSPEAK_API_KEY=your-read-api-key</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
