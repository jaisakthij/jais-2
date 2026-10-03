"""Train PULSE on synthetic longitudinal data and persist a CPU checkpoint."""
import os
import sys
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.join(_HERE, "LongitudinalGeneration")
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import numpy as np
import torch
from torch.utils.data import DataLoader

from pulse.data.dataset import LongitudinalDataset, create_synthetic_data, collate_visits
from pulse.model import PulseModel
from pulse.training.trainer import Trainer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_patients", type=int, default=400)
    ap.add_argument("--n_visits", type=int, default=3)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--modality_a_dim", type=int, default=61)
    ap.add_argument("--modality_b_dim", type=int, default=251)
    ap.add_argument("--train_mask_rate", type=float, default=0.6)
    ap.add_argument("--temporal_model", type=str, default="recurrent")
    ap.add_argument("--hidden_dim", type=int, default=128)
    ap.add_argument("--latent_dim", type=int, default=16)
    ap.add_argument("--save_dir", type=str, default=os.path.join(_HERE, "ckpt"))
    ap.add_argument("--device", type=str, default="cpu")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    os.makedirs(args.save_dir, exist_ok=True)

    modality_dims = {"modality_a": args.modality_a_dim, "modality_b": args.modality_b_dim}
    print(f"Generating synthetic data: {args.n_patients} patients x {args.n_visits} visits "
          f"(modality_a:{args.modality_a_dim}, modality_b:{args.modality_b_dim})...")
    patient_ids, visits_data, missing_masks = create_synthetic_data(
        n_patients=args.n_patients, n_visits=args.n_visits, modality_dims=modality_dims,
        missing_rate=0.0, seed=args.seed)

    dataset = LongitudinalDataset(
        patient_ids=patient_ids, visits_data=visits_data, missing_masks=missing_masks,
        min_completeness_ratio=1.0, train_mask_rate=args.train_mask_rate)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True,
                            collate_fn=collate_visits,
                            pin_memory=args.device.startswith("cuda"))

    model = PulseModel(
        modality_dims=modality_dims, latent_dim=args.latent_dim, hidden_dim=args.hidden_dim,
        lambda_kl=1.0, lambda_align=1.0, lambda_adv=0.1, temporal_model=args.temporal_model,
        temporal_num_heads=4, temporal_num_layers=1)
    model.to(args.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    print(f"Training on {args.device}...")
    trainer = Trainer(model=model, optimizer=optimizer, device=args.device)
    metrics = trainer.train(dataloader=dataloader, n_epochs=args.epochs, save_dir=args.save_dir)

    saved = [f for f in os.listdir(args.save_dir) if f.startswith("checkpoint_epoch_")]
    path = os.path.join(args.save_dir, sorted(saved)[-1])
    print(f"Done. Last checkpoint: {path}")

    # Persist a tiny manifest + config for the engine.
    config = {
        "latent_dim": args.latent_dim, "hidden_dim": args.hidden_dim,
        "modality_dims": modality_dims, "temporal_model": args.temporal_model,
        "seed": args.seed, "n_patients": args.n_patients, "n_visits": args.n_visits,
        "train_mask_rate": args.train_mask_rate, "train_metrics": metrics,
    }
    with open(os.path.join(args.save_dir, "model_config.json"), "w") as fh:
        np.savez(os.path.join(args.save_dir, "best_model.npz"),
                 np.asarray([float(m) for m in metrics.values()]))
    import json
    with open(os.path.join(args.save_dir, "train_config.json"), "w") as fh:
        json.dump(config, fh, indent=2)


if __name__ == "__main__":
    main()
