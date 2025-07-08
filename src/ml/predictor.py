"""
Machine learning prediction engine for scoring arbitrage opportunities.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pickle
import os
import asyncio
from dataclasses import dataclass

from config.settings import settings


@dataclass
class MLPrediction:
    """ML prediction result."""
    confidence: float
    expected_profit: float
    probability_success: float
    risk_score: float
    recommendation: str  # 'buy', 'sell', 'hold'
    features_used: List[str]
    model_version: str


class FeatureEngineer:
    """Feature engineering for ML models."""
    
    def __init__(self):
        """Initialize feature engineer."""
        self.lookback_periods = [5, 10, 20, 50]
        self.feature_cache = {}
    
    async def extract_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract features for ML prediction."""
        features = {}
        
        try:
            # Basic opportunity features
            features.update(self._basic_features(opportunity))
            
            # Price-based features
            features.update(await self._price_features(opportunity, market_data))
            
            # Volume features
            features.update(await self._volume_features(opportunity, market_data))
            
            # Technical indicator features
            features.update(await self._technical_features(opportunity, market_data))
            
            # Market microstructure features
            features.update(await self._microstructure_features(opportunity, market_data))
            
            # Time-based features
            features.update(self._time_features())
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return {}
    
    def _basic_features(self, opportunity: Dict) -> Dict[str, float]:
        """Extract basic features from opportunity."""
        return {
            'profit_pct': opportunity.get('profit_pct', 0.0),
            'profit_abs': opportunity.get('profit_abs', 0.0),
            'buy_price': opportunity.get('buy_price', 0.0),
            'sell_price': opportunity.get('sell_price', 0.0),
            'price_ratio': opportunity.get('sell_price', 0.0) / max(opportunity.get('buy_price', 1.0), 0.001)
        }
    
    async def _price_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract price-based features."""
        features = {}
        
        symbol = opportunity.get('symbol', '')
        buy_exchange = opportunity.get('buy_exchange', '')
        sell_exchange = opportunity.get('sell_exchange', '')
        
        # Price volatility
        for exchange in [buy_exchange, sell_exchange]:
            key = f"{exchange}_{symbol}"
            if key in market_data:
                ticker = market_data[key].get('data', {})
                
                # Spread
                bid = ticker.get('bid', 0)
                ask = ticker.get('ask', 0)
                if ask > 0:
                    spread = (ask - bid) / ask
                    features[f'{exchange}_spread'] = spread
                
                # Last price
                features[f'{exchange}_last_price'] = ticker.get('last', 0)
        
        return features
    
    async def _volume_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract volume-based features."""
        features = {}
        
        symbol = opportunity.get('symbol', '')
        buy_exchange = opportunity.get('buy_exchange', '')
        sell_exchange = opportunity.get('sell_exchange', '')
        
        total_volume = 0
        for exchange in [buy_exchange, sell_exchange]:
            key = f"{exchange}_{symbol}"
            if key in market_data:
                ticker = market_data[key].get('data', {})
                volume = ticker.get('volume', 0)
                features[f'{exchange}_volume'] = volume
                total_volume += volume
        
        features['total_volume'] = total_volume
        features['volume_imbalance'] = abs(
            features.get(f'{buy_exchange}_volume', 0) - 
            features.get(f'{sell_exchange}_volume', 0)
        ) / max(total_volume, 1)
        
        return features
    
    async def _technical_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract technical indicator features."""
        features = {}
        
        # Placeholder for technical indicators
        # Would integrate with TA-Lib for real implementation
        features['rsi'] = 50.0  # Placeholder
        features['macd'] = 0.0  # Placeholder
        features['bollinger_position'] = 0.5  # Placeholder
        
        return features
    
    async def _microstructure_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract market microstructure features."""
        features = {}
        
        symbol = opportunity.get('symbol', '')
        buy_exchange = opportunity.get('buy_exchange', '')
        sell_exchange = opportunity.get('sell_exchange', '')
        
        # Order book features (if available)
        for exchange in [buy_exchange, sell_exchange]:
            orderbook_key = f"{exchange}_{symbol}_orderbook"
            if orderbook_key in market_data:
                orderbook = market_data[orderbook_key].get('data', {})
                
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])
                
                if bids and asks:
                    # Bid-ask spread
                    best_bid = bids[0][0] if bids[0] else 0
                    best_ask = asks[0][0] if asks[0] else 0
                    
                    if best_ask > 0:
                        features[f'{exchange}_orderbook_spread'] = (best_ask - best_bid) / best_ask
                    
                    # Order book depth
                    bid_depth = sum(bid[1] for bid in bids[:5])  # Top 5 levels
                    ask_depth = sum(ask[1] for ask in asks[:5])
                    
                    features[f'{exchange}_bid_depth'] = bid_depth
                    features[f'{exchange}_ask_depth'] = ask_depth
                    features[f'{exchange}_depth_imbalance'] = (bid_depth - ask_depth) / max(bid_depth + ask_depth, 1)
        
        return features
    
    def _time_features(self) -> Dict[str, float]:
        """Extract time-based features."""
        now = datetime.utcnow()
        
        return {
            'hour_of_day': now.hour / 24.0,
            'day_of_week': now.weekday() / 6.0,
            'is_weekend': float(now.weekday() >= 5),
            'is_market_hours': float(9 <= now.hour <= 17)  # Simplified
        }


