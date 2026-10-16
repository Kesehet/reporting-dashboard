import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from DB import SQLConn, Transaction

# Config
THREADS = 10
BATCH_SIZE = 999
OUTPUT_DIR = "C:/Users/reddys/OneDrive - FNBCorp/Documents/my_python_scripts/JM_EXTRACTS"

# Get ID range
sql = SQLConn()
sql.connect()
txn = Transaction(sql)
id_range_query = "SELECT MIN(Id) AS MinId, MAX(Id) AS MaxId FROM [DigitalReport].[dbo].[JMExtract];"
range_result = txn.get_transactions_by_sql_query(id_range_query)
start_id = range_result[0]["MinId"]
end_id = range_result[0]["MaxId"]
sql.disconnect()

# Thread-safe queue for rows
row_queue = Queue()

def fetch_row(row_id):
    sql_p = SQLConn()
    sql_p.connect()
    txn_p = Transaction(sql_p)
    query = f"SELECT * FROM [DigitalReport].[dbo].[JMExtract] WHERE Id = {row_id};"
    result = txn_p.get_transactions_by_sql_query(query)
    sql_p.disconnect()
    return result[0] if result else None

def writer_thread():
    batch = []
    file_count = 1
    while True:
        row = row_queue.get()
        if row is None:  # Signal to stop
            break
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            write_batch(batch, file_count)
            file_count += 1
            batch.clear()
    # Write remaining rows
    if batch:
        write_batch(batch, file_count)

def write_batch(batch, file_count):
    csv_file = f"{OUTPUT_DIR}/JMExtract_batch_{file_count}.csv"
    headers = batch[0].keys()
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(batch)
    print(f"Written batch {file_count} with {len(batch)} rows")

    
    

    sql_file = f"{OUTPUT_DIR}/JMExtract_batch_{file_count}.sql"
    table_name = "JMExtract"
    headers = batch[0].keys()

    with open(sql_file, mode="w", encoding="utf-8") as file:
        for row in batch:
            # Escape single quotes in values            
            values = []
            for h in headers:
                val = row[h]
                if val is None:
                    values.append("NULL")
                else:
                    escaped = str(val).replace("'", "''")  # Escape single quotes for SQL
                    values.append(f"'{escaped}'")

            insert_stmt = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({', '.join(values)});\n"
            file.write(insert_stmt)

    print(f"Written batch {file_count} with {len(batch)} rows as SQL INSERT statements")




# Start writer thread
import threading
writer = threading.Thread(target=writer_thread)
writer.start()

# Fetch rows in parallel
start_time = time.time()
with ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = [executor.submit(fetch_row, row_id) for row_id in range(start_id, end_id + 1)]
    for idx, future in enumerate(as_completed(futures), start=1):
        row = future.result()
        if row:
            row_queue.put(row)
        if idx % 100 == 0:
            elapsed = time.time() - start_time
            eta = (elapsed / idx) * (end_id - start_id + 1 - idx)
            print(f"Processed {idx} rows | ETA: {eta:.2f}s")

# Signal writer to finish
row_queue.put(None)
writer.join()

print(f"Completed in {time.time() - start_time:.2f}s")