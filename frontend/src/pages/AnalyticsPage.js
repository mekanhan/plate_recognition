/**
 * Analytics Page Component
 * Traffic patterns, trends, and system performance analysis
 */
class AnalyticsPage {
    constructor() {
        this.timeframe = '24h';
        this.analyticsData = {};
        this.init();
    }

    init() {
        this.loadMockData();
        this.render();
        this.attachEventListeners();
        this.renderAnalytics();
    }

    loadMockData() {
        this.analyticsData = {
            trafficOverview: {
                totalVehicles: 1247,
                averagePerHour: 52,
                peakHour: '14:00',
                peakCount: 89,
                growthRate: 8.5
            },
            hourlyData: [
                { hour: '00:00', count: 12 },
                { hour: '01:00', count: 8 },
                { hour: '02:00', count: 5 },
                { hour: '03:00', count: 7 },
                { hour: '04:00', count: 15 },
                { hour: '05:00', count: 28 },
                { hour: '06:00', count: 45 },
                { hour: '07:00', count: 67 },
                { hour: '08:00', count: 78 },
                { hour: '09:00', count: 65 },
                { hour: '10:00', count: 58 },
                { hour: '11:00', count: 72 },
                { hour: '12:00', count: 81 },
                { hour: '13:00', count: 85 },
                { hour: '14:00', count: 89 },
                { hour: '15:00', count: 76 },
                { hour: '16:00', count: 82 },
                { hour: '17:00', count: 88 },
                { hour: '18:00', count: 65 },
                { hour: '19:00', count: 42 },
                { hour: '20:00', count: 35 },
                { hour: '21:00', count: 28 },
                { hour: '22:00', count: 22 },
                { hour: '23:00', count: 18 }
            ],
            cameraPerformance: [
                { name: 'Entrance Gate', uptime: 99.8, detections: 456, accuracy: 98.2 },
                { name: 'Parking Lot A', uptime: 98.5, detections: 342, accuracy: 96.8 },
                { name: 'Loading Dock', uptime: 97.2, detections: 189, accuracy: 94.5 },
                { name: 'Side Entrance', uptime: 99.1, detections: 167, accuracy: 97.3 },
                { name: 'Rear Exit', uptime: 96.8, detections: 93, accuracy: 95.1 },
                { name: 'Visitor Parking', uptime: 98.9, detections: 78, accuracy: 96.2 }
            ],
            detectionAccuracy: {
                overall: 96.8,
                trend: '+1.2%',
                high: 892, // 90%+
                medium: 234, // 70-89%
                low: 121 // <70%
            },
            frequentVehicles: [
                { plate: 'ABC-123', visits: 23, lastSeen: '2 hours ago' },
                { plate: 'XYZ-789', visits: 18, lastSeen: '4 hours ago' },
                { plate: 'DEF-456', visits: 15, lastSeen: '1 day ago' },
                { plate: 'GHI-789', visits: 12, lastSeen: '3 hours ago' },
                { plate: 'JKL-012', visits: 11, lastSeen: '6 hours ago' }
            ],
            alertsSummary: {
                total: 42,
                critical: 3,
                warning: 12,
                info: 27,
                resolved: 38
            }
        };
    }

    render() {
        const container = document.getElementById('analytics');
        if (!container) return;

        container.innerHTML = this.getTemplate();
    }

