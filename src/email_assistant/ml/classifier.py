from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import torch

from .vectorizer import HashingVectorizer

DEVICE = "cpu"


@dataclass
class LabelSpaces:
    cat1: list[str]
    cat2: list[str]
    cat3: list[str]
    cat4: list[str]

    @classmethod
    def from_taxonomy(cls, taxonomy: dict) -> LabelSpaces:
        labels = {c["name"]: c.get("labels", []) for c in taxonomy.get("categories", [])}

        def find(key):
            for k, v in labels.items():
                if key in k.lower():
                    return v
            return next(iter(labels.values()), [])

        return cls(
            cat1=find("type"),
            cat2=find("sender") or find("identity"),
            cat3=find("context"),
            cat4=find("handler"),
        )


class MultiHeadLinear(torch.nn.Module):
    def __init__(self, input_dim: int, label_spaces: LabelSpaces):
        super().__init__()
        self.head1 = torch.nn.Linear(input_dim, max(1, len(label_spaces.cat1)))
        self.head2 = torch.nn.Linear(input_dim, max(1, len(label_spaces.cat2)))
        self.head3 = torch.nn.Linear(input_dim, max(1, len(label_spaces.cat3)))
        self.head4 = torch.nn.Linear(input_dim, max(1, len(label_spaces.cat4)))

    def forward(self, x):
        return (self.head1(x), self.head2(x), self.head3(x), self.head4(x))


def _to_tensor(batch: list[list[float]]) -> torch.Tensor:
    return torch.tensor(batch, dtype=torch.float32, device=DEVICE)


def _labels_to_indices(y: list[str], space: list[str]) -> torch.Tensor:
    m = {v: i for i, v in enumerate(space)}
    return torch.tensor([m.get(v, 0) if space else 0 for v in y], dtype=torch.long, device=DEVICE)


def fit_classifier(
    df: pd.DataFrame, taxonomy: dict, n_features: int = 2**18, epochs: int = 3, lr: float = 0.5
):
    texts = (
        df["subject"].fillna("") + " " + df.get("body", pd.Series([""] * len(df))).fillna("")
    ).tolist()
    hv = HashingVectorizer(n_features=n_features, use_idf=True).fit(texts)
    X = hv.transform(texts)
    label_spaces = LabelSpaces.from_taxonomy(taxonomy)

    model = MultiHeadLinear(n_features, label_spaces).to(DEVICE)
    opt = torch.optim.Adagrad(model.parameters(), lr=lr, weight_decay=0.01)
    loss_fn = torch.nn.CrossEntropyLoss()

    y1 = _labels_to_indices(df["category1_type"].fillna("").tolist(), label_spaces.cat1)
    y2 = _labels_to_indices(df["category2_sender_identity"].fillna("").tolist(), label_spaces.cat2)
    y3 = _labels_to_indices(df["category3_context"].fillna("").tolist(), label_spaces.cat3)
    y4 = _labels_to_indices(df["category4_handler"].fillna("").tolist(), label_spaces.cat4)

    x_tensor = _to_tensor(X)
    for epoch in range(epochs):
        opt.zero_grad()
        o1, o2, o3, o4 = model(x_tensor)
        loss = loss_fn(o1, y1) + loss_fn(o2, y2) + loss_fn(o3, y3) + loss_fn(o4, y4)
        loss.backward()
        opt.step()
        print(f"epoch={epoch + 1} loss={loss.item():.4f}")

    return hv, model, label_spaces


def predict(
    hv: HashingVectorizer, model: MultiHeadLinear, label_spaces: LabelSpaces, texts: list[str]
) -> list[dict[str, str]]:
    X = _to_tensor(hv.transform(texts))
    with torch.no_grad():
        o1, o2, o3, o4 = model(X)
        p1 = torch.argmax(o1, dim=1).tolist()
        p2 = torch.argmax(o2, dim=1).tolist()
        p3 = torch.argmax(o3, dim=1).tolist()
        p4 = torch.argmax(o4, dim=1).tolist()

    def to(space, i):
        return space[i] if space and 0 <= i < len(space) else ""

    return [
        {
            "category0_reviewed": "reviewed",
            "category1_type": to(label_spaces.cat1, p1[i]),
            "category2_sender_identity": to(label_spaces.cat2, p2[i]),
            "category3_context": to(label_spaces.cat3, p3[i]),
            "category4_handler": to(label_spaces.cat4, p4[i]),
        }
        for i in range(len(texts))
    ]


def save_model(
    hv: HashingVectorizer, model: MultiHeadLinear, label_spaces: LabelSpaces, path: str
):
    torch.save(
        {
            "vectorizer": hv.save(),
            "label_spaces": label_spaces.__dict__,
            "state_dict": model.state_dict(),
        },
        path,
    )


def load_model(path: str):
    payload = torch.load(path, map_location=DEVICE)
    hv = HashingVectorizer.load(payload["vectorizer"])
    label_spaces = LabelSpaces(**payload["label_spaces"])
    model = MultiHeadLinear(hv.n_features, label_spaces)
    model.load_state_dict(payload["state_dict"])
    model.to(DEVICE).eval()
    return hv, model, label_spaces
