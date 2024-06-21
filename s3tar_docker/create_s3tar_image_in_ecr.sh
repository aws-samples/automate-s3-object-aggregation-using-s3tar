#!/bin/sh

set -e;

# Configuration File Path
APP_CONFIG=$1
export APP_CONFIG=$1

ACCOUNT=$(cat $APP_CONFIG | jq -r '.Project.Account') #ex> 123456789123
REGION=$(cat $APP_CONFIG | jq -r '.Project.Region') #ex> us-east-1
PROFILE_NAME=$(cat $APP_CONFIG | jq -r '.Project.Profile') #ex> cdk-demo
ECR_REPO_NAME=$(cat $APP_CONFIG | jq -r '.Stack.ECRInfra.RepoName') #ex> cdk-demo;
DOCKER_REGISTRY_URI=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com
DOCKER_IMAGE_TAG=$(cat $APP_CONFIG | jq -r '.Stack.ECRInfra.ImageTag')

echo ==--------ConfigInfo---------==
echo $APP_CONFIG
echo $ACCOUNT
echo $REGION
echo $PROFILE_NAME
echo $ECR_REPO_NAME
echo $DOCKER_REGISTRY_URI
echo $DOCKER_IMAGE_TAG
echo .
echo .

echo ==--------CreateEcrRepo---------==
# Please run it only once and comment it out.
aws ecr create-repository --repository-name $ECR_REPO_NAME
echo .
echo .

echo ==--------Builds3tarDockerImage---------==
echo 'Build and tag s3tar Docker image...';
docker build -t ${DOCKER_REGISTRY_URI}/${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG} .

echo ==--------LoginEcrRepo---------==
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com
echo .
echo .

echo ==--------PushBaseImageToEcr---------==
docker push ${DOCKER_REGISTRY_URI}/${ECR_REPO_NAME}:${DOCKER_IMAGE_TAG}
echo .
echo .
echo Completed