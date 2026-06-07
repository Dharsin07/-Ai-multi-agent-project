"""
Perfect Booking Automation - Fixed Version
Fixed sequence: Current Location -> Destination -> Date -> Flight Search -> Flight Click -> Form Filling
"""
import asyncio
import re
from playwright.async_api import async_playwright
from typing import Dict, Any, List, Optional

class PerfectBookingAutomation:
    def __init__(self):
        self.screenshots = []
        self.selected_flight = None
        
    async def book_flight_perfectly(self, origin: str, destination: str, date: str, passenger_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Perfect flight booking with exact sequence
        """
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--start-maximized'],
                    slow_mo=600
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                print(f"Perfect Booking: {origin} to {destination} on {date}")
                
                # Step 1: Fill current location FIRST
                await self._fill_current_location(page, origin)
                
                # Step 2: Fill destination SECOND
                await self._fill_destination_location(page, destination)
                
                # Step 3: Select date CORRECTLY
                await self._select_date_correctly(page, date)
                
                # Step 4: Search flights EXACT
                await self._search_flights_exact(page)
                
                # Step 5: Click flight AFTER search
                await self._click_flight_after_search(page)
                
                # Step 6: Fill form PROPERLY after flight selection
                await self._fill_form_properly(page, passenger_info)
                
                # Step 7: Final confirmation
                await self._final_confirmation(page)
                
                return {
                    'success': True,
                    'status': 'completed',
                    'screenshots': self.screenshots,
                    'message': 'Perfect booking automation completed!'
                }
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'screenshots': self.screenshots
            }
        finally:
            if browser:
                await browser.close()
    
    async def _fill_current_location(self, page, origin: str):
        """Step 1: Fill current location FIRST"""
        print(f"Step 1: Filling current location: {origin}")
        
        # Navigate first
        await page.goto('https://www.google.com/travel/flights', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Handle any popups
        await self._handle_popups(page)
        
        # Find and fill origin field with multiple strategies
        origin_strategies = [
            self._click_and_type_origin,
            self._direct_fill_origin,
            self._keyboard_fill_origin
        ]
        
        for strategy_func in origin_strategies:
            try:
                success = await strategy_func(page, origin)
                if success:
                    await self._take_screenshot(page, '01_current_location_filled')
                    print(f"SUCCESS: Current location filled: {origin}")
                    return
            except Exception as e:
                print(f"Strategy failed: {e}")
                continue
        
        raise Exception(f"Could not fill current location: {origin}")
    
    async def _click_and_type_origin(self, page, origin: str) -> bool:
        """Strategy 1: Click and type origin"""
        origin_selectors = [
            '[role="combobox"]:first-child',
            'div[role="combobox"]:first-child',
            '.VfPpkd-TkwUic:first-child',
            'input[placeholder*="From"]',
            'input[aria-label*="From"]'
        ]
        
        for selector in origin_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    print(f"Found origin field: {selector}")
                    
                    # Click the field
                    await element.click()
                    await page.wait_for_timeout(1000)
                    
                    # Clear and type
                    await page.keyboard.press('Control+a')
                    await page.keyboard.type(origin)
                    await page.wait_for_timeout(2000)
                    
                    # Select from dropdown
                    if await self._select_dropdown_option(page, origin):
                        return True
                    
            except Exception as e:
                print(f"Click and type failed: {e}")
                continue
        
        return False
    
    async def _direct_fill_origin(self, page, origin: str) -> bool:
        """Strategy 2: Direct fill origin"""
        input_selectors = [
            'input[placeholder*="From"]',
            'input[aria-label*="From"]',
            'input[name*="origin"]'
        ]
        
        for selector in input_selectors:
            try:
                input_field = page.locator(selector).first
                if await input_field.count() > 0 and await input_field.is_visible():
                    await input_field.fill(origin)
                    await page.wait_for_timeout(2000)
                    
                    if await self._select_dropdown_option(page, origin):
                        return True
                    
            except:
                continue
        
        return False
    
    async def _keyboard_fill_origin(self, page, origin: str) -> bool:
        """Strategy 3: Keyboard navigation to origin"""
        try:
            # Tab to first field
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(500)
            
            # Type origin
            await page.keyboard.type(origin)
            await page.wait_for_timeout(2000)
            
            # Select from dropdown
            return await self._select_dropdown_option(page, origin)
            
        except:
            return False
    
    async def _fill_destination_location(self, page, destination: str):
        """Step 2: Fill destination location SECOND"""
        print(f"Step 2: Filling destination: {destination}")
        
        dest_strategies = [
            self._click_and_type_destination,
            self._direct_fill_destination,
            self._keyboard_fill_destination
        ]
        
        for strategy_func in dest_strategies:
            try:
                success = await strategy_func(page, destination)
                if success:
                    await self._take_screenshot(page, '02_destination_filled')
                    print(f"SUCCESS: Destination filled: {destination}")
                    return
            except Exception as e:
                print(f"Destination strategy failed: {e}")
                continue
        
        raise Exception(f"Could not fill destination: {destination}")
    
    async def _click_and_type_destination(self, page, destination: str) -> bool:
        """Click and type destination"""
        dest_selectors = [
            '[role="combobox"]:nth-child(2)',
            'div[role="combobox"]:nth-of-type(2)',
            '.VfPpkd-TkwUic:nth-child(2)',
            'input[placeholder*="To"]',
            'input[aria-label*="To"]'
        ]
        
        for selector in dest_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    print(f"Found destination field: {selector}")
                    
                    await element.click()
                    await page.wait_for_timeout(1000)
                    
                    await page.keyboard.press('Control+a')
                    await page.keyboard.type(destination)
                    await page.wait_for_timeout(2000)
                    
                    if await self._select_dropdown_option(page, destination):
                        return True
                    
            except Exception as e:
                print(f"Destination click and type failed: {e}")
                continue
        
        return False
    
    async def _direct_fill_destination(self, page, destination: str) -> bool:
        """Direct fill destination"""
        input_selectors = [
            'input[placeholder*="To"]',
            'input[aria-label*="To"]',
            'input[name*="destination"]'
        ]
        
        for selector in input_selectors:
            try:
                input_field = page.locator(selector).first
                if await input_field.count() > 0 and await input_field.is_visible():
                    await input_field.fill(destination)
                    await page.wait_for_timeout(2000)
                    
                    if await self._select_dropdown_option(page, destination):
                        return True
                    
            except:
                continue
        
        return False
    
    async def _keyboard_fill_destination(self, page, destination: str) -> bool:
        """Keyboard fill destination"""
        try:
            # Tab to destination field (should be second field)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(500)
            
            await page.keyboard.type(destination)
            await page.wait_for_timeout(2000)
            
            return await self._select_dropdown_option(page, destination)
            
        except:
            return False
    
    async def _select_dropdown_option(self, page, value: str) -> bool:
        """Select option from dropdown"""
        try:
            # Look for exact match
            option_selectors = [
                f'li:has-text("{value}")',
                f'div[role="option"]:has-text("{value}")',
                f'.dropdown-item:has-text("{value}")',
                f'text="{value}"',
                f'text="{value}, India"'
            ]
            
            for selector in option_selectors:
                try:
                    option = page.locator(selector).first
                    if await option.count() > 0 and await option.is_visible():
                        await option.click()
                        await page.wait_for_timeout(1000)
                        print(f"Selected {value} from dropdown")
                        return True
                except:
                    continue
            
            # Try pressing Enter to select first option
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(1000)
            print(f"Selected {value} via Enter")
            return True
            
        except Exception as e:
            print(f"Dropdown selection failed: {e}")
            return False
    
    async def _select_date_correctly(self, page, date: str):
        """Step 3: Select date CORRECTLY"""
        print(f"Step 3: Selecting date correctly: {date}")
        
        # Find and click date field
        date_selectors = [
            'input[placeholder*="Departure"]',
            'input[aria-label*="Departure"]',
            'input[data-testid*="date"]',
            '.date-input'
        ]
        
        date_clicked = False
        for selector in date_selectors:
            try:
                date_field = page.locator(selector).first
                if await date_field.count() > 0 and await date_field.is_visible():
                    await date_field.click()
                    await page.wait_for_timeout(1500)
                    date_clicked = True
                    print(f"Clicked date field: {selector}")
                    break
            except:
                continue
        
        if not date_clicked:
            # Try clicking calendar icon
            calendar_selectors = [
                '.calendar-icon',
                'button[aria-label*="Calendar"]',
                '[data-testid*="calendar"]'
            ]
            
            for selector in calendar_selectors:
                try:
                    calendar = page.locator(selector).first
                    if await calendar.count() > 0 and await calendar.is_visible():
                        await calendar.click()
                        await page.wait_for_timeout(1500)
                        date_clicked = True
                        break
                except:
                    continue
        
        # Extract and select day
        day = self._extract_day_number(date)
        if day:
            success = await self._click_calendar_day(page, day)
            if success:
                await self._take_screenshot(page, '03_date_selected')
                print(f"SUCCESS: Date selected: {date}")
                return
        
        raise Exception(f"Could not select date: {date}")
    
    def _extract_day_number(self, date: str) -> Optional[str]:
        """Extract day number from date string"""
        patterns = [
            r'(\d{1,2})\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})',
            r'(\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date, re.IGNORECASE)
            if match:
                return match.group(1).zfill(2)
        return None
    
    async def _click_calendar_day(self, page, day: str) -> bool:
        """Click specific day in calendar"""
        day_selectors = [
            f'text="{day}"',
            f'button:has-text("{day}")',
            f'[data-day="{day}"]',
            f'.calendar-day:has-text("{day}")',
            f'td:has-text("{day}")'
        ]
        
        for selector in day_selectors:
            try:
                day_element = page.locator(selector).first
                if await day_element.count() > 0 and await day_element.is_visible():
                    await day_element.click()
                    await page.wait_for_timeout(1000)
                    print(f"Clicked day: {day}")
                    return True
            except:
                continue
        
        return False
    
    async def _search_flights_exact(self, page):
        """Step 4: Search flights EXACT"""
        print("Step 4: Searching flights exactly...")
        
        # Try multiple search strategies
        search_strategies = [
            self._click_search_button,
            self._press_enter_search,
            self._click_explore_button
        ]
        
        for strategy_func in search_strategies:
            try:
                success = await strategy_func(page)
                if success:
                    await page.wait_for_timeout(5000)  # Wait for results
                    await self._take_screenshot(page, '04_flight_search_results')
                    print("SUCCESS: Flight search completed")
                    return
            except Exception as e:
                print(f"Search strategy failed: {e}")
                continue
        
        raise Exception("Could not search flights")
    
    async def _click_search_button(self, page) -> bool:
        """Click search button"""
        search_selectors = [
            'button:has-text("Search")',
            'button[data-testid*="search"]',
            'input[type="submit"]',
            'button[type="submit"]'
        ]
        
        for selector in search_selectors:
            try:
                search_btn = page.locator(selector).first
                if await search_btn.count() > 0 and await search_btn.is_visible():
                    await search_btn.click()
                    print("Clicked search button")
                    return True
            except:
                continue
        
        return False
    
    async def _press_enter_search(self, page) -> bool:
        """Press Enter to search"""
        try:
            await page.keyboard.press('Enter')
            print("Pressed Enter to search")
            return True
        except:
            return False
    
    async def _click_explore_button(self, page) -> bool:
        """Click explore button"""
        explore_selectors = [
            'button:has-text("Explore")',
            'button:has-text("Search flights")'
        ]
        
        for selector in explore_selectors:
            try:
                explore_btn = page.locator(selector).first
                if await explore_btn.count() > 0 and await explore_btn.is_visible():
                    await explore_btn.click()
                    print("Clicked explore button")
                    return True
            except:
                continue
        
        return False
    
    async def _click_flight_after_search(self, page):
        """Step 5: Click flight AFTER search"""
        print("Step 5: Clicking flight after search...")
        
        await page.wait_for_timeout(3000)  # Ensure results loaded
        
        # Find flights with prices
        flight_selectors = [
            '.gws-flights-results__result',
            '.flight-result',
            'div:has-text("₹")',
            'div:has-text("$")'
        ]
        
        flights_found = []
        
        for selector in flight_selectors:
            try:
                flights = page.locator(selector)
                count = await flights.count()
                if count > 0:
                    print(f"Found {count} flights with selector: {selector}")
                    
                    # Extract flight info
                    for i in range(min(count, 10)):
                        flight = flights.nth(i)
                        try:
                            text = await flight.text_content()
                            if text and ('₹' in text or '$' in text):
                                price = self._extract_price(text)
                                if price:
                                    flights_found.append({
                                        'index': i,
                                        'selector': selector,
                                        'price': price,
                                        'text': text[:100]
                                    })
                        except:
                            continue
                    break
                    
            except Exception as e:
                print(f"Flight selector failed: {e}")
                continue
        
        if flights_found:
            # Sort by price and select cheapest
            flights_found.sort(key=lambda x: x['price'])
            cheapest = flights_found[0]
            
            print(f"Clicking cheapest flight: ₹{cheapest['price']}")
            
            try:
                flight_element = page.locator(cheapest['selector']).nth(cheapest['index'])
                await flight_element.click()
                await page.wait_for_timeout(3000)  # Wait for selection
                
                self.selected_flight = cheapest
                await self._take_screenshot(page, '05_flight_clicked')
                print("SUCCESS: Flight clicked successfully")
                return
                
            except Exception as e:
                print(f"Could not click flight: {e}")
        
        # Fallback: Click first available flight
        print("Trying first available flight...")
        try:
            first_flight = page.locator('div:has-text("₹"), div:has-text("$")').first
            if await first_flight.count() > 0:
                await first_flight.click()
                await page.wait_for_timeout(3000)
                await self._take_screenshot(page, '05_flight_clicked')
                print("SUCCESS: First flight clicked")
                return
        except:
            pass
        
        raise Exception("Could not click any flight")
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text"""
        patterns = [
            r'₹\s*([\d,]+)',
            r'\$\s*([\d,]+)',
            r'([\d,]+)\s*₹',
            r'([\d,]+)\s*\$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    continue
        return None
    
    async def _fill_form_properly(self, page, passenger_info: Dict[str, str]):
        """Step 6: Fill form PROPERLY after flight selection"""
        print("Step 6: Filling form properly after flight selection...")
        
        # Wait for passenger form to appear
        await page.wait_for_timeout(5000)
        
        # Check if we're on passenger details page
        page_indicators = [
            ('Passenger form', 'form'),
            ('Input fields', 'input'),
            ('Passenger details', '.passenger-details')
        ]
        
        form_found = False
        for indicator_name, selector in page_indicators:
            try:
                element = page.locator(selector).first
                count = await element.count()
                if count > 0:
                    print(f"Found {indicator_name}: {count} elements")
                    form_found = True
                    break
            except:
                continue
        
        if not form_found:
            print("No passenger form found, might need to continue...")
            # Try to find continue/book button
            await self._click_continue_button(page)
            await page.wait_for_timeout(3000)
        
        # Fill passenger fields with multiple strategies
        field_mappings = [
            ('first_name', passenger_info.get('first_name', ''), [
                'input[placeholder*="First"]',
                'input[name*="first"]',
                'input[aria-label*="First"]',
                '#firstName',
                'input[id*="first"]'
            ]),
            ('last_name', passenger_info.get('last_name', ''), [
                'input[placeholder*="Last"]',
                'input[name*="last"]',
                'input[aria-label*="Last"]',
                '#lastName',
                'input[id*="last"]'
            ]),
            ('email', passenger_info.get('email', ''), [
                'input[placeholder*="Email"]',
                'input[name*="email"]',
                'input[type="email"]',
                '#email',
                'input[id*="email"]'
            ]),
            ('phone', passenger_info.get('phone', ''), [
                'input[placeholder*="Phone"]',
                'input[name*="phone"]',
                'input[placeholder*="Mobile"]',
                '#phone',
                'input[id*="phone"]'
            ])
        ]
        
        filled_fields = 0
        for field_name, value, selectors in field_mappings:
            if value:
                success = await self._fill_field_with_strategies(page, field_name, value, selectors)
                if success:
                    filled_fields += 1
        
        if filled_fields >= 3:
            await self._take_screenshot(page, '06_form_filled')
            print(f"SUCCESS: Form filled properly: {filled_fields} fields")
        else:
            print(f"WARNING: Only filled {filled_fields} fields")
    
    async def _fill_field_with_strategies(self, page, field_name: str, value: str, selectors: List[str]) -> bool:
        """Fill field with multiple strategies"""
        for selector in selectors:
            try:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(value)
                    await page.wait_for_timeout(500)
                    print(f"Filled {field_name}: {value}")
                    return True
            except:
                continue
        
        # Try clicking and typing
        for selector in selectors:
            try:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.click()
                    await page.wait_for_timeout(300)
                    await page.keyboard.press('Control+a')
                    await page.keyboard.type(value)
                    await page.wait_for_timeout(500)
                    print(f"Filled {field_name} via keyboard: {value}")
                    return True
            except:
                continue
        
        print(f"Could not fill {field_name}: {value}")
        return False
    
    async def _click_continue_button(self, page):
        """Click continue/book button to reach passenger form"""
        continue_selectors = [
            'button:has-text("Continue")',
            'button:has-text("Book")',
            'button:has-text("Next")',
            'button[type="submit"]'
        ]
        
        for selector in continue_selectors:
            try:
                button = page.locator(selector).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    print(f"Clicked continue button: {selector}")
                    return True
            except:
                continue
        
        return False
    
    async def _final_confirmation(self, page):
        """Step 7: Final confirmation"""
        print("Step 7: Final confirmation...")
        
        await self._take_screenshot(page, '07_final_confirmation')
        
        print("SUCCESS: Perfect booking automation completed!")
        print("Browser will stay open for 60 seconds for manual payment...")
        await page.wait_for_timeout(60000)
    
    async def _handle_popups(self, page):
        """Handle cookie banners and popups"""
        popup_selectors = [
            'button:has-text("Accept all")',
            'button:has-text("Accept")',
            'button:has-text("I agree")',
            '.cookie-accept'
        ]
        
        for selector in popup_selectors:
            try:
                button = page.locator(selector).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    await page.wait_for_timeout(1000)
                    print("Handled popup")
                    break
            except:
                continue
    
    async def _take_screenshot(self, page, name: str):
        """Take screenshot"""
        timestamp = int(asyncio.get_event_loop().time())
        filename = f"{name}_{timestamp}.png"
        await page.screenshot(path=filename, full_page=True)
        self.screenshots.append(filename)
        print(f"Screenshot: {filename}")

# Test function
async def test_perfect_automation():
    """Test the perfect automation"""
    print("Perfect Booking Automation Test")
    print("=" * 50)
    
    automation = PerfectBookingAutomation()
    
    result = await automation.book_flight_perfectly(
        origin="Chennai",
        destination="Bangalore", 
        date="May 25",
        passenger_info={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+919876543210'
        }
    )
    
    print("\n" + "=" * 50)
    print("PERFECT AUTOMATION RESULT")
    print("=" * 50)
    print(f"Success: {result['success']}")
    print(f"Screenshots: {len(result['screenshots'])}")
    
    if result['success']:
        print("Status: Perfect automation completed successfully!")
        print("Sequence: Location -> Destination -> Date -> Search -> Click -> Form")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_perfect_automation())
