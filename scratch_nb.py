import nbformat as nbf
import json

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell('# 1. Setup & Restore Delft3D Bundle'))
cells.append(nbf.v4.new_code_cell('''\
from google.colab import drive
drive.mount('/content/drive')
'''))

cells.append(nbf.v4.new_code_cell('''\
%%bash
set -e
cp /content/drive/MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz .
cp /content/drive/MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz.sha256 .

echo "Verifying SHA256..."
sha256sum -c delft3dfm_linux_x86_64.tar.gz.sha256

echo "Extracting..."
rm -rf /content/delft3d_bin
mkdir -p /content/delft3d_bin
tar -xf delft3dfm_linux_x86_64.tar.gz -C /content/delft3d_bin

# Fallback Intel runtime installation if ldd is missing
if ldd /content/delft3d_bin/bin/dflowfm | grep -q "not found"; then
  echo "Intel libs missing, installing..."
  wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null
  echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | sudo tee /etc/apt/sources.list.d/oneAPI.list
  sudo apt-get update
  sudo apt-get install -y intel-oneapi-compiler-shared-runtime-2024.2 intel-oneapi-mpi-2021.13
fi

export LD_LIBRARY_PATH=/content/delft3d_bin/lib:$LD_LIBRARY_PATH
/content/delft3d_bin/bin/dflowfm --version
'''))

cells.append(nbf.v4.new_markdown_cell('# 2. Clone PravahX & Install Deps'))
cells.append(nbf.v4.new_code_cell('''\
%%bash
rm -rf PravahX
git clone https://github.com/Aesha023/The-Akashic-Nodes.git PravahX
cd PravahX
# git checkout main  # Uncomment to pin commit
pip install hydrolib-core netCDF4 numpy
'''))

cells.append(nbf.v4.new_markdown_cell('# 3. Generate and Run Benchmark Variants'))
cells.append(nbf.v4.new_code_cell('''\
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

sys.path.append('/content/PravahX')
from core.pravahx.engines.delft3d_fm.benchmark import Delft3DBenchmark
from hydrolib.core.dflowfm.mdu.models import FMModel

work_dir = Path('/content/runs')
work_dir.mkdir(exist_ok=True)

variants = {
    'Base_Frictionless': {'dx': 5.0, 'epsHu': None, 'uniffrictcoef': 0.0},
    'Variant_A_epsHu': {'dx': 5.0, 'epsHu': 0.01, 'uniffrictcoef': 0.0},
    'Variant_B_Manning': {'dx': 5.0, 'epsHu': None, 'uniffrictcoef': 0.005},
    'Variant_C_Fine_dx': {'dx': 2.5, 'epsHu': None, 'uniffrictcoef': 0.0},
}

results = []

for name, config in variants.items():
    print(f"\\n=== Running {name} ===")
    benchmark = Delft3DBenchmark(length=2000, width=50, dx=config['dx'])
    
    case_dir = work_dir / name
    if case_dir.exists():
        shutil.rmtree(case_dir)
        
    benchmark.generate_case(case_dir)
    
    # Modify MDU for specific variant settings
    mdu_path = case_dir / "ritter.mdu"
    fm = FMModel(filepath=mdu_path)
    fm.physics.uniffrictcoef = config['uniffrictcoef']
    if config['epsHu'] is not None:
        fm.numerics.epshu = config['epsHu']
    fm.save(filepath=mdu_path)
    
    # Run
    print("Executing Delft3D FM...")
    subprocess.run(["bash", "run_linux.sh"], cwd=case_dir, check=True)
    
    # Evaluate
    map_nc_path = case_dir / "DFM_OUTPUT_ritter" / "ritter_map.nc"
    if map_nc_path.exists():
        res = benchmark.evaluate_results(map_nc_path)
        results.append({
            'variant': name,
            'passes': res.passes_tolerance,
            'rmse_m': res.rmse_m,
            'front_err_m': res.front_error_m,
            'front_err_rel': res.front_error_rel,
            'notes': res.notes,
        })
        print(res.notes)
    else:
        print("ERROR: Output map.nc not found!")

'''))

cells.append(nbf.v4.new_markdown_cell('# 4. Report and Save to Drive'))
cells.append(nbf.v4.new_code_cell('''\
from datetime import datetime
import pandas as pd
from IPython.display import display

df = pd.DataFrame(results)
print("\\n=== FINAL RESULTS ===")
display(df)

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
out_dir = Path(f'/content/drive/MyDrive/PravahX/ritter_results_{timestamp}')
out_dir.mkdir(exist_ok=True, parents=True)

df.to_json(out_dir / 'report.json', orient='records', indent=2)

for name in variants.keys():
    map_file = work_dir / name / "DFM_OUTPUT_ritter" / "ritter_map.nc"
    if map_file.exists():
        shutil.copy(map_file, out_dir / f"{name}_map.nc")

print(f"\\nSaved all results and map files to: {out_dir}")
'''))

nb.cells = cells
with open('c:/Users/Krishna/Desktop/Pravahx/notebooks/ritter_benchmark_colab.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
