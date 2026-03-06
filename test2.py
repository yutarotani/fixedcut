#!/usr/bin/env python3

# Copyright (c) Peter Guld Leth 2025
# All rights reserved.

import os
import subprocess
import sys

def add_conversion_notice(svg_path):
    """Add a notice about the conversion tool to the SVG file."""
    try:
        with open(svg_path, 'r', encoding='shift-jis') as file:
            content = file.read()
        
        # Add notice after the XML declaration
        notice = '<!-- Converted from EPS using convert_eps_to_svg.py by Peter Guld Leth (https://github.com/kuff) -->\n'
        if '<?xml' in content:
            content = content.replace('?>', '?>\n' + notice, 1)
        else:
            content = notice + content
        
        with open(svg_path, 'w', encoding='utf-8') as file:
            file.write(content)
            
    except Exception as e:
        print(f"  Warning: Could not add conversion notice: {e}")

def convert_eps_to_svg(logos_dir="logos", inkscape_path=None):
    """
    Finds all .eps files in the specified directory (and subdirectories)
    and converts them to .svg using Inkscape.
    """
    print("\n=== Debug Information ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    # Default Inkscape paths for Windows
    default_paths = [
        r"C:\Program Files\Inkscape\bin\inkscape.exe",
        r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
    ]
    
    # Find Inkscape executable
    if inkscape_path is None:
        for path in default_paths:
            if os.path.exists(path):
                inkscape_path = path
                print(f"Found Inkscape at: {path}")
                # Test Inkscape version
                try:
                    version_result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        text=True
                    )
                    print(f"Inkscape version info:\n{version_result.stdout.strip()}")
                except Exception as e:
                    print(f"Warning: Could not get Inkscape version: {e}")
                break
        if inkscape_path is None:
            raise FileNotFoundError("Inkscape not found. Please install Inkscape or provide the correct path.")
    
    # Create svg_output directory if it doesn't exist
    output_dir = os.path.abspath("svg_output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory at: {output_dir}")
    else:
        print(f"Using existing output directory at: {output_dir}")
    
    # Check if logos directory exists
    logos_dir = os.path.abspath(logos_dir)
    if not os.path.exists(logos_dir):
        raise FileNotFoundError(f"Logos directory not found at: {logos_dir}")
    print(f"Processing logos from: {logos_dir}")
    
    for root, _, files in os.walk(logos_dir):
        for filename in files:
            if filename.lower().endswith(".eps"):
                eps_path = os.path.abspath(os.path.join(root, filename))
                # Create subdirectories in svg_output to match the source structure
                rel_path = os.path.relpath(root, logos_dir)
                output_subdir = os.path.join(output_dir, rel_path)
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                    print(f"Created subdirectory: {output_subdir}")
                
                svg_filename = os.path.splitext(filename)[0] + ".svg"
                svg_path = os.path.abspath(os.path.join(output_subdir, svg_filename))
                print(f"\nProcessing file:")
                print(f"  Source: {eps_path}")
                print(f"  Target: {svg_path}")
                
                try:
                    # Run Inkscape to convert EPS to SVG
                    result = subprocess.run(
                        [
                            inkscape_path,
                            eps_path,
                            "--export-filename=" + svg_path,
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print("Conversion output:")
                    if result.stdout:
                        print(f"  STDOUT: {result.stdout.strip()}")
                    if result.stderr:
                        print(f"  STDERR: {result.stderr.strip()}")
                    
                    if os.path.exists(svg_path):
                        print(f"✓ Successfully created: {svg_path}")
                        print(f"  File size: {os.path.getsize(svg_path)} bytes")
                        # Add conversion notice to the SVG file
                        add_conversion_notice(svg_path)
                    else:
                        print(f"✗ Error: File not created at {svg_path}")
                        
                except subprocess.CalledProcessError as e:
                    print(f"Error converting {eps_path} to SVG:")
                    print(f"  Return code: {e.returncode}")
                    print(f"  STDOUT: {e.stdout.strip()}")
                    print(f"  STDERR: {e.stderr.strip()}")

if __name__ == "__main__":
    try:
        # Replace "logos" with the path to your directory if needed
        convert_eps_to_svg("logos")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)