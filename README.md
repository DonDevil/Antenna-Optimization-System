AI-Driven Antenna Optimization System (Mode 2)

A complete AI-CST closed-loop framework for antenna design, optimization, simulation, and self-learning.
The system integrates:

Forward + inverse neural models for antenna parameter prediction

Lightweight optimizer for refinement

CST Studio Suite parametric model builder

S₁₁ extraction & performance evaluation

Automatic feedback logging

Autonomous self-learning retraining loop

UI built using Flet for interactive antenna design

1. Requirements
Python Version

This project requires:

Python 3.10  or  Python 3.11


(Recommended: Use a virtual environment.)

Install Dependencies

All required libraries are listed in requirements.txt.

Install them with:

pip install -r requirements.txt

2. Setting Up the Project
Clone the repository
git clone https://github.com/<your-repo>/antenna-optimization-ai.git
cd antenna-optimization-ai

Create a virtual environment
python -m venv .venv

Activate the environment

Windows:

.venv\Scripts\activate


Linux/macOS:

source .venv/bin/activate

Install dependencies
pip install -r requirements.txt

3. Project Structure (Overview)
ai_core/               → Core AI logic (forward/inverse models, optimizers)
cst_interface/         → CST geometry builders, command macros, S11 extraction
feedback/              → Feedback logger + incremental retraining
models/                → Saved Keras models + scalers
trainers/              → Scripts for training forward + inverse model families
ui/                    → Flet-based User Interface
dataset_generator/     → Synthetic dataset generator for Mode 2
automate.py            → Autonomous AI→CST→Feedback self-learning loop
utils.py               → Antenna math utilities
requirements.txt       → Required Python packages
README.md              → Documentation file

4. Running the Interactive UI (Flet)

The UI provides:

✔ Inverse AI prediction
✔ Parameter refinement
✔ CST simulation
✔ S11 extraction
✔ Automatic logging
✔ Quick retraining
✔ Dashboard & analytics

Run the UI
python ui/flet_ui_mode2.py


The Flet window will open and you can:

Select antenna family

Enter target frequency & bandwidth

Generate CST models

View real-time results

Run automatic feedback loop

View dashboard charts

5. Running the Autonomous Self-Learning System

The automate.py script makes the system continuously:

Generate random (Fr, BW) targets

Predict parameters (inverse model)

Refine using optimizer

Run CST simulation

Extract S11, real Fr & BW

Log feedback

Retrain quick model

Run automated learning
python automate.py


This will run continuously unless you stop it:

CTRL + C


To run a single cycle, edit:

RUNS = 1

6. Training the AI Models

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