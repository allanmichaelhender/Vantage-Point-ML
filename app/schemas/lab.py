from typing import List
from pydantic import BaseModel

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

class ModelProfile(BaseModel):
    summary: PerformanceSummary
    equity_curve: List[WeeklyPoint]
    monthly_breakdown: List[MonthlyStat]

class ModelPerformanceResponse(BaseModel):
    xgboost_nn: ModelProfile  
    xgboost: ModelProfile 
    nn: ModelProfile
    logistic: ModelProfile

class EdgeBucket(BaseModel):
    bucket: str
    roi: float
    match_count: int

class EdgeBucketResponse(BaseModel):
    xgboost_nn: List[EdgeBucket]
    xgboost: List[EdgeBucket]
    nn: List[EdgeBucket]
    logistic: List[EdgeBucket]

class CalibrationPoint(BaseModel):
    prob_bucket: str
    avg_predicted: float
    actual_win_rate: float
    match_count: int

class CalibrationPointResponse(BaseModel):
    xgboost_nn: List[CalibrationPoint]
    xgboost: List[CalibrationPoint]
    nn: List[CalibrationPoint]
    logistic: List[CalibrationPoint]


