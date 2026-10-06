# ReNexa

### Give Waste Its Next Life.

**AI-Powered Waste Recovery Intelligence System**

ReNexa is a software-based AI system that identifies household waste from images and provides practical recovery recommendations based on material, condition, safety, feasibility, and available recovery pathways.

---

## 1. ReNexa Workflow

```text
Image / Video
      ↓
Waste Detection
      ↓
Material & Condition Analysis
      ↓
Waste Profile
      ↓
Recovery Knowledge Base
      ↓
Constraint Checking
      ↓
Recovery Option Ranking
      ↓
Final Recommendation
      ↓
Tools + Materials + Step-by-Step Instructions
      ↓
Verified Tutorial
````

---

## 2. Current AI System

ReNexa uses multiple AI and data components for different tasks.

### Waste Detection

The current detection model is:

* YOLO26s
* 7 ReNexa waste classes

### ReNexa Waste Classes

| ID | Class     |
| -- | --------- |
| 0  | cardboard |
| 1  | glass     |
| 2  | metal     |
| 3  | organic   |
| 4  | other     |
| 5  | paper     |
| 6  | plastic   |

### Recovery Recommendation

The recovery recommendation layer uses a structured knowledge base containing:

* Waste item
* Material
* Object type
* Condition
* Recovery type
* Product
* Required tools
* Additional materials
* Required waste quantity
* Preparation
* Step-by-step instructions
* Safety level
* Adult supervision
* Feasibility
* Difficulty
* Skill level
* Tutorial information

The system checks the detected waste information against recovery pathways and constraints before ranking suitable recovery options.

---

## 3. Datasets

ReNexa uses multiple public datasets for different AI and data-processing tasks.

### Detection Datasets

The final YOLO detection dataset was created using:

* Asian Waste Detection Challenge
* TACO
* ZeroWaste-F

After cleaning, class mapping, invalid annotation removal, and duplicate handling, the final detection dataset contains:

**18,064 images**

### Classification / Supporting Datasets

The project also uses:

* TrashNet
* MMoRWaD

These datasets support waste classification and material/attribute-related analysis and are not blindly merged into the final YOLO detection dataset.

### Supporting Dataset

* MJU-Waste

MJU-Waste is used as a supporting waste localization/segmentation resource and is not directly merged into the final 7-class YOLO detection dataset because its local masks do not provide the same material-specific class structure required by the final detector.

---

## 4. Final Detection Dataset

The final processed detection dataset is intentionally **not stored in GitHub** because of its large size.

Expected local path:

```text
data/processed/renexa_detection_final/
```

Structure:

```text
renexa_detection_final/
│
├── train/
│   ├── images/
│   └── labels/
│
├── val/
│   ├── images/
│   └── labels/
│
├── test/
│   ├── images/
│   └── labels/
│
├── data.yaml
└── dataset_build_report.csv
```

The dataset contains:

* Training images
* Validation images
* Test images
* YOLO-format labels
* Dataset configuration
* Dataset build report

---

## 5. GitHub Repository

Large datasets and trained model files are intentionally excluded from the GitHub repository.

The repository contains:

* Application source code
* AI source code
* Training scripts
* Training notebooks
* Knowledge base
* Dataset reports
* Configuration files
* Documentation
* Tests

The following are intentionally not uploaded:

* Raw datasets
* Large processed training datasets
* `.pt` model files
* Training runs
* Virtual environments
* Environment secrets
* Runtime-generated JSON files

---

# 6. Local Setup

## Requirements

Recommended environment:

* Windows
* Python 3.11
* Git
* NVIDIA GPU for final YOLO training
* CUDA-compatible PyTorch
* Internet connection for initial package and pretrained-model setup

---

## 7. Clone the Repository

Replace the placeholder URL with the actual GitHub repository URL.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ReNexa
```

---

## 8. Create Virtual Environment

For Python 3.11:

