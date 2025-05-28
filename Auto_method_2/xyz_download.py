# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import pandas as pd
from ccdc.search import TextNumericSearch
from ccdc.io import EntryReader
from ccdc.molecule import Molecule

current_dir = os.path.dirname(os.path.abspath(__file__))

# Load CCDC Deposition Numbers and indices from a CSV file
def load_ccdc_numbers_from_csv(file_path):
    df = pd.read_csv(file_path)
    if '8. CCDC编号' not in df.columns:
        raise ValueError("csv 文件中必须包含 '8. CCDC编号' 列！")
    
    # Filter out non-numeric CCDC numbers and convert them to integers
    df = df[pd.to_numeric(df['8. CCDC编号'], errors='coerce').notna()]  # Keep valid numbers
    df['8. CCDC编号'] = df['8. CCDC编号'].astype(int)  # Convert to integers
    return df

# Remove solvent molecules based on the CSD Molecule API
def remove_solvent_from_molecule(molecule):
    non_solvent_molecule = Molecule(identifier=molecule.identifier)

    for component in molecule.components:
        if not component.is_organic:  # Determine if it's a solvent (adjust logic as needed)
            for atom in component.atoms:
                non_solvent_molecule.add_atom(atom)

    return non_solvent_molecule

# Generate solvent-free XYZ files directly based on CCDC Numbers
def generate_xyz_with_index(ccdc_data, output_folder):
    xyz_folder = output_folder

    if not os.path.exists(xyz_folder):
        os.makedirs(xyz_folder)

    searcher = TextNumericSearch()  # For CCDC Number search
    reader = EntryReader('CSD')  # Read from the CSD database

    downloaded = []
    failed = []

    for index, row in ccdc_data.iterrows():
        ccdc_number = row['8. CCDC编号']
        excel_index = row['Index']  # Get the corresponding index from Excel

        try:
            # Search for Entry using CCDC Number
            searcher.clear()
            searcher.add_ccdc_number(ccdc_number)
            hits = searcher.search()
            if not hits:
                raise ValueError(f"未找到 CCDC Number: {ccdc_number}")

            # Get the first matching Entry
            entry = hits[0].entry
            crystal = entry.crystal  # Get the Crystal object

            # Extract the molecule object
            molecule = crystal.molecule

            # Remove solvent molecules
            molecule_no_solvent = remove_solvent_from_molecule(molecule)

            # Check if the molecule is empty
            if not molecule_no_solvent.atoms:
                raise ValueError(f"分子 {ccdc_number} 移除溶剂后为空，跳过生成。")

            # Save as .xyz file
            xyz_path = os.path.join(xyz_folder, f"{excel_index}_{ccdc_number}_{entry.identifier}.xyz")
            with open(xyz_path, 'w') as xyz_file:
                valid_atoms = [atom for atom in molecule_no_solvent.atoms if atom.coordinates]
                if not valid_atoms:
                    raise ValueError(f"分子 {ccdc_number} 中没有有效的原子坐标，跳过生成。")

                xyz_file.write(f"{len(valid_atoms)}\n")
                xyz_file.write(f"CCDC Number: {ccdc_number}, Identifier: {entry.identifier}\n")
                for atom in valid_atoms:
                    xyz_file.write(f"{atom.atomic_symbol} {atom.coordinates.x:.4f} {atom.coordinates.y:.4f} {atom.coordinates.z:.4f}\n")

            downloaded.append(ccdc_number)
            print(f"成功生成 XYZ 文件: {excel_index}_{ccdc_number} -> {entry.identifier}")
        except Exception as e:
            print(f"生成失败: {excel_index}_{ccdc_number} - {e}")
            failed.append(ccdc_number)

    return downloaded, failed

if __name__ == "__main__":
    # Configure input file and output folder
    csv_file = os.path.join(current_dir, "final_results.csv")  # Path to the CSV file containing CCDC Numbers
    output_folder = os.path.join(current_dir, "output_xyz_files")  # Path to save XYZ files

    # Load CCDC Numbers and indices
    try:
        ccdc_data = load_ccdc_numbers_from_csv(csv_file)
        print(f"成功加载 {len(ccdc_data)} 个 CCDC Numbers。")

        # Generate solvent-free XYZ files
        downloaded, failed = generate_xyz_with_index(ccdc_data, output_folder)
        print(f"\n生成完成！成功: {len(downloaded)}，失败: {len(failed)}")

        if failed:
            print("生成失败的 CCDC Numbers:", failed)
    except Exception as e:
        print("发生错误:", e)
