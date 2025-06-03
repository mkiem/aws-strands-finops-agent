# Build a FinOps agent using Amazon Bedrock with multi-agent capability and
Amazon Nova as the foundation model

by Salman Ahmed, Ankush Goyal, Sergio Barraza, and Ravi Kumar on 18 APR 2025
in [Advanced (300)](https://aws.amazon.com/blogs/machine-
learning/category/learning-levels/advanced-300/ "View all posts in Advanced
\(300\)"), [Amazon Bedrock](https://aws.amazon.com/blogs/machine-
learning/category/artificial-intelligence/amazon-machine-learning/amazon-
bedrock/ "View all posts in Amazon Bedrock"), [Amazon
Cognito](https://aws.amazon.com/blogs/machine-learning/category/security-
identity-compliance/amazon-cognito/ "View all posts in Amazon Cognito"),
[Amazon Machine Learning](https://aws.amazon.com/blogs/machine-
learning/category/artificial-intelligence/amazon-machine-learning/ "View all
posts in Amazon Machine Learning"), [Amazon
Nova](https://aws.amazon.com/blogs/machine-learning/category/artificial-
intelligence/amazon-machine-learning/amazon-bedrock/amazon-nova/ "View all
posts in Amazon Nova"), [Artificial
Intelligence](https://aws.amazon.com/blogs/machine-
learning/category/artificial-intelligence/ "View all posts in Artificial
Intelligence"), [AWS Amplify](https://aws.amazon.com/blogs/machine-
learning/category/mobile-services/aws-amplify/ "View all posts in AWS
Amplify"), [AWS Cost Explorer](https://aws.amazon.com/blogs/machine-
learning/category/aws-cloud-financial-management/aws-cost-explorer/ "View all
posts in AWS Cost Explorer"), [AWS
Lambda](https://aws.amazon.com/blogs/machine-learning/category/compute/aws-
lambda/ "View all posts in AWS Lambda"), [AWS Trusted
Advisor](https://aws.amazon.com/blogs/machine-learning/category/management-
tools/aws-trusted-advisor/ "View all posts in AWS Trusted Advisor")
[Permalink](https://aws.amazon.com/blogs/machine-learning/build-a-finops-
agent-using-amazon-bedrock-with-multi-agent-capability-and-amazon-nova-as-the-
foundation-model/) [__Comments](https://aws.amazon.com/blogs/machine-
learning/build-a-finops-agent-using-amazon-bedrock-with-multi-agent-
capability-and-amazon-nova-as-the-foundation-model/#Comments) Share

AI agents are revolutionizing how businesses enhance their operational
capabilities and enterprise applications. By enabling natural language
interactions, these agents provide customers with a streamlined, personalized
experience. [Amazon Bedrock Agents](https://aws.amazon.com/bedrock/agents/)
uses the capabilities of foundation models (FMs), combining them with APIs and
data to process user requests, gather information, and execute specific tasks
effectively. The introduction of multi-agent collaboration now enables
organizations to orchestrate multiple specialized AI agents working together
to tackle complex, multi-step challenges that require diverse expertise.

[Amazon Bedrock](https://aws.amazon.com/bedrock/) offers a diverse selection
of FMs, allowing you to choose the one that best fits your specific use case.
Among these offerings, [Amazon Nova](https://aws.amazon.com/ai/generative-
ai/nova/) stands out as AWS’s next-generation FM, delivering breakthrough
intelligence and industry-leading performance at exceptional value.

The Amazon Nova family comprises three types of models:

  * **Understanding models** – Available in Micro, Lite, and Pro variants
  * **Content generation models** – Featuring Canvas and Reel
  * **Speech-to-Speech model** – Nova Sonic

These models are specifically optimized for enterprise and business
applications, excelling in the following capabilities:

  * Text generation
  * Summarization
  * Complex reasoning tasks
  * Content creation

This makes Amazon Nova ideal for sophisticated use cases like our FinOps
solution.

A key advantage of the Amazon Nova model family is its [industry-leading
price-performance](https://aws.amazon.com/blogs/aws/introducing-amazon-nova-
frontier-intelligence-and-industry-leading-price-performance/) ratio. Compared
to other enterprise-grade AI models, Amazon Nova offers comparable or superior
capabilities at a more competitive price point. This cost-effectiveness,
combined with its versatility and performance, makes Amazon Nova an attractive
choice for businesses looking to implement advanced AI solutions.

In this post, we use the [multi-
agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-
agent-collaboration.html) feature of Amazon Bedrock to demonstrate a powerful
and innovative approach to AWS cost management. By using the advanced
capabilities of Amazon Nova FMs, we’ve developed a solution that showcases how
AI-driven agents can revolutionize the way organizations analyze, optimize,
and manage their AWS costs.

## Solution overview

Our innovative AWS cost management solution uses the power of AI and multi-
agent collaboration to provide comprehensive cost analysis and optimization
recommendations. The core of the system is built around three key components:

  * **FinOps supervisor agent** – Acts as the central coordinator, managing user queries and orchestrating the activities of specialized subordinate agents
  * **Cost analysis agent** – Uses [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to gather and analyze cost data for specified time ranges
  * **Cost optimization agent** – Uses the [AWS Trusted Advisor](https://aws.amazon.com/premiumsupport/technology/trusted-advisor/) Cost Optimization Pillar to provide actionable cost-saving recommendations

The solution integrates the multi-agent collaboration capabilities of Amazon
Bedrock with Amazon Nova to create an intelligent, interactive, cost
management AI assistant. This integration enables seamless communication
between specialized agents, each focusing on different aspects of AWS cost
management. Key features of the solution include:

  * User authentication through [Amazon Cognito](https://aws.amazon.com/cognito/) with [role-based access control](https://docs.aws.amazon.com/cognito/latest/developerguide/role-based-access-control.html)
  * Frontend application hosted on [AWS Amplify](https://aws.amazon.com/amplify/)
  * Real-time cost insights and historical analysis
  * Actionable cost optimization recommendations
  * Parallel processing of tasks for improved efficiency

By combining AI-driven analysis with AWS cost management tools, this solution
offers finance teams and cloud administrators a powerful, user-friendly
interface to gain deep insights into AWS spending patterns and identify cost-
saving opportunities.

The architecture displayed in the following diagram uses several AWS services,
including [AWS Lambda](https://aws.amazon.com/lambda/) functions, to create a
scalable, secure, and efficient system. This approach demonstrates the
potential of AI-driven multi-agent systems to assist with cloud financial
management and solve a wide range of cloud management challenges.

[![Solutions Overview - FinOps Amazon Bedrock Multi
Agent](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/1-SolutionsOverview-
FinOps-AmazonBedrock-
MultiAgent.png)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/1-SolutionsOverview-
FinOps-AmazonBedrock-MultiAgent.png)

In the following sections, we dive deeper into the architecture of our
solution, explore the capabilities of each agent, and discuss the potential
impact of this approach on AWS cost management strategies.

## Prerequisites

You must have the following in place to complete the solution in this post:

  * An [AWS account](https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fportal.aws.amazon.com%2Fbilling%2Fsignup%2Fresume&client_id=signup)
  * FM [access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) in Amazon Bedrock for Amazon Nova Pro and Micro in the same [AWS Region](https://docs.aws.amazon.com/glossary/latest/reference/glos-chap.html#region) where you will deploy this solution
  * The accompanying [AWS CloudFormation](http://aws.amazon.com/cloudformation) template downloaded from the [aws-samples GitHub repo](https://github.com/aws-samples/sample-finops-bedrock-multiagent-nova)

## Deploy solution resources using AWS CloudFormation

This CloudFormation template is designed to run in the us-east-1 Region. If
you deploy in a different Region, you must configure cross-Region [inference
profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-
profiles-create.html) to have proper functionality and update the
CloudFormation template accordingly.

During the CloudFormation template deployment, you will need to specify three
required parameters:

  * Stack name
  * FM selection
  * Valid user email address

AWS resource usage will incur costs. When deployment is complete, the
following resources will be deployed:

  * Amazon Cognito resources: 
    * [User pool](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html) – `CognitoUserPoolforFinOpsApp`
    * [App client](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html) – `FinOpsApp`
    * [Identity pool](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools.html) – `cognito-identity-pool-finops`
    * [Groups](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-user-groups.html) – Finance
    * [User](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-users.html) – Finance User
  * [AWS Identity and Access Management](https://aws.amazon.com/iam/) (IAM) resources: 
    * [IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html): 
      * `FinanceUserRestrictedRole`
      * `DefaultCognitoAuthenticatedRole`
    * [IAM policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html): 
      * `Finance-BedrockAccess`
      * `Default-CognitoAccess`
    * Lambda functions: 
      * `TrustedAdvisorListRecommendationResources`
      * `TrustedAdvisorListRecommendations`
      * `CostAnalysis`
      * `ClockandCalendar`
      * `CostForecast`
    * Amazon Bedrock agents: 
      * `FinOpsSupervisorAgent`
      * `CostAnalysisAgent` with action groups: 
        * `CostAnalysisActionGroup`
        * `ClockandCalendarActionGroup`
        * `CostForecastActionGroup`
      * `CostOptimizationAgent` with action groups: 
        * `TrustedAdvisorListRecommendationResources`
        * `TrustedAdvisorListRecommendations`

After you deploy the CloudFormation template, copy the following from the
**Outputs** tab on the AWS CloudFormation console to use during the
configuration of your application after it’s deployed in Amplify:

  * `AWSRegion`
  * `BedrockAgentAliasId`
  * `BedrockAgentId`
  * `BedrockAgentName`
  * `IdentityPoolId`
  * `UserPoolClientId`
  * `UserPoolId`

The following screenshot shows you what the **Outputs** tab will look like.

[![FinOps CloudFormation
Output](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/2-FinOps-
CloudFormation-
Output.png)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/2-FinOps-
CloudFormation-Output.png)

## Deploy the Amplify application

You need to manually deploy the Amplify application using the frontend code
found on GitHub. Complete the following steps:

  1. Download the frontend code `AWS-Amplify-Frontend.zip` from [GitHub](https://github.com/aws-samples/sample-finops-bedrock-multiagent-nova).
  2. Use the .zip file to manually [deploy](https://docs.aws.amazon.com/amplify/latest/userguide/manual-deploys.html) the application in Amplify.
  3. Return to the Amplify page and use the domain it automatically generated to access the application.

## Amazon Cognito for user authentication

The FinOps application uses Amazon Cognito user pools and identity pools to
implement secure, role-based access control for finance team members. User
pools handle authentication and group management, and identity pools provide
temporary AWS credentials mapped to specific IAM roles. The system makes sure
that only verified finance team members can access the application and
interact with the Amazon Bedrock API, combining robust security with a
seamless user experience.

## Amazon Bedrock Agents with multi-agent capability

The Amazon Bedrock multi-agent architecture enables sophisticated FinOps
problem-solving through a coordinated system of AI agents, led by a
`FinOpsSupervisorAgent`. The `FinOpsSupervisorAgent` coordinates with two key
subordinate agents: the `CostAnalysisAgent`, which handles detailed cost
analysis queries, and the `CostOptimizationAgent`, which handles specific cost
optimization recommendations. Each agent focuses on their specialized
financial tasks while maintaining contextual awareness, with the
`FinOpsSupervisorAgent` managing communication and synthesizing comprehensive
responses from both agents. This coordinated approach enables parallel
processing of financial queries and delivers more effective answers than a
single agent could provide, while maintaining consistency and accuracy
throughout the FinOps interaction.

## Lambda functions for Amazon Bedrock action groups

As part of this solution, Lambda functions are deployed to support the action
groups defined for each subordinate agent.

The `CostAnalysisAgent` uses three distinct Lambda backed action groups to
deliver comprehensive cost management capabilities. The
`CostAnalysisActionGroup` connects with Cost Explorer to extract and analyze
detailed historical cost data, providing granular insights into cloud spending
patterns and resource utilization. The `ClockandCalendarActionGroup` maintains
temporal precision by providing current date and time functionality, essential
for accurate period-based cost analysis and reporting. The
`CostForecastActionGroup` uses the [Cost Explorer
forecasting](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-
forecast.html) function, which analyzes historical cost data and provides
future cost projections. This information helps the agent support proactive
budget planning and make informed recommendations. These action groups work
together seamlessly, enabling the agent to provide historical cost analysis
and future spend predictions while maintaining precise temporal context.

The `CostOptimizationAgent` incorporates two Trusted Advisor focused action
groups to enhance its recommendation capabilities. The
`TrustedAdvisorListRecommendationResources` action group interfaces with
Trusted Advisor to retrieve a comprehensive list of resources that could
benefit from optimization, providing a targeted scope for cost-saving efforts.
Complementing this, the `TrustedAdvisorListRecommendations` action group
fetches specific recommendations from Trusted Advisor, offering actionable
insights on potential cost reductions, performance improvements, and best
practices across various AWS services. Together, these action groups empower
the agent to deliver data-driven, tailored optimization strategies by using
the expertise embedded in Trusted Advisor.

## Amplify for frontend

Amplify provides a streamlined solution for deploying and hosting web
applications with built-in security and scalability features. The service
reduces the complexity of managing infrastructure, allowing developers to
concentrate on application development. In our solution, we use the manual
deployment capabilities of Amplify to host our frontend application code.

## Multi-agent and application walkthrough

To validate the solution before using the Amplify deployed frontend, we can
conduct testing directly on the [AWS Management
Console](http://aws.amazon.com/console). By navigating to the
`FinOpsSupervisorAgent`, we can pose a question like “What is my cost for Feb
2025 and what are my current cost savings opportunity?” This query
demonstrates the multi-agent orchestration in action. As shown in the
following screenshot, the `FinOpsSupervisorAgent` coordinates with both the
`CostAnalysisAgent` (to retrieve February 2025 cost data) and the
`CostOptimizationAgent` (to identify current cost savings opportunities). This
illustrates how the `FinOpsSupervisorAgent` effectively delegates tasks to
specialized agents and synthesizes their responses into a comprehensive
answer, showcasing the solution’s integrated approach to FinOps queries.

[![Amazon Bedrock Agents Console
Demo](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/3-AmazonBedrockAgentsConsoleDemo-
compressed.gif)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/3-AmazonBedrockAgentsConsoleDemo-
compressed.gif)

Navigate to the URL provided after you created the application in Amplify.
Upon accessing the application URL, you will be prompted to provide
information related to Amazon Cognito and Amazon Bedrock Agents. This
information is required to securely authenticate users and allow the frontend
to interact with the Amazon Bedrock agent. It enables the application to
manage user sessions and make authorized API calls to AWS services on behalf
of the user.

You can enter information with the values you collected from the
CloudFormation stack outputs. You will be required to enter the following
fields, as shown in the following screenshot:

  * User Pool ID
  * User Pool Client ID
  * Identity Pool ID
  * Region
  * Agent Name
  * Agent ID
  * Agent Alias ID
  * Region

[![AWS Amplify
Configuration](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/4-AWS-
Amplify-
Configuration-1.png)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/4-AWS-
Amplify-Configuration-1.png)

You need to sign in with your user name and password. A temporary password was
automatically generated during deployment and sent to the email address you
provided when launching the CloudFormation template. At first sign-in attempt,
you will be asked to reset your password, as shown in the following video.

[![Amplify
Login](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/5-AmplifyLogin-1.gif)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/5-AmplifyLogin-1.gif)

Now you can start asking the same question in the application, for example,
“What is my cost for February 2025 and what are my current cost savings
opportunity?” In a few seconds, the application will provide you detailed
results showing services spend for the particular month and savings
opportunity. The following video shows this chat.

[![FinOps Agent Front End Demo
1](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/6-FinOpsAgentFrontEndDemo1-compressed.gif)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/6-FinOpsAgentFrontEndDemo1-compressed.gif)

You can further dive into the details you got by asking a follow-up question
such as “Can you give me the details of the EC2 instances that are
underutilized?” and it will return the details for each of the [Amazon Elastic
Compute Cloud](http://aws.amazon.com/ec2) (Amazon EC2) instances that it found
underutilized.

[![Fin Ops Agent Front End Demo
2](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/7-FinOpsAgentFrontEndDemo2-compressed.gif)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/04/10/7-FinOpsAgentFrontEndDemo2-compressed.gif)

The following are a few additional sample queries to demonstrate the
capabilities of this tool:

  * What is my top services cost in June 2024?
  * In the past 6 months, how much did I spend on VPC cost?
  * What is my current savings opportunity?

## Clean up

If you decide to discontinue using the FinOps application, you can follow
these steps to remove it, its associated resources deployed using AWS
CloudFormation, and the Amplify deployment:

  1. Delete the CloudFormation stack: 
     * On the AWS CloudFormation console, choose **Stacks** in the navigation pane.
     * Locate the stack you created during the deployment process (you assigned a name to it).
     * Select the stack and choose **Delete**.
  2. Delete the Amplify application and its resources. For instructions, refer to [Clean Up Resources](https://aws.amazon.com/getting-started/hands-on/build-web-app-s3-lambda-api-gateway-dynamodb/module-six/).

## Considerations

For optimal visibility across your organization, deploy this solution in your
AWS payer account to access cost details for your linked accounts through Cost
Explorer.

Trusted Advisor cost optimization visibility is limited to the account where
you deploy this solution. To expand its scope,
[enable](https://docs.aws.amazon.com/awssupport/latest/user/organizational-
view.html) Trusted Advisor at the AWS organization level and modify this
solution accordingly.

Before deploying to production, enhance security by implementing additional
safeguards. You can do this by [associating
guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-
guardrail.html) with your agent in Amazon Bedrock.

## Conclusion

The integration of the multi-agent capability of Amazon Bedrock with Amazon
Nova demonstrates the transformative potential of AI in AWS cost management.
Our FinOps agent solution showcases how specialized AI agents can work
together to deliver comprehensive cost analysis, forecasting, and optimization
recommendations in a secure and user-friendly environment. This implementation
not only addresses immediate cost management challenges, but also adapts to
evolving cloud financial operations. As AI technologies advance, this approach
sets a foundation for more intelligent and proactive cloud management
strategies across various business operations.

## Additional resources

To learn more about Amazon Bedrock, refer to the following resources:

  * [Introducing multi-agent collaboration capability for Amazon Bedrock](https://aws.amazon.com/blogs/aws/introducing-multi-agent-collaboration-capability-for-amazon-bedrock/)
  * [Unlocking complex problem-solving with multi-agent collaboration on Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/unlocking-complex-problem-solving-with-multi-agent-collaboration-on-amazon-bedrock/)
  * [Introducing Amazon Nova foundation models: Frontier intelligence and industry leading price performance](https://aws.amazon.com/blogs/aws/introducing-amazon-nova-frontier-intelligence-and-industry-leading-price-performance/)

* * *

### About the Author

**[![Salman
Ahmed](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/salmanah.jpg)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/salmanah.jpg)Salman
Ahmed** is a Senior Technical Account Manager in AWS Enterprise Support. He
specializes in guiding customers through the design, implementation, and
support of AWS solutions. Combining his networking expertise with a drive to
explore new technologies, he helps organizations successfully navigate their
cloud journey. Outside of work, he enjoys photography, traveling, and watching
his favorite sports teams.

**[![Ravi
Kumar](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/vatsravi.jpg)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/vatsravi.jpg)Ravi
Kumar**  is a Senior Technical Account Manager in AWS Enterprise Support who
helps customers in the travel and hospitality industry to streamline their
cloud operations on AWS. He is a results-driven IT professional with over 20
years of experience. In his free time, Ravi enjoys creative activities like
painting. He also likes playing cricket and traveling to new places.

**[![Sergio
Barraza](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/sercast.jpg)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/sercast.jpg)Sergio
Barraza**  is a Senior Technical Account Manager at AWS, helping customers on
designing and optimizing cloud solutions. With more than 25 years in software
development, he guides customers through AWS services adoption. Outside work,
Sergio is a multi-instrument musician playing guitar, piano, and drums, and he
also practices Wing Chun Kung Fu.

**[![Ankush
Goyal](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/goyalaws.jpg)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2024/10/16/goyalaws.jpg)Ankush
Goyal**  is a Enterprise Support Lead in AWS Enterprise Support who helps
customers streamline their cloud operations on AWS. He is a results-driven IT
professional with over 20 years of experience.

Loading comments…

###  Resources

  * [Getting Started](https://aws.amazon.com/getting-started?sc_ichannel=ha&sc_icampaign=acq_awsblogsb&sc_icontent=machine-learning-resources)
  * [What's New](https://aws.amazon.com/new?sc_ichannel=ha&sc_icampaign=acq_awsblogsb&sc_icontent=machine-learning-resources)

* * *

###  Blog Topics

  * [Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-machine-learning/amazon-bedrock/)
  * [Amazon Comprehend](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-comprehend/)
  * [Amazon Kendra](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-kendra/)
  * [Amazon Lex](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-lex/)
  * [Amazon Polly](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-polly/)
  * [Amazon Q](https://aws.amazon.com/blogs/machine-learning/category/amazon-q/)
  * [Amazon Rekognition](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-rekognition/)
  * [Amazon SageMaker](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/sagemaker/)
  * [Amazon Textract](https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-textract/)

* * *

###  Follow

  * [__  Twitter](https://twitter.com/awscloud)
  * [__  Facebook](https://www.facebook.com/amazonwebservices)
  * [__  LinkedIn](https://www.linkedin.com/company/amazon-web-services/)
  * [__  Twitch](https://www.twitch.tv/aws)
  * [__  Email Updates](https://pages.awscloud.com/communication-preferences?sc_ichannel=ha&sc_icampaign=acq_awsblogsb&sc_icontent=maching-learning-social)

[ Sign In to the Console
](https://console.aws.amazon.com/console/home?nc1=f_ct&src=footer-signin-
mobile)

###  Learn About AWS

  * [What Is AWS?](https://aws.amazon.com/what-is-aws/?nc1=f_cc)
  * [What Is Cloud Computing?](https://aws.amazon.com/what-is-cloud-computing/?nc1=f_cc)
  * [AWS Accessibility](https://aws.amazon.com/accessibility/?nc1=f_cc)
  * [What Is DevOps?](https://aws.amazon.com/devops/what-is-devops/?nc1=f_cc)
  * [What Is a Container?](https://aws.amazon.com/containers/?nc1=f_cc)
  * [What Is a Data Lake?](https://aws.amazon.com/what-is/data-lake/?nc1=f_cc)
  * [What is Artificial Intelligence (AI)?](https://aws.amazon.com/what-is/artificial-intelligence/?nc1=f_cc)
  * [What is Generative AI?](https://aws.amazon.com/what-is/generative-ai/?nc1=f_cc)
  * [What is Machine Learning (ML)?](https://aws.amazon.com/what-is/machine-learning/?nc1=f_cc)
  * [AWS Cloud Security](https://aws.amazon.com/security/?nc1=f_cc)
  * [What's New](https://aws.amazon.com/new/?nc1=f_cc)
  * [Blogs](https://aws.amazon.com/blogs/?nc1=f_cc)
  * [Press Releases](https://press.aboutamazon.com/press-releases/aws "Press Releases")

###  Resources for AWS

  * [Getting Started](https://aws.amazon.com/getting-started/?nc1=f_cc)
  * [Training and Certification](https://aws.amazon.com/training/?nc1=f_cc)
  * [AWS Trust Center](https://aws.amazon.com/trust-center/?nc1=f_cc)
  * [AWS Solutions Library](https://aws.amazon.com/solutions/?nc1=f_cc)
  * [Architecture Center](https://aws.amazon.com/architecture/?nc1=f_cc)
  * [Product and Technical FAQs](https://aws.amazon.com/faqs/?nc1=f_dr)
  * [Analyst Reports](https://aws.amazon.com/resources/analyst-reports/?nc1=f_cc)
  * [AWS Partners](https://aws.amazon.com/partners/work-with-partners/?nc1=f_dr)

###  Developers on AWS

  * [Developer Center](https://aws.amazon.com/developer/?nc1=f_dr)
  * [SDKs & Tools](https://aws.amazon.com/developer/tools/?nc1=f_dr)
  * [.NET on AWS](https://aws.amazon.com/developer/language/net/?nc1=f_dr)
  * [Python on AWS](https://aws.amazon.com/developer/language/python/?nc1=f_dr)
  * [Java on AWS](https://aws.amazon.com/developer/language/java/?nc1=f_dr)
  * [PHP on AWS](https://aws.amazon.com/developer/language/php/?nc1=f_cc)
  * [JavaScript on AWS](https://aws.amazon.com/developer/language/javascript/?nc1=f_dr)

###  Help

  * [Contact Us](https://aws.amazon.com/contact-us/?nc1=f_m)
  * [Get Expert Help](https://iq.aws.amazon.com/?utm=mkt.foot/?nc1=f_m)
  * [File a Support Ticket](https://console.aws.amazon.com/support/home/?nc1=f_dr)
  * [AWS re:Post](https://repost.aws/?nc1=f_dr)
  * [Knowledge Center](https://repost.aws/knowledge-center/?nc1=f_dr)
  * [AWS Support Overview](https://aws.amazon.com/premiumsupport/?nc1=f_dr)
  * [Legal](https://aws.amazon.com/legal/?nc1=f_cc)
  * [AWS Careers](https://aws.amazon.com/careers/)
