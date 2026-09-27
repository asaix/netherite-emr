# 🕐 Temporal Reasoning Dataset (TRD)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Paper: IWSDS 2026](https://img.shields.io/badge/paper-IWSDS%202026-b31b1b.svg)](https://aclanthology.org/2026.iwsds-1.19.pdf)

> 🔬 **Replication Package** for the paper:  
> **["Benchmarking Multilingual Temporal Reasoning in LLMs: The Temporal Reasoning Dataset"](https://aclanthology.org/2026.iwsds-1.19.pdf)**  
> *Presented at IWSDS 2026*

> ⚠️ **Academic Release Notice**  
> This code is being released solely for academic and scientific reproducibility purposes, in support of the methods and findings described in the associated publication. Pull requests are not being accepted in order to maintain the code exactly as it was used in the paper.

A programmatically generated, multilingual benchmark designed to evaluate temporal reasoning capabilities in Large Language Models (LLMs). This package allows you to **reproduce the dataset** used in our research with a single command.

---

## 📖 Overview

TRD generates question-answer pairs across **10 languages** and **9 temporal task types**, enabling systematic evaluation of LLM temporal reasoning through 4 experimental axes:

| Experiment | Description | Default Samples |
|------------|-------------|-----------------|
| 🔄 **Variations** | Medium difficulty baseline across all task types | 9,000 |
| 📈 **Difficulties** | 5 difficulty levels (short to very_very_long) | 45,000 |
| 🎯 **Insertions** | Contextual distractors (similar/dissimilar) | 18,000 |
| 🧠 **Memorization** | Temporal shift 2025-2095 (8 year epochs) | 32,000 |

**📊 Total: 104,000 samples** with default settings (seed=9 for reproducibility).

---

## 🌍 Supported Languages

Our dataset spans **10 languages** across multiple language families to ensure comprehensive multilingual evaluation:

| Code | Language | Family |
|------|----------|--------|
| 🇺🇸 `en_US` | English | Indo-European (Germanic) |
| 🇪🇸 `es_ES` | Spanish | Indo-European (Romance) |
| 🇩🇪 `de_DE` | German | Indo-European (Germanic) |
| 🇫🇷 `fr_FR` | French | Indo-European (Romance) |
| 🇮🇹 `it_IT` | Italian | Indo-European (Romance) |
| 🇧🇷 `pt_BR` | Portuguese | Indo-European (Romance) |
| 🇳🇱 `nl_NL` | Dutch | Indo-European (Germanic) |
| 🇯🇵 `ja_JP` | Japanese | Japonic |
| 🇸🇦 `ar_SA` | Arabic | Afro-Asiatic |
| 🇮🇳 `hi_IN` | Hindi | Indo-European (Indo-Aryan) |

---

## 📋 Task Types

Nine carefully designed temporal reasoning tasks:

| # | Task | Description |
|---|------|-------------|
| 1️⃣ | **date_addition** | Adding days/weeks/months/years to a date |
| 2️⃣ | **date_subtraction** | Subtracting days/weeks/months/years from a date |
| 3️⃣ | **time_addition** | Adding hours/minutes to a time |
| 4️⃣ | **time_subtraction** | Subtracting hours/minutes from a time |
| 5️⃣ | **date_duration** | Days between two dates |
| 6️⃣ | **time_duration** | Hours/minutes between two times |
| 7️⃣ | **date_recurrence** | Next occurrence of recurring events |
| 8️⃣ | **interval_date** | Date intervals and ranges |
| 9️⃣ | **day_of_week** | Day name for a given date |

---

## 🚀 Installation

```bash
pip install trd
```

Or install from source:

```bash
git clone https://github.com/amazon-science/temporal-reasoning-dataset.git
cd temporal-reasoning-dataset
pip install -e .
```

---

## ⚡ Quick Start

### 🔁 Reproduce Paper Results

To generate the **exact dataset** used in our IWSDS 2026 paper:

```bash
trd generate all --output ./dataset --seed 9
```

This creates all 104,000 samples organized by experiment type.

### 💻 Command Line Interface

```bash
# Generate all experiments (104K samples)
trd generate all --output ./dataset

# Generate specific experiments
trd generate variations --output ./dataset
trd generate difficulties --output ./dataset
trd generate insertions --output ./dataset
trd generate memorization --output ./dataset

# Customize generation
trd generate variations \
    --samples 50 \
    --languages en_US,de_DE,ja_JP \
    --format json \
    --seed 42 \
    --output ./my_dataset
```

### 🐍 Python API

```python
from trd import generate_all, generate_variations

# Generate complete dataset (reproduces paper results)
total = generate_all(output_dir="./dataset", seed=9)
print(f"✅ Generated {total} samples")

# Generate specific experiment
total = generate_variations(
    samples_per_task=100,
    languages=["en_US", "de_DE", "ja_JP"],
    output_dir="./dataset",
    seed=9,
    format="csv"
)

# Use experiment classes directly
from trd import VariationsExperiment
from trd.config.languages import LANGUAGE_CODES

exp = VariationsExperiment(
    samples_per_task=100,
    languages=LANGUAGE_CODES,
    output_dir="./dataset",
    seed=9
)
exp.generate()
```

### 🔧 Using Individual Generators

```python
from trd.generators import get_generator
from trd.config import MEDIUM_TIMEFRAME

# Get a specific generator
GeneratorClass = get_generator("date_addition")
generator = GeneratorClass(MEDIUM_TIMEFRAME, "en_US")

# Generate samples
samples = generator.generate_samples(10)

for sample in samples:
    print(f"❓ Q: {sample.question}")
    print(f"✅ A: {sample.answer}")
    print()
```

---

## 📁 Output Format

### CSV Format (default)

Each experiment generates CSV files organized by task and language:

```
dataset/
├── variations/
│   ├── date_addition_medium_en_US.csv
│   ├── date_addition_medium_es_ES.csv
│   └── ...
├── difficulties/
│   ├── short/
│   ├── medium/
│   ├── long/
│   ├── very_long/
│   └── very_very_long/
├── insertions/
│   ├── similar/
│   └── dissimilar/
└── memorization/
    ├── 2025_date_addition_medium_en_US.csv
    ├── 2035_date_addition_medium_en_US.csv
    └── ...
```

### JSON Format

```json
{
  "metadata": {
    "experiment": "variations",
    "generated_at": "2025-01-15T12:00:00",
    "seed": 9,
    "total_samples": 9000
  },
  "samples": [
    {
      "id": "var_en_US_date_addition_001",
      "language": "en_US",
      "task_type": "date_addition",
      "question": "Today is 2027-08-07, what is the date going to be in 8 days?",
      "answer": "2027-08-15"
    }
  ]
}
```

---

## 📊 Difficulty Levels (Table 5)

Each difficulty level uses specific timeframe configurations from the paper:

| Level | Days | Hours | Recurrence Every | Recurrence Q | Duration Date | Duration Time (min) | Year Range |
|-------|------|-------|------------------|--------------|---------------|---------------------|------------|
| 🟢 short | 1-4 | 1-4 | 1-4 | 1-2 | 1-4 | 1-60 | 2025 |
| 🟡 medium | 4-8 | 4-8 | 4-8 | 2-4 | 4-8 | 60-120 | 2025-2028 |
| 🟠 long | 8-16 | 8-16 | 8-16 | 4-8 | 8-16 | 120-240 | 2025-2030 |
| 🔴 very_long | 16-32 | 16-32 | 16-32 | 8-16 | 16-32 | 240-480 | 2025-2033 |
| ⚫ very_very_long | 32-64 | 32-64 | 32-64 | 16-32 | 32-64 | 480-960 | 2025-2036 |


---

## 📜 Citation

If you use this dataset in your research, please cite our paper ([PDF](https://aclanthology.org/2026.iwsds-1.19.pdf)):

```bibtex
@inproceedings{mazzia2026trd,
  title={Benchmarking Multilingual Temporal Reasoning in LLMs: The Temporal Reasoning Dataset},
  author={Mazzia, Vittorio and Pollastrini, Sandro and Bernardi, Davide and Rubagotti, Chiara and Amberti, Daniele},
  booktitle={Proceedings of the 16th International Workshop on Spoken Dialogue Systems (IWSDS)},
  year={2026},
  organization={Amazon},
  url={https://aclanthology.org/2026.iwsds-1.19.pdf}
}
```

---

## 🏗️ Project Structure

```
trd/
├── __init__.py          # Main package API
├── cli.py               # Click CLI
├── config/              # Configuration
│   ├── timeframes.py    # TimeframeConfig dataclass
│   ├── languages.py     # Supported languages
│   └── defaults.py      # Difficulty level configs
├── templates/           # Language templates
│   ├── questions.py     # Question templates (10 languages x 9 tasks)
│   ├── plurals.py       # Pluralization rules
│   └── insertions.py    # Insertion templates (multilingual)
├── generators/          # Sample generators
│   ├── base.py          # BaseGenerator ABC
│   ├── date_arithmetic.py
│   ├── time_arithmetic.py
│   ├── duration.py
│   ├── recurrence.py
│   ├── interval.py
│   └── day_of_week.py
├── experiments/         # Experiment orchestrators
│   ├── base.py          # BaseExperiment ABC
│   ├── variations.py
│   ├── difficulties.py
│   ├── insertions.py
│   └── memorization.py
└── utils/               # Utilities
    ├── io.py            # CSV/JSON I/O
    └── locale.py        # Day name localization
```

---

## 📧 Contact

For questions about this dataset or the paper, please open an issue on GitHub or contact the corresponding authors.

---
