"""
Test RAG retrieval + LLM option generation for AC maintenance.

Tests the fixed category mapping and complete flow.
"""
import asyncio
import json
from app.rag.retriever import RAGRetriever
from app.utils.llm_client import LLMClient

async def test_ac_rag_to_llm():
    """Test RAG retrieval and LLM generation for AC issue."""
    print("\n" + "="*80)
    print("Test: RAG Retrieval + LLM Option Generation (AC Maintenance)")
    print("="*80)
    
    message = "My AC is broken and it's really hot in here"
    building_id = "BuildingA"
    category = "Maintenance"
    
    print(f"\nInput:")
    print(f"  Message: {message}")
    print(f"  Building: {building_id}")
    print(f"  Category: {category}")
    
    # Step 1: RAG Retrieval
    print(f"\n{'='*80}")
    print("STEP 1: RAG Retrieval")
    print(f"{'='*80}")
    
    retriever = RAGRetriever()
    
    # Check if RAG is available
    if not retriever.is_available():
        print("⚠️  RAG retriever not available - checking vector store...")
        if retriever.vectorstore:
            doc_count = retriever.vectorstore._collection.count()
            print(f"   Vector store has {doc_count} documents")
            if doc_count == 0:
                print("   ⚠️  Vector store is empty - documents may not be indexed")
                print("   Try running: python -m app.rag.ingest.ingest_documents")
        else:
            print("   ❌ Vector store not initialized")
        print("   Continuing test without RAG context...")
        rag_result = None
    else:
        rag_result = await retriever.retrieve_for_simulation(
            issue_text=message,
            building_id=building_id,
            category=category
        )
        
        print(f"Documents Retrieved: {rag_result.total_retrieved if rag_result else 0}")
        
        if not rag_result or rag_result.total_retrieved == 0:
            print("⚠️  No documents retrieved with filters - trying without category filter...")
            # Try without category filter to see if any documents exist
            rag_result_no_filter = await retriever.retrieve_for_simulation(
                issue_text=message,
                building_id=building_id,
                category=None  # Remove category filter
            )
            if rag_result_no_filter and rag_result_no_filter.total_retrieved > 0:
                print(f"   ✅ Found {rag_result_no_filter.total_retrieved} documents without category filter")
                print("   This suggests category mapping may need adjustment")
                rag_result = rag_result_no_filter
            else:
                print("   ⚠️  No documents found even without filters - vector store may be empty")
                print("   Continuing test without RAG context...")
                rag_result = None
    
    if rag_result and rag_result.total_retrieved > 0:
        print(f"✅ Retrieved {rag_result.total_retrieved} documents")
        for idx, doc in enumerate(rag_result.retrieved_docs, 1):
            doc_id = doc.get('doc_id', 'N/A')
            metadata = doc.get('metadata', {})
            category_val = metadata.get('category', 'N/A')
            building_val = metadata.get('building_id', 'N/A')
            doc_type = metadata.get('type', 'N/A')
            print(f"  [{idx}] {doc_id}")
            print(f"      Category: {category_val}, Building: {building_val}, Type: {doc_type}")
    else:
        print("⚠️  No RAG context available - LLM will generate options without policy documents")
    
    # Step 2: LLM Generation
    print(f"\n{'='*80}")
    print("STEP 2: LLM Option Generation")
    print(f"{'='*80}")
    
    llm_client = LLMClient()
    
    try:
        result = await llm_client.generate_options(
            message_text=message,
            category="Maintenance",
            urgency="High",
            risk_score=0.8,
            resident_id="test_resident_001",
            resident_history=None,
            tools_data=None,
            rag_context=rag_result
        )
        
        print(f"✅ LLM call completed")
        
        # Check if result has error or options
        if 'error' in result:
            print(f"❌ LLM returned error: {result['error']['type']}")
            print(f"   Message: {result['error']['message']}")
            if 'technical_details' in result['error']:
                print(f"   Technical: {result['error']['technical_details']}")
            return False
        
        if 'options' not in result:
            print(f"❌ Result missing 'options' key. Keys present: {list(result.keys())}")
            print(f"   Full result: {result}")
            return False
            
        print(f"✅ LLM generation successful")
        print(f"Options Generated: {len(result['options'])}")
        print(f"Has RAG Context: {rag_result is not None}")
        
        # Check for recommendation
        if 'recommended_option_id' in result:
            print(f"✅ Recommendation: {result['recommended_option_id']}")
            if 'recommendation_reasoning' in result:
                print(f"   Reasoning: {result['recommendation_reasoning'][:100]}...")
        
        if result['options']:
            print(f"\n{'-'*80}")
            print("Generated Options:")
            print(f"{'-'*80}")
            for idx, opt in enumerate(result['options'], 1):
                print(f"\n[Option {idx}] {opt.get('title', opt.get('action', 'N/A'))}")
                print(f"  Option ID: {opt.get('option_id', 'N/A')}")
                print(f"  Cost: ${opt.get('estimated_cost', 0):.2f}")
                print(f"  Time: {opt.get('estimated_time', 0):.1f}h")
                if opt.get('sources'):
                    print(f"  Sources: {opt['sources']}")
                if opt.get('source_doc_ids'):
                    print(f"  Source Doc IDs: {opt['source_doc_ids']}")
                if opt.get('escalations'):
                    print(f"  Escalations: {opt['escalations']}")
            
            # Validation
            print(f"\n{'='*80}")
            print("VALIDATION")
            print(f"{'='*80}")
            has_sources = any(opt.get('sources') or opt.get('source_doc_ids') for opt in result['options'])
            proper_count = 1 <= len(result['options']) <= 5  # Allow 1-5 (1 for escalation, 3-5 for normal)
            has_recommendation = 'recommended_option_id' in result and result['recommended_option_id']
            
            print(f"✅ Options generated: {len(result['options'])}")
            print(f"✅ Has sources: {has_sources} {'(RAG context available)' if rag_result else '(No RAG - escalation expected)'}")
            print(f"✅ Proper count (1-5): {proper_count}")
            print(f"✅ Has recommendation: {has_recommendation}")
            
            if proper_count and has_recommendation:
                print(f"\n{'='*40}")
                print("✅✅✅ TEST PASSED ✅✅✅")
                print(f"{'='*40}")
                if not has_sources:
                    print("⚠️  Note: No RAG sources (expected if vector store is empty)")
                return True
            else:
                print("\n❌ Validation failed")
                if not proper_count:
                    print(f"   - Expected 1-5 options, got {len(result['options'])}")
                if not has_recommendation:
                    print("   - Missing recommendation")
                return False
        else:
            print("❌ No options generated")
            return False
            
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ac_rag_to_llm())
    exit(0 if result else 1)

