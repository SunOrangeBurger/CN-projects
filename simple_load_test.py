"""
Simple load test for Quiz Network
Tests basic endpoints and measures response times
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method='GET', data=None):
    """Test a single endpoint and return response time"""
    start = time.time()
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", data=data)
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        return {
            'success': response.status_code < 400,
            'status': response.status_code,
            'time': elapsed
        }
    except Exception as e:
        return {
            'success': False,
            'status': 0,
            'time': 0,
            'error': str(e)
        }

def run_concurrent_requests(endpoint, num_requests=50, num_workers=10):
    """Run multiple concurrent requests to an endpoint"""
    print(f"\nTesting {endpoint} with {num_requests} requests ({num_workers} concurrent)...")
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(test_endpoint, endpoint) for _ in range(num_requests)]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        times = [r['time'] for r in successful]
        
        print(f"  ✓ Successful: {len(successful)}/{num_requests}")
        print(f"  ✗ Failed: {len(failed)}/{num_requests}")
        print(f"  ⏱ Total time: {total_time:.2f}s")
        print(f"  ⚡ Requests/sec: {num_requests/total_time:.2f}")
        print(f"  📊 Response times:")
        print(f"     - Min: {min(times):.2f}ms")
        print(f"     - Max: {max(times):.2f}ms")
        print(f"     - Avg: {statistics.mean(times):.2f}ms")
        print(f"     - Median: {statistics.median(times):.2f}ms")
        
        if len(times) > 1:
            print(f"     - Std Dev: {statistics.stdev(times):.2f}ms")
    else:
        print(f"  ✗ All requests failed!")
        if failed and 'error' in failed[0]:
            print(f"  Error: {failed[0]['error']}")

def test_user_flow():
    """Test a complete user flow"""
    print("\n" + "="*60)
    print("Testing complete user flow...")
    print("="*60)
    
    session = requests.Session()
    username = f"loadtest_{int(time.time())}"
    
    # Register
    start = time.time()
    response = session.post(f"{BASE_URL}/register", data={
        'username': username,
        'password': 'test123'
    })
    register_time = (time.time() - start) * 1000
    print(f"  Register: {register_time:.2f}ms (status: {response.status_code})")
    
    # Login
    start = time.time()
    response = session.post(f"{BASE_URL}/login", data={
        'username': username,
        'password': 'test123'
    })
    login_time = (time.time() - start) * 1000
    print(f"  Login: {login_time:.2f}ms (status: {response.status_code})")
    
    # Dashboard
    start = time.time()
    response = session.get(f"{BASE_URL}/dashboard")
    dashboard_time = (time.time() - start) * 1000
    print(f"  Dashboard: {dashboard_time:.2f}ms (status: {response.status_code})")
    
    # Create quiz page
    start = time.time()
    response = session.get(f"{BASE_URL}/create_quiz")
    create_quiz_time = (time.time() - start) * 1000
    print(f"  Create Quiz Page: {create_quiz_time:.2f}ms (status: {response.status_code})")
    
    total = register_time + login_time + dashboard_time + create_quiz_time
    print(f"\n  Total flow time: {total:.2f}ms")

def main():
    print("="*60)
    print("QUIZ NETWORK - SIMPLE LOAD TEST")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✓ Server is running\n")
    except:
        print("✗ Server is not running. Please start the server first.")
        return
    
    # Test static endpoints
    run_concurrent_requests("/", num_requests=100, num_workers=20)
    run_concurrent_requests("/login", num_requests=100, num_workers=20)
    run_concurrent_requests("/register", num_requests=100, num_workers=20)
    run_concurrent_requests("/static/css/style.css", num_requests=100, num_workers=20)
    
    # Test user flow
    test_user_flow()
    
    print("\n" + "="*60)
    print("LOAD TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
    except Exception as e:
        print(f"\n\nLoad test failed: {e}")
        import traceback
        traceback.print_exc()
