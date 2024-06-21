import os
from aws_cdk import (
    aws_sns as sns,
    aws_ecs as ecs,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfnt,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
)
import json
from constructs import Construct
from pathlib import Path

class S3TarStepFunctionStack(Construct):
    def state_machine(self) -> sfn.StateMachine:
        return self._state_machine

    def __init__(self, scope: Construct, id: str, cluster: ecs.ICluster, task: ecs.TaskDefinition, 
                 error_notify_topic: sns.ITopic, success_notify_topic: sns.ITopic, max_retry_count: int,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        with open('./config/s3tar-app-config.json', 'r') as file:
            data = json.load(file)
            account_id = data['Project']['Account']
            source_bucket_name = data['Stack']['S3TarECSStack']['SourceBucketName']
            dest_bucket_name = data['Stack']['S3TarECSStack']['DestBucketName']

        # Create a custom IAM policy statement with the desired permissions for ECS Task role
        s3_and_kms_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:PutObject",
                "kms:Decrypt",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:ListObjects",
                "s3:GetObject",
                "s3:GetObjectAttributes",
                "s3:GetObjectVersion"
            ],
            resources=[
                f"arn:aws:kms:*:{account_id}:key/*",
                f"arn:aws:s3:::{source_bucket_name}",
                f"arn:aws:s3:::{source_bucket_name}/*",
                f"arn:aws:s3:::{dest_bucket_name}",
                f"arn:aws:s3:::{dest_bucket_name}/*"
            ]
        )
        #update task role with needed IAM pemission policy
        task.add_to_task_role_policy(s3_and_kms_policy_statement)

        run_task = sfnt.EcsRunTask(
            self,
            "RunTask",
            cluster=cluster,
            task_definition=task,
            launch_target=sfnt.EcsFargateLaunchTarget(
                platform_version=ecs.FargatePlatformVersion.VERSION1_4
            ),
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            result_path="$.RunTask"
        )
        project_root = Path(__file__).parent.parent
        error_handler_path = os.path.join(project_root, "lambda", "error_handler")

        error_handler_function = _lambda.Function(
            self,
            "ErrorHandlerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset(error_handler_path),
            handler="index.handler",
        )
        
        error_handler = sfnt.LambdaInvoke(
            self,
            "ErrorHandler",
            lambda_function=error_handler_function,
            result_path="$.Error",
        )

        notify_error = sfnt.SnsPublish(
            self,
            "NotifyError",
            topic=error_notify_topic,
            message=sfn.TaskInput.from_json_path_at("$"),
            subject="Task failed",
            result_path="$.Notify",
        )

        notify_success = sfnt.SnsPublish(
            self,
            "NotifySuccess",
            topic=success_notify_topic,
            message=sfn.TaskInput.from_json_path_at("$"),
            subject="Task successfully processed.",
            result_path="$.Notify",
        )

        chain = (
            sfn.Chain.start(
                run_task.add_catch(
                    error_handler.next(
                        sfn.Choice(self, "Retryable?")
                        .when(
                            sfn.Condition.and_(
                                sfn.Condition.string_equals(
                                    "$.Error.Payload.type", "retryable"
                                ),
                                sfn.Condition.number_less_than(
                                    "$.Error.Payload.retryCount", max_retry_count
                                ),
                            ),
                            sfn.Wait(
                                self,
                                "RetryWait",
                                time=sfn.WaitTime.seconds_path("$.Error.Payload.waitTimeSeconds"),
                            ).next(run_task),
                        )
                        .otherwise(notify_error)
                    ),
                    result_path="$.RunTaskError"
                )
            )
            .next(notify_success)
        )
        sm_log_group = logs.LogGroup(self, "s3tarStateMachineLogGroup")
        self.state_machine = sfn.StateMachine(self, "s3tarStateMachine", 
                                              definition_body=sfn.DefinitionBody.from_chainable(chain),
                                              logs=sfn.LogOptions(
                                                    destination=sm_log_group,
                                                    level=sfn.LogLevel.ALL),
                                              tracing_enabled=True
                                              )

