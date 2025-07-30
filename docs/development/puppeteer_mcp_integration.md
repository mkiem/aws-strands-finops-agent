# Puppeteer MCP Server Integration

## Overview

The Puppeteer MCP server has been successfully integrated with the AWS FinOps Agent project to provide browser automation capabilities for web-based cost analysis and monitoring.

## Configuration Details

### MCP Server Configuration
- **Server Name**: `puppeteer`
- **Package**: `@modelcontextprotocol/server-puppeteer`
- **Version**: 2025.5.12 (latest)
- **Execution Method**: NPX (no local installation required)
- **Mode**: Headless (optimized for EC2 environment)

### Environment Settings
```json
{
  "FASTMCP_LOG_LEVEL": "ERROR",
  "PUPPETEER_LAUNCH_OPTIONS": "{\"headless\": true, \"args\": [\"--no-sandbox\", \"--disable-dev-shm-usage\", \"--disable-gpu\"]}",
  "ALLOW_DANGEROUS": "true"
}
```

### Headless Configuration Rationale
- `headless: true` - No visible browser window (suitable for EC2)
- `--no-sandbox` - Required for containerized/server environments
- `--disable-dev-shm-usage` - Prevents shared memory issues on Linux
- `--disable-gpu` - Disables GPU acceleration (not needed in headless mode)

## Available Tools

The integration provides access to these browser automation tools:

### Navigation & Control
- `puppeteer_navigate` - Navigate to URLs with custom launch options
- `puppeteer_click` - Click elements using CSS selectors
- `puppeteer_hover` - Hover over page elements
- `puppeteer_fill` - Fill input fields and forms
- `puppeteer_select` - Select dropdown options

### Data Capture & Analysis
- `puppeteer_screenshot` - Capture full page or element screenshots
- `puppeteer_evaluate` - Execute custom JavaScript code in browser context

### Resources Access
- `console://logs` - Access browser console output and error logs
- `screenshot://<name>` - Access captured screenshots by name

## Security Considerations

⚠️ **Important Security Notes:**
- Server can access local files and internal network addresses
- Running with `--no-sandbox` reduces security isolation
- `ALLOW_DANGEROUS: true` permits potentially risky browser arguments
- Only use with trusted websites and validated scripts
- Consider implementing network restrictions for production deployments

## Integration with FinOps Workflows

### Potential Use Cases
1. **AWS Console Automation**
   - Automate navigation through AWS Cost Explorer
   - Extract cost data from AWS billing dashboards
   - Monitor cost anomalies via web interfaces

2. **Third-Party Tool Integration**
   - Automate interaction with vendor billing portals
   - Extract data from third-party cost management tools
   - Monitor SaaS application usage dashboards

3. **Report Generation**
   - Capture screenshots of cost dashboards for reports
   - Generate visual documentation of cost trends
   - Create automated cost review presentations

4. **Monitoring & Alerting**
   - Automated checks of cost thresholds via web interfaces
   - Monitor for billing anomalies in web dashboards
   - Extract real-time cost data for analysis

### Example Workflow Patterns
```
Navigate to AWS Cost Explorer 
→ Take screenshot of current month costs
→ Execute JavaScript to extract cost data
→ Process data through FinOps agents
→ Generate insights and recommendations
```

## System Requirements Met
- ✅ Node.js v20.19.2 (compatible)
- ✅ NPX v10.8.2 (latest)
- ✅ Amazon Linux 2023 (supported)
- ✅ Headless environment configuration
- ✅ MCP integration configured

## Testing & Validation

### Basic Functionality Test
To test the integration, you can use these example commands through Amazon Q:
1. Navigate to a simple webpage
2. Take a screenshot
3. Extract page title using JavaScript
4. Access console logs

### Troubleshooting
- **Chrome Download Issues**: First run may download Chrome headless shell (~100MB)
- **Memory Issues**: Monitor `/tmp` space usage during operation
- **Network Access**: Ensure outbound HTTPS access for web navigation
- **Timeout Issues**: Increase timeout for complex page loads

## Maintenance & Updates

### Automatic Updates
- NPX automatically uses latest package version
- No manual updates required
- Package maintained by Anthropic/ModelContextProtocol team

### Monitoring
- Monitor Chrome process memory usage
- Watch for failed navigation attempts
- Check console logs for JavaScript errors
- Validate screenshot capture functionality

## Next Steps

1. **Test Basic Functionality**: Verify navigation and screenshot capabilities
2. **Develop FinOps Scripts**: Create automation scripts for AWS cost analysis
3. **Integration Testing**: Test with existing FinOps agent workflows
4. **Performance Optimization**: Monitor resource usage and optimize settings
5. **Security Review**: Implement additional security measures for production use

## Configuration Backup

A backup of the previous MCP configuration has been saved to:
`~/.aws/amazonq/mcp.json.backup`

To restore the previous configuration if needed:
```bash
cp ~/.aws/amazonq/mcp.json.backup ~/.aws/amazonq/mcp.json
```
