<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Configuration Modal</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-muted: #a0aec0;
            --border-color: #e2e8f0;
            --accent-color: #4299e1;
            --success-color: #48bb78;
            --warning-color: #ed8936;
            --danger-color: #f56565;
            --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            --modal-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f7fafc;
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }

        .demo-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 2rem;
            align-items: flex-start;
        }

        .demo-card {
            background: var(--bg-primary);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            box-shadow: var(--card-shadow);
            padding: 1.5rem;
            flex-shrink: 0;
        }

        .demo-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
        }

        .trigger-btn {
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .trigger-btn:hover {
            background: #3182ce;
            transform: translateY(-1px);
        }

        /* Modal Overlay */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 2rem;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }

        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .modal-container {
            background: var(--bg-primary);
            border-radius: 16px;
            box-shadow: var(--modal-shadow);
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            overflow: hidden;
            transform: scale(0.95);
            transition: transform 0.3s ease;
        }

        .modal-overlay.active .modal-container {
            transform: scale(1);
        }

        .modal-header {
            display: flex;
            align-items: center;
            justify-content: between;
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        }

        .modal-header-left {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
        }

        .modal-icon {
            background: var(--accent-color);
            color: white;
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
        }

        .modal-title-info h2 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .modal-title-info p {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--text-muted);
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        .modal-close:hover {
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }

        .modal-body {
            height: 70vh;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border-color) transparent;
        }

        .modal-body::-webkit-scrollbar {
            width: 6px;
        }

        .modal-body::-webkit-scrollbar-track {
            background: transparent;
        }

        .modal-body::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }

        /* Tab Navigation */
        .tab-navigation {
            display: flex;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .tab-btn {
            flex: 1;
            padding: 1rem 1.5rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            border-bottom: 3px solid transparent;
        }

        .tab-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        .tab-btn.active {
            background: var(--bg-primary);
            color: var(--accent-color);
            border-bottom-color: var(--accent-color);
        }

        /* Tab Content */
        .tab-content {
            display: none;
            padding: 2rem;
        }

        .tab-content.active {
            display: block;
        }

        .section {
            margin-bottom: 2rem;
        }

        .section:last-child {
            margin-bottom: 0;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-description {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
        }

        .form-grid.two-column {
            grid-template-columns: 1fr 1fr;
        }

        .form-grid.three-column {
            grid-template-columns: repeat(3, 1fr);
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-group.full-width {
            grid-column: 1 / -1;
        }

        .form-label {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-label .required {
            color: var(--danger-color);
        }

        .form-input, .form-select, .form-textarea {
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }

        .form-input:focus, .form-select:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }

        .form-textarea {
            resize: vertical;
            min-height: 80px;
        }

        .form-help {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }

        /* Range Slider */
        .range-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .range-slider {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--bg-tertiary);
            outline: none;
        }

        .range-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--accent-color);
            cursor: pointer;
            border: 3px solid white;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        .range-slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--accent-color);
            cursor: pointer;
            border: 3px solid white;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        .range-display {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .range-value {
            background: var(--bg-secondary);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: 600;
            color: var(--text-primary);
        }

        /* Toggle Switch */
        .toggle-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .toggle-switch {
            position: relative;
            width: 48px;
            height: 24px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .toggle-switch.active {
            background: var(--accent-color);
        }

        .toggle-switch::before {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .toggle-switch.active::before {
            transform: translateX(24px);
        }

        .toggle-label {
            font-weight: 500;
            color: var(--text-primary);
        }

        /* Button Groups */
        .button-group {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .btn-option {
            padding: 0.5rem 1rem;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            color: var(--text-secondary);
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .btn-option:hover {
            background: var(--bg-secondary);
            border-color: var(--accent-color);
        }

        .btn-option.active {
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }

        /* ROI Canvas */
        .roi-container {
            position: relative;
            background: #1a202c;
            border-radius: 8px;
            overflow: hidden;
            aspect-ratio: 16/9;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .roi-canvas {
            width: 100%;
            height: 100%;
            cursor: crosshair;
        }

        .roi-placeholder {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
        }

        .roi-placeholder i {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }

        /* Test Connection */
        .test-connection {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }

        .test-btn {
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .test-btn:hover {
            background: #3182ce;
        }

        .test-btn:disabled {
            background: var(--text-muted);
            cursor: not-allowed;
        }

        .test-result {
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .test-result.success {
            background: rgba(72, 187, 120, 0.1);
            color: var(--success-color);
            border: 1px solid rgba(72, 187, 120, 0.2);
        }

        .test-result.error {
            background: rgba(245, 101, 101, 0.1);
            color: var(--danger-color);
            border: 1px solid rgba(245, 101, 101, 0.2);
        }

        .test-result.testing {
            background: rgba(66, 153, 225, 0.1);
            color: var(--accent-color);
            border: 1px solid rgba(66, 153, 225, 0.2);
        }

        /* Modal Footer */
        .modal-footer {
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--accent-color);
            color: white;
        }

        .btn-primary:hover {
            background: #3182ce;
        }

        .btn-secondary {
            background: white;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--bg-tertiary);
        }

        .btn-success {
            background: var(--success-color);
            color: white;
        }

        .btn-success:hover {
            background: #38a169;
        }

        /* Preview Cards */
        .preview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .preview-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }

        .preview-card h4 {
            margin: 0 0 0.5rem 0;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .preview-card .value {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent-color);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .modal-container {
                margin: 1rem;
                max-height: 95vh;
            }

            .form-grid.two-column,
            .form-grid.three-column {
                grid-template-columns: 1fr;
            }

            .tab-btn {
                padding: 0.75rem 1rem;
                font-size: 0.875rem;
            }

            .modal-header {
                padding: 1rem 1.5rem;
            }

            .tab-content {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="demo-container">
        <div class="demo-card">
            <h3 class="demo-title">Camera Configuration</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                Click the button below to open the comprehensive camera configuration modal with all settings and features.
            </p>
            <button class="trigger-btn" onclick="openModal()">
                <i class="fas fa-cog"></i>
                Configure Camera
            </button>
        </div>
    </div>

    <!-- Modal -->
    <div class="modal-overlay" id="configModal">
        <div class="modal-container">
            <div class="modal-header">
                <div class="modal-header-left">
                    <div class="modal-icon">
                        <i class="fas fa-video"></i>
                    </div>
                    <div class="modal-title-info">
                        <h2>Configure Camera</h2>
                        <p>Test Camera 1 • Reolink RLC-811A</p>
                    </div>
                </div>
                <button class="modal-close" onclick="closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="modal-body">
                <!-- Tab Navigation -->
                <div class="tab-navigation">
                    <button class="tab-btn active" data-tab="network">
                        <i class="fas fa-network-wired"></i>
                        Network
                    </button>
                    <button class="tab-btn" data-tab="camera">
                        <i class="fas fa-video"></i>
                        Camera
                    </button>
                    <button class="tab-btn" data-tab="ai">
                        <i class="fas fa-brain"></i>
                        AI & Detection
                    </button>
                    <button class="tab-btn" data-tab="advanced">
                        <i class="fas fa-cogs"></i>
                        Advanced
                    </button>
                </div>

                <!-- Network Configuration Tab -->
                <div class="tab-content active" id="network">
                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-globe"></i>
                            Network Connection
                        </h3>
                        <p class="section-description">
                            Configure network settings to establish connection with your camera. Ensure the camera is accessible on your network.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">
                                    Camera Name <span class="required">*</span>
                                </label>
                                <input type="text" class="form-input" value="Test Camera 1" placeholder="Enter camera name">
                                <div class="form-help">Unique identifier for this camera</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Location <span class="required">*</span>
                                </label>
                                <select class="form-select">
                                    <option value="entrance">Entrance</option>
                                    <option value="parking">Parking Lot</option>
                                    <option value="exit">Exit Gate</option>
                                    <option value="lobby">Lobby</option>
                                    <option value="custom">Custom Location</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    IP Address <span class="required">*</span>
                                </label>
                                <input type="text" class="form-input" value="10.0.0.181" placeholder="192.168.1.100">
                                <div class="form-help">Camera's network IP address</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Connection Type <span class="required">*</span>
                                </label>
                                <select class="form-select">
                                    <option value="http">HTTP</option>
                                    <option value="https">HTTPS</option>
                                    <option value="rtsp">RTSP</option>
                                    <option value="onvif">ONVIF</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Port <span class="required">*</span>
                                </label>
                                <input type="number" class="form-input" value="80" placeholder="80">
                                <div class="form-help">Default ports: HTTP(80), HTTPS(443), RTSP(554), ONVIF(80)</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Stream Path
                                </label>
                                <input type="text" class="form-input" value="/mjpeg" placeholder="/stream1">
                                <div class="form-help">URL path to video stream (e.g., /mjpeg, /stream1)</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-key"></i>
                            Authentication
                        </h3>
                        <p class="section-description">
                            Provide authentication credentials if required by your camera.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">Username</label>
                                <input type="text" class="form-input" value="admin" placeholder="username">
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-input" value="password123" placeholder="••••••••">
                            </div>
                        </div>
                    </div>

                    <div class="test-connection">
                        <button class="test-btn" onclick="testConnection()">
                            <i class="fas fa-plug"></i>
                            Test Connection
                        </button>
                        <div class="test-result success" style="display: none;" id="testResult">
                            <i class="fas fa-check-circle"></i>
                            Connection successful! Camera is responding normally.
                        </div>
                    </div>
                </div>

                <!-- Camera Settings Tab -->
                <div class="tab-content" id="camera">
                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-film"></i>
                            Video Settings
                        </h3>
                        <p class="section-description">
                            Configure video quality, resolution, and recording parameters for optimal performance.
                        </p>
                        
                        <div class="form-grid three-column">
                            <div class="form-group">
                                <label class="form-label">Resolution</label>
                                <select class="form-select">
                                    <option value="4k">4K Ultra (3840×2160)</option>
                                    <option value="2k">2K (2560×1440)</option>
                                    <option value="1080p" selected>1080p HD (1920×1080)</option>
                                    <option value="720p">720p HD (1280×720)</option>
                                    <option value="480p">480p (854×480)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Frame Rate</label>
                                <select class="form-select">
                                    <option value="60">60 FPS</option>
                                    <option value="30" selected>30 FPS</option>
                                    <option value="25">25 FPS</option>
                                    <option value="15">15 FPS</option>
                                    <option value="10">10 FPS</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Compression</label>
                                <select class="form-select">
                                    <option value="h265">H.265 (HEVC)</option>
                                    <option value="h264" selected>H.264</option>
                                    <option value="mjpeg">MJPEG</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Bitrate (Kbps)</label>
                            <div class="range-group">
                                <input type="range" class="range-slider" min="500" max="8000" value="2000" id="bitrateSlider">
                                <div class="range-display">
                                    <span>500 Kbps</span>
                                    <span class="range-value" id="bitrateValue">2000 Kbps</span>
                                    <span>8000 Kbps</span>
                                </div>
                            </div>
                            <div class="form-help">Higher bitrate = better quality but more bandwidth usage</div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-adjust"></i>
                            Image Quality
                        </h3>
                        <p class="section-description">
                            Adjust image parameters for optimal visual quality based on your environment.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">Brightness</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="0" max="100" value="50" id="brightnessSlider">
                                    <div class="range-display">
                                        <span>0</span>
                                        <span class="range-value" id="brightnessValue">50</span>
                                        <span>100</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Contrast</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="0" max="100" value="50" id="contrastSlider">
                                    <div class="range-display">
                                        <span>0</span>
                                        <span class="range-value" id="contrastValue">50</span>
                                        <span>100</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Saturation</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="0" max="100" value="50" id="saturationSlider">
                                    <div class="range-display">
                                        <span>0</span>
                                        <span class="range-value" id="saturationValue">50</span>
                                        <span>100</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Sharpness</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="0" max="100" value="50" id="sharpnessSlider">
                                    <div class="range-display">
                                        <span>0</span>
                                        <span class="range-value" id="sharpnessValue">50</span>
                                        <span>100</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-search"></i>
                            Camera Controls
                        </h3>
                        <p class="section-description">
                            Configure zoom, focus, and positioning settings for your camera.
                        </p>
                        
                        <div class="form-grid three-column">
                            <div class="form-group">
                                <label class="form-label">Zoom Level</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="1" max="10" value="1.5" step="0.1" id="zoomSlider">
                                    <div class="range-display">
                                        <span>1.0x</span>
                                        <span class="range-value" id="zoomValue">1.5x</span>
                                        <span>10.0x</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Focus Mode</label>
                                <select class="form-select">
                                    <option value="auto" selected>Auto Focus</option>
                                    <option value="manual">Manual Focus</option>
                                    <option value="infinity">Infinity Focus</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">White Balance</label>
                                <select class="form-select">
                                    <option value="auto" selected>Auto</option>
                                    <option value="daylight">Daylight</option>
                                    <option value="fluorescent">Fluorescent</option>
                                    <option value="incandescent">Incandescent</option>
                                    <option value="cloudy">Cloudy</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-moon"></i>
                            Night Vision & Special Features
                        </h3>
                        <p class="section-description">
                            Configure low-light settings and special camera features.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Night Vision (IR)</span>
                                </div>
                                <div class="form-help">Enable infrared illumination for night recording</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Spotlight Control</span>
                                </div>
                                <div class="form-help">Control built-in LED spotlight</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Wide Dynamic Range (WDR)</span>
                                </div>
                                <div class="form-help">Improve image quality in high contrast scenes</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Digital Noise Reduction</span>
                                </div>
                                <div class="form-help">Reduce noise in low-light conditions</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-clock"></i>
                            Recording Settings
                        </h3>
                        <p class="section-description">
                            Configure recording modes and storage settings.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">Recording Mode</label>
                                <div class="button-group">
                                    <button class="btn-option active">Continuous</button>
                                    <button class="btn-option">Motion Only</button>
                                    <button class="btn-option">Scheduled</button>
                                    <button class="btn-option">Manual</button>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Pre-Record Duration</label>
                                <select class="form-select">
                                    <option value="0">No Pre-Record</option>
                                    <option value="5" selected>5 seconds</option>
                                    <option value="10">10 seconds</option>
                                    <option value="15">15 seconds</option>
                                    <option value="30">30 seconds</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AI & Detection Tab -->
                <div class="tab-content" id="ai">
                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-car"></i>
                            License Plate Recognition
                        </h3>
                        <p class="section-description">
                            Configure AI-powered license plate detection and recognition settings.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Enable LPR</span>
                                </div>
                                <div class="form-help">Enable automatic license plate recognition</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Detection Confidence Threshold</label>
                                <div class="range-group">
                                    <input type="range" class="range-slider" min="50" max="95" value="75" id="confidenceSlider">
                                    <div class="range-display">
                                        <span>50%</span>
                                        <span class="range-value" id="confidenceValue">75%</span>
                                        <span>95%</span>
                                    </div>
                                </div>
                                <div class="form-help">Minimum confidence level to trigger detection</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">License Plate Regions</label>
                                <select class="form-select" multiple>
                                    <option value="us" selected>United States</option>
                                    <option value="eu">European Union</option>
                                    <option value="uk">United Kingdom</option>
                                    <option value="ca">Canada</option>
                                    <option value="au">Australia</option>
                                    <option value="jp">Japan</option>
                                </select>
                                <div class="form-help">Select regions for license plate format recognition</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Processing Speed vs Accuracy</label>
                                <div class="button-group">
                                    <button class="btn-option">Fast</button>
                                    <button class="btn-option active">Balanced</button>
                                    <button class="btn-option">Accurate</button>
                                </div>
                                <div class="form-help">Fast: Real-time | Balanced: Good performance | Accurate: Best quality</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-vector-square"></i>
                            Detection Zones (ROI)
                        </h3>
                        <p class="section-description">
                            Define regions of interest where license plate detection should be active. Click and drag to create detection zones.
                        </p>
                        
                        <div class="form-group full-width">
                            <div class="roi-container">
                                <canvas class="roi-canvas" id="roiCanvas" width="640" height="360"></canvas>
                                <div class="roi-placeholder" id="roiPlaceholder">
                                    <i class="fas fa-video"></i>
                                    <p>Live camera feed will appear here</p>
                                    <small>Click and drag to create detection zones</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-grid three-column">
                            <div class="form-group">
                                <label class="form-label">Zone Name</label>
                                <input type="text" class="form-input" placeholder="Entry Lane 1" value="Main Detection Zone">
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Zone Priority</label>
                                <select class="form-select">
                                    <option value="high">High Priority</option>
                                    <option value="medium" selected>Medium Priority</option>
                                    <option value="low">Low Priority</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Zone Actions</label>
                                <div class="button-group">
                                    <button class="btn-option active">Add Zone</button>
                                    <button class="btn-option">Clear All</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-eye"></i>
                            Smart Detection Features
                        </h3>
                        <p class="section-description">
                            Configure additional AI-powered detection capabilities.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Vehicle Detection</span>
                                </div>
                                <div class="form-help">Detect and classify vehicles (car, truck, motorcycle)</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Person Detection</span>
                                </div>
                                <div class="form-help">Detect people in the camera view</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Speed Estimation</span>
                                </div>
                                <div class="form-help">Estimate vehicle speed based on movement</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Direction Analysis</span>
                                </div>
                                <div class="form-help">Determine vehicle direction (entering/exiting)</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-bell"></i>
                            Alert Configuration
                        </h3>
                        <p class="section-description">
                            Set up automated alerts and notifications based on detection events.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Real-time Alerts</span>
                                </div>
                                <div class="form-help">Send instant notifications for new detections</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Alert Channels</label>
                                <select class="form-select" multiple>
                                    <option value="dashboard" selected>Dashboard</option>
                                    <option value="email">Email</option>
                                    <option value="sms">SMS</option>
                                    <option value="webhook">Webhook</option>
                                    <option value="slack">Slack</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Alert Conditions</label>
                                <div class="button-group">
                                    <button class="btn-option active">All Detections</button>
                                    <button class="btn-option">High Confidence Only</button>
                                    <button class="btn-option">Suspicious Activity</button>
                                    <button class="btn-option">Custom Rules</button>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Alert Frequency Limit</label>
                                <select class="form-select">
                                    <option value="immediate">Immediate</option>
                                    <option value="1min">Max 1 per minute</option>
                                    <option value="5min" selected>Max 1 per 5 minutes</option>
                                    <option value="15min">Max 1 per 15 minutes</option>
                                    <option value="1hour">Max 1 per hour</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-chart-line"></i>
                            Performance Preview
                        </h3>
                        <p class="section-description">
                            Preview of expected AI performance with current settings.
                        </p>
                        
                        <div class="preview-grid">
                            <div class="preview-card">
                                <h4>Detection Rate</h4>
                                <div class="value">~8-12/min</div>
                            </div>
                            <div class="preview-card">
                                <h4>Accuracy</h4>
                                <div class="value">94.5%</div>
                            </div>
                            <div class="preview-card">
                                <h4>Processing Latency</h4>
                                <div class="value">250ms</div>
                            </div>
                            <div class="preview-card">
                                <h4>CPU Usage</h4>
                                <div class="value">15-25%</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Advanced Settings Tab -->
                <div class="tab-content" id="advanced">
                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-server"></i>
                            System Integration
                        </h3>
                        <p class="section-description">
                            Configure advanced system integration and performance settings.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">Processing Priority</label>
                                <select class="form-select">
                                    <option value="low">Low Priority</option>
                                    <option value="normal" selected>Normal Priority</option>
                                    <option value="high">High Priority</option>
                                    <option value="realtime">Real-time Priority</option>
                                </select>
                                <div class="form-help">Higher priority uses more system resources</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Buffer Size (frames)</label>
                                <input type="number" class="form-input" value="30" min="5" max="100">
                                <div class="form-help">Number of frames to buffer for processing</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Retry Attempts</label>
                                <input type="number" class="form-input" value="3" min="1" max="10">
                                <div class="form-help">Connection retry attempts before marking offline</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Health Check Interval</label>
                                <select class="form-select">
                                    <option value="10">10 seconds</option>
                                    <option value="30" selected>30 seconds</option>
                                    <option value="60">1 minute</option>
                                    <option value="300">5 minutes</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-database"></i>
                            Data Storage & Retention
                        </h3>
                        <p class="section-description">
                            Configure how detection data and recordings are stored and managed.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <label class="form-label">Detection Data Retention</label>
                                <select class="form-select">
                                    <option value="7">7 days</option>
                                    <option value="30" selected>30 days</option>
                                    <option value="90">90 days</option>
                                    <option value="365">1 year</option>
                                    <option value="unlimited">Unlimited</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Video Recording Retention</label>
                                <select class="form-select">
                                    <option value="3">3 days</option>
                                    <option value="7" selected>7 days</option>
                                    <option value="30">30 days</option>
                                    <option value="90">90 days</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Auto-cleanup Old Data</span>
                                </div>
                                <div class="form-help">Automatically delete old data based on retention policy</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Compress Old Recordings</span>
                                </div>
                                <div class="form-help">Compress recordings older than 24 hours</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-shield-alt"></i>
                            Security & Access Control
                        </h3>
                        <p class="section-description">
                            Configure security settings and access control for this camera.
                        </p>
                        
                        <div class="form-grid two-column">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Require Authentication</span>
                                </div>
                                <div class="form-help">Require login to view camera feed</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch active" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Encrypt Stream</span>
                                </div>
                                <div class="form-help">Use SSL/TLS encryption for video stream</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Access Level</label>
                                <select class="form-select">
                                    <option value="public">Public Access</option>
                                    <option value="authenticated">Authenticated Users</option>
                                    <option value="restricted" selected>Restricted Access</option>
                                    <option value="admin">Admin Only</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Allowed IP Ranges</label>
                                <textarea class="form-textarea" placeholder="192.168.1.0/24&#10;10.0.0.0/16&#10;Leave empty for no restrictions"></textarea>
                                <div class="form-help">One IP range per line (CIDR notation)</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-code"></i>
                            API & Webhooks
                        </h3>
                        <p class="section-description">
                            Configure API endpoints and webhook notifications for external integrations.
                        </p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <div class="toggle-group">
                                    <div class="toggle-switch" onclick="toggleSwitch(this)"></div>
                                    <span class="toggle-label">Enable Webhook Notifications</span>
                                </div>
                                <div class="form-help">Send HTTP POST requests for detection events</div>
                            </div>
                            
                            <div class="form-group full-width">
                                <label class="form-label">Webhook URL</label>
                                <input type="url" class="form-input" placeholder="https://your-server.com/webhook/camera-events">
                                <div class="form-help">URL to receive detection event notifications</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Webhook Events</label>
                                <select class="form-select" multiple>
                                    <option value="detection" selected>New Detection</option>
                                    <option value="camera_online">Camera Online</option>
                                    <option value="camera_offline">Camera Offline</option>
                                    <option value="low_confidence">Low Confidence Detection</option>
                                    <option value="system_alert">System Alert</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">API Rate Limit (requests/minute)</label>
                                <input type="number" class="form-input" value="100" min="10" max="1000">
                                <div class="form-help">Maximum API requests per minute</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h3 class="section-title">
                            <i class="fas fa-download"></i>
                            Backup & Export
                        </h3>
                        <p class="section-description">
                            Backup camera configuration and export settings for other cameras.
                        </p>
                        
                        <div class="form-grid three-column">
                            <div class="form-group">
                                <button class="btn btn-secondary" style="width: 100%;">
                                    <i class="fas fa-download"></i>
                                    Export Config
                                </button>
                                <div class="form-help">Download configuration as JSON file</div>
                            </div>
                            
                            <div class="form-group">
                                <button class="btn btn-secondary" style="width: 100%;">
                                    <i class="fas fa-upload"></i>
                                    Import Config
                                </button>
                                <div class="form-help">Load configuration from JSON file</div>
                            </div>
                            
                            <div class="form-group">
                                <button class="btn btn-secondary" style="width: 100%;">
                                    <i class="fas fa-copy"></i>
                                    Clone to Cameras
                                </button>
                                <div class="form-help">Apply settings to multiple cameras</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="resetToDefaults()">
                    <i class="fas fa-undo"></i>
                    Reset to Defaults
                </button>
                <button class="btn btn-primary" onclick="testAllSettings()">
                    <i class="fas fa-vial"></i>
                    Test All Settings
                </button>
                <button class="btn btn-secondary" onclick="closeModal()">
                    Cancel
                </button>
                <button class="btn btn-success" onclick="saveConfiguration()">
                    <i class="fas fa-save"></i>
                    Save Configuration
                </button>
            </div>
        </div>
    </div>

    <script>
        // Modal functionality
        function openModal() {
            document.getElementById('configModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            document.getElementById('configModal').classList.remove('active');
            document.body.style.overflow = '';
        }

        // Tab functionality
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                
                // Update tab buttons
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update tab content
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(targetTab).classList.add('active');
            });
        });

        // Range slider functionality
        function updateRangeValue(sliderId, valueId, suffix = '') {
            const slider = document.getElementById(sliderId);
            const valueDisplay = document.getElementById(valueId);
            
            slider.addEventListener('input', () => {
                valueDisplay.textContent = slider.value + suffix;
            });
        }

        // Initialize range sliders
        updateRangeValue('bitrateSlider', 'bitrateValue', ' Kbps');
        updateRangeValue('brightnessSlider', 'brightnessValue');
        updateRangeValue('contrastSlider', 'contrastValue');
        updateRangeValue('saturationSlider', 'saturationValue');
        updateRangeValue('sharpnessSlider', 'sharpnessValue');
        updateRangeValue('zoomSlider', 'zoomValue', 'x');
        updateRangeValue('confidenceSlider', 'confidenceValue', '%');

        // Toggle switch functionality
        function toggleSwitch(element) {
            element.classList.toggle('active');
        }

        // Button group functionality
        document.querySelectorAll('.button-group').forEach(group => {
            group.addEventListener('click', (e) => {
                if (e.target.classList.contains('btn-option')) {
                    group.querySelectorAll('.btn-option').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    e.target.classList.add('active');
                }
            });
        });

        // ROI Canvas functionality
        const canvas = document.getElementById('roiCanvas');
        const ctx = canvas.getContext('2d');
        let isDrawing = false;
        let startX, startY;
        const zones = [];

        canvas.addEventListener('mousedown', (e) => {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
        });

        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            // Clear and redraw
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawExistingZones();
            drawCurrentZone(startX, startY, currentX, currentY);
        });

        canvas.addEventListener('mouseup', (e) => {
            if (!isDrawing) return;
            isDrawing = false;
            
            const rect = canvas.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;
            
            // Add new zone
            zones.push({
                x: Math.min(startX, endX),
                y: Math.min(startY, endY),
                width: Math.abs(endX - startX),
                height: Math.abs(endY - startY)
            });
            
            drawExistingZones();
        });

        function drawExistingZones() {
            zones.forEach((zone, index) => {
                ctx.strokeStyle = '#4299e1';
                ctx.fillStyle = 'rgba(66, 153, 225, 0.2)';
                ctx.lineWidth = 2;
                ctx.fillRect(zone.x, zone.y, zone.width, zone.height);
                ctx.strokeRect(zone.x, zone.y, zone.width, zone.height);
                
                // Add zone label
                ctx.fillStyle = '#4299e1';
                ctx.font = '12px Arial';
                ctx.fillText(`Zone ${index + 1}`, zone.x + 5, zone.y + 15);
            });
        }

        function drawCurrentZone(x1, y1, x2, y2) {
            ctx.strokeStyle = '#ed8936';
            ctx.fillStyle = 'rgba(237, 137, 54, 0.2)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);
            
            ctx.fillRect(x, y, width, height);
            ctx.strokeRect(x, y, width, height);
            ctx.setLineDash([]);
        }

        // Initialize canvas with sample background
        function initCanvas() {
            ctx.fillStyle = '#2d3748';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid pattern
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.lineWidth = 1;
            for (let i = 0; i < canvas.width; i += 40) {
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, canvas.height);
                ctx.stroke();
            }
            for (let i = 0; i < canvas.height; i += 40) {
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }
            
            // Add sample zone
            zones.push({x: 100, y: 80, width: 440, height: 200});
            drawExistingZones();
        }

        // Test connection functionality
        function testConnection() {
            const testBtn = document.querySelector('.test-btn');
            const testResult = document.getElementById('testResult');
            
            testBtn.disabled = true;
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            
            testResult.className = 'test-result testing';
            testResult.innerHTML = '<i class="fas fa-clock"></i> Testing connection...';
            testResult.style.display = 'block';
            
            // Simulate test
            setTimeout(() => {
                const success = Math.random() > 0.2; // 80% success rate
                
                if (success) {
                    testResult.className = 'test-result success';
                    testResult.innerHTML = '<i class="fas fa-check-circle"></i> Connection successful! Camera is responding normally.';
                } else {
                    testResult.className = 'test-result error';
                    testResult.innerHTML = '<i class="fas fa-exclamation-circle"></i> Connection failed. Please check IP address and credentials.';
                }
                
                testBtn.disabled = false;
                testBtn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
            }, 2000);
        }

        // Reset to defaults
        function resetToDefaults() {
            if (confirm('Are you sure you want to reset all settings to default values? This action cannot be undone.')) {
                // Reset form values
                document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(input => {
                    if (input.hasAttribute('value')) {
                        input.value = input.getAttribute('value');
                    } else {
                        input.value = '';
                    }
                });
                
                // Reset toggles
                document.querySelectorAll('.toggle-switch').forEach(toggle => {
                    toggle.classList.remove('active');
                });
                
                // Reset some key toggles to active
                const defaultActiveToggles = [
                    'Night Vision (IR)',
                    'Enable LPR',
                    'Vehicle Detection',
                    'Real-time Alerts'
                ];
                
                document.querySelectorAll('.toggle-label').forEach(label => {
                    if (defaultActiveToggles.includes(label.textContent)) {
                        label.previousElementSibling.classList.add('active');
                    }
                });
                
                // Reset button groups
                document.querySelectorAll('.button-group').forEach(group => {
                    group.querySelectorAll('.btn-option').forEach(btn => btn.classList.remove('active'));
                    group.querySelector('.btn-option').classList.add('active');
                });
                
                // Clear ROI zones
                zones.length = 0;
                initCanvas();
                
                alert('Settings have been reset to default values.');
            }
        }

        // Test all settings
        function testAllSettings() {
            const testBtn = event.target;
            testBtn.disabled = true;
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing All Settings...';
            
            // Simulate comprehensive testing
            setTimeout(() => {
                const testResults = [
                    'Network connection: ✓ Success',
                    'Camera settings: ✓ Applied successfully',
                    'AI detection: ✓ Models loaded',
                    'ROI zones: ✓ 1 zone configured',
                    'Storage settings: ✓ Validated',
                    'Security settings: ✓ Configured'
                ];
                
                alert('Configuration Test Results:\n\n' + testResults.join('\n') + '\n\nAll settings are valid and ready to apply.');
                
                testBtn.disabled = false;
                testBtn.innerHTML = '<i class="fas fa-vial"></i> Test All Settings';
            }, 3000);
        }

        // Save configuration
        function saveConfiguration() {
            const saveBtn = event.target;
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            
            // Simulate save operation
            setTimeout(() => {
                alert('Camera configuration saved successfully!\n\nThe camera will restart with new settings in a few moments.');
                closeModal();
                
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Configuration';
            }, 2000);
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveConfiguration();
            }
        });

        // Click outside to close
        document.getElementById('configModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                closeModal();
            }
        });

        // Initialize canvas when page loads
        document.addEventListener('DOMContentLoaded', () => {
            initCanvas();
        });

        // Simulate real-time updates for performance preview
        setInterval(() => {
            const cards = document.querySelectorAll('.preview-card .value');
            if (cards.length > 0) {
                // Update detection rate
                const detectionRate = Math.floor(Math.random() * 5) + 8;
                cards[0].textContent = `~${detectionRate}-${detectionRate + 4}/min`;
                
                // Update accuracy
                const accuracy = (94 + Math.random() * 2).toFixed(1);
                cards[1].textContent = `${accuracy}%`;
                
                // Update latency
                const latency = Math.floor(Math.random() * 100) + 200;
                cards[2].textContent = `${latency}ms`;
                
                // Update CPU usage
                const cpuMin = Math.floor(Math.random() * 10) + 15;
                const cpuMax = cpuMin + Math.floor(Math.random() * 10) + 5;
                cards[3].textContent = `${cpuMin}-${cpuMax}%`;
            }
        }, 3000);

        // Auto-save draft functionality
        let autoSaveTimeout;
        document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(autoSaveTimeout);
                autoSaveTimeout = setTimeout(() => {
                    console.log('Auto-saving draft configuration...');
                    // In a real application, this would save to localStorage or send to server
                }, 2000);
            });
        });

        // Form validation
        function validateForm() {
            const requiredFields = document.querySelectorAll('.form-input[required], .form-select[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'var(--danger-color)';
                    isValid = false;
                } else {
                    field.style.borderColor = 'var(--border-color)';
                }
            });
            
            return isValid;
        }

        // Add validation indicators
        document.querySelectorAll('.form-input, .form-select').forEach(input => {
            input.addEventListener('blur', validateForm);
        });
    </script>
</body>
</html>