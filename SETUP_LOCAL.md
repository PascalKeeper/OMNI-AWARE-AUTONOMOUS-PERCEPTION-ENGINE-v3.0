# Local laptop setup (no Grok Build tokens required)

## 1. Clone or pull the repo
```bash
git clone https://github.com/PascalKeeper/OMNI-AWARE-AUTONOMOUS-PERCEPTION-ENGINE-v3.0.git
cd OMNI-AWARE-AUTONOMOUS-PERCEPTION-ENGINE-v3.0
```

## 2. Python environment
```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the wired synthetic test (no nuScenes needed)
```bash
python src/wired_pipeline.py
```
This exercises the shared feature buffer, Fast BEV lookup, and the full advisory stack on synthetic frames. You should see advisories and a stopping-distance number.

## 4. Optional: nuScenes mini (only if you want real data later)
- Register at https://www.nuscenes.org/download
- Download v1.0-mini.tgz (~4 GB)
- ```bash
  mkdir -p /data/sets/nuscenes
  tar -xf v1.0-mini.tgz -C /data/sets/nuscenes
  pip install nuscenes-devkit
  ```
- The adapter scripts from the earlier Grok Build prompt are not yet in the repo. Once the data is present we can add them.

## 5. Run unit tests
```bash
python -m pytest tests/ -q          # if pytest is installed
# or
python tests/test_shared_feature_buffer.py
python tests/test_fast_bev.py
```

## Notes
- Everything above runs on a laptop with only Python 3.9+ and the packages in requirements.txt.
- No GPU, no TensorRT, no real vehicle required for this synthetic path.
- After you run the synthetic test, paste the output back here and we can push findings or wire the next layer.
