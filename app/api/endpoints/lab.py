from fastapi import APIRouter,  Security
from app.api.deps import get_api_key
from app.services.quant.lab_service import LabService
from app.schemas.lab import ModelPerformanceResponse, EdgeBucketResponse, CalibrationPointResponse
from typing import List
import asyncio

# We use security here, it does the same as depends but is specifically for this application
router = APIRouter(
    dependencies=[Security(get_api_key)]
)

xgboost_nn_lab_service = LabService("app/ml/data/betting_results_XGBoost&NN.csv")
xgboost_lab_service = LabService("app/ml/data/betting_results_XGBoost.csv")

# Returns model performance
@router.get("/model-performance", response_model=ModelPerformanceResponse)
async def get_lab_stats():
    xgboost_nn_performance = xgboost_nn_lab_service.get_model_performance()
    xgboost_performance = xgboost_lab_service.get_model_performance()

    result_xgboost_nn, result_xbgoost = await asyncio.gather(xgboost_nn_performance, xgboost_performance)

    return {"xgboost_nn": result_xgboost_nn, "xgboost": result_xbgoost}



# Returns bucketed edge analysis on our model 
@router.get("/edge-analysis", response_model=List[EdgeBucketResponse])
async def get_edge_analysis():
    xgboost_nn_performance = xgboost_nn_lab_service.get_model_performance()
    xgboost_performance = xgboost_lab_service.get_model_performance()

    result_xgboost_nn, result_xbgoost = await asyncio.gather(xgboost_nn_performance, xgboost_performance)

    return {"xgboost_nn": result_xgboost_nn, "xgboost": result_xbgoost}


# Returns calibration data for plotting in the frontend
@router.get("/calibration", response_model=List[CalibrationPointResponse])
async def get_calibration_stats():
    xgboost_nn_performance = xgboost_nn_lab_service.get_calibration()
    xgboost_performance = xgboost_lab_service.get_calibration()

    result_xgboost_nn, result_xbgoost = await asyncio.gather(xgboost_nn_performance, xgboost_performance)

    return {"xgboost_nn": result_xgboost_nn, "xgboost": result_xbgoost}
