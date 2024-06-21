from aws_cdk import (
    aws_iam as iam,
    aws_scheduler as scheduler,
    aws_stepfunctions as sfn,
)
import json
from constructs import Construct

class S3TarEventBridgeScheduleStack(Construct):
    
    def __init__(self, scope: Construct, id: str, s3tarstatemachine: sfn.StateMachine, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ## Add scheduler permissions
        scheduler_role = iam.Role(self, "scheduler-role",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )

        scheduler_sf_execution_policy = iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[s3tarstatemachine.state_machine_arn],
                effect=iam.Effect.ALLOW,
        )

        scheduler_role.add_to_policy(scheduler_sf_execution_policy)

        ## Add schedule group
        schedule_group = scheduler.CfnScheduleGroup(self, "s3tar-schedule-group", name="s3tar-schedule-group");

        ## Add schedule - run one per day at 00.00 (midnight) UTC
        event_schedule = scheduler.CfnSchedule(self, "schedule",
                flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                    mode="OFF",
                ),
                schedule_expression="cron(0 0 ? * MON-SUN *)",
                group_name=schedule_group.name,
                target=scheduler.CfnSchedule.TargetProperty(
                    arn=s3tarstatemachine.state_machine_arn,
                    role_arn=scheduler_role.role_arn,
                    input=json.dumps({
                        "metadata": {
                            "eventId": "s3tar_scheduled_event",
                        },
                        "data" : {
                            "scheduleName": "s3tar",
                            "frequency": "daily"            
                        }
                    })
                )
            )

        self.s3tarEventSchedule = event_schedule