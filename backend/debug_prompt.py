"""
Debug: Print the actual prompt being sent to LLM.
"""
import asyncio
from app.rag.retriever import RAGRetriever
from app.prompts.simulation_prompt import SimulationPrompt

async def debug_prompt():
    """Print the exact prompt being sent to LLM."""
    print("\n" + "="*80)
    print("Debug: SimulationPrompt Content")
    print("="*80)
    
    message = "My AC is broken and it's really hot in here"
    building_id = "BuildingA"
    category = "Maintenance"
    
    # Get RAG context
    retriever = RAGRetriever()
    rag_result = await retriever.retrieve_for_simulation(
        issue_text=message,
        building_id=building_id,
        category=category
    )
    
    print(f"\nRAG Documents: {rag_result.total_retrieved if rag_result else 0}")
    
    # Create prompt
    sim_prompt = SimulationPrompt()
    prompt_text = sim_prompt.render(
        message_text=message,
        category=category,
        urgency="High",
        risk_score=0.8,
        resident_id="test_resident_001",
        resident_history=None,
        tools_data=None,
        rag_context=rag_result
    )
    
    print(f"\n{'='*80}")
    print("PROMPT TEXT:")
    print(f"{'='*80}")
    print(prompt_text)
    print(f"\n{'='*80}")
    print(f"Prompt Length: {len(prompt_text)} characters")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(debug_prompt())
