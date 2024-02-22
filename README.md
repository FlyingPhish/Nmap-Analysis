# Nmap Analysis Tool

This CLI python script is designed to be used by security consultants, IT admins and network engineers to do two things, compare two Nmap XML files to create a spreadsheet that compares IPs, ports and services between the files, and create a markdown report using GPT.

## Screenshots

![Introduction](images/tool.png)

![Snippet of Spreadsheet](images/spreadsheet.png)

![Spreadsheet Pie Chart](images/spreadsheet-pie.png)

![Sample GPT Report](images/gpt-report.png)
---
## Features

### Comprehensive Nmap XML Parsing

- **Multiple File Support**: Parse and analyze two Nmap XML output files.
- **Structured Data**: Converts Nmap's XML output into a structured format for further processing.

### Comparative Analysis

- **Change Detection**: Compare results from two Nmap scans to identify new, altered, or removed services and ports. Useful for when you scan the same IPs from different source IPs or over time.
- **Excel Reporting**: Automatically generates detailed Excel spreadsheets with the comparison results and some stats.

### Statistical Overview and Visualization

- **Network Exposure Statistics**: Offers statistical analysis on detected services and open ports.
- **Excel Visualizations**: Includes pie charts in Excel reports for a graphical representation of the network's security posture.

### AI-Powered Insights with GPT

- **GPT Report Generation**: Uses OpenAI's GPT to generate insightful analysis reports based on Nmap result stats. The tool uses a hardcoded prompt that sets the tone and requirements, then the script inserts the stats (no identifying information is provided) and if -c --context has been provided, it'll add the context to the bottom of the prompt.
- **Customizable Context**: Enhance GPT analysis by providing additional context, tailoring the report to specific needs.

## Installation and Setup

### Prerequisites

- 3.10+ probably (created using 3.12)
- An OpenAI API key for GPT report generation that is set in local env

### Secure Installation with `venv`

1. **Clone the Repository**:
```
git clone https://github.com/yourusername/nmap-analysis-tool.git
cd nmap-analysis-tool
```

2. **Create a Virtual Environment**:
```
python3 -m venv venv
```

3. **Activate the Virtual Environment**:

- On Windows:
```
.\venv\Scripts\activate
```

- On Unix or MacOS:
``` 
source venv/bin/activate
```

4. **Install Dependencies**:
``` 
pip install -r requirements.txt
```

### Alternative: Installation with `pipx`

**Install Nmap Analysis Tool with `pipx`**:

``` 
pipx install git+https://github.com/FlyingPhish/Nmap-Analysis.git
```

## Usage
The script prints the help page if no args are passed, or you can access with `python nmap-analysis.py -h`

- **Comparing Nmap Scans**:
```
python nmap-analysis.py compare -ff (--first-nmap-file) path/to/first.xml -lf (--last-nmap-file) path/to/second.xml
```

**Generating a GPT Report**:
``` 
python nmap-analysis.py gpt-report --gpt-nmap-file path/to/nmap.xml --context "Your optional context here"
```

## Contributing

Contributions are welcome! Whether it's adding new features, fixing bugs, or improving documentation, feel free to fork the repository and submit pull requests.

## License

This tool is available under a custom license that permits commercial use but requires any modifications, extensions, or derivative works to be open-sourced and contributed back to the original project. This ensures that the community benefits from improvements and that the tool evolves in a transparent and collaborative manner.

For detailed license terms, please see the LICENSE file in the repository.