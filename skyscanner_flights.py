import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd

def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "economy",
    max_stops: Optional[int] = None,
    preferred_carriers: Optional[List[str]] = None,
    currency: str = "USD",
    locale: str = "en-US",
    api_key: str = "YOUR_API_KEY",
    sort_by: str = "price",  # Options: price, duration, departure_time, arrival_time
    market: str = "US"
) -> Dict:
    """
    Search for flights using Skyscanner API with comprehensive parameters.
    
    Args:
        origin (str): Origin airport/city IATA code (e.g., 'LAX')
        destination (str): Destination airport/city IATA code (e.g., 'JFK')
        departure_date (str): Departure date in YYYY-MM-DD format
        return_date (Optional[str]): Return date in YYYY-MM-DD format for round trips
        adults (int): Number of adult passengers (age 16+)
        children (int): Number of children passengers (age 2-15)
        infants (int): Number of infant passengers (age < 2)
        cabin_class (str): Preferred cabin class ('economy', 'premium_economy', 'business', 'first')
        max_stops (Optional[int]): Maximum number of stops allowed
        preferred_carriers (Optional[List[str]]): List of preferred airline IATA codes
        currency (str): Currency code for prices (e.g., 'USD', 'EUR')
        locale (str): Language and country code (e.g., 'en-US')
        api_key (str): Skyscanner API key
        sort_by (str): Sorting criteria for results
        market (str): Country market code
    
    Returns:
        Dict: Processed and sorted flight search results
    """
    
    # API endpoint
    base_url = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search"
    
    # Construct the request headers
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Build the request payload
    payload = {
        "query": {
            "market": market,
            "locale": locale,
            "currency": currency,
            "queryLegs": [
                {
                    "originPlace": {
                        "iata": origin
                    },
                    "destinationPlace": {
                        "iata": destination
                    },
                    "date": {
                        "year": int(departure_date[:4]),
                        "month": int(departure_date[5:7]),
                        "day": int(departure_date[8:10])
                    }
                }
            ],
            "cabinClass": cabin_class.upper(),
            "adults": adults,
            "children": children,
            "infants": infants
        }
    }
    
    # Add return leg if return_date is provided
    if return_date:
        return_leg = {
            "originPlace": {
                "iata": destination
            },
            "destinationPlace": {
                "iata": origin
            },
            "date": {
                "year": int(return_date[:4]),
                "month": int(return_date[5:7]),
                "day": int(return_date[8:10])
            }
        }
        payload["query"]["queryLegs"].append(return_leg)
    
    # Add optional parameters if provided
    if max_stops is not None:
        payload["query"]["maxStops"] = max_stops
    
    if preferred_carriers:
        payload["query"]["preferredCarriers"] = preferred_carriers
    
    try:
        # Make the API request
        response = requests.post(base_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Process and organize the response data
        processed_results = []
        
        for itinerary in data["itineraries"]:
            for leg in itinerary["legs"]:
                flight_info = {
                    "price": itinerary["pricing"]["total"]["amount"],
                    "currency": itinerary["pricing"]["total"]["currency"],
                    "airline": leg["carriers"]["marketing"][0]["name"],
                    "flight_number": leg["segments"][0]["flightNumber"],
                    "departure_time": leg["departure"],
                    "arrival_time": leg["arrival"],
                    "duration_mins": leg["durationInMinutes"],
                    "stops": len(leg["segments"]) - 1,
                    "origin": leg["origin"]["flightPlaceId"],
                    "destination": leg["destination"]["flightPlaceId"]
                }
                processed_results.append(flight_info)
        
        # Convert to DataFrame for easier sorting and filtering
        df = pd.DataFrame(processed_results)
        
        # Sort results based on specified criteria
        if sort_by == "price":
            df = df.sort_values("price")
        elif sort_by == "duration":
            df = df.sort_values("duration_mins")
        elif sort_by == "departure_time":
            df = df.sort_values("departure_time")
        elif sort_by == "arrival_time":
            df = df.sort_values("arrival_time")
        
        # Convert DataFrame back to dictionary
        sorted_results = df.to_dict(orient="records")
        
        return {
            "status": "success",
            "total_results": len(sorted_results),
            "flights": sorted_results
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": str(e)
        }
        
if __name__ == "__main__":

    # Simple one-way search
    results = search_flights(
        origin="BGM",
        destination="LAS",
        departure_date="2024-12-01"
    )

    print(f"\nSimple Search Results:\n{results}",flush=True)
    
    # More complex round-trip search
    results = search_flights(
        origin="BGM",
        destination="LAS",
        departure_date="2024-12-01",
        return_date="2024-12-08",
        adults=2,
        children=1,
        cabin_class="coach",
        max_stops=1,
        # preferred_carriers=["AA", "DL"],
        sort_by="duration"
    )
    
    print(f"\nComplex Search with Return Trip Results:\n{results}")