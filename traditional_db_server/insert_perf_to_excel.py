import re
from save_traditional_test_data_to_excel import save_test_results
import os

def parse_perf_times(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    upload_times_local = []
    get_times_local = []
    for line in lines:
        m1 = re.search(r"/traditional/transaction/upload:.*elapsed=([0-9.]+)s", line)
        m2 = re.search(r"/traditional/transactions:.*elapsed=([0-9.]+)s", line)
        if m1:
            upload_times_local.append(float(m1.group(1)))
        if m2:
            get_times_local.append(float(m2.group(1)))
    return upload_times_local, get_times_local

if __name__ == "__main__":
    # Use absolute path for log file
    log_path = os.path.join(os.path.dirname(__file__), "last_test_run.txt")
    upload_times, get_times = parse_perf_times(log_path)
    for i, (u, g) in enumerate(zip(upload_times, get_times)):
        test_file = 'test_traditional_database_tests.py'
        test_names = 'test_upload_transaction_file, test_get_transactions'
        notes = f'Automated run {i+1}.'
        test_times = {"test_upload_transaction_file": u, "test_get_transactions": g}
        save_test_results(test_file, test_names, notes, test_times)
    print(f"Inserted {len(upload_times)} runs into Excel.")
