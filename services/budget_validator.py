import re
from typing import Dict, List, Any, Optional, Tuple
from utils.logger import logger
import json

class BudgetValidator:
    """Strict budget validation and rating verification system for TRAVA AI"""
    
    def __init__(self):
        # Currency conversion rates (approximate, should use real API in production)
        self.conversion_rates = {
            'USD': 1.0,
            'INR': 0.012,  # 1 INR = 0.012 USD
            'EUR': 1.08,
            'GBP': 1.27,
            'AED': 0.27  # Dubai Dirham
        }
        
        # Daily cost estimates by travel style (in USD)
        self.daily_costs = {
            'luxury': {'food': 150, 'activities': 200, 'transport': 80, 'misc': 70},
            'mid-range': {'food': 80, 'activities': 100, 'transport': 40, 'misc': 40},
            'budget': {'food': 30, 'activities': 40, 'transport': 20, 'misc': 20},
            'family': {'food': 120, 'activities': 150, 'transport': 60, 'misc': 50},
            'business': {'food': 100, 'activities': 80, 'transport': 50, 'misc': 40},
            'romantic': {'food': 120, 'activities': 120, 'transport': 40, 'misc': 50},
            'adventure': {'food': 60, 'activities': 150, 'transport': 60, 'misc': 40},
            'leisure': {'food': 80, 'activities': 100, 'transport': 40, 'misc': 40}
        }
        
        logger.info("Initializing Budget Validator")

    def validate_travel_budget(self, travel_intent: Dict, flights: List[Dict], 
                            hotels: List[Dict], duration_days: int) -> Dict[str, Any]:
        """
        Comprehensive budget validation and analysis
        
        Args:
            travel_intent: Extracted travel intent
            flights: List of flight options
            hotels: List of hotel options
            duration_days: Trip duration in days
            
        Returns:
            Detailed budget validation result
        """
        logger.info("Starting comprehensive budget validation")
        
        try:
            # Extract budget information
            budget_info = travel_intent.get('budget', {})
            budget_amount = self._parse_amount(budget_info.get('amount', '0'))
            budget_currency = budget_info.get('currency', 'USD')
            travel_style = travel_intent.get('travel_style', 'leisure')
            
            # Convert budget to USD for comparison
            budget_usd = self._convert_to_usd(budget_amount, budget_currency)
            
            # Calculate total estimated costs
            cost_breakdown = self._calculate_total_costs(
                flights, hotels, duration_days, travel_style
            )
            
            # Validate against budget
            validation_result = self._validate_against_budget(
                budget_usd, cost_breakdown, budget_currency
            )
            
            # Generate optimization suggestions if needed
            optimization_suggestions = self._generate_optimization_suggestions(
                validation_result, travel_style, cost_breakdown
            )
            
            # Create comprehensive budget analysis
            budget_analysis = {
                "budget_validation": {
                    "requested_budget": f"{budget_amount} {budget_currency}",
                    "budget_usd": budget_usd,
                    "total_estimated_cost_usd": cost_breakdown['total_usd'],
                    "total_estimated_cost_original": f"{self._convert_from_usd(cost_breakdown['total_usd'], budget_currency):.2f} {budget_currency}",
                    "is_within_budget": validation_result['is_within_budget'],
                    "budget_variance": validation_result['variance'],
                    "budget_variance_percentage": validation_result['variance_percentage'],
                    "validation_status": validation_result['status']
                },
                "cost_breakdown": {
                    "flights": {
                        "cost_usd": cost_breakdown['flights_usd'],
                        "cost_original": f"{self._convert_from_usd(cost_breakdown['flights_usd'], budget_currency):.2f} {budget_currency}",
                        "details": flights[:2] if flights else []
                    },
                    "accommodation": {
                        "cost_usd": cost_breakdown['accommodation_usd'],
                        "cost_original": f"{self._convert_from_usd(cost_breakdown['accommodation_usd'], budget_currency):.2f} {budget_currency}",
                        "details": hotels[:2] if hotels else []
                    },
                    "daily_expenses": {
                        "cost_usd": cost_breakdown['daily_usd'],
                        "cost_original": f"{self._convert_from_usd(cost_breakdown['daily_usd'], budget_currency):.2f} {budget_currency}",
                        "per_day_breakdown": cost_breakdown['daily_breakdown'],
                        "duration_days": duration_days
                    },
                    "contingency": {
                        "cost_usd": cost_breakdown['contingency_usd'],
                        "cost_original": f"{self._convert_from_usd(cost_breakdown['contingency_usd'], budget_currency):.2f} {budget_currency}",
                        "percentage": "10%"
                    }
                },
                "optimization_suggestions": optimization_suggestions,
                "budget_compliance": {
                    "meets_minimum_requirements": True,
                    "rating_requirements_met": self._validate_rating_requirements(travel_intent, hotels),
                    "hotel_preferences_matched": self._validate_hotel_preferences(travel_intent, hotels),
                    "flight_preferences_matched": self._validate_flight_preferences(travel_intent, flights)
                }
            }
            
            logger.info("Budget validation completed successfully")
            return budget_analysis
            
        except Exception as e:
            logger.error(f"Error in budget validation: {e}")
            return self._get_fallback_budget_analysis()

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount from string and return as float"""
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', str(amount_str))
        
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not parse amount: {amount_str}")
            return 0.0

    def _convert_to_usd(self, amount: float, currency: str) -> float:
        """Convert amount to USD"""
        if currency.upper() in self.conversion_rates:
            return amount * self.conversion_rates[currency.upper()]
        else:
            logger.warning(f"Unknown currency: {currency}, assuming USD")
            return amount

    def _convert_from_usd(self, amount_usd: float, target_currency: str) -> float:
        """Convert USD amount to target currency"""
        if target_currency.upper() in self.conversion_rates:
            return amount_usd / self.conversion_rates[target_currency.upper()]
        else:
            return amount_usd

    def _calculate_total_costs(self, flights: List[Dict], hotels: List[Dict], 
                             duration_days: int, travel_style: str) -> Dict[str, Any]:
        """Calculate comprehensive cost breakdown"""
        
        # Flight costs (take cheapest reasonable option)
        flight_cost_usd = 0
        if flights:
            flight_prices = []
            for flight in flights:
                price_str = flight.get('price_estimate', '0')
                price_usd = self._extract_price_usd(price_str)
                if price_usd > 0:
                    flight_prices.append(price_usd)
            
            if flight_prices:
                # Take second cheapest or median to avoid unrealistic options
                flight_prices.sort()
                flight_cost_usd = flight_prices[min(1, len(flight_prices)-1)]
        
        # Hotel costs (take reasonable option, not cheapest)
        accommodation_cost_usd = 0
        if hotels and duration_days > 0:
            hotel_prices = []
            for hotel in hotels:
                price_str = hotel.get('price_per_night', '0')
                price_usd = self._extract_price_usd(price_str)
                if price_usd > 0:
                    hotel_prices.append(price_usd)
            
            if hotel_prices:
                # Take mid-range option
                hotel_prices.sort()
                mid_index = len(hotel_prices) // 2
                accommodation_cost_usd = hotel_prices[mid_index] * duration_days
        
        # Daily expenses based on travel style
        daily_costs = self.daily_costs.get(travel_style, self.daily_costs['leisure'])
        daily_total = sum(daily_costs.values())
        daily_expenses_usd = daily_total * duration_days
        
        # Contingency (10% of subtotal)
        subtotal = flight_cost_usd + accommodation_cost_usd + daily_expenses_usd
        contingency_usd = subtotal * 0.10
        
        total_usd = subtotal + contingency_usd
        
        return {
            'flights_usd': flight_cost_usd,
            'accommodation_usd': accommodation_cost_usd,
            'daily_usd': daily_expenses_usd,
            'contingency_usd': contingency_usd,
            'total_usd': total_usd,
            'daily_breakdown': daily_costs
        }

    def _extract_price_usd(self, price_str: str) -> float:
        """Extract price in USD from price string"""
        if not price_str:
            return 0.0
        
        # Extract numeric value
        price_match = re.search(r'(\d{1,6}(?:,\d{3})*(?:\.\d{2})?)', price_str)
        if not price_match:
            return 0.0
        
        price_value = float(price_match.group(1).replace(',', ''))
        
        # Check currency and convert
        if '₹' in price_str or 'INR' in price_str or 'Rs' in price_str:
            return self._convert_to_usd(price_value, 'INR')
        elif '€' in price_str or 'EUR' in price_str:
            return self._convert_to_usd(price_value, 'EUR')
        elif '£' in price_str or 'GBP' in price_str:
            return self._convert_to_usd(price_value, 'GBP')
        elif 'AED' in price_str or 'د.إ' in price_str:
            return self._convert_to_usd(price_value, 'AED')
        else:
            return price_value  # Assume USD

    def _validate_against_budget(self, budget_usd: float, cost_breakdown: Dict[str, float], 
                               original_currency: str) -> Dict[str, Any]:
        """Validate costs against budget"""
        
        total_cost = cost_breakdown['total_usd']
        variance = budget_usd - total_cost
        variance_percentage = (variance / budget_usd * 100) if budget_usd > 0 else 0
        
        if variance >= 0:
            if variance_percentage >= 10:
                status = "well_within_budget"
            elif variance_percentage >= 5:
                status = "within_budget"
            else:
                status = "tight_budget"
        else:
            if variance_percentage <= -10:
                status = "significantly_over_budget"
            else:
                status = "slightly_over_budget"
        
        return {
            'is_within_budget': variance >= 0,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'status': status
        }

    def _generate_optimization_suggestions(self, validation_result: Dict[str, Any], 
                                         travel_style: str, cost_breakdown: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on validation"""
        
        suggestions = []
        
        if not validation_result['is_within_budget']:
            variance_percentage = validation_result['variance_percentage']
            
            if variance_percentage <= -20:
                suggestions.append("Consider reducing trip duration by 1-2 days")
                suggestions.append("Look for budget accommodation options")
                suggestions.append("Choose economy flights instead of premium options")
            elif variance_percentage <= -10:
                suggestions.append("Consider mid-range hotels instead of luxury options")
                suggestions.append("Look for flight deals or alternative dates")
            else:
                suggestions.append("Book in advance for better rates")
                suggestions.append("Consider travel packages for discounts")
        else:
            if validation_result['variance_percentage'] >= 20:
                suggestions.append("Consider upgrading to premium accommodations")
                suggestions.append("Add more activities or dining experiences")
            else:
                suggestions.append("Current plan is well-balanced")
        
        # Travel style specific suggestions
        if travel_style == 'luxury':
            suggestions.append("Look for luxury package deals")
        elif travel_style == 'budget':
            suggestions.append("Consider all-inclusive budget packages")
            suggestions.append("Travel during off-peak season for better rates")
        
        return suggestions[:6]  # Limit to 6 suggestions

    def _validate_rating_requirements(self, travel_intent: Dict, hotels: List[Dict]) -> bool:
        """Validate if hotels meet minimum rating requirements"""
        minimum_rating = travel_intent.get('minimum_ratings')
        if not minimum_rating:
            return True
        
        for hotel in hotels:
            rating_str = hotel.get('rating', '0')
            rating_value = self._extract_rating_value(rating_str)
            if rating_value >= minimum_rating:
                return True
        
        return False

    def _validate_hotel_preferences(self, travel_intent: Dict, hotels: List[Dict]) -> bool:
        """Validate if hotels match user preferences"""
        preferences = travel_intent.get('hotel_preferences', [])
        if not preferences:
            return True
        
        for hotel in hotels:
            amenities = hotel.get('amenities', [])
            # Check if at least 50% of preferences are met
            matched = sum(1 for pref in preferences if any(pref.lower() in amen.lower() for amen in amenities))
            if matched >= len(preferences) / 2:
                return True
        
        return False

    def _validate_flight_preferences(self, travel_intent: Dict, flights: List[Dict]) -> bool:
        """Validate if flights match user preferences"""
        flight_type = travel_intent.get('flight_type', 'economy')
        if not flights:
            return True
        
        for flight in flights:
            if flight_type.lower() in flight.get('flight_type', '').lower():
                return True
        
        return False

    def _extract_rating_value(self, rating_str: str) -> float:
        """Extract numeric rating value from rating string"""
        if not rating_str:
            return 0.0
        
        match = re.search(r'(\d+\.?\d*)', rating_str)
        if match:
            return float(match.group(1))
        
        return 0.0

    def _get_fallback_budget_analysis(self) -> Dict[str, Any]:
        """Fallback budget analysis if validation fails"""
        return {
            "budget_validation": {
                "requested_budget": "Not specified",
                "budget_usd": 0,
                "total_estimated_cost_usd": 0,
                "total_estimated_cost_original": "Not available",
                "is_within_budget": False,
                "budget_variance": 0,
                "budget_variance_percentage": 0,
                "validation_status": "validation_failed"
            },
            "cost_breakdown": {
                "flights": {"cost_usd": 0, "cost_original": "Not available"},
                "accommodation": {"cost_usd": 0, "cost_original": "Not available"},
                "daily_expenses": {"cost_usd": 0, "cost_original": "Not available"},
                "contingency": {"cost_usd": 0, "cost_original": "Not available"}
            },
            "optimization_suggestions": ["Please specify budget for better recommendations"],
            "budget_compliance": {
                "meets_minimum_requirements": False,
                "rating_requirements_met": False,
                "hotel_preferences_matched": False,
                "flight_preferences_matched": False
            }
        }
