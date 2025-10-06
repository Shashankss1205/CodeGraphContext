# src/codegraphcontext/package_resolver.py
import importlib
import subprocess
import os
import stdlibs
from pathlib import Path
from typing import Optional
from .utils.debug_log import debug_log


def _get_python_package_path(package_name: str) -> Optional[str]:
    """
    Finds the local installation path of a Python package.

    This function uses `importlib` to locate a package and determines its root
    directory, handling both regular packages (directories with __init__.py)
    and single-file modules.

    Args:
        package_name: The name of the package to locate (e.g., "requests").

    Returns:
        The absolute path to the package's directory as a string, or None if not found.
    """
    try:
        debug_log(f"Getting local path for Python package: {package_name}")

        module = importlib.import_module(package_name)

        if hasattr(module, '__file__') and module.__file__:
            module_file = Path(module.__file__)
            debug_log(f"Module file: {module_file}")

            if module_file.name == '__init__.py':
                # For a package, the path is the parent directory of __init__.py
                package_path = str(module_file.parent)
            elif package_name in stdlibs.module_names:
                # For a standard library single file module, the path is the file itself
                package_path = str(module_file)
            else:
                # For other single-file modules, assume the parent directory is the container
                package_path = str(module_file.parent)

            debug_log(f"Determined package path: {package_path}")
            return package_path

        elif hasattr(module, '__path__'):
            # This handles namespace packages which may not have an __init__.py
            if isinstance(module.__path__, list) and module.__path__:
                package_path = str(Path(module.__path__[0]))
                debug_log(f"Package path from __path__: {package_path}")
                return package_path
            else:
                # Fallback for other __path__ formats
                package_path = str(Path(str(module.__path__)))
                debug_log(f"Package path from __path__ (str): {package_path}")
                return package_path

        debug_log(f"Could not determine path for {package_name}")
        return None

    except ImportError as e:
        debug_log(f"Could not import {package_name}: {e}")
        return None
    except Exception as e:
        debug_log(f"Error getting local path for {package_name}: {e}")
        return None


def _get_cpp_package_path(package_name: str) -> Optional[str]:
    """
    Finds the local installation path of a C++ package.

    This function attempts to locate a C++ package using multiple strategies:
    1. Using pkg-config to find the package installation path
    2. Searching common C++ include directories
    3. Checking vcpkg installation directories (Windows)

    Args:
        package_name: The name of the package to locate (e.g., "tinyxml2", "nlohmann_json").

    Returns:
        The absolute path to the package's directory as a string, or None if not found.
    """
    try:
        debug_log(f"Getting local path for C++ package: {package_name}")

        # Strategy 1: Try using pkg-config
        try:
            result = subprocess.run(
                ['pkg-config', '--variable=includedir', package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                include_dir = result.stdout.strip()
                # Check if the package has a subdirectory with its name
                package_dir = os.path.join(include_dir, package_name)
                if os.path.exists(package_dir):
                    debug_log(f"Found C++ package via pkg-config: {package_dir}")
                    return package_dir
                # Otherwise return the include directory itself
                if os.path.exists(include_dir):
                    debug_log(f"Found C++ package include dir via pkg-config: {include_dir}")
                    return include_dir
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            debug_log(f"pkg-config not available or timed out: {e}")

        # Strategy 2: Search common include directories on Linux/macOS/Windows
        common_include_dirs = [
            '/usr/include',
            '/usr/local/include',
            '/opt/homebrew/include',  # macOS Homebrew ARM
            '/opt/local/include',      # MacPorts
            'C:\\MinGW\\include',      # MinGW on Windows
            'C:\\msys64\\mingw64\\include',  # MSYS2 on Windows
            'C:\\msys64\\ucrt64\\include',   # MSYS2 UCRT on Windows
        ]

        for base_dir in common_include_dirs:
            package_dir = os.path.join(base_dir, package_name)
            if os.path.exists(package_dir):
                debug_log(f"Found C++ package in common include dir: {package_dir}")
                return package_dir

            # Some packages might be directly in the include directory
            # Check for header files with the package name
            if os.path.exists(base_dir):
                try:
                    for item in os.listdir(base_dir):
                        if package_name.lower() in item.lower():
                            potential_path = os.path.join(base_dir, item)
                            if os.path.isdir(potential_path):
                                debug_log(f"Found C++ package by name matching: {potential_path}")
                                return potential_path
                except PermissionError:
                    continue

        # Strategy 3: Check vcpkg installation (Windows and cross-platform)
        vcpkg_paths = []

        # Check VCPKG_ROOT environment variable
        vcpkg_root = os.environ.get('VCPKG_ROOT')
        if vcpkg_root:
            vcpkg_paths.append(os.path.join(vcpkg_root, 'installed'))

        # Common vcpkg installation locations
        vcpkg_paths.extend([
            os.path.join(os.path.expanduser('~'), 'vcpkg', 'installed'),
            'C:\\vcpkg\\installed',
            '/usr/local/vcpkg/installed',
        ])

        for vcpkg_installed in vcpkg_paths:
            if os.path.exists(vcpkg_installed):
                # Check different triplets (x64-windows, x64-linux, etc.)
                try:
                    for triplet_dir in os.listdir(vcpkg_installed):
                        triplet_path = os.path.join(vcpkg_installed, triplet_dir)
                        if os.path.isdir(triplet_path):
                            include_dir = os.path.join(triplet_path, 'include')
                            if os.path.exists(include_dir):
                                package_dir = os.path.join(include_dir, package_name)
                                if os.path.exists(package_dir):
                                    debug_log(f"Found C++ package in vcpkg: {package_dir}")
                                    return package_dir
                except PermissionError:
                    continue

        # Strategy 4: Check for header-only libraries in common locations
        # Special handling for nlohmann/json which might be installed as "nlohmann"
        if package_name in ['json', 'nlohmann_json']:
            for base_dir in common_include_dirs:
                nlohmann_dir = os.path.join(base_dir, 'nlohmann')
                if os.path.exists(nlohmann_dir):
                    debug_log(f"Found nlohmann/json package: {nlohmann_dir}")
                    return nlohmann_dir

        debug_log(f"Could not find C++ package: {package_name}")
        return None

    except Exception as e:
        debug_log(f"Error getting local path for C++ package {package_name}: {e}")
        return None


def get_local_package_path(package_name: str, language: str = "python") -> Optional[str]:
    """
    Finds the local installation path of a package for the specified language.

    Args:
        package_name: The name of the package to locate.
        language: The programming language of the package (e.g., "python", "cpp").

    Returns:
        The absolute path to the package's directory as a string, or None if not found.
    """
    finders = {
        "python": _get_python_package_path,
        "cpp": _get_cpp_package_path,
    }

    finder = finders.get(language.lower())
    if not finder:
        debug_log(f"Unsupported language: {language}")
        return None

    return finder(package_name)