class SimpleMLModel:
    """Simple ML model for opportunity scoring."""
    
    def __init__(self):
        """Initialize simple ML model."""
        self.is_trained = False
        self.feature_weights = {}
        self.scaler_params = {}
        
        # Initialize with some default weights
        self._initialize_default_weights()
    
    def _initialize_default_weights(self):
        """Initialize default feature weights."""
        self.feature_weights = {
            'profit_pct': 0.3,
            'profit_abs': 0.2,
            'total_volume': 0.1,
            'volume_imbalance': -0.1,
            'buy_exchange_spread': -0.15,
            'sell_exchange_spread': -0.15,
            'is_market_hours': 0.1
        }
    
    async def predict(self, features: Dict[str, float]) -> MLPrediction:
        """Make prediction based on features."""
        try:
            # Normalize features (simple min-max scaling)
            normalized_features = self._normalize_features(features)
            
            # Calculate weighted score
            score = 0.0
            used_features = []
            
            for feature_name, weight in self.feature_weights.items():
                if feature_name in normalized_features:
                    score += normalized_features[feature_name] * weight
                    used_features.append(feature_name)
            
            # Convert score to probability
            confidence = max(0.0, min(1.0, (score + 1) / 2))  # Sigmoid-like transformation
            
            # Estimate expected profit (simplified)
            expected_profit = features.get('profit_abs', 0) * confidence
            
            # Calculate risk score
            risk_score = 1.0 - confidence
            
            # Make recommendation
            if confidence > 0.7:
                recommendation = 'buy'
            elif confidence < 0.3:
                recommendation = 'sell'
            else:
                recommendation = 'hold'
            
            return MLPrediction(
                confidence=confidence,
                expected_profit=expected_profit,
                probability_success=confidence,
                risk_score=risk_score,
                recommendation=recommendation,
                features_used=used_features,
                model_version="simple_v1.0"
            )
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return MLPrediction(
                confidence=0.5,
                expected_profit=0.0,
                probability_success=0.5,
                risk_score=0.5,
                recommendation='hold',
                features_used=[],
                model_version="simple_v1.0"
            )
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Simple feature normalization."""
        normalized = {}
        
        for feature_name, value in features.items():
            # Simple clipping and normalization
            if 'pct' in feature_name or 'ratio' in feature_name:
                # Percentage features - clip to reasonable range
                normalized[feature_name] = max(-1.0, min(1.0, value / 10.0))
            elif 'volume' in feature_name:
                # Volume features - log normalization
                normalized[feature_name] = np.log1p(max(0, value)) / 20.0
            elif 'price' in feature_name:
                # Price features - relative to reasonable range
                normalized[feature_name] = max(0.0, min(1.0, value / 100000.0))
            elif 'spread' in feature_name:
                # Spread features - typically small values
                normalized[feature_name] = max(0.0, min(1.0, value * 1000))
            else:
                # Default normalization
                normalized[feature_name] = max(-1.0, min(1.0, value))
        
        return normalized
    
    async def train(self, training_data: List[Dict]):
        """Train the model with historical data."""
        # Placeholder for training logic
        # In a real implementation, this would train on historical opportunities
        # and their outcomes
        self.is_trained = True
        print("Model training completed (placeholder)")
    
    def save_model(self, filepath: str):
        """Save model to file."""
        try:
            model_data = {
                'feature_weights': self.feature_weights,
                'scaler_params': self.scaler_params,
                'is_trained': self.is_trained,
                'version': 'simple_v1.0'
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"Model saved to {filepath}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, filepath: str):
        """Load model from file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.feature_weights = model_data.get('feature_weights', {})
                self.scaler_params = model_data.get('scaler_params', {})
                self.is_trained = model_data.get('is_trained', False)
                
                print(f"Model loaded from {filepath}")
            else:
                print(f"Model file {filepath} not found, using default weights")
        except Exception as e:
            print(f"Error loading model: {e}")


