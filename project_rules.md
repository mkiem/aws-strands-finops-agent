The following project rules is pre-pended to the user prompt.
<project-rules>
- Use Strands SDK as the core development framework, refer to the STRANDS_SDK_README.md, STRANDS_SDK_GUIDE.md, and STRANDS_QUICK_REFERENCE.md at the root project directory
- Use Python 3.10 and above when developing in Python
- Adhere to usage of Material UI for our front-end - https://mui.com/material-ui/ 
- When building FinOps-UI, always package all files at the ROOT, do not include in a BUILD folder.
- Do not change user interface unless explicity told to do so. When updating UI, only make changes that interact with the back-end unless otherwise stated. 
- Agents should always return clean markdown and NOT content blocks for front-end to process!
- Use Puppeteer MCP server for testing front-end deployments, making use of console logs and screenshots to resolve issues.
- When building a deployment package, always keep it in the same folder as the main application file project folder
- When building a deployment package, use what's in the local environment to avoid issues, reference design_document.md or readme.md for notes
- Do not deploy to AWS, simply package it up for manual deployment, unless explicity told to deploy
- When deploying an application, check what's already deployed first, then make decision to deploy new or an update
- Make sure to update the README.md with deployed resources so you can reference it later
- Prefer CloudFormation for IAC into AWS (exception made for Lambda, use CDK)
- Keep services / capabilities self contained in its own folder that is self-encompassing for portability like a microservice
- Name the Cloudformation scripts to be self-evident, that matches the application
- All Cloudformation deployment packages should be stored in this S3 bucket: "finops-deployment-packages-062025"
- MCP refer to Model Context Protocol (https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- When you troubleshoot and can't fix the issue, use the AWS Documentation MCP Server to research or use CURL to research websites for the latest information
- Use CURL to research websites
- Use AWS Documentation MCP Tool to research AWS services
- You can start a python virutal environmeny with: source .venv/bin/activate
- If you run into a recurring issue, once you solve it, make sure to document the resolution so you don't make the same mistake
- reference websocket_api/websocet_api.md as needed to understand implementation rules
- development best practice: think step by step and: 1. Review documentation. 2. Design and plan implementation plan. 3. Execute implementation plan. 4. Update/modify project progress in README.md
</project-rules>
The user prompt begins now: