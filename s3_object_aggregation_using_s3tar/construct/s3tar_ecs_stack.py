from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    Stack,
)
from constructs import Construct
import json

class S3TarECSStack(Construct):
 
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        with open('./config/s3tar-app-config.json', 'r') as file:
            data = json.load(file)
            repo_name = data['Stack']['ECRInfra']['RepoName']
            image_tag = data['Stack']['ECRInfra']['ImageTag']
            source_bucket_name = data['Stack']['S3TarECSStack']['SourceBucketName']
            dest_bucket_name = data['Stack']['S3TarECSStack']['DestBucketName']
            dest_bucket_inventory_prefix = data['Stack']['S3TarECSStack']['DestBucketInventoryPrefix']
            dest_bucket_s3tar_prefix = data['Stack']['S3TarECSStack']['DestBucketS3TarPrefix']
            dest_bucket_region = data['Stack']['S3TarECSStack']['DestBucketRegion']

        cluster = ecs.Cluster(self, "s3tarECSCluster", vpc=vpc, container_insights=True)
       
        td = ecs.FargateTaskDefinition(self, "s3tarTaskDefinition", memory_limit_mib=4096, cpu=2048)
        
        td.add_container("s3tarContainer", 
                         image=ecs.ContainerImage.from_ecr_repository(
                             ecr.Repository.from_repository_name(self, "s3tarECRRepo", repo_name),
                             image_tag),
                         memory_limit_mib=512,
                         cpu=512,
                         port_mappings=[ecs.PortMapping(container_port=80)],
                         logging=ecs.AwsLogDriver(stream_prefix="s3tarContainer"),
                         environment={
                             "SOURCE_BUCKET_NAME": source_bucket_name,
                             "DEST_BUCKET_NAME": dest_bucket_name,
                             "DEST_BUCKET_INVENTORY_PREFIX": dest_bucket_inventory_prefix,
                             "DEST_BUCKET_S3TAR_PREFIX": dest_bucket_s3tar_prefix,
                             "DEST_BUCKET_REGION": dest_bucket_region
                         })
        self.ecs_cluster = cluster
        self.s3tar_task_definition = td
