FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Update package repositories
RUN yum update -y

# Install required packages
RUN yum install -y wget unzip gzip awscli jq

# Copy the shell script to the container
COPY generatemanifest.sh /usr/local/bin/

# Set the working directory
WORKDIR /usr/local/bin/

# Make the script executable
RUN chmod +x /usr/local/bin/generatemanifest.sh

RUN DOWNLOAD_URL="https://github.com/awslabs/amazon-s3-tar-tool/releases/download/v1.0.24/s3tar-linux-amd64.zip" && \
    wget -O /tmp/s3tar.zip "${DOWNLOAD_URL}" && \
    unzip -d /tmp/ /tmp/s3tar.zip && \
    chmod +x /tmp/s3tar-linux-amd64 && \
    mv /tmp/s3tar-linux-amd64 /usr/local/bin/s3tar

# Set the entrypoint to s3tar
ENTRYPOINT ["/usr/local/bin/generatemanifest.sh"]

