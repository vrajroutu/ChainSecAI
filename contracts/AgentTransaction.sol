// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AgentReputation {
    struct Reputation {
        uint256 totalTasks;
        uint256 successfulTasks;
        uint256 validationAccuracy;
        uint256 averageResponseTime;
        uint256 peerReviewsCount;
        uint256 peerReviewScore;
    }

    mapping(address => Reputation) public reputations;
    mapping(address => bool) public validators;

    event ReputationUpdated(address indexed agent, uint256 newScore);

    modifier onlyValidator() {
        require(validators[msg.sender], "Not authorized validator");
        _;
    }

    function updateReputation(
        address agent,
        bool taskSuccess,
        uint256 responseTime,
        uint256 validationScore,
        uint256 peerRating
    ) external onlyValidator {
        Reputation storage rep = reputations[agent];
        
        rep.totalTasks += 1;
        if(taskSuccess) rep.successfulTasks += 1;
        rep.validationAccuracy = (rep.validationAccuracy + validationScore) / 2;
        rep.averageResponseTime = (rep.averageResponseTime + responseTime) / 2;
        
        if(peerRating > 0) {
            rep.peerReviewsCount += 1;
            rep.peerReviewScore = (rep.peerReviewScore * (rep.peerReviewsCount - 1) + peerRating) / rep.peerReviewsCount;
        }

        emit ReputationUpdated(agent, calculateReputationScore(agent));
    }

    function calculateReputationScore(address agent) public view returns (uint256) {
        Reputation memory rep = reputations[agent];
        return (
            (rep.successfulTasks * 40 * 1e18) / (rep.totalTasks > 0 ? rep.totalTasks : 1) +
            (rep.validationAccuracy * 30) / 100 +
            ((1e18 - rep.averageResponseTime) * 20) / 1e18 +
            (rep.peerReviewScore * 10) / 5
        ) / 1e16; // Returns score 0-100
    }

    function addValidator(address validator) external {
        validators[validator] = true;
    }
}