class MLPredictor:
    """
    Main ML prediction engine that coordinates feature engineering and model predictions.
    """
    
    def __init__(self):
        """Initialize ML predictor."""
        self.feature_engineer = FeatureEngineer()
        self.model = SimpleMLModel()
        
        # Load existing model if available
        model_path = os.path.join(settings.ml.model_path, 'arbitrage_model.pkl')
        self.model.load_model(model_path)
        
        # Performance tracking
        self.predictions_made = 0
        self.prediction_accuracy = []
    
    async def predict_opportunity(self, opportunity: Dict, market_data: Dict = None) -> Dict:
        """
        Predict the viability of an arbitrage opportunity.
        
        Args:
            opportunity: The arbitrage opportunity to evaluate
            market_data: Current market data for feature extraction
            
        Returns:
            Dictionary containing prediction results
        """
        try:
            # Extract features
            if market_data:
                features = await self.feature_engineer.extract_features(opportunity, market_data)
            else:
                features = self.feature_engineer._basic_features(opportunity)
            
            # Make prediction
            prediction = await self.model.predict(features)
            
            self.predictions_made += 1
            
            # Return prediction in dictionary format for compatibility
            return {
                'confidence': prediction.confidence,
                'expected_profit': prediction.expected_profit,
                'probability_success': prediction.probability_success,
                'risk_score': prediction.risk_score,
                'recommendation': prediction.recommendation,
                'features_used': prediction.features_used,
                'model_version': prediction.model_version
            }
            
        except Exception as e:
            print(f"Error predicting opportunity: {e}")
            return {
                'confidence': 0.5,
                'expected_profit': 0.0,
                'probability_success': 0.5,
                'risk_score': 0.5,
                'recommendation': 'hold',
                'features_used': [],
                'model_version': 'error'
            }
    
    async def batch_predict(self, opportunities: List[Dict], market_data: Dict = None) -> List[Dict]:
        """Predict multiple opportunities in batch."""
        predictions = []
        
        for opportunity in opportunities:
            prediction = await self.predict_opportunity(opportunity, market_data)
            predictions.append(prediction)
        
        return predictions
    
    async def retrain_model(self, historical_data: List[Dict]):
        """Retrain the model with new historical data."""
        try:
            await self.model.train(historical_data)
            
            # Save updated model
            model_path = os.path.join(settings.ml.model_path, 'arbitrage_model.pkl')
            self.model.save_model(model_path)
            
            print("Model retrained successfully")
        except Exception as e:
            print(f"Error retraining model: {e}")
    
    async def evaluate_prediction(self, prediction: Dict, actual_outcome: Dict):
        """Evaluate prediction accuracy against actual outcome."""
        try:
            predicted_success = prediction['probability_success']
            actual_success = actual_outcome.get('success', False)
            
            # Simple accuracy tracking
            if (predicted_success > 0.5 and actual_success) or (predicted_success <= 0.5 and not actual_success):
                accuracy = 1.0
            else:
                accuracy = 0.0
            
            self.prediction_accuracy.append(accuracy)
            
            # Keep only recent accuracy data
            if len(self.prediction_accuracy) > 1000:
                self.prediction_accuracy = self.prediction_accuracy[-1000:]
            
        except Exception as e:
            print(f"Error evaluating prediction: {e}")
    
    async def get_model_performance(self) -> Dict:
        """Get model performance metrics."""
        if not self.prediction_accuracy:
            return {
                'accuracy': 0.0,
                'predictions_made': self.predictions_made,
                'model_trained': self.model.is_trained
            }
        
        return {
            'accuracy': np.mean(self.prediction_accuracy),
            'predictions_made': self.predictions_made,
            'recent_accuracy': np.mean(self.prediction_accuracy[-100:]) if len(self.prediction_accuracy) >= 100 else np.mean(self.prediction_accuracy),
            'model_trained': self.model.is_trained,
            'total_evaluations': len(self.prediction_accuracy)
        }
    
    async def get_feature_importance(self) -> Dict:
        """Get feature importance from the model."""
        return self.model.feature_weights.copy()
    
    async def update_feature_weights(self, new_weights: Dict[str, float]):
        """Update model feature weights."""
        self.model.feature_weights.update(new_weights)
        
        # Save updated model
        model_path = os.path.join(settings.ml.model_path, 'arbitrage_model.pkl')
        self.model.save_model(model_path)
    
    async def get_status(self) -> Dict:
        """Get ML predictor status."""
        return {
            'model_trained': self.model.is_trained,
            'predictions_made': self.predictions_made,
            'model_version': 'simple_v1.0',
            'feature_count': len(self.model.feature_weights),
            'accuracy': np.mean(self.prediction_accuracy) if self.prediction_accuracy else 0.0
        }