    getTemplate() {
        return `
            <div class="page-header">
                <h1 class="page-title">Analytics</h1>
                <p class="page-subtitle">Traffic patterns, trends, and system performance</p>
            </div>
            
            <!-- Analytics Controls -->
            <div class="analytics-controls">
                <select id="analytics-timeframe" class="analytics-select">
                    <option value="24h" ${this.timeframe === '24h' ? 'selected' : ''}>Last 24 Hours</option>
                    <option value="7d" ${this.timeframe === '7d' ? 'selected' : ''}>Last 7 Days</option>
                    <option value="30d" ${this.timeframe === '30d' ? 'selected' : ''}>Last 30 Days</option>
                    <option value="90d" ${this.timeframe === '90d' ? 'selected' : ''}>Last 90 Days</option>
                </select>
                <button class="btn btn-primary" id="export-analytics-btn">
                    <i class="fas fa-download"></i>
                    Export Report
                </button>
            </div>
            
            <!-- Analytics Grid -->
            <div class="analytics-grid" id="analytics-grid">
                <!-- Traffic Overview Card -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Traffic Overview</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="analytics-stats">
                            <div class="stat-item">
                                <div class="stat-value">${this.analyticsData.trafficOverview.totalVehicles.toLocaleString()}</div>
                                <div class="stat-label">Total Vehicles</div>
                                <div class="stat-change positive">+${this.analyticsData.trafficOverview.growthRate}%</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${this.analyticsData.trafficOverview.averagePerHour}</div>
                                <div class="stat-label">Avg per Hour</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${this.analyticsData.trafficOverview.peakHour}</div>
                                <div class="stat-label">Peak Hour</div>
                                <div class="stat-sublabel">${this.analyticsData.trafficOverview.peakCount} vehicles</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Peak Hours Chart -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Peak Hours Analysis</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="chart-placeholder" id="peak-hours-chart">
                            <div class="chart-bars">
                                ${this.generateHourlyChart()}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Camera Performance -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Camera Performance</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="performance-list">
                            ${this.analyticsData.cameraPerformance.map(camera => `
                                <div class="performance-item">
                                    <div class="camera-name">${camera.name}</div>
                                    <div class="performance-metrics">
                                        <div class="metric">
                                            <span class="metric-label">Uptime:</span>
                                            <span class="metric-value ${camera.uptime >= 99 ? 'good' : camera.uptime >= 95 ? 'warning' : 'critical'}">${camera.uptime}%</span>
                                        </div>
                                        <div class="metric">
                                            <span class="metric-label">Detections:</span>
                                            <span class="metric-value">${camera.detections}</span>
                                        </div>
                                        <div class="metric">
                                            <span class="metric-label">Accuracy:</span>
                                            <span class="metric-value ${camera.accuracy >= 95 ? 'good' : camera.accuracy >= 90 ? 'warning' : 'critical'}">${camera.accuracy}%</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Detection Accuracy Trends -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Detection Accuracy</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="accuracy-overview">
                            <div class="accuracy-main">
                                <div class="accuracy-value">${this.analyticsData.detectionAccuracy.overall}%</div>
                                <div class="accuracy-trend positive">${this.analyticsData.detectionAccuracy.trend}</div>
                            </div>
                            <div class="accuracy-breakdown">
                                <div class="accuracy-segment">
                                    <div class="segment-bar">
                                        <div class="segment-fill high" style="width: ${(this.analyticsData.detectionAccuracy.high / 1247) * 100}%"></div>
                                    </div>
                                    <div class="segment-label">High (90%+): ${this.analyticsData.detectionAccuracy.high}</div>
                                </div>
                                <div class="accuracy-segment">
                                    <div class="segment-bar">
                                        <div class="segment-fill medium" style="width: ${(this.analyticsData.detectionAccuracy.medium / 1247) * 100}%"></div>
                                    </div>
                                    <div class="segment-label">Medium (70-89%): ${this.analyticsData.detectionAccuracy.medium}</div>
                                </div>
                                <div class="accuracy-segment">
                                    <div class="segment-bar">
                                        <div class="segment-fill low" style="width: ${(this.analyticsData.detectionAccuracy.low / 1247) * 100}%"></div>
                                    </div>
                                    <div class="segment-label">Low (<70%): ${this.analyticsData.detectionAccuracy.low}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Frequent Vehicles -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Frequent Vehicles</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="frequent-vehicles-list">
                            ${this.analyticsData.frequentVehicles.map(vehicle => `
                                <div class="frequent-vehicle-item">
                                    <div class="vehicle-plate">${vehicle.plate}</div>
                                    <div class="vehicle-stats">
                                        <span class="visit-count">${vehicle.visits} visits</span>
                                        <span class="last-seen">Last seen: ${vehicle.lastSeen}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Alerts Summary -->
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <h3 class="analytics-card-title">Alerts Summary</h3>
                    </div>
                    <div class="analytics-card-body">
                        <div class="alerts-overview">
                            <div class="alert-stats">
                                <div class="alert-stat critical">
                                    <div class="alert-count">${this.analyticsData.alertsSummary.critical}</div>
                                    <div class="alert-label">Critical</div>
                                </div>
                                <div class="alert-stat warning">
                                    <div class="alert-count">${this.analyticsData.alertsSummary.warning}</div>
                                    <div class="alert-label">Warning</div>
                                </div>
                                <div class="alert-stat info">
                                    <div class="alert-count">${this.analyticsData.alertsSummary.info}</div>
                                    <div class="alert-label">Info</div>
                                </div>
                                <div class="alert-stat resolved">
                                    <div class="alert-count">${this.analyticsData.alertsSummary.resolved}</div>
                                    <div class="alert-label">Resolved</div>
                                </div>
                            </div>
                            <div class="alert-resolution-rate">
                                <div class="resolution-percentage">
                                    ${Math.round((this.analyticsData.alertsSummary.resolved / this.analyticsData.alertsSummary.total) * 100)}%
                                </div>
                                <div class="resolution-label">Resolution Rate</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generateHourlyChart() {
        const maxCount = Math.max(...this.analyticsData.hourlyData.map(h => h.count));
        return this.analyticsData.hourlyData.slice(0, 12).map(hourData => {
            const height = (hourData.count / maxCount) * 100;
            return `
                <div class="chart-bar" title="${hourData.hour}: ${hourData.count} vehicles">
                    <div class="bar-fill" style="height: ${height}%"></div>
                    <div class="bar-label">${hourData.hour.substring(0, 2)}</div>
                </div>
            `;
        }).join('');
    }

    attachEventListeners() {
        // Timeframe selection
        document.getElementById('analytics-timeframe')?.addEventListener('change', (e) => {
            this.timeframe = e.target.value;
            this.updateAnalytics();
        });

        // Export button
        document.getElementById('export-analytics-btn')?.addEventListener('click', () => {
            this.exportAnalyticsReport();
        });
    }

    renderAnalytics() {
        // This method can be extended to render actual charts using libraries like Chart.js
        console.log('Analytics rendered for timeframe:', this.timeframe);
    }

    updateAnalytics() {
        // Simulate data loading for different timeframes
        this.showLoadingState();
        
        setTimeout(() => {
            // Update data based on timeframe
            this.updateDataForTimeframe();
            this.render();
            this.attachEventListeners();
            this.renderAnalytics();
            this.hideLoadingState();
        }, 500);
    }

    updateDataForTimeframe() {
        // Simulate different data for different timeframes
        const multipliers = {
            '24h': 1,
            '7d': 7,
            '30d': 30,
            '90d': 90
        };

        const multiplier = multipliers[this.timeframe] || 1;
        
        // Update traffic overview
        this.analyticsData.trafficOverview.totalVehicles = Math.round(1247 * multiplier);
        this.analyticsData.trafficOverview.averagePerHour = Math.round(52 * (multiplier / 24));
    }

    showLoadingState() {
        const grid = document.getElementById('analytics-grid');
        if (grid) {
            grid.style.opacity = '0.5';
            grid.style.pointerEvents = 'none';
        }
    }

    hideLoadingState() {
        const grid = document.getElementById('analytics-grid');
        if (grid) {
            grid.style.opacity = '1';
            grid.style.pointerEvents = 'auto';
        }
    }

    exportAnalyticsReport() {
        const reportData = {
            generated: new Date().toISOString(),
            timeframe: this.timeframe,
            data: this.analyticsData
        };

        const csvContent = this.generateAnalyticsCSV(reportData);
        this.downloadFile(csvContent, `analytics_report_${this.timeframe}.csv`, 'text/csv');
        this.showToast('Analytics report exported successfully', 'success');
    }

    generateAnalyticsCSV(reportData) {
        const lines = [
            `Analytics Report - ${reportData.timeframe}`,
            `Generated: ${new Date(reportData.generated).toLocaleString()}`,
            '',
            'Traffic Overview',
            `Total Vehicles,${reportData.data.trafficOverview.totalVehicles}`,
            `Average per Hour,${reportData.data.trafficOverview.averagePerHour}`,
            `Peak Hour,${reportData.data.trafficOverview.peakHour}`,
            `Peak Count,${reportData.data.trafficOverview.peakCount}`,
            '',
            'Camera Performance',
            'Camera,Uptime %,Detections,Accuracy %'
        ];

        reportData.data.cameraPerformance.forEach(camera => {
            lines.push(`${camera.name},${camera.uptime},${camera.detections},${camera.accuracy}`);
        });

        lines.push('');
        lines.push('Frequent Vehicles');
        lines.push('Plate,Visits,Last Seen');
        
        reportData.data.frequentVehicles.forEach(vehicle => {
            lines.push(`${vehicle.plate},${vehicle.visits},${vehicle.lastSeen}`);
        });

        return lines.join('\n');
    }

    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

export default AnalyticsPage;