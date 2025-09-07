class AlertsPage {
    constructor() {
        this.alerts = [];
        this.filteredAlerts = [];
        this.filters = {
            severity: '',
            status: '',
            category: '',
            search: ''
        };
        this.selectedAlerts = new Set();
        this.currentView = 'list';
        this.bulkMode = false;
        this.init();
    }

    init() {
        this.loadMockData();
        this.render();
        this.attachEventListeners();
        this.loadAlerts();
    }

    loadMockData() {
        this.alerts = [
            {
                id: '1',
                title: 'Camera Connection Lost',
                message: 'Entrance Gate camera has lost connection and is no longer streaming',
                severity: 'critical',
                status: 'active',
                category: 'camera',
                timestamp: new Date(Date.now() - 15 * 60 * 1000),
                source: 'Entrance Gate',
                acknowledged: false,
                acknowledgedBy: null,
                resolvedAt: null,
                details: {
                    cameraId: '1',
                    lastSeen: new Date(Date.now() - 15 * 60 * 1000),
                    errorCode: 'CONN_TIMEOUT'
                }
            },
            {
                id: '2',
                title: 'High Detection Volume',
                message: 'Unusual spike in vehicle detections at Parking Lot A-120% above normal',
                severity: 'warning',
                status: 'acknowledged',
                category: 'detection',
                timestamp: new Date(Date.now() - 45 * 60 * 1000),
                source: 'Parking Lot A',
                acknowledged: true,
                acknowledgedBy: 'admin',
                acknowledgedAt: new Date(Date.now() - 30 * 60 * 1000),
                resolvedAt: null,
                details: {
                    threshold: 50,
                    currentRate: 110,
                    normalRate: 45
                }
            },
            {
                id: '3',
                title: 'Storage Space Warning',
                message: 'Detection images storage is at 85% capacity',
                severity: 'warning',
                status: 'active',
                category: 'system',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
                source: 'Storage System',
                acknowledged: false,
                acknowledgedBy: null,
                resolvedAt: null,
                details: {
                    usedSpace: '8.5GB',
                    totalSpace: '10GB',
                    percentage: 85
                }
            },
            {
                id: '4',
                title: 'Detection Accuracy Drop',
                message: 'Loading Dock camera accuracy has dropped below 90% threshold',
                severity: 'warning',
                status: 'resolved',
                category: 'detection',
                timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
                source: 'Loading Dock',
                acknowledged: true,
                acknowledgedBy: 'operator',
                acknowledgedAt: new Date(Date.now() - 3 * 60 * 60 * 1000),
                resolvedAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
                details: {
                    currentAccuracy: 87.5,
                    threshold: 90,
                    previousAccuracy: 94.2
                }
            },
            {
                id: '5',
                title: 'Scheduled Maintenance Due',
                message: 'Side Entrance camera is due for scheduled maintenance',
                severity: 'info',
                status: 'active',
                category: 'maintenance',
                timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
                source: 'Side Entrance',
                acknowledged: false,
                acknowledgedBy: null,
                resolvedAt: null,
                details: {
                    lastMaintenance: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
                    scheduledDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
                }
            },
            {
                id: '6',
                title: 'License Plate Blocklist Match',
                message: 'Vehicle with blocked license plate ABC-123 detected at Entrance Gate',
                severity: 'critical',
                status: 'acknowledged',
                category: 'security',
                timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
                source: 'Entrance Gate',
                acknowledged: true,
                acknowledgedBy: 'security',
                acknowledgedAt: new Date(Date.now() - 7 * 60 * 60 * 1000),
                resolvedAt: null,
                details: {
                    licensePlate: 'ABC-123',
                    blocklistReason: 'Suspended access',
                    detectionImage: 'detection_001.jpg'
                }
            }
        ];
    }render() {
        const container = document.getElementById('alerts');
        if (!container) return;

        container.innerHTML = this.getTemplate();
        this.renderAlerts();
    }

    getTemplate() {
        const alertCounts = this.getAlertSummary();
        return `
            <div class="page-header">
                <h1 class="page-title">Alerts</h1>
                <p class="page-subtitle">System notifications and alert management</p>
            </div>

            <!-- Alert Summary Cards -->
            <div class="alert-summary-cards">
                <div class="summary-card critical">
                    <div class="summary-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-count">${alertCounts.critical}</div>
                        <div class="summary-label">Critical</div>
                    </div>
                </div>
                <div class="summary-card warning">
                    <div class="summary-icon">
                        <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-count">${alertCounts.warning}</div>
                        <div class="summary-label">Warning</div>
                    </div>
                </div>
                <div class="summary-card info">
                    <div class="summary-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-count">${alertCounts.info}</div>
                        <div class="summary-label">Info</div>
                    </div>
                </div>
                <div class="summary-card resolved">
                    <div class="summary-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-count">${alertCounts.resolved}</div>
                        <div class="summary-label">Resolved</div>
                    </div>
                </div>
            </div>

            <!-- Alert Controls -->
            <div class="alert-controls">
                <div class="quick-actions">
                    <button class="quick-action-btn" id="acknowledge-all-btn">
                        <i class="fas fa-check"></i>
                        <span>Acknowledge All</span>
                    </button>
                    <button class="quick-action-btn" id="bulk-actions-btn">
                        <i class="fas fa-tasks"></i>
                        <span>Bulk Actions</span>
                    </button>
                    <button class="quick-action-btn" id="export-alerts-btn">
                        <i class="fas fa-download"></i>
                        <span>Export</span>
                    </button>
                    <button class="quick-action-btn" id="refresh-alerts-btn">
                        <i class="fas fa-sync-alt"></i>
                        <span>Refresh</span>
                    </button>
                </div>
                <div class="view-controls">
                    <button class="view-btn ${this.currentView === 'list' ? 'active' : ''}" data-view="list">
                        <i class="fas fa-list"></i>
                    </button>
                    <button class="view-btn ${this.currentView === 'cards' ? 'active' : ''}" data-view="cards">
                        <i class="fas fa-th"></i>
                    </button>
                </div>
            </div>

            <!-- Alert Filters -->
            <div class="alert-filters">
                <div class="filter-group">
                    <label for="alert-severity-filter">Severity:</label>
                    <select id="alert-severity-filter" class="filter-select">
                        <option value="">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="warning">Warning</option>
                        <option value="info">Info</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="alert-status-filter">Status:</label>
                    <select id="alert-status-filter" class="filter-select">
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="acknowledged">Acknowledged</option>
                        <option value="resolved">Resolved</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="alert-category-filter">Category:</label>
                    <select id="alert-category-filter" class="filter-select">
                        <option value="">All Categories</option>
                        <option value="camera">Camera</option>
                        <option value="detection">Detection</option>
                        <option value="system">System</option>
                        <option value="security">Security</option>
                        <option value="maintenance">Maintenance</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="alert-search-filter">Search:</label>
                    <input type="text" id="alert-search-filter" class="filter-input" placeholder="Search alerts...">
                </div>
                <div class="filter-actions">
                    <button class="btn btn-primary" id="apply-alert-filters">Apply</button>
                    <button class="btn btn-secondary" id="clear-alert-filters">Clear</button>
                </div>
            </div>

            <!-- Bulk Actions Bar -->
            <div class="bulk-actions-bar" id="bulk-actions-bar" style="display:none;">
                <div class="bulk-selection-info">
                    <span id="selected-alert-count">0</span> alerts selected
                </div>
                <div class="bulk-actions">
                    <button class="btn btn-small btn-success" id="bulk-acknowledge">Acknowledge</button>
                    <button class="btn btn-small btn-primary" id="bulk-resolve">Resolve</button>
                    <button class="btn btn-small btn-danger" id="bulk-delete">Delete</button>
                </div>
                <button class="bulk-close" id="bulk-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <!-- Alerts Container -->
            <div class="alerts-container ${this.currentView}" id="alerts-container">
                <!-- Alerts will be dynamically loaded -->
            </div>

            <!-- Pagination -->
            <div class="alerts-pagination" id="alerts-pagination">
                <!-- Pagination controls -->
            </div>
        `;
    }renderAlerts(){const container=document.getElementById('alerts-container');if(!container)return;if(this.filteredAlerts.length===0){container.innerHTML=this.getEmptyState();return;}container.innerHTML=this.filteredAlerts.map(alert=> this.currentView==='list' ? this.renderAlertRow(alert):this.renderAlertCard(alert)).join('');this.attachAlertEventListeners();}renderAlertRow(alert){const timeAgo=this.getRelativeTime(alert.timestamp);const severityIcon=this.getSeverityIcon(alert.severity);return ` <div class="alert-row ${alert.severity}${alert.status}" data-alert-id="${alert.id}"> <div class="alert-checkbox" style="display:${this.bulkMode ? 'block':'none'}"> <input type="checkbox" class="alert-select" data-alert-id="${alert.id}" ${this.selectedAlerts.has(alert.id)? 'checked':''}> </div> <div class="alert-severity ${alert.severity}"> <i class="fas ${severityIcon}"></i> </div> <div class="alert-content"> <div class="alert-header"> <h4 class="alert-title">${alert.title}</h4> <div class="alert-badges"> <span class="alert-badge status ${alert.status}">${this.capitalizeFirst(alert.status)}</span> <span class="alert-badge category">${this.capitalizeFirst(alert.category)}</span> </div> </div> <p class="alert-message">${alert.message}</p> <div class="alert-meta"> <span class="alert-source"> <i class="fas fa-map-marker-alt"></i> ${alert.source}</span> <span class="alert-time"> <i class="fas fa-clock"></i> ${timeAgo}</span> ${alert.acknowledged ? ` <span class="alert-acknowledged"> <i class="fas fa-user-check"></i> Acknowledged by ${alert.acknowledgedBy}</span> `:''}</div> </div> <div class="alert-actions"> ${!alert.acknowledged ? ` <button class="action-btn acknowledge" data-action="acknowledge" data-alert-id="${alert.id}" title="Acknowledge"> <i class="fas fa-check"></i> </button> `:''}${alert.status !=='resolved' ? ` <button class="action-btn resolve" data-action="resolve" data-alert-id="${alert.id}" title="Resolve"> <i class="fas fa-check-double"></i> </button> `:''}<button class="action-btn details" data-action="details" data-alert-id="${alert.id}" title="View Details"> <i class="fas fa-info-circle"></i> </button> <button class="action-btn delete danger" data-action="delete" data-alert-id="${alert.id}" title="Delete"> <i class="fas fa-trash"></i> </button> </div> </div> `;}renderAlertCard(alert){const timeAgo=this.getRelativeTime(alert.timestamp);const severityIcon=this.getSeverityIcon(alert.severity);return ` <div class="alert-card ${alert.severity}${alert.status}" data-alert-id="${alert.id}"> <div class="alert-card-header"> <div class="alert-severity-icon ${alert.severity}"> <i class="fas ${severityIcon}"></i> </div> <div class="alert-card-title"> <h4>${alert.title}</h4> <div class="alert-card-badges"> <span class="alert-badge status ${alert.status}">${this.capitalizeFirst(alert.status)}</span> <span class="alert-badge category">${this.capitalizeFirst(alert.category)}</span> </div> </div> <div class="alert-card-checkbox" style="display:${this.bulkMode ? 'block':'none'}"> <input type="checkbox" class="alert-select" data-alert-id="${alert.id}" ${this.selectedAlerts.has(alert.id)? 'checked':''}> </div> </div> <div class="alert-card-body"> <p class="alert-card-message">${alert.message}</p> <div class="alert-card-meta"> <div class="meta-item"> <i class="fas fa-map-marker-alt"></i> <span>${alert.source}</span> </div> <div class="meta-item"> <i class="fas fa-clock"></i> <span>${timeAgo}</span> </div> ${alert.acknowledged ? ` <div class="meta-item acknowledged"> <i class="fas fa-user-check"></i> <span>Acknowledged by ${alert.acknowledgedBy}</span> </div> `:''}</div> </div> <div class="alert-card-actions"> ${!alert.acknowledged ? ` <button class="btn btn-small btn-success" data-action="acknowledge" data-alert-id="${alert.id}"> <i class="fas fa-check"></i> Acknowledge </button> `:''}${alert.status !=='resolved' ? ` <button class="btn btn-small btn-primary" data-action="resolve" data-alert-id="${alert.id}"> <i class="fas fa-check-double"></i> Resolve </button> `:''}<button class="btn btn-small btn-secondary" data-action="details" data-alert-id="${alert.id}"> <i class="fas fa-info-circle"></i> Details </button> <button class="btn btn-small btn-danger" data-action="delete" data-alert-id="${alert.id}"> <i class="fas fa-trash"></i> Delete </button> </div> </div> `;}getEmptyState(){return ` <div class="empty-state"> <i class="fas fa-bell-slash"></i> <h3>No alerts found</h3> <p>All systems are running smoothly</p> </div> `;}attachEventListeners(){document.getElementById('acknowledge-all-btn')?.addEventListener('click',()=> this.acknowledgeAll());document.getElementById('bulk-actions-btn')?.addEventListener('click',()=> this.toggleBulkMode());document.getElementById('export-alerts-btn')?.addEventListener('click',()=> this.exportAlerts());document.getElementById('refresh-alerts-btn')?.addEventListener('click',()=> this.refreshAlerts());document.querySelectorAll('.view-btn').forEach(btn=>{btn.addEventListener('click',(e)=> this.changeView(e.target.dataset.view));});document.getElementById('apply-alert-filters')?.addEventListener('click',()=> this.applyFilters());document.getElementById('clear-alert-filters')?.addEventListener('click',()=> this.clearFilters());document.getElementById('alert-search-filter')?.addEventListener('input',(e)=> this.handleSearchInput(e));document.getElementById('bulk-acknowledge')?.addEventListener('click',()=> this.bulkAction('acknowledge'));document.getElementById('bulk-resolve')?.addEventListener('click',()=> this.bulkAction('resolve'));document.getElementById('bulk-delete')?.addEventListener('click',()=> this.bulkAction('delete'));document.getElementById('bulk-close')?.addEventListener('click',()=> this.closeBulkMode());}attachAlertEventListeners(){document.querySelectorAll('.alert-select').forEach(checkbox=>{checkbox.addEventListener('change',(e)=> this.handleAlertSelection(e));});document.querySelectorAll('.action-btn[data-action],.btn[data-action]').forEach(btn=>{btn.addEventListener('click',(e)=> this.handleAlertAction(e));});}async loadAlerts(){try{this.filteredAlerts=[...this.alerts];this.renderAlerts();}catch(error){console.error('Error loading alerts:',error);this.showToast('Failed to load alerts','error');}}getAlertSummary() {
        return {
            critical: this.alerts.filter(a => a.severity === 'critical' && a.status !== 'resolved').length,
            warning: this.alerts.filter(a => a.severity === 'warning' && a.status !== 'resolved').length,
            info: this.alerts.filter(a => a.severity === 'info' && a.status !== 'resolved').length,
            resolved: this.alerts.filter(a => a.status === 'resolved').length
        };
    }

    getSeverityIcon(severity) {
        const icons = {
            critical: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        return icons[severity] || 'fa-question-circle';
    }handleAlertSelection(e){const alertId=e.target.dataset.alertId;const isChecked=e.target.checked;if(isChecked){this.selectedAlerts.add(alertId);}else{this.selectedAlerts.delete(alertId);}this.updateBulkActionsBar();}updateBulkActionsBar(){const bulkBar=document.getElementById('bulk-actions-bar');const selectedCount=document.getElementById('selected-alert-count');if(this.selectedAlerts.size > 0){bulkBar.style.display='flex';selectedCount.textContent=this.selectedAlerts.size;}else{bulkBar.style.display='none';}}handleAlertAction(e){e.stopPropagation();const action=e.target.dataset.action || e.target.parentElement.dataset.action;const alertId=e.target.dataset.alertId || e.target.parentElement.dataset.alertId;switch(action){case 'acknowledge':this.acknowledgeAlert(alertId);break;case 'resolve':this.resolveAlert(alertId);break;case 'details':this.showAlertDetails(alertId);break;case 'delete':this.deleteAlert(alertId);break;}}async acknowledgeAlert(alertId){const alert=this.alerts.find(a=> a.id===alertId);if(!alert || alert.acknowledged)return;try{alert.acknowledged=true;alert.acknowledgedBy='current_user';alert.acknowledgedAt=new Date();this.renderAlerts();this.showToast('Alert acknowledged successfully','success');}catch(error){this.showToast('Failed to acknowledge alert','error');}}async resolveAlert(alertId){const alert=this.alerts.find(a=> a.id===alertId);if(!alert || alert.status==='resolved')return;try{alert.status='resolved';alert.resolvedAt=new Date();if(!alert.acknowledged){alert.acknowledged=true;alert.acknowledgedBy='current_user';alert.acknowledgedAt=new Date();}this.renderAlerts();this.render();this.showToast('Alert resolved successfully','success');}catch(error){this.showToast('Failed to resolve alert','error');}}showAlertDetails(alertId){const alert=this.alerts.find(a=> a.id===alertId);if(alert){console.log('Show alert details:',alert);}}async deleteAlert(alertId){const alert=this.alerts.find(a=> a.id===alertId);if(!alert)return;if(confirm(`Are you sure you want to delete the alert "${alert.title}"?`)){try{this.alerts=this.alerts.filter(a=> a.id !==alertId);this.applyFilters();this.render();this.showToast('Alert deleted successfully','success');}catch(error){this.showToast('Failed to delete alert','error');}}}async acknowledgeAll(){const unacknowledgedAlerts=this.alerts.filter(a=> !a.acknowledged && a.status !=='resolved');if(unacknowledgedAlerts.length===0){this.showToast('No alerts to acknowledge','info');return;}if(confirm(`Are you sure you want to acknowledge all ${unacknowledgedAlerts.length}active alerts?`)){try{unacknowledgedAlerts.forEach(alert=>{alert.acknowledged=true;alert.acknowledgedBy='current_user';alert.acknowledgedAt=new Date();});this.renderAlerts();this.showToast(`${unacknowledgedAlerts.length}alerts acknowledged`,'success');}catch(error){this.showToast('Failed to acknowledge alerts','error');}}}applyFilters(){this.filters.severity=document.getElementById('alert-severity-filter').value;this.filters.status=document.getElementById('alert-status-filter').value;this.filters.category=document.getElementById('alert-category-filter').value;this.filters.search=document.getElementById('alert-search-filter').value.toLowerCase();this.filteredAlerts=this.alerts.filter(alert=>{const matchesSeverity=!this.filters.severity || alert.severity===this.filters.severity;const matchesStatus=!this.filters.status || alert.status===this.filters.status;const matchesCategory=!this.filters.category || alert.category===this.filters.category;const matchesSearch=!this.filters.search || alert.title.toLowerCase().includes(this.filters.search)|| alert.message.toLowerCase().includes(this.filters.search)|| alert.source.toLowerCase().includes(this.filters.search);return matchesSeverity && matchesStatus && matchesCategory && matchesSearch;});this.renderAlerts();}clearFilters(){document.getElementById('alert-severity-filter').value='';document.getElementById('alert-status-filter').value='';document.getElementById('alert-category-filter').value='';document.getElementById('alert-search-filter').value='';this.filters={severity:'',status:'',category:'',search:''};this.filteredAlerts=[...this.alerts];this.renderAlerts();}handleSearchInput(e){clearTimeout(this.searchTimeout);this.searchTimeout=setTimeout(()=>{this.applyFilters();},300);}changeView(view){this.currentView=view;document.querySelectorAll('.view-btn').forEach(btn=>{btn.classList.toggle('active',btn.dataset.view===view);});this.renderAlerts();}toggleBulkMode(){this.bulkMode=!this.bulkMode;const checkboxes=document.querySelectorAll('.alert-checkbox,.alert-card-checkbox');if(this.bulkMode){checkboxes.forEach(cb=> cb.style.display='block');}else{checkboxes.forEach(cb=> cb.style.display='none');this.selectedAlerts.clear();document.querySelectorAll('.alert-select').forEach(cb=> cb.checked=false);this.updateBulkActionsBar();}}closeBulkMode(){this.bulkMode=false;this.selectedAlerts.clear();document.querySelectorAll('.alert-select').forEach(cb=> cb.checked=false);document.querySelectorAll('.alert-checkbox,.alert-card-checkbox').forEach(cb=> cb.style.display='none');this.updateBulkActionsBar();}async bulkAction(action){const selectedIds=Array.from(this.selectedAlerts);if(selectedIds.length===0)return;const confirmMessage=`Are you sure you want to ${action}${selectedIds.length}alert(s)?`;if(!confirm(confirmMessage))return;try{selectedIds.forEach(alertId=>{const alert=this.alerts.find(a=> a.id===alertId);if(!alert)return;switch(action){case 'acknowledge':if(!alert.acknowledged){alert.acknowledged=true;alert.acknowledgedBy='current_user';alert.acknowledgedAt=new Date();}break;case 'resolve':alert.status='resolved';alert.resolvedAt=new Date();if(!alert.acknowledged){alert.acknowledged=true;alert.acknowledgedBy='current_user';alert.acknowledgedAt=new Date();}break;case 'delete':this.alerts=this.alerts.filter(a=> a.id !==alertId);break;}});this.closeBulkMode();this.applyFilters();this.render();this.showToast(`Bulk ${action}completed successfully`,'success');}catch(error){this.showToast(`Bulk ${action}failed`,'error');}}exportAlerts(){const csvContent=this.generateAlertsCSV();this.downloadFile(csvContent,`alerts_export_${new Date().toISOString().split('T')[0]}.csv`,'text/csv');this.showToast('Alerts exported successfully','success');}generateAlertsCSV(){const headers=['ID','Title','Message','Severity','Status','Category','Source','Timestamp','Acknowledged','Acknowledged By','Resolved At'];const rows=this.filteredAlerts.map(alert=> [ alert.id,alert.title,alert.message,alert.severity,alert.status,alert.category,alert.source,alert.timestamp.toISOString(),alert.acknowledged ? 'Yes':'No',alert.acknowledgedBy || '',alert.resolvedAt ? alert.resolvedAt.toISOString():'' ]);return [headers,...rows].map(row=> row.map(field=> `"${String(field).replace(/"/g,'""')}"`).join(',')).join('\n');}downloadFile(content,filename,contentType){const blob=new Blob([content],{type:contentType});const url=window.URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();window.URL.revokeObjectURL(url);document.body.removeChild(a);}async refreshAlerts(){const refreshBtn=document.getElementById('refresh-alerts-btn');const icon=refreshBtn.querySelector('i');icon.classList.add('fa-spin');refreshBtn.disabled=true;try{await this.loadAlerts();this.render();this.showToast('Alerts refreshed successfully','success');}catch(error){this.showToast('Failed to refresh alerts','error');}finally{icon.classList.remove('fa-spin');refreshBtn.disabled=false;}}getRelativeTime(date){const now=new Date();const diff=now-date;const minutes=Math.floor(diff/60000);if(minutes < 1)return 'Just now';if(minutes < 60)return `${minutes}m ago`;if(minutes < 1440)return `${Math.floor(minutes/60)}h ago`;return `${Math.floor(minutes/1440)}d ago`;}capitalizeFirst(str){return str.charAt(0).toUpperCase()+str.slice(1);}showToast(message,type='info'){const toast=document.createElement('div');toast.className=`toast toast-${type}`;toast.innerHTML=` <i class="fas ${type==='success' ? 'fa-check-circle':type==='error' ? 'fa-exclamation-circle':'fa-info-circle'}"></i> <span>${message}</span> <button class="toast-close" onclick="this.parentElement.remove()"> <i class="fas fa-times"></i> </button> `;let container=document.getElementById('toast-container');if(!container){container=document.createElement('div');container.id='toast-container';container.className='toast-container';document.body.appendChild(container);}container.appendChild(toast);setTimeout(()=>{if(toast.parentElement){toast.remove();}},5000);}}export default AlertsPage;