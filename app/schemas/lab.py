from pydantic import BaseModel
from typing import List

class PerformanceSummary(BaseModel):
    roi: float          
    total_profit: float   
    win_rate: float      
    brier_score: float    
    total_bets: int       

class WeeklyPoint(BaseModel):
    date: str             
    balance: float        

class MonthlyStat(BaseModel):
    month: str            
    roi: float            
    profit: float         

class ModelPerformanceResponse(BaseModel):
    summary: PerformanceSummary
    equity_curve: List[WeeklyPoint]
    monthly_breakdown: List[MonthlyStat]

class EdgeBucket(BaseModel):
    bucket: str
    roi: float
    match_count: int

class CalibrationPoint(BaseModel):
    prob_bucket: str
    avg_predicted: float
    actual_win_rate: float
    match_count: int

