# Migration Guide: Dash to Flask Dashboard

This guide helps you transition from the Dash-based dashboard to the new Flask implementation.

## Why Migrate?

### Benefits of Flask Dashboard

1. **More Customizable** - Full control over HTML, CSS, and JavaScript
2. **Better Performance** - Smaller bundle size, optimized loading
3. **Easier Maintenance** - Standard web technologies (HTML/CSS/JS)
4. **Mobile-First Design** - Optimized for phones and tablets
5. **Enhanced Dark Mode** - Smoother transitions, better colors
6. **Standard Flask Patterns** - Easier for Flask developers to understand

### What Stays the Same

- All dashboard functionality
- All API endpoints
- Data structures
- Database schema
- Docker network configuration
- Environment variables

## Side-by-Side Comparison

| Feature | Dash (Port 3000) | Flask (Port 3001) |
|---------|------------------|-------------------|
| Framework | Dash/Plotly | Flask + Chart.js |
| Auto-refresh | 15 min | 15 min (configurable) |
| Dark mode | ✅ | ✅ Enhanced |
| Mobile support | Basic | Mobile-first |
| Tabs | ✅ | ✅ + Keyboard nav |
| Export | Planned | ✅ JSON/CSV |
| Charts | Plotly | Chart.js |
| Customization | Limited | Highly flexible |

## Running Both Simultaneously

You can run both dashboards side-by-side for testing:

### Update docker-compose.yml

```yaml
services:
  # Existing Dash frontend (port 3000)
  frontend:
    build:
      context: ./srcs/Frontend
    ports:
      - "3000:3000"
    # ... existing config

  # New Flask frontend (port 3001)
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
    init: true
```

### Start Both Services

```bash
docker-compose up -d frontend flask-frontend
```

### Access Points

- **Dash Dashboard**: http://localhost:3000
- **Flask Dashboard**: http://localhost:3001

### Compare and Test

Test both dashboards with the same data:
1. Open both in separate browser tabs
2. Verify data consistency
3. Compare performance
4. Test mobile responsiveness
5. Evaluate user experience

## Migration Paths

### Path 1: Gradual Migration (Recommended)

**Phase 1: Testing** (Week 1-2)
1. Deploy Flask dashboard on different port (3001)
2. Run both dashboards in parallel
3. Test Flask dashboard thoroughly
4. Gather user feedback

**Phase 2: Evaluation** (Week 3)
1. Compare performance metrics
2. Validate all features work
3. Test with production data
4. Train users on new interface

**Phase 3: Switch** (Week 4)
1. Set Flask as default (port 3000)
2. Keep Dash as backup (port 3001)
3. Monitor for issues
4. Gather feedback

**Phase 4: Finalize** (Week 5+)
1. Remove Dash if all is well
2. Update documentation
3. Archive old code

### Path 2: Direct Switch

**For Quick Migration:**

1. **Stop Dash service**
```bash
docker-compose stop frontend
```

2. **Update docker-compose.yml**
```yaml
flask-frontend:
  build:
    context: ./srcs/Backend
    dockerfile: Dockerfile.flask
  ports:
    - "3000:3001"  # Map to port 3000
  # ... rest of config
```

3. **Update Dockerfile.flask port**
```dockerfile
EXPOSE 3000
```

4. **Update app.py port**
```python
app.run(host='0.0.0.0', port=3000)
```

5. **Deploy**
```bash
docker-compose up -d flask-frontend
```

## Feature Mapping

### Dash Components → Flask Equivalents

| Dash Component | Flask Implementation | Location |
|----------------|---------------------|----------|
| `dcc.Tabs` | Custom tabs with JS | `templates/dashboard/index.html` |
| `dcc.Interval` | JavaScript setInterval | `static/js/dashboard.js` |
| `dcc.Download` | JavaScript download | `static/js/export.js` |
| `html.Div` | HTML templates | `templates/` |
| Dash callbacks | API + JavaScript | `static/js/dashboard.js` |
| Plotly graphs | Chart.js | `static/js/charts.js` |

### Configuration Migration

**Dash (config.py):**
```python
KU_COLORS = {...}
DASHBOARD_CONFIG = {...}
```

**Flask (flask_config.py):**
```python
KU_COLORS = {...}  # Same
DASHBOARD_CONFIG = {...}  # Same
```

No changes needed - configurations are compatible!

### Custom Modifications

If you customized the Dash dashboard:

1. **Colors**: Update `flask_config.py` → `KU_COLORS`
2. **Layout**: Modify templates in `templates/dashboard/`
3. **Styling**: Edit CSS files in `static/css/`
4. **Behavior**: Update JavaScript in `static/js/`
5. **Data processing**: Edit `utils/formatters.py`

## Data Migration

**No data migration needed!**

Both dashboards use the same:
- Database schema
- API endpoints
- Data structures

## Environment Variables

Both use the same `.env` file:

```bash
# Works for both Dash and Flask
DEBUG=True
POSTGRES_PASSWORD=your_password
API_BASE_URL=http://API:5000/api
# ... server credentials
```

