import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from typing import Dict, List

SEQUENCE_LENGTH = 10
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lstm_price_model.keras")


class LSTMPricePredictor:
    """
    2-layer LSTM network that predicts whether a flight/transport price
    will rise or fall in the next booking window.

    Architecture:
        Input  → LSTM(64, return_sequences=True)
               → Dropout(0.2)
               → LSTM(32)
               → Dropout(0.2)
               → Dense(16, relu)
               → Dense(1, sigmoid)
    Output: probability of price going UP (>0.5 → UP, <0.5 → DOWN)
    """

    def __init__(self):
        self.model = None
        self.scaler_min = 500.0
        self.scaler_max = 15000.0
        self._init_model()

    # ── Data generation ────────────────────────────────────────────────────────

    def _generate_sequences(self, n: int = 1200, base: float = 5000.0):
        """
        Synthesise realistic Indian flight price sequences.
        Patterns included:
          • Random upward / downward macro trend
          • Weekly seasonality (prices spike Fri–Sat)
          • Gaussian noise
          • Demand shock spikes (rare sudden surge)
        """
        X, y = [], []
        rng = np.random.default_rng(42)

        for _ in range(n):
            trend_dir = rng.choice([-1, 1])
            price = base * rng.uniform(0.6, 1.4)
            seq = []

            for t in range(SEQUENCE_LENGTH + 1):
                weekly   = np.sin(2 * np.pi * t / 7) * base * 0.04
                trend    = trend_dir * base * 0.015
                noise    = rng.normal(0, base * 0.025)
                shock    = base * 0.12 if rng.random() < 0.05 else 0.0
                price    = max(price + trend + weekly + noise + shock, base * 0.25)
                seq.append(price)

            X.append(seq[:SEQUENCE_LENGTH])
            y.append(1 if seq[SEQUENCE_LENGTH] > seq[SEQUENCE_LENGTH - 1] else 0)

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        return (x - self.scaler_min) / (self.scaler_max - self.scaler_min + 1e-8)

    # ── Model build & train ────────────────────────────────────────────────────

    def _build_model(self, tf):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(SEQUENCE_LENGTH, 1)),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1,  activation="sigmoid"),
        ], name="lstm_price_predictor")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )
        return model

    def _init_model(self):
        try:
            import tensorflow as tf

            # ── Load cached model if available ─────────────────────────────
            if os.path.exists(MODEL_PATH):
                self.model = tf.keras.models.load_model(MODEL_PATH)
                print("[LSTM] Loaded cached model from disk.")
                return

            print("[LSTM] Training price-prediction model on synthetic data…")
            X, y = self._generate_sequences()
            X_norm = self._normalize(X).reshape(-1, SEQUENCE_LENGTH, 1)

            # 80 / 20 split
            split = int(0.8 * len(X_norm))
            X_tr, X_val = X_norm[:split], X_norm[split:]
            y_tr, y_val = y[:split],      y[split:]

            self.model = self._build_model(tf)

            cb = [
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss", patience=4, restore_best_weights=True
                )
            ]
            self.model.fit(
                X_tr, y_tr,
                validation_data=(X_val, y_val),
                epochs=30,
                batch_size=32,
                callbacks=cb,
                verbose=0,
            )

            val_loss, val_acc = self.model.evaluate(X_val, y_val, verbose=0)
            print(f"[LSTM] Training complete — val_accuracy: {val_acc:.3f}  val_loss: {val_loss:.4f}")

            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            self.model.save(MODEL_PATH)
            print(f"[LSTM] Model saved → {MODEL_PATH}")

        except Exception as e:
            print(f"[LSTM] Init failed ({e}); falling back to heuristic predictor.")
            self.model = None

    # ── Inference ──────────────────────────────────────────────────────────────

    def _simulate_history(self, base_price: float, route_key: str) -> List[float]:
        """Generate a plausible recent price history for any route."""
        seed = abs(hash(route_key)) % (2 ** 31)
        rng  = np.random.default_rng(seed)
        prices = [base_price]
        for _ in range(SEQUENCE_LENGTH - 1):
            delta = prices[-1] * rng.uniform(-0.04, 0.04)
            prices.append(max(prices[-1] + delta, base_price * 0.4))
        return prices

    def predict(self, base_price: float, route_key: str = "") -> Dict:
        """
        Returns price-trend prediction for a given base price and route.

        Returns
        -------
        {
            trend          : "UP" | "DOWN",
            confidence     : float  (percentage, e.g. 78.4),
            current_price  : int,
            predicted_price: int,
            change_pct     : float,
            recommendation : str,
            model          : str,
        }
        """
        if self.model is None:
            return self._heuristic(base_price, route_key)

        try:
            import tensorflow as tf

            history = self._simulate_history(base_price, route_key)
            x       = self._normalize(np.array(history, dtype=np.float32))
            x       = x.reshape(1, SEQUENCE_LENGTH, 1)

            prob  = float(self.model.predict(x, verbose=0)[0][0])
            up    = prob > 0.5
            conf  = round((prob if up else 1 - prob) * 100, 1)
            delta = base_price * (0.09 if up else -0.07)

            return {
                "trend":           "UP"   if up else "DOWN",
                "confidence":      conf,
                "current_price":   int(base_price),
                "predicted_price": int(base_price + delta),
                "change_pct":      round(abs(delta / base_price) * 100, 1),
                "recommendation":  "Book Now — prices likely to rise 🔴"
                                   if up else
                                   "Wait — prices likely to drop 🟢",
                "model":           "LSTM (64→32 units, TensorFlow 2.x)",
            }

        except Exception as e:
            return self._heuristic(base_price, route_key)

    def _heuristic(self, base_price: float, route_key: str) -> Dict:
        """Deterministic fallback when TF is unavailable."""
        seed = abs(hash(route_key + str(int(base_price)))) % 100
        up   = seed > 45
        conf = 55.0 + (seed % 25)
        delta = base_price * (0.09 if up else -0.07)
        return {
            "trend":           "UP"   if up else "DOWN",
            "confidence":      round(conf, 1),
            "current_price":   int(base_price),
            "predicted_price": int(base_price + delta),
            "change_pct":      round(abs(delta / base_price) * 100, 1),
            "recommendation":  "Book Now — prices likely to rise 🔴"
                               if up else
                               "Wait — prices likely to drop 🟢",
            "model":           "Heuristic fallback (LSTM unavailable)",
        }

    def model_summary(self) -> str:
        if self.model is None:
            return "Model not loaded."
        lines = []
        self.model.summary(print_fn=lambda x: lines.append(x))
        return "\n".join(lines)


# Module-level singleton — trained once on import
lstm_predictor = LSTMPricePredictor()
