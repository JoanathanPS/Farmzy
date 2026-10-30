# Farmzy Frontend

Modern Astro-based frontend for Farmzy Smart Farming Platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
src/
├── pages/           # Application pages
│   ├── index.astro           # Main dashboard
│   ├── soilytics/           # Soil intelligence
│   ├── hydroiq/             # Irrigation management
│   ├── marketplace/         # Buy & sell
│   └── agrogo/              # Delivery logistics
├── components/      # Reusable components
├── layouts/        # Page layouts
└── lib/           # Utilities and API clients
    └── api/       # API integration
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
PUBLIC_API_URL=http://localhost:8000
```

### API Integration

The frontend uses API clients in `src/lib/api/` to communicate with the FastAPI backend. The development server automatically proxies `/api/*` requests to the backend.

## 🎨 Styling

- **Tailwind CSS** - Utility-first CSS framework
- **AstroWind Theme** - Pre-configured design system
- **Custom Theme** - Farmzy-specific colors and styles

## 📱 Responsive Design

All pages are built mobile-first and responsive across all device sizes.

## 🛠️ Development

The frontend uses Astro's static site generation with API integration for dynamic data. Pages are server-rendered by default for optimal performance.
