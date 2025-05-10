import pandas as pd
from datetime import datetime
import os
import openpyxl

excel_path = 'traditional_test_data.xlsx'
csv_path = 'traditional_test_data.csv'

# Always use these columns
CSV_COLUMNS = ['timestamp', 'test_file', 'test_names', 'notes', 'performance_times']

def save_test_results(test_file, test_names, notes, test_times):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    perf_str = ','.join([f"{k}:{v:.4f}" for k, v in test_times.items()])
    new_row = {
        'timestamp': timestamp,
        'test_file': test_file,
        'test_names': test_names,
        'notes': notes,
        'performance_times': perf_str
    }
    # Save to Excel
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path, engine='openpyxl')
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])
    df.to_excel(excel_path, index=False, engine='openpyxl')
    # Save to CSV (force all columns)
    if os.path.exists(csv_path):
        df_csv = pd.read_csv(csv_path)
        # Add missing columns if needed
        for col in CSV_COLUMNS:
            if col not in df_csv.columns:
                df_csv[col] = ''
        df_csv = pd.concat([df_csv, pd.DataFrame([new_row])], ignore_index=True)
        df_csv = df_csv[CSV_COLUMNS]
    else:
        df_csv = pd.DataFrame([new_row], columns=CSV_COLUMNS)
    df_csv.to_csv(csv_path, index=False)

# Example usage:
if __name__ == "__main__":
    test_file = 'test_traditional_database_tests.py'
    test_names = 'test_upload_transaction_file, test_get_transactions'
    notes = 'Includes pytest timing hook and FastAPI TestClient tests for upload and fetch.'
    # Replace with actual measured times from your test run
    test_times = {"test_upload_transaction_file": 0.31, "test_get_transactions": 0.29}
    save_test_results(test_file, test_names, notes, test_times)
