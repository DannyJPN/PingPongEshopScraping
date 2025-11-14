"""
Test script to verify token tracking functionality.
This script tests the TokenTracker without making actual API calls.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to display to console
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

from unifierlib.token_tracker import get_tracker

def test_token_tracking():
    """Test the token tracking functionality."""
    print("Testing Token Tracking System")
    print("=" * 80)

    # Get the tracker instance
    tracker = get_tracker()

    # Reset any previous data
    tracker.reset()

    # Simulate some API calls
    print("\nSimulating API calls...")

    # Simulate call 1: gpt-4o for complex task
    tracker.track_usage(
        model='gpt-4o',
        prompt_tokens=1500,
        completion_tokens=500,
        total_tokens=2000,
        task_type='category_mapping'
    )
    print("✓ Tracked gpt-4o call (category_mapping): 1500 prompt + 500 completion = 2000 tokens")

    # Simulate call 2: gpt-4o-mini for simple task
    tracker.track_usage(
        model='gpt-4o-mini',
        prompt_tokens=800,
        completion_tokens=200,
        total_tokens=1000,
        task_type='keyword_generation'
    )
    print("✓ Tracked gpt-4o-mini call (keyword_generation): 800 prompt + 200 completion = 1000 tokens")

    # Simulate call 3: Another gpt-4o call
    tracker.track_usage(
        model='gpt-4o',
        prompt_tokens=2000,
        completion_tokens=800,
        total_tokens=2800,
        task_type='translation'
    )
    print("✓ Tracked gpt-4o call (translation): 2000 prompt + 800 completion = 2800 tokens")

    # Simulate call 4: Another gpt-4o-mini call
    tracker.track_usage(
        model='gpt-4o-mini',
        prompt_tokens=600,
        completion_tokens=150,
        total_tokens=750,
        task_type='brand_detection'
    )
    print("✓ Tracked gpt-4o-mini call (brand_detection): 600 prompt + 150 completion = 750 tokens")

    # Get and verify statistics
    print("\n" + "=" * 80)
    print("Getting statistics...")
    stats = tracker.get_statistics()

    print(f"\nTotal calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost_usd']:.4f}")

    # Verify expected values
    assert stats['total_calls'] == 4, f"Expected 4 calls, got {stats['total_calls']}"
    assert stats['total_tokens'] == 6550, f"Expected 6550 tokens, got {stats['total_tokens']}"
    assert stats['total_prompt_tokens'] == 4900, f"Expected 4900 prompt tokens, got {stats['total_prompt_tokens']}"
    assert stats['total_completion_tokens'] == 1650, f"Expected 1650 completion tokens, got {stats['total_completion_tokens']}"

    # Check model breakdown
    assert 'gpt-4o' in stats['by_model'], "gpt-4o not in model breakdown"
    assert 'gpt-4o-mini' in stats['by_model'], "gpt-4o-mini not in model breakdown"
    assert stats['by_model']['gpt-4o']['calls'] == 2, "Expected 2 gpt-4o calls"
    assert stats['by_model']['gpt-4o-mini']['calls'] == 2, "Expected 2 gpt-4o-mini calls"

    print("\n✓ All statistics verified correctly!")

    # Print formatted statistics
    print("\n" + "=" * 80)
    print("Displaying formatted statistics:")
    print("=" * 80)
    tracker.print_statistics()

    print("\n✓ Test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_token_tracking()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
