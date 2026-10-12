# OMNI-AWARE Autonomous Perception Engine v3.0

CPU-first perception pipeline for autonomous hazard detection and decision-making.

## Architecture

### 1. RGB Filter (`src/rgb_filter.py`)
Weighted luminance filter: **21% red, 70% green, 7% blue**.
- Reduces image data 3x (RGB -> single channel)
- Green-weighted because it carries most luminance detail
- Cuts memory bandwidth and decode load on the cluster

### 2. Quadrant Split (`src/quadrants.py`)
Spider-eye architecture: each sensor split into 4 quadrants.
- Bottom bumper sensors focus on the lower half (road surface)
- Upper sensors focus on the horizon
- Compute spread across quadrants instead of one full frame
- Region-of-interest processing per quadrant

### 3. RANSAC Inlier/Outlier Detection (`src/ransac.py`)
Inlier-outlier detection for weighing scenarios before they happen.
- Fits a model to road samples while rejecting outliers (boulders, debris)
- Example: 18-wheeler with logs — predicts whether falling logs veer left, right, or straight at the vehicle
- Keeps the perception system from being fooled by a single bad frame

### 4. Physics Kernel (`src/physics.py`)
Forward simulation of falling objects.
- Models mass, velocity, gravity, and road surface
- Predicts impact point and trajectory
- Gives the vehicle a heads-up on evasive direction

### 5. Decision Engine (`src/decision.py`)
Weighs survival odds against cost for each hazard path.
- Example: cliff on the left, waterfall on the right — scores both options
- Chooses the path with the best survival-to-cost ratio
- Not a full predictive simulation of every outcome; a fast heuristic scorer

## Performance

- Filter + quadrants + RANSAC: ~218 FPS on plain CPU (4.6 ms/frame)
- Data reduction: 3x fewer channels after RGB filter
- RANSAC rejects outliers cleanly (boulder detection verified)

## License

GPL v3