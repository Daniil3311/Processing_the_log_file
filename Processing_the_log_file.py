import argparse
import json
from collections import defaultdict
from datetime import datetime
from tabulate import tabulate


class LogAnalyzer:
    def __init__(self):
        self.report_handlers = {
            'average': self.generate_average_report,
        }
        
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Process log files and generate reports.')
        parser.add_argument('--file', nargs='+', required=True, help='Path to log file(s)')
        parser.add_argument('--report', required=True, choices=self.report_handlers.keys(),
                            help='Type of report to generate')
        parser.add_argument('--date', help='Filter logs by date (format: YYYY-MM-DD)')
        return parser.parse_args()

    def load_logs(self, file_paths, filter_date=None):
        logs = []
        for file_path in file_paths:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        if filter_date:
                            log_date = datetime.fromisoformat(log_entry['@timestamp']).date()
                            if log_date != datetime.fromisoformat(filter_date).date():
                                continue
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        return logs

    def generate_average_report(self, logs):
        pass
        endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0})

        for log in logs:
            endpoint = log['url']
            response_time = log['response_time']
            endpoint_stats[endpoint]['count'] += 1
            endpoint_stats[endpoint]['total_time'] += response_time

        report_data = []
        for endpoint, stats in endpoint_stats.items():
            avg_time = stats['total_time'] / stats['count']
            report_data.append([endpoint, stats['count'], f"{avg_time:.2f} ms"])

        return sorted(report_data, key=lambda x: x[1], reverse=True)

    def generate_report(self, report_type, logs):
        handler = self.report_handlers.get(report_type)
        if not handler:
            raise ValueError(f"Unknown report type: {report_type}")
        return handler(logs)


    def run(self):
        args = self.parse_args()
        logs = self.load_logs(args.file, args.date)

        if not logs:
            print("No log entries found matching the criteria.")
            return

        report_data = self.generate_report(args.report, logs)

        headers = ["Endpoint", "Request Count", "Average Response Time"]
        print(tabulate(report_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.run()
