"""
Parameter Extractor Tool for the FinOps Supervisor Agent.

This tool extracts relevant parameters from user messages, such as time ranges,
service names, and other query-specific information.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from strands_agents.tools import Tool

# Configure logging
logger = logging.getLogger(__name__)

class ParameterExtractorTool(Tool):
    """
    Tool for extracting parameters from user messages.
    
    This tool analyzes the user's message to extract relevant parameters
    such as time ranges, AWS service names, and other query-specific information.
    """
    
    name = "parameter_extractor"
    description = "Extracts relevant parameters from user messages for cost analysis and optimization"
    
    # AWS service names for recognition
    AWS_SERVICES = [
        "EC2", "S3", "RDS", "Lambda", "DynamoDB", "ECS", "EKS", "Fargate",
        "CloudFront", "API Gateway", "SQS", "SNS", "Kinesis", "Glue", "EMR",
        "Redshift", "ElastiCache", "OpenSearch", "MSK", "EFS", "FSx",
        "Route 53", "CloudWatch", "IAM", "KMS", "Secrets Manager", "ELB",
        "ALB", "NLB", "VPC", "Direct Connect", "Storage Gateway", "Backup",
        "Elastic Beanstalk", "AppSync", "Amplify", "Cognito", "SageMaker"
    ]
    
    # Time period keywords
    TIME_PERIODS = {
        "today": {"days": 0, "period_type": "day"},
        "yesterday": {"days": -1, "period_type": "day"},
        "this week": {"days": -7, "period_type": "week"},
        "last week": {"days": -14, "period_type": "week", "offset": -7},
        "this month": {"months": 0, "period_type": "month"},
        "last month": {"months": -1, "period_type": "month"},
        "this quarter": {"months": 0, "period_type": "quarter"},
        "last quarter": {"months": -3, "period_type": "quarter"},
        "this year": {"months": 0, "period_type": "year"},
        "last year": {"months": -12, "period_type": "year"},
        "past 7 days": {"days": -7, "period_type": "custom"},
        "past 30 days": {"days": -30, "period_type": "custom"},
        "past 90 days": {"days": -90, "period_type": "custom"},
        "past 12 months": {"months": -12, "period_type": "custom"},
        "ytd": {"period_type": "ytd"},
        "year to date": {"period_type": "ytd"}
    }
    
    # Month names for date parsing
    MONTHS = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    def _run(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract parameters from the user message.
        
        Args:
            message: The user's message
            context: Optional context information including conversation history
            
        Returns:
            Dict containing extracted parameters
        """
        logger.info(f"Extracting parameters from message: {message[:50]}...")
        
        # Initialize result dictionary
        result = {
            "time_range": self._extract_time_range(message, context),
            "services": self._extract_services(message),
            "granularity": self._extract_granularity(message),
            "filters": self._extract_filters(message),
            "comparison": self._extract_comparison(message),
            "limit": self._extract_limit(message)
        }
        
        logger.info(f"Extracted parameters: {result}")
        return result
    
    def _extract_time_range(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract time range information from the message.
        
        Args:
            message: The user's message
            context: Optional context information
            
        Returns:
            Dict containing time range information
        """
        message_lower = message.lower()
        
        # Check for predefined time periods
        for period, info in self.TIME_PERIODS.items():
            if period in message_lower:
                return self._calculate_time_range(info)
        
        # Check for specific months or quarters
        time_range = self._extract_specific_period(message_lower)
        if time_range:
            return time_range
        
        # Check for date ranges in format "from X to Y"
        date_range_match = re.search(r'from\s+(.+?)\s+to\s+(.+?)(?:\s|$|\.|\?)', message_lower)
        if date_range_match:
            start_date_str = date_range_match.group(1)
            end_date_str = date_range_match.group(2)
            try:
                start_date = self._parse_date_string(start_date_str)
                end_date = self._parse_date_string(end_date_str)
                if start_date and end_date:
                    return {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "period_type": "custom"
                    }
            except Exception as e:
                logger.warning(f"Error parsing date range: {str(e)}")
        
        # Default to current month if no time range is specified
        return self._calculate_time_range({"months": 0, "period_type": "month"})
    
    def _calculate_time_range(self, period_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate start and end dates based on period information.
        
        Args:
            period_info: Information about the time period
            
        Returns:
            Dict containing start_date and end_date as ISO format strings
        """
        today = datetime.now()
        start_date = None
        end_date = None
        
        if period_info["period_type"] == "day":
            if "days" in period_info:
                date = today + timedelta(days=period_info["days"])
                start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
                end_date = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        elif period_info["period_type"] == "week":
            # Get the start of the current week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            start_date = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0)
            
            if "days" in period_info:
                start_date = start_date + timedelta(days=period_info["days"])
            
            if "offset" in period_info:
                start_date = start_date + timedelta(days=period_info["offset"])
            
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        elif period_info["period_type"] == "month":
            if "months" in period_info:
                # Calculate months offset
                year_offset = period_info["months"] // 12
                month_offset = period_info["months"] % 12
                
                month = today.month + month_offset
                year = today.year + year_offset
                
                if month <= 0:
                    month += 12
                    year -= 1
                elif month > 12:
                    month -= 12
                    year += 1
                
                start_date = datetime(year, month, 1, 0, 0, 0)
                
                # Calculate the last day of the month
                if month == 12:
                    end_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
                else:
                    end_date = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        elif period_info["period_type"] == "quarter":
            if "months" in period_info:
                # Calculate the current quarter
                current_quarter = (today.month - 1) // 3 + 1
                quarter_offset = period_info["months"] // 3
                
                target_quarter = current_quarter + quarter_offset
                year_offset = target_quarter // 4
                
                if target_quarter <= 0:
                    target_quarter += 4
                    year_offset -= 1
                elif target_quarter > 4:
                    target_quarter -= 4
                    year_offset += 1
                
                start_month = (target_quarter - 1) * 3 + 1
                start_date = datetime(today.year + year_offset, start_month, 1, 0, 0, 0)
                
                if start_month + 3 > 12:
                    end_date = datetime(today.year + year_offset + 1, (start_month + 3) % 12, 1, 0, 0, 0) - timedelta(seconds=1)
                else:
                    end_date = datetime(today.year + year_offset, start_month + 3, 1, 0, 0, 0) - timedelta(seconds=1)
        
        elif period_info["period_type"] == "year":
            if "months" in period_info:
                year_offset = period_info["months"] // 12
                start_date = datetime(today.year + year_offset, 1, 1, 0, 0, 0)
                end_date = datetime(today.year + year_offset, 12, 31, 23, 59, 59)
        
        elif period_info["period_type"] == "ytd":
            start_date = datetime(today.year, 1, 1, 0, 0, 0)
            end_date = datetime(today.year, today.month, today.day, 23, 59, 59)
        
        elif period_info["period_type"] == "custom":
            if "days" in period_info:
                end_date = today
                start_date = end_date + timedelta(days=period_info["days"])
            elif "months" in period_info:
                end_date = today
                
                # Calculate months offset
                year_offset = period_info["months"] // 12
                month_offset = period_info["months"] % 12
                
                month = today.month + month_offset
                year = today.year + year_offset
                
                if month <= 0:
                    month += 12
                    year -= 1
                elif month > 12:
                    month -= 12
                    year += 1
                
                start_date = datetime(year, month, today.day, 0, 0, 0)
        
        # If we couldn't determine the dates, default to current month
        if not start_date or not end_date:
            start_date = datetime(today.year, today.month, 1, 0, 0, 0)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period_type": period_info["period_type"]
        }
    
    def _extract_specific_period(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract specific month, quarter, or year mentions.
        
        Args:
            message: The user's message in lowercase
            
        Returns:
            Dict containing time range information or None if not found
        """
        today = datetime.now()
        
        # Check for specific month mentions (e.g., "January 2023")
        for month_name, month_num in self.MONTHS.items():
            # Look for "month year" pattern
            pattern = rf'{month_name}\s+(\d{{4}})'
            match = re.search(pattern, message)
            if match:
                year = int(match.group(1))
                start_date = datetime(year, month_num, 1, 0, 0, 0)
                if month_num == 12:
                    end_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
                else:
                    end_date = datetime(year, month_num + 1, 1, 0, 0, 0) - timedelta(seconds=1)
                
                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_type": "month"
                }
            
            # Look for just month name (assume current year)
            if re.search(rf'\b{month_name}\b', message):
                year = today.year
                # If the mentioned month is ahead of current month, assume last year
                if month_num > today.month:
                    year -= 1
                
                start_date = datetime(year, month_num, 1, 0, 0, 0)
                if month_num == 12:
                    end_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
                else:
                    end_date = datetime(year, month_num + 1, 1, 0, 0, 0) - timedelta(seconds=1)
                
                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_type": "month"
                }
        
        # Check for specific quarter mentions (e.g., "Q1 2023")
        quarter_match = re.search(r'q(\d)\s+(\d{4})', message)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            year = int(quarter_match.group(2))
            
            if 1 <= quarter <= 4:
                start_month = (quarter - 1) * 3 + 1
                start_date = datetime(year, start_month, 1, 0, 0, 0)
                
                if start_month + 3 > 12:
                    end_date = datetime(year + 1, (start_month + 3) % 12, 1, 0, 0, 0) - timedelta(seconds=1)
                else:
                    end_date = datetime(year, start_month + 3, 1, 0, 0, 0) - timedelta(seconds=1)
                
                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_type": "quarter"
                }
        
        # Check for specific year mentions (e.g., "2023")
        year_match = re.search(r'\b(20\d{2})\b', message)
        if year_match:
            year = int(year_match.group(1))
            start_date = datetime(year, 1, 1, 0, 0, 0)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period_type": "year"
            }
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        
        Args:
            date_str: String representation of a date
            
        Returns:
            datetime object or None if parsing fails
        """
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Check for month name
        for month_name, month_num in self.MONTHS.items():
            if month_name in date_str.lower():
                # Try to extract day and year
                day_match = re.search(r'\b(\d{1,2})\b', date_str)
                year_match = re.search(r'\b(20\d{2})\b', date_str)
                
                day = int(day_match.group(1)) if day_match else 1
                year = int(year_match.group(1)) if year_match else datetime.now().year
                
                try:
                    return datetime(year, month_num, day)
                except ValueError:
                    continue
        
        return None
    
    def _extract_services(self, message: str) -> List[str]:
        """
        Extract AWS service names from the message.
        
        Args:
            message: The user's message
            
        Returns:
            List of AWS service names mentioned in the message
        """
        message_upper = message.upper()
        mentioned_services = []
        
        for service in self.AWS_SERVICES:
            service_upper = service.upper()
            # Check for exact service name match
            if re.search(rf'\b{service_upper}\b', message_upper):
                mentioned_services.append(service)
        
        return mentioned_services
    
    def _extract_granularity(self, message: str) -> str:
        """
        Extract time granularity from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Granularity string (DAILY, MONTHLY, HOURLY)
        """
        message_lower = message.lower()
        
        if re.search(r'\b(hourly|per hour|by hour)\b', message_lower):
            return "HOURLY"
        elif re.search(r'\b(daily|per day|by day|day by day)\b', message_lower):
            return "DAILY"
        elif re.search(r'\b(monthly|per month|by month|month by month)\b', message_lower):
            return "MONTHLY"
        
        # Default to DAILY
        return "DAILY"
    
    def _extract_filters(self, message: str) -> List[Dict[str, Any]]:
        """
        Extract filters from the message.
        
        Args:
            message: The user's message
            
        Returns:
            List of filter dictionaries
        """
        filters = []
        message_lower = message.lower()
        
        # Check for region filters
        region_match = re.search(r'(in|for) (region|regions) ([\w\s,-]+)', message_lower)
        if region_match:
            regions_str = region_match.group(3)
            regions = [r.strip() for r in re.split(r'[,\s]+and\s+', regions_str)]
            filters.append({
                "dimension": "REGION",
                "values": regions,
                "operator": "EQUALS"
            })
        
        # Check for instance type filters
        instance_match = re.search(r'(instance type|instance types) ([\w\s,-]+)', message_lower)
        if instance_match:
            instance_types_str = instance_match.group(2)
            instance_types = [t.strip() for t in re.split(r'[,\s]+and\s+', instance_types_str)]
            filters.append({
                "dimension": "INSTANCE_TYPE",
                "values": instance_types,
                "operator": "EQUALS"
            })
        
        # Check for tag filters
        tag_match = re.search(r'tag[s]? ([\w-]+)[=:]([\w\s-]+)', message_lower)
        if tag_match:
            tag_key = tag_match.group(1)
            tag_value = tag_match.group(2).strip()
            filters.append({
                "dimension": f"TAG:{tag_key}",
                "values": [tag_value],
                "operator": "EQUALS"
            })
        
        return filters
    
    def _extract_comparison(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract comparison information from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dict with comparison information or None if not found
        """
        message_lower = message.lower()
        
        # Check for comparison keywords
        comparison_match = re.search(r'compare (?:with|to) ([\w\s]+)', message_lower)
        if comparison_match:
            comparison_period = comparison_match.group(1).strip()
            
            # Try to extract time range for the comparison period
            for period, info in self.TIME_PERIODS.items():
                if period in comparison_period:
                    return {
                        "type": "time_period",
                        "period": period,
                        "time_range": self._calculate_time_range(info)
                    }
            
            # Check for specific periods
            time_range = self._extract_specific_period(comparison_period)
            if time_range:
                return {
                    "type": "time_period",
                    "period": comparison_period,
                    "time_range": time_range
                }
        
        # Check for service comparison
        service_comparison_match = re.search(r'compare ([\w\s]+) (?:with|to|and) ([\w\s]+)', message_lower)
        if service_comparison_match:
            service1 = service_comparison_match.group(1).strip()
            service2 = service_comparison_match.group(2).strip()
            
            # Check if these match AWS service names
            services1 = [s for s in self.AWS_SERVICES if s.lower() in service1]
            services2 = [s for s in self.AWS_SERVICES if s.lower() in service2]
            
            if services1 and services2:
                return {
                    "type": "service_comparison",
                    "services": [services1[0], services2[0]]
                }
        
        return None
    
    def _extract_limit(self, message: str) -> Optional[int]:
        """
        Extract result limit from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Limit as integer or None if not found
        """
        message_lower = message.lower()
        
        # Check for limit patterns
        limit_match = re.search(r'(top|bottom|first|last) (\d+)', message_lower)
        if limit_match:
            return int(limit_match.group(2))
        
        return None
