"""
Integration tests for RAG schemas.
Tests the schema models defined in app/models/schemas.py
"""
import pytest
from datetime import datetime
from app.models.schemas import (
    SimulatedOption,
    DecisionResponse,
    DocumentChunk,
    RetrievalContext,
    RAGOption,
    RuleContext
)


class TestSimulatedOptionIntegration:
    """Integration tests for SimulatedOption with RAG fields."""
    
    def test_simulated_option_without_rag(self):
        """Test SimulatedOption works without RAG fields (backward compatibility)."""
        option = SimulatedOption(
            option_id="opt_1",
            action="Send maintenance crew",
            estimated_cost=150.0,
            estimated_time=2.5,
            reasoning="Cost-effective solution"
        )
        
        assert option.source_doc_ids is None
        assert option.option_id == "opt_1"
    
    def test_simulated_option_with_rag(self):
        """Test SimulatedOption with RAG source citations."""
        option = SimulatedOption(
            option_id="opt_2",
            action="Dispatch emergency HVAC tech",
            estimated_cost=250.0,
            estimated_time=1.0,
            reasoning="Per policy, high urgency requires immediate response",
            source_doc_ids=["policy_maint_1.0", "sop_emergency_1.0"]
        )
        
        assert len(option.source_doc_ids) == 2
        assert "policy_maint_1.0" in option.source_doc_ids
    
    def test_simulated_option_serialization(self):
        """Test that SimulatedOption serializes correctly to JSON."""
        option = SimulatedOption(
            option_id="opt_1",
            action="Test action",
            estimated_cost=100.0,
            estimated_time=1.5,
            reasoning="Test reasoning",
            source_doc_ids=["doc1", "doc2"]
        )
        
        json_data = option.model_dump()
        
        assert json_data["source_doc_ids"] == ["doc1", "doc2"]
        assert json_data["option_id"] == "opt_1"


class TestDecisionResponseIntegration:
    """Integration tests for DecisionResponse with RAG fields."""
    
    def test_decision_response_without_rag(self):
        """Test DecisionResponse works without RAG fields (backward compatibility)."""
        decision = DecisionResponse(
            chosen_action="Send crew",
            chosen_option_id="opt_1",
            reasoning="Best option",
            alternatives_considered=["opt_2"],
            policy_scores={"opt_1": 0.9}
        )
        
        assert decision.rule_sources is None
        assert decision.rule_object is None
    
    def test_decision_response_with_rag(self):
        """Test DecisionResponse with RAG rule citations."""
        decision = DecisionResponse(
            chosen_action="Dispatch emergency tech",
            chosen_option_id="opt_1",
            reasoning="Meets policy requirements",
            alternatives_considered=["opt_2", "opt_3"],
            policy_scores={"opt_1": 0.95, "opt_2": 0.75},
            rule_sources=["policy_maint_1.0", "sop_emergency_1.0"],
            rule_object={
                "rule_id": "emergency_response",
                "threshold": "2 hours",
                "cost_limit": 300
            }
        )
        
        assert len(decision.rule_sources) == 2
        assert decision.rule_object["rule_id"] == "emergency_response"
    
    def test_decision_response_serialization(self):
        """Test DecisionResponse serialization with RAG fields."""
        decision = DecisionResponse(
            chosen_action="Test action",
            chosen_option_id="opt_1",
            reasoning="Test reasoning",
            alternatives_considered=[],
            rule_sources=["rule1"],
            rule_object={"test": "value"}
        )
        
        json_data = decision.model_dump()
        
        assert json_data["rule_sources"] == ["rule1"]
        assert json_data["rule_object"]["test"] == "value"


