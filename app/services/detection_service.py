import asyncio
import cv2
import time
import numpy as np
import os
import uuid
import traceback
import torch
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException
from app.services.license_plate_recognition_service import LicensePlateRecognitionService
from app.utils.license_plate_processor import process_detection_result
import logging

logger = logging.getLogger(__name__)
