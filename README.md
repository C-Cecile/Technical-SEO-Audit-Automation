# Technical SEO Audit Automation Suite

A comprehensive system for automating technical SEO audits from Screaming Frog crawls to prioritized recommendations.

## Features

- **Full End-to-End Automation** - From crawling to reporting in one workflow
- **Prioritized Issue Detection** - Issues categorized by impact and effort
- **Multiple Export Formats** - HTML, JSON, Excel and visual charts
- **Email Integration** - Automatically send reports to stakeholders
- **Screaming Frog Integration** - Automate crawls using CLI or API

## System Requirements

### Core Requirements
- Python 3.7+
- Screaming Frog SEO Spider (free version works with CLI, API requires license)

### Python Dependencies
```
pandas>=1.2.0
numpy>=1.19.0
matplotlib>=3.3.0
xlsxwriter>=1.3.0
requests>=2.25.0
```

## Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/technical-seo-audit-automation.git
cd technical-seo-audit-automation
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Make sure Screaming Frog is installed on your system

## Project Structure

```
technical-seo-audit-automation/
├── seo_audit_automation.py      # Core SEO audit functionality
├── workflow.py                  # SEO audit workflow
├── screaming_frog_automation.py # SF CLI automation
├── screaming_frog_api.py        # SF API automation
├── full_workflow.py             # End-to-end workflow
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── projects/                    # Generated project folders
│   └── domain_timestamp/        # One folder per audit
│       ├── exports/             # Screaming Frog exports
│       └── reports/             # Generated reports
└── templates/                   # Report templates
```

## Usage

### Quick Start (Using CLI)

The simplest way to run a complete audit is:

```bash
python full_workflow.py --domain example.com --crawl-url https://example.com
```

This will:
1. Crawl the website using Screaming Frog
2. Process the exports
3. Generate prioritized reports
4. Save all outputs to a timestamped project folder

### Using Pre-exported Data

If you already have Screaming Frog exports:

```bash
python workflow.py --domain example.com --exports_path /path/to/exports
```

### Advanced Options

```bash
python full_workflow.py --domain example.com \
  --crawl-url https://example.com \
  --max-urls 1000 \
  --config-file /path/to/screaming_frog_config.seospiderconfig \
  --send-email \
  --email-recipients client@example.com,manager@agency.com \
  --smtp-server smtp.gmail.com \
  --smtp-port 587 \
  --smtp-user your-email@gmail.com \
  --smtp-password your-password
```

## Automating Screaming Frog

### Using the Command Line Interface (CLI)

The CLI integration works with both free and licensed versions:

```python
from screaming_frog_automation import ScreamingFrogAutomation

# Initialize
sf = ScreamingFrogAutomation()

# Run crawl with specific exports
sf.run_crawl_with_exports(
    url="https://example.com",
    output_dir="./exports/example_com",
    export_tabs=["Internal:All", "Response Codes", "Page Titles"]
)
```

### Using the API (Licensed Version Only)

The API integration requires a licensed version of Screaming Frog:

```python
from screaming_frog_api import ScreamingFrogAPI

# Initialize
sf_api = ScreamingFrogAPI()

# Make sure SF is running with API enabled
if sf_api.check_status():
    # Run full crawl and export workflow
    sf_api.run_full_crawl_and_export(
        url="https://example.com",
        output_dir="./exports/example_com_api",
        max_urls=1000
    )
```

## Setting Up Scheduled Audits

You can set up scheduled audits using cron (Linux/Mac) or Task Scheduler (Windows).

### Example Cron Job (Linux/Mac)

```bash
# Run weekly audit every Monday at 2am
0 2 * * 1 /usr/bin/python3 /path/to/full_workflow.py --domain example.com --crawl-url https://example.com --send-email --email-recipients team@example.com --smtp-server smtp.example.com --smtp-user user --smtp-password pass >> /path/to/logs/audit.log 2>&1
```

### Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger (e.g., weekly on Monday)
4. Action: Start a program
5. Program/script: `C:\Path\to\Python\python.exe`
6. Arguments: `C:\Path\to\full_workflow.py --domain example.com --crawl-url https://example.com`

## Issue Detection

The system can detect and prioritize numerous technical SEO issues, including:

### Critical Issues
- Broken links (4xx errors)
- Server errors (5xx errors)
- Redirect chains
- Duplicate page titles

### High Priority Issues
- Missing meta descriptions
- Missing H1 tags
- Slow-loading pages
- Duplicate content

### Medium Priority Issues
- Title tags that are too long
- Meta descriptions that are too long
- Low word count pages
- Missing alt text on images

### Low Priority Issues
- Multiple H1 tags
- Missing meta keywords
- Excessive outlinks
- Low text-to-HTML ratio

## Report Formats

The system generates several report formats:

1. **HTML Report** - Interactive, visually appealing format ideal for presentations
2. **Excel Report** - Detailed data with separate sheets for each issue category
3. **JSON Report** - Machine-readable format for further processing
4. **Visual Charts** - Summary charts showing issues by category and priority

## Customization

### Adjusting Issue Priorities

You can customize the impact and effort scores for different issues by modifying the `ISSUE_SCORES` dictionary in `seo_audit_automation.py`:

```python
ISSUE_SCORES = {
    "broken_links": {"impact": 10, "effort": 5, "category": "critical"},
    "missing_meta_descriptions": {"impact": 7, "effort": 2, "category": "high"},
    # Add or modify issues here
}
```

### Adding New Issue Types

To add new issue types:

1. Add the issue definition to the `ISSUE_SCORES` dictionary
2. Create a new analysis method in the `SEOAuditAutomation` class
3. Call your new method from the `run_analysis` method

## Enabling the Screaming Frog API

To use the API integration (licensed version only):

1. Open Screaming Frog SEO Spider
2. Go to Configuration > API
3. Check "Enable API"
4. Make sure the port is set to 8777 (default)
5. Keep Screaming Frog running when using the API integration

## Troubleshooting

### Common Issues

**Issue:** "Screaming Frog executable not found"  
**Solution:** Specify the path to the SF executable with `--sf-path`

**Issue:** "No exports were created. Crawl may have failed."  
**Solution:** Check your Screaming Frog configuration and make sure it has permission to crawl the site

**Issue:** "Screaming Frog API is not running or not accessible"  
**Solution:** Make sure Screaming Frog is running and the API is enabled (Configuration > API)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE).

## Acknowledgments

- This project uses [Screaming Frog SEO Spider](https://www.screamingfrog.co.uk/seo-spider/) for web crawling
- Thanks to all contributors and users for suggestions and feedback
