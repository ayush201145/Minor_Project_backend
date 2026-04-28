"""
CityPulse-X Perception Helpers — Video and geometry utilities.
"""

import os
import glob


def get_latest_video(v_dir, lid):
    """Return the most recent video file matching the lane ID prefix."""
    files = glob.glob(os.path.join(v_dir, f"{lid}*.mp4"))
    return max(files, key=os.path.getmtime) if files else None


def calc_centroid(box):
    """Calculate the center point of a bounding box [x1, y1, x2, y2]."""
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
