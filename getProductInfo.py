from mcp.server.fastmcp import FastMCP
import requests
from typing import Dict, List, Any
import logging
import sys

# CRITICAL FIX: Direct logging output to sys.stderr instead of sys.stdout.
# sys.stdout must be kept clear for the JSON-RPC communication required by FastMCP.
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:\t%(message)s')

# --- FAST MCP SERVER DEFINITION ---

# The connector name must match the key in the Claude configuration JSON (e.g., "SAP_Product_Connector")
mcp = FastMCP("SAP_Product_Info")

# 1. Define API Credentials and Base URL
# Base URL from your Java code: https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product
SAP_BASE_URL = "https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product"
# NOTE: Using the validated sandbox key from your Java code
SAP_API_KEY = "YXxoMnRrsAyLmrIHcS1NZSujCd83uwHl"


# --- TOOL FUNCTION ---

@mcp.tool()
def get_sap_products(top_count: int) -> Dict[str, List[Dict] | str | Any]:
    """
    Retrieves general product data from the SAP API Sandbox using a $top filter.
    Parameters:
        top_count (int): The maximum number of records to retrieve. Limited to 50 for the sandbox.
    """
    logging.info(f"OData query: Fetching top {top_count} general product records from API_PRODUCT_SRV.")

    # Headers match your Java code's headers
    headers = {
        "APIKey": SAP_API_KEY,
        "DataServiceVersion": "2.0",
        "Accept": "application/json"
    }

    # Parameters for the OData query, mirroring the URL query string in your Java code
    # (%24inlinecount=allpages&%24top=50)
    params = {
        "$top": min(top_count, 50),  # Limit to 50 as in your Java code and for sandbox safety
        "$inlinecount": "allpages",
        "$format": "json" # Often good practice for OData requests
    }

    try:
        # Perform the GET request
        response = requests.get(SAP_BASE_URL, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        data = response.json()

        # Extract results based on OData structure (V2: d/results or V4: value)
        # API_PRODUCT_SRV is typically OData V2, so we look for 'd' and 'results'
        if 'd' in data and 'results' in data['d']:
            results = data['d']['results']
        elif 'value' in data:
            results = data['value']
        else:
            results = []

        logging.info(f"Successfully retrieved {len(results)} general product records.")
        # Return a structured dictionary for the agent
        return {"results": results}

    except requests.exceptions.RequestException as e:
        logging.error(f"SAP OData Request Failed: {e}")
        # Return structured error for the agent to process
        return {"error": f"Failed to access SAP OData API_PRODUCT_SRV. Details: {e}"}


# --- RUN BLOCK (CRITICAL: Starts the server process) ---

if __name__ == "__main__":
    logging.info("Attempting to start FastMCP server...")
    mcp.run()