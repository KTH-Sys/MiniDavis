# Rylee — Day 5 & Day 6 Implementation

## Day 5: Trading Implementation

**Assigned task:** Implement trade offers and acceptance between residents, with safe resource transfers.

### Work completed
- Updated `backend/app/schemas.py` to support trade offers and trade actions.
- Updated `backend/app/world.py` to implement trade creation, acceptance, and resource transfers.
- Added support for pending, accepted, and rejected trade offers.
- Ensured that creating an offer does not immediately transfer resources.
- Implemented validation to prevent:
  - Accepting the same trade more than once.
  - Accepting another resident's trade.
  - Trading resources that are no longer available.
  - Reusing an existing trade offer ID.
- Created `backend/tests/test_trade.py` to verify trading behavior.

### Test results
- Trading safety tests passed locally.
- Fixed notebook validation compatibility after adding trade fields to the action schema.
- GitHub Actions passed after the compatibility fix.

## Day 6: Trading Verification and CPU Classifier Integration

**Assigned tasks:** Finish trading, shortage, reset and replay; implement the classifier-loading hook; package the CPU backend and measure RAM before deployment.

### Trading, shortage, reset, and replay

**Work completed**
- Verified that accepted trades transfer resources between residents without creating additional food, wood, or coins.
- Verified that gathering reduces available resource stock and that depleted resources cannot be gathered.
- Added tests verifying that reset clears pending trade offers.
- Added a deterministic baseline replay test comparing simulation results after reset.
- Verified that trading safety checks reject invalid transfers.

**Test results**
- All 8 trading and simulation safety tests passed locally.

### CPU classifier-loading hook

**Work completed**
- Created `backend/app/classifier.py`.
- Implemented `InteractionClassifier` to load a locally exported Hugging Face classifier and tokenizer.
- Configured the model to run on CPU using evaluation mode.
- Added prediction functionality returning a label and confidence score.
- Used the existing `classifier_model_path` setting from `backend/app/config.py`.
- Integrated optional classifier loading into the FastAPI startup lifecycle in `backend/app/main.py`.
- Kept classifier inference separate from deterministic world and relationship rules.
- Added `backend/tests/test_classifier.py` to verify missing-model handling and prediction-before-loading errors.

**Test results**
- Both classifier safety tests passed.
- FastAPI started successfully without the trained classifier.
- Full local backend and ML test suite: **106 passed, 1 warning**.
- Fixed a classifier test import error discovered by GitHub Actions.
- GitHub Actions passed after the fix.

### CPU deployment and RAM measurements

**Work completed**
- Created `backend/requirements-classifier.txt` for optional classifier inference dependencies.
- Confirmed the project uses Python 3.12.
- Verified that the backend starts successfully using Uvicorn.
- Created `scripts/measure_classifier_ram.py` to measure process peak memory before and after classifier loading.

**Measurements**
- Backend import-time peak RAM: **52.81 MB**.
- RAM measurement script peak RAM without classifier: **36.25 MB**.
- Classifier-loaded RAM: **Not yet measured**.

The two recorded measurements were collected from different Python processes and should not be interpreted as a direct comparison.

Verified that the cached MiniLM embedding model loads successfully on CPU. Peak process RAM increased from **37.59 MB before loading** to **401.11 MB after loading**, an increase of **363.52 MB**. These measurements were collected locally on an Apple Silicon Mac and include supporting Python libraries.

Updated `backend/requirements-classifier.txt` to specify PyTorch 2.14.1 and Transformers 4.57.1 for classifier inference. Linux CPU compatibility and installation remain to be verified.

The trained DistilBERT classifier is not yet available locally, so classifier-loaded RAM and combined backend + MiniLM + classifier RAM have not been measured. No paid hosting service has been selected or approved.

### Remaining work
- Finalize CPU deployment packaging and platform-specific PyTorch dependencies.
- Obtain Gayatri's exported DistilBERT classifier after dataset review and training.
- Verify actual model loading and inference on CPU.
- Measure RAM with the classifier loaded.
- Complete final deployment integration checks.

### GitHub integration
- Pushed Day 5 trading implementation and safety tests.
- Pushed Day 6 CPU classifier-loading hook and additional simulation tests.
- Resolved a GitHub Actions import error.
- Latest confirmed passing CI commit: `50a79e2`.

## Summary

Completed Day 5 trading functionality and Day 6 simulation safety verification, implemented an optional CPU classifier-loading hook, and passed 106 local backend and ML tests. GitHub Actions is passing. CPU deployment packaging and trained-classifier memory measurements remain pending.