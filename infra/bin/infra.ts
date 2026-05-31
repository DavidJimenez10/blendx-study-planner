#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { NetworkingStack } from '../lib/networking-stack';
import { AppStack } from '../lib/app-stack';

const app = new cdk.App();

const env: cdk.Environment = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

const networkingStack = new NetworkingStack(app, 'NetworkingStack', { env });

new AppStack(app, 'AppStack', {
  env,
  vpc: networkingStack.vpc,
});
