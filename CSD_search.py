# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import ccdc.search
import ccdc.io
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the target substructure [Au]-[Au]
specified = ccdc.search.SMARTSSubstructure("[Au]-[Au]")                 #--> [Au]-[Au]

# Create a substructure search object and configure the search settings
substructure_search = ccdc.search.SubstructureSearch()
settings = substructure_search.settings
settings.only_organometallic = True
settings.no_disorder = 'Non-hydrogen'
settings.no_ions = True
settings.not_polymeric = True
settings.must_not_have_elements = ['Re', 'Ir', 'As', 'Cu', 'Os', 'Fe', 'Co', 
                                   'Ru', 'W', 'B', 'Ag', 'Li', 'Se', 'Si', 
                                   'Rh', 'Mn', 'Pd', 'Ge', 'Sb', 'Sn']   # --> Remove unwanted elements
substructure_search.add_substructure(specified)

# Perform the substructure search
hits = substructure_search.search()

# Read the CSD database
csd_reader = ccdc.io.EntryReader('CSD')
specified_molecules = []

# Filter molecules that contain Au2 in the formula
for i in range(len(hits)):
    id = hits[i].identifier
    hit = csd_reader.entry(id)
    formula = hit.molecule.formula
    if 'Au2 ' in formula:                                               # --> check if 'Au2' in formula
        specified_molecules.append(hits[i].identifier)

# Remove duplicates and sort the list of molecules
specified_molecules = sorted(list(set(specified_molecules)))

# Collect molecule and DOI information
data = []
for i in range(len(specified_molecules)):
    abruf = csd_reader.entry(specified_molecules[i])
    doi = abruf.publication.doi if abruf.publication else None
    data.append([specified_molecules[i], doi])

# Save the information to a CSV file
df = pd.DataFrame(data, columns=["Molecule", "DOI"])
df['url'] = df['DOI'].apply(lambda doi: f"https://doi.org/{doi}" if pd.notna(doi) else None)
output_file = os.path.join(current_dir, "molecule_doi_info.csv")
df.to_csv(output_file, index_label="Index")
print("Search complete. Results saved to 'molecule_doi_info.csv'.")
