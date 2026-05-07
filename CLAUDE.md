# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Rules

Before creating or editing any `.py` files, read `~\projects_nw\Claude\python\rules.md`. Key constraints for this repo:
- Type-hint all function signatures
- Use `pathlib.Path` over `os.path`
- Google-style docstrings
- Windows-first platform considerations

Note: pymeasure targets Python 3.8–3.12, so use `Optional[str]` instead of `str | None` and avoid Python 3.10+ syntax in library code.

## Commands

```bash
# Install in editable mode with test and doc dependencies
pip install -e .[tests,docs]

# Run all tests
pytest

# Run a single test file
pytest tests/test_procedure.py

# Run tests with coverage
pytest --cov=pymeasure --cov-report=xml

# Lint (checks for critical errors)
flake8 . --count --extend-select=E9,F63,F7,F82 --show-source --statistics

# Build docs
cd docs && make html SPHINXOPTS="-W --keep-going"

# Run doctests
cd docs && make doctest SPHINXOPTS="-W --keep-going"
```

Linting config (`.flake8`): max line length 100, max complexity 15.

## Architecture

PyMeasure has three independent but composable subsystems:

### 1. Instruments (`pymeasure/instruments/`)

100+ instrument driver classes organized by manufacturer. All inherit from `Instrument` (or `Instrument` + `SCPIMixin` for SCPI devices). The property system in `CommonBase` (`common_base.py`) is central:

- `Instrument.control(get_cmd, set_cmd, ...)` — bidirectional read/write property
- `Instrument.measurement(get_cmd, ...)` — read-only property
- `Instrument.setting(set_cmd, ...)` — write-only property

These property creators accept `validator`, `values`, `map_values`, `cast`, and `get_process` to handle the full VISA query→validate→cast→map pipeline in one declaration. Multi-channel instruments use `Channel` (`channel.py`) with `Instrument.channels`.

**Adapters** (`pymeasure/adapters/`) abstract the communication layer: `VISAAdapter` (default, PyVISA), `SerialAdapter`, `PrologixAdapter`, `TelnetAdapter`, `VXI11Adapter`.

### 2. Experiment Framework (`pymeasure/experiment/`)

- **`Procedure`** (`procedure.py`): Base class for experiments. Override `startup()`, `execute()`, `shutdown()`. Declare inputs as class-level `Parameter` instances and outputs via `DATA_COLUMNS`. Call `self.emit('results', data_dict)` and `self.emit('progress', pct)` inside `execute()`.
- **`Parameter` types** (`parameters.py`): `Parameter`, `IntegerParameter`, `FloatParameter`, `BooleanParameter`, `ListParameter`. Use `group_by`/`group_condition` for conditional visibility.
- **`Results`** (`results.py`): Manages CSV data files. Filename templates support `{Parameter Name}`, `{date}`, `{time}` placeholders.
- **`Worker`** (`workers.py`): Runs procedures in background threads.
- **`Sequencer`** (`sequencer.py`): Chains multiple procedures.

### 3. Display/GUI (`pymeasure/display/`)

Qt-based GUI system. `Qt.py` abstracts PyQt5/PySide2. The primary entry point is `ManagedWindow`:

```python
class MainWindow(ManagedWindow):
    def __init__(self):
        super().__init__(
            procedure_class=MyProcedure,
            inputs=['param1', 'param2'],   # procedure attributes to show as inputs
            displays=['param1', 'param2'],  # parameters shown in the experiment list
            x_axis='X Column',
            y_axis='Y Column',
        )
```

`Manager` (`manager.py`) handles the `ExperimentQueue` and coordinates `Worker` threads with GUI updates via `Listener` (`listeners.py`).

## Adding a New Instrument

1. Create `pymeasure/instruments/<manufacturer>/<model>.py`
2. Add class to `pymeasure/instruments/<manufacturer>/__init__.py`
3. Add to `pymeasure/instruments/__init__.py`
4. Add simulation YAML for tests if pyvisa-sim is used
5. Write tests in `tests/instruments/<manufacturer>/test_<model>.py`

See `docs/dev/adding_instruments/` for detailed property creator usage and testing patterns.

## Testing Instruments

Tests use `pyvisa-sim` for simulated VISA connections. Fixtures are in `tests/conftest.py`. GUI tests use `pytest-qt`.
