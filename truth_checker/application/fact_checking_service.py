"""Implementation of the fact checking service using LangChain and LangGraph."""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union

import langgraph.graph as lg
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda

from truth_checker.domain.models import Claim, FactCheckResult, FactCheckVerdict, Source
from truth_checker.domain.ports import FactCheckingService, KnowledgeRepository

logger = logging.getLogger(__name__)

# Define prompt templates for fact checking

QUERY_CONSTRUCTION_TEMPLATE = """You are an expert fact-checker. Your task is to create search queries that will help verify the following claim:

Claim: {claim}

Context: {context}

Generate 3 concise search queries that would help verify this claim. These should be specific, focused, and diverse to maximize the chance of finding relevant information. 

Return your queries in JSON format:
{{"queries": ["query1", "query2", "query3"]}}"""

EVIDENCE_ANALYSIS_TEMPLATE = """You are a meticulous fact-checker working to verify claims using evidence.

CLAIM TO VERIFY: {claim}

CONTEXT: {context}

EVIDENCE:
{evidence}

Your task is to analyze this evidence and determine:
1. Is the claim supported, contradicted, or neither based on the evidence?
2. How reliable is the evidence?
3. What specific parts of the evidence are most relevant to the claim?
4. Is more evidence needed to reach a confident verdict?

Return your analysis in this JSON format:
{{
  "verdict": "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE",
  "confidence": <float between 0.0 and 1.0>,
  "key_evidence": "specific quotes or information from the evidence that directly relates to the claim",
  "needs_more_evidence": <boolean>,
  "missing_information": "description of what additional information would help (if needs_more_evidence is true)"
}}"""

FINAL_VERDICT_TEMPLATE = """As a fact-checking expert, provide a final verdict on the following claim.

CLAIM: {claim}

CONTEXT: {context}

EVIDENCE ANALYSIS: {evidence_analysis}

Based on your analysis, provide a final fact-check verdict in this JSON format:
{{
  "verdict": "TRUE" | "FALSE" | "PARTLY_TRUE" | "UNVERIFIABLE" | "MISLEADING" | "OUTDATED",
  "confidence": <float between 0.0 and 1.0>,
  "explanation": "clear explanation of why this verdict was reached",
  "sources": ["source1", "source2"]
}}

Your explanation should be clear, concise, and directly tied to the evidence. Cite specific sources."""


# Define the state for the LangGraph workflow
class FactCheckState(TypedDict):
    """State for the fact-checking workflow."""
    
    claim: str
    context: str
    queries: List[str]
    evidence: List[Dict[str, Any]]
    evidence_analysis: Dict[str, Any]
    final_verdict: Dict[str, Any]
    iteration_count: int
    max_iterations: int


