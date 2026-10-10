# Plan: Building Delft3D Flexible Mesh (D-Flow FM) from Public GitHub on Linux

> [!NOTE]
> **Status: APPROVED BY USER (INTEL oneAPI + CONAN NINJA BUILD).**
> Switched from GNU Make to an Intel oneAPI compilation using Conan 2, Ninja, and CMake. GNU compilers failed due to Makefile OOM, `mpi.mod` incompatibilities, and `mpi_bcast_` linking errors.

---

## 1. Executive Summary & Objective

This document outlines the exact verified recipe to compile the open-source **Delft3D Flexible Mesh** (D-Flow FM) engine natively on Ubuntu 22.04 LTS (Google Colab) from the `Deltares/Delft3D` GitHub repository. The build utilizes Intel oneAPI compilers, Conan for third-party dependencies, and Ninja for memory-efficient compilation.

---

## 2. Host Environment & Failures Noted

*   **Host:** Google Colab (Ubuntu 22.04 LTS, 2 cores).
*   **Compilers:** Intel oneAPI 2024.2 (`icx`, `icpx`, `ifx`) + Intel MPI 2021.13.
*   **Why GNU Failed:**
    *   **Makefile OOM:** Standard `make` caused out-of-memory errors on Colab.
    *   **mpi.mod:** GNU Fortran 11 encountered `mpi.mod` module format incompatibilities with pre-built MPI libraries.
    *   **Linking:** `mpi_bcast_` and other MPI symbols failed to link under GCC/gfortran.

---

## 3. Verified Build Recipe (Colab Sequence)

> [!WARNING]
> **Builder Notebook Status: NOT RUN**
> The build recipe below was executed manually in Colab on 10 Oct 2026 and is **RUN AND PASSED**. The corresponding `notebooks/delft3d_colab_builder.ipynb` is a generated artifact and remains **NOT RUN**.

### 3.1 Build Metadata
*   **Deltares Commit:** `761dc502e7fe3fac61ecece8c93b94b635f3643b` (2026-10-09 10:40:19 +0200, "UNST-10187: Replaced fp and hp by dp in nearfield (#1354)")
*   **Bundle Name:** `MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz` (147 MB)
*   **Bundle SHA-256:** `491364fbba88948752356fb1af0edc8aaecc496ba95545a9b66494c0ba1a6258`

### Step 1: Toolchain Installation
Install Intel oneAPI compilers, MPI, Conan, Ninja, and Patchelf.
```bash
wget -qO- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | tee /etc/apt/sources.list.d/oneAPI.list
apt-get update -qq
apt-get install -y -qq intel-oneapi-compiler-fortran intel-oneapi-compiler-dpcpp-cpp-and-cpp-classic intel-oneapi-mpi-devel ninja-build patchelf python3-pip
python3 -m pip install -q "conan>=2.0"
```

### Step 2: Source Clone, Checkout & Conan Initialization
```bash
git clone https://github.com/Deltares/Delft3D.git /content/delft3d_src
cd /content/delft3d_src
git checkout 761dc502e7fe3fac61ecece8c93b94b635f3643b
conan config install https://github.com/Deltares/conan-config.git
conan install . -pr:b delft3d_alma8_intel_2024_v3 -pr:h delft3d_alma8_intel_2024_v3 --build=missing
```

### Step 3: Source Code Patches (UNIX Shared Library Fixes)
Apply patches to `dflowfm-cli` and `dflowfm_dll` CMakeLists to ensure proper linking on UNIX. The exact patch appended to these targets is:
```cmake
if(UNIX)
    target_include_directories(<target> PRIVATE ${mpi_module_path})
    target_link_options(<target> PRIVATE ${openmp_flag})
endif()
```

### Step 4: CMake Configuration (Ninja)
```bash
source /opt/intel/oneapi/setvars.sh
cmake -S src/cmake -B build_ninja -G Ninja \
    -DCONFIGURATION_TYPE=dflowfm \
    -DCMAKE_TOOLCHAIN_FILE=build/generators/conan_toolchain.cmake \
    -DCMAKE_C_COMPILER=icx \
    -DCMAKE_CXX_COMPILER=icpx \
    -DCMAKE_Fortran_COMPILER=ifx \
    -Dmpi_include_path=/opt/intel/oneapi/mpi/latest/include \
    -DCMAKE_Fortran_STANDARD_LIBRARIES="-lifcore -limf -liomp5" \
    -DCMAKE_CXX_STANDARD_LIBRARIES="-limf -liomp5" \
    -DCMAKE_INSTALL_PREFIX=/content/delft3d_bin
```

### Step 5: Build, Patchelf, and Install
```bash
cmake --build build_ninja
# Apply patchelf to fix rpaths before install
find build_ninja -name "dflowfm" -exec patchelf --set-rpath "\$ORIGIN/../lib" {} \;
cmake --install build_ninja
```

### Step 6: Package to Google Drive
```bash
tar -czvf delft3dfm_linux_x86_64.tar.gz -C /content delft3d_bin
cp delft3dfm_linux_x86_64.tar.gz /content/drive/MyDrive/PravahX/
sha256sum /content/drive/MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz > /content/drive/MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz.sha256
```
