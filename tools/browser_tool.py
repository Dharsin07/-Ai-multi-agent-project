from langchain.tools import tool
from utils.logger import logger

@tool("Browser Automation Tool (Mock)")
def browser_tool(action: str, url: str) -> str:
    """
    A placeholder tool for future Playwright-based browser automation.
    Use this to simulate booking a flight or hotel on a specific URL.
    """
    logger.info(f"Browser Tool invoked: action={action}, url={url}")
    # In the future, this will initialize Playwright, navigate to the URL, 
    # find the relevant form fields, and execute the booking action.
    
    return f"Simulated browser automation successful. Action '{action}' completed on '{url}'."
