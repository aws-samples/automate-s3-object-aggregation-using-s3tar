#! /bin/sh

previous_day=$(date -d "-1 day" "+%Y-%m-%d")
echo 'Previous Day:-'$previous_day

current_date=$(date +"%Y-%m-%d")
finaltarname="s3tar_archive_${current_date}.tar"
echo "Final Tar Name:- "$finaltarname

# set environment variables
sourcebucketname=$SOURCE_BUCKET_NAME
destbucketname=$DEST_BUCKET_NAME
destbucketinventoryprefix=$DEST_BUCKET_INVENTORY_PREFIX
destbucketregion=$DEST_BUCKET_REGION
destbuckets3tarprefix=$DEST_BUCKET_S3TAR_PREFIX

# print shell arguments for logging
echo "S3 Source-BucketName:- "$sourcebucketname
echo "S3 Destination-BucketName:- "$destbucketname
echo "S3 Destination-BucketInventoryPrefix:- "$destbucketinventoryprefix
echo "S3 Destination-BucketRegion:- "$destbucketregion
echo "S3 Destination-S3TarPrefix:- "$destbuckets3tarprefix

# Search the inventory file prefix which was generated for the previous day and set the prefix to a variable
inventory_prefix_search="$(aws s3 ls $destbucketinventoryprefix | grep -i $previous_day)"
inventory_prefix=$(echo "$inventory_prefix_search" | awk -F' ' '{print $2}')
echo "S3 Inventory Prefix:- "$inventory_prefix

# Search and pick the S3 object key from manifest.json generated from S3 inventory
manifest_filename="manifest.json"
if [ -n "$inventory_prefix" ]; then
    aws s3 cp s3://$destbucketinventoryprefix$inventory_prefix$manifest_filename /tmp/$inventory_prefix/manifest.json
    result=$?

    if [ $result -eq 0 ]; then
        echo "Download of manifest.json from S3 prefix - $destbucketinventoryprefix$inventory_prefix was successful."
    else
        echo "Download of manifest.json from S3 prefix - $destbucketinventoryprefix$inventory_prefix failed. Error code: $result"
        exit 1
    fi
else
    echo "S3 Inventory Prefix was NULL or empty"
    exit 1
fi

key_value=$(jq -r '.files[0].key' /tmp/$inventory_prefix/manifest.json)
echo "S3 Inventory Key from manifest.json:- "$key_value

# Copy the inventory gzip file from S3 key to a local tmp directory
if [ -n "$key_value" ]; then
    aws s3 cp s3://$destbucketname/$key_value /tmp/$inventory_prefix/tmpinventory.gz
    result=$?

    if [ $result -eq 0 ]; then
        echo "S3 Inventory file key copied successfully from manifest.json"
    else
        echo "S3 Inventory file key copy failed. Error code: $result"
        exit 1
    fi
else
    echo "S3 Inventory Key from manifest.json was NULL or empty"
    exit 1
fi

# Check if the .gz file exists
gz_file="/tmp/$inventory_prefix/tmpinventory.gz"
if [ -f "$gz_file" ]; then
    # Deflate the .gz file
    gunzip -c "$gz_file" > "/tmp/$inventory_prefix/inventory.csv"
else
    echo "File not found: $gz_file"
    exit 1
fi

# Filter the inventory file for the previous day's objects for archival
# TO-DO - Confirm the final inventory config and csv and revisit the logic below to tar only objects of size > 0 bytes,
# data logic for object keys to be included based on last modified timestamp and the correct indexes in file to use
# Column 1 is the bucket
# Column 2 is the key
# Column 3 is the size
# Column 4 is the LastModified timestamp
# Column 5 is the ETag
# Column 6 is the Storage Class
if [ -f "/tmp/$inventory_prefix/inventory.csv" ]; then
    echo "inventory.csv file exists in /tmp/$inventory_prefix"
    awk -F',' 'BEGIN {OFS=","} {gsub(/"/,"",$3);gsub(/"/, "", $4); if($3>0 && "$(date -d "$4" +%s)" -lt "$(date -d "$date" +%s)") print $1,$2,$3,$5}' /tmp/$inventory_prefix/inventory.csv > /tmp/$inventory_prefix/s3tarinputmanifest.csv
else
    echo "inventory.csv file not found under /tmp/$inventory_prefix"
    exit 1
fi

if [ -f "/tmp/$inventory_prefix/s3tarinputmanifest.csv" ] && [ -s "/tmp/$inventory_prefix/s3tarinputmanifest.csv" ]; then
    echo "s3tarinputmanifest.csv File exists in /tmp/$inventory_prefix"
    # upload final manifest file to s3 destination bucket date prefix
    aws s3 cp /tmp/$inventory_prefix/s3tarinputmanifest.csv s3://$destbucketinventoryprefix$inventory_prefix
    result=$?

    if [ $result -eq 0 ]; then
        echo "s3tarinputmanifest.csv File upload to S3 prefix - $destbucketinventoryprefix$inventory_prefix was successful."
    else
        echo "s3tarinputmanifest.csv File upload to S3 prefix - $destbucketinventoryprefix$inventory_prefix failed. Error code: $result"
    fi
else
    echo "s3tarinputmanifest.csv file not found or empty under /tmp/$inventory_prefix"
    exit 1
fi

rm -rf /tmp

#Execute s3 tar with the input manifest
# TO-DO - Modify options in command below to customize with other s3tar options
/usr/local/bin/s3tar --region $destbucketregion -cvf s3://$destbuckets3tarprefix/$current_date/$finaltarname -m 's3://'$destbucketinventoryprefix$inventory_prefix's3tarinputmanifest.csv'