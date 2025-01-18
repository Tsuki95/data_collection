# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import ccdc.search
import ccdc.io
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the target substructure [Au]-[Au]
dAu = ccdc.search.SMARTSSubstructure("[Au]-[Au]")

# Create a substructure search object and configure search settings
substructure_search = ccdc.search.SubstructureSearch()
settings = substructure_search.settings
settings.only_organometallic = True
settings.no_disorder = 'Non-hydrogen'
settings.no_ions = True
settings.not_polymeric = True
settings.must_not_have_elements = ['Re', 'Ir', 'As', 'Cu', 'Os', 'Fe', 'Co', 
                                   'Ru', 'W', 'B', 'Ag', 'Li', 'Se', 'Si', 
                                   'Rh', 'Mn', 'Pd', 'Ge', 'Sb', 'Sn']
substructure_search.add_substructure(dAu)

# Perform the substructure search
hits = substructure_search.search()

# Read the CSD database
csd_reader = ccdc.io.EntryReader('CSD')
dAu_molecules = []

# Filter results to include only molecules with Au2
for i in range(len(hits)):
    id = hits[i].identifier
    hit = csd_reader.entry(id)
    formula = hit.molecule.formula
    if 'Au2 ' in formula:
        dAu_molecules.append(hits[i].identifier)

# Remove duplicates and sort the molecule list
dAu_molecules = sorted(list(set(dAu_molecules)))

# Collect molecule and DOI information
data = []
for i in range(len(dAu_molecules)):
    abruf = csd_reader.entry(dAu_molecules[i])
    doi = abruf.publication.doi if abruf.publication else None
    data.append([dAu_molecules[i], doi])

# Convert to a Pandas DataFrame
df = pd.DataFrame(data, columns=["Molecule", "DOI"])

# Add a column for DOI URLs
df['url'] = df['DOI'].apply(lambda doi: f"https://doi.org/{doi}" if pd.notna(doi) else None)

output_file = os.path.join(current_dir, "molecule_doi_info.csv")

# Save the results to a CSV file
df.to_csv(output_file, index_label="Index")

print("Search complete. Results saved to 'molecule_doi_info.csv'.")
