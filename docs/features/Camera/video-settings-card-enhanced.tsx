import React, { useState, useEffect } from 'react';
import { Camera, Video, HardDrive, AlertCircle, Check, Loader } from 'lucide-react';

const VideoSettingsCard = ({ camera = { id: 'demo-camera' }, onSettingsUpdate }) => {
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [recordingQuality, setRecordingQuality] = useState('1080p');
    const [storageEstimate, setStorageEstimate] = useState(null);
    const [success, setSuccess] = useState(false);

    // Quality options with details
    const qualityOptions = [
        {
            id: '4k',
            label: '4K (Main Stream)',
            resolution: '3840x2160',
            fps: 30,
            bitrate: '15 Mbps',
            source: 'Direct from camera',
            storagePerHour: '6.75 GB',
            daysIn10GB: 1.5,
            description: 'Highest quality, uses main camera stream directly'
        },
        {
            id: '1080p',
            label: '1080p HD',
            resolution: '1920x1080',
            fps: 25,
            bitrate: '5 Mbps',
            source: 'Transcoded from 4K',
            storagePerHour: '2.25 GB',
            daysIn10GB: 4.4,
            description: 'Balanced quality and storage, resized from 4K stream'
        },
        {
            id: '720p',
            label: '720p HD',
            resolution: '1280x720',
            fps: 25,
            bitrate: '2.5 Mbps',
            source: 'Transcoded from 4K',
            storagePerHour: '1.125 GB',
            daysIn10GB: 8.9,
            description: 'Good quality with efficient storage usage'
        },
        {
            id: '480p',
            label: '480p (Sub Stream)',
            resolution: '640x480',
            fps: 15,
            bitrate: '1 Mbps',
            source: 'Direct from camera sub-stream',
            storagePerHour: '450 MB',
            daysIn10GB: 22.2,
            description: 'Lowest quality but maximum storage efficiency'
        }
    ];

    useEffect(() => {
        if (camera && camera.id) {
            fetchCurrentSettings();
        }
    }, [camera?.id]);

    const fetchCurrentSettings = async () => {
        if (!camera || !camera.id) return;
        
        setLoading(true);
        try {
            const response = await fetch(`/api/cameras/${camera.id}/recording/quality`);
            if (response.ok) {
                const data = await response.json();
                // Map resolution to quality preset
                const quality = mapResolutionToQuality(data.resolution);
                setRecordingQuality(quality);
            }
        } catch (error) {
            console.error('Failed to fetch recording settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const mapResolutionToQuality = (resolution) => {
        switch (resolution) {
            case '3840x2160': return '4k';
            case '1920x1080': return '1080p';
            case '1280x720': return '720p';
            case '640x480': return '480p';
            default: return '1080p';
        }
    };

    const handleQualityChange = async (qualityId) => {
        setRecordingQuality(qualityId);
        const selectedQuality = qualityOptions.find(q => q.id === qualityId);
        
        // Update storage estimate
        setStorageEstimate({
            perHour: selectedQuality.storagePerHour,
            perDay: `${(parseFloat(selectedQuality.storagePerHour) * 24).toFixed(2)} GB`,
            daysRetention: selectedQuality.daysIn10GB
        });
    };

    const saveSettings = async () => {
        if (!camera || !camera.id) {
            console.error('No camera ID available');
            return;
        }
        
        setSaving(true);
        setSuccess(false);
        
        const selectedQuality = qualityOptions.find(q => q.id === recordingQuality);
        
        try {
            const response = await fetch(`/api/cameras/${camera.id}/recording/quality`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quality: recordingQuality === '4k' ? 'high' : recordingQuality === '480p' ? 'low' : 'medium',
                    resolution: selectedQuality.resolution,
                    fps: selectedQuality.fps,
                    bitrate: selectedQuality.bitrate,
                    source: selectedQuality.source
                })
            });

            if (response.ok) {
                setSuccess(true);
                setTimeout(() => setSuccess(false), 3000);
                
                // Notify parent component
                if (onSettingsUpdate) {
                    onSettingsUpdate({
                        quality: recordingQuality,
                        ...selectedQuality
                    });
                }
            } else {
                throw new Error('Failed to update settings');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            alert('Failed to update recording settings. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const selectedQuality = qualityOptions.find(q => q.id === recordingQuality);

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-6">
                <Video className="w-6 h-6 text-blue-600 mr-3" />
                <h3 className="text-xl font-semibold">Video Recording Settings</h3>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-8">
                    <Loader className="w-6 h-6 animate-spin text-blue-600" />
                    <span className="ml-2">Loading settings...</span>
                </div>
            ) : (
                <>
                    {/* Quality Selection */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 mb-3">
                            Recording Quality
                        </label>
                        <div className="space-y-3">
                            {qualityOptions.map((option) => (
                                <label
                                    key={option.id}
                                    className={`
                                        relative flex items-start p-4 border rounded-lg cursor-pointer
                                        transition-all duration-200
                                        ${recordingQuality === option.id 
                                            ? 'border-blue-500 bg-blue-50' 
                                            : 'border-gray-200 hover:border-gray-300'
                                        }
                                    `}
                                >
                                    <input
                                        type="radio"
                                        name="quality"
                                        value={option.id}
                                        checked={recordingQuality === option.id}
                                        onChange={(e) => handleQualityChange(e.target.value)}
                                        className="sr-only"
                                    />
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <span className="font-medium text-gray-900">
                                                    {option.label}
                                                </span>
                                                <span className="ml-2 text-sm text-gray-500">
                                                    ({option.resolution})
                                                </span>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-sm font-medium text-gray-700">
                                                    {option.storagePerHour}/hr
                                                </span>
                                                <span className="block text-xs text-gray-500">
                                                    ~{option.daysIn10GB} days in 10GB
                                                </span>
                                            </div>
                                        </div>
                                        <p className="mt-1 text-sm text-gray-600">
                                            {option.description}
                                        </p>
                                        <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                                            <span>{option.fps} FPS</span>
                                            <span>•</span>
                                            <span>{option.bitrate}</span>
                                            <span>•</span>
                                            <span>{option.source}</span>
                                        </div>
                                    </div>
                                    {recordingQuality === option.id && (
                                        <div className="absolute top-4 right-4">
                                            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                                <Check className="w-3 h-3 text-white" />
                                            </div>
                                        </div>
                                    )}
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Storage Estimate */}
                    {storageEstimate && (
                        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                            <div className="flex items-center mb-2">
                                <HardDrive className="w-5 h-5 text-gray-600 mr-2" />
                                <h4 className="font-medium text-gray-900">Storage Estimate</h4>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500">Per Hour:</span>
                                    <p className="font-medium">{storageEstimate.perHour}</p>
                                </div>
                                <div>
                                    <span className="text-gray-500">Per Day:</span>
                                    <p className="font-medium">{storageEstimate.perDay}</p>
                                </div>
                                <div>
                                    <span className="text-gray-500">Days in 10GB:</span>
                                    <p className="font-medium">{storageEstimate.daysRetention} days</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Current Settings Info */}
                    <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                        <div className="flex items-start">
                            <AlertCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium text-blue-900 mb-1">
                                    Current Recording Configuration
                                </p>
                                <p className="text-blue-700">
                                    {selectedQuality.id === '4k' || selectedQuality.id === '480p' 
                                        ? `Using camera's ${selectedQuality.id === '4k' ? 'main' : 'sub'} stream directly.`
                                        : `Transcoding from 4K main stream to ${selectedQuality.resolution}.`
                                    }
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex items-center justify-between">
                        <button
                            onClick={saveSettings}
                            disabled={saving}
                            className={`
                                px-6 py-2 rounded-md font-medium transition-all duration-200
                                ${saving 
                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                                    : 'bg-blue-600 text-white hover:bg-blue-700'
                                }
                            `}
                        >
                            {saving ? (
                                <span className="flex items-center">
                                    <Loader className="w-4 h-4 animate-spin mr-2" />
                                    Saving...
                                </span>
                            ) : (
                                'Save Settings'
                            )}
                        </button>
                        
                        {success && (
                            <span className="flex items-center text-green-600">
                                <Check className="w-5 h-5 mr-1" />
                                Settings saved successfully
                            </span>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default VideoSettingsCard;