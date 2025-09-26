#!/usr/bin/env python3
"""
PySR MCP Server - Advanced Symbolic Regression Server
Provides comprehensive PySR functionality through a single endpoint
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List, Union
import numpy as np
import pandas as pd
import pickle
import json
import os
import uuid
import asyncio
import sys
from datetime import datetime
import logging
from pathlib import Path
import tempfile
import io
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PySR components
try:
    from pysr import PySRRegressor
    import sympy
    PYSR_AVAILABLE = True
    logger.info("PySR successfully imported")
except ImportError as e:
    logger.warning(f"PySR not available: {e}. Please install with: pip install pysr")
    PYSR_AVAILABLE = False

# Global storage for models and jobs
model_store = {}
job_store = {}
training_status = {}

# Data Models
class ModelConfig(BaseModel):
    """Configuration for PySR model creation"""
    model_id: Optional[str] = None
    maxsize: int = 20
    niterations: int = 40
    populations: int = 8
    population_size: int = 33
    ncycles_per_iteration: int = 500
    binary_operators: List[str] = ["+", "-", "*", "/"]
    unary_operators: List[str] = ["cos", "sin", "exp", "log", "sqrt"]
    constraints: Optional[Dict[str, Union[int, tuple]]] = None
    nested_constraints: Optional[Dict[str, Dict[str, int]]] = None
    complexity_of_operators: Optional[Dict[str, int]] = None
    elementwise_loss: str = "loss(prediction, target) = (prediction - target)^2"
    maxdepth: int = 10
    parsimony: float = 0.0032
    dimensional_constraint_penalty: Optional[float] = None
    dimensionless_constants_only: bool = False
    use_frequency: bool = True
    use_frequency_in_tournament: bool = True
    adaptive_parsimony_scaling: float = 20.0
    alpha: float = 0.1
    annealing: bool = False
    early_stop_condition: Optional[str] = None
    timeout_in_seconds: Optional[float] = None
    turbo: bool = False
    precision: int = 32
    random_state: Optional[int] = None
    deterministic: bool = False
    warm_start: bool = False
    verbosity: int = 1
    update_verbosity: int = 1000
    progress: bool = True
    equation_file: Optional[str] = None
    temp_equation_file: bool = False
    tempdir: Optional[str] = None
    delete_tempfiles: bool = True
    julia_project: Optional[str] = None
    update: bool = False
    temp_julia_project: bool = False
    model_selection: str = "best"
    should_optimize_constants: bool = True
    weight_optimize: float = 0.001
    weight_mutate_constant: float = 0.048
    weight_mutate_operator: float = 0.47
    weight_add_node: float = 0.79
    weight_insert_node: float = 5.1
    weight_delete_node: float = 1.7
    weight_simplify: float = 0.0016
    weight_randomize: float = 0.00023
    weight_do_nothing: float = 0.21
    crossover_probability: float = 0.066
    skip_mutation_failures: bool = True
    migration: bool = True
    hof_migration: bool = True
    topn: int = 12
    optimizer_algorithm: str = "BFGS"
    optimizer_nrestarts: int = 2
    optimize_probability: float = 0.14
    optimizer_iterations: int = 8
    perturbation_factor: float = 0.076
    batching: bool = False
    batch_size: int = 50
    fast_cycle: bool = False
    bumper: bool = False
    enable_autodiff: bool = False

class TrainingData(BaseModel):
    """Training data structure"""
    X: List[List[float]]
    y: List[float]
    feature_names: Optional[List[str]] = None
    variable_names: Optional[List[str]] = None
    weights: Optional[List[float]] = None

class PredictionRequest(BaseModel):
    """Prediction request structure"""
    model_id: str
    X: List[List[float]]
    equation_index: Optional[int] = None

class EquationExportRequest(BaseModel):
    """Equation export request"""
    model_id: str
    equation_index: Optional[int] = None
    format: str = "sympy"  # sympy, latex, jax, pytorch, callable

class JobRequest(BaseModel):
    """Generic job request structure"""
    action: str
    data: Dict[str, Any]

class JobResponse(BaseModel):
    """Generic job response structure"""
    job_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime

# Utility Functions
def generate_job_id() -> str:
    """Generate unique job ID"""
    return str(uuid.uuid4())

def validate_data_format(X, y):
    """Validate input data format"""
    try:
        X = np.array(X)
        y = np.array(y)
        
        if len(X.shape) != 2:
            raise ValueError("X must be 2D array")
        if len(y.shape) != 1:
            raise ValueError("y must be 1D array")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have same number of samples")
        if X.shape[0] == 0:
            raise ValueError("No data provided")
        if np.any(np.isnan(X)) or np.any(np.isnan(y)):
            raise ValueError("Data contains NaN values")
        if np.any(np.isinf(X)) or np.any(np.isinf(y)):
            raise ValueError("Data contains infinite values")
            
        return X, y
    except Exception as e:
        raise ValueError(f"Data validation failed: {str(e)}")

async def train_model_async(model_id: str, model: PySRRegressor, X: np.ndarray, y: np.ndarray):
    """Asynchronously train PySR model"""
    try:
        training_status[model_id] = {
            "status": "training",
            "progress": 0,
            "message": "Training started",
            "start_time": datetime.now(),
            "current_iteration": 0
        }
        
        # Run training in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, model.fit, X, y)
        
        # Store trained model
        model_store[model_id] = model
        
        training_status[model_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Training completed successfully",
            "end_time": datetime.now(),
            "equations_found": len(model.equations_) if hasattr(model, 'equations_') else 0
        })
        
    except Exception as e:
        training_status[model_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Training failed: {str(e)}",
            "error": str(e),
            "end_time": datetime.now()
        })
        logger.error(f"Training failed for model {model_id}: {str(e)}")

# FastAPI App Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("PySR MCP Server starting up...")
    if not PYSR_AVAILABLE:
        logger.warning("PySR not available - server running in mock mode")
    
    # Create temp directories
    os.makedirs("temp_models", exist_ok=True)
    os.makedirs("temp_data", exist_ok=True)
    
    yield
    
    # Cleanup
    logger.info("PySR MCP Server shutting down...")

app = FastAPI(
    title="PySR MCP Server",
    description="Advanced Symbolic Regression Server with PySR",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single Main Endpoint
@app.post("/pysr")
async def pysr_endpoint(request: JobRequest) -> JobResponse:
    """
    Single endpoint for all PySR operations
    
    Supported actions:
    - create_model: Create PySR model with configuration
    - fit_model: Train model with data
    - predict: Make predictions
    - get_equations: Get discovered equations
    - save_model: Save model to file
    - load_model: Load model from file
    - export_equation: Export equation in different formats
    - set_operators: Configure operators
    - validate_data: Validate input data
    - monitor_training: Get training status
    - evaluate_model: Evaluate model performance
    """
    job_id = generate_job_id()
    timestamp = datetime.now()
    
    try:
        action = request.action
        data = request.data
        
        if not PYSR_AVAILABLE and action in ['create_model', 'fit_model', 'predict']:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="PySR not available - please install pysr package",
                timestamp=timestamp
            )
        
        # Route to appropriate handler
        if action == "create_model":
            return await handle_create_model(job_id, data, timestamp)
        elif action == "fit_model":
            return await handle_fit_model(job_id, data, timestamp)
        elif action == "predict":
            return await handle_predict(job_id, data, timestamp)
        elif action == "get_equations":
            return await handle_get_equations(job_id, data, timestamp)
        elif action == "save_model":
            return await handle_save_model(job_id, data, timestamp)
        elif action == "load_model":
            return await handle_load_model(job_id, data, timestamp)
        elif action == "export_equation":
            return await handle_export_equation(job_id, data, timestamp)
        elif action == "set_operators":
            return await handle_set_operators(job_id, data, timestamp)
        elif action == "validate_data":
            return await handle_validate_data(job_id, data, timestamp)
        elif action == "monitor_training":
            return await handle_monitor_training(job_id, data, timestamp)
        elif action == "evaluate_model":
            return await handle_evaluate_model(job_id, data, timestamp)
        else:
            return JobResponse(
                job_id=job_id,
                status="error",
                message=f"Unknown action: {action}",
                timestamp=timestamp
            )
            
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Internal server error: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

# Action Handlers
async def handle_create_model(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Create a new PySR model"""
    try:
        config = ModelConfig(**data)
        model_id = config.model_id or generate_job_id()
        
        # Create PySR model with configuration
        model_params = {
            "maxsize": config.maxsize,
            "niterations": config.niterations,
            "populations": config.populations,
            "population_size": config.population_size,
            "ncycles_per_iteration": config.ncycles_per_iteration,
            "binary_operators": config.binary_operators,
            "unary_operators": config.unary_operators,
            "maxdepth": config.maxdepth,
            "parsimony": config.parsimony,
            "elementwise_loss": config.elementwise_loss,
            "turbo": config.turbo,
            "precision": config.precision,
            "random_state": config.random_state,
            "warm_start": config.warm_start,
            "verbosity": config.verbosity,
            "progress": config.progress,
            "model_selection": config.model_selection,
        }
        
        # Add optional parameters if specified
        if config.constraints:
            model_params["constraints"] = config.constraints
        if config.nested_constraints:
            model_params["nested_constraints"] = config.nested_constraints
        if config.complexity_of_operators:
            model_params["complexity_of_operators"] = config.complexity_of_operators
        if config.early_stop_condition:
            model_params["early_stop_condition"] = config.early_stop_condition
        if config.timeout_in_seconds:
            model_params["timeout_in_seconds"] = config.timeout_in_seconds
            
        if PYSR_AVAILABLE:
            model = PySRRegressor(**model_params)
            model_store[model_id] = model
        else:
            # Mock model for testing when PySR not available
            model_store[model_id] = {"mock": True, "config": model_params}
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Model created successfully",
            result={
                "model_id": model_id,
                "configuration": model_params
            },
            timestamp=timestamp
        )
        
    except ValidationError as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Invalid configuration: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to create model: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_fit_model(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Fit/train a PySR model"""
    try:
        model_id = data.get("model_id")
        if not model_id or model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        training_data = TrainingData(**data.get("training_data", {}))
        X, y = validate_data_format(training_data.X, training_data.y)
        
        model = model_store[model_id]
        
        if not PYSR_AVAILABLE:
            # Mock training for testing
            training_status[model_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Mock training completed",
                "start_time": datetime.now(),
                "end_time": datetime.now()
            }
            return JobResponse(
                job_id=job_id,
                status="success",
                message="Mock training completed (PySR not available)",
                result={"model_id": model_id, "data_shape": X.shape},
                timestamp=timestamp
            )
        
        # Set feature names if provided
        if training_data.feature_names:
            model.feature_names_in_ = training_data.feature_names
        if training_data.variable_names:
            model.variable_names = training_data.variable_names
        
        # Start asynchronous training
        asyncio.create_task(train_model_async(model_id, model, X, y))
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Training started",
            result={
                "model_id": model_id,
                "data_shape": X.shape,
                "training_status": "started"
            },
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to start training: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_predict(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Make predictions with trained model"""
    try:
        pred_request = PredictionRequest(**data)
        
        if pred_request.model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[pred_request.model_id]
        
        if not PYSR_AVAILABLE:
            # Mock predictions
            X = np.array(pred_request.X)
            mock_predictions = np.random.random(len(X)).tolist()
            return JobResponse(
                job_id=job_id,
                status="success",
                message="Mock predictions generated",
                result={"predictions": mock_predictions, "input_shape": X.shape},
                timestamp=timestamp
            )
        
        if not hasattr(model, 'equations_') or model.equations_ is None:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not trained yet",
                timestamp=timestamp
            )
        
        X = np.array(pred_request.X)
        
        if pred_request.equation_index is not None:
            predictions = model.predict(X, pred_request.equation_index)
        else:
            predictions = model.predict(X)
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Predictions generated successfully",
            result={
                "predictions": predictions.tolist(),
                "equation_index": pred_request.equation_index,
                "input_shape": X.shape
            },
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Prediction failed: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_get_equations(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Get discovered equations from trained model"""
    try:
        model_id = data.get("model_id")
        
        if model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[model_id]
        
        if not PYSR_AVAILABLE:
            # Mock equations
            mock_equations = [
                {"equation": "x0 + x1", "loss": 0.001, "complexity": 3, "score": 0.95},
                {"equation": "x0 * x1", "loss": 0.002, "complexity": 3, "score": 0.93},
                {"equation": "sin(x0) + x1", "loss": 0.005, "complexity": 4, "score": 0.90}
            ]
            return JobResponse(
                job_id=job_id,
                status="success",
                message="Mock equations retrieved",
                result={
                    "equations": mock_equations,
                    "best_equation_index": 0,
                    "total_equations": len(mock_equations)
                },
                timestamp=timestamp
            )
        
        if not hasattr(model, 'equations_') or model.equations_ is None:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not trained yet",
                timestamp=timestamp
            )
        
        equations_df = model.equations_
        equations_data = equations_df.to_dict('records')
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Equations retrieved successfully",
            result={
                "equations": equations_data,
                "best_equation_index": int(equations_df[equations_df['pick'] > 0].index[0]) if len(equations_df[equations_df['pick'] > 0]) > 0 else 0,
                "total_equations": len(equations_data)
            },
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to get equations: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_save_model(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Save trained model to file"""
    try:
        model_id = data.get("model_id")
        filepath = data.get("filepath", f"temp_models/{model_id}.pkl")
        format_type = data.get("format", "pkl")
        
        if model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[model_id]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if format_type == "pkl":
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
        elif format_type == "json":
            # Save as JSON for non-PySR models
            with open(filepath.replace('.pkl', '.json'), 'w') as f:
                json.dump({"model_data": str(model)}, f, indent=2, default=str)
            filepath = filepath.replace('.pkl', '.json')
        
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Model saved successfully",
            result={
                "filepath": filepath,
                "format": format_type,
                "file_size": file_size
            },
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to save model: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_load_model(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Load model from file"""
    try:
        filepath = data.get("filepath")
        model_id = data.get("model_id") or generate_job_id()
        
        if not os.path.exists(filepath):
            return JobResponse(
                job_id=job_id,
                status="error",
                message="File not found",
                timestamp=timestamp
            )
        
        if filepath.endswith('.pkl'):
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
        elif filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                model = json.load(f)
        else:
            raise ValueError("Unsupported file format")
        
        model_store[model_id] = model
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Model loaded successfully",
            result={
                "model_id": model_id,
                "filepath": filepath,
                "has_equations": hasattr(model, 'equations_') and model.equations_ is not None if PYSR_AVAILABLE else False
            },
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to load model: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_export_equation(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Export equation in different formats"""
    try:
        export_request = EquationExportRequest(**data)
        
        if export_request.model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[export_request.model_id]
        
        if not PYSR_AVAILABLE:
            # Mock export
            mock_equation = "x0 + sin(x1)"
            return JobResponse(
                job_id=job_id,
                status="success",
                message="Mock equation exported",
                result={"equation": mock_equation},
                timestamp=timestamp
            )
        
        if not hasattr(model, 'equations_') or model.equations_ is None:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not trained yet",
                timestamp=timestamp
            )
        
        export_result = {}
        
        if export_request.format == "sympy":
            export_result["equation"] = str(model.sympy(export_request.equation_index))
        elif export_request.format == "latex":
            sympy_expr = model.sympy(export_request.equation_index)
            export_result["equation"] = sympy.latex(sympy_expr)
        elif export_request.format == "callable":
            export_result["equation"] = str(model.equations_.iloc[export_request.equation_index or 0]['lambda_format'])
        else:
            return JobResponse(
                job_id=job_id,
                status="error",
                message=f"Unsupported export format: {export_request.format}",
                timestamp=timestamp
            )
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Equation exported successfully",
            result=export_result,
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Export failed: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_set_operators(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Configure operators for existing model"""
    try:
        model_id = data.get("model_id")
        binary_operators = data.get("binary_operators")
        unary_operators = data.get("unary_operators")
        
        if model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[model_id]
        
        if PYSR_AVAILABLE and hasattr(model, 'binary_operators'):
            if binary_operators:
                model.binary_operators = binary_operators
            if unary_operators:
                model.unary_operators = unary_operators
            
            result = {
                "binary_operators": model.binary_operators,
                "unary_operators": model.unary_operators
            }
        else:
            # Mock response
            result = {
                "binary_operators": binary_operators or ["+", "-", "*", "/"],
                "unary_operators": unary_operators or ["sin", "cos", "exp"]
            }
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Operators updated successfully",
            result=result,
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to set operators: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_validate_data(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Validate input data"""
    try:
        X = data.get("X")
        y = data.get("y")
        
        if not X or not y:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Missing X or y data",
                timestamp=timestamp
            )
        
        X_validated, y_validated = validate_data_format(X, y)
        
        # Additional validation checks
        validation_results = {
            "data_shape": X_validated.shape,
            "target_shape": y_validated.shape,
            "has_nan": bool(np.any(np.isnan(X_validated)) or np.any(np.isnan(y_validated))),
            "has_inf": bool(np.any(np.isinf(X_validated)) or np.any(np.isinf(y_validated))),
            "feature_stats": {
                "min": np.min(X_validated, axis=0).tolist(),
                "max": np.max(X_validated, axis=0).tolist(),
                "mean": np.mean(X_validated, axis=0).tolist(),
                "std": np.std(X_validated, axis=0).tolist()
            },
            "target_stats": {
                "min": float(np.min(y_validated)),
                "max": float(np.max(y_validated)),
                "mean": float(np.mean(y_validated)),
                "std": float(np.std(y_validated))
            }
        }
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Data validation successful",
            result=validation_results,
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Data validation failed: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_monitor_training(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Monitor training status"""
    try:
        model_id = data.get("model_id")
        
        if model_id not in training_status:
            return JobResponse(
                job_id=job_id,
                status="success",
                message="No training status found",
                result={"status": "not_started"},
                timestamp=timestamp
            )
        
        status = training_status[model_id].copy()
        
        # Convert datetime objects to strings
        if "start_time" in status:
            status["start_time"] = status["start_time"].isoformat()
        if "end_time" in status:
            status["end_time"] = status["end_time"].isoformat()
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Training status retrieved",
            result=status,
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Failed to get training status: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

async def handle_evaluate_model(job_id: str, data: Dict[str, Any], timestamp: datetime) -> JobResponse:
    """Evaluate model performance"""
    try:
        model_id = data.get("model_id")
        X_test = np.array(data.get("X_test", []))
        y_test = np.array(data.get("y_test", []))
        
        if model_id not in model_store:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not found",
                timestamp=timestamp
            )
        
        model = model_store[model_id]
        
        if not PYSR_AVAILABLE:
            # Mock evaluation
            evaluation_results = {
                "mse": 0.001,
                "mae": 0.02,
                "r2_score": 0.95,
                "rmse": 0.032,
                "total_equations": 5,
                "best_equation": {
                    "equation": "x0 + sin(x1)",
                    "loss": 0.001,
                    "complexity": 4,
                    "score": 0.95
                }
            }
            return JobResponse(
                job_id=job_id,
                status="success",
                message="Mock model evaluation completed",
                result=evaluation_results,
                timestamp=timestamp
            )
        
        if not hasattr(model, 'equations_') or model.equations_ is None:
            return JobResponse(
                job_id=job_id,
                status="error",
                message="Model not trained yet",
                timestamp=timestamp
            )
        
        # Make predictions
        evaluation_results = {}
        
        if len(X_test) > 0 and len(y_test) > 0:
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = np.mean((y_test - y_pred) ** 2)
            mae = np.mean(np.abs(y_test - y_pred))
            r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
            
            evaluation_results.update({
                "mse": float(mse),
                "mae": float(mae),
                "r2_score": float(r2),
                "rmse": float(np.sqrt(mse)),
                "predictions": y_pred.tolist()
            })
        
        # Add model complexity metrics
        equations_df = model.equations_
        evaluation_results.update({
            "total_equations": len(equations_df),
            "best_equation": {
                "equation": str(equations_df.iloc[0]["equation"]),
                "loss": float(equations_df.iloc[0]["loss"]),
                "complexity": int(equations_df.iloc[0]["complexity"]),
                "score": float(equations_df.iloc[0]["score"])
            },
            "complexity_range": {
                "min": int(equations_df["complexity"].min()),
                "max": int(equations_df["complexity"].max()),
                "mean": float(equations_df["complexity"].mean())
            }
        })
        
        return JobResponse(
            job_id=job_id,
            status="success",
            message="Model evaluation completed",
            result=evaluation_results,
            timestamp=timestamp
        )
        
    except Exception as e:
        return JobResponse(
            job_id=job_id,
            status="error",
            message=f"Model evaluation failed: {str(e)}",
            error=str(e),
            timestamp=timestamp
        )

# Additional endpoints for health check and info
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pysr_available": PYSR_AVAILABLE,
        "active_models": len(model_store),
        "active_jobs": len(training_status),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/info")
async def server_info():
    """Server information endpoint"""
    return {
        "name": "PySR MCP Server",
        "version": "1.0.0",
        "pysr_available": PYSR_AVAILABLE,
        "supported_actions": [
            "create_model",
            "fit_model", 
            "predict",
            "get_equations",
            "save_model",
            "load_model",
            "export_equation",
            "set_operators",
            "validate_data",
            "monitor_training",
            "evaluate_model"
        ],
        "export_formats": ["sympy", "latex", "callable"]
    }

@app.get("/models")
async def list_models():
    """List all active models"""
    models_info = []
    for model_id, model in model_store.items():
        info = {
            "model_id": model_id,
            "has_equations": hasattr(model, 'equations_') and model.equations_ is not None if PYSR_AVAILABLE else False,
            "training_status": training_status.get(model_id, {}).get("status", "unknown")
        }
        if PYSR_AVAILABLE and hasattr(model, 'equations_') and model.equations_ is not None:
            info["equations_count"] = len(model.equations_)
        models_info.append(info)
    
    return {
        "models": models_info,
        "total_models": len(model_store)
    }

if __name__ == "__main__":
    print("🚀 Starting PySR MCP Server...")
    print("📊 Advanced Symbolic Regression Server")
    print("=" * 50)
    print(f"🔗 Single Endpoint: http://localhost:8001/pysr")
    print(f"💡 Health Check: http://localhost:8001/health")
    print(f"ℹ️  Server Info: http://localhost:8001/info")
    print(f"📋 Models List: http://localhost:8001/models")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)