class LangGraphFactCheckingService(FactCheckingService):
    """Implementation of FactCheckingService using LangChain and LangGraph."""

    def __init__(
        self, 
        llm: BaseChatModel,
        knowledge_repository: KnowledgeRepository,
        max_iterations: int = 3
    ):
        """Initialize the fact checking service.
        
        Args:
            llm: Language model to use for fact checking
            knowledge_repository: Repository to search for evidence
            max_iterations: Maximum number of iterations for the retrieval-verification loop
        """
        self.llm = llm
        self.knowledge_repository = knowledge_repository
        self.max_iterations = max_iterations
        self.result_handlers = []
        
        # Initialize the output parser
        self.parser = JsonOutputParser()
        
        # Build the workflow components
        self._build_workflow_components()
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        
        logger.info("Initialized LangGraphFactCheckingService")
    
    def _build_workflow_components(self):
        """Build the components for the fact-checking workflow."""
        # Create query construction chain
        self.query_construction_prompt = ChatPromptTemplate.from_template(QUERY_CONSTRUCTION_TEMPLATE)
        self.query_construction_chain = (
            self.query_construction_prompt 
            | self.llm 
            | self.parser
        )
        
        # Create evidence analysis chain
        self.evidence_analysis_prompt = ChatPromptTemplate.from_template(EVIDENCE_ANALYSIS_TEMPLATE)
        self.evidence_analysis_chain = (
            self.evidence_analysis_prompt 
            | self.llm 
            | self.parser
        )
        
        # Create final verdict chain
        self.final_verdict_prompt = ChatPromptTemplate.from_template(FINAL_VERDICT_TEMPLATE)
        self.final_verdict_chain = (
            self.final_verdict_prompt 
            | self.llm 
            | self.parser
        )
    
    def _build_workflow(self) -> lg.StateGraph:
        """Build and return the LangGraph workflow for fact checking."""
        # Define the workflow
        workflow = lg.StateGraph(FactCheckState)
        
        # Add nodes to the workflow
        workflow.add_node("construct_queries", self._construct_queries)
        workflow.add_node("retrieve_evidence", self._retrieve_evidence)
        workflow.add_node("analyze_evidence", self._analyze_evidence)
        workflow.add_node("generate_verdict", self._generate_verdict)
        
        # Define the edges
        workflow.add_edge("construct_queries", "retrieve_evidence")
        workflow.add_edge("retrieve_evidence", "analyze_evidence")
        workflow.add_edge("analyze_evidence", "generate_verdict")
        
        # Add conditional edge for retrieving more evidence if needed
        workflow.add_conditional_edges(
            "analyze_evidence",
            self._should_retrieve_more_evidence,
            {
                True: "retrieve_evidence",
                False: "generate_verdict"
            }
        )
        
        # Set the entry point
        workflow.set_entry_point("construct_queries")
        
        # Compile the workflow
        return workflow.compile()
    
    async def check_claim(self, claim: Claim) -> FactCheckResult:
        """Check the factual accuracy of a claim.

        Args:
            claim: The claim to verify

        Returns:
            Result of the fact check
        """
        logger.info(f"Fact-checking claim: {claim.text}")
        
        try:
            # Initialize the state
            initial_state = {
                "claim": claim.text,
                "context": claim.context or "",
                "queries": [],
                "evidence": [],
                "evidence_analysis": {},
                "final_verdict": {},
                "iteration_count": 0,
                "max_iterations": self.max_iterations
            }
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Convert to FactCheckResult
            fact_check_result = self._create_fact_check_result(claim, result)
            
            # Notify result handlers
            self._notify_result_handlers(fact_check_result)
            
            return fact_check_result
            
        except Exception as e:
            logger.error(f"Error checking claim: {e}")
            # Return a default result in case of error
            return FactCheckResult(
                claim=claim,
                verdict=FactCheckVerdict.UNVERIFIABLE,
                is_true=False,
                confidence=0.0,
                explanation=f"Error during fact checking: {str(e)}",
                sources=[],
                metadata={"error": str(e)}
            )
    
    def register_result_handler(self, handler: Callable[[FactCheckResult], None]) -> None:
        """Register a function to be called for each fact check result.

        Args:
            handler: Function that takes a FactCheckResult object as an argument
        """
        self.result_handlers.append(handler)
    
    def _notify_result_handlers(self, result: FactCheckResult) -> None:
        """Notify all registered result handlers."""
        for handler in self.result_handlers:
            try:
                handler(result)
            except Exception as e:
                logger.error(f"Error in result handler: {e}")
    
    async def _construct_queries(self, state: FactCheckState) -> FactCheckState:
        """Construct search queries to verify the claim."""
        logger.info("Constructing search queries for fact checking")
        
        response = await self.query_construction_chain.ainvoke({
            "claim": state["claim"],
            "context": state["context"]
        })
        
        # Extract queries from response
        queries = response.get("queries", [])
        if not queries:
            # Fallback if no queries were generated
            queries = [state["claim"]]
        
        # Update state
        state["queries"] = queries
        logger.info(f"Generated {len(queries)} search queries")
        
        return state
    
    async def _retrieve_evidence(self, state: FactCheckState) -> FactCheckState:
        """Retrieve evidence from the knowledge repository."""
        logger.info("Retrieving evidence from knowledge repository")
        
        # Increment iteration count
        state["iteration_count"] += 1
        
        # Select query based on iteration count
        query_index = min(state["iteration_count"] - 1, len(state["queries"]) - 1)
        current_query = state["queries"][query_index]
        
        # Search for evidence
        search_results = await self.knowledge_repository.search(
            query=current_query,
            limit=5
        )
        
        # Add to evidence
        state["evidence"].extend(search_results)
        logger.info(f"Retrieved {len(search_results)} evidence items")
        
        return state
    
    async def _analyze_evidence(self, state: FactCheckState) -> FactCheckState:
        """Analyze the evidence to determine if it supports or contradicts the claim."""
        logger.info("Analyzing evidence")
        
        # Format the evidence for the prompt
        evidence_text = ""
        for i, item in enumerate(state["evidence"]):
            evidence_text += f"[{i+1}] {item.get('content', '')}\n"
            evidence_text += f"Source: {item.get('metadata', {}).get('source', 'Unknown')}\n\n"
        
        # If no evidence found, add a note
        if not evidence_text:
            evidence_text = "No evidence found."
        
        # Analyze the evidence
        response = await self.evidence_analysis_chain.ainvoke({
            "claim": state["claim"],
            "context": state["context"],
            "evidence": evidence_text
        })
        
        # Update state
        state["evidence_analysis"] = response
        logger.info(f"Evidence analysis complete: {response.get('verdict', 'UNKNOWN')}")
        
        return state
    
    def _should_retrieve_more_evidence(self, state: FactCheckState) -> bool:
        """Determine if more evidence should be retrieved."""
        # Don't continue if we've reached the max iterations
        if state["iteration_count"] >= state["max_iterations"]:
            return False
        
        # Check if the analysis indicates we need more evidence
        needs_more = state["evidence_analysis"].get("needs_more_evidence", False)
        
        # Continue if we need more evidence
        return needs_more
    
    async def _generate_verdict(self, state: FactCheckState) -> FactCheckState:
        """Generate the final verdict based on the evidence analysis."""
        logger.info("Generating final verdict")
        
        # Format the evidence analysis
        evidence_analysis = str(state["evidence_analysis"])
        
        # Generate the verdict
        response = await self.final_verdict_chain.ainvoke({
            "claim": state["claim"],
            "context": state["context"],
            "evidence_analysis": evidence_analysis
        })
        
        # Update state
        state["final_verdict"] = response
        logger.info(f"Final verdict: {response.get('verdict', 'UNKNOWN')}")
        
        return state
    
    def _create_fact_check_result(self, claim: Claim, result: FactCheckState) -> FactCheckResult:
        """Create a FactCheckResult from the workflow result."""
        # Extract the verdict from the result
        verdict_str = result.get("final_verdict", {}).get("verdict", "UNVERIFIABLE")
        
        # Map the verdict string to FactCheckVerdict enum
        verdict_map = {
            "TRUE": FactCheckVerdict.TRUE,
            "FALSE": FactCheckVerdict.FALSE,
            "PARTLY_TRUE": FactCheckVerdict.PARTLY_TRUE,
            "UNVERIFIABLE": FactCheckVerdict.UNVERIFIABLE,
            "MISLEADING": FactCheckVerdict.MISLEADING,
            "OUTDATED": FactCheckVerdict.OUTDATED
        }
        verdict = verdict_map.get(verdict_str, FactCheckVerdict.UNVERIFIABLE)
        
        # Extract other fields
        confidence = float(result.get("final_verdict", {}).get("confidence", 0.0))
        explanation = result.get("final_verdict", {}).get("explanation", "")
        sources = result.get("final_verdict", {}).get("sources", [])
        
        # Create the result
        return FactCheckResult(
            claim=claim,
            verdict=verdict,
            is_true=(verdict == FactCheckVerdict.TRUE),
            confidence=confidence,
            explanation=explanation,
            sources=sources,
            metadata={
                "evidence": result.get("evidence", []),
                "evidence_analysis": result.get("evidence_analysis", {}),
                "queries": result.get("queries", []),
                "iteration_count": result.get("iteration_count", 0)
            }
        ) 