```powershell
py -3.11 -m venv venv
```

Activate the environment:

```powershell
venv\Scripts\activate
```

---

## 9. Install PyTorch

For the final training laptop, install the appropriate CUDA-compatible PyTorch version according to the NVIDIA GPU and current PyTorch installation requirements.

After installation, verify GPU availability:

```python
import torch

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
```

Expected for the GPU training system:

```text
CUDA available: True
```

If CUDA is not available, do not start the final training because CPU training will be significantly slower.

---

## 10. Install ReNexa Dependencies

After installing the appropriate PyTorch build:

```powershell
pip install -r requirements.txt
```

Verify Ultralytics:

```powershell
yolo version
```

---

# 11. Add the Processed Dataset

The final processed dataset is transferred separately because it is too large for the normal GitHub repository.

Place the dataset at:

```text
ReNexa\data\processed\renexa_detection_final\
```

The final structure should be:

```text
ReNexa/
└── data/
    └── processed/
        └── renexa_detection_final/
            ├── train/
            ├── val/
            ├── test/
            ├── data.yaml
            └── dataset_build_report.csv
```

### Important

The raw datasets do **not** need to be transferred to the training laptop.

The preprocessing and dataset cleaning have already been completed on the development laptop.

The final processed detection dataset is sufficient for YOLO26 training.

---

# 12. Verify data.yaml

The file:

```text
data/processed/renexa_detection_final/data.yaml
```

should contain:

```yaml
path: .

train: train/images
val: val/images
test: test/images

names:
  0: cardboard
  1: glass
  2: metal
  3: organic
  4: other
  5: paper
  6: plastic
```

The relative path is intentional so that the dataset can be used on another computer without changing the absolute drive path.

---

# 13. YOLO26s Pretrained Model

The project uses the pretrained:

```text
yolo26s.pt
```

The model file is intentionally excluded from GitHub.

The training script loads:

```python
YOLO("yolo26s.pt")
```

If the pretrained model is not already available locally, Ultralytics can download it during the initial setup when an internet connection is available.

---

# 14. Final YOLO26s Training

The final training script is:

```text
training/train_yolo26.py
```

Run:

```powershell
python training/train_yolo26.py
```

The script automatically:

1. Detects the ReNexa project directory.
2. Locates the processed dataset.
3. Checks whether a GPU is available.
4. Loads YOLO26s.
5. Starts training.
6. Saves the training results.
7. Saves the best and last model weights.

---

## 15. Training Configuration

The current training configuration uses:

```text
Model: YOLO26s
Image size: 640
Epochs: 100
Batch size: 8
Workers: 4
Pretrained: Yes
```

The batch size can be reduced if the GPU does not have enough VRAM.

For example:

```text
batch=4
```

can be used if a CUDA out-of-memory error occurs.

---

# 16. Training Output

Training results are saved inside:

```text
training/runs/yolo26s_final/
```

The best trained model will be:

```text
training/runs/yolo26s_final/weights/best.pt
```

The final epoch model will be:

```text
training/runs/yolo26s_final/weights/last.pt
```

The `best.pt` model should be used for final evaluation and later ReNexa integration.

---

# 17. Model Evaluation

After training, the final model should be evaluated using the separate test dataset.

The final evaluation should report:

* Precision
* Recall
* mAP@50
* mAP@50-95
* F1-score
* Per-class performance
* Confusion matrix
* Precision-Recall curve

### Important

Accuracy is not the primary evaluation metric for object detection.

Precision, Recall, mAP, and F1-score provide more meaningful information for evaluating an object detector.

---

# 18. Development vs Training Workflow

## Development Laptop

The development laptop is used for:

```text
Raw Datasets
      ↓
Dataset Audit
      ↓
Data Cleaning
      ↓
Class Mapping
      ↓
Duplicate / Invalid Data Handling
      ↓
Final Processed Dataset
      ↓
Application Development
```

