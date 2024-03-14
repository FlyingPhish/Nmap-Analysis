#!.venv/bin/python3

import argparse
import os
import re
import xml.etree.ElementTree as ET
import subprocess
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.chart import PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Tuple

load_dotenv()

def obligatory_banner():
    ascii_art = """
 ███▄    █  ███▄ ▄███▓ ▄▄▄       ██▓███      ▄▄▄      ███▄    █  ▄▄▄       ██▓   ▓██   ██▓  ██████  ██▓  ██████ 
 ██ ▀█   █ ▓██▒▀█▀ ██▒▒████▄    ▓██░  ██▒   ▒████▄    ██ ▀█   █ ▒████▄    ▓██▒    ▒██  ██▒▒██    ▒ ▓██▒▒██    ▒ 
▓██  ▀█ ██▒▓██    ▓██░▒██  ▀█▄  ▓██░ ██▓▒   ▒██  ▀█▄ ▓██  ▀█ ██▒▒██  ▀█▄  ▒██░     ▒██ ██░░ ▓██▄   ▒██▒░ ▓██▄   
▓██▒  ▐▌██▒▒██    ▒██ ░██▄▄▄▄██ ▒██▄█▓▒ ▒   ░██▄▄▄▄██▓██▒  ▐▌██▒░██▄▄▄▄██ ▒██░     ░ ▐██▓░  ▒   ██▒░██░  ▒   ██▒
▒██░   ▓██░▒██▒   ░██▒ ▓█   ▓██▒▒██▒ ░  ░    ▓█   ▓██▒██░   ▓██░ ▓█   ▓██▒░██████▒ ░ ██▒▓░▒██████▒▒░██░▒██████▒▒
░ ▒░   ▒ ▒ ░ ▒░   ░  ░ ▒▒   ▓▒█░▒▓▒░ ░  ░    ▒▒   ▓▒█░ ▒░   ▒ ▒  ▒▒   ▓▒█░░ ▒░▓  ░  ██▒▒▒ ▒ ▒▓▒ ▒ ░░▓  ▒ ▒▓▒ ▒ ░
░ ░░   ░ ▒░░  ░      ░  ▒   ▒▒ ░░▒ ░          ▒   ▒▒ ░ ░░   ░ ▒░  ▒   ▒▒ ░░ ░ ▒  ░▓██ ░▒░ ░ ░▒  ░ ░ ▒ ░░ ░▒  ░ ░
   ░   ░ ░ ░      ░     ░   ▒   ░░            ░   ▒     ░   ░ ░   ░   ▒     ░ ░   ▒ ▒ ░░  ░  ░  ░   ▒ ░░  ░  ░  
         ░        ░         ░  ░                  ░  ░        ░       ░  ░    ░  ░░ ░           ░   ░        ░  
                                                                                  ░ ░                           
by @FlyingPhishy
    """
    print(ascii_art)

def validate_file(file_path: str) -> bool:
    return os.path.exists(file_path) and file_path.endswith('.xml')

def parse_nmap_xml(file_path: str) -> Dict[str, List[Tuple[str, str]]]:
    ip_ports_services = {}
    tree = ET.parse(file_path)
    root = tree.getroot()
    for host in root.findall('host'):
        ip_address = host.find("address").attrib['addr']
        ports_services = []
        for port in host.findall(".//port"):
            if port.find('state').attrib['state'] == 'open':
                port_id_protocol = f"{port.attrib['portid']}/{port.attrib['protocol'].upper()}"
                service = port.find('service')
                service_name = service.attrib['name'].upper() if service is not None else 'UNKNOWN'
                ports_services.append((port_id_protocol, service_name))
        ip_ports_services[ip_address] = ports_services
    return ip_ports_services

def merge_detailed_data(data1, data2):
    """
    Merge detailed data from two Nmap XML parsing results.
    
    Args:
        data1, data2: The detailed data structures from each of the two Nmap XML files.
        
    Returns:
        Dict: A merged detailed data structure.
    """
    merged_data = data1.copy()  # Start with a copy of the first file's data.

    for ip, ports_services in data2.items():
        if ip in merged_data:
            # Combine unique port/service tuples for the same IP
            merged_data[ip] = list(set(merged_data[ip] + ports_services))
        else:
            merged_data[ip] = ports_services
    
    return merged_data

def compare_ports(file1_data: Dict[str, List[Tuple[str, str]]], file2_data: Dict[str, List[Tuple[str, str]]]) -> List[Tuple[str, str, str, str, str, str]]:
    """Compare open ports and services of the same IP addresses in both files and identify differences."""
    compared_data = []
    all_ips = set(file1_data.keys()) | set(file2_data.keys())
    for ip in all_ips:
        file1_ports = {port_service[0]: port_service for port_service in file1_data.get(ip, [])}
        file2_ports = {port_service[0]: port_service for port_service in file2_data.get(ip, [])}
        all_ports = set(file1_ports.keys()) | set(file2_ports.keys())
        
        for port in all_ports:
            port1, service1 = file1_ports.get(port, ('N/A', 'N/A'))
            port2, service2 = file2_ports.get(port, ('N/A', 'N/A'))
            differences = 'Yes' if (port1, service1) != (port2, service2) else 'No'
            compared_data.append((ip, port1, service1, port2, service2, differences))
    return compared_data

