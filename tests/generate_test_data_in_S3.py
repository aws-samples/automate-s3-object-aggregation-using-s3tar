#!/usr/bin/env python3

import boto3
import random
import string
import argparse
from datetime import datetime, timedelta

# Create S3 client
s3 = boto3.client('s3')

# generates 100 random log entries per daily S3 bucket prefix for the past number of days from today specified as
# num_days - 10, 20 or any number. Indicates specified number of days from today in the past, random entries are inserted in S3 prefix
# s3_bucket_name - S3 source bucket name. The function creates daily prefixes under the daily_logs prefix in this bucket
def generate_test_data_in_S3(num_days, s3_bucket_name):
    start_date = datetime.now() - timedelta(days=num_days-1)
    # Generate sample log entries
    for day in range(num_days):
        log_date = start_date + timedelta(days=day)
        num_logs = 100
        print(f"{num_logs} random log files will be inserted in daily s3 prefix, from {num_days} days in the past until current date {datetime.now().strftime('%Y-%m-%d')}. Prefix Index- {day}")
        for i in range(num_logs):
            log_date = log_date + timedelta(seconds=i * 60)
            log_level = random.choice(['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
            log_message = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(50, 200)))
            log_entry = f"{log_date.isoformat()} | {log_level} | {log_message}"
            # Upload the log entry to S3
            key = f"logs/{log_date.strftime('%Y/%m/%d')}/log_{i}.txt"
            s3.put_object(Bucket=s3_bucket_name, Key=key, Body=log_entry.encode())
    return {
        'statusCode': 200,
        'body': 'Uploaded {num_logs} sample log files to S3 bucket: {s3_bucket_name}'
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num_of_days", type=int)
    parser.add_argument("-b", "--bucket_name")
    args = parser.parse_args()

    generate_test_data_in_S3(args.num_of_days, args.bucket_name)
    print("Test data generated successfully")

if __name__ == "__main__":
    main()