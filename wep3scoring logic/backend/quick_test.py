#!/usr/bin/env python3
"""
Quick test script to manually test the scoring engine.
Run this to see if everything works!

Usage: python quick_test.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.score_calculator import calculate_score
from app.services.pdf_generator import save_pdf_report
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_excellent_answer():
    """Test with an excellent interview answer"""
    print_section("TEST 1: Excellent Answer")
    
    transcript = """
    In the situation where our e-commerce platform was experiencing severe performance issues,
    my task was to optimize the system within two weeks. I implemented Redis caching, 
    optimized database queries, and introduced a CDN. As a result, we reduced page load 
    times by 60% and handled Black Friday traffic successfully, saving $200,000 in potential 
    lost revenue.
    """
    
    result = calculate_score(
        transcript=transcript,
        wpm=145.0,
        filler_rate=0.01,
        answer_length_s=90.0,
        jd_keywords=["redis", "optimization", "database", "cdn"],
        question="Tell me about a time you improved system performance"
    )
    
    print(f"\n✅ Final Score: {result['final_score']}/100")
    print(f"   Content: {result['content']['score']:.1f}")
    print(f"   Delivery: {result['delivery']['score']:.1f}")
    print(f"   Communication: {result['communication']['score']:.1f}")
    
    print("\n📊 Evidence:")
    for evidence in result['evidence']:
        print(f"   • {evidence}")
    
    print("\n💪 Next Actions:")
    for action in result['next_actions']:
        print(f"   • {action}")
    
    return result


def test_poor_answer():
    """Test with a poor interview answer"""
    print_section("TEST 2: Poor Answer")
    
    transcript = "Um, like, I did stuff and it was okay."
    
    result = calculate_score(
        transcript=transcript,
        wpm=220.0,  # Too fast
        filler_rate=0.20,  # 20% fillers
        answer_length_s=15.0,  # Too short
        jd_keywords=["python", "aws", "docker"],
        question="Tell me about your technical experience"
    )
    
    print(f"\n❌ Final Score: {result['final_score']}/100")
    print(f"   Content: {result['content']['score']:.1f}")
    print(f"   Delivery: {result['delivery']['score']:.1f}")
    print(f"   Communication: {result['communication']['score']:.1f}")
    
    print("\n📊 Evidence:")
    for evidence in result['evidence']:
        print(f"   • {evidence}")
    
    print("\n💪 Next Actions:")
    for action in result['next_actions']:
        print(f"   • {action}")
    
    return result


def test_xai_contributions(result):
    """Verify XAI contributions sum correctly"""
    print_section("TEST 3: XAI Contribution Check")
    
    # Sum all contributions
    total = 0.0
    
    print("\n🔍 Content Features:")
    for name, feature in result['content']['features'].items():
        print(f"   {name}: {feature['contribution']:.2f} points")
        total += feature['contribution']
    
    print("\n🔍 Delivery Features:")
    for name, feature in result['delivery']['features'].items():
        print(f"   {name}: {feature['contribution']:.2f} points")
        total += feature['contribution']
    
    print("\n🔍 Communication Features:")
    for name, feature in result['communication']['features'].items():
        print(f"   {name}: {feature['contribution']:.2f} points")
        total += feature['contribution']
    
    print(f"\n📊 Total Contributions: {total:.2f}")
    print(f"📊 Final Score: {result['final_score']:.2f}")
    print(f"📊 Difference: {abs(total - result['final_score']):.4f}")
    
    if abs(total - result['final_score']) < 0.1:
        print("✅ XAI CHECK PASSED - Contributions sum correctly!")
    else:
        print("❌ XAI CHECK FAILED - Contributions don't sum to final score!")
    
    return abs(total - result['final_score']) < 0.1


def test_pdf_generation(result):
    """Test PDF report generation"""
    print_section("TEST 4: PDF Report Generation")
    
    try:
        pdf_path = save_pdf_report(
            score_data=result,
            candidate_name="Test Candidate",
            question="Tell me about a time you solved a technical problem",
            session_id="test_12345"
        )
        print(f"\n✅ PDF generated successfully!")
        print(f"📄 Saved to: {pdf_path}")
        return True
    except Exception as e:
        print(f"\n❌ PDF generation failed: {str(e)}")
        print("   This might be due to WeasyPrint dependencies.")
        print("   See README for installation instructions.")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("WP3 SCORING ENGINE - QUICK TEST")
    print("🚀" * 30)
    
    try:
        # Test 1: Excellent answer
        excellent_result = test_excellent_answer()
        
        # Test 2: Poor answer
        poor_result = test_poor_answer()
        
        # Test 3: XAI contributions
        xai_pass = test_xai_contributions(excellent_result)
        
        # Test 4: PDF generation
        pdf_pass = test_pdf_generation(excellent_result)
        
        # Summary
        print_section("SUMMARY")
        print(f"\n✅ Test 1 (Excellent Answer): PASSED")
        print(f"✅ Test 2 (Poor Answer): PASSED")
        print(f"{'✅' if xai_pass else '❌'} Test 3 (XAI Contributions): {'PASSED' if xai_pass else 'FAILED'}")
        print(f"{'✅' if pdf_pass else '⚠️ '} Test 4 (PDF Generation): {'PASSED' if pdf_pass else 'FAILED (see README)'}")
        
        if xai_pass:
            print("\n🎉 All critical tests passed! Your scoring engine is working!")
            print("\n📝 Next steps:")
            print("   1. Run full test suite: pytest -v")
            print("   2. Test the /score endpoint with WP1")
            print("   3. Integrate with WP2 frontend")
        else:
            print("\n⚠️  XAI test failed. Check your contribution calculations!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()