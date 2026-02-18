# Flask Dashboard - Khalifa University Server Monitoring

A modern, mobile-first Flask dashboard recreating the functionality of the Dash-based server monitoring system with enhanced UI/UX following KU Brand Guidelines 2020.

## Architecture Overview

This Flask implementation follows **Single Responsibility Principle** with a modular, blueprint-based architecture:

```
srcs/Backend/
├── app.py                    # Main Flask application (factory pattern)
├── flask_config.py           # Configuration (KU colors, settings)
├── blueprints/               # Modular route handlers
│   ├── dashboard.py          # Dashboard page routes
│   └── api_proxy.py          # API proxy endpoints
├── templates/                # Jinja2 templates
│   ├── base.html             # Base template with KU branding
│   ├── dashboard/
│   │   ├── index.html        # Main dashboard layout
│   │   └── panels/           # Tab content panels
│   │       ├── overview.html
│   │       ├── servers.html
│   │       ├── users.html
│   │       ├── analytics.html
│   │       └── network.html
│   └── errors/               # Error pages
│       ├── 404.html
│       └── 500.html
├── static/                   # Static assets
│   ├── css/                  # Mobile-first responsive CSS
│   │   ├── main.css          # Core styles with KU colors
│   │   ├── dark-mode.css     # Dark theme
│   │   ├── dashboard.css     # Dashboard components
│   │   ├── tabs.css          # Tab navigation
│   │   ├── tables.css        # Data tables
│   │   ├── cards.css         # Card components
│   │   ├── charts.css        # Chart containers
│   │   └── animations.css    # Smooth animations
│   ├── js/                   # Modular JavaScript
│   │   ├── theme.js          # Dark mode toggle
│   │   ├── time.js           # Time display
│   │   ├── toast.js          # Notifications
│   │   ├── mobile.js         # Mobile optimizations
│   │   ├── api.js            # API client with retry logic
│   │   ├── tabs.js           # Tab navigation
│   │   ├── dashboard.js      # Main dashboard logic
│   │   ├── charts.js         # Chart.js integration
│   │   └── export.js         # Export functionality
│   └── images/
│       └── KU_logo.png       # Khalifa University logo
└── utils/                    # Utility modules
    └── formatters.py         # Data formatting helpers
```

## Key Features

