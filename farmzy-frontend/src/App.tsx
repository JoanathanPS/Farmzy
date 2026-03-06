import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import Dashboard from '@/pages/Dashboard';
import Marketplace from '@/pages/Marketplace';
import SoilAnalytics from '@/pages/SoilAnalytics';
import Irrigation from '@/pages/Irrigation';
import Delivery from '@/pages/Delivery';
import Settings from '@/pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/soil" element={<SoilAnalytics />} />
          <Route path="/irrigation" element={<Irrigation />} />
          <Route path="/delivery" element={<Delivery />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
