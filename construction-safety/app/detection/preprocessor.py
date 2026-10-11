"""Lightweight frame preprocessing for CPU-bound inference.

All operations are chosen to cost < 5 ms on a typical VGA frame so they
never become a bottleneck on the Ryzen 5 5625U.
"""
from __future__ import annotations

import cv2
import numpy as np

# CLAHE (Contrast Limited Adaptive Histogram Equalisation) improves
# detection in shadows, backlighting, and low-light construction sites.
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


def preprocess(
    frame: np.ndarray,
    *,
    enhance_contrast: bool = True,
    denoise: bool = False,
) -> np.ndarray:
    """Return a preprocessed copy of *frame*.

    Parameters
    ----------
    enhance_contrast:
        Apply CLAHE to the luminance channel.  Helps YOLO see PPE in
        difficult lighting without changing colour information.
    denoise:
        Light Gaussian blur to soften heavy JPEG compression artefacts
        from the ESP32-CAM.  Disabled by default because it slightly
        softens edges that YOLO relies on.
    """
    result = frame

    if enhance_contrast:
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = _clahe.apply(lab[:, :, 0])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    if denoise:
        result = cv2.GaussianBlur(result, (3, 3), 0)

    return result