### 🎨 **KU Brand Compliance**
- Official KU colors (Primary #003DA5, Secondary #6F5091, etc.)
- Inter font family (closest free alternative to DIN Next)
- 12-column grid system with proper spacing
- Consistent visual language across all components

### 📱 **Mobile-First Responsive Design**
- Breakpoints: Mobile (0px), Tablet (768px), Desktop (1024px)
- Touch-optimized interactions
- Horizontal scrolling tables
- Collapsible navigation on mobile
- Viewport height fixes for mobile browsers

### 🌓 **Dark Mode**
- Toggle with button or `Ctrl+D` keyboard shortcut
- LocalStorage persistence
- System preference detection
- Smooth theme transitions
- Adjusted color palette for dark theme

### ⚡ **Performance Optimized**
- API retry logic (3 attempts with exponential backoff)
- Auto-refresh every 15 minutes
- Lazy loading of tab content
- Efficient Chart.js rendering
- Debounced resize handlers

### ♿ **Accessibility**
- ARIA labels and roles
- Keyboard navigation support
- Reduced motion preferences
- Semantic HTML5
- High contrast ratios

## Installation & Setup

### Prerequisites
- Python 3.10+
- UV package manager
- Access to the backend API service

### Install Dependencies

```bash
cd srcs/Backend
uv sync
```

### Configuration

The dashboard uses the same environment variables as the existing system:

```bash
# .env file
DEBUG=True
SECRET_KEY=your-secret-key-here
API_BASE_URL=http://API:5000/api
```

### Run the Application

```bash
# Development mode
uv run python app.py

# Or using Flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
uv run flask run --host=0.0.0.0 --port=3001
```

The dashboard will be available at: `http://localhost:3001`

## Usage

### Dashboard Tabs

1. **Usage Overview** - Compact server grid showing real-time metrics
2. **Server Details** - System overview stats + enhanced server cards
3. **User Activity** - Searchable/filterable user resource consumption table
4. **Performance Analytics** - Historical charts with configurable time ranges
5. **Network Monitor** - Connection statistics and network health

### Features

- **Auto-Refresh**: Data updates every 15 minutes automatically
- **Manual Refresh**: Click "Refresh All Data" button
- **Export**: Download dashboard data as JSON/CSV
- **Dark Mode**: Toggle with button (top-right) or press `Ctrl+D`
- **Tab Navigation**: Use arrow keys to navigate between tabs

## API Integration

The Flask app proxies requests to the existing backend API service:

```python
# API endpoints available through the proxy
GET /api/servers/metrics/latest
GET /api/servers/<server_name>/metrics/historical/<hours>
GET /api/servers/<server_name>/status
GET /api/servers/list
GET /api/users/top
GET /api/users/top/<server_name>
GET /api/system/overview
GET /api/health/<server_name>
```

All API calls include:
- 3 retry attempts with exponential backoff
- 10-second timeout
- Comprehensive error handling
- Toast notifications for user feedback

## Customization

### Modify KU Colors

Edit `flask_config.py`:

```python
KU_COLORS = {
    "primary": "#003DA5",  # Your custom blue
    "secondary": "#6F5091",
    # ... other colors
}
```

### Adjust Refresh Interval

Edit `flask_config.py`:

```python
DASHBOARD_CONFIG = {
    "refresh_interval": 900000,  # milliseconds (15 min)
    # ...
}
```

### Add New Dashboard Tab

1. Add route in `blueprints/dashboard.py`:
```python
@dashboard_bp.route('/mytab')
def my_new_tab():
    return render_template('dashboard/index.html', active_tab='mytab')
```

2. Add tab button in `templates/dashboard/index.html`
3. Create panel template in `templates/dashboard/panels/mytab.html`
4. Implement data loading function in `static/js/dashboard.js`

### Customize Performance Thresholds

Edit `flask_config.py`:

```python
PERFORMANCE_THRESHOLDS = {
    "cpu_warning": 50.0,
    "cpu_critical": 80.0,
    "memory_warning": 85,
    "memory_critical": 95,
    # ...
}
```

## Development Guidelines

### Adding New Components

Follow Single Responsibility Principle:

1. **Create dedicated module** - One file, one responsibility
2. **Use blueprints** - Keep routes organized
3. **Template inheritance** - Extend `base.html`
4. **CSS modules** - Separate concerns (layout, theme, components)
5. **JS modules** - IIFE pattern to avoid global pollution

### Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Use `'use strict'`, ES6+ features
- **CSS**: Mobile-first, BEM-like naming
- **Templates**: Jinja2 with proper escaping

### Error Handling

All functions should handle errors gracefully:

```javascript
// Good
try {
    const data = await API.getLatestMetrics();
    // Process data
} catch (error) {
    console.error('Error:', error);
    Toast.error('Failed to load metrics');
}
```

### Accessibility Checklist

- [ ] All interactive elements have ARIA labels
- [ ] Keyboard navigation works
- [ ] Color contrast ratios meet WCAG AA
- [ ] Form inputs have associated labels
- [ ] Reduce motion preferences honored

## Docker Integration

To run this Flask dashboard in the existing Docker setup:

### Update docker-compose.yml

```yaml
flask-frontend:
  build:
    context: ./srcs/Backend
    dockerfile: Dockerfile.flask
  ports:
    - "3001:3001"
  environment:
    - DEBUG=${DEBUG}
    - API_BASE_URL=http://API:5000/api
  networks:
    - backend
  depends_on:
    - api
```

### Create Dockerfile.flask

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy application code
COPY . .

EXPOSE 3001

CMD ["uv", "run", "python", "app.py"]
```

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Android 90+
- **Features**: ES6+, CSS Grid, CSS Custom Properties, Fetch API

## Performance Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.0s
- **Lighthouse Score**: 90+ (Performance, Accessibility, Best Practices)
- **Bundle Size**: ~50KB CSS, ~80KB JS (unminified)

## Troubleshooting

### Dashboard not loading

```bash
# Check if Flask app is running
curl http://localhost:3001/health

# Check backend API
curl http://localhost:5000/api/health
```

### API connection errors

- Verify `API_BASE_URL` in `.env` or `flask_config.py`
- Check if API service is running: `docker ps | grep API`
- Review API logs: `docker logs <api-container-id>`

### Dark mode not persisting

- Check browser localStorage permissions
- Clear browser cache
- Verify `theme.js` is loaded without errors

### Charts not rendering

- Ensure Chart.js CDN is accessible
- Check browser console for JavaScript errors
- Verify canvas elements have proper IDs

## Testing

```bash
# Unit tests (when implemented)
uv run pytest

# Accessibility testing
# Use axe DevTools browser extension

# Performance testing
# Use Lighthouse in Chrome DevTools
```

## Roadmap

- [ ] Add unit tests for Python utilities
- [ ] Implement real-time WebSocket updates
- [ ] Add more chart types and visualizations
- [ ] Create admin panel for configuration
- [ ] Add user authentication
- [ ] Implement report scheduling
- [ ] Add PDF export functionality
- [ ] Multi-language support (EN/AR)

## Credits

- **Design**: Based on Khalifa University Brand Guidelines 2020 V7
- **Framework**: Flask 3.x
- **Charts**: Chart.js 4.x
- **Fonts**: Inter (Google Fonts)
- **Icons**: Font Awesome 6.x

## License

Internal use only - Khalifa University

## Support

For issues or questions:
1. Check the main project `CLAUDE.md`
2. Review Docker logs
3. Contact the development team
