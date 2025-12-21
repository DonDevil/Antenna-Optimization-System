# AI-Driven Antenna Optimization System (Mode 2)

This project implements an AI-assisted closed-loop antenna design and optimization framework integrated with CST Studio Suite.
It combines machine learning surrogate models, inverse parameter prediction, CST-based electromagnetic simulation, and online correction learning to iteratively improve antenna designs toward specified electrical targets.

The system supports both interactive UI-based usage and fully autonomous overnight training.

## How the System Works

The project is built around a closed-loop learning pipeline:

#### Target Specification
+ The user (or automation script) specifies:

+ Desired resonant frequency (GHz)

+ Desired bandwidth (MHz)

+ Antenna family (e.g., rectangular patch, monopole, dipole)

#### Inverse AI Prediction
+ A trained inverse neural network (ANN) predicts initial antenna geometry parameters that should meet the target specifications.

#### Parameter Engine (Core Logic)
All parameter generation flows through a unified ParameterEngine, which:

 * Uses the inverse ANN as prior knowledge

 * Applies learned correction from past CST simulations

 * Introduces controlled exploration to avoid stagnation

 + Enforces safe parameter bounds for CST stability

#### CST Simulation
The generated parameters are passed to CST Studio Suite, which:

+ Builds the antenna geometry

+ Runs a frequency sweep

+ Extracts S₁₁, resonant frequency, and bandwidth

+ Feedback Logging
CST results are logged as feedback, capturing:

+ Target specifications

+ Parameters actually used

+ Actual CST results

#### Online Correction Learning
+ A lightweight neural model is periodically retrained to learn parameter correction deltas, improving future predictions without retraining the main models.

+ This loop enables the system to improve over time for similar design targets.

## Project Structure Overview
```
ai_core/
├── ai_core_manager.py        # Loads and manages forward/inverse ANN models
├── ai_config.py              # Global configuration and parameter ranges
├── parameter_engine.py       # Unified parameter prediction & correction logic

cst_interface/
├── cst_driver.py             # CST macro execution and S-parameter extraction
├── cst_driver_mode2.py       # Family-specific antenna geometry builders
├── database/
│   ├── commands.json
│   └── material_library.json

feedback/
├── ai_feedback_mode2.csv     # Logged CST feedback (generated at runtime)
├── ai_quick_retrain.py       # Online correction model trainer
├── ai_quick_retrain.save     # Trained correction model (generated)

models/
├── forward_*.keras           # Forward ANN models (per antenna family)
├── inverse_*.keras           # Inverse ANN models (per antenna family)
├── *_scaler.save             # Feature scalers

trainers/
├── train_forward_family.py   # Train forward ANN models
├── train_inverse_family.py   # Train inverse ANN models

ui/
├── flet_ui_mode2.py          # Interactive UI (Flet-based)

automate.py                   # Fully autonomous training loop
dataset_generator_mode2.py    # Synthetic dataset generator
dataset_mode2.csv             # Generated training dataset
utils.py                      # Antenna-related math utilities
requirements.txt              # Python dependencies
```
## Installation Guide
#### Prerequisites

+ Python: 3.10 or 3.11

+ CST Studio Suite (installed and licensed)

+ CST Python Interface available in your environment

+ Windows OS recommended (CST dependency)

#### Clone the Repository
    git clone https://github.com/<your-username>/ai-antenna-optimization.git
    cd ai-antenna-optimization

#### Create and Activate Virtual Environment
    python -m venv .venv
    .venv\Scripts\activate

#### Install Dependencies
    pip install -r requirements.txt

#### Configure CST Output Path

Edit the following file:

    ai_core/ai_config.py

Set the correct CST project output path:

    ANTENNA_PATH = r"E:\Your\CST\Output\antenna.cst"


Ensure this path is writable by CST.

## Training the AI Models (Required First)
#### Step 1: Generate Synthetic Dataset

This generates physics-based antenna samples used for training.

    python dataset_generator_mode2.py
Output:

    dataset_mode2.csv
#### Step 2: Train Forward Models

Forward models predict electrical performance from geometry.

    python trainers/train_forward_family.py
Generated:

    models/forward_*.keras

    models/forward_*_scaler.save
#### Step 3: Train Inverse Models

Inverse models predict geometry from target specifications.

    python trainers/train_inverse_family.py
Generated:

    models/inverse_*.keras

    models/inverse_*_scalerX.save

    models/inverse_*_scalerY.save
## Interactive Usage (UI Mode)

The UI allows manual antenna design and CST simulation.

    python ui/flet_ui_mode2.py
#### Features:

+ Select antenna family

+ Enter target frequency and bandwidth

+ Generate CST models

+ View real-time results

+ Automatic feedback logging

+ Online correction learning

## Autonomous Training (Recommended for Fine-Tuning)

For large-scale learning and overnight improvement, use automation.

Run Autonomous Learning Loop

    python automate.py
What happens:

+ Random targets are generated

+ Parameters are predicted using ParameterEngine

+ CST simulations are executed

+ Feedback is logged

+ Correction model retrains periodically

+ System improves over time

Stop anytime using:

    CTRL + C

## Current Capabilities and Limitations 
#### Capabilities

+ Multi-family antenna support

+ CST-integrated simulation loop

+ Online correction learning

Training scripts are in:

trainers/


Before training, ensure:

You have a valid dataset at dataset_mode2.csv

You have generated synthetic data using dataset_generator_mode2.py (if needed)

Generate Mode-2 Dataset
python dataset_generator_mode2.py

Train Forward Models
python trainers/train_forward_family.py

Train Inverse Models
python trainers/train_inverse_family.py


Models and scalers will be saved in the models/ directory:

models/
    forward_*.keras
    forward_*_scaler.save
    inverse_*.keras
    inverse_*_scalerX.save
    inverse_*_scalerY.save

7. Quick Retrain (Online Learning)

Each CST simulation logs:

Target Fr, BW

Predicted parameters

Actual CST results

S11 (dB)

These are written to:

feedback/ai_feedback_mode2.csv


The incremental retraining script runs automatically,
but you can run it manually:

python feedback/ai_quick_retrain.py


This trains a correction model that improves performance without retraining the full neural networks.

8. CST Integration Notes

The CST driver requires:

CST Studio Suite installed

Python CST interface available

Correct path set for the antenna output:

Defined in:

ai_core/ai_config.py
ANTENNA_PATH = r"...\cst_interface\output\antenna.cst"


The CST pipeline automatically:

Builds geometry

Applies materials

Defines ports

Runs frequency sweep

Extracts S₁₁

Determines Fr_actual & BW_actual

9. Dashboard & Analytics

Inside the UI:

python ui/flet_ui_mode2.py


Click "Show Dashboard" to view:

Frequency error trend

Bandwidth error trend

Histogram of prediction errors

Summary statistics

This uses the logged feedback file.

10. Contributing

If you want to extend or fix functionality:

Create a new branch

Commit changes with meaningful messages

Open a pull request

11. Known Limitations / To-Do

CPW, U-Slot, E-Shape, Vivaldi geometry are placeholders

Full CST parameter extraction may require refinement

Forward/inverse models can be enhanced with more training data

Add multi-objective optimization (Fr, BW, S11, Gain)

More visual analytics for model drift detection

12. License

MIT License (recommended; change if required).