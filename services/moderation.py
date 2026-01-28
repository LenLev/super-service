import numpy as np
from schemas.models import AdRequest

def prepare_features(ad: AdRequest) -> np.ndarray:

    if ad.images_qty < 0:
        raise ValueError("images_qty не может быть отрицательным")
    if ad.category < 0:
        raise ValueError("category не может быть отрицательным")

    is_verified = 1.0 if ad.is_verified_seller else 0.0
    images_qty_norm = min(ad.images_qty, 10) / 10.0
    description_len_norm = len(ad.description) / 1000.0
    category_norm = ad.category / 100.0

    features = np.array([[is_verified, images_qty_norm, description_len_norm, category_norm]])

    return features