def calculate_statistics(ip_ports_services: Dict[str, List[Tuple[str, str]]]):
    """
    Calculate statistics based on parsed Nmap XML data.
    
    Args:
        ip_ports_services (Dict): Output from parse_nmap_xml containing IPs with their open ports and services.
    
    Returns:
        Dict: A dictionary containing various statistics such as counts of unique IPs with specific services,
              and counts of open ports across all IPs.
    """
    service_counts = {}  # Tracks counts of each service across all IPs
    port_counts = {}  # Tracks counts of each port across all IPs
    total_ips = len(ip_ports_services)

    for ip, ports_services in ip_ports_services.items():
        for port_service in ports_services:
            port, service = port_service
            # Increment service count
            if service not in service_counts:
                service_counts[service] = {"count": 1, "ips": set([ip])}
            else:
                service_counts[service]["count"] += 1
                service_counts[service]["ips"].add(ip)
            
            # Increment port count
            if port not in port_counts:
                port_counts[port] = 1
            else:
                port_counts[port] += 1
    
    # Convert IP sets to counts for services
    for service in service_counts:
        service_counts[service]["ips"] = len(service_counts[service]["ips"])
    
    stats = {
        "service_counts": service_counts,
        "port_counts": port_counts,
        "total_ips": total_ips
    }

    return stats

def generate_xlsx_report_final(data: List[Tuple[str, str, str, str, str, str]], file1_path: str, file2_path: str, stats):
    filename1 = os.path.splitext(os.path.basename(file1_path))[0]
    filename2 = os.path.splitext(os.path.basename(file2_path))[0]
    output_file = f"Nmap_Comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Scan Comparison"
    ws.append(['IP Address', f'{filename1} - Port/Protocol', f'{filename1} - Service', f'{filename2} - Port/Protocol', f'{filename2} - Service', 'Differences'])

    for row in data:
        ws.append(row)
    wb.save(output_file)

    # Create a new sheet for statistics
    stats_sheet = wb.create_sheet(title="Statistics")

    stat_row = 1
    for service, detail in stats["service_counts"].items():
        stats_sheet.append([service, detail["count"]])
        stat_row += 1

    data = Reference(stats_sheet, min_col=2, min_row=1, max_row=stat_row)
    categories = Reference(stats_sheet, min_col=1, min_row=1, max_row=stat_row)

    chart = PieChart()
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.title = "Service Distribution"
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showPercent = True  # Show percentages on the pie chart

    stats_sheet.add_chart(chart, f"E4")
    wb.save(output_file)

def create_markdown_table(ip_ports_services: Dict[str, List[Tuple[str, str]]]) -> str:
    """Create a Markdown table from the parsed Nmap data."""
    markdown_table = "IP Address | Port/Protocol | Service\n--- | --- | ---\n"
    for ip, ports_services in ip_ports_services.items():
        for port, service in ports_services:
            markdown_table += f"{ip} | {port} | {service}\n"
    return markdown_table

def format_stats_for_gpt(stats):
    """Format statistics into a bullet-point list for GPT prompt."""
    lines = []
    # Format port and service counts
    for service, data in stats["service_counts"].items():
        lines.append(f"- {data['count']}x IPs had {service} open")

    # Format total counts
    lines.append("\nOverall statistics:")
    for port, count in stats["port_counts"].items():
        lines.append(f"- {count}/{stats['total_ips']} Ports were {port}")

    return "\n".join(lines)

