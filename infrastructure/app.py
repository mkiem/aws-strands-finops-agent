#!/usr/bin/env python3
import os
import aws_cdk as cdk
from appsync_stack import FinOpsAppSyncStack

app = cdk.App()

FinOpsAppSyncStack(
    app, "FinOpsAppSyncStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    ),
)

app.synth()
