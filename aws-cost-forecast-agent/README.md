# FinOps Agent Response Formatting

This document explains the implementation of structured response formatting for the FinOps Agent.

## Overview

The FinOps Agent now uses Strands content blocks to format responses in a more user-friendly way. This implementation:

1. Extracts cost data from the agent's responses
2. Structures the data with clear headings and formatting
3. Presents the information in a consistent, readable format

## Implementation Details

### Content Blocks

The agent uses Strands content blocks to structure responses. Each block contains a piece of formatted text that can include markdown formatting:

```python
content_blocks = [
    {"text": f"# Amazon S3 Cost Summary\n\n"},
    {"text": f"## Total Cost: ${cost_value:.2f} {currency}\n\n"},
    {"text": f"**Time Period**: {start_date} to {end_date}\n\n"},
    {"text": f"**Usage**: {format(usage_units, ',')} units\n\n"},
    {"text": f"---\n\n"},
    {"text": f"Additional information and context...\n\n"}
]
```

### Data Extraction

The implementation includes a function to extract cost data from the agent's responses:

```python
def extract_cost_data(response_text: str) -> Dict[str, Any]:
    # Extract cost value, date range, usage units, and service name
    # from the response text using regular expressions
    ...
```

### Response Formatting

The `format_cost_response` function creates a well-structured response with proper headers and content blocks:

```python
def format_cost_response(
    query: str,
    response_text: str,
    cost_value: float,
    currency: str = "USD",
    start_date: str = "",
    end_date: str = "",
    usage_units: int = 0,
    service_name: str = ""
) -> Dict[str, Any]:
    # Create structured content blocks
    ...
```

## Testing

You can test the formatting using the included `test_formatting.py` script:

```bash
cd /home/ec2-user/projects/finopsAgent/my_agent
python test_formatting.py
```

This will simulate a request to the Lambda handler and display the formatted response.

## Example Response

A formatted response for an S3 cost query looks like:

```
# Amazon S3 Cost Summary

## Total Cost: $0.07 USD

**Time Period**: 2025-06-01 to 2025-06-09 (first 9 days of June 2025)

**Usage**: 196,336 units

---

This represents your Amazon Simple Storage Service (S3) costs for approximately the first 9 days of June 2025.

Would you like me to provide any cost optimization recommendations for your S3 usage, or do you need information about specific aspects of your S3 spending?
```

## Next Steps

1. Enhance the data extraction to handle more complex cost queries
2. Add visualization capabilities (charts, graphs) for cost data
3. Implement more sophisticated formatting for different query types