def generate_gpt_report(nmap_data: Dict[str, List[Tuple[str, str]]], file_path: str, context: str, stats_summary) -> str:
    """Generate a report from GPT based on the Nmap XML file analysis."""

    system_prompt = f"### Nmap Scan Analysis\n" \
             f"You are a network security consultant that has been tasked with analysing open ports and services provided by the user."

    user_prompt = f"Create a markdown formatted report findings that will be added to a formal security report. Pay attention to ports and services that may be targeted by an attacker. Your response has to confirm with the following requirements: include a Description section that concisely describes the nature of open ports (do not hyperfocus on risk), include a Risk section that details the risk of identified ports and services, include a Remediation section from the perspective of IP allow/deny lists, monitoring and alerting safeguards and 'air gapping' if services are highly sensitive such as ICS/OT.\n" \
    f"Identified ports and services below:\n{stats_summary}\n\n" 

    if context:
        user_prompt += f"Context: {context}\n\n"
    
    full_prompt = system_prompt + user_prompt

    response = openai_key.completions.create(
        prompt=full_prompt,
        model="gpt-3.5-turbo-instruct",
        temperature=0.7,
        max_tokens=1500,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response.choices[0].text

def execute_fabric(stats_summary):
    fabric_executable = None
    inc_file_path = os.path.expanduser('~/.config/fabric/fabric-bootstrap.inc')

    # Open and read the .inc file to find the alias for fabric
    with open(inc_file_path, 'r', encoding='utf-8') as inc_file:
        for line in inc_file:
            # Looking for the line that starts with "alias fabric="
            if line.startswith("alias fabric="):
                # Extract the path using a regular expression. Adjusted to match your provided format
                match = re.match(r"alias fabric='(.+)'", line)
                if match:
                    fabric_executable = match.group(1)
                    break

    if fabric_executable is None:
        raise ValueError("Fabric executable path not found in .inc file")

    command = [fabric_executable, "-p", "create_network_threat_landscape"]
    
    try:
        # Execute the command without using shell=True for security
        result = subprocess.run(command, input=stats_summary, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e.stderr)
    
def create_markdown_report(gpt_response: str, table: str, stats: str):
    """Write the GPT-generated analysis and the port/service table to a Markdown file."""
    filename = f"Nmap_Analysis_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"

    with open(filename, "w") as file:
        file.write(gpt_response + "\n\n---\n\n" + "### Port/Service Stats\n\n" + stats + "\n\n---\n\n" + "### Detailed Port/Service Table\n\n" + table)

    print(f"Report generated: {filename}")

if __name__ == "__main__":
    obligatory_banner()
    parser = argparse.ArgumentParser(description='Nmap Analysis Tool that can be used to compare two nmap xml files to create a spreadsheet or can be used to get ChatGPT to analyse one nmap xml file to create a markdown report.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Nmap comparison
    compare_parser = subparsers.add_parser('compare', help='Compare two Nmap XML files to create a spreadsheet that compares port/service differences between both files')
    compare_parser.add_argument('-ff', '--first-nmap-file', required=True, help='The first Nmap XML output file for comparison')
    compare_parser.add_argument('-lf', '--last-nmap-file', required=True, help='The second Nmap XML output file for comparison')

    # GPT report generation
    gpt_parser = subparsers.add_parser('gpt-report', help='Generate an md report that includes description, risk, remediation sections with a markdown table that shows IPs, ports and services')
    gpt_parser.add_argument('-gf', '--gpt-nmap-file', required=True, help='Target Nmap XML file for GPT analysis')
    gpt_parser.add_argument('-c', '--context', type=str, default="", help='Context that will be passed to GPT. For example, scans completed from an internal IP address to an internal network')

    # fabric GPT report generation
    gpt_parser = subparsers.add_parser('fabric-report', help="Use Daniel Miessler's Fabric software to generate an md report that includes description, risk, remediation, one sentence summary, trends, and quotes sections with a markdown table that shows IPs, ports and services")
    gpt_parser.add_argument('-gf', '--gpt-nmap-file', required=True, help='Target Nmap XML file for GPT analysis')

    args = parser.parse_args()
    
    if args.command == 'compare':
        if args.first_nmap_file and args.last_nmap_file and validate_file(args.first_nmap_file) and validate_file(args.last_nmap_file):
            file1_data = parse_nmap_xml(args.first_nmap_file)
            file2_data = parse_nmap_xml(args.last_nmap_file)
            merged_data = merge_detailed_data(file1_data, file2_data)

            stats = calculate_statistics(merged_data)
            compared_data = compare_ports(file1_data, file2_data)

            generate_xlsx_report_final(compared_data, args.first_nmap_file, args.last_nmap_file, stats)
            print("Comparison spreadsheet generated.")
        else:
            print("Invalid file paths provided for comparison.")

    elif args.command == 'gpt-report':
        if validate_file(args.gpt_nmap_file) and os.getenv("OPENAI_KEY"):
            openai_key = OpenAI(api_key=os.getenv("OPENAI_KEY"))

            print(f"Passing analysed stats for {args.gpt_nmap_file} to GPT to create .md report.")
            nmap_data = parse_nmap_xml(args.gpt_nmap_file)
            table = create_markdown_table(nmap_data)

            stats = calculate_statistics(nmap_data)
            stats_summary = format_stats_for_gpt(stats)

            gpt_response = generate_gpt_report(nmap_data, args.gpt_nmap_file, args.context,stats_summary)
            create_markdown_report(gpt_response, table, stats_summary)

    elif args.command == 'fabric-report':
        if validate_file(args.gpt_nmap_file):
            print(f"Function disabled until pull request is merged.")
            # print(f"Passing analysed stats for {args.gpt_nmap_file} to Fabric to create .md report using pattern create_network_threat_landscape")
            # nmap_data = parse_nmap_xml(args.gpt_nmap_file)
            # table = create_markdown_table(nmap_data)

            # stats = calculate_statistics(nmap_data)
            # stats_summary = format_stats_for_gpt(stats)

            # fabric_response = execute_fabric(stats_summary)
            # create_markdown_report(fabric_response, table, stats_summary)

        else:
            if not os.getenv("OPENAI_KEY"):
                print("The OPENAI_KEY environment variable is not set. Please set the OPENAI_KEY with your OpenAI API key.")
            else:
                print(f"File {args.gpt_nmap_file} does not exist or is not a valid XML file.")
    else:
        parser.print_help()
