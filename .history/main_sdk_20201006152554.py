from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.grid_data_api  import GridDataApi
from allensdk.core.structure_tree import StructureTree
from allensdk.api.queries.mouse_atlas_api import MouseAtlasApi
from allensdk.api.queries.rma_api import RmaApi
from allensdk.api.cache import Cache

from types import SimpleNamespace
import numpy as np
import pandas as pd

# https://python-reference.readthedocs.io/en/latest/docs/operators/index.html
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
# for docs, see: https://alleninstitute.github.io/AllenSDK/allensdk.api.queries.rma_api.html
rma = RmaApi() 

# the cache_writeer allows us to easily cache the results
cache_writer = Cache()
use_cache = False # load data once with use_cache = True, then change it to False to read it from disk instead of fetching it from the api

geneAcronym = "Gabra4"

# https://alleninstitute.github.io/AllenSDK/examples.html
# https://community.brain-map.org/t/allen-mouse-ccf-accessing-and-using-related-data-and-tools/359
# https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py


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
                        include=f"genes[acronym$il{geneAcronym}],products[id$eq1]", # $il = case-insensitive like | yes, weird notation... id = 1 = mouse brain atlas (not developing!)
                        num_rows='all'))
# model's documentation: http://api.brain-map.org/doc/SectionDataSet.html
print(sectionDataSets)

# ok, so we don't need to do multiple requests to forward data from a model to a service, but simply use the pipe-concept:
# http://help.brain-map.org/display/api/Service+Pipelines
# e.g. this finds all probes for gabra4 and then queries the microarray-expression data for these probes. note that variables generated by a pipe are referenced by $variableName

humanMicroarrayQuery = ("http://api.brain-map.org/api/v2/data/query.json?criteria="
        f"model::Probe,rma::criteria,gene[acronym$il{geneAcronym}],rma::options[num_rows$eqall],"
         "pipe::list[probes$eq'id'],"
         "service::human_microarray_expression[probes$eq$probes]")


humanExpressionData = cache_writer.wrap(
        rma.json_msg_query,
        path='cache\\human-microarray-expression.json',
        cache=use_cache,
        url=humanMicroarrayQuery
    )

# ok, now we got n probes with m expression-levels & z-scores
# we also got m samples that describe which donor and which structure each expression-level stems from
# we have to be aware that the expression-levels are retrieved from a probe, which represents a plane through the brain.
# so if the plane of the probe is not cutting through a specific brain-region, then there are null-values present for the expression-level.
# details: http://help.brain-map.org/display/humanbrain/API

# for each el in  humanExpressionData["probes"] ([1]["expression_level"]) => concat expression_level + z-score with sample-columns (+ ontology??)

# https://docs.python.org/3/library/types.html#types.SimpleNamespace
combined = SimpleNamespace()

setattr(combined, 'samples', []) 
setattr(combined, 'expression_levels', [])
setattr(combined, 'z_scores', [])

for probe in humanExpressionData["probes"]:
    # https://stackoverflow.com/questions/30522724/take-multiple-lists-into-dataframe
    #combined.append((["human" for x in range(num_samples)], 
    combined.samples += humanExpressionData["samples"]
    combined.expression_levels += probe["expression_level"]
    combined.z_scores += probe["z-score"]

# https://stackoverflow.com/questions/29325458/dictionary-column-in-pandas-dataframe
human = pd.DataFrame(np.column_stack([combined.expression_levels, combined.z_scores ]), 
                               columns=['expression_level', 'z-score'])

def unpack_dict_list(dict_list, attribute, prefix):
    return pd.DataFrame.from_dict([dict_list[i][attribute] for i in range(len(dict_list))]).add_prefix(prefix) # prefix to prevent naming conflicts

#donor = pd.DataFrame.from_dict([combined.samples[i]["donor"] for i in range(len(combined.samples))])

attributes = [("donor", ""), ("sample", "sample_"), ("structure", "struct_"), ("top_level_structure", "top_lvl_struct_")]

human = pd.concat([*[unpack_dict_list(combined.samples, attr[0], attr[1]) for attr in attributes], human], axis=1) # note that here, the * is the splat-operator

#pd.DataFrame.from_dict([combined.samples[i]["donor"] for i in range(len(combined.samples))])                           

# we spread / unpack the dictionaries in the sample column
#human = pd.concat([human.drop(['sample'], axis=1), human['sample'].apply(pd.Series)], axis=1)

print(len(human))



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
# gdApi = GridDataApi()

# experiments = []

# for index, row in sectionDataSets.iterrows(): # https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
#     exp_id = row['id']
#     exp_path = f"data\\{exp_id}\\"
#     try:
#         gdApi.download_gene_expression_grid_data(exp_id, GridDataApi.ENERGY, exp_path)

#         # According to the docs here: http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data
#         # we have "A raw uncompressed float (32-bit) little-endian volume representing average expression energy per voxel. A value of "-1" represents no data. This file is returned by default if the volumes parameter is null."
#         # https://docs.python.org/3/library/struct.html
#         # struct helps us to read binary data by providing the used format. here, it is little-endian (represented by "<") and a 32-bit 
#         #energy = numpy.array(list(struct.iter_unpack("<f", open(exp_path + "energy.raw", "rb").read()))).flatten() # way too complicated, but there is a delta in mean and sum. what is the right value??
#         # just use 
#         experiments.append(numpy.fromfile(exp_path + "energy.raw",  dtype=numpy.float32)) # we can use numpy.float32 or "<f"
#     except Exception as e:
#         print(f"Error retrieving experiment {exp_id}: {str(e)}")

# print(experiments)

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


#datasets = mouseAtlasApi.get_section_data_sets(gene_ids)
#print(datasets)

# https://allensdk.readthedocs.io/en/latest/data_api_client.html

# "http://api.brain-map.org/api/v2/data/query.xml?criteria=model::SectionDataSet,rma::criteria,[failed$eq%27false%27],rma::include,genes[acronym$eq%27Gabra4%27]"

