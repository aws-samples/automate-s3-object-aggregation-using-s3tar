#!/bin/sh

# Configuration File Path
APP_CONFIG=$1
export APP_CONFIG=$APP_CONFIG

PROJECT_NAME=$(cat $APP_CONFIG | jq -r '.Project.Name') #ex> IoTData
PROJECT_STAGE=$(cat $APP_CONFIG | jq -r '.Project.Stage') #ex> Dev
PROFILE_NAME=$(cat $APP_CONFIG | jq -r '.Project.Profile') #ex> cdk-demo

echo ==--------ConfigInfo---------==
echo $APP_CONFIG
echo $PROFILE_NAME
echo $PROJECT_NAME
echo .
echo .

echo ==--------SetAwsProfileEnv---------==
if [ -z "$PROFILE_NAME" ]; then
    echo "Project.Profile is empty, default AWS Profile is used"
else
    if [ -z "$ON_PIPELINE" ]; then
        echo "$PROFILE_NAME AWS Profile is used"
        export AWS_PROFILE=$PROFILE_NAME
    else
        echo "Now on CodePipeline, default AWS Profile is used"
    fi
fi
echo .
echo .

echo ==--------CDKVersionCheck---------==
# npm install -g aws-cdk
cdk --version
echo .
echo .

echo ==--------ListStacks---------==
cdk list
echo .
echo .

echo ==--------DeployStacksStepByStep---------==
cdk deploy S3TarStack --require-approval never
echo .
echo .