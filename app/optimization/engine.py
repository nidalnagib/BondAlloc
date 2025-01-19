import cvxpy as cp
import numpy as np
from typing import List, Dict, Optional
import logging
from ..data.models import Bond, PortfolioConstraints, CreditRating, OptimizationResult
from .solver_manager import SolverManager

# Get logger
logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    def __init__(self, universe: List[Bond], constraints: PortfolioConstraints):
        self.universe = universe
        self.constraints = constraints
        self.solver_manager = SolverManager()
        logger.info(f"Initializing optimizer with {len(universe)} bonds")
        
    def _setup_variables(self):
        """Setup optimization variables"""
        logger.info("Setting up optimization variables")
        self.weights = cp.Variable(len(self.universe))
        
    def _setup_objective(self):
        """Setup optimization objective"""
        logger.info("Setting up optimization objective")
        
        # Simple yield maximization
        yields = np.array([bond.ytm for bond in self.universe])
        objective = cp.Maximize(yields @ self.weights)
        logger.info(f"Objective created with {len(self.universe)} components")
        
        return objective, []

    def _setup_constraints(self):
        """Setup optimization constraints"""
        constraints = []
        
        # Budget constraint - weights must sum to 1
        constraints.append(cp.sum(self.weights) == 1)
        
        # Non-negativity constraint
        constraints.append(self.weights >= 0)
        
        # Duration constraint with small tolerance for numerical precision
        duration_vector = np.array([bond.modified_duration for bond in self.universe])
        portfolio_duration = duration_vector @ self.weights
        epsilon = 1e-4  # Small tolerance for numerical precision
        constraints.append(portfolio_duration >= self.constraints.target_duration - self.constraints.duration_tolerance - epsilon)
        constraints.append(portfolio_duration <= self.constraints.target_duration + self.constraints.duration_tolerance + epsilon)
        
        # Rating constraint
        rating_scores = np.array([self._get_rating_score(bond.credit_rating) for bond in self.universe])
        portfolio_rating = rating_scores @ self.weights
        min_rating_score = self._get_rating_score(self.constraints.min_rating)
        constraints.append(portfolio_rating >= min_rating_score)
        
        # Yield constraint
        yield_vector = np.array([bond.ytm for bond in self.universe])
        portfolio_yield = yield_vector @ self.weights
        constraints.append(portfolio_yield >= self.constraints.min_yield)
        
        # Maximum number of securities constraint
        binary_vars = cp.Variable(len(self.universe), boolean=True)
        M = 1  # Big M value (1 is sufficient since weights are between 0 and 1)
        
        # Link binary variables to weights and enforce position size constraints
        for i in range(len(self.universe)):
            # Weight must be 0 if binary is 0
            constraints.append(self.weights[i] <= M * binary_vars[i])
            # If binary is 1, weight must be at least min_position_size
            constraints.append(self.weights[i] >= self.constraints.min_position_size * binary_vars[i])
            # Weight cannot exceed max_position_size
            constraints.append(self.weights[i] <= self.constraints.max_position_size)
        
        # Constraint on number of securities
        constraints.append(cp.sum(binary_vars) <= self.constraints.max_securities)
        
        # Issuer exposure constraints
        unique_issuers = set(bond.issuer for bond in self.universe)
        for issuer in unique_issuers:
            issuer_indices = [i for i, bond in enumerate(self.universe) if bond.issuer == issuer]
            issuer_exposure = cp.sum(self.weights[issuer_indices])
            constraints.append(issuer_exposure <= self.constraints.max_issuer_exposure)
        
        return constraints

    def optimize(self) -> OptimizationResult:
        """Run the optimization"""
        logger.info("Starting optimization")
        
        try:
            # Setup optimization variables
            logger.info("Setting up optimization variables")
            self.weights = cp.Variable(len(self.universe))
            
            # Setup objective and constraints
            objective, additional_constraints = self._setup_objective()
            constraints = self._setup_constraints()
            constraints.extend(additional_constraints)
            
            # Create and solve problem
            problem = cp.Problem(objective, constraints)
            status, solve_time = self.solver_manager.solve(problem)
            
            if status in ['optimal', 'optimal_inaccurate']:
                # Extract results
                portfolio = {}
                for i, bond in enumerate(self.universe):
                    if self.weights.value[i] > 1e-5:  # Filter out very small positions
                        portfolio[bond.isin] = float(self.weights.value[i])
                
                # Calculate portfolio metrics
                metrics = self._calculate_portfolio_metrics(portfolio)
                
                # Check for constraint violations
                violations = self._check_constraint_violations(portfolio)
                
                return OptimizationResult(
                    success=True,
                    status=status,
                    solve_time=solve_time,
                    portfolio=portfolio,
                    metrics=metrics,
                    constraints_satisfied=len(violations) == 0,
                    constraint_violations=violations,
                    optimization_status=status
                )
            else:
                # Failed optimization
                empty_metrics = {
                    'yield': 0.0,
                    'duration': 0.0,
                    'rating': 0.0,
                    'number_of_securities': 0
                }
                return OptimizationResult(
                    success=False,
                    status=status,
                    solve_time=solve_time,
                    portfolio={},
                    metrics=empty_metrics,
                    constraints_satisfied=False,
                    constraint_violations=["Optimization failed to find a solution"],
                    optimization_status=status
                )
                
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            empty_metrics = {
                'yield': 0.0,
                'duration': 0.0,
                'rating': 0.0,
                'number_of_securities': 0
            }
            return OptimizationResult(
                success=False,
                status="error",
                solve_time=0.0,
                portfolio={},
                metrics=empty_metrics,
                constraints_satisfied=False,
                constraint_violations=[f"Error during optimization: {str(e)}"],
                optimization_status="error"
            )

    def _calculate_portfolio_metrics(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Calculate portfolio metrics"""
        metrics = {}
        
        # Portfolio yield
        yields = np.array([bond.ytm for bond in self.universe])
        weights = np.array([portfolio.get(bond.isin, 0) for bond in self.universe])
        metrics['yield'] = float(yields @ weights)
        
        # Portfolio duration
        durations = np.array([bond.modified_duration for bond in self.universe])
        metrics['duration'] = float(durations @ weights)
        
        # Portfolio rating
        rating_scale = {
            CreditRating.AAA: 1, CreditRating.AA_PLUS: 2, CreditRating.AA: 3,
            CreditRating.AA_MINUS: 4, CreditRating.A_PLUS: 5, CreditRating.A: 6,
            CreditRating.A_MINUS: 7, CreditRating.BBB_PLUS: 8, CreditRating.BBB: 9,
            CreditRating.BBB_MINUS: 10
        }
        ratings = np.array([rating_scale[bond.credit_rating] for bond in self.universe])
        metrics['rating'] = float(ratings @ weights)
        
        # Number of securities
        metrics['number_of_securities'] = sum(1 for w in weights if w > 1e-5)
        
        return metrics
        
    def _calculate_portfolio_rating(self, portfolio: Dict[str, float]) -> float:
        """Calculate weighted average portfolio rating"""
        weights = np.array([portfolio.get(bond.isin, 0) for bond in self.universe])
        rating_scale = {
            CreditRating.AAA: 1, CreditRating.AA_PLUS: 2, CreditRating.AA: 3,
            CreditRating.AA_MINUS: 4, CreditRating.A_PLUS: 5, CreditRating.A: 6,
            CreditRating.A_MINUS: 7, CreditRating.BBB_PLUS: 8, CreditRating.BBB: 9,
            CreditRating.BBB_MINUS: 10
        }
        rating_values = np.array([rating_scale[bond.credit_rating] for bond in self.universe])
        return float(rating_values @ weights)
        
    def _check_constraint_violations(self, portfolio: Dict[str, float]) -> List[str]:
        """Check if portfolio satisfies all constraints"""
        violations = []
        epsilon = 1e-4  # Small tolerance for numerical precision
        
        # Number of securities constraint
        num_securities = sum(1 for weight in portfolio.values() if weight > epsilon)
        if num_securities > self.constraints.max_securities:
            violations.append(f"Maximum number of securities constraint violated: {num_securities} > {self.constraints.max_securities}")
        
        # Position size constraints
        for i, bond in enumerate(self.universe):
            weight = portfolio.get(bond.isin, 0)
            if weight > epsilon:  # Only check non-zero positions
                if weight < self.constraints.min_position_size - epsilon:
                    violations.append(f"Minimum position size constraint violated for bond {bond.isin}: {weight:.4f} < {self.constraints.min_position_size:.4f}")
                elif weight > self.constraints.max_position_size + epsilon:
                    violations.append(f"Maximum position size constraint violated for bond {bond.isin}: {weight:.4f} > {self.constraints.max_position_size:.4f}")
        
        # Duration constraints
        duration_vector = np.array([bond.modified_duration for bond in self.universe])
        portfolio_duration = duration_vector @ np.array([portfolio.get(bond.isin, 0) for bond in self.universe])
        if portfolio_duration < self.constraints.target_duration - self.constraints.duration_tolerance - epsilon:
            violations.append(f"Minimum duration constraint violated: {portfolio_duration:.4f} < {self.constraints.target_duration - self.constraints.duration_tolerance:.4f}")
        elif portfolio_duration > self.constraints.target_duration + self.constraints.duration_tolerance + epsilon:
            violations.append(f"Maximum duration constraint violated: {portfolio_duration:.4f} > {self.constraints.target_duration + self.constraints.duration_tolerance:.4f}")
        
        # Rating constraint
        portfolio_rating = self._calculate_portfolio_rating(portfolio)
        min_rating_score = self._get_rating_score(self.constraints.min_rating)
        if portfolio_rating > min_rating_score + epsilon:  # Lower score means better rating
            violations.append(f"Minimum rating constraint violated: {portfolio_rating:.4f} > {min_rating_score:.4f}")
        
        # Yield constraint
        ytm_vector = np.array([bond.ytm for bond in self.universe])
        portfolio_yield = ytm_vector @ np.array([portfolio.get(bond.isin, 0) for bond in self.universe])
        if portfolio_yield < self.constraints.min_yield - epsilon:
            violations.append(f"Minimum yield constraint violated: {portfolio_yield:.4f} < {self.constraints.min_yield:.4f}")
        
        return violations

    def _get_rating_score(self, rating: CreditRating) -> int:
        """Get rating score"""
        rating_scale = {
            CreditRating.AAA: 1, CreditRating.AA_PLUS: 2, CreditRating.AA: 3,
            CreditRating.AA_MINUS: 4, CreditRating.A_PLUS: 5, CreditRating.A: 6,
            CreditRating.A_MINUS: 7, CreditRating.BBB_PLUS: 8, CreditRating.BBB: 9,
            CreditRating.BBB_MINUS: 10
        }
        return rating_scale[rating]
