import re
from save_blockchain_test_data_to_excel import save_test_results
import os

def parse_perf_times(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Adjust regexes for blockchain test output
    test_names = [
        ("test_get_chain", r"/chain:.*elapsed=([0-9.]+)s"),
        ("test_upload_transaction_file_and_add_block", r"/transaction/upload:.*elapsed=([0-9.]+)s"),
        ("test_add_block", r"/add_block:.*elapsed=([0-9.]+)s"),
        ("test_validate_chain", r"/validate:.*elapsed=([0-9.]+)s"),
        ("test_get_block", r"/block/0:.*elapsed=([0-9.]+)s"),
        ("test_get_all_blocks_for_powerbi", r"/powerbi/all_blocks:.*elapsed=([0-9.]+)s"),
        ("test_save_blockchain_to_csv", r"/powerbi/save_csv:.*elapsed=([0-9.]+)s")
    ]
    runs = []
    current = {}
    for line in lines:
        for name, regex in test_names:
            m = re.search(regex, line)
            if m:
                current[name] = float(m.group(1))
        if len(current) == len(test_names):
            runs.append(current)
            current = {}
    return runs

if __name__ == "__main__":
    log_path = os.path.join(os.path.dirname(__file__), "last_test_run.txt")
    runs = parse_perf_times(log_path)
    for i, test_times in enumerate(runs):
        test_file = 'test_blockchain_api_tests.py'
        test_names = ', '.join(test_times.keys())
        notes = f'Automated blockchain run {i+1}.'
        save_test_results(test_file, test_names, notes, test_times)
    print(f"Inserted {len(runs)} blockchain runs into Excel and CSV.")
