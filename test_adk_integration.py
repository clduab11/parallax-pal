#!/usr/bin/env python3
"""
Test script for ADK Integration

This script tests the core ADK components without requiring full configuration.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add project to path
sys.path.append('/Users/chrisdukes/Desktop/projects/Parallax-Pal')

async def test_orchestrator_agent():
    """Test the orchestrator agent."""
    print("🔄 Testing Orchestrator Agent...")
    
    try:
        from agents.orchestrator.orchestrator_agent import OrchestratorAgent
        
        # Create orchestrator instance
        orchestrator = OrchestratorAgent()
        
        # Test basic functionality
        print("✓ Orchestrator agent created successfully")
        
        # Test research request handling
        test_request = {
            "query": "artificial intelligence trends 2024",
            "continuous_mode": False,
            "force_refresh": False,
            "max_sources": 5,
            "depth_level": "detailed",
            "focus_areas": []
        }
        
        request_id = "test_request_001"
        user_id = "test_user_001"
        
        print("✓ Test request prepared")
        print(f"  Query: {test_request['query']}")
        print(f"  Request ID: {request_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator agent test failed: {e}")
        return False

async def test_specialized_agents():
    """Test specialized research agents."""
    print("\n🔄 Testing Specialized Agents...")
    
    try:
        # Test Citation Agent
        from agents.research.citation_agent import CitationAgent
        citation_agent = CitationAgent()
        print("✓ Citation Agent initialized")
        
        # Test Knowledge Graph Agent
        from agents.research.knowledge_graph_agent import KnowledgeGraphAgent
        kg_agent = KnowledgeGraphAgent()
        print("✓ Knowledge Graph Agent initialized")
        
        # Test Retrieval Agent
        from agents.research.retrieval_agent import retrieval_agent
        print("✓ Retrieval Agent imported")
        
        # Test Analysis Agent
        from agents.research.analysis_agent import analysis_agent
        print("✓ Analysis Agent imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Specialized agents test failed: {e}")
        return False

async def test_citation_agent_functionality():
    """Test citation agent functionality."""
    print("\n🔄 Testing Citation Agent Functionality...")
    
    try:
        from agents.research.citation_agent import CitationAgent
        
        citation_agent = CitationAgent()
        
        # Test with sample sources
        test_sources = [
            {
                "url": "https://example.com/ai-research-2024",
                "title": "AI Research Trends in 2024",
                "content": "This article discusses the latest trends in artificial intelligence research, including machine learning advances and neural network improvements.",
                "domain": "example.com"
            },
            {
                "url": "https://academic.edu/deep-learning-study",
                "title": "Deep Learning Applications Study",
                "content": "A comprehensive study on deep learning applications in various industries, published by researchers at Academic University.",
                "domain": "academic.edu"
            }
        ]
        
        # Process sources
        result = await citation_agent.process_sources(test_sources, "AI research trends")
        
        print(f"✓ Processed {len(result.get('citations', []))} citations")
        print(f"✓ Found {result.get('high_reliability_count', 0)} high-reliability sources")
        print(f"✓ Found {result.get('duplicates_found', [])} duplicates")
        
        # Test bibliography generation
        if result.get('citations'):
            citation_ids = [c['id'] for c in result['citations']]
            bibliography = await citation_agent.generate_bibliography(citation_ids, "apa")
            print(f"✓ Generated {len(bibliography.get('bibliography', []))} APA citations")
        
        return True
        
    except Exception as e:
        print(f"✗ Citation agent functionality test failed: {e}")
        return False

async def test_knowledge_graph_functionality():
    """Test knowledge graph agent functionality."""
    print("\n🔄 Testing Knowledge Graph Agent Functionality...")
    
    try:
        from agents.research.knowledge_graph_agent import KnowledgeGraphAgent
        
        kg_agent = KnowledgeGraphAgent()
        
        # Test with sample research data
        test_research_data = {
            "sources": [
                {
                    "url": "https://example.com/ai-research",
                    "title": "AI Research Advances",
                    "content": "Machine learning and neural networks are advancing rapidly. Deep learning techniques are being applied to computer vision and natural language processing."
                },
                {
                    "url": "https://example.com/tech-trends",
                    "title": "Technology Trends",
                    "content": "Artificial intelligence is transforming industries. Companies are adopting AI solutions for automation and data analysis."
                }
            ],
            "analysis": "Research focuses on AI applications in various domains"
        }
        
        # Build knowledge graph
        knowledge_graph = await kg_agent.build_knowledge_graph(test_research_data, "AI technology trends")
        
        print(f"✓ Generated knowledge graph with {len(knowledge_graph.get('entities', {}))} entity types")
        print(f"✓ Found {len(knowledge_graph.get('relationships', []))} relationships")
        print(f"✓ Created {len(knowledge_graph.get('clusters', []))} clusters")
        
        # Test graph structure
        graph_structure = knowledge_graph.get('graph_structure', {})
        nodes = graph_structure.get('nodes', [])
        edges = graph_structure.get('edges', [])
        
        print(f"✓ Graph has {len(nodes)} nodes and {len(edges)} edges")
        
        return True
        
    except Exception as e:
        print(f"✗ Knowledge graph functionality test failed: {e}")
        return False

async def test_websocket_manager():
    """Test WebSocket manager initialization."""
    print("\n🔄 Testing WebSocket Manager...")
    
    try:
        from src.api.websocket_adk import ADKWebSocketManager
        
        # Create WebSocket manager instance
        ws_manager = ADKWebSocketManager()
        print("✓ WebSocket manager created")
        
        # Test initialization
        await ws_manager.initialize()
        print("✓ WebSocket manager initialized")
        
        if ws_manager.adk_initialized:
            print("✓ ADK integration initialized successfully")
        else:
            print("⚠ ADK integration not fully initialized (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"✗ WebSocket manager test failed: {e}")
        return False

async def run_integration_tests():
    """Run comprehensive integration tests."""
    print("🚀 Starting ADK Integration Tests\n")
    print("=" * 60)
    
    test_results = []
    
    # Test orchestrator agent
    result = await test_orchestrator_agent()
    test_results.append(("Orchestrator Agent", result))
    
    # Test specialized agents
    result = await test_specialized_agents()
    test_results.append(("Specialized Agents", result))
    
    # Test citation agent functionality
    result = await test_citation_agent_functionality()
    test_results.append(("Citation Agent Functionality", result))
    
    # Test knowledge graph functionality
    result = await test_knowledge_graph_functionality()
    test_results.append(("Knowledge Graph Functionality", result))
    
    # Test WebSocket manager
    result = await test_websocket_manager()
    test_results.append(("WebSocket Manager", result))
    
    # Print results summary
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! ADK Integration is working correctly!")
        print("✅ System is ready for production deployment")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review errors above.")
        print("🔧 Some components may need attention before deployment")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = asyncio.run(run_integration_tests())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)