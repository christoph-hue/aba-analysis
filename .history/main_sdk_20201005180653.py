from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.grid_data_api  import GridDataApi
from allensdk.core.structure_tree import StructureTree
from allensdk.api.queries.mouse_atlas_api import MouseAtlasApi
from allensdk.api.queries.rma_api import RmaApi
from allensdk.api.cache import Cache

import numpy
import pandas as pd

# https://github.com/benfulcher/AllenSDK
# http://help.brain-map.org/display/api/Atlas+Drawings+and+Ontologies


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


# we use the RmaApi to query specific information, such as the section data sets of a specific gene
rma = RmaApi()

# the cache_writeer allows us to easily cache the results
cache_writer = Cache()
use_cache = True


# accessing microarray-data?
# https://github.com/benfulcher/AllenSDK
# https://human.brain-map.org/microarray/search/show?exact_match=false&search_term=gabra4&search_type=gene
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5777841/
# http://help.brain-map.org/display/api/Connected+Services+and+Pipes

# http://api.brain-map.org/examples/rma_builder/index.html
# http://api.brain-map.org/examples/rma_builder/rma_builder.html
# https://allensdk.readthedocs.io/en/latest/data_api_client.html
sectionDataSets = pd.DataFrame( # wrap is told to be deprecated, but there is no information on what to use instead :(
    cache_writer.wrap(rma.model_query,
                        path='cache\\section-data-sets.json',
                        cache=use_cache,
                        model='SectionDataSet',
                        filters={'failed':'false'},
                        include="genes[acronym$ilGabra4],products[id$eq1]", # $il = case-insensitive like | yes, weird notation... id = 1 = mouse brain atlas (not developing!)
                        num_rows='all'))
# model's documentation: http://api.brain-map.org/doc/SectionDataSet.html
print(sectionDataSets)

# ok, so we don't need to do multiple requests to forward data from a model to a service, but simply use the pipe-concept:
# http://help.brain-map.org/display/api/Service+Pipelines
# e.g. this finds all probes for gabra4 and then queries the microarray-expression data for these probes
# http://api.brain-map.org/api/v2/data/query.json?criteria=
# model::Probe
# ,
# rma::criteria,
# gene[acronym$ilgabra4]
# ,
# pipe::list
# [probes$eq'id']
# ,
# service::human_microarray_expression
# [probes$eq$probes]

# this is a good usecase of using model_query
# https://download.alleninstitute.org/informatics-archive/september-2017/mouse_projection/download_projection_structure_unionize_as_csv.html

#oapi = OntologiesApi()
#structure_graph = oapi.get_structures_with_sets([1])  # 1 is the id of the adult mouse structure graph

# This removes some unused fields returned by the query
#structure_graph = StructureTree.clean_structures(structure_graph)  

#tree = StructureTree(structure_graph)
#print(tree.parents([1011]))

# some list of experiments with gene-search
# http://www.brainspan.org/ish/search/show?page_num=0&page_size=35&no_paging=false&search_term=H376.IV.03.R&search_type=advanced&facet_specimen_hemisphere=right
gdApi = GridDataApi()

experiments = []

for index, row in sectionDataSets.iterrows(): # https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
    exp = row['id']
    exp_path = f"data\\{exp}\\"
    try:
        gdApi.download_gene_expression_grid_data(exp,GridDataApi.ENERGY, exp_path)

        # According to the docs here: http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data
        # we have "A raw uncompressed float (32-bit) little-endian volume representing average expression energy per voxel. A value of "-1" represents no data. This file is returned by default if the volumes parameter is null."
        # https://docs.python.org/3/library/struct.html
        # struct helps us to read binary data by providing the used format. here, it is little-endian (represented by "<") and a 32-bit 
        #energy = numpy.array(list(struct.iter_unpack("<f", open(exp_path + "energy.raw", "rb").read()))).flatten() # way too complicated, but there is a delta in mean and sum. what is the right value??
        # just use 
        experiments.append(numpy.fromfile(exp_path + "energy.raw",  dtype=numpy.float32)) # we can use numpy.float32 or "<f"
    except Exception as e:
        print(f"Error retrieving experiment {exp}: {str(e)}")

print(experiments)

#gdApi.download_expression_grid_data(exp,GridDataApi.ENERGY,'gd.zip')



#print(numpy.mean(energy))
#print(numpy.mean(energy2))
#print(gd)

# http://help.brain-map.org/display/mousebrain/API#API-Expression3DGridsExpressionGridding
# http://help.brain-map.org/display/mousebrain/Documentation
# https://developingmouse.brain-map.org/static/atlas
# http://help.brain-map.org/pages/viewpage.action?pageId=2424836

# we only have 2 experiments for gabra4, right?
# https://mouse.brain-map.org/search/show?page_num=0&page_size=34&no_paging=false&exact_match=false&search_term=gaba%20alpha%204&search_type=gene
# mice: 75551483, 71924402
#

# humans:
# https://human.brain-map.org/ish/search/?page_num=0&page_size=400&no_paging=false&exact_match=false&search_term=gabra4&search_type=gene


# https://allensdk.readthedocs.io/en/latest/allensdk.api.queries.mouse_atlas_api.html

# mouseAtlasApi = MouseAtlasApi()

# print('getting genes')
# # data-model: http://api.brain-map.org/doc/Gene.html
# # https://stackoverflow.com/questions/17815945/convert-generator-object-to-a-dictionary
# all_genes = mouseAtlasApi.get_genes()
# print('got all genes')
# genes = {c['acronym']:c['id'] for c in all_genes} # (mouseAtlasApi.get_genes())
# print('transformed genes to dict')

# print(genes)
# gene_ids = []
# print('bla')

#for gene in genes:
    #if(gene['acronym'].lower() == 'gabra4'):
         #print('gene')
         #print(gene['id'])
         #gene_ids.append(gene['id'])
#print('done')
#print(gene_ids)

#datasets = mouseAtlasApi.get_section_data_sets(gene_ids)
#print(datasets)

# https://allensdk.readthedocs.io/en/latest/data_api_client.html

# "http://api.brain-map.org/api/v2/data/query.xml?criteria=model::SectionDataSet,rma::criteria,[failed$eq%27false%27],rma::include,genes[acronym$eq%27Gabra4%27]"

