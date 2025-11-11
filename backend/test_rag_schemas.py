#!/usr/bin/env python3
"""
Test script to validate RAG schema modifications in schemas.py
Tests backward compatibility and new RAG fields.
"""

import sys
from datetime import datetime

# Import all models
from app.models.schemas import (
    SimulatedOption,
    DecisionResponse,
    DocumentChunk,
    RetrievalContext,
    RAGOption,
    RuleContext
)


def test_simulated_option_backward_compatibility():
    """Test that SimulatedOption still works without source_doc_ids (backward compatible)"""
    print("✓ Testing SimulatedOption backward compatibility...")
    
    # Create without RAG field (legacy behavior)
    option_legacy = SimulatedOption(
        option_id="opt_1",
        action="Send maintenance request",
        estimated_cost=150.0,
        estimated_time=2.5,
        reasoning="Based on urgency and cost"
    )
    assert option_legacy.source_doc_ids is None
    print(f"  Legacy option (no RAG): {option_legacy.option_id}")
    
    # Create with RAG field (new behavior)
    option_rag = SimulatedOption(
        option_id="opt_2",
        action="Dispatch emergency plumber",
        estimated_cost=250.0,
        estimated_time=1.0,
        reasoning="High urgency based on policy",
        source_doc_ids=["policy_maint_1.0", "sop_emergency_1.0"]
    )
    assert option_rag.source_doc_ids == ["policy_maint_1.0", "sop_emergency_1.0"]
    print(f"  RAG-enabled option: {option_rag.option_id} with {len(option_rag.source_doc_ids)} sources")
    print("  ✅ SimulatedOption is backward compatible")


def test_decision_response_backward_compatibility():
    """Test that DecisionResponse still works without RAG fields"""
    print("\n✓ Testing DecisionResponse backward compatibility...")
    
    # Create without RAG fields (legacy)
    decision_legacy = DecisionResponse(
        chosen_action="Send maintenance crew",
        chosen_option_id="opt_1",
        reasoning="Cost-effective solution",
        alternatives_considered=["opt_2", "opt_3"],
        policy_scores={"opt_1": 0.85, "opt_2": 0.72}
    )
    assert decision_legacy.rule_sources is None
    assert decision_legacy.rule_object is None
    print(f"  Legacy decision: {decision_legacy.chosen_option_id}")
    
    # Create with RAG fields (new)
    decision_rag = DecisionResponse(
        chosen_action="Dispatch emergency plumber",
        chosen_option_id="opt_2",
        reasoning="High urgency requires immediate response per policy",
        alternatives_considered=["opt_1"],
        policy_scores={"opt_2": 0.92, "opt_1": 0.65},
        rule_sources=["policy_maint_1.0", "sop_emergency_1.0"],
        rule_object={
            "rule_id": "emergency_maintenance",
            "threshold": "< 2 hours",
            "escalation_required": False
        }
    )
    assert decision_rag.rule_sources == ["policy_maint_1.0", "sop_emergency_1.0"]
    assert decision_rag.rule_object["rule_id"] == "emergency_maintenance"
    print(f"  RAG-enabled decision: {decision_rag.chosen_option_id} with {len(decision_rag.rule_sources)} rule sources")
    print("  ✅ DecisionResponse is backward compatible")


def test_document_chunk():
    """Test new DocumentChunk schema"""
    print("\n✓ Testing DocumentChunk schema...")
    
    chunk = DocumentChunk(
        doc_id="policy_noise_1.0",
        chunk_id="policy_noise_1.0_chunk_0",
        text="Quiet hours are 10 PM to 8 AM. Violations may result in warnings.",
        metadata={
            "type": "policy",
            "category": "community",
            "building_id": "all_buildings",
            "version": "1.0"
        },
        embedding_id="vec_123abc"
    )
    assert chunk.doc_id == "policy_noise_1.0"
    assert "Quiet hours" in chunk.text
    assert chunk.metadata["type"] == "policy"
    print(f"  Created DocumentChunk: {chunk.doc_id} ({len(chunk.text)} chars)")
    print("  ✅ DocumentChunk schema valid")


def test_retrieval_context():
    """Test new RetrievalContext schema"""
    print("\n✓ Testing RetrievalContext schema...")
    
    context = RetrievalContext(
        query="What is the noise complaint policy?",
        retrieved_docs=[
            {
                "doc_id": "policy_noise_1.0",
                "text": "Quiet hours are 10 PM to 8 AM...",
                "score": 0.89,
                "metadata": {"type": "policy", "category": "community"}
            },
            {
                "doc_id": "sop_noise_complaint_1.0",
                "text": "When handling noise complaints...",
                "score": 0.76,
                "metadata": {"type": "sop", "category": "operations"}
            }
        ],
        total_retrieved=2,
        retrieval_method="similarity_search"
    )
    assert context.total_retrieved == 2
    assert len(context.retrieved_docs) == 2
    assert context.retrieved_docs[0]["score"] == 0.89
    print(f"  Created RetrievalContext: '{context.query[:40]}...' with {context.total_retrieved} docs")
    print("  ✅ RetrievalContext schema valid")


def test_rag_option():
    """Test new RAGOption schema"""
    print("\n✓ Testing RAGOption schema...")
    
    base_option = SimulatedOption(
        option_id="opt_1",
        action="Send noise complaint warning",
        estimated_cost=0.0,
        estimated_time=0.5,
        reasoning="Based on noise complaint policy",
        source_doc_ids=["policy_noise_1.0"]
    )
    
    retrieval = RetrievalContext(
        query="noise complaint at night",
        retrieved_docs=[{"doc_id": "policy_noise_1.0", "score": 0.89}],
        total_retrieved=1,
        retrieval_method="similarity_search"
    )
    
    rag_option = RAGOption(
        option=base_option,
        retrieval_context=retrieval,
        confidence_score=0.89
    )
    
    assert rag_option.option.option_id == "opt_1"
    assert rag_option.confidence_score == 0.89
    assert rag_option.retrieval_context.total_retrieved == 1
    print(f"  Created RAGOption: {rag_option.option.option_id} with confidence {rag_option.confidence_score}")
    print("  ✅ RAGOption schema valid")


def test_rule_context():
    """Test new RuleContext schema"""
    print("\n✓ Testing RuleContext schema...")
    
    rule = RuleContext(
        rule_id="noise_quiet_hours",
        rule_text="Quiet hours are enforced from 10 PM to 8 AM. First violation results in written warning.",
        source_docs=["policy_noise_1.0"],
        confidence=0.92,
        policy_section="community_standards",
        metadata={"severity": "medium", "escalation_threshold": 3}
    )
    
    assert rule.rule_id == "noise_quiet_hours"
    assert rule.confidence == 0.92
    assert len(rule.source_docs) == 1
    assert rule.metadata["escalation_threshold"] == 3
    print(f"  Created RuleContext: {rule.rule_id} (confidence: {rule.confidence})")
    print("  ✅ RuleContext schema valid")


def main():
    """Run all schema validation tests"""
    print("=" * 60)
    print("RAG Schema Validation Tests")
    print("=" * 60)
    
    try:
        test_simulated_option_backward_compatibility()
        test_decision_response_backward_compatibility()
        test_document_chunk()
        test_retrieval_context()
        test_rag_option()
        test_rule_context()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - RAG schemas are valid and backward compatible")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