## Troubleshooting Migration

### Issue: Both dashboards conflict

**Solution:** Run on different ports
```yaml
frontend:
  ports:
    - "3000:3000"

flask-frontend:
  ports:
    - "3001:3001"
```

### Issue: API connection errors

**Solution:** Verify network
```yaml
flask-frontend:
  networks:
    - backend  # Must be same network as API
```

### Issue: Missing KU logo

**Solution:** Copy logo
```bash
cp srcs/Frontend/assets/KU_logo.png srcs/Backend/static/images/
```

### Issue: Charts not displaying

**Solution:**
1. Check internet connection (Chart.js CDN)
2. Or download Chart.js locally:
```bash
cd srcs/Backend/static/js
curl -o chart.min.js https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
```

Update templates:
```html
<script src="{{ url_for('static', filename='js/chart.min.js') }}"></script>
```

## Rollback Plan

If you need to revert to Dash:

1. **Stop Flask service**
```bash
docker-compose stop flask-frontend
```

2. **Start Dash service**
```bash
docker-compose up -d frontend
```

3. **Verify**
```bash
curl http://localhost:3000
```

## User Training

### Key Differences for End Users

1. **Tabs**: Same functionality, new visual style
2. **Dark Mode**: Press Ctrl+D for quick toggle
3. **Export**: New feature - download data as JSON/CSV
4. **Mobile**: Better experience on phones/tablets
5. **Performance**: Faster loading, smoother animations

### Quick Start for Users

1. Navigate to http://localhost:3001 (or 3000 after switch)
2. Use tabs to navigate (Overview, Servers, Users, etc.)
3. Toggle dark mode with sun/moon button (top-right)
4. Click "Refresh All Data" to update manually
5. Click "Export Report" to download data

## Performance Comparison

Test both dashboards and compare:

### Metrics to Monitor

1. **Page Load Time**
   - Dash: Measure with browser DevTools
   - Flask: Measure with browser DevTools

2. **Memory Usage**
   - Check browser task manager
   - Compare after 1 hour of use

3. **Network Traffic**
   - Monitor API calls
   - Check payload sizes

4. **User Experience**
   - Survey users
   - Collect feedback
   - Monitor usage patterns

### Expected Results

Flask should show:
- ✅ Faster initial load (smaller bundle)
- ✅ Lower memory usage
- ✅ Smoother animations
- ✅ Better mobile performance

## Customization After Migration

### Adding New Features

**Dash approach:**
```python
# Dash callback
@app.callback(...)
def update_graph(...):
    return new_figure
```

**Flask approach:**
```javascript
// JavaScript function
async function updateGraph() {
    const data = await API.getSomeData();
    ChartManager.updateChart('my-chart', data);
}
```

### Styling Changes

**Dash:**
```python
# Inline styles
html.Div(style={'color': 'blue'})
```

**Flask:**
```css
/* External CSS */
.my-component {
    color: blue;
}
```

## Support During Migration

### Resources

- **Flask Docs**: `README_FLASK.md`
- **Quick Start**: `QUICKSTART_FLASK.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **Original Docs**: `../../Docs/INDEX.md`

### Getting Help

1. Check documentation files
2. Review browser console for errors
3. Check Docker logs: `docker logs flask-frontend`
4. Compare with working Dash implementation
5. Contact development team

## Post-Migration Checklist

After switching to Flask:

- [ ] All tabs load correctly
- [ ] Data displays accurately
- [ ] Charts render properly
- [ ] Dark mode works
- [ ] Export functionality works
- [ ] Mobile view is responsive
- [ ] Auto-refresh is working
- [ ] No console errors
- [ ] Users are trained
- [ ] Documentation updated
- [ ] Monitoring in place
- [ ] Backup plan ready

## Timeline Example

### 4-Week Migration Plan

**Week 1:**
- Deploy Flask on port 3001
- Internal testing
- Identify any issues

**Week 2:**
- User acceptance testing
- Gather feedback
- Fix issues
- Performance testing

**Week 3:**
- Final testing
- User training
- Prepare switch

**Week 4:**
- Switch to Flask (port 3000)
- Monitor closely
- Keep Dash as backup
- Document lessons learned

**Week 5+:**
- Remove Dash if stable
- Archive old code
- Update documentation

## Success Criteria

Migration is successful when:

1. ✅ All features work as before
2. ✅ No data loss or inconsistencies
3. ✅ Performance is equal or better
4. ✅ Users can perform all tasks
5. ✅ Mobile experience is improved
6. ✅ No critical bugs for 2 weeks
7. ✅ User feedback is positive
8. ✅ Documentation is complete

## Conclusion

The Flask dashboard provides the same functionality as Dash with enhanced UI/UX and better mobile support. Migration can be done gradually or directly, with both options well-supported.

**Recommended approach**: Run both in parallel for 2-4 weeks, then switch to Flask while keeping Dash as backup for another 2 weeks.

---

**Questions?** Refer to the comprehensive documentation:
- README_FLASK.md
- QUICKSTART_FLASK.md
- IMPLEMENTATION_SUMMARY.md
