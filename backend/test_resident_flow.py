#!/usr/bin/env python3
"""
Test script to verify the resident submission flow end-to-end.
Tests the complete flow: Classification -> Risk Prediction -> Simulation (with LLM) -> Response
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_resident_flow():
    """Test the resident submission flow."""
    print("\n" + "="*80)
    print("🧪 TESTING RESIDENT SUBMISSION FLOW (with Gemini 2.5 Flash Experimental)")
    print("="*80 + "\n")
    
    # Import after path setup
    from app.models.schemas import MessageRequest
    from app.services.message_intake import submit_request
    
    # Test data
    test_request = MessageRequest(
        resident_id="RES_BuildingA_1001",
        message_text="My AC is not working and it's very hot in my apartment",
        category=None,  # Let system classify
        urgency=None    # Let system classify
    )
    
    print(f"📝 Test Request:")
    print(f"   Resident ID: {test_request.resident_id}")
    print(f"   Message: {test_request.message_text}")
    print(f"\n{'─'*80}\n")
    
    try:
        # Submit request
        print("🔄 Step 1: Submitting request...")
        result = await submit_request(test_request)
        
        # Check result
        if isinstance(result, dict):
            if result.get('status') == 'error':
                print(f"\n❌ ERROR: {result.get('error_type')}")
                print(f"   Message: {result.get('message')}")
                print(f"   User Message: {result.get('action_required')}")
                return False
            
            # Success!
            print(f"\n✅ Step 2: Classification successful")
            classification = result.get('classification', {})
            print(f"   Category: {classification.get('category')}")
            print(f"   Urgency: {classification.get('urgency')}")
            print(f"   Intent: {classification.get('intent')}")
            print(f"   Confidence: {classification.get('confidence', 0):.2f}")
            
            risk = result.get('risk_assessment')
            if risk:
                print(f"\n✅ Step 3: Risk assessment successful")
                print(f"   Risk Score: {risk.get('risk_forecast', 0):.4f}")
                print(f"   Risk Level: {risk.get('risk_level')}")
            
            simulation = result.get('simulation')
            if simulation:
                print(f"\n✅ Step 4: Simulation successful")
                print(f"   Options Generated: {simulation.get('options_generated')}")
                print(f"   Recommended Option: {simulation.get('recommended_option_id')}")
                
                # Display options
                options = simulation.get('options', [])
                print(f"\n📋 Generated Options:")
                for idx, opt in enumerate(options, 1):
                    print(f"\n   Option {idx}: {opt.get('title', 'N/A')}")
                    print(f"      ID: {opt.get('option_id')}")
                    print(f"      Action: {opt.get('action', 'N/A')[:100]}...")
                    print(f"      Cost: ${opt.get('estimated_cost', 0):.2f}")
                    print(f"      Time: {opt.get('estimated_time', 0):.1f}h")
                    print(f"      Satisfaction: {opt.get('satisfaction_score', 0)*100:.0f}%")
                    is_recommended = opt.get('option_id') == simulation.get('recommended_option_id')
                    if is_recommended:
                        print(f"      ⭐ RECOMMENDED")
                
                # Display recommendation reasoning
                rec_reasoning = simulation.get('recommendation_reasoning')
                if rec_reasoning:
                    print(f"\n💡 Recommendation Reasoning:")
                    print(f"   {rec_reasoning}")
                
                print(f"\n{'─'*80}")
                print(f"✅ ALL TESTS PASSED - Flow completed successfully!")
                print(f"   Request ID: {result.get('request_id')}")
                print(f"   Status: {result.get('status')}")
                print("="*80 + "\n")
                return True
            else:
                print("\n❌ ERROR: No simulation results in response")
                return False
        else:
            print(f"\n❌ ERROR: Unexpected response type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION CAUGHT: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_model_configuration():
    """Test that the model is correctly configured to gemini-2.5-flash."""
    print("\n" + "="*80)
    print("🔧 CHECKING MODEL CONFIGURATION")
    print("="*80 + "\n")
    
    from app.config import get_settings
    settings = get_settings()
    
    print(f"📌 Configuration:")
    print(f"   GEMINI_MODEL: {settings.GEMINI_MODEL}")
    print(f"   GOOGLE_API_KEY: {'*' * 10}{settings.GOOGLE_API_KEY[-4:]}")
    print(f"   RAG_ENABLED: {settings.RAG_ENABLED}")
    print(f"   RETRIEVAL_K: {settings.RETRIEVAL_K}")
    print(f"   MAX_CONTEXT_TOKENS: {settings.MAX_CONTEXT_TOKENS}")
    
    if settings.GEMINI_MODEL == "gemini-2.5-flash":
        print(f"\n✅ Model correctly set to gemini-2.5-flash")
    else:
        print(f"\n⚠️  WARNING: Model is set to {settings.GEMINI_MODEL} instead of gemini-2.5-flash")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_model_configuration())
    success = asyncio.run(test_resident_flow())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