class TestDocumentChunkIntegration:
    """Integration tests for DocumentChunk schema."""
    
    def test_document_chunk_from_sample(self, sample_policies):
        """Test creating DocumentChunk from sample policy."""
        policy = sample_policies[0]
        
        chunk = DocumentChunk(
            doc_id=policy["doc_id"],
            chunk_id=f"{policy['doc_id']}_chunk_0",
            text=policy["text"],
            metadata={
                "type": policy["type"],
                "category": policy["category"],
                "building_id": policy["building_id"]
            }
        )
        
        assert chunk.doc_id == policy["doc_id"]
        assert chunk.metadata["type"] == "policy"
    
    def test_document_chunk_with_embedding_id(self):
        """Test DocumentChunk with embedding ID."""
        chunk = DocumentChunk(
            doc_id="test_doc",
            chunk_id="test_doc_chunk_0",
            text="Test text",
            metadata={},
            embedding_id="vec_abc123"
        )
        
        assert chunk.embedding_id == "vec_abc123"
    
    def test_document_chunk_json_schema(self):
        """Test DocumentChunk JSON schema example."""
        chunk = DocumentChunk(
            doc_id="policy_noise_1.0",
            chunk_id="policy_noise_1.0_chunk_0",
            text="Quiet hours are 10 PM to 8 AM...",
            metadata={
                "type": "policy",
                "category": "community",
                "building_id": "all_buildings"
            },
            embedding_id="vec_123"
        )
        
        json_data = chunk.model_dump()
        assert "doc_id" in json_data
        assert "metadata" in json_data


class TestRetrievalContextIntegration:
    """Integration tests for RetrievalContext schema."""
    
    def test_retrieval_context_basic(self):
        """Test basic RetrievalContext creation."""
        context = RetrievalContext(
            query="noise complaint",
            retrieved_docs=[
                {
                    "doc_id": "policy_noise_1.0",
                    "text": "Sample policy text",
                    "score": 0.89,
                    "metadata": {"type": "policy"}
                }
            ],
            total_retrieved=1
        )
        
        assert context.query == "noise complaint"
        assert context.total_retrieved == 1
        assert len(context.retrieved_docs) == 1
    
    def test_retrieval_context_multiple_docs(self, sample_policies):
        """Test RetrievalContext with multiple documents."""
        retrieved = [
            {
                "doc_id": policy["doc_id"],
                "text": policy["text"][:200],
                "score": 0.9 - i * 0.1,
                "metadata": {"type": policy["type"]}
            }
            for i, policy in enumerate(sample_policies[:3])
        ]
        
        context = RetrievalContext(
            query="policy search",
            retrieved_docs=retrieved,
            total_retrieved=len(retrieved)
        )
        
        assert context.total_retrieved == 3
        assert all("score" in doc for doc in context.retrieved_docs)
    
    def test_retrieval_context_with_timestamp(self):
        """Test RetrievalContext includes timestamp."""
        context = RetrievalContext(
            query="test query",
            retrieved_docs=[],
            total_retrieved=0
        )
        
        assert isinstance(context.retrieval_timestamp, datetime)
        assert context.retrieval_method == "similarity_search"


class TestRAGOptionIntegration:
    """Integration tests for RAGOption schema."""
    
    def test_rag_option_complete(self):
        """Test complete RAGOption with all fields."""
        base_option = SimulatedOption(
            option_id="opt_1",
            action="Dispatch tech",
            estimated_cost=250.0,
            estimated_time=1.5,
            reasoning="Based on policy",
            source_doc_ids=["policy_1"]
        )
        
        retrieval = RetrievalContext(
            query="HVAC emergency",
            retrieved_docs=[{"doc_id": "policy_1", "score": 0.9}],
            total_retrieved=1
        )
        
        rag_option = RAGOption(
            option=base_option,
            retrieval_context=retrieval,
            confidence_score=0.9
        )
        
        assert rag_option.option.option_id == "opt_1"
        assert rag_option.confidence_score == 0.9
        assert rag_option.retrieval_context.total_retrieved == 1
    
    def test_rag_option_without_context(self):
        """Test RAGOption without retrieval context (optional)."""
        base_option = SimulatedOption(
            option_id="opt_1",
            action="Test action",
            estimated_cost=100.0,
            estimated_time=1.0,
            reasoning="Test"
        )
        
        rag_option = RAGOption(
            option=base_option
        )
        
        assert rag_option.retrieval_context is None
        assert rag_option.confidence_score is None


