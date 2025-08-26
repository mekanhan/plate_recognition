/**
 * Storage Management Modal Component
 * Provides tools for managing recordings storage, especially orphaned recordings
 * Part of the recordings-first architecture implementation
 */

class StorageManagementModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.storageData = null;
        this.orphanedData = null;
        
        this.createModal();
        this.attachEventListeners();
    }
    
    createModal() {
        this.modal = document.createElement('div');
        this.modal.className = 'modal-overlay storage-management-modal';
        this.modal.setAttribute('role', 'dialog');
        this.modal.setAttribute('aria-labelledby', 'storage-modal-title');
        
        this.modal.innerHTML = `
            <div class="modal-container">
                <div class="modal-header">
                    <h2 id="storage-modal-title">
                        <i class="fas fa-hdd"></i>
                        Storage Management
                    </h2>
                    <button class="modal-close" aria-label="Close modal">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="modal-body">
                    <!-- Storage Overview -->
                    <div class="storage-section">
                        <h3>Storage Overview</h3>
                        <div class="storage-stats" id="storageStats">
                            <div class="storage-stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-database status-online"></i>
                                </div>
                                <div class="stat-details">
                                    <span class="stat-label">Active Cameras</span>
                                    <span class="stat-value" id="activeCameraSize">--</span>
                                    <span class="stat-count" id="activeCameraCount">-- cameras</span>
                                </div>
                            </div>
                            
                            <div class="storage-stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-archive status-warning"></i>
                                </div>
                                <div class="stat-details">
                                    <span class="stat-label">Archived Cameras</span>
                                    <span class="stat-value" id="deletedCameraSize">--</span>
                                    <span class="stat-count" id="deletedCameraCount">-- cameras</span>
                                </div>
                            </div>
                            
                            <div class="storage-stat-card total">
                                <div class="stat-icon">
                                    <i class="fas fa-chart-pie status-info"></i>
                                </div>
                                <div class="stat-details">
                                    <span class="stat-label">Total Storage</span>
                                    <span class="stat-value" id="totalStorageSize">--</span>
                                    <span class="stat-count" id="totalCameraCount">-- cameras</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Orphaned Recordings Section -->
                    <div class="storage-section">
                        <h3>
                            Orphaned Recordings Management
                            <span class="section-badge" id="orphanedBadge">0 cameras</span>
                        </h3>
                        <p class="section-description">
                            Recordings from cameras that no longer exist in the system. These can be safely removed to free up storage space.
                        </p>
                        
                        <div class="orphaned-controls">
                            <div class="cleanup-settings">
                                <div class="form-group">
                                    <label for="cleanupAge">Delete recordings older than:</label>
                                    <select id="cleanupAge" class="form-select">
                                        <option value="7">7 days</option>
                                        <option value="30" selected>30 days</option>
                                        <option value="60">60 days</option>
                                        <option value="90">90 days</option>
                                        <option value="180">6 months</option>
                                        <option value="365">1 year</option>
                                    </select>
                                </div>
                                
                                <div class="cleanup-actions">
                                    <button class="btn btn-outline-primary" id="previewCleanupBtn">
                                        <i class="fas fa-search"></i>
                                        Preview Cleanup
                                    </button>
                                    <button class="btn btn-warning" id="performCleanupBtn" disabled>
                                        <i class="fas fa-trash"></i>
                                        Delete Files
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Cleanup Preview Results -->
                        <div class="cleanup-preview" id="cleanupPreview" style="display: none;">
                            <div class="preview-header">
                                <h4>Cleanup Preview</h4>
                                <span class="preview-timestamp" id="previewTimestamp"></span>
                            </div>
                            
                            <div class="preview-stats">
                                <div class="preview-stat">
                                    <i class="fas fa-file-video"></i>
                                    <span>
                                        <strong id="previewFileCount">0</strong> files
                                    </span>
                                </div>
                                <div class="preview-stat">
                                    <i class="fas fa-hdd"></i>
                                    <span>
                                        <strong id="previewSpaceFreed">0 MB</strong> to be freed
                                    </span>
                                </div>
                            </div>
                            
                            <div class="preview-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                <strong>Warning:</strong> This action cannot be undone. Files will be permanently deleted.
                            </div>
                        </div>
                        
                        <!-- Cleanup Results -->
                        <div class="cleanup-results" id="cleanupResults" style="display: none;">
                            <div class="results-header">
                                <h4 id="resultsTitle">Cleanup Complete</h4>
                                <span class="results-timestamp" id="resultsTimestamp"></span>
                            </div>
                            
                            <div class="results-summary">
                                <div class="result-stat success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>
                                        <strong id="deletedFileCount">0</strong> files deleted
                                    </span>
                                </div>
                                <div class="result-stat success">
                                    <i class="fas fa-hdd"></i>
                                    <span>
                                        <strong id="spaceFreed">0 MB</strong> freed
                                    </span>
                                </div>
                                <div class="result-stat" id="errorStat" style="display: none;">
                                    <i class="fas fa-exclamation-circle"></i>
                                    <span>
                                        <strong id="errorCount">0</strong> errors
                                    </span>
                                </div>
                            </div>
                            
                            <div class="results-errors" id="resultsErrors" style="display: none;">
                                <h5>Errors encountered:</h5>
                                <ul id="errorList"></ul>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Orphaned Camera List -->
                    <div class="storage-section">
                        <h3>Orphaned Camera Details</h3>
                        <div class="orphaned-camera-list" id="orphanedCameraList">
                            <div class="loading-spinner">
                                <i class="fas fa-spinner fa-spin"></i>
                                Loading orphaned recordings...
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="refreshDataBtn">
                        <i class="fas fa-sync-alt"></i>
                        Refresh Data
                    </button>
                    <button class="btn btn-primary" id="closeModalBtn">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
    }
    
    attachEventListeners() {
        // Close modal events
        const closeBtn = this.modal.querySelector('.modal-close');
        const closeModalBtn = this.modal.querySelector('#closeModalBtn');
        
        closeBtn.addEventListener('click', () => this.close());
        closeModalBtn.addEventListener('click', () => this.close());
        
        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
        
        // Action buttons
        const refreshBtn = this.modal.querySelector('#refreshDataBtn');
        const previewBtn = this.modal.querySelector('#previewCleanupBtn');
        const performBtn = this.modal.querySelector('#performCleanupBtn');
        
        refreshBtn.addEventListener('click', () => this.loadData());
        previewBtn.addEventListener('click', () => this.previewCleanup());
        performBtn.addEventListener('click', () => this.performCleanup());
    }
    
    async open() {
        this.isOpen = true;
        this.modal.classList.add('show');
        
        // Load initial data
        await this.loadData();
        
        // Focus management for accessibility
        const firstFocusable = this.modal.querySelector('.modal-close');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        // Show toast notification
        if (window.toast) {
            window.toast.info('Storage Management', 'Loading storage analytics...');
        }
    }
    
    close() {
        this.isOpen = false;
        this.modal.classList.remove('show');
        
        // Clear any cleanup results
        this.hideCleanupPreview();
        this.hideCleanupResults();
    }
    
    async loadData() {
        try {
            // Show loading states
            this.showLoadingStates();
            
            // Load storage usage data
            const storageResponse = await fetch('http://localhost:8002/api/v1/recordings/storage/usage');
            if (!storageResponse.ok) {
                throw new Error('Failed to fetch storage data');
            }
            this.storageData = await storageResponse.json();
            
            // Load orphaned recordings data
            const orphanedResponse = await fetch('http://localhost:8002/api/v1/recordings/orphaned');
            if (!orphanedResponse.ok) {
                throw new Error('Failed to fetch orphaned recordings');
            }
            this.orphanedData = await orphanedResponse.json();
            
            // Update UI with data
            this.updateStorageStats();
            this.updateOrphanedCamerasList();
            
            // Show success toast\n            if (window.toast) {\n                window.toast.success('Data Loaded', 'Storage analytics updated successfully');\n            }\n            \n        } catch (error) {\n            console.error('Failed to load storage data:', error);\n            this.showError('Failed to load storage data: ' + error.message);\n            \n            if (window.toast) {\n                window.toast.error('Load Failed', error.message);\n            }\n        }\n    }\n    \n    showLoadingStates() {\n        // Storage stats loading\n        const statValues = this.modal.querySelectorAll('.stat-value, .stat-count');\n        statValues.forEach(el => {\n            el.textContent = '--';\n            el.classList.add('loading');\n        });\n        \n        // Orphaned list loading\n        const orphanedList = this.modal.querySelector('#orphanedCameraList');\n        orphanedList.innerHTML = `\n            <div class=\"loading-spinner\">\n                <i class=\"fas fa-spinner fa-spin\"></i>\n                Loading orphaned recordings...\n            </div>\n        `;\n    }\n    \n    updateStorageStats() {\n        if (!this.storageData || !this.storageData.usage) {\n            return;\n        }\n        \n        const usage = this.storageData.usage;\n        \n        // Helper function to format file size\n        const formatSize = (mb) => {\n            if (mb < 1024) {\n                return `${mb.toFixed(1)} MB`;\n            } else {\n                return `${(mb / 1024).toFixed(2)} GB`;\n            }\n        };\n        \n        // Update active cameras stats\n        document.getElementById('activeCameraSize').textContent = formatSize(usage.active_cameras_mb);\n        \n        const activeCameras = Object.values(usage.cameras).filter(c => c.is_active);\n        document.getElementById('activeCameraCount').textContent = `${activeCameras.length} cameras`;\n        \n        // Update deleted cameras stats\n        document.getElementById('deletedCameraSize').textContent = formatSize(usage.deleted_cameras_mb);\n        \n        const deletedCameras = Object.values(usage.cameras).filter(c => !c.is_active);\n        document.getElementById('deletedCameraCount').textContent = `${deletedCameras.length} cameras`;\n        \n        // Update total stats\n        document.getElementById('totalStorageSize').textContent = formatSize(usage.total_mb);\n        document.getElementById('totalCameraCount').textContent = `${Object.keys(usage.cameras).length} cameras`;\n        \n        // Remove loading states\n        const statValues = this.modal.querySelectorAll('.stat-value, .stat-count');\n        statValues.forEach(el => el.classList.remove('loading'));\n    }\n    \n    updateOrphanedCamerasList() {\n        const orphanedList = this.modal.querySelector('#orphanedCameraList');\n        const orphanedBadge = this.modal.querySelector('#orphanedBadge');\n        \n        if (!this.orphanedData || !this.orphanedData.orphaned_sources) {\n            orphanedList.innerHTML = `\n                <div class=\"empty-state\">\n                    <i class=\"fas fa-check-circle status-success\"></i>\n                    <p>No orphaned recordings found</p>\n                    <small>All recordings belong to active cameras</small>\n                </div>\n            `;\n            orphanedBadge.textContent = '0 cameras';\n            return;\n        }\n        \n        const orphaned = this.orphanedData.orphaned_sources;\n        orphanedBadge.textContent = `${orphaned.length} cameras`;\n        \n        if (orphaned.length === 0) {\n            orphanedList.innerHTML = `\n                <div class=\"empty-state\">\n                    <i class=\"fas fa-check-circle status-success\"></i>\n                    <p>No orphaned recordings found</p>\n                    <small>All recordings belong to active cameras</small>\n                </div>\n            `;\n            return;\n        }\n        \n        // Helper function to format file size\n        const formatSize = (mb) => {\n            if (mb < 1024) {\n                return `${mb.toFixed(1)} MB`;\n            } else {\n                return `${(mb / 1024).toFixed(2)} GB`;\n            }\n        };\n        \n        orphanedList.innerHTML = orphaned.map(camera => {\n            const dateRange = camera.date_range && camera.date_range.length > 0 \n                ? `${camera.date_range[0]} to ${camera.date_range[camera.date_range.length - 1]}`\n                : 'Unknown dates';\n            \n            return `\n                <div class=\"orphaned-camera-card\">\n                    <div class=\"camera-header\">\n                        <div class=\"camera-info\">\n                            <h4>${camera.display_name}</h4>\n                            <span class=\"camera-id\">${camera.camera_id}</span>\n                        </div>\n                        <div class=\"camera-stats\">\n                            <span class=\"storage-size\">${formatSize(camera.storage_used_mb)}</span>\n                            <span class=\"recording-count\">${camera.recording_count} files</span>\n                        </div>\n                    </div>\n                    \n                    <div class=\"camera-details\">\n                        <div class=\"detail-item\">\n                            <i class=\"fas fa-calendar\"></i>\n                            <span>Recording period: ${dateRange}</span>\n                        </div>\n                        <div class=\"detail-item\">\n                            <i class=\"fas fa-info-circle\"></i>\n                            <span>Camera was deleted from system but recordings remain</span>\n                        </div>\n                    </div>\n                </div>\n            `;\n        }).join('');\n    }\n    \n    async previewCleanup() {\n        const ageSelect = this.modal.querySelector('#cleanupAge');\n        const olderThanDays = parseInt(ageSelect.value);\n        \n        try {\n            // Show loading state\n            const previewBtn = this.modal.querySelector('#previewCleanupBtn');\n            const originalContent = previewBtn.innerHTML;\n            previewBtn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Analyzing...';\n            previewBtn.disabled = true;\n            \n            // Call cleanup API with dry run\n            const response = await fetch(\n                `http://localhost:8002/api/v1/recordings/orphaned?older_than_days=${olderThanDays}&dry_run=true`,\n                { method: 'DELETE' }\n            );\n            \n            if (!response.ok) {\n                throw new Error('Failed to preview cleanup');\n            }\n            \n            const results = await response.json();\n            this.showCleanupPreview(results.cleanup_results);\n            \n            // Enable perform cleanup button\n            const performBtn = this.modal.querySelector('#performCleanupBtn');\n            performBtn.disabled = false;\n            \n            if (window.toast) {\n                const fileCount = results.cleanup_results.file_count || 0;\n                const spaceToFree = results.cleanup_results.space_to_free_mb || 0;\n                window.toast.info('Preview Ready', `${fileCount} files (${spaceToFree.toFixed(1)} MB) ready for cleanup`);\n            }\n            \n        } catch (error) {\n            console.error('Preview cleanup failed:', error);\n            this.showError('Preview failed: ' + error.message);\n            \n            if (window.toast) {\n                window.toast.error('Preview Failed', error.message);\n            }\n            \n        } finally {\n            // Restore button state\n            const previewBtn = this.modal.querySelector('#previewCleanupBtn');\n            previewBtn.innerHTML = originalContent;\n            previewBtn.disabled = false;\n        }\n    }\n    \n    showCleanupPreview(results) {\n        const previewDiv = this.modal.querySelector('#cleanupPreview');\n        const timestamp = this.modal.querySelector('#previewTimestamp');\n        const fileCount = this.modal.querySelector('#previewFileCount');\n        const spaceFreed = this.modal.querySelector('#previewSpaceFreed');\n        \n        timestamp.textContent = new Date().toLocaleString();\n        fileCount.textContent = results.file_count || 0;\n        spaceFreed.textContent = `${(results.space_to_free_mb || 0).toFixed(1)} MB`;\n        \n        previewDiv.style.display = 'block';\n        \n        // Scroll preview into view\n        previewDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });\n    }\n    \n    hideCleanupPreview() {\n        const previewDiv = this.modal.querySelector('#cleanupPreview');\n        previewDiv.style.display = 'none';\n        \n        // Disable perform cleanup button\n        const performBtn = this.modal.querySelector('#performCleanupBtn');\n        performBtn.disabled = true;\n    }\n    \n    async performCleanup() {\n        // Get user confirmation\n        const confirmed = confirm(\n            'Are you sure you want to permanently delete these orphaned recordings? This action cannot be undone.'\n        );\n        \n        if (!confirmed) {\n            return;\n        }\n        \n        const ageSelect = this.modal.querySelector('#cleanupAge');\n        const olderThanDays = parseInt(ageSelect.value);\n        \n        try {\n            // Show loading state\n            const performBtn = this.modal.querySelector('#performCleanupBtn');\n            const originalContent = performBtn.innerHTML;\n            performBtn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Deleting...';\n            performBtn.disabled = true;\n            \n            // Show progress toast\n            const progressToastId = window.toast ? window.toast.loading('Cleanup in Progress', 'Deleting orphaned recordings...') : null;\n            \n            // Call cleanup API with actual deletion\n            const response = await fetch(\n                `http://localhost:8002/api/v1/recordings/orphaned?older_than_days=${olderThanDays}&dry_run=false`,\n                { method: 'DELETE' }\n            );\n            \n            if (!response.ok) {\n                throw new Error('Failed to perform cleanup');\n            }\n            \n            const results = await response.json();\n            \n            // Update progress toast to success\n            if (progressToastId && window.toast) {\n                const fileCount = results.cleanup_results.file_count || 0;\n                const spaceFreed = results.cleanup_results.space_to_free_mb || 0;\n                window.toast.update(progressToastId, {\n                    type: 'success',\n                    title: 'Cleanup Complete',\n                    message: `Deleted ${fileCount} files, freed ${spaceFreed.toFixed(1)} MB`\n                });\n            }\n            \n            this.showCleanupResults(results.cleanup_results);\n            this.hideCleanupPreview();\n            \n            // Refresh data to show updated storage stats\n            await this.loadData();\n            \n        } catch (error) {\n            console.error('Cleanup failed:', error);\n            this.showError('Cleanup failed: ' + error.message);\n            \n            if (window.toast) {\n                window.toast.error('Cleanup Failed', error.message);\n            }\n            \n        } finally {\n            // Restore button state\n            const performBtn = this.modal.querySelector('#performCleanupBtn');\n            performBtn.innerHTML = originalContent;\n            performBtn.disabled = true; // Keep disabled until next preview\n        }\n    }\n    \n    showCleanupResults(results) {\n        const resultsDiv = this.modal.querySelector('#cleanupResults');\n        const timestamp = this.modal.querySelector('#resultsTimestamp');\n        const deletedFileCount = this.modal.querySelector('#deletedFileCount');\n        const spaceFreed = this.modal.querySelector('#spaceFreed');\n        const errorStat = this.modal.querySelector('#errorStat');\n        const errorCount = this.modal.querySelector('#errorCount');\n        const errorList = this.modal.querySelector('#errorList');\n        const resultsErrors = this.modal.querySelector('#resultsErrors');\n        \n        timestamp.textContent = new Date().toLocaleString();\n        deletedFileCount.textContent = results.file_count || 0;\n        spaceFreed.textContent = `${(results.space_to_free_mb || 0).toFixed(1)} MB`;\n        \n        // Handle errors if any\n        if (results.errors && results.errors.length > 0) {\n            errorStat.style.display = 'flex';\n            errorCount.textContent = results.errors.length;\n            errorList.innerHTML = results.errors.map(error => `<li>${error}</li>`).join('');\n            resultsErrors.style.display = 'block';\n        } else {\n            errorStat.style.display = 'none';\n            resultsErrors.style.display = 'none';\n        }\n        \n        resultsDiv.style.display = 'block';\n        \n        // Scroll results into view\n        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });\n    }\n    \n    hideCleanupResults() {\n        const resultsDiv = this.modal.querySelector('#cleanupResults');\n        resultsDiv.style.display = 'none';\n    }\n    \n    showError(message) {\n        const orphanedList = this.modal.querySelector('#orphanedCameraList');\n        orphanedList.innerHTML = `\n            <div class=\"error-state\">\n                <i class=\"fas fa-exclamation-triangle status-error\"></i>\n                <p>Error loading data</p>\n                <small>${message}</small>\n                <button class=\"btn btn-outline-primary btn-sm\" onclick=\"this.closest('.storage-management-modal').querySelector('#refreshDataBtn').click()\">\n                    <i class=\"fas fa-retry\"></i>\n                    Retry\n                </button>\n            </div>\n        `;\n    }\n    \n    // Public method to open modal\n    static async open() {\n        if (!window.storageManagementModal) {\n            window.storageManagementModal = new StorageManagementModal();\n        }\n        \n        await window.storageManagementModal.open();\n        return window.storageManagementModal;\n    }\n}\n\n// Export for use in other modules\nif (typeof module !== 'undefined' && module.exports) {\n    module.exports = StorageManagementModal;\n}\n\nexport default StorageManagementModal;"