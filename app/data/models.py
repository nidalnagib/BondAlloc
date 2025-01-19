from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum

class CreditRating(Enum):
    """Bond credit rating"""
    AAA = 1
    AA_PLUS = 2
    AA = 3
    AA_MINUS = 4
    A_PLUS = 5
    A = 6
    A_MINUS = 7
    BBB_PLUS = 8
    BBB = 9
    BBB_MINUS = 10
    BB_PLUS = 11
    BB = 12
    BB_MINUS = 13
    B_PLUS = 14
    B = 15
    B_MINUS = 16
    CCC_PLUS = 17
    CCC = 18
    CCC_MINUS = 19
    CC = 20
    C = 21
    D = 22
    
    @classmethod
    def from_string(cls, rating: str) -> 'CreditRating':
        """Convert string rating to enum value"""
        # Remove any whitespace
        rating = rating.strip().upper()
        
        # Handle modifiers
        rating = rating.replace('+', '_PLUS').replace('-', '_MINUS')
        
        try:
            return cls[rating]
        except KeyError:
            raise ValueError(f"Invalid credit rating: {rating}")
            
    def display(self) -> str:
        """Return rating in standard format (e.g., 'AA+', 'BBB-')"""
        name = self.name
        return name.replace('_PLUS', '+').replace('_MINUS', '-')
        
    @classmethod
    def from_score(cls, score: float) -> 'CreditRating':
        """Convert numerical score to nearest rating"""
        score = round(score)  # Round to nearest integer
        try:
            return next(r for r in cls if r.value == score)
        except StopIteration:
            # Return the worst rating if score is too high
            return cls.D if score > cls.D.value else cls.AAA

class Bond(BaseModel):
    isin: str
    clean_price: float
    ytm: float
    modified_duration: float
    maturity_date: datetime
    coupon_rate: float
    coupon_frequency: int
    credit_rating: CreditRating
    min_piece: int
    increment_size: int
    currency: str
    day_count_convention: str
    issuer: str

class PortfolioConstraints(BaseModel):
    total_size: float = Field(..., description="Total portfolio size in base currency")
    min_securities: int = Field(..., description="Minimum number of securities")
    max_securities: int = Field(..., description="Maximum number of securities")
    min_position_size: float = Field(..., description="Minimum position size")
    max_position_size: float = Field(..., description="Maximum position size")
    target_duration: float = Field(..., description="Target portfolio duration")
    duration_tolerance: float = Field(0.5, description="Acceptable deviation from target duration")
    min_rating: CreditRating = Field(..., description="Minimum portfolio rating")
    rating_tolerance: int = Field(1, description="Number of notches tolerance for rating")
    min_yield: float = Field(..., description="Minimum portfolio yield")
    max_issuer_exposure: float = Field(0.1, description="Maximum exposure to single issuer")
    rating_constraints: Dict[CreditRating, Tuple[float, float]] = Field(
        default_factory=dict, description="Min/Max allocation per rating"
    )
    maturity_bucket_constraints: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict, description="Min/Max allocation per maturity bucket"
    )
    min_coupon_income: float = Field(0.0, description="Minimum annual coupon income")

class OptimizationResult(BaseModel):
    success: bool = Field(..., description="Whether the optimization succeeded")
    status: str = Field(..., description="Solver status")
    portfolio: Dict[str, float]
    metrics: Dict[str, float]
    constraints_satisfied: bool
    constraint_violations: List[str]
    optimization_status: str
    solve_time: float
