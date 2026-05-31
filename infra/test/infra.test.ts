import * as cdk from 'aws-cdk-lib/core';
import { Template } from 'aws-cdk-lib/assertions';
import { NetworkingStack } from '../lib/networking-stack';
import { AppStack } from '../lib/app-stack';

test('NetworkingStack synthesizes without errors', () => {
  const app = new cdk.App();
  const stack = new NetworkingStack(app, 'TestNetworkingStack');
  const template = Template.fromStack(stack);

  template.resourceCountIs('AWS::EC2::VPC', 1);
  template.resourceCountIs('AWS::EC2::InternetGateway', 1);
  template.resourceCountIs('AWS::EC2::Subnet', 4);
});

test('AppStack synthesizes without errors', () => {
  const app = new cdk.App();
  const networkingStack = new NetworkingStack(app, 'TestNetworkingStack');
  const appStack = new AppStack(app, 'TestAppStack', {
    vpc: networkingStack.vpc,
  });
  const template = Template.fromStack(appStack);

  template.resourceCountIs('AWS::RDS::DBInstance', 1);
  template.resourceCountIs('AWS::ECR::Repository', 1);
  template.resourceCountIs('AWS::ECS::TaskDefinition', 1);
  template.resourceCountIs('AWS::EC2::SecurityGroup', 3);
});
