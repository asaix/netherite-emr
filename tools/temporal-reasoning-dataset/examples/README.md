# TRD Examples

This directory contains example scripts demonstrating how to use the Temporal Reasoning Dataset (TRD) package.

## Examples

### basic_usage.py

Basic usage example showing how to:
- Generate the variations experiment
- Generate the complete dataset
- Generate for specific languages only
- Use different output formats (CSV, JSON)

```bash
python examples/basic_usage.py
```

### custom_generators.py

Advanced example showing how to:
- Use individual generators directly
- List available generators
- Apply different difficulty levels
- Create custom timeframe configurations
- Generate samples for different languages

```bash
python examples/custom_generators.py
```

## CLI Examples

### Generate all experiments

```bash
# Default settings (104K samples, seed=9)
trd generate all --output ./dataset

# With custom settings
trd generate all --samples 50 --seed 42 --format json --output ./dataset
```

### Generate specific experiments

```bash
# Variations (9K samples with defaults)
trd generate variations --output ./dataset

# Difficulties (45K samples with defaults)
trd generate difficulties --output ./dataset

# Insertions (18K samples with defaults)
trd generate insertions --output ./dataset

# Memorization (32K samples with defaults)
trd generate memorization --output ./dataset
```

### Generate for specific languages

```bash
trd generate variations --languages en_US,de_DE,ja_JP --output ./dataset
```

### Show available options

```bash
trd --help
trd generate --help
trd generate variations --help
