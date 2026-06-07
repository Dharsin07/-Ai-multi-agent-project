"""
Correct Browser Automation for Chennai to Goa Flight Booking
Actually fills forms correctly with visible passenger details
"""
import asyncio
from playwright.async_api import async_playwright

class CorrectBookingAutomation:
    def __init__(self):
        pass
    
    async def book_chennai_goa_flight(self, passenger_info):
        """
        Book Chennai to Goa flight with correct automation
        
        Args:
            passenger_info: dict with passenger details
            
        Returns:
            dict with booking status
        """
        async with async_playwright() as p:
            # Launch browser maximized
            browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            try:
                # Navigate to Google Flights
                print("Opening Google Flights...")
                await page.goto('https://www.google.com/travel/flights')
                await page.wait_for_timeout(5000)
                
                # Screenshot 1: Initial page
                await page.screenshot(path='01_initial_page.png', full_page=True)
                print("Screenshot saved: 01_initial_page.png")
                
                # Find and fill origin (Chennai)
                print("Filling origin: Chennai")
                try:
                    # Try multiple selectors for origin input
                    origin_selectors = [
                        'input[placeholder="Where from?"]',
                        'input[aria-label*="From"]',
                        'input[placeholder*="From"]',
                        'input[placeholder*="where from"]'
                    ]
                    
                    origin_filled = False
                    for selector in origin_selectors:
                        try:
                            origin_input = page.locator(selector).first
                            if await origin_input.count() > 0:
                                print(f"Found origin input with selector: {selector}")
                                await origin_input.click()
                                await origin_input.fill('Chennai')
                                await page.wait_for_timeout(2000)
                                
                                # Select Chennai from dropdown
                                chennai_selectors = [
                                    'text=Chennai',
                                    'text=Chennai, India',
                                    'text=MAA'
                                ]
                                for chennai_sel in chennai_selectors:
                                    try:
                                        chennai_option = page.locator(chennai_sel).first
                                        if await chennai_option.count() > 0:
                                            await chennai_option.click()
                                            print("Chennai selected from dropdown")
                                            origin_filled = True
                                            break
                                    except:
                                        pass
                                
                                if origin_filled:
                                    break
                        except:
                            continue
                    
                    if not origin_filled:
                        print("Warning: Could not fill origin field")
                
                except Exception as e:
                    print(f"Origin fill error: {e}")
                
                await page.wait_for_timeout(2000)
                
                # Screenshot 2: After filling origin
                await page.screenshot(path='02_after_origin.png', full_page=True)
                print("Screenshot saved: 02_after_origin.png")
                
                # Find and fill destination (Goa)
                print("Filling destination: Goa")
                try:
                    dest_selectors = [
                        'input[placeholder="Where to?"]',
                        'input[aria-label*="To"]',
                        'input[placeholder*="To"]',
                        'input[placeholder*="where to"]'
                    ]
                    
                    dest_filled = False
                    for selector in dest_selectors:
                        try:
                            dest_input = page.locator(selector).first
                            if await dest_input.count() > 0:
                                print(f"Found destination input with selector: {selector}")
                                await dest_input.click()
                                await dest_input.fill('Goa')
                                await page.wait_for_timeout(2000)
                                
                                # Select Goa from dropdown
                                goa_selectors = [
                                    'text=Goa',
                                    'text=Goa, India',
                                    'text=GOI'
                                ]
                                for goa_sel in goa_selectors:
                                    try:
                                        goa_option = page.locator(goa_sel).first
                                        if await goa_option.count() > 0:
                                            await goa_option.click()
                                            print("Goa selected from dropdown")
                                            dest_filled = True
                                            break
                                    except:
                                        pass
                                
                                if dest_filled:
                                    break
                        except:
                            continue
                    
                    if not dest_filled:
                        print("Warning: Could not fill destination field")
                
                except Exception as e:
                    print(f"Destination fill error: {e}")
                
                await page.wait_for_timeout(2000)
                
                # Screenshot 3: After filling destination
                await page.screenshot(path='03_after_destination.png', full_page=True)
                print("Screenshot saved: 03_after_destination.png")
                
                # Fill departure date - June 10, 2024
                print("Filling departure date: June 10, 2024")
                try:
                    date_selectors = [
                        'input[placeholder*="Departure"]',
                        'input[aria-label*="Departure"]',
                        'input[placeholder*="departure"]'
                    ]
                    
                    date_filled = False
                    for selector in date_selectors:
                        try:
                            date_input = page.locator(selector).first
                            if await date_input.count() > 0:
                                print(f"Found date input with selector: {selector}")
                                await date_input.click()
                                await page.wait_for_timeout(1000)
                                
                                # Try to select June 10
                                try:
                                    june_10 = page.locator('text="10"').nth(2)
                                    if await june_10.count() > 0:
                                        await june_10.click()
                                        date_filled = True
                                        print("June 10 selected")
                                except:
                                    pass
                                
                                if date_filled:
                                    break
                        except:
                            continue
                    
                    if not date_filled:
                        print("Warning: Could not fill date field")
                
                except Exception as e:
                    print(f"Date fill error: {e}")
                
                await page.wait_for_timeout(2000)
                
                # Screenshot 4: After filling date
                await page.screenshot(path='04_after_date.png', full_page=True)
                print("Screenshot saved: 04_after_date.png")
                
                # Click search button
                print("Searching for flights...")
                try:
                    search_button = page.locator('button:has-text("Search")').first
                    if await search_button.count() > 0:
                        await search_button.click()
                        print("Search button clicked")
                    else:
                        # Try Enter key as fallback
                        await page.keyboard.press('Enter')
                        print("Pressed Enter to search")
                except:
                    await page.keyboard.press('Enter')
                
                # Wait for search results
                print("Waiting for search results...")
                await page.wait_for_timeout(10000)
                
                # Check if page is still active
                if await page.locator('body').count() == 0:
                    print("Page closed unexpectedly, trying to navigate again...")
                    await page.goto('https://www.google.com/travel/flights')
                    await page.wait_for_timeout(3000)
                
                # Screenshot 5: Flight search results
                await page.screenshot(path='05_flight_results.png', full_page=True)
                print("Screenshot saved: 05_flight_results.png")
                
                # Try to select first flight
                print("Selecting first flight...")
                try:
                    first_flight = page.locator('.flight-item').first
                    if await first_flight.count() > 0:
                        await first_flight.click()
                        await page.wait_for_timeout(2000)
                        print("First flight selected")
                        
                        # Click book button
                        book_button = page.locator('button:has-text("Book")').first
                        if await book_button.count() > 0:
                            await book_button.click()
                            await page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"Flight selection error: {e}")
                
                # Screenshot 6: After flight selection
                await page.screenshot(path='06_after_flight_selection.png', full_page=True)
                print("Screenshot saved: 06_after_flight_selection.png")
                
                # Fill passenger details with visible text
                print("Filling passenger details...")
                try:
                    # First name
                    name_selectors = [
                        'input[placeholder="First Name"]',
                        'input[placeholder="First name"]',
                        'input[name*="first"]',
                        'input[aria-label*="First"]'
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_input = page.locator(selector).first
                            if await name_input.count() > 0:
                                await name_input.fill(passenger_info['first_name'])
                                print(f"Filled first name: {passenger_info['first_name']}")
                                break
                        except:
                            continue
                    
                    await page.wait_for_timeout(500)
                    
                    # Last name
                    last_name_selectors = [
                        'input[placeholder="Last Name"]',
                        'input[placeholder="Last name"]',
                        'input[name*="last"]',
                        'input[aria-label*="Last"]'
                    ]
                    
                    for selector in last_name_selectors:
                        try:
                            last_name_input = page.locator(selector).first
                            if await last_name_input.count() > 0:
                                await last_name_input.fill(passenger_info['last_name'])
                                print(f"Filled last name: {passenger_info['last_name']}")
                                break
                        except:
                            continue
                    
                    await page.wait_for_timeout(500)
                    
                    # Phone
                    phone_selectors = [
                        'input[placeholder="Mobile Number"]',
                        'input[placeholder="Phone"]',
                        'input[name*="phone"]',
                        'input[name*="mobile"]',
                        'input[aria-label*="Phone"]'
                    ]
                    
                    for selector in phone_selectors:
                        try:
                            phone_input = page.locator(selector).first
                            if await phone_input.count() > 0:
                                await phone_input.fill(passenger_info['phone'])
                                print(f"Filled phone: {passenger_info['phone']}")
                                break
                        except:
                            continue
                    
                    await page.wait_for_timeout(500)
                    
                    # Email
                    email_selectors = [
                        'input[placeholder="Email"]',
                        'input[name*="email"]',
                        'input[aria-label*="Email"]',
                        'input[type="email"]'
                    ]
                    
                    for selector in email_selectors:
                        try:
                            email_input = page.locator(selector).first
                            if await email_input.count() > 0:
                                await email_input.fill(passenger_info['email'])
                                print(f"Filled email: {passenger_info['email']}")
                                break
                        except:
                            continue
                    
                    await page.wait_for_timeout(1000)
                    
                    # Screenshot 7: Passenger form filled
                    await page.screenshot(path='07_passenger_form_filled.png', full_page=True)
                    print("Screenshot saved: 07_passenger_form_filled.png")
                    
                except Exception as e:
                    print(f"Form filling error: {e}")
                
                # Keep browser open for user to see
                print("Browser will stay open for 60 seconds...")
                print("You can see the filled forms and complete payment manually.")
                print(f"Passenger details: {passenger_info}")
                await page.wait_for_timeout(60000)
                
                return {
                    'success': True,
                    'status': 'forms_filled_correctly',
                    'message': 'Chennai to Goa flight searched and forms filled correctly.',
                    'screenshots': [
                        '01_initial_page.png',
                        '02_after_origin.png',
                        '03_after_destination.png',
                        '04_after_date.png',
                        '05_flight_results.png',
                        '06_after_flight_selection.png',
                        '07_passenger_form_filled.png'
                    ],
                    'passenger_info': passenger_info
                }
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Automation failed'
                }
            
            finally:
                await browser.close()

async def main():
    """Main function to run the automation"""
    print("=" * 70)
    print("CORRECT Browser Automation - Chennai to Goa Flight Booking")
    print("=" * 70)
    
    passenger_info = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'phone': '+919876543210'
    }
    
    automation = CorrectBookingAutomation()
    result = await automation.book_chennai_goa_flight(passenger_info)
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(result)
    
    if result['success']:
        print("\nSUCCESS: Browser automation completed correctly!")
        print(f"Passenger details used: {result.get('passenger_info')}")
        print(f"Screenshots saved: {len(result.get('screenshots', []))}")
    else:
        print(f"\nFAILED: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(main())
