import numpy as np
import pandas as pd

from pandasgui import show

# TODO: load all experiments for mice and humans (=> rows), collect meta-data (sex, age, species, etc. => columns). then: get variance/std by meta-data and brain-region
# meta-data model definition: http://api.brain-map.org/doc/Donor.html
# how do i get a list of all experiments? => http://help.brain-map.org/display/api/Example+Queries+for+Experiment+Metadata
# http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI
# https://portal.brain-map.org/explore/transcriptome
# how do i get the 20 microm data? => 3-D PROJECTION GRID DATA is available in: 10, 25, 50, and 100 (in microns).
# https://wiki.mouseimaging.ca/ => https://wiki.mouseimaging.ca/display/MICePub/Mouse+Brain+Atlases

# https://allensdk.readthedocs.io/en/latest/allensdk.api.queries.grid_data_api.html
# https://allensdk.readthedocs.io/en/latest/data_api_client.html
# correlation of gabra4 expression in % for humans vs mice
# expression levels by brain region (also by species)
# comparison triangle: in situ human - microarray human - in situ mice
#   probe -> annotation -> ontology
#            location ? tree-structure from parent to root

# nice to have:
# ------------------------------
# single-cell rna-seq data.
# co-expression with beta- and gamma-subunits?
# if rna-seq not possible => smoothen correlation of subunits using 3d-gaussian per voxel

# medical case given:
# ------------------------------
# epilepsy-patient has variant of GABRA4 => alpha 4 subunit. question: in which brain regions is this gabra4 mainly expressed??
# differences in expression between humans and mice => heatmap of brain-structures + the numbers, please. differences in age?
# eventually exclude opposing sex? 
# for human-data, only one donor is available for each brain-region (most likely). 
# mice: one mouse per gene => only one animal for gabra4...
# normalization?

from HumanMicroarrayData import HumanMicroarrayData
from MouseISHData import MouseISHData
import FormattedExport
import Comparison
import Visualisation
import Constants

geneAcronym = "Gabra4"

# TODO: try nrrd http://help.brain-map.org/display/mouseconnectivity/API#API-DownloadAtlas
aggregations = ['min', 'max', 'mean', 'var', 'count']

# columns_and_rows_to_freeze='B2', 
human = HumanMicroarrayData(geneAcronym).get(from_cache=True, aggregations=aggregations)
FormattedExport.to_excel(human, f'export\\human_agg_{geneAcronym}.xlsx') # , columns_and_rows_to_freeze='M2'

mouse = MouseISHData(geneAcronym).get(from_cache=True, aggregations=aggregations) 
for i in range(0, len(mouse)):
    FormattedExport.to_excel(mouse[i], f'export\\mouse_{i}_agg_{geneAcronym}.xlsx')

comp = Comparison.by(human, mouse[0], 'acronym')
FormattedExport.to_excel(comp, f'export\\human_mouse_{geneAcronym}.xlsx')

#z_corr = comp[[(Constants.GLOB_Z + '_human', 'mean'), (Constants.GLOB_Z + '_mouse', 'mean'), ('acronym', '')]].corr()
agg ='mean'
groupBy = 'acronym'




u = Comparison.union([human.iloc[:,-3:], mouse[0].iloc[:,-3:]])

FormattedExport.to_excel(u, f'export\\human_mouse_union_{geneAcronym}.xlsx')

df = comp[[(Constants.GLOB_Z + '_human', 'mean'), (Constants.GLOB_Z + '_mouse', 'mean'), ('acronym', '')]]

# we flatten the data to make it more accesible:
# https://stackoverflow.com/questions/14507794/pandas-how-to-flatten-a-hierarchical-index-in-columns
df.columns = df.columns.get_level_values(0)

# get correlations by structure:
# https://stackoverflow.com/questions/28988627/pandas-correlation-groupby
z_corr = df.groupby(groupBy)[[Constants.GLOB_Z + '_human',Constants.GLOB_Z + '_mouse']].corr()
# we should compare the mean by region.
print(z_corr)
Visualisation.heatmap(z_corr)

# TODO: clarify - groupby poses an issue: donor-information for specific regions might vary => we cant group by donor-columns
# TODO: clarify - we got sagittal and coronal planes for mice. do we need both? for humans, no planes are specified (i guess microarray works differently).

#print(mouse)
#print(human)

#show(human, settings={'block': True})
#show(mouse[0], settings={'block': True})

# TODO: check ABA institute approach => works? fine! else: report bug and evaluate devmouse. fallback visualize microarray-data if possible.
# TODO: other databases for mice gene expression, preferably using in-situ hybridization => florian will send some links.

# TODO: check http://help.brain-map.org/display/devmouse/API -> are there any expression-levels without structureid as well? it is a decent fallback.
# TODO: detailed microarray or sequencing would also be ok. single-cell is difficult.


# https://binx.io/blog/2020/03/05/setting-python-source-folders-vscode/