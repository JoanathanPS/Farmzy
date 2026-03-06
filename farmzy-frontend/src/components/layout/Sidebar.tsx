import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingCart,
  Droplets,
  Sprout,
  Truck,
  Settings,
  Leaf,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/marketplace', icon: ShoppingCart, label: 'Marketplace' },
  { to: '/soil', icon: Sprout, label: 'Soil Analytics' },
  { to: '/irrigation', icon: Droplets, label: 'Irrigation' },
  { to: '/delivery', icon: Truck, label: 'Delivery' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2 border-b border-gray-200 px-6 py-5">
          <Leaf className="h-7 w-7 text-green-600" />
          <span className="text-xl font-bold text-gray-900">Farmzy</span>
        </div>

        {/* Farm Info */}
        <div className="border-b border-gray-100 px-6 py-3">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Farm</p>
          <p className="text-sm font-semibold text-gray-700">FARM_PNL_01</p>
          <p className="text-xs text-gray-500">Poonamallee, Chennai</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-green-50 text-green-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-xs text-gray-500">System Online</span>
          </div>
          <p className="mt-1 text-xs text-gray-400">v1.0.0</p>
        </div>
      </div>
    </aside>
  );
}
