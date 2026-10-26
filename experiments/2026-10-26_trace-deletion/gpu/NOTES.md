# Self-hosted run notes

## Instance

{"machine_id": "548505", "started_at": "2026-10-26T19:11:29+00:00", "work": "/home/trace-deletion"}

- Created with `jl create --gpu H100 --num-gpus 2 --vm --storage 250 --region IN2 --name netherite-trace --yes --json`.
- Changed from the command in `instruction_gpu.md` (approved by the user):
  - `--vm` added and `--template pytorch` dropped: 2 x H100 in IN2 had 0 free containers and 7 free VMs; `--template` applies to containers only.
  - `--region IN2` added: the rules allow only IN2, and the written command did not pin a region.
- Result: on-demand (`is_spot: false`, `billing_frequency: hour`, no reservation), 2 x H100, 48 cores, 400 GB RAM, 250 GB SSD, user `ubuntu`.

- Boot: the VM reported `Running` at 19:11:52Z but SSH (port 22) only answered at 19:21:09Z, about 10 minutes later. That time is billed.

## Session 2 (instruction_gpu_resume.md)

- Resumed with `jl resume 548505 --yes --json` at 2026-10-26T20:05:03Z. New machine id **548606** (same IP 151.185.52.24, 2 x H100, IN2, on-demand, hourly).
- `instance.json`: `{"machine_id": "548606", "started_at": "2026-10-26T20:05:03+00:00", "work": "/home/trace-deletion", "previous_hours": 0.65}`.
- Budget: at most 3 h from the resume; deadline guard at resume + 11700 s; monitor `--max-hours 3`.
- SSH answered at 20:06:22Z (about 1 minute). Checks: 2 x H100 80GB HBM3, 23 shards, vllm 0.15.0. The resumed machine has new SSH host keys on the same IP (expected after the id changed); `known_hosts` left unchanged.
- Deadline guard: `deadline guard active: pausing 548606 at Mon Oct 26 23:20:03 UTC 2026` (session 1 log kept as `deadline_session1.log`).
- Uploaded the new `continue.py` and `status.py` (MD5 matches local: 5beb16d4..., 9e86655a...). Remote and local `selfhost/sanity.json` renamed to `sanity_attempt1.json`. Server started 20:07:05Z (`serve_attempt2.log` is session 1's working server log).

- Server ready 20:12:25Z. Sanity (one request at a time, 27 requests) 20:12:44Z to about 20:26Z: **SANITY: FAIL** (`outputs/selfhost/sanity.json`, `outputs/selfhost/logs/sanity.log`).
  - Every generation ran to max_tokens 4096 (`finish_reason=length`, about 30.1 s each at about 136 tokens/s) and none produced an Answer line: the 2 fresh answers without pre-fill, the 2 with `<think></think>` pre-filled, and all 6 trace continuations.
  - The visible content of those 4096-token outputs is essentially empty: `'<think>'`, `'\n'` or `' '`. So the model generated 4096 tokens that decode to nothing visible, which points to degenerate output (for example NaN logits giving the same special token every step) rather than long reasoning. Not verified; needs a token-level check.
  - The PASS checks are therefore vacuous: "not restarted" passes because the output is empty, and 8/8 identical repeats are identical empty outputs.
  - The session 1 fresh answers (`'<think>'`) were probably the same symptom, not "opened a thinking block and stopped".
- Downloaded `selfhost/` and logs (`serve_tail_session2.log`, `sanity.log`, `deadline.log`). Paused with `jl pause 548606 --yes` at 20:27:00Z. Session 2 runtime about 0.37 h (about ₹242). Total both sessions about 1.02 h (about ₹671). The pause stopped the deadline guard process.

## Probe (19:21Z)

- `ubuntu` (uid 1000), passwordless sudo works. Ubuntu 22.04.5 LTS, Python 3.10.12, `venv` available, `wget` and `curl` present.
- **pip missing** (`No module named pip`).
- `nvidia-smi`: 2 x NVIDIA H100 80GB HBM3 (81559 MiB each), driver 580.126.20, CUDA 13.0.
- Disk: `/dev/vda1` 243G mounted at `/` (227G free); `/home` is on the same disk, so no symlinks were needed. `/home` is root-owned.

## Environment fixes (no change to continue.py, decoding settings or requests)

- Installed pip with `sudo apt-get install -y python3-pip` (pip 22.0.2). Reason: the image has no pip.
- Created `/home/trace-deletion` and `/home/models` with `sudo mkdir -p` and `sudo chown -R ubuntu:`. Reason: `/home` is not writable by `ubuntu`; the scripts and monitor use these absolute paths.
- `gpu/setup.sh` and `gpu/serve.sh`: added `export PATH="$HOME/.local/bin:$PATH"` after `set -euo pipefail`. Reason: as a non-root user pip installs to `~/.local`, so `hf`/`huggingface-cli` (setup.sh) and `vllm` (serve.sh) would not be on PATH in a fresh shell.
- Setup finished at about 19:38Z: `105G`, `vllm 0.15.0`, `PATCH_OK`, `23`, `SETUP_DONE`. Torch check: `2.9.1+cu128 12.8 True 2`. Server started 19:40Z.
- `gpu/serve.sh`: added `--block-size 64`. Reason: the first start (log kept as `serve_attempt1.log`) crashed at 19:41Z with `ValueError: No common block size for 16`. vLLM picked the FLASHMLA attention backend (`Using FLASHMLA attention backend out of potential backends: ('FLASHMLA',)`), which only supports KV-cache blocks of 64 tokens, while the KV manager defaulted to 16. Block size changes only the KV-cache memory layout, not the decoding settings. Restarted 19:42:48Z.
- Server ready 19:44Z (`/v1/models` lists `sarvam-105b-fp8`).
- Sanity 19:45Z: **SANITY: FAIL**. Split-word continuation PASS ('us.'); English A continuations PASS (0 of 4 restarted); **fresh answers FAIL**: both fresh answers (`add_generation_prompt=true`, `enable_thinking=false`) returned the content `<think>` and nothing else. Same request twice identical: 0/8 (informational). Downloaded `outputs/selfhost/sanity.json`; paused the VM with `jl pause 548505 --yes` at 19:50:24Z, as the instructions require on FAIL. Runtime about 0.65 h (19:11:29Z to 19:50:24Z), about ₹429. The pause stopped the deadline guard process; it must be restarted if the VM is resumed.
- Deadline guard launched with `PATH=$HOME/.local/bin:$PATH` in its environment (not a change to `deadline.sh`), for the same reason: `deadline.sh` pip-installs `jl` and then calls it. `deadline.log`: `deadline guard active: pausing 548505 at Mon Oct 26 23:41:29 UTC 2026` (start + 16200 s).
