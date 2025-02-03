def test_reputation_flow():
    blockchain = Blockchain()
    agent = TaskAgent(blockchain, ...)
    validator = ValidatorAgent(blockchain, ...)
    
    # Initial reputation check
    assert agent.reputation['score'] == 0
    
    # Execute successful task
    agent.execute("Simple data processing")
    rep = blockchain.get_agent_reputation(agent.public_key)
    assert rep['score'] > 50
    
    # Test validation with low reputation
    agent.reputation['score'] = 45  # Force low score
    validation_report = validator.validate_transaction(...)
    assert "Low reputation" in validation_report['warnings']
    
    # Test reputation recovery
    for _ in range(5):
        agent.execute("Valid task")
    assert blockchain.get_agent_reputation(agent.public_key)['score'] > 75