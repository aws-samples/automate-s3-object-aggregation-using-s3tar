from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_ec2 as ec2,
    aws_kms as kms,
    CfnOutput,
)

from constructs import Construct
from .construct.s3tar_step_function_stack import S3TarStepFunctionStack
from .construct.s3tar_ecs_stack import S3TarECSStack
from .construct.s3tar_eventbridge_schedule import S3TarEventBridgeScheduleStack

class S3TarStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "s3tarVPC", nat_gateways=1, max_azs=2)

        topic = sns.Topic(self, "s3tarNotificationTopic")

        target = S3TarECSStack(self, "s3tarECSTask", vpc=vpc)

        run_task_with_retry = S3TarStepFunctionStack(
            self,
            "s3tarStateMachineStack",
            error_notify_topic=topic,
            success_notify_topic=topic,
            task=target.s3tar_task_definition,
            cluster=target.ecs_cluster,
            max_retry_count=3
        )

        statemachine_schedule = S3TarEventBridgeScheduleStack(
            self,
            "s3tarEventBridgeScheduleStack",
            s3tarstatemachine=run_task_with_retry.state_machine
        )

        CfnOutput(
            self,
            "s3TarStateMachineArn",
            value=run_task_with_retry.state_machine.state_machine_arn,
            export_name="s3TarStateMachineArn",
        )
        CfnOutput(self, "s3tarEventBridgeScheduleName", value=statemachine_schedule.s3tarEventSchedule.ref)