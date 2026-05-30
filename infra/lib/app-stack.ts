import * as cdk from 'aws-cdk-lib/core';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as elbv2_targets from 'aws-cdk-lib/aws-elasticloadbalancingv2-targets';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';

export interface AppStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
}

export class AppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: AppStackProps) {
    super(scope, id, props);

    const { vpc } = props;

    // ── Security Groups ──

    const albSg = new ec2.SecurityGroup(this, 'AlbSg', {
      vpc,
      description: 'ALB Security Group',
      allowAllOutbound: false,
    });
    albSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP from world');

    const fargateSg = new ec2.SecurityGroup(this, 'FargateSg', {
      vpc,
      description: 'Fargate Security Group',
      allowAllOutbound: true,
    });
    fargateSg.addIngressRule(albSg, ec2.Port.tcp(8000), 'Allow from ALB only');

    const rdsSg = new ec2.SecurityGroup(this, 'RdsSg', {
      vpc,
      description: 'RDS Security Group',
      allowAllOutbound: false,
    });
    rdsSg.addIngressRule(fargateSg, ec2.Port.tcp(5432), 'Allow PostgreSQL from Fargate');

    // ── RDS — PostgreSQL 16.4 ──

    const dbInstance = new rds.DatabaseInstance(this, 'Database', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16_4,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [rdsSg],
      databaseName: 'study_planner',
      allocatedStorage: 20,
      storageType: rds.StorageType.GP3,
      storageEncrypted: true,
      multiAz: false,
      deletionProtection: false,
      deleteAutomatedBackups: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ── ECR ──

    const repository = new ecr.Repository(this, 'Repository', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      lifecycleRules: [
        {
          maxImageCount: 10,
        },
      ],
    });

    // ── Secrets Manager ──
    // Single JSON secret grouping JWT_SECRET and OPENAI_API_KEY.
    // DATABASE_URL is constructed inline in the task definition from RDS values.

    const kmsKey = new kms.Key(this, 'AppSecretKey', {
      description: 'KMS key for BlendX application secrets',
      enableKeyRotation: true,
      alias: 'alias/blendx-app-secrets',
    });

    const appSecret = new sm.Secret(this, 'AppSecret', {
      secretName: 'blendx/app-secrets',
      description: 'Application secrets for BlendX Study Planner',
      encryptionKey: kmsKey,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          OPENAI_API_KEY: 'CHANGE_ME',
        }),
        generateStringKey: 'JWT_SECRET',
        excludePunctuation: false,
        passwordLength: 32,
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // ── CloudWatch Logs ──

    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ── ECS Cluster ──

    const cluster = new ecs.Cluster(this, 'Cluster', { vpc });

    // ── IAM Roles ──

    const taskExecutionRole = new iam.Role(this, 'TaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'Grants ECS agent permission to pull images, read secrets, write logs',
    });

    taskExecutionRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
    );

    const rdsSecret = dbInstance.secret!;
    rdsSecret.grantRead(taskExecutionRole);

    taskExecutionRole.addToPrincipalPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue',
        'secretsmanager:DescribeSecret',
      ],
      resources: [appSecret.secretArn],
      conditions: {
        Bool: { 'aws:SecureTransport': 'true' },
      },
    }));

    kmsKey.grantDecrypt(taskExecutionRole);

    const taskRole = new iam.Role(this, 'TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'Grants the running container permission to call AWS APIs',
    });

    // ── Task Definition ──

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
      memoryLimitMiB: 512,
      cpu: 256,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
      executionRole: taskExecutionRole,
      taskRole,
    });

    const databaseUrl = cdk.Fn.join('', [
      'postgresql://',
      rdsSecret.secretValueFromJson('username').unsafeUnwrap(),
      ':',
      rdsSecret.secretValueFromJson('password').unsafeUnwrap(),
      '@',
      dbInstance.dbInstanceEndpointAddress,
      ':',
      dbInstance.dbInstanceEndpointPort,
      '/study_planner',
    ]);

    taskDefinition.addContainer('AppContainer', {
      image: ecs.ContainerImage.fromEcrRepository(repository, 'latest'),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'blendx', logGroup, mode: ecs.AwsLogDriverMode.BLOCKING }),
      environment: {
        DATABASE_URL: databaseUrl,
      },
      secrets: {
        JWT_SECRET: ecs.Secret.fromSecretsManager(appSecret, 'JWT_SECRET'),
        OPENAI_API_KEY: ecs.Secret.fromSecretsManager(appSecret, 'OPENAI_API_KEY'),
      },
      portMappings: [{ containerPort: 8000, protocol: ecs.Protocol.TCP }],
    });

    // ── Fargate Service ──

    const fargateService = new ecs.FargateService(this, 'Service', {
      cluster,
      taskDefinition,
      desiredCount: 1,
      assignPublicIp: true,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [fargateSg],
      minHealthyPercent: 100,
      maxHealthyPercent: 200,
      circuitBreaker: { enable: true, rollback: true },
      healthCheckGracePeriod: cdk.Duration.seconds(60),
      platformVersion: ecs.FargatePlatformVersion.LATEST,
    });

    // ── ALB ──

    const alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      vpc,
      internetFacing: true,
      securityGroup: albSg,
    });

    const httpListener = alb.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      open: false,
    });

    const targetGroup = httpListener.addTargets('FargateTarget', {
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [fargateService],
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 3,
        unhealthyThresholdCount: 3,
      },
    });

    targetGroup.setAttribute('deregistration_delay.timeout_seconds', '30');

    // ── Outputs ──

    new cdk.CfnOutput(this, 'AlbDnsName', {
      value: alb.loadBalancerDnsName,
      description: 'ALB DNS name — set as VITE_API_URL in Amplify',
    });

    new cdk.CfnOutput(this, 'EcrRepoUri', {
      value: repository.repositoryUri,
      description: 'ECR repository URI',
    });

    new cdk.CfnOutput(this, 'AppSecretArn', {
      value: appSecret.secretArn,
      description: 'ARN of the application secret (update OPENAI_API_KEY here)',
    });
  }
}
