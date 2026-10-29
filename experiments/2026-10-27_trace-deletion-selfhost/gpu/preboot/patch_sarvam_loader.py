import hashlib
import sys
from pathlib import Path

OLD = """    def load_weights(
        self,
        weights: Iterable[tuple[str, torch.Tensor]],
    ) -> set[str]:
        loader = AutoWeightsLoader(self)
        return loader.load_weights(weights)
"""
NEW = """    def load_weights(
        self,
        weights: Iterable[tuple[str, torch.Tensor]],
    ) -> set[str]:
        n_layers = self.config.num_hidden_layers
        weights = (
            (n, w)
            for n, w in weights
            if not n.endswith(("k_scale", "v_scale", "q_scale", "prob_scale", "kv_scale"))
            and not (n.startswith("model.layers.") and int(n.split(".")[2]) >= n_layers)
        )
        loader = AutoWeightsLoader(self)
        return loader.load_weights(weights)
"""

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if NEW in text:
    print("already patched")
    sys.exit(0)
if text.count(OLD) != 1:
    sys.exit(f"expected exactly one SarvamMLAForCausalLM.load_weights block, found {text.count(OLD)}; not patching")
path.with_suffix(".py.orig").write_text(text, encoding="utf-8")
path.write_text(text.replace(OLD, NEW), encoding="utf-8")
print("patched", path, hashlib.sha256(path.read_bytes()).hexdigest()[:16])
