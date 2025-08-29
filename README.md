# Thunder Muscle

Fast Thunderbird email dataset extraction and analysis using Gloda database.

## Setup

### Dependencies
```bash
# With virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Or system-wide
pip install -r requirements.txt
```

### Thunderbird Profile
You must ensure your Thunderbird profile is indexed.

1. Settings → Search "Indexing":
   1. [✓] *Enable Global Search and Indexer*
   2. *Message Store Type for new accounts* → Select *File per folder (mbox)*
2. Tools → Activity Manager - wait for indexing to complete
3. Copy Thunderbird's profile folder (e.g. ~/.thunderbird/) to a location of your choice
   ``` bash
   cp ~/.thunderbird/*.default-release assets/
   ```
   If you want to run directly on the in-situ profile on your computer, Thunderbird must be closed first.
4. Configure `config.yaml` with your profile name and preferences, if desired (see `config.example.yaml`)

## Usage

The main script to export the thunderbird profile as a dataset is `tm.py`, which also functions
as the API layer for other scripts.

### Data API (`tm.py`)
```bash
# Extract complete dataset
python3 tm.py extract [--output data/tb-profile.json]

# Filter emails by criteria
python3 tm.py filter tb-profile.json output.json --domain "*.edu" --year 2023

# Query by content pattern  
python3 tm.py query tb-profile.json output.json --pattern "unsubscribe"

# Show dataset statistics
python3 tm.py stats tb-profile.json
```

### Domain Analysis (`analyze_domains.py`)
```bash
# Analyze domains producing emails with specific patterns
python3 analyze_domains.py dataset.json compare_domain --pattern "unsubscribe"
```

## Output Formats

All commands support `--format json|csv|yaml`. Default format configured in `config.yaml`.

## Performance

Since the tool uses direct "Gloda" (**Glo**bal **Da**tabase) access, the JSON extraction takes roughly 2 seconds to extract 35K emails on a 2015 netbook.

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
