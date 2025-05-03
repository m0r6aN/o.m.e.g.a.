# examples/weather_agent.py

from typing import Dict, Any, List

from omega.agents.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope
from omega.core.agent_discovery import AgentCapability

class WeatherAgent(RegisterableDualModeAgent):
    """
    Example weather agent that demonstrates the capability discovery system
    """
    
    def __init__(self):
        # Define detailed capabilities
        capabilities = [
            AgentCapability(
                name="get_current_weather",
                description="Get the current weather conditions for a location",
                examples=[
                    "What's the weather like in New York?",
                    "Tell me the current weather in London",
                    "Weather conditions in Tokyo right now"
                ],
                parameters={"location": {"type": "string", "description": "The location to get weather for"}},
                tags=["weather", "current", "conditions"]
            ),
            AgentCapability(
                name="get_weather_forecast",
                description="Get a multi-day weather forecast for a location",
                examples=[
                    "What's the forecast for Paris this week?",
                    "Give me a 5-day forecast for Sydney",
                    "Weather forecast for Chicago"
                ],
                parameters={
                    "location": {"type": "string", "description": "The location to get forecast for"},
                    "days": {"type": "integer", "description": "Number of days in the forecast"}
                },
                tags=["weather", "forecast", "prediction"]
            ),
            AgentCapability(
                name="get_severe_weather_alerts",
                description="Get severe weather alerts and warnings for a location",
                examples=[
                    "Are there any weather alerts for Florida?",
                    "Weather warnings in Colorado",
                    "Severe weather alerts near me"
                ],
                parameters={"location": {"type": "string", "description": "The location to get alerts for"}},
                tags=["weather", "alerts", "warnings", "severe"]
            )
        ]
        
        super().__init__(
            agent_id="weather_agent",
            tool_name="weather",
            description="Provides weather information for locations worldwide",
            version="1.0.0",
            capabilities=capabilities,
            agent_type="agent",
            tags=["weather", "forecast", "meteorology"]
        )
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """Process a task from any source (Redis stream or A2A)"""
        try:
            # Extract input from the task envelope
            input_text = env.input.get("text", "") if env.input else ""
            
            # Check if this is a weather request and parse the location
            if "weather" in input_text.lower() and "in" in input_text.lower():
                location = input_text.split("in", 1)[1].strip().rstrip("?.")
                
                # Mock weather response
                weather_data = self._get_mock_weather(location)
                
                response_text = (
                    f"Current weather in {location}:\n"
                    f"Temperature: {weather_data['temperature']}°F\n"
                    f"Condition: {weather_data['condition']}\n"
                    f"Humidity: {weather_data['humidity']}%\n"
                    f"Wind: {weather_data['wind']}"
                )
                
                env.output = {"text": response_text}
                env.status = "COMPLETED"
                
            # Check if this is a forecast request
            elif "forecast" in input_text.lower() and "in" in input_text.lower():
                location = input_text.split("in", 1)[1].strip().rstrip("?.")
                
                # Get days if specified
                days = 3  # default
                if "for" in input_text.lower() and "days" in input_text.lower():
                    try:
                        days_part = input_text.split("for", 1)[1].split("days", 1)[0].strip()
                        days = int(days_part)
                    except (ValueError, IndexError):
                        pass
                
                # Mock forecast response
                forecast_data = self._get_mock_forecast(location, days)
                
                response_text = f"Weather forecast for {location}:\n\n"
                for day in forecast_data:
                    response_text += (
                        f"{day['day']}:\n"
                        f"Temperature: {day['temperature']}°F\n"
                        f"Condition: {day['condition']}\n\n"
                    )
                
                env.output = {"text": response_text}
                env.status = "COMPLETED"
                
            # Check if this is an alert request
            elif any(term in input_text.lower() for term in ["alert", "warning", "severe"]) and "in" in input_text.lower():
                location = input_text.split("in", 1)[1].strip().rstrip("?.")
                
                # Mock alerts response
                alerts = self._get_mock_alerts(location)
                
                if alerts:
                    response_text = f"Weather alerts for {location}:\n\n"
                    for alert in alerts:
                        response_text += (
                            f"{alert['type']} - {alert['severity']}\n"
                            f"{alert['description']}\n"
                            f"Valid until: {alert['valid_until']}\n\n"
                        )
                else:
                    response_text = f"No weather alerts currently active for {location}."
                
                env.output = {"text": response_text}
                env.status = "COMPLETED"
                
            else:
                # Default response for unknown queries
                env.output = {
                    "text": (
                        "I'm a weather agent with detailed capabilities. You can ask for:\n"
                        "- Current weather in [location]\n"
                        "- Weather forecast in [location] for [X] days\n"
                        "- Weather alerts in [location]"
                    )
                }
                env.status = "COMPLETED"
            
            return env
            
        except Exception as e:
            # Handle errors
            env.output = {"text": f"Error processing request: {str(e)}"}
            env.status = "ERROR"
            return env
    
    def _get_mock_weather(self, location: str) -> Dict[str, Any]:
        """Get mock current weather for a location"""
        # In a real implementation, this would call a weather API
        return {
            "temperature": 72,
            "condition": "Sunny",
            "humidity": 45,
            "wind": "5 mph NE"
        }
    
    # examples/weather_agent.py (continued)

    def _get_mock_forecast(self, location: str, days: int = 3) -> List[Dict[str, Any]]:
        """Get a mock forecast for the specified number of days"""
        # In a real implementation, this would call a weather API
        forecast = []
        for i in range(days):
            forecast.append({
                "day": f"Day {i+1}",
                "temperature": 70 + i * 2,
                "condition": "Partly Cloudy" if i % 2 == 0 else "Sunny"
            })
        return forecast
    
    def _get_mock_alerts(self, location: str) -> List[Dict[str, Any]]:
        """Get mock severe weather alerts for a location"""
        # In a real implementation, this would call a weather API
        # Return some alerts for certain locations, none for others
        if location.lower() in ["florida", "miami", "tampa"]:
            return [
                {
                    "type": "Flood Watch",
                    "severity": "Moderate",
                    "description": "Potential for flooding in low-lying areas due to heavy rainfall",
                    "valid_until": "Tomorrow at 6:00 PM"
                },
                {
                    "type": "Thunderstorm Warning",
                    "severity": "Severe",
                    "description": "Severe thunderstorms capable of producing damaging winds and hail",
                    "valid_until": "Today at 9:00 PM"
                }
            ]
        elif location.lower() in ["colorado", "denver", "boulder"]:
            return [
                {
                    "type": "Winter Storm Warning",
                    "severity": "Severe",
                    "description": "Heavy snow and blizzard conditions expected",
                    "valid_until": "Tomorrow at 12:00 PM"
                }
            ]
        else:
            return []  # No alerts for other locations

if __name__ == "__main__":
    # Create and run the weather agent
    agent = WeatherAgent()
    
    # Register capabilities on startup
    async def startup():
        await agent.register_capabilities()
    
    # Run the startup task
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    
    # Run the agent
    agent.run()