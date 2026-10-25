"""Segmentadores de vegetación tras el puerto `VegetationSegmenter`."""

from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_NDVI_THRESHOLD = 0.40


class NdviThresholdSegmenter:
    """Baseline: vegetación = NDVI >= umbral. No requiere entrenamiento."""

    def __init__(self, threshold: float = DEFAULT_NDVI_THRESHOLD) -> None:
        self._threshold = threshold

    def segment(self, ndvi_patches: np.ndarray) -> np.ndarray:
        return np.asarray(ndvi_patches) >= self._threshold


class UNetSegmenter:
    """U-Net ligera (PyTorch, import perezoso). Opcional: no la usa el pipeline por defecto.

    En producción se sustituye por un foundation model (Prithvi-EO-2.0 o Clay) con ajuste
    fino sobre parches Sentinel-2 etiquetados; la interfaz `segment` no cambia.
    Requiere `uv sync --extra dl` y pesos entrenados (`weights_path`).
    """

    def __init__(self, weights_path: Path | None = None, base_channels: int = 8) -> None:
        self._weights_path = weights_path
        self._base_channels = base_channels
        self._network = None

    def segment(self, ndvi_patches: np.ndarray) -> np.ndarray:
        torch = self._import_torch()
        network = self._load_network(torch)
        with torch.no_grad():
            x = torch.from_numpy(np.asarray(ndvi_patches, dtype=np.float32))[:, None]
            logits = network(x)
        return (torch.sigmoid(logits)[:, 0] >= 0.5).numpy()

    @staticmethod
    def _import_torch():
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ImportError("UNetSegmenter requiere torch: uv sync --extra dl") from exc
        return torch

    def _load_network(self, torch):
        if self._network is None:
            self._network = _build_unet(torch, self._base_channels)
            if self._weights_path is not None:
                self._network.load_state_dict(torch.load(self._weights_path, map_location="cpu"))
            self._network.eval()
        return self._network


def _build_unet(torch, c: int):
    """U-Net de dos niveles con una banda de entrada (NDVI) y un canal de salida."""
    nn = torch.nn

    def block(i: int, o: int):
        return nn.Sequential(
            nn.Conv2d(i, o, 3, padding=1), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.ReLU()
        )

    class UNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.enc1, self.enc2 = block(1, c), block(c, 2 * c)
            self.pool = nn.MaxPool2d(2)
            self.up = nn.Upsample(scale_factor=2, mode="nearest")
            self.dec1 = block(3 * c, c)
            self.head = nn.Conv2d(c, 1, 1)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool(e1))
            d1 = self.dec1(torch.cat([e1, self.up(e2)], dim=1))
            return self.head(d1)

    return UNet()
