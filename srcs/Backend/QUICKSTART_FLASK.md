# Quick Start Guide - Flask Dashboard

Get the Flask-based Khalifa University Server Monitoring Dashboard up and running in minutes.

## 🚀 Quick Start (Local Development)

### 1. Navigate to Backend Directory

```bash
cd srcs/Backend
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Set Environment Variables

```bash
# Optional: Create .env file or use existing one
export DEBUG=True
export API_BASE_URL=http://localhost:5000/api
```

### 4. Run the Application

```bash
uv run python app.py
```

### 5. Open in Browser

Navigate to: `http://localhost:3001`

## 🐳 Docker Deployment

### Option 1: Add to existing docker-compose.yml

Add this service to your `docker-compose.yml`:

```yaml
flask-dashboard:
  build:
    context: ./srcs/Backend
    dockerfile: Dockerfile.flask
  container_name: flask-dashboard
  ports:
    - "3001:3001"
  environment:
    - DEBUG=${DEBUG}
    - SECRET_KEY=${SECRET_KEY}
  networks:
    - backend
  depends_on:
    - api
  init: true
  restart: unless-stopped
```

Then run:

```bash
docker-compose up -d flask-dashboard
```

### Option 2: Standalone Docker Build

```bash
cd srcs/Backend

# Build the image
docker build -f Dockerfile.flask -t ku-flask-dashboard .

# Run the container
docker run -d \
  --name flask-dashboard \
  -p 3001:3001 \
  -e DEBUG=True \
  -e API_BASE_URL=http://api:5000/api \
  --network backend \
  ku-flask-dashboard
```

## 📋 Verification

### Check Application Health

```bash
curl http://localhost:3001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "flask-dashboard"
}
```

### Check Dashboard Access

Open browser: `http://localhost:3001`

You should see:
- KU logo in header
- Tab navigation (Usage Overview, Server Details, etc.)
- Dark mode toggle button
- System time display

### Verify API Connection

The dashboard should automatically fetch data from the backend API. Check browser console for:
- No CORS errors
- Successful API calls
- Data loading in tabs

## 🎨 Features to Test

### 1. Dark Mode
- Click sun/moon icon (top-right)
- Or press `Ctrl+D`
- Theme should persist on page reload

### 2. Tab Navigation
- Click each tab
- Use keyboard arrows when focused on tabs
- Data should load for each tab

### 3. Auto-Refresh
- Wait 15 minutes
- Data should automatically update
- Or click "Refresh All Data" button

### 4. Mobile Responsiveness
- Resize browser window
- Test on mobile device
- Verify touch interactions

### 5. Export Functionality
- Click "Export Report" button
- Should download JSON file with dashboard data

## 🔧 Configuration

### Change Port

Edit `app.py`:
```python
app.run(host='0.0.0.0', port=3001)  # Change 3001 to desired port
```

### Modify Refresh Interval

Edit `flask_config.py`:
```python
DASHBOARD_CONFIG = {
    "refresh_interval": 900000,  # Change to desired milliseconds
}
```

### Update API URL

Set environment variable:
```bash
export API_BASE_URL=http://your-api-host:5000/api
```

Or edit `flask_config.py`:
```python
API_BASE_URL = os.getenv("API_BASE_URL", "http://your-api-host:5000/api")
```

## 🐛 Troubleshooting

### Issue: Dashboard not loading

**Solution:**
```bash
# Check if app is running
curl http://localhost:3001/health

# Check logs
# Docker: docker logs flask-dashboard
# Local: Check terminal output
```

### Issue: "Cannot connect to API service" error

**Solution:**
1. Verify API service is running:
   ```bash
   curl http://localhost:5000/api/health
   ```
2. Check `API_BASE_URL` configuration
3. Ensure network connectivity (in Docker, check network)

### Issue: Dark mode not working

**Solution:**
1. Clear browser localStorage
2. Check browser console for JavaScript errors
3. Verify `theme.js` is loaded

### Issue: Charts not displaying

**Solution:**
1. Check internet connection (Chart.js CDN)
2. Verify browser console for errors
3. Ensure canvas elements exist in DOM

### Issue: CORS errors

**Solution:**
1. Backend API must have CORS enabled
2. Check `flask_cors` is installed
3. Verify API allows requests from dashboard origin

## 📱 Testing Checklist

- [ ] Dashboard loads at http://localhost:3001
- [ ] Health check endpoint responds
- [ ] All tabs are accessible
- [ ] Server metrics display correctly
- [ ] Dark mode toggle works
- [ ] Data refreshes (manual and auto)
- [ ] Export functionality works
- [ ] Mobile responsive design works
- [ ] No console errors
- [ ] API calls succeed

## 🔐 Production Deployment

### Security Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Set `DEBUG=False`
- [ ] Use HTTPS (configure reverse proxy)
- [ ] Enable CORS only for specific origins
- [ ] Set secure session cookies
- [ ] Review file permissions
- [ ] Use non-root user (already in Dockerfile)

### Performance Optimization

- [ ] Enable gzip compression
- [ ] Configure CDN for static assets
- [ ] Set proper cache headers
- [ ] Use production WSGI server (gunicorn/uwsgi)
- [ ] Monitor resource usage

### Example Production Setup with Gunicorn

```bash
# Install gunicorn
uv add gunicorn

# Run with gunicorn
uv run gunicorn -w 4 -b 0.0.0.0:3001 app:app
```

Update Dockerfile.flask:
```dockerfile
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:3001", "app:app"]
```

## 📚 Next Steps

1. **Customize Branding**: Modify colors in `flask_config.py`
2. **Add Authentication**: Implement user login (Flask-Login)
3. **Add More Charts**: Extend analytics panel
4. **Enable Notifications**: WebSocket for real-time alerts
5. **Add Tests**: Write unit and integration tests

## 🆘 Getting Help

- Read full documentation: `README_FLASK.md`
- Check main project docs: `../../CLAUDE.md`
- Review API documentation: `../Backend/api.py`
- Check Docker logs: `docker logs flask-dashboard`

## 📖 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [KU Brand Guidelines](../../DesginGuideLine/KU_Guidelines_2020_V7.pdf)
- [UV Package Manager](https://docs.astral.sh/uv/)

---

**Ready to go!** 🎉 Your Flask dashboard should now be running and accessible.