## GPU Training Laptop

The GPU laptop is used for:

```text
GitHub Repository
      +
Final Processed Dataset
      ↓
YOLO26s Training
      ↓
Model Evaluation
      ↓
best.pt
      ↓
ReNexa Model Integration
```

---

# 19. Knowledge Base

ReNexa's recovery knowledge is stored in:

```text
data/knowledge/
```

Important files include:

```text
recovery_projects.csv
recovery_projects_master.csv
recovery_projects_needs_verification.csv
recovery_pathways.csv
safety_rules.csv
video_index.csv
```

These files support the recovery recommendation and constraint-checking layer.

The knowledge base contains information related to:

* Materials
* Waste items
* Conditions
* Recovery methods
* Tools
* Additional materials
* Safety
* Feasibility
* Difficulty
* Step-by-step recovery instructions
* Tutorial references

---

# 20. Project Structure

```text
ReNexa/
│
├── ai/
│   ├── placeholder.py
│   └── waste_detector.py
│
├── app/
│   ├── main.py
│   ├── components/
│   └── pages/
│
├── assets/
│
├── database/
│
├── data/
│   ├── knowledge/
│   │   ├── recovery_projects.csv
│   │   ├── recovery_projects_master.csv
│   │   ├── recovery_projects_needs_verification.csv
│   │   ├── recovery_pathways.csv
│   │   ├── safety_rules.csv
│   │   └── video_index.csv
│   │
│   ├── raw/
│   │
│   ├── processed/
│   │   └── renexa_detection_final/
│   │
│   ├── runtime/
│   │
│   └── evaluation/
│
├── models/
│
├── services/
│
├── tests/
│
├── training/
│   ├── 01_dataset_audit_preprocessing.ipynb
│   ├── 02_build_clean_detection_dataset.ipynb
│   ├── 03_yolo26_training_setup.ipynb
│   └── train_yolo26.py
│
├── utils/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 21. Data and Model Management

The `.gitignore` configuration prevents large files from being uploaded to the normal GitHub repository.

Ignored files include:

```text
Raw datasets
Large processed datasets
*.pt
*.pth
*.onnx
Training runs
Virtual environments
.env files
Runtime-generated JSON files
```

This keeps the GitHub repository lightweight and suitable for source-code collaboration.

---

# 22. What Must Be Transferred to the GPU Laptop?

The GPU laptop does **not** need the raw datasets.

After cloning the repository, the main additional project data required for YOLO26 training is:

```text
data/processed/renexa_detection_final/
```

The repository already contains:

* Training script
* Training notebooks
* Dataset configuration
* Application code
* Knowledge base
* Dataset reports
* Requirements
* Git configuration

The pretrained YOLO26s model can be downloaded during setup if it is not already available.

---

# 23. Final Training Checklist

Before starting training:

```text
[ ] Python 3.11 installed
[ ] NVIDIA GPU available
[ ] CUDA-compatible PyTorch installed
[ ] torch.cuda.is_available() returns True
[ ] Git repository cloned
[ ] Virtual environment activated
[ ] requirements.txt installed
[ ] Final processed dataset copied
[ ] data.yaml verified
[ ] yolo26s.pt available or internet connection enabled
[ ] training/train_yolo26.py available
```

Start training:

```powershell
python training/train_yolo26.py
```

---

# 24. Current Project Status

```text
[x] Project structure
[x] Dataset collection
[x] Dataset audit
[x] Dataset cleaning
[x] Class mapping
[x] Final 7-class mapping
[x] Final detection dataset
[x] YOLO26 setup
[x] YOLO26 micro-test
[x] Final training script
[x] GitHub-ready project structure
[ ] Final GPU training
[ ] Final test evaluation
[ ] Final model integration
```

---

## ReNexa

**Give Waste Its Next Life.**

**AI-Powered Waste Recovery Intelligence System**

```
```
