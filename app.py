#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )
from s3_object_aggregation_using_s3tar.s3_object_aggregation_using_s3tar_stack import S3TarStack

app = cdk.App()
cdk.Aspects.of(app).add(AwsSolutionsChecks())
s3tarstack = S3TarStack(app, "S3TarStack")

NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-IAM4", "reason":"AWSLambdaBasicExecutionRole used for Lambda function logging"}])
NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-IAM5", "reason":"ECS Task permissions to read and write on mentioned Source and Dest S3 Buckets as the buckets are not created by this stack"}])
NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-ECS2", "reason":"Env variable for ECS task gets injected from config file during stack deployment rather than modifying it from console after stack is available"}])
NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-SNS2", "reason":"SNS SSE settings ignored for the sample implementation"}])
NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-SNS3", "reason":"SNS enforcing SSL for publishers is ignored as in sample implementation only step function will publishSSE settings ignored for the sample implementation"}])
NagSuppressions.add_stack_suppressions(s3tarstack, [{"id":"AwsSolutions-VPC7", "reason":"Setting up VPC flow log is ignored for sample implementation."}])

app.synth()
