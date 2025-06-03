"""
Tracker for maintaining unique IDs for detected vehicles using Deep SORT.
"""
import numpy as np
import time

try:
    from deep_sort_realtime.deepsort import DeepSort
    DEEP_SORT_AVAILABLE = True
except ImportError:
    DEEP_SORT_AVAILABLE = False
    print("Warning: deep_sort_realtime not installed, using simple tracker instead.")

class ObjectTracker:
    def __init__(self):
        """Initialize the object tracker."""
        self.next_id = 0
        if DEEP_SORT_AVAILABLE:
            try:
                self.deepsort = DeepSort()
                self.use_deepsort = True
                print("Using DeepSort for object tracking")
            except Exception as e:
                print(f"Error initializing DeepSort: {e}")
                self.use_deepsort = False
        else:
            self.use_deepsort = False
            print("Using simple tracker")

    def assign_id(self, detection) -> int:
        """
        Assign a unique ID to a detection. Used as a simple placeholder 
        when full tracking is not needed.
        
        Args:
            detection: Detection data
            
        Returns:
            Unique ID for the detection
        """
        # Simple ID assignment (real tracking happens in update())
        object_id = self.next_id
        self.next_id += 1
        return object_id

    def update(self, detections, frame):
        """
        Update tracker with new detections.
        
        Args:
            detections: List of current detections with bounding boxes.
            frame: Current video frame for context.
        
        Returns:
            List of tracked objects with updated IDs.
        """
        if not self.use_deepsort or not detections:
            # Simple tracking - just assign IDs if they don't exist
            for i, det in enumerate(detections):
                if 'object_id' not in det:
                    det['object_id'] = self.assign_id(det)
            return detections
            
        try:
            # Detections need to be in the format [x1, y1, x2, y2, confidence]
            detection_boxes = []
            for det in detections:
                box = det["box"]
                confidence = det["confidence"]
                detection_boxes.append(box + [confidence])  # x1, y1, x2, y2, conf

            tracked_objects = self.deepsort.update(np.array(detection_boxes), frame)
            
            # Map tracking results back to original detections
            for i, track in enumerate(tracked_objects):
                track_id = track[4]  # ID from DeepSort
                if i < len(detections):
                    detections[i]['object_id'] = int(track_id)
                    
            return detections
        except Exception as e:
            print(f"Error in tracking: {e}")
            # Fallback to simple tracking
            for i, det in enumerate(detections):
                if 'object_id' not in det:
                    det['object_id'] = self.assign_id(det)
            return detections