class TestRuleContextIntegration:
    """Integration tests for RuleContext schema."""
    
    def test_rule_context_basic(self):
        """Test basic RuleContext creation."""
        rule = RuleContext(
            rule_id="noise_quiet_hours",
            rule_text="Quiet hours are 10 PM to 8 AM",
            source_docs=["policy_noise_1.0"],
            confidence=0.92
        )
        
        assert rule.rule_id == "noise_quiet_hours"
        assert rule.confidence == 0.92
        assert len(rule.source_docs) == 1
    
    def test_rule_context_with_metadata(self):
        """Test RuleContext with full metadata."""
        rule = RuleContext(
            rule_id="emergency_hvac",
            rule_text="Emergency HVAC requires 2-hour response",
            source_docs=["policy_maint_1.0", "sop_emergency_1.0"],
            confidence=0.95,
            policy_section="emergency_response",
            metadata={
                "severity": "high",
                "cost_limit": 300,
                "escalation_threshold": 2
            }
        )
        
        assert rule.policy_section == "emergency_response"
        assert rule.metadata["cost_limit"] == 300
        assert len(rule.source_docs) == 2
    
    def test_rule_context_json_schema(self):
        """Test RuleContext JSON schema example."""
        rule = RuleContext(
            rule_id="test_rule",
            rule_text="Test rule text",
            source_docs=["doc1"],
            confidence=0.8,
            policy_section="test_section",
            metadata={"key": "value"}
        )
        
        json_data = rule.model_dump()
        
        assert json_data["rule_id"] == "test_rule"
        assert json_data["confidence"] == 0.8
        assert json_data["metadata"]["key"] == "value"


class TestSchemaInteroperability:
    """Test how RAG schemas work together."""
    
    def test_option_to_rag_option_flow(self):
        """Test converting SimulatedOption to RAGOption."""
        # Simulate agent generating option
        option = SimulatedOption(
            option_id="opt_1",
            action="Test action",
            estimated_cost=100.0,
            estimated_time=1.0,
            reasoning="Test reasoning",
            source_doc_ids=["doc1", "doc2"]
        )
        
        # Simulate RAG retrieval
        retrieval = RetrievalContext(
            query="test query",
            retrieved_docs=[
                {"doc_id": "doc1", "score": 0.9},
                {"doc_id": "doc2", "score": 0.8}
            ],
            total_retrieved=2
        )
        
        # Wrap in RAGOption
        rag_option = RAGOption(
            option=option,
            retrieval_context=retrieval,
            confidence_score=0.85
        )
        
        # Verify flow
        assert rag_option.option.source_doc_ids == retrieval.retrieved_docs[0]["doc_id"] or \
               rag_option.option.source_doc_ids == [retrieval.retrieved_docs[0]["doc_id"], retrieval.retrieved_docs[1]["doc_id"]]
    
    def test_decision_with_rules_flow(self):
        """Test DecisionResponse with RuleContext."""
        # Create rule from KB
        rule = RuleContext(
            rule_id="test_rule",
            rule_text="Test rule text",
            source_docs=["policy_1"],
            confidence=0.9
        )
        
        # Create decision referencing rule
        decision = DecisionResponse(
            chosen_action="Action based on rule",
            chosen_option_id="opt_1",
            reasoning=f"Following {rule.rule_id}",
            alternatives_considered=[],
            rule_sources=rule.source_docs,
            rule_object={
                "rule_id": rule.rule_id,
                "confidence": rule.confidence
            }
        )
        
        # Verify linkage
        assert decision.rule_sources == rule.source_docs
        assert decision.rule_object["rule_id"] == rule.rule_id
