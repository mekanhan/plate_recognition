"""
Core recording module for 24/7 continuous video recording
"""
from .continuous_recorder import ContinuousRecorder
from .recording_manager import RecordingManager

__all__ = ['ContinuousRecorder', 'RecordingManager']